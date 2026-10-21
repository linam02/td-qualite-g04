# S2 · Great Expectations : des règles en tests automatisés

Groupe : `04`  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-2`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Règles en tests (US-10)

Une ligne par règle. L'expectation porte son `rule_id` ; la base et la table visées sont des paramètres.
| Règle | Table bronze | Expectation (type) | Lignes testées | Lignes en échec | Taux de réussite | Sévérité retenue (bloquante / avertissement) |
|---|---|---|---|---|---|---|
| RQ-001 | crm_contrat | expect_column_pair_values_A_to_be_greater_than_B | 100 000 | 800 | 99,200 % | Bloquante |
| RQ-002 | crm_contrat | expect_column_values_to_be_between (min 18) | 100 000 | 301 | 99,699 % | Bloquante |
| RQ-003 | crm_client | expect_column_values_to_not_be_null + expect_column_values_to_match_regex (\S) | 49 898 (1) | 5 989 | 87,998 % | Avertissement |
| RQ-005 | crm_client | expect_column_values_to_match_regex (^\d{5}$) | 95 437 (2) | 1 456 | 98,474 % | Avertissement |
| RQ-009 | crm_client | expect_column_values_to_be_in_set | 100 000 | 200 | 99,800 % | Bloquante |
| RQ-010 | crm_contrat | expect_column_values_to_be_in_set (12, 24, 36, 60) | 100 000 | 600 | 99,400 % | Bloquante |
| RQ-020 | crm_client, crm_contrat, crm_sinistre, cif_clients (3) | expect_column_values_to_not_be_null + expect_column_values_to_be_unique | 340 000 | 0 | 100,000 % | Bloquante |

(1) RQ-003 ne concerne que les souscripteurs : seuls les 49 898 clients du CRM de type « souscripteur » sont testés, sur 100 000. Deux expectations portent le même identifiant RQ-003 : la première compte les NULL, la seconde les chaînes vides et blanches, ce qui distingue les trois cas.
(2) RQ-005 ne concerne que les adresses en France : 95 437 lignes sur 100 000. Les codes postaux étrangers sont exclus du test.
(3) La même règle RQ-020 est appliquée aux quatre tables : 100 000 lignes pour chacune des trois tables du CRM et 40 000 pour cif_clients, 0 échec dans chacune.

Règle testée en plus du modèle : RQ-007 (pays dans le référentiel silver.ref_pays, bloquante), 3 050 échecs sur 100 000 lignes de crm_client (96,950 %). Seuils et justification des sévérités : `livrables/JOURNAL_DECISIONS.md`.

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

Export complet : `reports/echecs/lignes_en_echec_RQ-xxx.csv`(branche lyse_td_qualite_g04), un fichier par règle (identifiant, valeur, motif), régénéré par le notebook. 

Échantillon commenté de 20 lignes : `notebooks/S2_regles_great_expectations.ipynb` (branche lyse_td_qualite_g04), cellule US-11 (4 lignes par règle).

| Règle | Famille d'erreur observée | Nombre de lignes de l'échantillon | Cause probable | Action proposée (à qui ?) |
|---|---|---|---|---|
| RQ-001 | Date de fin égale ou antérieure au début | 4 | Durée nulle ou dates inversées à la saisie | Quarantaine en silver ; correction à la source par la gestion des contrats (Data Steward) |
| RQ-003 | Téléphone vide ou blanc (invisible pour IS NULL) | 4 | Champ facultatif, ou espaces tapés pour contourner l'obligation | Champ obligatoire dans le CRM (DSI) ; vide et blanc ramenés à NULL en silver |
| RQ-005 | Code postal à 4 chiffres (7300 au lieu de 07300) | 4 | Zéro initial perdu lors d'un export ou d'un passage par un tableur | Restaurer le zéro en silver et contrôler avec `ref_postal` (Ingénieur qualité) |
| RQ-009 | « assuré », « Souscripteur » | 4 | Saisie libre, sans liste fermée | Table de correspondance en silver (Data Steward) ; « client » arbitré par le Data Owner |
| RQ-010 | Durées de 6, 9 ou 48 mois | 4 | Produit hors catalogue ou erreur de saisie | Décision du Data Owner : élargir la liste ou mettre en quarantaine |

Trois familles sont corrigeables en silver (RQ-003, 005, 009) ; deux demandent une décision métier (RQ-001, 010).


## 3. Âge à la date de début du contrat (US-13, RQ-002)

| Date de référence | Définition de l'âge | Lignes en échec | Preuve |
|---|---|---|---|
| Date de début du contrat | … | … | … |
| Date du jour | … | … | … |

Un cas où « à la date du jour » donne un autre résultat, et pourquoi : [À COMPLÉTER]

## 4. Mesure de référence sur bronze (US-15)

Écrite dans `dq.dq_history`, couche BRONZE, lot : [À COMPLÉTER]

| Dimension | Règles | Taux moyen | Règle la plus faible | Constat |
|---|---|---|---|---|
| Unicité | … | … | … | … |
| Complétude | … | … | … | … |
| Validité | … | … | … | … |
| Cohérence | … | … | … | … |

Phrase de synthèse (« Voici la qualité de ce qui nous est livré : … ») : [À COMPLÉTER]

## 5. Critères de fin

- [ ] Chaque expectation porte l'identifiant de sa règle.
- [ ] La même suite se relance sur une autre base ou table sans modification de code.
- [ ] La mesure de référence est dans `dq.dq_history` avec le lot, la couche, les lignes testées et les échecs.
- [ ] Les règles sont exécutables d'un seul geste (script ou notebook relançable de bout en bout).

## 6. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
