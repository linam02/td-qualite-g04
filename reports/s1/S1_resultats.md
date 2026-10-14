# Résultats S1 (générés par pipelines/S1_g04_mesures.py)

Lot `L-2026-10-01` · date de référence `2026-10-01` · exécuté le 2026-10-14T14:22:43


## US-01 · Inventaire des sources

| Source | Table | Lignes | Colonnes | Clé primaire | Doublons de clé | Observation chiffrée |
|---|---|---|---|---|---|---|
| crm | client | 100000 | 13 | client_id | 0 | NULL : raison_sociale 95723 (95.7 %), email 19365 (19.4 %), telephone 5999 (6.0 %) ; doublons de clé : 0 |
| crm | contrat | 100000 | 9 | contrat_id | 0 | NULL : date_derniere_cotisation 7460 (7.5 %) ; doublons de clé : 0 |
| crm | sinistre | 100000 | 10 | sinistre_id | 0 | aucun NULL ; doublons de clé : 0 |
| crm | type_contrat | 12 | 3 | code_type | 0 | aucun NULL ; doublons de clé : 0 |
| cif | clients | 40000 | 10 | column0 | 0 | NULL : column9 18872 (47.2 %), column8 6324 (15.8 %), column2 645 (1.6 %) ; doublons de clé : 0 |
| cif | compte | 45000 | 4 | column0 | 0 | aucun NULL ; doublons de clé : 0 |
| cif | pays | 250 | 2 | code_pays | 0 | aucun NULL ; doublons de clé : 0 |


## US-01 · Observations complémentaires (sources)

| Observation | Valeur |
|---|---|
| contrat.assure_id = '0' (valeur sentinelle) | 40000 |
| contrat.souscripteur_id absent de crm.client | 1000 |
| contrat.code_type absent de type_contrat | 200 |
| sinistre.contrat_id absent de contrat | 0 |
| cif.compte.column1 absent de cif.clients.column0 | 0 |
| crm.client : personnes morales (raison_sociale renseignée, nom NULL) | 4277 |


## US-02 · Ingestion bronze

| Table bronze | Lignes écrites | Lignes du lot remplacées |
|---|---|---|
| crm_client | 100000 | 0 |
| crm_contrat | 100000 | 0 |
| crm_sinistre | 100000 | 0 |
| crm_type_contrat | 12 | 0 |
| cif_clients | 40000 | 0 |
| cif_compte | 45000 | 0 |
| cif_pays | 250 | 0 |


## US-03 · Porte B (RQ-021 comptage + somme de contrôle + lignes, RQ-022 métadonnées)

| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Somme de contrôle source | Somme de contrôle bronze | Écart de somme de contrôle | Lignes sans jumelle | RQ-022 lignes sans métadonnées valides | Porte B |
|---|---|---|---|---|---|---|---|---|---|
| crm_client | 100000 | 100000 | 0 | 214528576956306 | 214528576956306 | 0 | 0 | 0 | OK |
| crm_contrat | 100000 | 100000 | 0 | 214970337491057 | 214970337491057 | 0 | 0 | 0 | OK |
| crm_sinistre | 100000 | 100000 | 0 | 214902603302661 | 214902603302661 | 0 | 0 | 0 | OK |
| crm_type_contrat | 12 | 12 | 0 | 27536952762 | 27536952762 | 0 | 0 | 0 | OK |
| cif_clients | 40000 | 40000 | 0 | 85973760448678 | 85973760448678 | 0 | 0 | 0 | OK |
| cif_compte | 45000 | 45000 | 0 | 96842431909202 | 96842431909202 | 0 | 0 | 0 | OK |
| cif_pays | 250 | 250 | 0 | 529205112408 | 529205112408 | 0 | 0 | 0 | OK |


## US-03 · Dernières mesures dans dq.dq_history (couche BRONZE)

| id | batch_id | couche | rule_id | table_cible | nb_testees | nb_echecs | taux_conformite | mesure_le |
|---|---|---|---|---|---|---|---|---|
| 23 | L-2026-10-01 | BRONZE | RQ-021 | bronze.cif_clients | 40000 | 0 | 100.0 | 2026-10-14 14:25:25 |
| 25 | L-2026-10-01 | BRONZE | RQ-021 | bronze.cif_compte | 45000 | 0 | 100.0 | 2026-10-14 14:25:26 |
| 27 | L-2026-10-01 | BRONZE | RQ-021 | bronze.cif_pays | 250 | 0 | 100.0 | 2026-10-14 14:25:26 |
| 15 | L-2026-10-01 | BRONZE | RQ-021 | bronze.crm_client | 100000 | 0 | 100.0 | 2026-10-14 14:25:17 |
| 17 | L-2026-10-01 | BRONZE | RQ-021 | bronze.crm_contrat | 100000 | 0 | 100.0 | 2026-10-14 14:25:21 |
| 19 | L-2026-10-01 | BRONZE | RQ-021 | bronze.crm_sinistre | 100000 | 0 | 100.0 | 2026-10-14 14:25:24 |
| 21 | L-2026-10-01 | BRONZE | RQ-021 | bronze.crm_type_contrat | 12 | 0 | 100.0 | 2026-10-14 14:25:24 |
| 24 | L-2026-10-01 | BRONZE | RQ-022 | bronze.cif_clients | 40000 | 0 | 100.0 | 2026-10-14 14:25:25 |
| 26 | L-2026-10-01 | BRONZE | RQ-022 | bronze.cif_compte | 45000 | 0 | 100.0 | 2026-10-14 14:25:26 |
| 28 | L-2026-10-01 | BRONZE | RQ-022 | bronze.cif_pays | 250 | 0 | 100.0 | 2026-10-14 14:25:26 |
| 16 | L-2026-10-01 | BRONZE | RQ-022 | bronze.crm_client | 100000 | 0 | 100.0 | 2026-10-14 14:25:17 |
| 18 | L-2026-10-01 | BRONZE | RQ-022 | bronze.crm_contrat | 100000 | 0 | 100.0 | 2026-10-14 14:25:21 |
| 20 | L-2026-10-01 | BRONZE | RQ-022 | bronze.crm_sinistre | 100000 | 0 | 100.0 | 2026-10-14 14:25:24 |
| 22 | L-2026-10-01 | BRONZE | RQ-022 | bronze.crm_type_contrat | 12 | 0 | 100.0 | 2026-10-14 14:25:24 |


## Épreuve 1 · Relance du même lot

| Table bronze | Lignes du lot avant relance | Après relance | Lignes créées par la relance | Empreintes en double dans le lot | dont doublons déjà présents en source |
|---|---|---|---|---|---|
| crm_client | 100000 | 100000 | 0 | 0 | 0 |
| crm_contrat | 100000 | 100000 | 0 | 0 | 0 |
| crm_sinistre | 100000 | 100000 | 0 | 0 | 0 |
| crm_type_contrat | 12 | 12 | 0 | 0 | 0 |
| cif_clients | 40000 | 40000 | 0 | 0 | 0 |
| cif_compte | 45000 | 45000 | 0 | 0 | 0 |
| cif_pays | 250 | 250 | 0 | 0 | 0 |


## Épreuve 2 · Porte B sur une copie altérée (1 valeur modifiée, 1 ligne supprimée)

| Table bronze | Lignes source | Lignes bronze | Écart de comptage | Somme de contrôle source | Somme de contrôle bronze | Écart de somme de contrôle | Lignes sans jumelle | RQ-022 lignes sans métadonnées valides | Porte B |
|---|---|---|---|---|---|---|---|---|---|
| epreuve_crm_client | 100000 | 99999 | -1 | 214528576956306 | 214524096630065 | -4480326241 | 3 | 1 | ÉCHEC |


## Épreuve 3 · Écarts d'une lecture naïve (SELECT * puis astype(str)) par rapport à la source

| Table | Colonne | Cellules altérées | Valeur source (\N = NULL) | Lecture naïve |
|---|---|---|---|---|
| crm.client | nom | 4277 | \N | None |
| crm.client | prenom | 4277 | \N | None |
| crm.client | raison_sociale | 95723 | \N | None |
| crm.client | date_naissance | 4277 | \N | None |
| crm.client | telephone | 5999 | \N | None |
| crm.client | email | 19365 | \N | None |
| crm.contrat | prime_annuelle | 9912 | 184.10 | 184.1 |
| crm.contrat | date_derniere_cotisation | 7460 | \N | None |
| crm.sinistre | montant_estime | 10083 | 1007.80 | 1007.8 |
| cif.clients | column2 | 645 | \N | None |
| cif.clients | column3 | 645 | \N | None |
| cif.clients | column8 | 6324 | \N | None |
| cif.clients | column9 | 18872 | \N | None |


## US-06 · Profil colonne par colonne de crm.client (BRONZE)

| Colonne | Lignes | nuls | vides | blancs | espaces_parasites | distincts | lg_min | lg_max | % nuls |
|---|---|---|---|---|---|---|---|---|---|
| client_id | 100000 | 0 | 0 | 0 | 0 | 100000 | 6 | 7 | 0.0 |
| type_personne | 100000 | 0 | 0 | 0 | 0 | 8 | 6 | 12 | 0.0 |
| nom | 100000 | 4277 | 0 | 0 | 0 | 784 | 3 | 9 | 4.28 |
| prenom | 100000 | 4277 | 0 | 0 | 0 | 293 | 2 | 10 | 4.28 |
| raison_sociale | 100000 | 95723 | 0 | 0 | 0 | 3229 | 12 | 27 | 95.72 |
| date_naissance | 100000 | 4277 | 0 | 0 | 0 | 28413 | 10 | 10 | 4.28 |
| adresse | 100000 | 0 | 0 | 0 | 0 | 7561 | 10 | 31 | 0.0 |
| cp | 100000 | 0 | 0 | 0 | 0 | 230 | 4 | 8 | 0.0 |
| ville | 100000 | 0 | 0 | 0 | 0 | 172 | 3 | 24 | 0.0 |
| pays | 100000 | 0 | 400 | 0 | 0 | 18 | 0 | 6 | 0.0 |
| telephone | 100000 | 5999 | 2000 | 2000 | 0 | 88702 | 0 | 17 | 6.0 |
| email | 100000 | 19365 | 0 | 0 | 0 | 77795 | 13 | 36 | 19.36 |
| date_creation | 100000 | 0 | 0 | 0 | 0 | 5391 | 10 | 10 | 0.0 |


## US-06 · Domaine de type_personne (attendu : prospect, souscripteur, assure)

| valeur | lignes |
|---|---|
| souscripteur | 49898 |
| assure | 28944 |
| prospect | 20958 |
| client | 60 |
| Souscripteur | 50 |
| assuré | 40 |
| SOUSCRIPTEUR | 30 |
| prosp. | 20 |


## US-06 · Valeurs de pays (crochets pour voir les espaces)

| valeur | lignes |
|---|---|
| [FR] | 95437 |
| [France] | 1200 |
| [F] | 600 |
| [fr] | 400 |
| [] | 400 |
| [Frnace] | 400 |
| [ES] | 243 |
| [IT] | 231 |
| [CH] | 227 |
| [DE] | 222 |
| [BE] | 216 |
| [LU] | 125 |
| [GB] | 125 |
| [PT] | 124 |
| [UK] | 20 |


## US-06 · Constats chiffrés sur crm.client (BRONZE)

| Colonne | Indicateur | Valeur |
|---|---|---|
| type_personne | hors domaine {prospect, souscripteur, assure} (NULL inclus) | 200 |
| telephone | NULL / vide / blanc | 5999 / 2000 / 2000 |
| nom / raison_sociale | personnes morales (nom NULL, raison_sociale renseignée) | 4277 |
| nom / raison_sociale | ni nom ni raison sociale | 0 |
| date_naissance | personnes physiques sans date de naissance | 0 |
| date_naissance | min / max | 1938-04-11 / 2026-07-13 |
| date_naissance | postérieure à la date de référence 2026-10-01 ou avant 1900 | 0 |
| client_id | hors motif ^[AHS]-[0-9]+$ | 0 |
| pays | valeurs distinctes (NULL exclu) | 18 |
| email | renseigné mais hors motif simple x@y.zz | 1210 |
| nom + prenom + date_naissance | lignes en double, NULL écartés (personnes physiques) | 738 |
| nom + prenom + date_naissance | même calcul SANS écarter les NULL (piège : les personnes morales se comptent entre elles) | 5014 |


## US-07 · Motifs (BRONZE, crm.client)

| Attribut | Motif testé | Périmètre (lignes) | Conformes | Non conformes | % conformes | Exemples non conformes (fréquence) |
|---|---|---|---|---|---|---|
| Code postal (RQ-005) | ^[0-9]{5}$, pays = 'FR' exactement | 95437 | 93981 | 1456 | 98.47 | [1000] ×92; [1100] ×77; [1360] ×74 |
| Code postal | ^[0-9]{5}$, adresse en France (FR, France, fr après TRIM/UPPER) | 97037 | 95559 | 1478 | 98.48 | [1000] ×92; [1100] ×78; [1360] ×75 |
| Code postal | ^[0-9]{5}$, toutes adresses | 100000 | 97683 | 2317 | 97.68 | [1000] ×199; [SW1A 1AA] ×125; [1009] ×125 |
| Téléphone (brut) | ^0[1-9][0-9]{8}$, adresse en France | 97037 | 65495 | 31542 | 67.49 | [NULL] ×5820; [   ] ×1945; [] ×1936 |
| Téléphone (normalisé) | ^0[1-9][0-9]{8}$ après nettoyage, adresse en France | 97037 | 86470 | 10567 | 89.11 | [NULL] ×5820; [   ] ×1945; [] ×1936 |
| Pays (format) | ^[A-Z]{2}$ | 100000 | 97000 | 3000 | 97.0 | [France] ×1200; [F] ×600; [fr] ×400 |
| Pays (référentiel) | code présent dans silver.ref_pays | 100000 | 96950 | 3050 | 96.95 | [France] ×1200; [F] ×600; [Frnace] ×400 |


## US-07 · Détail des codes postaux non conformes (adresse en France)

| Code postal, adresse en France | Lignes |
|---|---|
| NULL | 0 |
| vide ou blanc | 0 |
| 4 chiffres (zéro initial perdu ?) | 1478 |
| autre format | 0 |


## US-04 · Profil des colonnes anonymes de cif_clients (BRONZE)

| Colonne | Lignes | % NULL ou vide | Distincts | % uniques | Long. min-max | % identifiant (unique, chiffres) | % date JJ/MM/AAAA | % date AAAA-MM-JJ | % code postal 5 chiffres | % téléphone | % e-mail | % code pays ISO2 | % adresse (numéro + voie) | % code 1 caractère | % texte alphabétique |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| column0 | 40000 | 0.0 | 40000 | 100.0 | 7-7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column1 | 40000 | 0.0 | 731 | 1.8 | 3-31 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 99.6 |
| column2 | 40000 | 1.6 | 180 | 0.5 | 3-10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 |
| column3 | 40000 | 1.6 | 21081 | 53.6 | 10-10 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column4 | 40000 | 0.0 | 9811 | 24.5 | 11-31 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 |
| column5 | 40000 | 0.0 | 188 | 0.5 | 4-8 | 99.8 | 0.0 | 0.0 | 99.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column6 | 40000 | 0.0 | 172 | 0.4 | 3-24 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 |
| column7 | 40000 | 0.0 | 9 | 0.0 | 2-2 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 100.0 |
| column8 | 40000 | 15.8 | 33676 | 100.0 | 10-10 | 100.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column9 | 40000 | 47.2 | 21128 | 100.0 | 18-35 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 |


## US-04 · Profil des colonnes anonymes de cif_compte (BRONZE)

| Colonne | Lignes | % NULL ou vide | Distincts | % uniques | Long. min-max | % identifiant (unique, chiffres) | % date JJ/MM/AAAA | % date AAAA-MM-JJ | % code postal 5 chiffres | % téléphone | % e-mail | % code pays ISO2 | % adresse (numéro + voie) | % code 1 caractère | % texte alphabétique |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| column0 | 45000 | 0.0 | 45000 | 100.0 | 10-10 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column1 | 45000 | 0.0 | 40000 | 88.9 | 7-7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column2 | 45000 | 0.0 | 7920 | 17.6 | 10-10 | 0.0 | 0.0 | 100.0 | 0.0 | 100.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| column3 | 45000 | 0.0 | 2 | 0.0 | 1-1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 100.0 | 100.0 |


## US-04 · Dictionnaire proposé du CIF (à relire et valider par le Data Steward)

| Table | Colonne d'origine | Nom proposé | Type | Justification chiffrée | % NULL ou vide |
|---|---|---|---|---|---|
| cif.clients | column0 | id_cif | VARCHAR(10) (clé) | 100.0 % de valeurs uniques, 40000 distincts, longueur 7-7, aucun format métier reconnu | 0.0 |
| cif.clients | column1 | nom_ou_raison_sociale | VARCHAR | 99.6 % alphabétique, 731 distincts ; recouvrement avec crm.client : nom ou raison sociale 98.4 %, prenom 11.6 %, ville 0.8 % | 0.0 |
| cif.clients | column2 | prenom | VARCHAR | 100.0 % alphabétique, 180 distincts ; recouvrement avec crm.client : nom ou raison sociale 17.9 %, prenom 100.0 %, ville 0.0 % | 1.6 |
| cif.clients | column3 | date_naissance | DATE (texte JJ/MM/AAAA à convertir) | 100.0 % au format JJ/MM/AAAA, années 1938 à 2026 | 1.6 |
| cif.clients | column4 | adresse | VARCHAR(255) | 100.0 % commencent par un numéro suivi d'un libellé de voie | 0.0 |
| cif.clients | column5 | code_postal | CHAR(5) | 99.1 % de valeurs à 5 chiffres, 188 distincts | 0.0 |
| cif.clients | column6 | ville | VARCHAR | 100.0 % alphabétique, 172 distincts ; recouvrement avec crm.client : nom ou raison sociale 0.4 %, prenom 0.0 %, ville 83.3 % | 0.0 |
| cif.clients | column7 | code_pays | CHAR(2) | 100.0 % de codes à 2 majuscules, 100.0 % présents dans cif.pays, 9 distincts | 0.0 |
| cif.clients | column8 | telephone | VARCHAR(20) | 100.0 % de valeurs numériques de 9 caractères ou plus, 100.0 % au format 0X XX XX XX XX | 15.8 |
| cif.clients | column9 | email | VARCHAR(150) | 100.0 % au motif x@y.zz | 47.2 |
| cif.compte | column0 | id_compte | VARCHAR (clé primaire) | 100.0 % de valeurs uniques, longueur 10-10 | 0.0 |
| cif.compte | column1 | id_cif | VARCHAR (clé étrangère vers cif.clients.column0) | 100.0 % des valeurs existent dans cif.clients.column0 ; 88.9 % uniques (plusieurs comptes par client) | 0.0 |
| cif.compte | column2 | date_ouverture | DATE | 100.0 % au format AAAA-MM-JJ, de 2005-01-01 à 2026-09-30 | 0.0 |
| cif.compte | column3 | statut | CHAR(1) | 100.0 % d'un seul caractère ; domaine : O=39611, F=5389 | 0.0 |


## US-09 · Client actif au 2026-10-01, cotisation depuis le 2026-07-01 (souscripteurs distincts, crm)

| Direction | Définition utilisée | Nombre de clients | Écart avec CD-001 | Dans la direction mais pas CD-001 | Dans CD-001 mais pas la direction | Rapport à la plus large |
|---|---|---|---|---|---|---|
| Commerciale | au moins un contrat (quel que soit son état) | 50508 | 12459 | 12459 | 0 | 1.0 |
| Sinistres | un contrat en cours à la date de référence (début ≤ date ≤ fin) | 44116 | 6067 | 6067 | 0 | 0.873 |
| Risques | CD-001 : un contrat en cours ET une cotisation à jour sur les trois derniers mois | 38049 | 0 | 0 | 0 | 0.753 |


## US-09 · Bornes des dates de crm.contrat (pour vérifier que la date de référence est cohérente)

| debut_min | debut_max | fin_max | cotis_max |
|---|---|---|---|
| 2009-08-10 | 2026-10-01 | 2036-09-23 | 2026-10-01 |

