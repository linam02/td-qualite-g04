# Dossier GO/NO-GO : migration des données consolidées vers le CRM

**Groupe :** G04
**Date de remise :** 18/11/2026
**Étiquette :** `rendu-final`
**Lot :** `S1_G04_001`
**Destinataire :** Directrice Générale

## 1. Recommandation

**Décision métier retenue par le Data Owner : NO-GO pour toute nouvelle migration vers le CRM.**

Cette décision repose sur trois constats chiffrés :

1. **Qualité des adresses insuffisante :** 11 871 adresses sur 100 000 ne sont pas reconnues par le référentiel national BAN. La conformité observée à Silver est de **88,129 %**, contre un seuil bloquant de **100 %** pour RQ-014.
2. **Anomalies non résolues :** 3 914 corrections ont été proposées, mais non appliquées. Même après correction simulée, 7 957 adresses resteraient non reconnues.
3. **Certification incomplète :** le certificat affiche **36/36 contrôles bloquants mesurés conformes**, mais la règle bloquante RQ-014 n'a pas été historisée.

Une publication technique de **312 878 lignes** vers le CRM a déjà été réalisée et réconciliée. Elle ne constitue pas une validation métier.

**Décision : suspendre toute nouvelle publication métier jusqu'à la levée des écarts bloquants et l'obtention d'une certification complète, ou jusqu'à un arbitrage formel conforme aux règles de gouvernance.**

## 2. Les preuves

### Qualité par couche et par dimension

Résultats du lot `S1_G04_001`, issus de `dq.dq_kpi_dimension`.

| Dimension | Bronze | Silver | Gold | Seuil visé | Atteint ? |
|---|---:|---:|---:|---|---|
| Cohérence | 99,20 % | 100 % | 100 % | Selon les RQ | À vérifier par règle |
| Complétude | 87,86 % | 97,60 % | 89,94 % | RQ-003 : 98 % | Non pour RQ-003 Gold |
| Intégrité référentielle | 99,50 % | 99,38 % | 100 % | Selon les RQ | Oui pour les contrôles Gold mesurés |
| Cohérence de statut | 98,80 % | 98,61 % | 100 % | Selon les RQ | À vérifier par règle |
| Validité métier | 99,68 % | 99,70 % | 100 % | Selon les RQ | À vérifier par règle |
| Validité format | 98,48 % | 100 % | 100 % | Selon les RQ | À vérifier par règle |
| Unicité | 100 % | 100 % | 100 % | Selon les RQ | Oui pour les contrôles mesurés |
| Traçabilité | 100 % | 100 % | 100 % | Selon les RQ | Oui pour les contrôles mesurés |

**Graphique :** `reports/qualite_par_dimension.png`.

La qualité progresse sur plusieurs dimensions. Toutefois, la complétude à Gold reste insuffisante pour RQ-003 (89,938 % contre 98 %). Les résultats agrégés ne garantissent pas la couverture de toutes les règles obligatoires.

### Certificat de qualité

- **Numéro :** `CERT-S1_G04_001`
- **Décision enregistrée :** GO technique, avec réserve de périmètre.
- **Contrôles bloquants mesurés :** 36/36 conformes.
- **Règle bloquante non mesurée :** RQ-014 à Silver.
- **Empreinte SHA-256 Gold :** `98530596879d5bc6c1ccf929a01972e40dc2b235e2561b21928e2b88d01ef1f4`

Le GO technique ne peut pas être assimilé à une autorisation métier.

### Traçabilité et publication

Trois cas sont retracés dans `livrables/S4_silver_gold.md`, section 5 : rapprochement de plusieurs identifiants clients, conservation du code postal `03100` et suivi du sinistre `SIN0000006` de Bronze à Gold.

Les données publiées vers le CRM cible comprennent **120 480 clients, 95 866 contrats et 96 532 sinistres**, soit **312 878 lignes**. Les volumes et contrôles CRC32 concordent avec Gold, sans écart observé.

## 3. Les écarts

| Écart | Chiffre | Règle | Conséquence pour le CRM | Qui doit agir |
|---|---|---|---|---|
| Adresses non reconnues à Silver | 11 871 / 100 000 | RQ-014 | Risque d'adresses de sinistres non fiables | Data Steward / équipe Data |
| Complétude insuffisante à Gold | 4 692 échecs ; 89,938 % | RQ-003 | Informations clients incomplètes | Data Steward |
| Quarantaine à la porte S | 2 050 lignes | RQ-001, 007, 009, 010 | Données écartées de Silver | Équipe Data |
| Quarantaine à la porte G | 6 213 cas comptabilisés par règle, avec chevauchements possibles | RQ-002, 011, 012, 013, 017 | Contrats et sinistres écartés | Équipe Data |
| Couverture incomplète | RQ-014 non mesurée ; quatre mesures d'avertissement absentes | RQ-004, 006, 008, 014, 016 | Certification incomplète | Data Owner / équipe Data |

**Détail des quarantaines :** porte S : RQ-007 (450), RQ-009 (200), RQ-001 (800), RQ-010 (600). Porte G : RQ-002 (294), RQ-011 (199), RQ-012 (1 595), RQ-013 (657), RQ-017 (3 468).

**Hypothèses métier à valider :** seuils de rapprochement des clients (85/70), priorité CIF puis CRM dans la constitution du client unique, traitement des adresses non reconnues par la BAN et acceptation des anomalies résiduelles non bloquantes.

## 4. La décision

### Seuils et arbitrages

Les décisions n° 2, 6, 7, 8 et 9 du `JOURNAL_DECISIONS.md` documentent les principales conventions métier : sévérités et seuils, traitement de la valeur sentinelle `assure_id = '0'`, correction des statuts clients, définition unique du client actif et maintien du caractère bloquant de RQ-017.

Les quatre propositions S4/S5 concernant le rapprochement des clients, la règle de survie CIF/CRM, RQ-014 et la publication métier restent à formaliser dans le journal.

### Responsabilités

- **Data Owner – LE Thi Quynh :** décide du GO/NO-GO et valide les arbitrages métier.
- **Data Steward :** contrôle la qualité et suit les anomalies.
- **Équipe Data :** réalise les corrections, les tests et les opérations techniques de migration.

### Conditions avant toute nouvelle migration

| Condition | Responsable | Échéance |
|---|---|---|
| Traiter les adresses non reconnues et mesurer RQ-014 à Silver | Équipe Data / Data Steward | Avant nouvelle publication |
| Vérifier la couverture des règles bloquantes et réémettre le certificat | Équipe Data / Data Steward | Avant certification finale |
| Valider les seuils de rapprochement et la règle de survie | Data Owner | Avant validation métier |
| Vérifier les écarts résiduels et autoriser formellement la migration | Data Owner | Après levée des conditions |

### Décision du Data Owner

**Décision : NO-GO métier.**

Toute nouvelle publication métier est suspendue jusqu'à la levée des conditions définies ci-dessus.

**Nom :** LE Thi Quynh
**Rôle :** Data Owner – Groupe G04
**Date de validation :** à renseigner lors de la signature
**Signature :** à apposer par le Data Owner

## Annexes

- `livrables/S1_bronze_profilage.md`
- `livrables/S2_regles_great_expectations.md`
- `livrables/S3_integrite_soda.md`
- `livrables/S4_silver_gold.md`
- `livrables/S5_certificat_publication.md`
- `livrables/JOURNAL_DECISIONS.md`
- `AVANCEMENT.md`
- `reports/qualite_par_dimension.png`
- `pipelines/S4_silver_gold.py`
- `pipelines/S5_certificat_publication.py`
