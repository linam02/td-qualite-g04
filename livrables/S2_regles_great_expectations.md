# S2 · Great Expectations : des règles en tests automatisés

**Groupe :** G04  
**Date :** 22/10/2026  
**Rédacteur :** Groupe 04  
**Étiquette :** `seance-2`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Règles en tests (US-10)

Sept règles de qualité ont été implémentées avec Great Expectations et exécutées sur les données Bronze du lot `S1_G04_001`.

Chaque test contient l'identifiant de sa règle (`rule_id`). Les résultats permettent de mesurer le nombre de lignes contrôlées, le nombre d'échecs et le taux de conformité.

| Règle | Table bronze | Expectation (type) | Lignes testées | Lignes en échec | Taux de réussite | Sévérité retenue |
|---|---|---|---:|---:|---:|---|
| RQ-001 | crm_contrat | Cohérence des dates : date_fin > date_debut | 100 000 | 800 | 99,200 % | Bloquante |
| RQ-002 | crm_contrat | Souscripteur majeur à la date de début du contrat | 92 996 | 301 | 99,676 % | Bloquante |
| RQ-003 | crm_contrat | Téléphone renseigné : ni NULL, ni vide, ni blanc | 99 000 | 12 024 | 87,855 % | Avertissement |
| RQ-005 | crm_client | Code postal français composé de cinq chiffres | 98 037 | 1 493 | 98,477 % | Avertissement |
| RQ-009 | crm_client | Valeur de type_personne appartenant au référentiel autorisé | 100 000 | 200 | 99,800 % | Bloquante |
| RQ-010 | crm_contrat | Durée de garantie appartenant aux valeurs autorisées | 100 000 | 600 | 99,400 % | Bloquante |
| RQ-020 | 7 tables Bronze | Unicité et non-nullité des clés | 385 262 | 0 | 100,000 % | Bloquante |

**Précisions sur le périmètre :**

- RQ-002 : seules les personnes physiques disposant des informations nécessaires sont évaluées.
- RQ-003 : les contrats dont le souscripteur est introuvable sont exclus de cette mesure.
- RQ-005 : seuls les enregistrements identifiés comme des adresses françaises sont concernés.
- RQ-009 : valeurs autorisées `prospect`, `souscripteur`, `assure`.
- RQ-010 : durées autorisées `12`, `24`, `36`, `60` mois.
- RQ-020 : contrôle réalisé sur les sept tables Bronze.

### Pièges rencontrés et traitement

| Règle | Piège | Chiffre avant correction | Chiffre après correction | Preuve |
|---|---|---:|---:|---|
| RQ-003 | La vérification des seules valeurs NULL oublie les chaînes vides et les espaces | 4 047 | 12 024 | `reports/S2_pieges_comparaison.sql` |
| RQ-005 | Le contrôle du code postal français était appliqué à tort aux adresses étrangères | 2 317 | 1 493 | `reports/S2_pieges_comparaison.sql` |
| RQ-009 | Une comparaison souple ne détecte pas certaines différences de casse ou d'accents | 80 | 200 | `reports/S2_pieges_comparaison.sql` |

Ces corrections concernent la logique de détection des anomalies et non la modification des données sources.

Pour RQ-003, le contrôle a été élargi aux valeurs NULL, vides et composées uniquement d'espaces. Cela permet de détecter 7 977 anomalies supplémentaires.

Pour RQ-005, le contrôle a été limité aux adresses françaises afin de ne pas considérer les codes postaux étrangers comme des erreurs.

Pour RQ-009, une comparaison exacte a été utilisée afin de respecter strictement les valeurs autorisées.

### Suites de validation (chemins)

- `great_expectations/test_rq001.py`
- `great_expectations/test_rq002.py`
- `great_expectations/test_rq003.py`
- `great_expectations/test_rq005.py`
- `great_expectations/test_rq009.py`
- `great_expectations/test_rq010.py`
- `great_expectations/test_rq020.py`

Les sept scripts ont été exécutés sur le lot `S1_G04_001`.

La connexion à la base et le lot peuvent être configurés. La possibilité de changer la table cible sans modification du code reste à finaliser.

## 2. Lignes en échec (US-11)

**Export complet :** `reports/S2_erreurs/`

Les six fichiers CSV contiennent au total 15 418 occurrences d'échec de règles :

- `RQ-001_erreurs.csv` : 800 lignes
- `RQ-002_erreurs.csv` : 301 lignes
- `RQ-003_erreurs.csv` : 12 024 lignes
- `RQ-005_erreurs.csv` : 1 493 lignes
- `RQ-009_erreurs.csv` : 200 lignes
- `RQ-010_erreurs.csv` : 600 lignes

Le total correspond aux échecs cumulés des règles et non nécessairement à un nombre de lignes distinctes.

**Échantillon commenté de 20 lignes :** `reports/S2_erreurs/echantillon_20.csv`

| Règle | Famille d'erreur observée | Nombre de lignes de l'échantillon | Cause probable | Action proposée (à qui ?) |
|---|---|---:|---|---|
| RQ-001 | Dates de contrat incohérentes | 4 | Erreur de saisie ou de gestion des dates | Vérifier et corriger les dates (Data Owner) |
| RQ-002 | Souscripteurs mineurs au début du contrat | 4 | Contrôle de l'âge insuffisant lors de la souscription | Renforcer la validation métier (Data Owner) |
| RQ-003 | Téléphone NULL, vide ou blanc | 4 | Information manquante ou mal renseignée | Compléter les coordonnées et contrôler la saisie (Data Steward) |
| RQ-005 | Codes postaux français invalides | 3 | Erreur de format ou perte possible d'un zéro initial | Vérifier les codes postaux et imposer un format à cinq chiffres (Data Steward) |
| RQ-009 | Types de personne non autorisés | 3 | Différences de casse, d'accents ou valeur hors référentiel | Normaliser les valeurs et contrôler le référentiel (Data Steward) |
| RQ-010 | Durées de garantie non autorisées | 2 | Valeur hors domaine métier | Vérifier les durées et appliquer la liste autorisée (Data Owner) |

Les 20 lignes ont été sélectionnées parmi les six familles d'anomalies.

Les causes indiquées sont des hypothèses qui devront être confirmées auprès des responsables des données.

Les exports complets permettent de retrouver les enregistrements concernés et de préparer les corrections.

## 3. Âge à la date de début du contrat (US-13, RQ-002)

La règle RQ-002 vérifie qu'un souscripteur personne physique a au moins 18 ans au moment du début du contrat.

Deux méthodes de calcul ont été comparées sur 92 996 contrats évaluables.

| Date de référence | Définition de l'âge | Lignes en échec | Preuve |
|---|---|---:|---|
| Date de début du contrat | Âge calculé entre la naissance et le début du contrat | 301 | `reports/S2_comparaison_age.sql` |
| Date du jour | Âge calculé entre la naissance et la date actuelle | 149 | `reports/S2_comparaison_age.sql` |

**Exemple concret : contrat CT0000387**

- Date de naissance : 28/09/1996
- Date de début du contrat : 01/09/2014
- Âge au début du contrat : 17 ans
- Âge à la date du contrôle : 30 ans

Ce souscripteur était mineur lors de la prise d'effet du contrat, mais il est majeur aujourd'hui.

La méthode fondée sur la date actuelle détecte 152 non-conformités de moins que celle fondée sur la date de début du contrat.

**Conclusion :** la règle RQ-002 doit utiliser la date de début du contrat. L'utilisation de la date du jour ne permet pas de détecter toutes les non-conformités historiques.

## 4. Mesure de référence sur bronze (US-15)

Les mesures de qualité ont été enregistrées dans la table `dq.dq_history`.

- **Couche :** BRONZE
- **Lot :** `S1_G04_001`
- **Nombre de règles :** 7
- **Nombre de mesures enregistrées pour ces règles :** 13

### Synthèse par dimension

| Dimension | Règles | Taux moyen | Règle la plus faible | Constat |
|---|---|---:|---|---|
| Unicité | RQ-020 | 100,000 % | RQ-020 (100,000 %) | Aucune anomalie d'unicité ou de clé nulle détectée sur les sept tables contrôlées |
| Complétude | RQ-003 | 87,855 % | RQ-003 (87,855 %) | 12 024 anomalies sur les numéros de téléphone |
| Validité | RQ-002, RQ-005, RQ-009, RQ-010 | 99,338 % | RQ-005 (98,477 %) | An