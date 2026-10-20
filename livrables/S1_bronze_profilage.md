# S1 · Stack Docker, profilage, construction de bronze

Groupe : [À COMPLÉTER]  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-1`

Rappel : un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Inventaire des sources (US-01)

| Source | Table | Lignes | Clé primaire | Observation chiffrée |
|---|---|---|---|---|
| crm | client | 100 000 | client_id | Clé unique, 0 doublon. 7 colonnes sur 13 ont des manques : 133 918 NULL, 2 400 vides et 2 000 blancs. Une grande partie des NULL est normale : 4 277 clients sont des entreprises, sans nom, prénom ni date de naissance. |
| crm | contrat | 100 000 | contrat_id | Clé unique, 0 doublon. 1 colonne sur 9 a des manques : 7 460 NULL. |
| crm | sinistre | 100 000 | sinistre_id | Clé unique, 0 doublon. 1 colonne sur 10 a des manques : 1 965 vides, 0 NULL. |
| crm | type_contrat | 12 | code_type | Clé unique, 0 doublon. Petite table de référence, aucune valeur manquante. |
| cif | clients | 40 000 | column0 | Clé unique, 0 doublon. 10 colonnes sans nom, toutes en texte. 4 colonnes sur 10 ont des manques : 26 486 NULL. |
| cif | compte | 45 000 | column0 | Clé unique, 0 doublon. Aucune valeur manquante. 100 % des valeurs de column1 existent dans cif.clients.column0 : lien vers les clients, non déclaré. |
| cif | pays | 250 | code_pays | Clé unique, 0 doublon. Aucune valeur manquante. Les 250 codes sont tous dans silver.ref_pays. |

Preuve : `notebooks/S1_US01_Fatine.ipynb` ; tableau dans `reports/S1_US01_inventaire.md`.

|---|---|---|---|---|
| crm | client | 100 000 | client_id | Clé unique, 0 doublon. 7 colonnes sur 13 ont des manques : 133 918 NULL, 2 400 vides et 2 000 blancs. Une grande partie des NULL est normale : 4 277 clients sont des entreprises, sans nom, prénom ni date de naissance. |
| crm | contrat | 100 000 | contrat_id | Clé unique, 0 doublon. 1 colonne sur 9 a des manques : 7 460 NULL. |
| crm | sinistre | 100 000 | sinistre_id | Clé unique, 0 doublon. 1 colonne sur 10 a des manques : 1 965 vides, 0 NULL. |
| crm | type_contrat | 12 | code_type | Clé unique, 0 doublon. Petite table de référence, aucune valeur manquante. |
| cif | clients | 40 000 | column0 | Clé unique, 0 doublon. 10 colonnes sans nom, toutes en texte. 4 colonnes sur 10 ont des manques : 26 486 NULL. |
| cif | compte | 45 000 | column0 | Clé unique, 0 doublon. Aucune valeur manquante. 100 % des valeurs de column1 existent dans cif.clients.column0 : lien vers les clients, non déclaré. |
| cif | pays | 250 | code_pays | Clé unique, 0 doublon. Aucune valeur manquante. Les 250 codes sont tous dans silver.ref_pays. |



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 



nes sur rande s nom, 
onne sur 
olonne 
 table 
es sans . |
eur umn0 : 
 

## 2. Bronze et porte B (US-02, US-03)

Méthode d'ingestion en trois lignes (lecture, conversion, métadonnées, relance du lot) : [À COMPLÉTER]

Réconciliation RQ-021 (comptage) et RQ-022 (somme de contrôle), pour le lot mesuré :

| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Écart de somme de contrôle |
|---|---|---|---|---|
| crm_client | … | … | … | … |
| crm_contrat | … | … | … | … |
| crm_sinistre | … | … | … | … |
| crm_type_contrat | … | … | … | … |
| cif_clients | … | … | … | … |
| cif_compte | … | … | … | … |
| cif_pays | … | … | … | … |

Épreuves de la porte (à documenter, avec la preuve de chacune) :

| Épreuve | Résultat obtenu | Preuve |
|---|---|---|
| Relance du même lot : doublons créés | … | … |
| Écart introduit volontairement sur une copie : la porte échoue-t-elle ? | … | … |
| Un problème de conversion rencontré (décimales, NULL, accents) et sa correction | … | … |

## 3. Profil de crm.client (US-06, US-07)

Au moins cinq constats chiffrés.

| N° | Colonne | Indicateur (nulls, vides, distincts, motif…) | Valeur mesurée | Ce que cela change pour la qualité |
|---|---|---|---|---|
| 1 | … | … | … | … |
| 2 | … | … | … | … |
| 3 | … | … | … | … |
| 4 | … | … | … | … |
| 5 | … | … | … | … |

Motifs (conformes / non conformes) :

| Attribut | Motif testé | Lignes conformes | Lignes non conformes | Exemple de valeur non conforme |
|---|---|---|---|---|
| Code postal | … | … | … | … |
| Téléphone | … | … | … | … |
| Pays | … | … | … | … |

Preuve (notebook, requête) : [À COMPLÉTER]

## 4. Dictionnaire du CIF (US-04)

| Colonne d'origine | Nom proposé | Type | Justification chiffrée (comment l'avez-vous déduit ?) |
|---|---|---|---|
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |

## 5. Trois définitions du « client actif » (US-09)

| Direction | Définition utilisée | Nombre de clients | Écart avec la définition de la fiche CD-001 |
|---|---|---|---|
| Commerciale | … | … | … |
| Sinistres | … | … | … |
| Risques | … | … | … |

Conséquence pour la gouvernance, en trois phrases : [À COMPLÉTER]

## 6. Critères de fin (cochez, avec la preuve si elle n'est pas dans une section ci-dessus)

- [ ] Les sept tables bronze existent et chaque ligne porte ses quatre métadonnées.
- [ ] La porte B ne montre aucun écart de comptage ni de somme de contrôle.
- [ ] Relancer l'ingestion du même lot ne crée aucun doublon.
- [ ] Un écart introduit volontairement fait échouer la porte.
- [ ] RQ-021 est écrite dans `dq.dq_history` (couche BRONZE).

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
