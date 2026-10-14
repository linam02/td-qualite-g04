# S1 · Stack Docker, profilage, construction de bronze

Groupe : g04  ·  Date : 14/10/2026  ·  Rédacteur : Amadou Macka Diallo  ·  Étiquette : `seance-1`

Rappel : un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

**Preuve commune à toutes les sections** : `pipelines/S1_g04_mesures.py` (relançable de bout en bout : `docker exec -it dq_jupyter python pipelines/S1_g04_mesures.py --ydata`), sorties dans `reports/s1/S1_resultats.md`, `reports/s1/s1_resultats.json` et `reports/ydata_profiling_client.html`. Lot mesuré : `L-2026-10-01`, date de référence 01/10/2026, cotisation à jour depuis le 01/07/2026 (mêmes paramètres que `pipelines/aq.py`). Le script de référence fourni, `pipelines/S1_bronze_profilage.py`, est conservé tel quel.

## 1. Inventaire des sources (US-01)

Comptages par requête `SELECT COUNT(*)`, clé primaire lue dans `information_schema`, doublons de clé = `COUNT(*) - COUNT(DISTINCT clé)`.

| Source | Table | Lignes | Clé primaire | Observation chiffrée |
|---|---|---|---|---|
| crm | client | 100 000 | client_id | 0 doublon de clé. 4 277 personnes morales (nom NULL, raison_sociale renseignée) ; email NULL 19 365 (19,4 %), téléphone NULL 5 999 (6,0 %) |
| crm | contrat | 100 000 | contrat_id | 0 doublon de clé. `assure_id = '0'` sur 40 000 lignes (40 %, valeur sentinelle) ; 1 000 souscripteurs absents de client ; 200 code_type absents de type_contrat ; date_derniere_cotisation NULL 7 460 (7,5 %) |
| crm | sinistre | 100 000 | sinistre_id | 0 doublon de clé, aucun NULL, 0 contrat_id orphelin |
| crm | type_contrat | 12 | code_type | 0 doublon, aucun NULL ; 12 codes seulement alors que 200 contrats citent un code inconnu |
| cif | clients | 40 000 | column0 | 0 doublon de clé. column9 NULL 18 872 (47,2 %), column8 NULL 6 324 (15,8 %), column2 et column3 NULL 645 (1,6 %) |
| cif | compte | 45 000 | column0 | 0 doublon de clé, aucun NULL ; column1 : 40 000 valeurs distinctes, 0 orpheline vers cif.clients |
| cif | pays | 250 | code_pays | 0 doublon, aucun NULL : référentiel de 250 codes pays |

Preuve (notebook, requête) : `pipelines/S1_g04_mesures.py`, cellule « US-01 » ; résultat dans `reports/s1/S1_resultats.md`, sections « US-01 ».

## 2. Bronze et porte B (US-02, US-03)

Méthode d'ingestion en trois lignes (lecture, conversion, métadonnées, relance du lot) :
1. **Lecture** de chaque table source avec chaque colonne convertie en texte par MariaDB (`CAST(col AS CHAR)`) : dates, décimales et NULL gardent exactement leur forme source (NULL reste NULL, `''` reste `''`, `'   '` reste `'   '`).
2. **Métadonnées** ajoutées à chaque ligne : `_batch_id` (`L-2026-10-01`), `_source_system` (crm ou cif), `_ingested_at`, `_row_hash` = 16 premiers caractères du SHA-256 des valeurs jointes par `|` (NULL écrit `\N`).
3. **Relance** : les lignes du lot sont supprimées puis réécrites dans la même transaction, donc relancer un lot le remplace sans jamais le dupliquer ; le lot est suivi dans `dq.lot_ingestion`.

Réconciliation RQ-021 (comptage + somme de contrôle `SUM(CRC32(ligne en texte))` calculée par MariaDB des deux côtés + comparaison ligne à ligne des empreintes) et RQ-022 (quatre métadonnées présentes, empreinte conforme au contenu), pour le lot `L-2026-10-01` :

| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Écart de somme de contrôle |
|---|---|---|---|---|
| crm_client | 100 000 | 100 000 | 0 | 0 (214 528 576 956 306 des deux côtés) |
| crm_contrat | 100 000 | 100 000 | 0 | 0 (214 970 337 491 057) |
| crm_sinistre | 100 000 | 100 000 | 0 | 0 (214 902 603 302 661) |
| crm_type_contrat | 12 | 12 | 0 | 0 (27 536 952 762) |
| cif_clients | 40 000 | 40 000 | 0 | 0 (85 973 760 448 678) |
| cif_compte | 45 000 | 45 000 | 0 | 0 (96 842 431 909 202) |
| cif_pays | 250 | 250 | 0 | 0 (529 205 112 408) |

Sur les 7 tables : 0 ligne sans jumelle (RQ-021), 0 ligne sans métadonnées valides (RQ-022). **Porte B franchie.** Les 14 mesures (RQ-021 et RQ-022 × 7 tables) sont écrites dans `dq.dq_history`, couche BRONZE, taux de conformité 100 %. Un écart nul est ici le résultat attendu : il prouve que bronze est une copie fidèle, pas que les valeurs sont de bonne qualité (cf. section 3).

Épreuves de la porte (à documenter, avec la preuve de chacune) :

| Épreuve | Résultat obtenu | Preuve |
|---|---|---|
| Relance du même lot : doublons créés | 0 ligne créée sur les 7 tables (ex. crm_client : 100 000 lignes avant et après relance), 0 empreinte en double dans le lot | cellule « Épreuve 1 », `reports/s1/S1_resultats.md` |
| Écart introduit volontairement sur une copie : la porte échoue-t-elle ? | Oui. Copie `bronze.epreuve_crm_client` avec 1 valeur modifiée et 1 ligne supprimée : écart de comptage −1, écart de somme de contrôle −4 480 326 241, 3 lignes sans jumelle, 1 empreinte non conforme (RQ-022) ⇒ porte **ÉCHEC**. La copie est supprimée ensuite ; bronze n'est jamais modifié | cellule « Épreuve 2 » |
| Un problème de conversion rencontré (décimales, NULL, accents) et sa correction | Lecture naïve `SELECT *` puis `astype(str)` : 9 912 primes de crm.contrat altérées (`184.10` → `184.1`), 10 083 montants de crm.sinistre (`1007.80` → `1007.8`), et chaque NULL devenu le texte `None` (ex. 5 999 téléphones de crm.client). Correction : conversion en texte par MariaDB (`CAST AS CHAR`) et NULL conservé, ce qui donne 0 écart à la porte B | cellule « Épreuve 3 » |

## 3. Profil de crm.client (US-06, US-07)

Mesuré sur `bronze.crm_client` (lot `L-2026-10-01`, 100 000 lignes). NULL, vide et blanc comptés séparément.

| N° | Colonne | Indicateur (nulls, vides, distincts, motif…) | Valeur mesurée | Ce que cela change pour la qualité |
|---|---|---|---|---|
| 1 | type_personne | valeurs hors domaine {prospect, souscripteur, assure} | 200 lignes : `client` 60, `Souscripteur` 50, `assuré` 40, `SOUSCRIPTEUR` 30, `prosp.` 20 (8 valeurs distinctes pour 3 attendues) | RQ-009 (bloquante) échoue sur bronze. Casse et accent se normalisent en silver ; `client` et `prosp.` sont ambigus : quarantaine, décision du Data Steward |
| 2 | telephone | NULL / vide / blanc | 5 999 / 2 000 / 2 000, soit 9 999 non renseignés (10,0 %) | RQ-003 (complétude, seuil 98 %) à mesurer en S2 sur les souscripteurs : les trois états doivent être comptés, pas seulement NULL |
| 3 | pays | valeurs distinctes ; hors format ISO2 | 18 distinctes pour 100 000 lignes ; 3 000 hors `^[A-Z]{2}$` (`France` 1 200, `F` 600, `fr` 400, `''` 400, `Frnace` 400), et 50 codes à deux lettres absents du référentiel, dont `UK` ×20 (code ISO réel : GB) | RQ-007 (bloquante) : 3 050 lignes hors référentiel silver.ref_pays. Il faut une table de correspondance en silver, et `F` / `Frnace` ne sont pas reconnus comme France par un filtre simple |
| 4 | cp | longueur ; codes à 4 chiffres en France | longueur 4 à 8 ; 1 456 codes postaux à 4 chiffres sur les 95 437 adresses `pays = 'FR'` (ex. `1000`), 0 vide | Zéro initial perdu (01000 lu comme nombre) : RQ-005 et RQ-006 échouent tant que le zéro n'est pas restauré en silver |
| 5 | nom + prenom + date_naissance | lignes en double | 738 en écartant les NULL ; 5 014 avec un `duplicated()` pandas naïf | Écart de 4 276 dû aux 4 277 personnes morales (nom, prénom et date NULL) qui se comptent entre elles. Le dédoublonnage S4 doit écarter les NULL |
| 6 | email | NULL ; renseigné hors motif | 19 365 NULL (19,4 %) ; 1 210 renseignés mais hors motif `x@y.zz` | RQ-008 (avertissement) : 1 210 adresses à corriger à la source |
| 7 | date_naissance | min / max | 11/04/1938 à 13/07/2026 ; 0 date future ; 4 277 NULL = exactement les personnes morales | Des clients nés en 2026 sont possibles (assuré mineur) mais pas en tant que souscripteur : RQ-002, âge calculé à la date de début du contrat en S2 |

Motifs (conformes / non conformes) :

| Attribut | Motif testé | Lignes conformes | Lignes non conformes | Exemple de valeur non conforme |
|---|---|---|---|---|
| Code postal (RQ-005) | `^[0-9]{5}$`, adresses avec `pays = 'FR'` exactement (95 437 lignes) | 93 981 (98,47 %) | 1 456 | `1000` (×92), `1100` (×77) : zéro initial perdu |
| Code postal (périmètre élargi) | `^[0-9]{5}$`, pays FR, France ou fr après TRIM/UPPER (97 037 lignes) | 95 559 (98,48 %) | 1 478 | les 22 de plus viennent des adresses `France` / `fr` |
| Téléphone | `^0[1-9][0-9]{8}$`, adresse en France : brut / après normalisation (espaces, points, tirets retirés, +33 et 0033 → 0) | 65 495 brut (67,49 %) / 86 470 normalisé (89,11 %) | 31 542 / 10 567 | NULL (×5 820), blanc `'   '` (×1 945), vide (×1 936) |
| Pays | code ISO2 présent dans silver.ref_pays (100 000 lignes) | 96 950 (96,95 %) | 3 050 | `France` (×1 200), `F` (×600), `Frnace` (×400) |

La normalisation du téléphone fait passer 20 975 lignes de non conforme à conforme : ce sont des numéros valides mal écrits, à traiter en silver, pas à rejeter. Les 10 567 restants sont surtout des téléphones absents (RQ-003).

Preuve (notebook, requête) : `pipelines/S1_g04_mesures.py`, cellules « US-06 » et « US-07 » ; `reports/s1/S1_resultats.md`.

Rapport YData-Profiling (fichier `reports/ydata_profiling_client.html`, généré par `pipelines/S1_g04_mesures.py --ydata` et ouvert dans un navigateur) :

| N° | Variable | Ce que le rapport montre sans requête | Requête qui le chiffre |
|---|---|---|---|
| 1 | raison_sociale | [À COMPLÉTER : % de valeurs manquantes affiché et alerte éventuelle, à lire dans le rapport] | `SUM(raison_sociale IS NULL)` = 95 723 (95,7 %) : ce sont les personnes physiques, un manque normal et non un défaut |
| 2 | type_personne | [À COMPLÉTER : nombre de catégories et tableau des fréquences affichés] | `GROUP BY type_personne` : 8 valeurs pour 3 attendues, 200 lignes hors domaine |
| 3 | pays | [À COMPLÉTER : nombre de valeurs distinctes et valeurs les plus fréquentes affichés] | `GROUP BY pays` : 18 valeurs distinctes, 3 050 hors silver.ref_pays |

Un constat que le rapport ne signale pas (aucune alerte), et la requête qui l'a trouvé : [À COMPLÉTER après lecture du rapport : vérifier qu'aucune alerte ne porte sur cp] le zéro initial perdu du code postal. Le rapport voit `cp` comme un texte de 4 à 8 caractères, sans règle de format : c'est la requête `cp REGEXP '^[0-9]{5}$' AND pays = 'FR'` qui trouve 1 456 codes à 4 chiffres. De même, il ne compte comme manquants que les 5 999 téléphones NULL, pas les 2 000 vides ni les 2 000 blancs.

Apport et limite de l'outil, en deux phrases : [À COMPLÉTER : relire après ouverture du rapport] YData donne en une passe une vue d'ensemble (manquants, cardinalités, distributions) qui oriente les requêtes à écrire. Il décrit les valeurs sans connaître les règles métier : il ne dit pas qu'un code postal à 4 chiffres ou `Frnace` sont invalides, ni qu'une chaîne blanche équivaut à une absence.

## 4. Dictionnaire du CIF (US-04)

Mesuré sur `bronze.cif_clients` (40 000 lignes) et `bronze.cif_compte` (45 000 lignes) : taux de valeurs conformes à des formats candidats, distincts, unicité, recouvrement avec les valeurs de crm.client.

| Colonne d'origine | Nom proposé | Type | Justification chiffrée (comment l'avez-vous déduit ?) |
|---|---|---|---|
| clients.column0 | id_cif | VARCHAR(10), clé primaire | 40 000 valeurs distinctes sur 40 000 (100 % uniques), 0 NULL, longueur fixe 7 ; 100 % des 45 000 compte.column1 y font référence (0 orphelin) |
| clients.column1 | nom_ou_raison_sociale | VARCHAR(120) | 99,6 % alphabétique, 731 distincts, longueur 3 à 31 ; 98,4 % des valeurs existent comme nom dans crm.client (11,6 % comme prénom) |
| clients.column2 | prenom | VARCHAR(80) | 100 % alphabétique, 180 distincts ; 100 % existent comme prénom dans crm.client ; 645 NULL (1,6 %), les mêmes lignes que column3 NULL : personnes morales |
| clients.column3 | date_naissance | DATE (stockée en texte JJ/MM/AAAA) | 100 % des valeurs renseignées au format JJ/MM/AAAA, années 1938 à 2026, 21 081 distinctes ; 645 NULL |
| clients.column4 | adresse | VARCHAR(255) | 100 % commencent par un numéro suivi d'un libellé de voie, 9 811 distinctes |
| clients.column5 | code_postal | CHAR(5) | 99,1 % à 5 chiffres, 99,8 % uniquement numériques, 188 distincts ; les 0,9 % restants à 4 chiffres : même zéro perdu que crm.client |
| clients.column6 | ville | VARCHAR(80) | 100 % alphabétique, 172 distinctes ; 83,3 % existent comme ville dans crm.client (0,4 % comme nom) |
| clients.column7 | code_pays | CHAR(2) | 100 % à deux majuscules, 9 distincts, 100 % présents dans cif.pays |
| clients.column8 | telephone | VARCHAR(20) | 100 % des valeurs renseignées à 10 chiffres au format 0X XX XX XX XX, 33 676 distinctes ; 6 324 NULL (15,8 %) |
| clients.column9 | email | VARCHAR(150) | 100 % des valeurs renseignées au motif `x@y.zz`, 21 128 distinctes ; 18 872 NULL (47,2 %) |

Table cif.compte (même méthode) : column0 = **id_compte** (45 000 uniques, longueur 10) ; column1 = **id_cif**, clé étrangère vers clients.column0 (100 % trouvées, 40 000 distinctes pour 45 000 lignes : 1 à plusieurs comptes par client) ; column2 = **date_ouverture** (100 % AAAA-MM-JJ, du 01/01/2005 au 30/09/2026) ; column3 = **statut du compte** (domaine {O, F} : O = 39 611, F = 5 389).

Ce que cela change : une première détection automatique avait inversé id_cif et telephone (column8 est aussi 100 % unique et 100 % numérique). C'est le croisement avec cif.compte (0 orphelin) et le format à 10 chiffres commençant par 0 qui tranche. Le dictionnaire est à valider par le Data Steward avant la construction de silver.

## 5. Trois définitions du « client actif » (US-09)

Souscripteurs distincts de crm.contrat (NULL écartés), à la date de référence du 01/10/2026 ; cotisation à jour = dernière cotisation au 01/07/2026 ou après. Définitions de la fiche CD-001.

| Direction | Définition utilisée | Nombre de clients | Écart avec la définition de la fiche CD-001 |
|---|---|---|---|
| Commerciale | au moins un contrat, quel que soit son état | 50 508 | +12 459 (+32,7 %) : clients sans contrat en cours ou sans cotisation récente |
| Sinistres | un contrat en cours à la date de référence (début ≤ 01/10/2026 ≤ fin) | 44 116 | +6 067 (+15,9 %) : contrat en cours mais cotisation non à jour depuis 3 mois |
| Risques | CD-001 : un contrat en cours ET une cotisation à jour sur les trois derniers mois | 38 049 | 0 (c'est la définition de référence) |

Les trois ensembles sont emboîtés : tout client « Risques » est aussi « Sinistres », et tout client « Sinistres » est aussi « Commerciale » (0 client dans CD-001 absent des deux autres). Rapport à la plus large : 1,000 / 0,873 / 0,753.

Conséquence pour la gouvernance, en trois phrases : Les trois chiffres sont exacts, chacun pour sa propre question, et ils vont de 38 049 à 50 508, soit 12 459 clients d'écart : un quart des « clients actifs » de la direction commerciale ne le sont pas au sens de la fiche CD-001. Tant que chaque direction calcule « son » client actif, aucun indicateur ne se compare ni ne se consolide, et le futur CRM hériterait de trois vérités. Le Data Owner doit arrêter la définition unique CD-001 (règle RQ-018), calculée par une seule requête partagée par les trois directions (S3), puis portée dans gold.

Preuve : `pipelines/S1_g04_mesures.py`, cellule « US-09 » (les trois requêtes y sont écrites en clair, et dans `reports/s1/s1_resultats.json`, clé `us09_requetes`).

## 6. Critères de fin (cochez, avec la preuve si elle n'est pas dans une section ci-dessus)

- [x] Les sept tables bronze existent et chaque ligne porte ses quatre métadonnées. (RQ-022 : 0 échec sur les 7 tables, section 2)
- [x] La porte B ne montre aucun écart de comptage ni de somme de contrôle. (section 2)
- [x] Relancer l'ingestion du même lot ne crée aucun doublon. (Épreuve 1)
- [x] Un écart introduit volontairement fait échouer la porte. (Épreuve 2)
- [x] RQ-021 est écrite dans `dq.dq_history` (couche BRONZE). (7 lignes RQ-021 et 7 lignes RQ-022, lot L-2026-10-01 ; vérifiable par `SELECT * FROM dq.v_derniere_mesure WHERE batch_id = 'L-2026-10-01'`)

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : installation de Git et clonage (URL du dépôt mal recopiée, environ 10 min) ; récupération tardive des scripts de référence (`pipelines/aq.py`, `S1` à `S5`, `sql/`) absents du dépôt GitHub, d'où un premier essai sous un mauvais lot et de mauvaises définitions du client actif (environ 20 min) ; premier `docker compose up --build` interrompu par un redémarrage du terminal VS Code et relancé (environ 15 min, plus 10 min de build) ; dictionnaire du CIF : l'heuristique automatique confondait id_cif et telephone, corrigée par le critère « référencé par cif.compte » (environ 10 min).

Point de reprise utilisé (oui / non, lequel) : non. Un premier essai avait été ingéré sous un identifiant de lot erroné (`L-2026-10-14`, date du 14/10/2026) avant que nous récupérions `pipelines/aq.py`, qui fixe le lot `L-2026-10-01`. Ce lot d'essai a été supprimé entièrement (bronze, `dq.dq_history`, `dq.lot_ingestion`), sans toucher au contenu d'aucune ligne, puis le bon lot a été réingéré par le script. Décision consignée dans `livrables/JOURNAL_DECISIONS.md`.

Ce que nous ferions autrement : démarrer la pile Docker la veille (le premier build dure plus de 10 minutes) ; lancer le build depuis un PowerShell indépendant plutôt que le terminal intégré ; lire les paramètres du lot (`pipelines/aq.py`) et la fiche CD-001 avant de mesurer.
