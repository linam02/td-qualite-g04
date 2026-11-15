
# S4 · Construire Silver puis Gold

**Groupe :** G04
**Lot :** `S1_G04_001`
**Étiquette :** `seance-4`
**Rédacteur et date :** LE Thi Quynh 30/10/2026

## 1. Silver et quarantaine (US-21, US-22)

**Script principal :** `pipelines/S4_silver_gold.py`

La couche Silver vise à standardiser les données provenant de Bronze, contrôler leur qualité et isoler les enregistrements non conformes dans une quarantaine traçable.

Les traitements concernent notamment la normalisation des identifiants, des informations de contact, des données géographiques et des relations métier.

### Bilan des volumes

| Table | Lignes Bronze | Lignes Silver | Rejets | Écart |
|---|---:|---:|---:|---:|
| Client CRM | 100 000 | 99 350 | 650 | 0 |
| Client CIF | 40 000 | 40 000 | 0 | 0 |
| Contrat | 100 000 | 98 600 | 1 400 | 0 |
| Sinistre | 100 000 | 100 000 | 0 | 0 |
| **Total** | **340 000** | **337 950** | **2 050** | **0** |

L'invariant de conservation est respecté :

**Nombre de lignes Bronze = Nombre de lignes Silver + Nombre de lignes rejetées.**

Aucune suppression silencieuse n'est constatée dans ces quatre bilans.

### Rejets enregistrés dans `dq.rejets`

| Porte | Entité | Règle | Lignes |
|---|---|---|---:|
| S | Client | RQ-007 | 450 |
| S | Client | RQ-009 | 200 |
| S | Contrat | RQ-001 | 800 |
| S | Contrat | RQ-010 | 600 |

Ces rejets représentent les 2 050 lignes écartées lors du passage vers Silver.

**Preuves :**
- `pipelines/S4_silver_gold.py`
- `reports/go_nogo_quarantaine.csv`
- `reports/go_nogo_historique.csv`

### Idempotence

Le pipeline doit produire le même résultat lorsqu'il est relancé sur un lot identique.

Les volumes obtenus sont cohérents avec les invariants attendus. Toutefois, une comparaison formelle de deux exécutions successives reste à joindre pour démontrer l'idempotence.

**Preuve de double exécution :** [À VÉRIFIER].

## 2. Porte S : comparaison Bronze / Silver (US-23)

La porte S vérifie que les règles bloquantes applicables à Silver respectent leur seuil avant la construction de Gold.

| Règle | Sévérité | Bronze | Silver | Évolution |
|---|---|---:|---:|---|
| RQ-002 | Bloquante à G | 99,676 % | 99,702 % | +0,026 point |
| RQ-011 | Bloquante à G | 99,800 % | 99,798 % | -0,002 point |
| RQ-012 | Bloquante à G | 99,000 % | 98,382 % | -0,618 point |
| RQ-013 | Bloquante à G | 99,700 % | 99,334 % | -0,366 point |
| RQ-015 | Bloquante à G | 99,521 % | 99,524 % | +0,003 point |
| RQ-017 | Bloquante à G | 98,800 % | 98,800 % | Stable |

Les règles ci-dessus sont mesurées à plusieurs couches, mais leur porte bloquante officielle est G. Leur taux sur Silver ne constitue donc pas à lui seul une décision de blocage à la porte S.

Les diminutions observées doivent être interprétées avec prudence : la composition et le dénominateur des populations changent après les traitements Silver.

### Décision de la porte S

Les règles bloquantes effectivement mesurées à leur porte respectent les seuils enregistrés. Toutefois, RQ-014 est une règle bloquante à la porte S, avec un seuil minimal de 100 %.

**Analyse BAN (US-26) :** sur 100 000 adresses Silver, 11 871 ne sont pas reconnues dans le référentiel BAN, soit un taux de conformité de 88,129 %. Le rapprochement flou propose 3 914 corrections potentielles, non appliquées aux données Silver. Après ces corrections théoriques, 7 957 adresses resteraient non reconnues (7,957 %).

**Traçabilité :** aucune mesure officielle RQ-014 n'est enregistrée dans `dq.dq_history` pour le lot `S1_G04_001`. Ces résultats constituent une analyse technique, et non une mesure historisée.

**Conclusion : NO-GO proposé pour la porte S.** La conformité de RQ-014 n'est pas démontrée. Une remédiation suivie d'un nouveau contrôle, ou une dérogation formelle du Data Owner selon la procédure applicable, est nécessaire avant validation métier.
## 3. Dédoublonnage et golden record (US-24, US-25)

Le rapprochement flou a été exécuté sur 139 350 lignes de `silver.client` issues des sources CRM et CIF.

### US-24 – Rapprochement des identités

| Indicateur | Résultat |
|---|---:|
| Lignes Silver analysées | 139 350 |
| Paires candidates | 2 782 840 |
| Paires automatiques | 19 505 |
| Paires non fusionnées à revoir | 2 120 |
| Identités uniques obtenues | 120 480 |
| Vrais positifs | 100 |
| Faux positifs | 0 |
| Faux négatifs | 0 |
| Précision | 100 % |
| Rappel | 100 % |

**Méthode :** trois clés de blocage sont utilisées : code postal et début d'identité, code postal et date de naissance, ville et début d'identité. La similarité des identités est calculée avec `rapidfuzz.fuzz.ratio`. La fusion automatique exige un score d'au moins 85, un même code postal et au moins un signal complémentaire. Les regroupements sont construits par Union-Find.

**Analyse de sensibilité :**

| Seuil automatique | Paires automatiques | Précision | Rappel |
|---|---:|---:|---:|
| 80 | 19 509 | 100 % | 100 % |
| 85 | 19 505 | 100 % | 100 % |
| 90 | 19 194 | 100 % | 91 % |
| 95 | 18 415 | 100 % | 87 % |

La précision et le rappel sont calculés sur les paires étiquetées exploitables, et non sur l'ensemble des 2 782 840 paires candidates.

Le seuil automatique de 85 et le seuil de revue de 70 sont implémentés techniquement. Leur validation métier reste à formaliser dans `livrables/JOURNAL_DECISIONS.md`.

### US-25 – Golden Record

La consolidation produit 120 480 clients uniques dans `gold.client_unique` et 139 350 correspondances dans `gold.xref_identifiants`.

La règle de survie implémentée privilégie les données CIF, puis CRM. Pour chaque attribut, la première valeur non nulle est sélectionnée selon l'ordre défini dans le pipeline.

**Cas de la Société Meunier SARL :**

| Source | Identifiant source | CLI Gold |
|---|---|---|
| CRM | A-4471 | CLI-033758 |
| CRM | H-9012 | CLI-033758 |
| CRM | S-2208 | CLI-033758 |
| CIF | K471226 | CLI-033758 |

Les quatre identifiants sources sont bien rattachés au même client unique.

**Contrôles d'intégrité réalisés dans Gold :**

| Contrôle | Résultat |
|---|---:|
| Correspondances sans client Gold | 0 |
| Clients Gold sans correspondance | 0 |
| CLI dupliqués dans `gold.client_unique` | 0 |
| Lignes Silver sans CLI lors du rapprochement | 0 |

Ces contrôles confirment l'unicité des CLI et l'intégrité référentielle entre les deux tables Gold dans le périmètre vérifié.

**Décision métier :** la validation des seuils de rapprochement et des règles de survie reste en attente du Data Owner.

**Preuves :** `pipelines/S4_silver_gold.py` (US-24/25), `gold.client_unique`, `gold.xref_identifiants` et sorties des contrôles SQL.
## 4. Gold et client actif (US-27)

La couche Gold contient les données consolidées et certifiées destinées au CRM cible.

| Table Gold | Nombre de lignes |
|---|---:|
| `gold.client_unique` | 120 480 |
| `gold.contrat_certifie` | 95 866 |
| `gold.sinistre_certifie` | 96 532 |
| `gold.xref_identifiants` | 139 350 |

### Quarantaine à la porte G

| Entité | Règle | Lignes rejetées |
|---|---|---:|
| Contrat | RQ-002 | 294 |
| Contrat | RQ-011 | 199 |
| Contrat | RQ-012 | 1 595 |
| Contrat | RQ-013 | 657 |
| Sinistre | RQ-017 | 3 468 |

Ces valeurs proviennent de `dq.rejets`. Elles représentent des rejets associés aux règles et ne doivent pas être additionnées sans vérifier les éventuels recouvrements entre populations.

### Intégrité en Gold

Les contrôles bloquants mesurés à la porte G ont atteint leurs seuils de conformité.

Le nombre exact d'orphelins par relation doit être confirmé par les requêtes de contrôle spécifiques.

### Client actif

La vue `v_client_actif` doit appliquer la définition métier CD-001 :

**Contrat en cours et cotisations à jour sur trois mois glissants.**

La vue `gold.v_client_actif` retourne **35 985 clients actifs** selon la définition métier CD-001.

À titre de comparaison, la vue Bronze de référence indiquait 38 049 clients actifs, soit un écart de 2 064 clients (-5,42 %). Cet écart doit être analysé en tenant compte des transformations, des rejets et du dédoublonnage ; sa cause exacte n'est pas encore démontrée.

## 5. Traçabilité de trois données (US-28)

Trois enregistrements ont été suivis depuis Bronze jusqu'à Gold à l'aide des identifiants techniques et du lot `S1_G04_001`.

### Trace 1 – Société Meunier SARL

Quatre identifiants sources sont regroupés sous `CLI-033758` :

| Source | Identifiant | Bronze row ID | Silver row ID | Gold CLI |
|---|---|---:|---:|---|
| CIF | K471226 | 16620 | 255320 | CLI-033758 |
| CRM | A-4471 | 34450 | 173569 | CLI-033758 |
| CRM | H-9012 | 73793 | 212675 | CLI-033758 |
| CRM | S-2208 | 88069 | 226862 | CLI-033758 |

Les différentes raisons sociales Bronze (« Société Meunier SARL », « MEUNIER SARL », « Sté Meunier S.A.R.L. » et « SOCIETE MEUNIER S.A.R.L. ») sont normalisées en `MEUNIER SARL` dans Silver et consolidées sous un seul CLI dans Gold.

Les identifiants techniques et le batch ont été vérifiés dans les trois couches.

### Trace 2 – Conservation du zéro initial

Le client CRM `A-10006` a été suivi de `bronze.crm_client` (`bronze_row_id = 8`) à `silver.client` (`silver_row_id = 139357`), puis à `gold.client_unique` (`CLI-000007`).

Son code postal `03100` est conservé à l'identique dans Bronze, Silver et Gold. Le lot est `S1_G04_001` dans les trois couches.

Quatre autres codes postaux commençant par zéro ont également été observés sans perte du zéro initial : `01700`, `01120`, `08200` et `01360`.

### Trace 3 – Adresse de sinistre

Le sinistre `SIN0000006`, associé au contrat `CT0000027`, a été suivi dans les trois couches.

| Élément | Bronze | Silver | Gold |
|---|---|---|---|
| Identifiant technique | `bronze_row_id = 6` | `silver_row_id = 100006` | `SIN0000006` |
| Adresse | 3 rue du 8 Mai 1945 | 3 RUE DU 8 MAI 1945 | 3 RUE DU 8 MAI 1945 |
| Code postal | 02200 | 02200 | 02200 |
| Ville | Soissons | SOISSONS | SOISSONS |
| Lot | S1_G04_001 | S1_G04_001 | S1_G04_001 |

La normalisation de l'adresse et la conservation des informations géographiques sont confirmées pour cet enregistrement.

**Limite :** cette trace démontre le lineage et la normalisation, mais ne prouve pas la conformité au référentiel BAN. La mesure bloquante RQ-014 à Silver reste absente.

**Preuves :** requêtes SQL de traçabilité sur `bronze.crm_client`, `bronze.cif_clients`, `bronze.crm_sinistre`, `silver.client`, `silver.sinistre`, `gold.client_unique`, `gold.xref_identifiants` et `gold.sinistre_certifie`.
## 6. Critères de fin

- [x] Conservation des volumes Bronze = Silver + rejets sur les quatre entités.
- [ ] Idempotence démontrée par deux exécutions comparées.

**Analyse de l'idempotence :** le pipeline applique une stratégie `DELETE + INSERT`. Dans Silver, les suppressions sont filtrées par `_batch_id`, tandis que les quatre tables Gold sont entièrement vidées avant leur reconstruction. La fonction `ecrire()` utilise `if_exists="append"` et une transaction distincte pour chaque écriture. Le mécanisme vise à éviter les doublons après une réexécution complète, mais aucune comparaison entre deux exécutions n'a été réalisée. L'idempotence reste donc non démontrée. Une interruption entre la suppression et le rechargement peut également laisser des données incomplètes.
- [ ] Toutes les règles bloquantes Silver couvertes, notamment RQ-014.
- [ ] Absence d'orphelins Gold démontrée par les requêtes détaillées (contrôles réalisés, validation métier de `cli_assure` restant à obtenir).

**Contrôles d'intégrité référentielle Gold – lot `S1_G04_001` :**

- `gold.xref_identifiants` → `gold.client_unique` : 0 référence orpheline ; 0 client sans correspondance.
- `gold.sinistre_certifie` → `gold.contrat_certifie` : 0 sinistre sans contrat sur 96 532 sinistres.
- `gold.contrat_certifie.cli_souscripteur` → `gold.client_unique.cli_id` : 0 référence absente ou NULL sur 95 866 contrats.
- `gold.contrat_certifie.cli_assure` → `gold.client_unique.cli_id` : 0 référence invalide parmi 57 240 valeurs non NULL.
- `cli_assure` est NULL pour 38 626 contrats (40,29 %). Le caractère obligatoire ou facultatif de cet attribut doit être confirmé par le Data Owner.

**Conclusion :** aucune référence orpheline détectée dans les relations contrôlées. La complétude de `cli_assure` reste soumise à une clarification métier.
- [x] Trois traces complètes avec identifiants de ligne et de lot.

## 7. Difficultés, écarts et reprise

**Difficultés rencontrées :** normalisation des données hétérogènes, gestion des rejets, contrôles de cohérence entre couches et rapprochement des identités.

Le traitement des adresses de sinistre constitue une limite connue : le rapprochement avec BAN n'est pas entièrement couvert par une mesure bloquante RQ-014.

**Temps perdu :** [À COMPLÉTER].

**Point de reprise :** [À COMPLÉTER].

**Améliorations proposées :** compléter la mesure RQ-014, conserver les preuves d'idempotence et automatiser les trois démonstrations de lineage au niveau des enregistrements.
