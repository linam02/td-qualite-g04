# Dossier go/no-go : migration des données consolidées vers le CRM

Groupe : g04  ·  Date de remise : 15/11/2026  ·  Étiquette : `rendu-final`

Destinataire : la Directrice Générale. Registre : un rapport court, sans jargon, quatre pages au plus hors annexes. Chaque chiffre renvoie à une preuve du dépôt (livrable de séance, requête, fichier).

## 1. Recommandation

**Nous recommandons un GO sous conditions** : charger dans le nouveau CRM les données consolidées du lot du 1er octobre 2026, en levant deux conditions dans les trois mois qui suivent.

1. **Les données chargées sont fiables.** Les 36 contrôles bloquants sont conformes : aucun contrat sans client, aucun sinistre hors garantie, aucun client en double (certificat CERT-L-2026-10-01, `livrables/S5_certificat_publication.md`, section 2).
2. **Rien n'a été perdu ni modifié en cachette.** Chaque ligne écartée est enregistrée avec son motif (8 263 lignes, dont 650 clients), et le CRM contient exactement ce qui a été certifié : 120 480 clients, 95 866 contrats, 96 532 sinistres, 0 écart (`livrables/S5_certificat_publication.md`, section 3).
3. **Deux faiblesses restent à corriger après la bascule.** 4 692 clients, actifs ou ayant eu un contrat, n'ont pas de téléphone (89,9 % de fiches complètes, pour un objectif de 98 %), et les adresses de sinistre ne sont pas certifiées (7,96 % d'adresses non reconnues après correction).

## 2. Les preuves

Qualité mesurée par couche et par dimension (reprise de S5, avec la courbe `reports/courbe_qualite.png`) :

| Dimension | Bronze | Silver | Gold | Seuil visé | Atteint ? |
|---|---|---|---|---|---|
| Cohérence (dates de contrat) | 99,20 % | 100,00 % | 100,00 % | 100 % | Oui |
| Intégrité référentielle (pays, types, clients, assurés) | 98,86 % | 99,38 % | 100,00 % | 100 % | Oui |
| Cohérence inter-tables (sinistres dans la garantie) | 98,80 % | 98,80 % | 100,00 % | 100 % | Oui |
| Validité format (code postal) | 98,47 % | 100,00 % | 100,00 % | 98 % | Oui |
| Validité métier (souscripteur majeur) | 99,70 % | 99,70 % | 100,00 % | 100 % | Oui |
| Unicité (un seul identifiant par client) | 100,00 % | 100,00 % | 100,00 % | 100 % | Oui |
| Complétude (téléphone du client) | 88,00 % | 88,01 % (RQ-003) | 89,94 % | 98 % | Non |

Certificat joint : numéro CERT-L-2026-10-01, décision GO (36 contrôles bloquants conformes sur 36), empreinte `dd23cc3a7405c4366a4a979545a37e1cd8eaf1f928712a9bd2ed199c2a25a894`. Le certificat ne vaut que pour ces données exactes : nous avons vérifié qu'une seule ligne modifiée après sa signature bloque le chargement.

Trois données retracées de la source à gold : renvoi vers `livrables/S4_silver_gold.md`, section 5. Résumé en trois lignes :
- La Société Meunier, saisie de quatre façons différentes dans les deux systèmes, est devenue un seul client (CLI-033758), et chacune de ses quatre fiches d'origine est retrouvable.
- Un code postal abîmé (`1500`) a été corrigé en `01500` et marqué « à surveiller », avec le lien vers sa ligne d'origine.
- Une adresse de sinistre (SIN0000012) a été mise au format standard, et sa saisie d'origine reste consultable.

## 3. Les écarts

| Écart | Chiffre | Règle | Conséquence pour le CRM | Qui doit agir |
|---|---|---|---|---|
| Anomalies résiduelles dans gold | 0 sur les contrôles bloquants | RQ-001 à RQ-025 | Aucune anomalie bloquante n'entre dans le CRM | — |
| Lignes mises en quarantaine, par règle | 8 263 : pays inconnu 450, type de personne 200, dates de contrat 800, durée hors catalogue 600, souscripteur mineur 294, type de contrat inconnu 199, souscripteur absent 1 595, assuré absent 657, sinistres 3 468 | RQ-007, 009, 001, 010, 002, 011, 012, 013, 017 | Ces clients, contrats et sinistres n'apparaissent pas dans le CRM tant qu'ils ne sont pas corrigés | Data Steward, avec la gestion des contrats et des sinistres |
| Avertissements restants | 4 692 clients sans téléphone (89,9 %) ; 1 143 souscripteurs sans contrat en silver (97,7 %) | RQ-003, RQ-016 | Clients joignables seulement par courrier ou e-mail | Direction commerciale (collecte), Data Owner |
| Règles non mesurées ou non couvertes par le certificat | Adresses de sinistre : 7,96 % non reconnues ; RQ-004, 006, 008 non mesurées | RQ-014 (bloquante), RQ-004, 006, 008 | La qualité des adresses de sinistre n'est pas garantie | Gestion des sinistres (ressaisie manuelle : 68 % des erreurs), Data Steward |

Hypothèses à faire valider par le métier (listez-les, ne les cachez pas) :
- Pour fusionner deux fiches, le dépôt central (CIF) l'emporte sur le CRM : si un client a déménagé et que seul le CRM le sait, l'ancienne adresse est conservée.
- La valeur `0` du champ assuré signifie « pas d'assuré distinct du souscripteur ».
- Les durées de 6, 9, 18 et 48 mois sont considérées hors catalogue, et 120 mois comme une erreur de saisie probable (12 mois).
- Nos décisions de corriger 140 types de personne mal écrits (décision n° 3) et de passer en souscripteurs les prospects titulaires d'un contrat (décision n° 7) ne sont pas encore appliquées : ces clients sont en quarantaine ou gardent leur ancien statut. C'est en partie pour cela que le nombre de clients actifs certifiés (35 985) est inférieur au comptage brut (38 049).

## 4. La décision

Seuils retenus et leur justification devant le Data Owner (renvoi vers `JOURNAL_DECISIONS.md`, numéros) : sévérités et seuils des règles confirmés (n° 2) ; correction de `type_personne` (n° 3) ; âge calculé à la date de signature (n° 4) ; quarantaine des durées hors catalogue (n° 5) ; valeur `0` de l'assuré (n° 6) ; statuts de personne (n° 7) ; définition unique du client actif CD-001 (n° 8) ; sinistres hors garantie (n° 9) ; seuils de fusion 85 et 70 (n° 10) ; règle de survie CIF puis CRM (n° 11) ; signature du certificat et recommandation (n° 12) ; acceptation des écarts connus RQ-003 et RQ-014 (n° 13).

Rôles : qui décide, qui contrôle, qui exécute la migration : le Data Owner décide et signe le certificat ; le Data Steward contrôle les règles, les quarantaines et les corrections ; l'Ingénieur qualité exécute la chaîne et la publication, qui ne part que si le certificat est valide. En S5 : Data Owner Lina Merazga ; Data Steward LE Thi Quynh ; Ingénieurs qualité Amadou Macka Diallo et Lyse Ndifo.

Conditions à lever avant migration, avec échéance et responsable :

| Condition | Responsable | Échéance |
|---|---|---|
| Appliquer les décisions n° 3 et n° 7 dans le traitement, puis réémettre le certificat | Ingénieur qualité, validation par le Data Steward | 30/11/2026 |
| Mesurer RQ-014 sur silver et traiter les adresses de sinistre non reconnues (priorité à la ressaisie manuelle) | Data Steward, gestion des sinistres | 15/12/2026 |
| Rendre le téléphone obligatoire à la saisie et lancer une collecte auprès des 4 692 clients concernés | Direction commerciale | 15/02/2027 |
| Examiner les 8 263 lignes en quarantaine et décider de leur correction ou de leur abandon | Data Steward, gestion des contrats | 15/01/2027 |

Signature du Data Owner (nom, rôle, date) : Lina Merazga, Data Owner (S5), 15/11/2026

## Annexes

Certificat de qualité : ligne de `dq.certificat_qualite` exportée dans `livrables/certificat_qualite.txt` (CERT-L-2026-10-01, GO, 36/36, signataire Lina Merazga, Data Owner). Démonstration : `notebooks/S5_certificat_publication.ipynb`, déjà exécuté.

Dépôt : https://github.com/linam02/td-qualite-g04 (étiquette `rendu-final`).

Liens vers les livrables : `livrables/S1_bronze_profilage.md`, `S2_regles_great_expectations.md`, `S3_integrite_soda.md`, `S4_silver_gold.md`, `S5_certificat_publication.md`, `JOURNAL_DECISIONS.md`, `AVANCEMENT.md`. Chiffres exportés : `reports/go_nogo_seuils.csv`, `go_nogo_ecarts.csv`, `go_nogo_quarantaine.csv`, `go_nogo_historique.csv`, `go_nogo_reconciliation.csv`. Courbe : `reports/courbe_qualite.png`.
