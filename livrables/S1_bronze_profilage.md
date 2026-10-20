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

 

## 2. Bronze et porte B (US-02, US-03)

**Méthode d'ingestion en trois lignes :**

1. Nous avons d'abord récupéré les données des sept tables avec le compte `reader`, qui permet uniquement de lire les données sans modifier les sources.
2. Ensuite, nous avons converti les colonnes en texte pour conserver les valeurs d'origine, notamment les décimales grâce à `coerce_float=False`. Nous avons aussi ajouté quatre informations à chaque ligne : le lot, la source, la date d'ingestion et l'empreinte de la ligne.
3. Enfin, avant chaque chargement, nous supprimons les données du même lot pour éviter les doublons. Ainsi, même si nous relançons l'ingestion, nous obtenons le même résultat.**Méthode d'ingestion en trois lignes :**

1. Nous avons d'abord récupéré les données des sept tables avec le compte `reader`, qui permet uniquement de lire les données sans modifier les sources.
2. Ensuite, nous avons converti les colonnes en texte pour conserver les valeurs d'origine, notamment les décimales grâce à `coerce_float=False`. Nous avons aussi ajouté quatre informations à chaque ligne : le lot, la source, la date d'ingestion et l'empreinte de la ligne.
3. Enfin, avant chaque chargement, nous supprimons les données du même lot pour éviter les doublons. Ainsi, même si nous relançons l'ingestion, nous obtenons le même résultat.

Réconciliation RQ-021 (comptage) et RQ-022 (somme de contrôle), pour le lot mesuré : `L-2026-10-01`
| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Écart de somme de contrôle |
|---|---|---|---|---|
| crm_client | 100 000 | 100 000 | 0 | 0 |
| crm_contrat | 100 000 | 100 000 | 0 | 0 |
| crm_sinistre | 100 000 | 100 000 | 0 | 0 |
| crm_type_contrat | 12 | 12 | 0 | 0 |
| cif_clients | 40 000 | 40 000 | 0 | 0 |
| cif_compte | 45 000 | 45 000 | 0 | 0 |
| cif_pays | 250 | 250 | 0 | 0 |

Aucun écart de comptage ni de somme de contrôle sur les sept tables : la porte B est franchie. Résultat enregistré dans dq.dq_history (règle RQ-021, couche BRONZE). Preuve : notebooks/S1_US02_Fatine.ipynb, cellule 7.

Épreuves de la porte (à documenter, avec la preuve de chacune) :

| Épreuve | Résultat obtenu | Preuve |
|---|---|---|
| Relance du même lot : doublons créés | 0 doublon. Après une deuxième ingestion du lot L-2026-10-01, chaque table bronze garde le même nombre de lignes : 100 000 (crm_client, crm_contrat, crm_sinistre), 12 (crm_type_contrat), 40 000 (cif_clients), 45 000 (cif_compte) et 250 (cif_pays). | `notebooks/S1_US02_Fatine.ipynb`, cellule 5 |
| Écart introduit volontairement sur une copie : la porte échoue-t-elle ? | Oui. Sur une copie de test de crm_client, la porte B échoue dans les 3 cas : une valeur modifiée (écart de comptage 0, mais somme de contrôle différente), une ligne supprimée (écart de comptage -1) et une ligne en double (écart de comptage +1). La copie non modifiée passe la porte. Le vrai bronze n'est jamais modifié. | `notebooks/S1_US02_Fatine.ipynb`, cellule 8 |
| Un problème de conversion rencontré (décimales, NULL, accents) et sa correction | Décimales : lue sans option, une prime dont la deuxième décimale est 0 perd ce zéro (CT0000020 : 184.10 devient 184.1). 9 912 primes sur 100 000 dans crm.contrat sont concernées, ce qui ferait échouer la somme de contrôle de la porte B. Correction : lecture avec `coerce_float=False`, la valeur reste 184.10 dans bronze et la porte B affiche 0 écart. | `notebooks/S1_US02_Fatine.ipynb`, cellules 6 et 7 |

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

- [X ] Les sept tables bronze existent et chaque ligne porte ses quatre métadonnées.
- [X ] La porte B ne montre aucun écart de comptage ni de somme de contrôle.
- [ X] Relancer l'ingestion du même lot ne crée aucun doublon.
- [ ] Un écart introduit volontairement fait échouer la porte.
- [ X] RQ-021 est écrite dans `dq.dq_history` (couche BRONZE).

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
