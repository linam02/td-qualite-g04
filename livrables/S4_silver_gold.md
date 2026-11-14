# S4 · PySpark : construire silver puis gold

Groupe : g04  ·  Date : 13/11/2026  ·  Rédacteur : Amadou Macka Diallo  ·  Étiquette : `seance-4`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

**Preuve commune** : `pipelines/S4_silver_gold.py` (relançable de bout en bout : `docker exec -it dq_jupyter python pipelines/S4_silver_gold.py`), lot `L-2026-10-01`. Rôles en S4 : Rédacteur = Amadou Macka Diallo ; Data Owner, Data Steward, Ingénieur qualité : [À COMPLÉTER].

## 1. Silver et quarantaine (US-21, US-22)

Scripts ou notebooks (chemins) : `pipelines/S4_silver_gold.py`, cellules US-21 (fonctions de standardisation PySpark `maj`, `identite`, `adresse`, `telephone`, `pays`, `courriel`) et US-21, 22 (fonction idempotente `construire_silver`) ; tables `silver.client`, `silver.contrat`, `silver.sinistre`, `silver.type_contrat` ; quarantaine `dq.rejets` (porte S).

Traitements appliqués (pays, code postal, identité, autres), avec le nombre de lignes touchées par chacun :

| Traitement | Table | Lignes modifiées | Garde-fou (ce que le traitement ne doit pas faire) |
|---|---|---|---|
| Pays : `France`, `F`, `fr`, `Frnace` (après TRIM et majuscules) ramenés à `FR` | client (crm) | 2 600 (1 200 + 600 + 400 + 400, répartition mesurée en S1) ; variantes distinctes : 18 en bronze, 9 en silver | Ne jamais deviner un pays vide ou inconnu : les 400 vides et les 50 codes hors référentiel (`UK`…) partent en quarantaine (RQ-007) |
| Code postal : zéro initial restauré (`1500` → `01500`), ligne marquée `A_SURVEILLER` | client (crm) | 1 456 (codes à 4 chiffres, adresse FR : 1 456 en bronze, 0 en silver) | Seulement pour la France et un code de 4 chiffres exactement ; un code étranger n'est jamais complété |
| Sentinelle `assure_id = '0'` remplacée par NULL (décision n° 6) | contrat | 40 000 | Seule la valeur `'0'` est concernée ; aucun identifiant réel n'est modifié |
| Téléphone : vide et blanc ramenés à NULL ; espaces, points, tirets retirés ; `+33` et `0033` → `0` | client (crm, cif) | 4 000 vides ou blancs ramenés à NULL (crm, mesure S1) ; 21 134 numéros reformatés (crm, téléphone silver différent du téléphone bronze) | Ne jamais inventer un numéro ; un numéro étranger garde ses chiffres |
| Identité : majuscules, sans accent, préfixes `SOCIETE`, `SOC.`, `STE`, `ETS` retirés, `S.A.R.L.` → `SARL` | client (crm, cif) | 1 316 raisons sociales du CRM dont le préfixe (`Société`, `Sté`, `Soc.`, `Ets`) ou la forme `S.A.R.L.` est normalisé ; toutes les identités passent en majuscules sans accent ; ex. `Sté Meunier S.A.R.L.` → `MEUNIER SARL` | La normalisation sert à comparer ; la valeur d'origine reste en bronze, retrouvable par `bronze_row_id` |
| Types : dates converties en DATE, primes en DECIMAL, durée en entier | contrat, sinistre | 100 000 + 100 000 | Aucune conversion en flottant (pas de `184.1` pour `184.10`) |

Invariant silver + rejets = bronze :

| Table | Lignes bronze | Lignes silver | Lignes rejetées | Écart |
|---|---|---|---|---|
| client (crm) | 100 000 | 99 350 | 650 | 0 |
| client (cif) | 40 000 | 40 000 | 0 | 0 |
| contrat | 100 000 | 98 600 | 1 400 | 0 |
| sinistre | 100 000 | 100 000 | 0 | 0 |

Mesuré aussi comme règle : RQ-024 (silver + rejets = bronze) à 100 % sur les quatre tables, couche SILVER, dans `dq.dq_history`.

Rejets par règle (`dq.rejets`) :

| Règle | Table | Lignes rejetées | Raison métier |
|---|---|---|---|
| RQ-007 | client (crm) | 450 | Pays vide (400) ou code absent du référentiel après normalisation (50) : on ne devine pas le pays d'un client |
| RQ-009 | client (crm) | 200 | `type_personne` hors domaine {prospect, souscripteur, assure} |
| RQ-001 | contrat | 800 | Date de fin antérieure ou égale à la date de début : aucune période de garantie |
| RQ-010 | contrat | 600 | Durée hors catalogue {12, 24, 36, 60}, sans arrondi (décision n° 5) |

Écart avec nos décisions : le script de référence met en quarantaine les 200 lignes RQ-009, alors que la décision n° 3 prévoyait de corriger 140 d'entre elles en silver (casse 80, accent 40, abréviation 20) et de n'écarter que les 60 `client`. De même, la décision n° 7 (un prospect titulaire d'un contrat devient souscripteur) n'est pas appliquée : RQ-015 reste à 99,524 % sur silver. Ces deux corrections restent à coder dans `client_crm` (Ingénieur qualité) ; en attendant, 140 clients corrigeables et leurs contrats sortent du périmètre certifié.

Idempotence : le traitement relancé deux fois donne le même résultat (preuve) : cellule « Idempotence » de `pipelines/S4_silver_gold.py`, signature (nombre de lignes, somme CRC32 du contenu) identique aux deux passages : client [139 350 ; 299 661 536 892 034], contrat [98 600 ; 211 834 759 198 832], sinistre [100 000 ; 214 741 857 433 874]. 0 ligne silver sans ligne bronze d'origine (RQ-023 à 100 %).

## 2. Porte S : bronze contre silver (US-23)

Great Expectations relancé sans modification avec `COUCHE=SILVER` (code retour 0) ; Soda sur silver avec `soda/checks/silver/integrite_checks.yml` (code retour 2 : règles d'intégrité, mesurées pour la porte G).

| Règle | Sévérité | Taux bronze | Taux silver | Écart | Explication de l'écart |
|---|---|---|---|---|---|
| RQ-001 | Bloquante (porte S) | 99,200 % | 100,000 % | +0,800 | Les 800 contrats incohérents sont en quarantaine |
| RQ-007 | Bloquante (porte S) | 96,950 % | 100,000 % | +3,050 | 2 600 variantes ramenées à `FR`, 450 lignes en quarantaine |
| RQ-009 | Bloquante (porte S) | 99,800 % | 100,000 % | +0,200 | Les 200 valeurs hors domaine sont en quarantaine |
| RQ-010 | Bloquante (porte S) | 99,400 % | 100,000 % | +0,600 | Les 600 durées hors catalogue sont en quarantaine |
| RQ-005 | Avertissement (porte S) | 98,474 % | 100,000 % | +1,526 | Zéro initial restauré sur 1 456 codes postaux |
| RQ-003 | Avertissement (porte S) | 87,998 % | 88,006 % | +0,008 | Un téléphone absent ne se corrige pas par traitement ; la légère hausse vient des souscripteurs mis en quarantaine |
| RQ-020 | Bloquante (porte S) | 100 % | 100 % | 0 | Clés toujours uniques |
| RQ-012 | Bloquante (porte G) | 99,000 % | 98,382 % | −0,618 | Effet domino : les 650 clients mis en quarantaine laissent leurs contrats sans souscripteur |
| RQ-013 | Bloquante (porte G) | 99,700 % | 99,334 % | −0,366 | Même effet domino sur les assurés |
| RQ-016 | Avertissement (porte G) | 98,086 % | 97,700 % | −0,386 | Contrats en quarantaine (RQ-001, RQ-010) : des souscripteurs perdent leur seul contrat |
| RQ-011 | Bloquante (porte G) | 99,800 % | 99,798 % | −0,002 | Même nombre de codes inconnus sur un dénominateur plus petit (98 600 contrats) |

Toute règle dont le taux baisse de bronze à silver doit être expliquée : les quatre baisses (RQ-011, 012, 013, 016) sont des règles d'intégrité entre tables. Elles baissent parce que la quarantaine de silver retire des clients et des contrats, ce qui rend orphelins des contrats ou des souscripteurs jusque-là reliés. C'est l'effet domino attendu : il ne se masque pas, il se traite à la porte G (section 4).

Règles bloquantes de la porte S toutes conformes sur silver ? Sinon, lesquelles et pourquoi : oui. Les cinq règles bloquantes de la porte S (RQ-001, 007, 009, 010, 020) et les règles de traçabilité (RQ-023, 024) sont à 100 % : la porte S est franchie. Seule RQ-003, un avertissement, reste sous son seuil (88,0 % pour 98 %) : elle ne bloque pas la porte, mais le manque de téléphones doit être traité à la source.

## 3. Dédoublonnage et golden record (US-24, US-25)

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| Normalisation appliquée avant comparaison | Identité en majuscules sans accent, préfixes `SOCIETE`, `STE`… retirés, `S.A.R.L.` → `SARL` ; adresses abrégées développées (`R.` → `RUE`, `AV.` → `AVENUE`) | Sans normalisation, `Sté Meunier S.A.R.L.` et `MEUNIER SARL` ne se ressemblent pas |
| Clé(s) de blocage | Trois clés : code postal + 3 premières lettres de l'identité ; code postal + date de naissance (insensible à l'inversion jour / mois) ; ville + 4 premières lettres ; bloc de plus de 400 lignes ignoré | Comparer 139 350 lignes deux à deux est impossible ; le blocage ramène le travail à 2 782 840 paires candidates |
| Mesure de similarité | `fuzz.ratio` (rapidfuzz) sur l'identité normalisée, de 0 à 100, plus trois signaux : adresse ressemblante (≥ 80), même téléphone ou courriel, même date de naissance | Le nom seul confond les homonymes ; les signaux confirment |
| Seuil de fusion automatique | Similarité ≥ 85 ET même code postal ET au moins un signal concordant ; jamais une personne morale avec une personne physique ; même initiale de prénom ; dates de naissance non contradictoires | 85 donne la même précision et le même rappel que 80 (1,0 et 1,0) avec 4 fusions de moins ; à 90, le rappel tombe à 0,91 (9 vraies paires manquées) |
| Seuil de la zone de revue | Entre 70 et 85, ou sans signal concordant : non fusionné, à relire | Exemples : `DUMONT SARL` (H-35197) et `DUMONT SARL` (K883187), similarité 100 mais 0 signal : deux sociétés homonymes possibles |

| Mesure | Valeur |
|---|---|
| Groupes de doublons trouvés | 18 237 CLI regroupant au moins deux identifiants source (`gold.xref_identifiants`) ; 18 870 lignes silver rattachées à l'identité d'une autre (139 350 lignes → 120 480 identités) |
| Paires fusionnées automatiquement | 19 505 |
| Paires en zone de revue | 2 120 |
| Précision sur les 200 paires étiquetées | 1,0 (100 vrais positifs, 0 faux positif ; paires dont une ligne est en quarantaine non jugées) |
| Rappel sur les 200 paires étiquetées | 1,0 (0 faux négatif) |
| Identités distinctes obtenues | 120 480 |

Golden record de la Société Meunier :

| Identifiant source | Système | CLI attribué |
|---|---|---|
| A-4471 (`Société Meunier SARL`) | crm | CLI-033758 |
| H-9012 (`MEUNIER SARL`) | crm | CLI-033758 |
| S-2208 (`Sté Meunier S.A.R.L.`) | crm | CLI-033758 |
| K471226 (`SOCIETE MEUNIER S.A.R.L.`) | cif | CLI-033758 |

Les quatre écritures se normalisent en `MEUNIER SARL`, code postal 69003 : un seul CLI.

Règle de survie par attribut :

| Attribut | Source retenue | Règle (priorité, plus récent, non nul) | Cas où la règle se trompe |
|---|---|---|---|
| Nom | CIF, puis CRM | Priorité au CIF (dépôt central) ; dans une source, la ligne silver la plus ancienne ; première valeur non nulle | Une raison sociale changée récemment dans le CRM est écrasée par l'ancienne valeur du CIF |
| Adresse | CIF, puis CRM (code postal, ville, pays) | Même règle | Le client a déménagé et seul le CRM le sait : le CIF, prioritaire, garde l'ancienne adresse. L'adresse complète n'est pas reprise dans `gold.client_unique` (seulement code postal, ville, pays) |
| Téléphone | CIF, puis CRM | Première valeur non nulle dans l'ordre de priorité (15,8 % de téléphones absents dans le CIF : le CRM prend alors le relais) | Un numéro ancien mais renseigné dans le CIF l'emporte sur le numéro récent du CRM |
| Courriel | CIF, puis CRM | Première valeur non nulle (47,2 % de courriels absents dans le CIF) | La règle ne vérifie pas le format : une adresse invalide (1 210 dans le CRM) peut l'emporter |

Règle et seuils validés par : le Data Owner de la séance, sur proposition du Data Steward, reportés dans `JOURNAL_DECISIONS.md` (seuils de fusion 85 et 70, règle de survie CIF puis CRM).
## 4. Gold et client actif (US-27)

| Table gold | Lignes | Lignes écartées (porte G) | Règles responsables |
|---|---|---|---|
| client_unique | 120 480 | 0 | aucune |
| xref_identifiants | 139 350 | 0 | aucune (une ligne par identifiant source) |
| contrat_certifie | 95 866 | 2 734 (sur 98 600 contrats silver) | RQ-012 souscripteur absent : 1 595 ; RQ-013 assuré absent : 657 ; RQ-002 souscripteur mineur : 294 ; RQ-011 type inconnu : 199 (11 contrats écartés par deux règles) |
| sinistre_certifie | 96 532 | 3 468 | RQ-017 : sinistre hors période de garantie, ou contrat écarté en amont (détail par motif dans `dq.rejets`) |

Orphelins dans gold (contrat sans client, sinistre sans contrat) : 0. RQ-012, RQ-013 et RQ-017 sont à 100 % sur gold ; toutes les règles bloquantes mesurées sur gold sont conformes : la porte G est franchie. Soda sur gold (`soda/checks/client_unique_checks.yml`, RQ-019) : code retour 0, aucun CLI en double.

Client actif publié par la vue `v_client_actif` : 35 985 (vue `gold.v_client_actif`, la même pour les trois directions). Écart avec la définition de la fiche CD-001 : RQ-018 à 100 % sur gold (le statut ACTIF correspond exactement à CD-001 appliquée aux contrats certifiés). Par rapport aux 38 049 de bronze (S3), 2 064 clients actifs de moins : contrats en quarantaine (RQ-001, 010 en silver ; RQ-002, 011, 012, 013 en gold) et fusion de doublons (plusieurs identifiants source pour un même CLI).

Statuts dans `gold.client_unique` : PROSPECT 46 363, ACTIF 35 985, ASSURE 27 485, INACTIF 10 647.

Effet de la quarantaine sur l'intégrité en aval (un client écarté laisse-t-il des contrats orphelins ?) : oui. Les 650 clients mis en quarantaine en silver laissent des contrats sans souscripteur : RQ-012 rejette 1 595 contrats en gold, contre 1 000 orphelins mesurés en bronze, soit environ 595 de plus ; RQ-013 en rejette 657 contre 300 en bronze. Ces contrats écartés entraînent à leur tour leurs sinistres (RQ-017, 3 468 rejetés contre 1 200 hors garantie en bronze). La porte G garantit un gold sans orphelin, au prix de ces rejets en cascade. Appliquer la décision n° 3 (corriger 140 des 200 types de personne au lieu de les écarter) réduirait cette cascade.

## 5. Traçabilité de trois données (US-28)

| Donnée | Valeur dans gold | Silver (identifiants de ligne) | Bronze (identifiants de ligne, lot) | Source (table, clé) |
|---|---|---|---|---|
| Société Meunier | `gold.client_unique` CLI-033758, `MEUNIER SARL` | `silver.client` 173569, 212675, 226862 (crm), 255320 (cif) | `bronze.crm_client` 334450, 373793, 388069 ; `bronze.cif_clients` 136620 ; lot L-2026-10-01 | `crm.client` A-4471, H-9012, S-2208 ; `cif.clients` K471226 |
| Un code postal à zéro initial | CLI-000069, code postal `01500` | `silver.client`, source A-10062, `cp = 01500`, statut `A_SURVEILLER` | `bronze.crm_client` 300070, `cp = 1500`, lot L-2026-10-01 | `crm.client` A-10062 |
| Une adresse de sinistre | `gold.sinistre_certifie` SIN0000012, `89 RUE DE L'HOTEL DE VILLE` | `silver.sinistre` 100012 | `bronze.crm_sinistre` 300012, `89 rue de l'Hôtel de Ville`, lot L-2026-10-01 | `crm.sinistre` SIN0000012 |

Chaîne : `gold.client_unique` (cli_id) → `gold.xref_identifiants` → `silver.client` (silver_row_id) → `bronze.*` (bronze_row_id, `_batch_id`) → source (identifiant source).

Requête de traçabilité (chemin) : `pipelines/S4_silver_gold.py`, cellule US-28 (trois requêtes, une par cas).

## 6. Critères de fin

- [x] Pour chaque table, silver + rejets = bronze, sans suppression silencieuse. (écart 0 sur les quatre tables, RQ-024 à 100 %, section 1)
- [x] Relancer le traitement deux fois donne le même résultat. (signatures identiques, section 1)
- [x] Les règles bloquantes de la porte S sont conformes sur silver. (RQ-001, 007, 009, 010, 020, 023, 024 à 100 %, section 2)
- [x] Le gold ne contient aucun orphelin ; le client actif est publié par une seule vue. (RQ-012, 013, 017 à 100 % ; `gold.v_client_actif` : 35 985, section 4)
- [x] Les trois traces remontent du gold à la source avec identifiants de ligne et de lot. (section 5)

## 7. Difficultés, écarts avec l'attendu, reprise

le traitement S4 dure plusieurs minutes (Spark, comparaison de 2,8 millions de paires) et ne doit pas être interrompu ; le message de fusion de Git s'est ouvert dans l'éditeur Vim, qu'il a fallu apprendre à quitter (`:wq`).
Écart avec l'attendu : les décisions n° 3 (correction de `type_personne`) et n° 7 (prospect avec contrat devenu souscripteur) ne sont pas encore appliquées par le code de silver (section 1).

Point de reprise utilisé (oui / non, lequel, à quel moment) : non.

appliquer les décisions de gouvernance dans le code avant de construire silver (décisions n° 3 et 7), plutôt que de constater l'écart après coup ; faire afficher par le script le nombre de lignes modifiées par chaque normalisation et le nombre de groupes de doublons ; relire les 2 120 paires de la zone de revue, en commençant par les homonymes à similarité 100 sans signal.

## Annexe · Adresses de sinistre et BAN (US-26, Should)

Mesuré par `pipelines/S4_silver_gold.py`, cellule US-26, sur les 100 000 sinistres de silver :
- Taux d'adresses non reconnues dans l'extrait de la BAN : 11,87 % avant correction (11 871 adresses), 7,96 % après (3 914 voies corrigées, un seul candidat ressemblant, ex. `R JEAN MOULIN` → `RUE JEAN MOULIN`, `AVENUE FOH` → `AVENUE FOCH`).
- Pareto par canal de saisie : la ressaisie manuelle concentre 8 066 des 11 871 adresses non reconnues (68 %), pour 30 % des sinistres.
- Restent non corrigées : 3 939 couples code postal / commune absents de la BAN, 2 020 numéros absents de la BAN, 1 982 adresses sans numéro, 16 cas ambigus. La cible de 2 % est hors d'atteinte avec la BAN seule : ces adresses n'ont aucun candidat fiable, il faut les faire corriger à la saisie (ressaisie manuelle) ou en revue par un Data Steward.
