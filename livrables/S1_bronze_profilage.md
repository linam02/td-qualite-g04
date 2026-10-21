
# S1 · Stack Docker, profilage, construction de bronze

Groupe : 04 · Date : 21/10/2026 · Rédacteur : Groupe 04 · Étiquette : `seance-1`

## 1. Inventaire des sources (US-01)

| Source | Table | Lignes | Clé primaire | Observation chiffrée |
<<<<<<< HEAD
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
=======
|---|---|---:|---|---|
| crm | client | 100000 | client_id | 19365 emails vides (19,37 %) |
| crm | contrat | 100000 | contrat_id | 400 contrats avec date_fin antérieure à date_debut |
| crm | sinistre | 100000 | sinistre_id | 0 déclaration antérieure à la survenance |
| crm | type_contrat | 12 | code_type | 0 libellé vide |
| cif | clients | 40000 | column0 | 18872 emails vides (47,18 %) |
| cif | compte | 45000 | column0 | 0 valeur vide dans column1 |
| cif | pays | 250 | code_pays | 0 nom_pays vide |

**Total : 385262 lignes dans 7 tables sources.**

Les sept tables possèdent une clé primaire déclarée dans MariaDB.

**Preuves :**
- `reports/S1_profilage_sources.sql`
- `reports/S1_profilage_crm_client.sql`
- `reports/S1_dictionnaire_cif.sql`

## 2. Bronze et porte B (US-02, US-03)

### Méthode d'ingestion

1. Lecture des sept tables sources CRM et CIF par lots de 1000 lignes.
2. Conservation des données sources sous forme textuelle dans Bronze, avec quatre métadonnées : `_batch_id`, `_source_system`, `_ingested_at` et `_row_hash`.
3. Contrôle du lot d'ingestion afin de permettre une relance sans duplication des données.

Le chargement utilise le lot `S1_G04_001`. Les empreintes `_row_hash` permettent de contrôler l'intégrité des données entre les sources et Bronze.
>>>>>>> 72dc2deba2ec32a09b9300dfafe8a8b5dde5fd46

**Preuve :** `pipelines/ingest_bronze.py`

### Réconciliation des données : RQ-021 et contrôle d'intégrité

| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Écart de contrôle des empreintes |
|---|---:|---:|---:|---:|
| crm_client | 100000 | 100000 | 0 | 0 |
| crm_contrat | 100000 | 100000 | 0 | 0 |
| crm_sinistre | 100000 | 100000 | 0 | 0 |
| crm_type_contrat | 12 | 12 | 0 | 0 |
| cif_clients | 40000 | 40000 | 0 | 0 |
| cif_compte | 45000 | 45000 | 0 | 0 |
| cif_pays | 250 | 250 | 0 | 0 |

**Résultat : 7 tables conformes sur 7. Porte B : GO.**

La réconciliation ne révèle aucun écart de comptage ni d'empreinte entre les données sources et les données Bronze pour le lot contrôlé.

Les résultats des contrôles sont enregistrés dans `dq.dq_history`, avec notamment les mesures RQ-021 et RQ-022.

**Preuves :**
- `pipelines/check_gate_b.py`
- `reports/S1_gate_b.sql`

### Épreuves de la porte B

| Épreuve | Résultat obtenu | Preuve |
|---|---|---|
<<<<<<< HEAD
| Relance du même lot : doublons créés | 0 doublon. Après une deuxième ingestion du lot L-2026-10-01, chaque table bronze garde le même nombre de lignes : 100 000 (crm_client, crm_contrat, crm_sinistre), 12 (crm_type_contrat), 40 000 (cif_clients), 45 000 (cif_compte) et 250 (cif_pays). | `notebooks/S1_US02_Fatine.ipynb`, cellule 5 |
| Écart introduit volontairement sur une copie : la porte échoue-t-elle ? | Oui. Sur une copie de test de crm_client, la porte B échoue dans les 3 cas : une valeur modifiée (écart de comptage 0, mais somme de contrôle différente), une ligne supprimée (écart de comptage -1) et une ligne en double (écart de comptage +1). La copie non modifiée passe la porte. Le vrai bronze n'est jamais modifié. | `notebooks/S1_US02_Fatine.ipynb`, cellule 8 |
| Un problème de conversion rencontré (décimales, NULL, accents) et sa correction | Décimales : lue sans option, une prime dont la deuxième décimale est 0 perd ce zéro (CT0000020 : 184.10 devient 184.1). 9 912 primes sur 100 000 dans crm.contrat sont concernées, ce qui ferait échouer la somme de contrôle de la porte B. Correction : lecture avec `coerce_float=False`, la valeur reste 184.10 dans bronze et la porte B affiche 0 écart. | `notebooks/S1_US02_Fatine.ipynb`, cellules 6 et 7 |
=======
| Relance du même lot | Le contrôle des volumes montre 385262 lignes Bronze, sans dépassement des volumes sources. La preuve d'une seconde exécution reste à confirmer. | `pipelines/ingest_bronze.py` |
| Écart introduit volontairement sur une copie | NO-GO détecté après modification d'une valeur sans actualisation de son empreinte. | `pipelines/check_gate_b_negative_test.py` |
| Problème de conversion | Les colonnes anonymes du CIF sont conservées sous forme textuelle afin d'éviter des conversions prématurées. | `pipelines/ingest_bronze.py` |

Le test négatif a été réalisé sur une copie de `bronze.crm_type_contrat`. La valeur d'un libellé a été modifiée sans recalcul de `_row_hash`, ce qui a entraîné un résultat NO-GO. La table Bronze d'origine n'a pas été modifiée.
>>>>>>> 72dc2deba2ec32a09b9300dfafe8a8b5dde5fd46

## 3. Profil de crm.client (US-06, US-07)

Le profilage porte sur les 100000 lignes de la table `crm.client`.

### Constats chiffrés

| N° | Colonne | Indicateur | Valeur mesurée | Ce que cela change pour la qualité |
|---|---|---|---|---|
| 1 | client_id | Unicité | 100000 identifiants uniques sur 100000 lignes | Aucun doublon de clé primaire détecté |
| 2 | email | Valeurs vides | 19365 (19,37 %) | Certains clients ne peuvent pas être contactés par email |
| 3 | email | Format invalide | 1210 (1,21 %) | Une validation des adresses est nécessaire |
| 4 | telephone | Hors format français initial | 23531 (23,53 %) | Une normalisation des formats est nécessaire |
| 5 | pays | Modalités distinctes | 18 | Les codes pays doivent être harmonisés |

### Contrôle des motifs

| Attribut | Motif testé | Lignes conformes | Lignes non conformes | Exemple hors motif |
|---|---|---:|---:|---|
| Code postal | `^[0-9]{5}$` | 97683 | 2317 | `SW1A 1AA` |
| Téléphone | `^0[0-9]{9}$` | 66470 | 23531 | `04.89.95.86.69` |
| Pays | Référentiel de codes pays à normaliser | À mesurer après validation du référentiel | À mesurer après validation du référentiel | `Frnace` |

Pour le téléphone, les 9999 valeurs vides sont exclues du contrôle de format.

Les contrôles de code postal et de téléphone utilisent des motifs français. Une valeur hors motif ne constitue donc pas nécessairement une erreur pour un client international.

### Analyse complémentaire des téléphones

Parmi les 23531 numéros initialement hors format français, 21271 deviennent conformes après normalisation des séparateurs et du préfixe international `+33`.

Cela représente environ 90,4 % des numéros initialement hors format.

Il reste 2260 numéros hors format après cette normalisation. Ces valeurs doivent faire l'objet d'une analyse complémentaire, notamment selon le pays du client.

### Analyse des pays

La colonne `pays` contient 18 modalités distinctes.

Plusieurs valeurs désignent la France sous des formes différentes :

- `FR` : 95437 lignes
- `France` : 1200 lignes
- `F` : 600 lignes
- `fr` : 400 lignes
- `Frnace` : 400 lignes

Par ailleurs, 400 lignes présentent une valeur vide pour le pays.

Ces différences nécessitent une harmonisation avec un référentiel de pays avant les traitements Silver.

### Analyse des valeurs manquantes

Les colonnes `nom`, `prenom` et `date_naissance` présentent chacune 4277 valeurs manquantes.

Ces 4277 lignes correspondent aux personnes morales présumées, identifiées par une `raison_sociale` renseignée.

Ces absences ne doivent donc pas être considérées automatiquement comme des anomalies : elles peuvent être cohérentes avec la nature juridique du client.

**Preuve :** `reports/S1_profilage_crm_client.sql`

## 4. Dictionnaire du CIF (US-04)

La table `cif.clients` contient 40000 lignes et dix colonnes anonymes, nommées de `column0` à `column9`.

Le profilage permet de proposer le dictionnaire suivant.

| Colonne d'origine | Nom proposé | Type | Justification chiffrée |
|---|---|---|---|
| column0 | id_client | VARCHAR(20) | 40000 identifiants uniques, 0 valeur vide |
| column1 | nom | VARCHAR(100) | 0 valeur vide |
| column2 | prenom | VARCHAR(100) | 645 valeurs vides |
| column3 | date_naissance | DATE | 645 valeurs vides, 0 format invalide parmi les valeurs renseignées |
| column4 | adresse | VARCHAR(255) | 0 valeur vide |
| column5 | code_postal | VARCHAR(10) | 341 valeurs hors motif français |
| column6 | ville | VARCHAR(100) | 0 valeur vide |
| column7 | code_pays | VARCHAR(2) | 9 pays distincts, tous présents dans `cif.pays` |
| column8 | telephone | VARCHAR(20) | 6324 valeurs vides (15,81 %) |
| column9 | email | VARCHAR(255) | 18872 valeurs vides (47,18 %) |

### Décisions de typage

- `date_naissance` : convertir les dates du format `JJ/MM/AAAA` vers le type DATE dans Silver.
- `code_postal` : conserver le type VARCHAR pour préserver les zéros initiaux et les formats internationaux.
- `telephone` : conserver le type VARCHAR pour préserver les préfixes et les séparateurs.
- `code_pays` : contrôler les valeurs à partir du référentiel `cif.pays`.

Les noms et les types proposés constituent un dictionnaire de travail qui devra être validé avant les transformations Silver.

**Preuve :** `reports/S1_dictionnaire_cif.sql`


## 5. Trois définitions du « client actif » (US-09)

Date de référence : 01/10/2026.

Population étudiée : souscripteurs distincts (`souscripteur_id`).

### Définition officielle CD-001

Selon la règle RQ-018, un client actif doit avoir un contrat en cours ET une cotisation à jour sur les trois derniers mois, à la date de référence du lot.

Le calcul réalisé à partir de `crm.contrat` donne **38049 clients actifs selon CD-001**.

### Comparaison des définitions métier

| Direction | Définition utilisée | Nombre de clients | Écart numérique avec CD-001 |
|---|---|---:|---:|
| Commerciale | Au moins un contrat en vigueur | 44116 | +6067 |
| Sinistres | Au moins un sinistre déclaré durant les 12 derniers mois | 30617 | -7432 |
| Risques | Contrat en vigueur ET sinistre déclaré durant les 12 derniers mois | 29976 | -8073 |
| Référence CD-001 | Contrat en vigueur ET cotisation à jour sur 3 mois | 38049 | 0 |

Les écarts numériques sont calculés par rapport aux 38049 clients actifs selon CD-001. Ils comparent les volumes obtenus, sans représenter nécessairement le nombre de clients individuels classés différemment.

### Conséquence pour la gouvernance

Les trois directions utilisent des critères différents pour définir un client actif.

Les résultats varient de 29976 à 44116 clients, soit un écart maximal de 14140 clients.

La définition officielle CD-001 doit être appliquée de manière identique par les trois directions afin de garantir la cohérence des indicateurs publiés dans le CRM cible.

**Preuves :**
- `reports/S1_client_actif.sql`
- `initdb/02_dq_regles.sql` (RQ-018 / CD-001)


## 6. Critères de fin

- [x] Les sept tables Bronze existent et les quatre métadonnées d'ingestion sont prévues pour chaque ligne.
  Preuve : `pipelines/ingest_bronze.py`, `pipelines/check_gate_b.py`.

- [x] La porte B ne montre aucun écart de comptage ni de contrôle des empreintes.
  Preuve : `reports/S1_gate_b.sql`, `pipelines/check_gate_b.py`.

<<<<<<< HEAD
- [X ] Les sept tables bronze existent et chaque ligne porte ses quatre métadonnées.
- [X ] La porte B ne montre aucun écart de comptage ni de somme de contrôle.
- [ X] Relancer l'ingestion du même lot ne crée aucun doublon.
- [ ] Un écart introduit volontairement fait échouer la porte.
- [ X] RQ-021 est écrite dans `dq.dq_history` (couche BRONZE).
=======
- [ ] Relancer l'ingestion du même lot ne crée aucun doublon.
  Le volume Bronze contrôlé est de 385262 lignes. La confirmation d'une seconde exécution reste à documenter.
  Preuve : `pipelines/ingest_bronze.py`.

- [x] Un écart introduit volontairement fait échouer la porte B.
  Preuve : `pipelines/check_gate_b_negative_test.py`.

- [x] RQ-021 est enregistrée dans `dq.dq_history` pour la couche BRONZE.
  Preuve : `pipelines/check_gate_b.py`, `reports/S1_gate_b.sql`.
>>>>>>> 72dc2deba2ec32a09b9300dfafe8a8b5dde5fd46

## 7. Difficultés, écarts avec l'attendu, reprise

### Difficultés rencontrées

- Configuration et utilisation de Docker, MariaDB et PowerShell.
- Identification des dix colonnes anonymes de la table `cif.clients`.
- Analyse des différences de formats dans les numéros de téléphone, les codes postaux et les pays.
- Vérification de l'intégrité des données entre les sources et Bronze.

### Point de reprise utilisé

Les scripts Python et SQL enregistrés dans le dépôt permettent de reprendre les opérations et les contrôles sans recommencer les analyses manuellement.

### Ce que nous ferions autrement

Nous automatiserions davantage les contrôles de qualité et documenterions les règles de normalisation dès le début du projet.

Nous conserverions également les résultats des tests de relance et des tests négatifs dans des fichiers de preuve dédiés afin de faciliter la validation des portes de qualité.