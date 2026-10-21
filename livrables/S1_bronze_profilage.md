# S1 · Stack Docker, profilage, construction de bronze

Groupe : 04  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-1`

Rappel : un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Inventaire des sources (US-01)

| Source | Table | Lignes | Clé primaire | Observation chiffrée |
|---|---|---|---|---|
| crm | client | … | … | … |
| crm | contrat | … | … | … |
| crm | sinistre | … | … | … |
| crm | type_contrat | … | … | … |
| cif | clients | … | … | … |
| cif | compte | … | … | … |
| cif | pays | … | … | … |

Preuve (notebook, requête) : [À COMPLÉTER]

## 2. Bronze et porte B (US-02, US-03)

Méthode d'ingestion en trois lignes (lecture, conversion, métadonnées, relance du lot) : [À COMPLÉTER]

Réconciliation RQ-021 (comptage) et RQ-022 (somme de contrôle), pour le lot mesuré :

| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Écart de somme de contrôle |
|---|---|---|---|---|
| crm_client | 100 000 | 100 000 | 0 | 0 |
| crm_contrat | 100 000 | 100 000 | 0 | 0 |
| crm_sinistre | 100 000 | 100 000 | 0 | 0 |
| crm_type_contrat | 12 | 12 | 0 | 0 |
| cif_clients | 40 000 | 40 000 | 0 | 0 |
| cif_compte | 45 000 | 45 000 | 0 | 0 |
| cif_pays | 250 | 250 | 0 | 0 |

La porte B passe : 0 écart sur les 7 tables (RQ-021) et toutes les lignes portent leurs 4 métadonnées (RQ-022). Les mesures sont enregistrées dans `dq.dq_history`, couche BRONZE.

Épreuves de la porte (à documenter, avec la preuve de chacune) :

| Épreuve | Résultat obtenu | Preuve |
|---|---|---|
| Relance du même lot : doublons créés | Aucun : après une 2e ingestion, chaque table bronze a toujours le même nombre de lignes que sa source, avec un seul lot et 0 doublon de client_id. | `notebooks/S1_bronze_profilage.ipynb`, cellule US-02 |
| Écart introduit volontairement sur une copie : la porte échoue-t-elle ? | Oui. En modifiant une seule ville sur une copie de crm_client, on garde 100 000 lignes mais la somme de contrôle change (1 écart). En supprimant ensuite une ligne, on passe à 99 999 lignes (2 écarts). Compter les lignes ne suffit pas : la somme de contrôle repère une valeur modifiée. | `notebooks/S1_bronze_profilage.ipynb`, cellule US-03 |
| Un problème de conversion rencontré (décimales, NULL, accents) et sa correction | Les montants sont en DECIMAL dans la source. Lus comme des nombres, « 184.10 » deviendrait « 184.1 » et la somme de contrôle ne correspondrait plus. Ils sont donc lus en texte (`coerce_float=False`), ce qui donne 0 écart. | `pipelines/S1_bronze_profilage.py`, fonction `ingerer` |

## 3. Profil de crm.client (US-06, US-07)

Au moins cinq constats chiffrés.

| N° | Colonne | Indicateur (nulls, vides, distincts, motif…) | Valeur mesurée | Ce que cela change pour la qualité |
|---|---|---|---|---|
| 1 | client_id | distincts, nuls | 100 000 distincts, 0 nul | La clé est fiable : on peut s'appuyer dessus pour relier les tables. |
| 2 | type_personne | valeurs hors domaine (prospect, souscripteur, assure) | 200 lignes : client 60, Souscripteur 50, assuré 40, SOUSCRIPTEUR 30, prosp. 20 | Des fautes de casse, d'accent ou d'abréviation, à normaliser en silver ; « client » ne correspond à aucun rôle et doit être arbitré. |
| 3 | nom / raison_sociale | nuls | 4 277 noms nuls, qui sont exactement les 4 277 lignes avec une raison sociale (et sans date de naissance) | Ce ne sont pas des erreurs mais des entreprises : le contrôle doit porter sur « nom ou raison sociale ». |
| 4 | telephone | nuls, vides, blancs | 5 999 nuls + 2 000 vides + 2 000 blancs = 9 999 (10 %) | Trois formes d'absence : un simple test IS NULL n'en verrait que 5 999. |
| 5 | date_naissance | âge au 01/10/2026 | 10 479 mineurs, dont 10 301 assurés mais 162 souscripteurs | Un enfant peut être assuré, mais pas signer un contrat : ces 162 souscripteurs sont des anomalies à vérifier en S2 (RQ-002). |

Motifs (conformes / non conformes) :

| Attribut | Motif testé | Lignes conformes | Lignes non conformes | Exemple de valeur non conforme |
|---|---|---|---|---|
| Code postal | … | … | … | … |
| Téléphone | … | … | … | … |
| Pays | … | … | … | … |

Preuve (notebook, requête) : `notebooks/S1_bronze_profilage.ipynb`, cellules US-06 et US-07 ; rapport `reports/ydata_profiling_client.html`

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
- [x] La porte B ne montre aucun écart de comptage ni de somme de contrôle.
- [ ] Relancer l'ingestion du même lot ne crée aucun doublon.
- [x] Un écart introduit volontairement fait échouer la porte.
- [x] RQ-021 est écrite dans `dq.dq_history` (couche BRONZE).

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
