# Avancement du groupe

Groupe : g04

Mettez à jour ce tableau à chaque fin de séance (et dès qu'une story change d'état). Statut : `À faire`, `En cours`, `Fait`, `Bloqué`. La preuve est un chemin du dépôt (notebook, fichier de checks, requête) ou une commande ; pas de preuve, pas de `Fait`.

| Séance | Story | Intitulé | Statut | Preuve (chemin ou commande) | Remarque |
|---|---|---|---|---|---|
| S1 | US-01 | Inventorier les sources | Fait | reports/S1_profilage_sources.sql |7 tables, 385 262 lignes, clés primaires identifiées |
| S1 | US-02 | Alimenter bronze | Fait | pipelines/ingest_bronze.py |385 262 lignes chargées en Bronze |
| S1 | US-03 | Porte B : réconcilier source et bronze | Fait | pipelines/check_gate_b.py |Gate B : GO, 7/7 tables conformes |
| S1 | US-04 | Dictionnaire du CIF | Fait | reports/S1_dictionnaire_cif.sql |10 colonnes identifiées |
| S1 | US-06 | Profil de crm.client | Fait | reports/S1_profilage_crm_client.sql |Profilage de 100 000 clients |
| S1 | US-07 | Motifs code postal, téléphone, pays | Fait | reports/S1_profilage_crm_client.sql |Contrôles téléphone, code postal et pays |
| S1 | US-09 | Trois définitions du client actif | Fait | reports/S1_client_actif.sql |3 définitions comparées |
| S2 | US-10 | Règles en tests Great Expectations | Fait | `pipelines/S2_regles_great_expectations.py`, `reports/ge/gx/expectations/` | 8 règles, chaque expectation porte son rule_id |
| S2 | US-11 | Lignes en échec | Fait | `reports/echecs/` (non versionné), `livrables/S2_regles_great_expectations.md` section 2 | 20 lignes RQ-009 classées en 4 familles |
| S2 | US-13 | Âge à la date de début du contrat | Fait | `pipelines/S2_regles_great_expectations.py` (US-13) | 301 à la signature contre 157 à la date de référence |
| S2 | US-15 | Mesure de référence sur bronze | Fait | `dq.dq_history`, couche BRONZE, lot L-2026-10-01 | complétude 88,0 %, 5 règles bloquantes sur 6 sous le seuil |
| S3 | US-12 | Checks Soda, une source par couche | Fait | `soda/configuration.yml`, `soda/checks/bronze/`, `pipelines/S3_integrite_soda.py` | code retour de la porte : 2 (échec), 9 règles bloquantes en échec |
| S3 | US-16 | Clés étrangères | Fait | `pipelines/S3_integrite_soda.py` (US-16) | RQ-012 : 1 000 ; RQ-011 : 200 ; RQ-007 : 3 050 ; sinistre → contrat : 0 |
| S3 | US-17 | Valeur sentinelle | Fait | `soda/checks/bronze/sentinelle_avant.yml`, `soda/checks/contrat_checks.yml` | 40 300 orphelins avant, 300 après ; décision n° 6 |
| S3 | US-18 | Statuts de personne | Fait | `pipelines/S3_integrite_soda.py` (US-18) | RQ-015 : 479 ; RQ-016 : 955 ; décision n° 7 |
| S3 | US-19 | Période de garantie | Fait | `pipelines/S3_integrite_soda.py` (US-19) | 1 200 hors période, dont 344 couverts par un autre contrat ; décision n° 9 |
| S3 | US-14 | Définition unique du client actif | Fait | vue `dq.v_client_actif_bronze`, `pipelines/S3_integrite_soda.py` (US-14) | 38 049 pour les 3 directions ; décision n° 8 |
| S4 | US-21 | Silver : standardiser | Fait | `pipelines/S4_silver_gold.py` (US-21), `silver.client`, `silver.contrat`, `silver.sinistre` | idempotent : signatures identiques sur deux passages |
| S4 | US-22 | Quarantaine | Fait | `dq.rejets` (porte S) | silver + rejets = bronze, écart 0 sur 4 tables |
| S4 | US-23 | Porte S : re-mesurer sur silver | Fait | `pipelines/S4_silver_gold.py` (US-23), `dq.dq_history` couche SILVER | règles bloquantes de la porte S à 100 % |
| S4 | US-24 | Dédoublonnage | Fait | `pipelines/S4_silver_gold.py` (US-24) | 139 350 lignes → 120 480 identités, précision et rappel 1,0 |
| S4 | US-25 | Golden record | Fait | `gold.client_unique`, `gold.xref_identifiants` | Société Meunier : 4 identifiants → CLI-033758 |
| S4 | US-27 | Gold et client actif unique | Fait | `gold.v_client_actif`, `dq.dq_history` couche GOLD | porte G franchie, 0 orphelin, 35 985 clients actifs |
| S4 | US-28 | Traçabilité de trois données | Fait | `pipelines/S4_silver_gold.py` (US-28) | Meunier, code postal 01500, sinistre SIN0000012 |
| S5 | US-29 | Historique des mesures | Fait | `pipelines/S5_certificat_publication.py` (US-29), `dq.v_derniere_mesure`, `reports/go_nogo_historique.csv` | une mesure par règle et par couche ; RQ-004, 006, 008, 014 non mesurées sur silver |
| S5 | US-30 | Courbes d'évolution | Fait | `reports/courbe_qualite.png` | toutes les dimensions à 100 % sur gold sauf la complétude (89,9 %) ; courbe plate non démontrée |
| S5 | US-31 | Certificat de qualité | Fait | `dq.certificat_qualite`, CERT-L-2026-10-01 | GO, 36 règles bloquantes conformes sur 36 ; lot dégradé L-TEST : NO_GO |
| S5 | US-32 | Publication vers le CRM | Fait | `pipelines/S5_certificat_publication.py` (US-32), `crm_cible.*` | 3 refus démontrés ; RQ-025 : 0 écart sur 3 tables |
| S5 | US-34 | Catalogue, propriétaires, lineage | Fait | `catalogue/catalog.json` | 30 tables documentées, lineage de gold.client_unique jusqu'aux sources |
| S5 | US-35 | Dossier go/no-go | En cours | `livrables/DOSSIER_GO_NOGO.md` | GO sous conditions ; signature du Data Owner et échéances à compléter |

Stories d'extension (facultatives) : US-05, US-08, US-20, US-26, US-33. Ajoutez une ligne si vous les traitez.
| S5 | US-33 | Planifier la chaîne quotidienne | Fait | `pipelines/S5_certificat_publication.py` (US-33) | portes B, S, G ouvertes ; une porte fermée bloque la suite |