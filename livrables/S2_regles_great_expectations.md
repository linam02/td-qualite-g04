# S2 · Great Expectations : des règles en tests automatisés

Groupe : g04  ·  Date : 21/10/2026  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-2`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

**Preuves** : `pipelines/S2_regles_great_expectations.py` (script de référence, relançable de bout en bout), `notebooks/S2_Fatine.ipynb` (US-10), `notebooks/S2_regles_great_expectations.ipynb` (US-11, branche de Lyse), journal des décisions (`livrables/JOURNAL_DECISIONS.md`, décisions 2 à 5). Lot `L-2026-10-01`, couche BRONZE.

Contributions : section 1 et pièges : Fatine Mourid ; échantillon des lignes en échec (section 2) : Lyse Ndifo ; classement RQ-009, familles RQ-010, sévérités et décisions : Amadou Macka Diallo (Data Steward) ; sections 3 et 4 : [À COMPLÉTER : qui] ; Quỳnh Lê : [À COMPLÉTER]. Rôles S2 : voir `livrables/00_equipe.md`.

## 1. Règles en tests (US-10)

Une ligne par règle. L'expectation porte son `rule_id` dans `meta` ; la couche est un paramètre (`COUCHE=BRONZE`, `COUCHE=SILVER` en S4), la sévérité et le seuil sont lus dans `dq.regle`, pas dans le code.

| Règle | Table bronze | Expectation (type) | Lignes testées | Lignes en échec | Taux de réussite | Sévérité retenue (bloquante / avertissement) |
|---|---|---|---|---|---|---|
| RQ-001 | crm_contrat | `expect_column_pair_values_A_to_be_greater_than_B` (date_fin > date_debut, strict) | 100 000 | 800 | 99,200 % | Bloquante : un contrat qui finit avant de commencer n'a pas de période de garantie calculable |
| RQ-002 | crm_contrat | `expect_column_values_to_be_between` (age_debut ≥ 18, âge à la date de début) | 100 000 | 301 | 99,699 % | Bloquante : un mineur ne peut pas souscrire, le contrat est juridiquement invalide |
| RQ-003 | crm_client (souscripteurs crm) | `expect_column_values_to_not_be_null` + `expect_column_values_to_match_regex` (`\S`) | 49 898 | 5 989 | 87,998 % | Avertissement (seuil 98 %) : le client reste joignable par adresse ou e-mail ; règle sous le seuil, à signaler au Data Owner |
| RQ-005 | crm_client (`pays = 'FR'`) | `expect_column_values_to_match_regex` (`^\d{5}$`) | 95 437 | 1 456 | 98,474 % | Avertissement (seuil 98 %) : défaut corrigeable en silver (zéro initial) ; conforme au seuil |
| RQ-009 | crm_client | `expect_column_values_to_be_in_set` ({prospect, souscripteur, assure}) | 100 000 | 200 | 99,800 % | Bloquante : le type décide du statut client et du calcul du client actif |
| RQ-010 | crm_contrat | `expect_column_values_to_be_in_set` ({12, 24, 36, 60}) | 100 000 | 600 | 99,400 % | Bloquante : une durée hors catalogue ne correspond à aucun produit |
| RQ-020 | crm_client, crm_contrat, crm_sinistre, cif_clients | `expect_column_values_to_not_be_null` + `expect_column_values_to_be_unique` (clé) | 340 000 (100 000 × 3 + 40 000) | 0 | 100 % | Bloquante : sans clé fiable, aucun rapprochement entre tables |

(1) RQ-003 ne concerne que les souscripteurs : seuls les 49 898 clients du CRM de type « souscripteur » sont testés, sur 100 000. Deux expectations portent le même identifiant RQ-003 : la première compte les NULL, la seconde les chaînes vides et blanches, ce qui distingue les trois cas.
(2) RQ-005 ne concerne que les adresses en France : 95 437 lignes sur 100 000. Les codes postaux étrangers sont exclus du test.
(3) La même règle RQ-020 est appliquée aux quatre tables : 100 000 lignes pour chacune des trois tables du CRM et 40 000 pour cif_clients, 0 échec dans chacune.

Règle mesurée en plus : RQ-007 (pays dans `silver.ref_pays`), crm_client, `expect_column_values_to_be_in_set`, 100 000 testées, 3 050 en échec, 96,950 %, bloquante.

Sévérités confirmées par le Data Steward sans modification par rapport à `dq.regle` (décision n° 2 du journal).

Pièges rencontrés et traitement (nul, vide, blanc ; adresses étrangères ; comparaisons exactes) :

| Règle | Piège | Chiffre avant correction | Chiffre après correction | Preuve |
|---|---|---|---|---|
| RQ-003 | Nul, vide et blanc : en ne comptant que les NULL, les téléphones vides ('') et blancs ('   ') passent inaperçus | 1 995 (NULL seulement) | 5 989 (1 995 NULL + 1 995 vides + 1 999 blancs) | `notebooks/S2_Fatine.ipynb`, cellules 5 et 7 |
| RQ-005 | Adresses étrangères : en testant toutes les adresses, les codes postaux étrangers comptent comme des erreurs | 2 317 (toutes les adresses) | 1 456 (adresses en France seulement) : 861 fausses erreurs écartées | `notebooks/S2_Fatine.ipynb`, cellule 5 |
| RQ-009 | Comparaison exacte : une comparaison insensible à la casse et aux accents accepte à tort « Souscripteur » ou « assuré » | 80 (comparaison souple) | 200 (comparaison exacte) : 120 valeurs mal écrites détectées | `notebooks/S2_Fatine.ipynb`, cellules 5 et 7 |

Suites de validation (chemins) : `reports/ge/gx/expectations/`, une suite par table :
- `assurconnect_bronze_crm_client_suite.json` (RQ-003, RQ-005, RQ-007, RQ-009, RQ-020)
- `assurconnect_bronze_crm_contrat_suite.json` (RQ-001, RQ-002, RQ-010, RQ-020)
- `assurconnect_bronze_crm_sinistre_suite.json` (RQ-020)
- `assurconnect_bronze_cif_clients_suite.json` (RQ-020)

Checkpoints : `reports/ge/gx/checkpoints/` (un par table, `dq_bronze_<table>.yml`). Rapport HTML (Data Docs) : `reports/ge/gx/uncommitted/data_docs/local_site/index.html`, généré localement et non versionné.

## 2. Lignes en échec (US-11)

Export complet : `reports/echecs/lignes_en_echec_RQ-001.csv`, `…_RQ-003.csv`, `…_RQ-005.csv`, `…_RQ-009.csv`, `…_RQ-010.csv`, un fichier par règle (identifiant, valeur, motif), régénéré par `pipelines/S2_regles_great_expectations.py` ; non versionné (le `.gitignore` exclut les CSV hors `livrables/`).

Échantillon commenté de 20 lignes, 4 par règle en échec : `notebooks/S2_regles_great_expectations.ipynb`, cellule US-11.

| Règle | Famille d'erreur observée | Nombre de lignes de l'échantillon | Cause probable | Action proposée (à qui ?) |
|---|---|---|---|---|
| RQ-001 | Date de fin égale ou antérieure au début | 4 | Durée nulle ou dates inversées à la saisie | Quarantaine en silver ; correction à la source par la gestion des contrats (Data Steward) |
| RQ-003 | Téléphone vide ou blanc (invisible pour IS NULL) | 4 | Champ facultatif, ou espaces tapés pour contourner l'obligation | Champ obligatoire dans le CRM (DSI) ; vide et blanc ramenés à NULL en silver |
| RQ-005 | Code postal à 4 chiffres (7300 au lieu de 07300) | 4 | Zéro initial perdu lors d'un export ou d'un passage par un tableur | Restaurer le zéro en silver et contrôler avec `ref_postal` (Ingénieur qualité) |
| RQ-009 | « assuré », « Souscripteur » | 4 | Saisie libre, sans liste fermée | Table de correspondance en silver (Data Steward) ; « client » arbitré par le Data Owner |
| RQ-010 | Durées de 6, 9 ou 48 mois | 4 | Produit hors catalogue ou erreur de saisie | Quarantaine en silver sans arrondi (décision n° 5 du journal, Data Steward) ; élargir le catalogue reste une décision du Data Owner |

Trois familles sont corrigeables en silver (RQ-003, 005, 009) ; deux demandent une décision métier (RQ-001, 010).

Second échantillon, centré sur la règle bloquante RQ-009 : 20 lignes tirées par le script (`random_state=1`), classées par le Data Steward (décision n° 3 du journal) :

| Règle | Famille d'erreur observée | Nombre de lignes de l'échantillon | Cause probable | Action proposée (à qui ?) |
|---|---|---|---|---|
| RQ-009 | Accent sur une valeur du domaine : `assuré` (ex. A-34062, H-18891, S-4573) | 8 / 20 (40 lignes sur 200 au total) | saisie libre sans liste fermée | Retrait de l'accent en silver, `assuré` → `assure` (Ingénieur qualité, règle validée par le Data Steward) |
| RQ-009 | Casse non normalisée : `Souscripteur` (4), `SOUSCRIPTEUR` (2) (ex. A-25815, A-16506) | 6 / 20 (80 sur 200) | saisie libre, majuscules en début ou verrouillage majuscule | Passage en minuscules en silver (Ingénieur qualité) |
| RQ-009 | Valeur hors référentiel : `client` (ex. S-9808, A-22145, A-3412) | 4 / 20 (60 sur 200) | ancien libellé générique : impossible de savoir s'il s'agit d'un souscripteur, d'un assuré ou d'un prospect | Quarantaine en silver (`dq.rejets`), pas de correction automatique ; statut à faire trancher par la direction commerciale (Data Owner) |
| RQ-009 | Abréviation : `prosp.` (ex. S-17392, H-4145) | 2 / 20 (20 sur 200) | saisie abrégée | Remplacement par `prospect` en silver (Ingénieur qualité) |

Familles des autres règles en échec (sur l'ensemble des lignes) :

| Règle | Famille d'erreur observée | Lignes en échec | Cause probable | Action proposée (à qui ?) |
|---|---|---|---|---|
| RQ-005 | Zéro initial perdu (code à 4 chiffres, ex. `1000` pour 01000) | 1 456 | code postal traité comme un nombre lors d'un export | Restauration du zéro en silver, puis contrôle par le référentiel postal (RQ-006) (Ingénieur qualité) |
| RQ-003 | Téléphone absent (NULL, vide ou blanc) | 5 989 souscripteurs | champ facultatif dans l'outil de saisie | Non corrigeable par traitement : collecte auprès du client et champ obligatoire à la source (Data Owner, direction commerciale) |
| RQ-001 | Incohérence de dates (date de fin ≤ date de début) | 800 | inversion des deux dates ou erreur de saisie | Quarantaine en silver ; correction à la source par la gestion des contrats (Data Owner) |
| RQ-010 | Durée intermédiaire hors catalogue : 18 (229), 6 (148), 48 (104), 9 (64) mois | 545 | durées réelles mais absentes du catalogue {12, 24, 36, 60} : anciennes offres ou contrats sur mesure | Quarantaine en silver, sans arrondi automatique ; liste des produits à confirmer par la direction produit (Data Owner) |
| RQ-010 | Durée aberrante : 120 mois (55) | 55 | probable zéro ajouté à la saisie (12 → 120) | Quarantaine ; vérification contrat par contrat avant toute correction (Data Steward, gestion des contrats) |

## 3. Âge à la date de début du contrat (US-13, RQ-002)

92 996 contrats ont un souscripteur dont la date de naissance est connue (les autres : souscripteur orphelin ou personne morale, âge non testable).

| Date de référence | Définition de l'âge | Lignes en échec | Preuve |
|---|---|---|---|
| Date de début du contrat | années révolues entre la naissance du souscripteur et `date_debut` (même calcul que `TIMESTAMPDIFF(YEAR, …)`), échec si < 18 | 301 | `pipelines/S2_regles_great_expectations.py`, cellule US-13, colonne `age_debut` |
| Date du jour | années révolues à la date de référence du lot (01/10/2026, utilisée à la place de la date du jour pour un résultat stable), échec si < 18 | 157 | même cellule, colonne `age_reference` |

Un cas où « à la date du jour » donne un autre résultat, et pourquoi : le contrat CT0000387, souscrit le 01/09/2014 par A-22244, né le 28/09/1996, avait 17 ans à la signature : il est en échec à la date de début, mais a 30 ans au 01/10/2026 et passerait le test « à la date du jour ». Au total, 144 contrats changent de verdict : tous sont des contrats signés par un mineur qui est devenu majeur depuis. Mesurer l'âge à la date du jour masquerait donc 144 des 301 souscriptions invalides (48 %).

## 4. Mesure de référence sur bronze (US-15)

Écrite dans `dq.dq_history`, couche BRONZE, lot : `L-2026-10-01` (11 mesures Great Expectations + 14 mesures de la porte B issues de S1). Synthèse lue dans la vue `dq.dq_kpi_dimension`.

| Dimension | Règles | Taux moyen | Règle la plus faible | Constat |
|---|---|---|---|---|
| Unicité | RQ-020 (4 tables) | 100,00 % | aucune | 0 clé nulle ou en double sur 340 000 lignes |
| Complétude | RQ-003 | 88,00 % | RQ-003 (87,998 %) | dimension la plus faible : 5 989 souscripteurs sans téléphone, 10 points sous le seuil de 98 % |
| Validité | RQ-005 (format) 98,47 % ; RQ-009, RQ-010 (domaine) 99,60 % ; RQ-002 (métier) 99,70 % | 98,47 à 99,70 % | RQ-005 (98,474 %), mais au-dessus de son seuil ; parmi les bloquantes : RQ-010 (99,400 %) | 200 types de personne, 600 durées et 301 souscripteurs mineurs empêchent la conformité des règles bloquantes |
| Cohérence | RQ-001 | 99,20 % | RQ-001 (99,200 %) | 800 contrats aux dates incohérentes |

Intégrité référentielle (RQ-007) : 96,95 %, 3 050 pays hors référentiel. Traçabilité et réconciliation (RQ-021, RQ-022) : 100 %.

Phrase de synthèse : Voici la qualité de ce qui nous est livré : sur bronze (lot L-2026-10-01), la copie est fidèle (porte B à 100 %) et les clés sont saines (RQ-020 à 100 %), mais 5 des 6 règles bloquantes mesurées sont sous leur seuil de 100 % (RQ-001, 002, 007, 009, 010, soit 4 951 lignes en échec) et la complétude du téléphone des souscripteurs n'est qu'à 88,0 % : en l'état, ces données ne peuvent pas être certifiées, et silver devra corriger ou mettre en quarantaine ces lignes.

## 5. Critères de fin

- [x] Chaque expectation porte l'identifiant de sa règle. (`meta={"rule_id": …}` sur chaque expectation, section 1)
- [ ] La même suite se relance sur une autre base ou table sans modification de code. (non démontré à ce jour : la variable `COUCHE` et les requêtes `CHARGEMENT["SILVER"]` sont prêtes, mais silver est vide ; la relance sera faite en S4, US-23, avec `COUCHE=SILVER`)
- [x] La mesure de référence est dans `dq.dq_history` avec le lot, la couche, les lignes testées et les échecs. (section 4)
- [x] Les règles sont exécutables d'un seul geste (script ou notebook relançable de bout en bout). (`pipelines/S2_regles_great_expectations.py` ; la relance remplace les mesures du lot, sans doublon)

## 6. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : fusion des branches de S1 dans `main`, conflit sur `AVANCEMENT.md` et sur le livrable S1, environ 30 min en début de séance. [À COMPLÉTER : autres difficultés]

Point de reprise utilisé (oui / non, lequel) : non.

Ce que nous ferions autrement : [À COMPLÉTER]