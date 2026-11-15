# S5 · Certifier, publier vers le CRM, gouverner

Groupe : [À COMPLÉTER]  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-5`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Historique des mesures (US-29, US-30)

Une ligne par règle mesurée ; laissez vide la couche où la règle ne s'applique pas, et dites pourquoi.

| Règle | Dimension | Taux bronze | Taux silver | Taux gold | Évolution (monte, stable, descend) | Explication |
|---|---|---|---|---|---|---|
| … | … | … | … | … | … | … |
| … | … | … | … | … | … | … |
| … | … | … | … | … | … | … |
| … | … | … | … | … | … | … |
| … | … | … | … | … | … | … |
| … | … | … | … | … | … | … |

Courbes (chemin des images) : [À COMPLÉTER]

Toute règle qui descend d'une couche à l'autre : cause (filtre mal posé, conversion, effet de la quarantaine) et preuve : [À COMPLÉTER]

## 2. Certificat de qualité (US-31)

| Élément | Valeur |
|---|---|
| Numéro du certificat | … |
| Lot | … |
| Décision (GO ou NO_GO) | … |
| Règles bloquantes testées | … |
| Règles bloquantes conformes | … |
| Écarts connus (avertissements) | … |
| Empreinte du gold | … |
| Signataire (rôle) | … |

Requête de décision (chemin) : [À COMPLÉTER]

Épreuve du NO_GO : lot volontairement dégradé (comment), décision obtenue, preuve : [À COMPLÉTER]

Règles bloquantes non mesurées par votre pipeline et donc non couvertes par le certificat : [À COMPLÉTER]

## 3. Publication vers le CRM (US-32)

Script (chemin) : [À COMPLÉTER]

| Scénario | Message obtenu | Chargement effectué ? | Preuve |
|---|---|---|---|
| Sans certificat | … | … | … |
| Certificat NO_GO | … | … | … |
| Gold modifié après émission du certificat | … | … | … |
| Certificat GO et gold intact | … | … | … |

Réconciliation après chargement (RQ-025) :

| Table | Lignes gold | Lignes CRM cible | Somme de contrôle gold | Somme de contrôle CRM cible | Écart |
|---|---|---|---|---|---|
| client | … | … | … | … | … |
| contrat | … | … | … | … | … |
| sinistre | … | … | … | … | … |

Le chargement est-il tout-ou-rien ? Comment l'avez-vous vérifié : [À COMPLÉTER]

## 3 bis. Gouvernance (US-34)

Fiche de catalogue de `gold.client_unique` (chemin) : `catalogue/catalog.json`, entrée `"name": "gold.client_unique"`. Le catalogue documente 30 tables (sources cif et crm, bronze, silver, gold, dq), avec leurs colonnes, leur propriétaire, leur steward, le glossaire et le lineage. Il est généré par `notebooks/S5_certificat_publication.ipynb`, cellule US-34.

Définition de la table : référentiel unique des personnes d'AssurConnect ; une ligne par client réel (CLI), obtenue par dédoublonnage des clients CRM et CIF (139 350 identifiants source réunis en 120 480 clients, 11 colonnes), avec son golden record et son statut (ACTIF selon la fiche CD-001, INACTIF, ASSURE, PROSPECT).

| Élément | Valeur |
|---|---|
| Propriétaire (Data Owner) | Claire Dumontier, Directrice Risques, Data Owner du domaine « client » |
| Steward (Data Steward) | Yanis Belkacem, responsable qualité des données |
| Définition de « client actif » rattachée à la fiche | Contrat en cours ET à jour de cotisation sur 3 mois glissants (fiche CD-001, validée le 01/04/2026 par Claire Dumontier), publiée par une seule vue `gold.v_client_actif` : 35 985 clients actifs |
| Règles RQ rattachées à la table | 7 règles mesurées sur gold : RQ-003 (téléphone renseigné, avertissement : 89,9 % pour 98 %), RQ-005 (code postal FR, 100 %), RQ-007 (pays ISO, 100 %), RQ-015 (prospect sans contrat, 100 %), RQ-018 (client actif CD-001, 100 %), RQ-019 (un seul CLI par personne, 100 %), RQ-020 (clé unique, 100 %) |

Lineage de `gold.client_unique` jusqu'aux sources :

    gold.client_unique  <- silver.client         [dédoublonnage, porte G, RQ-019]
      silver.client     <- bronze.crm_client     [standardisation et quarantaine, porte S]
        bronze.crm_client  <- crm.client         [ingestion, porte B, RQ-021]
      silver.client     <- bronze.cif_clients    [standardisation et quarantaine, porte S]
        bronze.cif_clients <- cif.clients        [ingestion, porte B, RQ-021]
    en aval : gold.client_unique -> crm_cible.client   [publication sous certificat CERT-L-2026-10-01, RQ-025 : 120 480 lignes, 0 écart]

La correspondance ligne à ligne (CLI vers identifiant source, ligne silver, ligne bronze et lot) est portée par `gold.xref_identifiants` (139 350 lignes). Exemple : la Société Meunier (CLI-033758) remonte vers ses 4 identifiants source K471226 (CIF), A-4471, H-9012 et S-2208 (CRM), lot L-2026-10-01 (US-28).

Limites de gouvernance observées dans le catalogue :
- **Owner et Steward confondus** : pour 26 tables sur 30, la même personne (Yanis Belkacem) est Data Owner et Data Steward. Or, selon le cours, le Data Owner décide et rend des comptes, tandis que le Data Steward applique et escalade ; un même rôle ne peut pas valider ce qu'il applique. Un Data Owner métier doit être nommé pour les domaines contrat et sinistre (par exemple la direction des Sinistres).
- **Domaine « client » incohérent** : l'Owner est attribué automatiquement aux tables dont le nom finit par « client ». Les tables CIF `cif.clients` et `bronze.cif_clients` (finales en « clients ») ne sont donc pas rattachées à Claire Dumontier, alors qu'elles alimentent `gold.client_unique`. La propriété d'un domaine doit être déclarée, pas déduite du nom des tables.

## 4. Décisions de la séance

Reportez dans `JOURNAL_DECISIONS.md` chaque seuil, sévérité ou règle de survie arrêté, avec son rôle. Nombre de décisions ajoutées en S5 : [À COMPLÉTER]

## 5. Critères de fin

- [ ] Un lot volontairement dégradé produit un NO_GO, le lot nominal un GO.
- [ ] La publication refuse sans certificat, avec une décision NO_GO, et quand le gold a changé.
- [ ] Après un chargement réussi, comptage et somme de contrôle sont égaux entre gold et CRM cible.
- [ ] Chaque décision de seuil ou de sévérité est attribuée à un rôle.

## 6. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
