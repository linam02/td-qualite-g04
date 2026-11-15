# S5 · Certifier, publier vers le CRM, gouverner

Groupe : g04  ·  Date : 14/11/2026  ·  Rédacteur : Fatine Mourid  ·  Étiquette : `seance-5`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

**Preuve commune** : `pipelines/S5_certificat_publication.py` (relançable de bout en bout : `docker exec -it dq_jupyter python pipelines/S5_certificat_publication.py`), lot `L-2026-10-01`. Rôles en S5 : Data Owner = Lina Merazga ; Data Steward = LE Thi Quynh ; Ingénieurs qualité = Amadou Macka Diallo et Lyse Ndifo ; Rédacteur = Fatine Mourid. Chiffres exportés dans `reports/go_nogo_*.csv`.

## 1. Historique des mesures (US-29, US-30)

Une ligne par règle mesurée ; laissez vide la couche où la règle ne s'applique pas, et dites pourquoi. Quand une règle porte sur plusieurs tables, le taux affiché est le pire de la couche.

| Règle | Dimension | Taux bronze | Taux silver | Taux gold | Évolution (monte, stable, descend) | Explication |
|---|---|---|---|---|---|---|
| RQ-001 date de fin > début | Cohérence | 99,200 | 100,000 | 100,000 | monte | 800 contrats incohérents en quarantaine (porte S) |
| RQ-002 souscripteur majeur | Validité métier | 99,699 | 99,702 | 100,000 | monte | 294 contrats de mineurs écartés à la porte G |
| RQ-003 téléphone renseigné | Complétude | 87,998 | 88,006 | 89,938 | monte, mais reste sous 98 % | Un téléphone absent ne se corrige pas par traitement. En gold, la règle porte sur les clients ACTIF et INACTIF (46 632) ; la hausse vient probablement du dédoublonnage, un CLI gardant le téléphone de l'un de ses identifiants (à vérifier) |
| RQ-005 code postal FR | Validité format | 98,474 | 100,000 | 100,000 | monte | Zéro initial restauré sur 1 456 codes |
| RQ-007 pays dans le référentiel | Intégrité référentielle | 96,950 | 100,000 | 100,000 | monte | 2 600 variantes ramenées à `FR`, 450 lignes en quarantaine |
| RQ-009 type de personne | Validité domaine | 99,800 | 100,000 | — | monte | 200 lignes en quarantaine ; gold ne garde pas `type_personne` (remplacé par `statut_client`) |
| RQ-010 durée de garantie | Validité domaine | 99,400 | 100,000 | 100,000 | monte | 600 durées hors catalogue en quarantaine |
| RQ-011 type de contrat connu | Intégrité référentielle | 99,800 | 99,798 | 100,000 | descend puis monte | Dénominateur réduit en silver ; 199 contrats écartés à la porte G |
| RQ-012 souscripteur existant | Intégrité référentielle | 99,000 | 98,382 | 100,000 | descend puis monte | Effet domino : les 650 clients en quarantaine laissent des contrats orphelins ; 1 595 contrats écartés à la porte G |
| RQ-013 assuré existant | Intégrité référentielle | 99,700 | 99,334 | 100,000 | descend puis monte | Même effet domino ; 657 contrats écartés à la porte G |
| RQ-015 prospect sans contrat | Cohérence de statut | 99,521 | 99,524 | 100,000 | monte | En gold, le statut est dérivé des contrats certifiés |
| RQ-016 souscripteur avec contrat | Cohérence de statut | 98,086 | 97,700 | — | descend | Contrats en quarantaine : des souscripteurs perdent leur seul contrat ; non mesurée sur gold (voir section 2) |
| RQ-017 sinistre dans la garantie | Cohérence inter-tables | 98,800 | 98,800 | 100,000 | stable puis monte | 3 468 sinistres écartés à la porte G |
| RQ-018 client actif CD-001 | Cohérence de définition | — | — | 100,000 | — | Ne s'applique qu'à gold, où le statut ACTIF est calculé |
| RQ-019 un seul CLI par personne | Unicité | — | — | 100,000 | — | Ne s'applique qu'à gold (golden record) |
| RQ-020 clés uniques | Unicité | 100,000 | 100,000 | 100,000 | stable | Aucune clé nulle ni en double à aucune couche |
| RQ-021 réconciliation source-bronze | Complétude, intégrité | 100,000 | — | — | — | Règle de la porte B, mesurée sur bronze seulement |
| RQ-022 métadonnées bronze | Traçabilité | 100,000 | — | — | — | Règle de la porte B |
| RQ-023 lien vers la ligne d'origine | Traçabilité | — | 100,000 | 100,000 | stable | Chaque ligne silver et gold garde son `bronze_row_id` |
| RQ-024 silver + rejets = bronze | Complétude | — | 100,000 | — | — | Règle de la porte S |
| RQ-025 gold = CRM cible | Intégrité | — | — | — | — | Mesurée sur la couche CRM : 100 % sur les trois tables (section 3) |

Courbes (chemin des images) : `reports/courbe_qualite.png` (une courbe par dimension, bronze → silver → gold, avec la ligne du seuil de 98 %).

Lecture de la courbe pour un non-technicien : la qualité monte à chaque étape. Sur les données brutes, cinq familles de contrôles sont imparfaites (cohérence 99,2 %, intégrité 98,9 %, format 98,5 %, complétude 88,0 %) ; après nettoyage et consolidation, toutes atteignent 100 %, sauf la complétude du téléphone, qui reste à 89,9 % parce qu'un numéro manquant ne s'invente pas : il faut le demander aux clients.

Toute règle qui descend d'une couche à l'autre : cause (filtre mal posé, conversion, effet de la quarantaine) et preuve :
- RQ-011, 012, 013 et 016 descendent de bronze à silver : c'est l'effet de la quarantaine. Retirer 650 clients et 1 400 contrats en silver rend orphelins des contrats ou des souscripteurs jusque-là reliés. La porte G écarte ensuite ces contrats, et les règles remontent à 100 % sur gold (preuve : `dq.v_derniere_mesure`, section 1 de la sortie du script ; `livrables/S4_silver_gold.md`, sections 2 et 4).
- La courbe « Complétude » semble descendre de silver (97,60 %) à gold (89,94 %). Ce n'est pas une dégradation : la dimension ne regroupe pas les mêmes règles selon la couche. En silver, elle fait la moyenne de RQ-003 (88,0 %) et de RQ-024 (100 % sur quatre tables) ; en gold, seule RQ-003 est mesurée (89,9 %). Règle par règle, RQ-003 monte : 88,0 % → 88,0 % → 89,9 %.
- « Cohérence de statut » baisse de 98,80 % à 98,61 % en silver : c'est RQ-016 (97,70 %), même effet de la quarantaine.

Courbe « plate tant que rien ne change » : non démontrée faute de temps (écart déclaré en section 6). Pour la démontrer : relancer `pipelines/S2_regles_great_expectations.py` sans rien modifier, puis la S5 ; les taux de bronze doivent rester identiques.

## 2. Certificat de qualité (US-31)

| Élément | Valeur |
|---|---|
| Numéro du certificat | CERT-L-2026-10-01 |
| Lot | L-2026-10-01 |
| Décision (GO ou NO_GO) | GO |
| Règles bloquantes testées | 36 mesures (règles bloquantes des portes B, S et G, une mesure par table, chacune sur la couche de sa porte) |
| Règles bloquantes conformes | 36 sur 36 |
| Écarts connus (avertissements) | RQ-003 sur gold : 89,938 % pour un seuil de 98 % (4 692 clients sans téléphone) ; RQ-016 sur silver : 97,700 % (1 143 souscripteurs sans contrat) |
| Empreinte du gold | `dd23cc3a7405c4366a4a979545a37e1cd8eaf1f928712a9bd2ed199c2a25a894` (SHA-256) |
| Signataire (rôle) | Data Owner Lina Merazga ; émis le 14/11/2026 à 22:49 |

Requête de décision (chemin) : `pipelines/S5_certificat_publication.py`, cellule US-31, requête `DECISION` : GO si aucune règle BLOQUANTE des portes B, S et G n'est sous son seuil, chaque règle étant lue sur la couche de sa porte (B → bronze, S → silver, G → gold).

Épreuve du NO_GO : lot volontairement dégradé (comment), décision obtenue, preuve : les mesures du lot ont été copiées sous l'identifiant `L-TEST`, en fixant 10 échecs sur RQ-012 (souscripteur absent) dans `gold.contrat_certifie`, sans toucher au lot réel. Décision obtenue : NO_GO, 35 règles conformes sur 36, commentaire « Règles en échec : RQ-012 (contrat_certifie) ». Le lot `L-TEST` est supprimé à la fin du script. Preuve : cellule US-31.

Règles bloquantes non mesurées par votre pipeline et donc non couvertes par le certificat : RQ-014 (adresse de sinistre reconnue dans la BAN, porte S) n'a pas de mesure sur silver. Elle a été mesurée sur bronze en S3 (12,1 % d'adresses non reconnues, échec) et en annexe de S4 (7,96 % après correction), mais elle n'entre pas dans la décision. Le GO ne garantit donc pas la qualité des adresses de sinistre. Avertissements non mesurés : RQ-004, RQ-006, RQ-008 (extensions US-20 et US-26), et RQ-016 sur gold.

## 3. Publication vers le CRM (US-32)

Script (chemin) : `pipelines/S5_certificat_publication.py`, cellule US-32, fonction `publier`.

| Scénario | Message obtenu | Chargement effectué ? | Preuve |
|---|---|---|---|
| Sans certificat | « REFUS : aucun certificat de qualité » | Non | `publier("CERT-INEXISTANT")` |
| Certificat NO_GO | « REFUS : décision NO_GO sur CERT-L-TEST » | Non | `publier("CERT-L-TEST")` |
| Gold modifié après émission du certificat | « REFUS : le gold a changé depuis l'émission du certificat » | Non | Téléphone d'une ligne de `gold.client_unique` remplacé par `0000000000`, puis restauré (bloc `try/finally`) |
| Certificat GO et gold intact | « PUBLIÉ : CERT-L-2026-10-01 » | Oui | `publier("CERT-L-2026-10-01")` ; republication idempotente : même résultat |

Réconciliation après chargement (RQ-025) :

| Table | Lignes gold | Lignes CRM cible | Somme de contrôle gold | Somme de contrôle CRM cible | Écart |
|---|---|---|---|---|---|
| client | 120 480 | 120 480 | égale (SUM(CRC32) calculée, non affichée par le script) | égale | 0 |
| contrat | 95 866 | 95 866 | égale | égale | 0 |
| sinistre | 96 532 | 96 532 | égale | égale | 0 |

RQ-025 à 100 % sur les trois tables, couche CRM, dans `dq.dq_history` (un écart de comptage ou de somme de contrôle aurait compté comme échec).

Le chargement est-il tout-ou-rien ? Comment l'avez-vous vérifié : oui par construction. Les trois tables sont vidées et rechargées dans une seule transaction (`with eng().begin()`) : si une instruction échoue, toute la transaction est annulée et le CRM cible garde son état précédent. La réconciliation RQ-025 confirme qu'après le chargement les trois tables sont complètes. Nous n'avons pas provoqué d'échec en cours de chargement pour le démontrer.

## 3 bis. Gouvernance (US-34)

Fiche de catalogue de `gold.client_unique` (chemin) : `catalogue/catalog.json` (30 tables documentées), consultable dans l'interface `streamlit run catalogue/app.py --server.port 8502 --server.address 0.0.0.0` puis http://localhost:8502.

| Élément | Valeur |
|---|---|
| Propriétaire (Data Owner) | Claire Dumontier |
| Steward (Data Steward) | Yanis Belkacem |
| Définition de « client actif » rattachée à la fiche | Contrat en cours ET à jour de cotisation sur 3 mois glissants (fiche CD-001), validée le 01/04/2026 |
| Règles RQ rattachées à la table | RQ-003 (89,938 %), RQ-005, RQ-007, RQ-015, RQ-018, RQ-019, RQ-020 (100 % chacune), mesurées sur gold |

Définition de `gold.client_unique` : une ligne par personne réelle, physique ou morale, identifiée par un identifiant client unique (CLI) qui regroupe ses identifiants du CRM et du CIF, avec les coordonnées retenues par la règle de survie et son statut (ACTIF, INACTIF, ASSURE, PROSPECT) ; 120 480 clients au lot L-2026-10-01.

Lineage de `gold.client_unique` jusqu'aux sources (liste ou schéma) :
- `gold.client_unique` ← `silver.client` (dédoublonnage, porte G, RQ-019)
- `silver.client` ← `bronze.crm_client` ← `crm.client` (standardisation et quarantaine, porte S ; ingestion, porte B, RQ-021)
- `silver.client` ← `bronze.cif_clients` ← `cif.clients` (mêmes étapes)
- Au-delà de gold : `gold.client_unique` → `crm_cible.client` (publication sous certificat, RQ-025)

Chaîne quotidienne (US-33, Could) : ingest_bronze → porte B (ouverte) → build_silver → porte S (ouverte) → build_gold → porte G (ouverte) → certifier → publier_crm. Une porte fermée arrête toutes les tâches suivantes.

## 4. Décisions de la séance

Reportez dans `JOURNAL_DECISIONS.md` chaque seuil, sévérité ou règle de survie arrêté, avec son rôle. Nombre de décisions ajoutées en S5 : 2 (n° 12 : signature du certificat CERT-L-2026-10-01 et recommandation GO sous conditions ; n° 13 : acceptation des écarts connus RQ-003 et RQ-014), par le Data Owner Lina Merazga. Décisions de S4 ajoutées en même temps : n° 10 et 11.

## 5. Critères de fin

- [x] Un lot volontairement dégradé produit un NO_GO, le lot nominal un GO. (L-TEST : NO_GO, 35/36 ; L-2026-10-01 : GO, 36/36)
- [x] La publication refuse sans certificat, avec une décision NO_GO, et quand le gold a changé. (trois refus, section 3)
- [x] Après un chargement réussi, comptage et somme de contrôle sont égaux entre gold et CRM cible. (RQ-025 à 100 % sur trois tables)
- [x] Chaque décision de seuil ou de sévérité est attribuée à un rôle. (journal, décisions 1 à 13)

## 6. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : fusion de `main` dans la branche personnelle par l'éditeur Vim de Git (message de fusion à valider, Échap puis `:wq`) ; temps perdu non mesuré précisément.

Écarts avec l'attendu : RQ-014, règle bloquante, n'est pas mesurée sur silver et n'est donc pas couverte par le certificat ; la courbe plate n'est pas démontrée ; les décisions n° 3 et 7 ne sont pas appliquées par le code de silver (voir `livrables/S4_silver_gold.md`).

Point de reprise utilisé (oui / non, lequel) : non.

Ce que nous ferions autrement : mesurer RQ-014 sur silver pour qu'elle entre dans le certificat ; démontrer la courbe plate ; inscrire chaque décision au journal pendant la séance.
