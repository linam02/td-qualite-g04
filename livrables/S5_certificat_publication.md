# S5 · Certifier, publier vers le CRM, gouverner

**Groupe :** G04 · **Date :** 15/11/2026 · **Rédacteur :** LE Thi Quynh · **Étiquette :** `seance-5` · **Lot :** `S1_G04_001`

**Principe :** chaque constat distingue mesure observée, preuve reproductible et conséquence métier. Les absences de mesure ne sont jamais assimilées à une conformité.

## 1. Historique des mesures (US-29, US-30)

78 mesures historisées, couvrant 21 règles distinctes (dont RQ-025 à la couche CRM). Le tableau suivant reprend, pour chaque règle disponible dans l'extraction, le **minimum des taux mesurés par couche** lorsque plusieurs tables sont concernées. « — » signifie **aucune mesure disponible à cette couche**, et non 0 %.

| Règle | Dimension | Bronze (%) | Silver (%) | Gold (%) | Évolution et observation |
|---|---|---:|---:|---:|---|
| RQ-001 | Cohérence | 99,200 | 100,000 | 100,000 | Monte, puis stable |
| RQ-002 | Validité métier | 99,676 | 99,702 | 100,000 | Monte |
| RQ-003 | Complétude | 87,855 | 88,006 | 89,938 | Monte, mais Gold sous le seuil d'avertissement de 98 % |
| RQ-005 | Validité format | 98,477 | 100,000 | 100,000 | Monte, puis stable |
| RQ-007 | Intégrité référentielle | — | 100,000 | 100,000 | Stable sur les couches mesurées |
| RQ-009 | Validité domaine | 99,800 | 100,000 | — | Monte jusqu'à Silver ; pas de mesure Gold |
| RQ-010 | Validité domaine | 99,400 | 100,000 | 100,000 | Monte, puis stable |
| RQ-011 | Intégrité référentielle | 99,800 | 99,798 | 100,000 | Baisse de 0,002 point à Silver, puis remonte |
| RQ-012 | Intégrité référentielle | 99,000 | 98,382 | 100,000 | Baisse de 0,618 point à Silver, puis remonte |
| RQ-013 | Intégrité référentielle | 99,700 | 99,334 | 100,000 | Baisse de 0,366 point à Silver, puis remonte |
| RQ-015 | Cohérence de statut | 99,521 | 99,524 | 100,000 | Monte |
| RQ-016 | Cohérence de statut | 98,086 | 97,700 | — | Baisse de 0,386 point ; mesure attendue à Gold absente |
| RQ-017 | Cohérence inter-tables | 98,800 | 98,800 | 100,000 | Stable, puis monte |
| RQ-018 | Cohérence de définition | — | — | 100,000 | Mesurée à Gold uniquement |
| RQ-019 | Unicité | — | — | 100,000 | Mesurée à Gold uniquement |
| RQ-020 | Unicité | 100,000 | 100,000 | 100,000 | Stable |
| RQ-021 | Complétude, intégrité | 100,000 | — | — | Mesurée à Bronze uniquement |
| RQ-022 | Traçabilité | 100,000 | — | — | Mesurée à Bronze uniquement |
| RQ-023 | Traçabilité | — | 100,000 | 100,000 | Stable sur les couches mesurées |
| RQ-024 | Complétude | — | 100,000 | — | Mesurée à Silver uniquement |

**Courbes :** `reports/courbe_qualite.png` (courbe par dimension) ; `reports/qualite_par_dimension.png` (barres par dimension et couche, taux pondérés par les lignes testées). Sources : `dq.dq_history`, `dq.dq_kpi_dimension`, `reports/go_nogo_historique.csv` et `reports/go_nogo_seuils.csv`.

**Interprétation des baisses :** RQ-011, RQ-012, RQ-013 et RQ-016 baissent entre Bronze et Silver. Les périmètres et dénominateurs changent selon les transformations et quarantaines ; la cause précise n'est pas démontrée par les seuls taux. Une investigation par règle et par enregistrement est nécessaire avant d'attribuer ces variations à une anomalie de transformation. Les mesures proviennent d'un seul lot : il s'agit d'une comparaison entre couches, **pas d'une tendance multi-lots dans le temps**.

## 2. Certificat de qualité (US-31)

| Élément | Valeur |
|---|---|
| Numéro du certificat | `CERT-S1_G04_001` |
| Lot | `S1_G04_001` |
| Décision enregistrée | `GO` **technique, avec réserve de périmètre** |
| Règles bloquantes testées | 36 mesures bloquantes aux portes B/S/G |
| Règles bloquantes conformes | 36 / 36 mesures disponibles |
| Écarts connus | RQ-003 : Gold 89,938 % (seuil d'avertissement 98 %) ; RQ-016 : absence de mesure Gold ; RQ-004, RQ-006, RQ-008 : absence de mesure Silver |
| Règle bloquante non mesurée | **RQ-014 à Silver**, seuil 100 % |
| Empreinte SHA-256 du Gold | `98530596879d5bc6c1ccf929a01972e40dc2b235e2561b21928e2b88d01ef1f4` (empreinte enregistrée ; à recalculer avant toute nouvelle publication) |
| Signataire renseigné en base | `Data Owner` (libellé de rôle, **pas une signature nominative vérifiée**) |

**Requête de décision :** `pipelines/S5_certificat_publication.py`, section `US-31`, requêtes `DECISION` et `EN_ECHEC`, fonction `emettre(lot)`. La requête actuelle compte les mesures existantes : elle **ne rejette pas automatiquement un lot en cas de règle bloquante absente**. Une validation formelle du périmètre ou une correction du contrôle de complétude des règles est nécessaire.

**Épreuve NO_GO :** un lot `L-TEST` a été constitué avec 78 mesures copiées du lot nominal ; RQ-012 a été dégradée à Gold (99,990 % pour un seuil de 100 %). Résultat observé : `CERT-L-TEST`, décision **NO_GO**, **35/36** contrôles conformes, commentaire `Regles en echec : RQ-012 (contrat_certifie)`. Le certificat et les mesures du lot de test ont été supprimés après validation. Preuve : sortie terminal du test de la fonction `emettre("L-TEST")`.

**Réserve BAN / RQ-014 :** l'analyse exploratoire US-26 de `pipelines/S4_silver_gold.py` sur 100 000 sinistres Silver donne **11 871 adresses non reconnues (11,87 %)** avant correction ; **3 914 corrections proposées** ; **7 957 adresses non reconnues (7,96 %)** après correction *simulée*. Causes résiduelles : 3 939 couples code postal/commune absents du référentiel, 2 020 numéros absents, 1 982 adresses sans numéro, 16 cas ambigus. Les corrections **n'ont pas été appliquées à Silver** ; aucune mesure RQ-014 n'a été historisée. Le seuil bloquant de 100 % n'est donc **pas démontré**. Une exclusion explicite du périmètre, si admise, doit être décidée et tracée par le Data Owner ; sinon la publication métier doit être suspendue en attente de résolution.

**Décision métier proposée : NO-GO.** Le contrôle analytique US-26 indique un taux de conformité BAN de 88,129 % avant correction, inférieur au seuil bloquant de 100 % fixé pour RQ-014 à la porte S. Cette analyse n'est pas historisée dans `dq.dq_history`. Le certificat `CERT-S1_G04_001` conserve son statut GO technique enregistré, mais celui-ci ne constitue pas une autorisation métier de publication. Une remédiation et une nouvelle certification, ou un arbitrage formel du Data Owner conforme aux règles de gouvernance, restent nécessaires.
## 3. Publication vers le CRM (US-32)

**Script :** `pipelines/S5_certificat_publication.py`, fonction `publier(certificat_id)` ; contrôle préalable du certificat, de la décision et de l'empreinte, puis chargement dans une transaction.

| Scénario | Message obtenu / résultat | Chargement effectué ? | Preuve |
|---|---|---|---|
| Sans certificat | `REFUS : aucun certificat de qualité` | Non, refus avant écriture | Test direct `publier("CERT-INEXISTANT")` : PASS |
| Certificat NO_GO | `REFUS : décision NO_GO sur CERT-L-TEST` | Non, refus avant écriture | Test direct : PASS |
| Empreinte différente | `REFUS : le gold a changé depuis l'émission du certificat` | Non, refus avant écriture | `CERT-HASH-TEST`, certificat GO fictif à empreinte nulle : PASS |
| Certificat GO et Gold intact | Publication nominale déjà réalisée ; réconciliation conforme | Oui, état publié constaté | Mesures RQ-025 et vérification des tables CRM ; **ne constitue pas à elle seule une nouvelle exécution du chemin GO** |

**Réconciliation RQ-025 (contrôle direct des volumes et CRC32) :**

| Table | Lignes Gold | Lignes CRM cible | CRC32 Gold | CRC32 CRM cible | Écart |
|---|---:|---:|---:|---:|---:|
| client | 120 480 | 120 480 | 258550004144553 | 258550004144553 | 0 |
| contrat | 95 866 | 95 866 | 205808379803748 | 205808379803748 | 0 |
| sinistre | 96 532 | 96 532 | 207187308913189 | 207187308913189 | 0 |
| **Total** | **312 878** | **312 878** | — | — | **0** |

Les trois mesures RQ-025 dans `dq.dq_history` affichent 100,000 % et zéro échec (horodatage : 15/11/2026 à 19:08:44). Le fichier `reports/go_nogo_reconciliation.csv` contient les **mesures RQ-025**, pas les valeurs CRC détaillées ; ces dernières ont été recalculées directement dans le terminal. Une égalité de sommes CRC32 n'est pas une preuve cryptographique absolue d'identité.

**Atomicité « tout-ou-rien » :** le code place les suppressions et insertions des trois tables dans `with eng().begin()` ; cela fournit une transaction pour le DML sur un moteur transactionnel. **Aucun test d'échec injecté en milieu de chargement n'a encore été produit** ; la propriété n'est donc pas validée expérimentalement. Les instructions DDL `CREATE TABLE IF NOT EXISTS` sont exécutées avant cette transaction et ne font pas partie de la même garantie.

## 3 bis. Gouvernance (US-34)

**Catalogue :** `catalogue/catalog.json` (30 tables documentées, 1 terme de glossaire, 13 liens de lineage).

| Élément | Valeur |
|---|---|
| Table | `gold.client_unique` |
| Data Owner dans le catalogue | `Claire Dumontier` (**valeur codée en dur, identité/attribution à valider**) |
| Data Steward dans le catalogue | `Yanis Belkacem` (**valeur codée en dur, attribution à valider**) |
| Définition de « client actif » | Contrat en cours **et** cotisations à jour sur trois mois glissants (CD-001) |
| Règles RQ rattachées | Voir la requête de `S5_certificat_publication.py` filtrant `table_cible = 'client_unique'` ; liste exhaustive non reproduite faute d'extraction confirmée |

**Lineage principal :** `crm.client → bronze.crm_client → silver.client → gold.client_unique → crm_cible.client` ; `cif.clients → bronze.cif_clients → silver.client → gold.client_unique`. La table `gold.xref_identifiants` assure la traçabilité des identifiants issus de `silver.client`. Le catalogue indique les transformations et les règles aux différents passages.

## 4. Décisions de la séance

**Journal :** `livrables/JOURNAL_DECISIONS.md`.

Le journal contient 9 décisions documentées pour les séances S1 à S3. Une section complémentaire présente 4 propositions de décisions pour S4 et S5, dont 2 concernant directement S5.

**Propositions S5 en attente de validation :**

- **RQ-014 – Rapprochement BAN :** arbitrer le traitement des adresses non reconnues et le périmètre de certification. La mesure Silver de cette règle bloquante est absente.
- **Certification et publication CRM :** décider de l'autorisation métier de publication compte tenu de la réserve RQ-014, malgré les 36/36 mesures bloquantes disponibles conformes et la réconciliation de 312 878 lignes.

D'autres arbitrages restent à formaliser, notamment l'absence de mesure RQ-016 à Gold, le traitement de l'avertissement RQ-003 et l'approbation nominative du certificat.

**Bilan :** 0 nouvelle décision S5 formellement approuvée dans le journal ; 2 propositions S5 documentées et en attente de validation du Data Owner. Aucune signature n'est présumée acquise.
## 5. Critères de fin

- [x] Un lot dégradé produit NO_GO et le lot nominal a produit un GO technique (avec réserve RQ-014).
- [x] La publication refuse sans certificat, avec décision NO_GO, ou si l'empreinte Gold ne correspond pas.
- [x] Après publication, comptages et sommes de contrôle CRC32 concordent entre Gold et CRM cible.
- [ ] Chaque décision de seuil/sévérité est attribuée et validée par le rôle responsable dans `JOURNAL_DECISIONS.md`.
- [ ] Le périmètre de certification, en particulier RQ-014, est validé par le Data Owner.
- [ ] L'atomicité a été vérifiée par une simulation d'échec pendant le chargement (si exigée).

## 6. Difficultés, écarts avec l'attendu, reprise

**Difficultés constatées :** absence de mesure RQ-014 malgré son statut bloquant ; absence de mesure RQ-016 à Gold ; qualité des adresses BAN inférieure à la cible ; certificat GO calculé seulement sur les mesures présentes ; preuves de tests à consolider dans les annexes. **Temps perdu : non chronométré.**

**Point de reprise :** reprise ciblée depuis les mesures `dq.dq_history` et les scripts `pipelines/S4_silver_gold.py` (US-26) / `pipelines/S5_certificat_publication.py` (US-31/32), sans reconstruction des couches Silver et Gold. Tests `L-TEST` et `CERT-HASH-TEST` nettoyés après exécution.

**Ce que nous ferions autrement :** rendre la présence de toutes les règles obligatoires une condition préalable du GO, séparer explicitement extensions optionnelles et règles bloquantes, conserver les preuves de tests dans des annexes versionnées, automatiser les tests de rollback et faire signer la décision métier avant publication.

**Annexes et preuves :** `reports/go_nogo_historique.csv`, `reports/go_nogo_seuils.csv`, `reports/go_nogo_ecarts.csv`, `reports/go_nogo_quarantaine.csv`, `reports/go_nogo_reconciliation.csv`, `reports/courbe_qualite.png`, `reports/qualite_par_dimension.png`, `catalogue/catalog.json`. Les sorties de tests NO_GO et de refus sont à archiver si le jury exige une reproduction autonome.