# Avancement du groupe

Groupe : [À COMPLÉTER]

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
| S3 | US-12 | Checks Soda, une source par couche | À faire | … | |
| S3 | US-16 | Clés étrangères | À faire | … | |
| S3 | US-17 | Valeur sentinelle | À faire | … | |
| S3 | US-18 | Statuts de personne | À faire | … | |
| S3 | US-19 | Période de garantie | À faire | … | |
| S3 | US-14 | Définition unique du client actif | À faire | … | |
| S4 | US-21 | Silver : standardiser | À faire | … | |
| S4 | US-22 | Quarantaine | À faire | … | |
| S4 | US-23 | Porte S : re-mesurer sur silver | À faire | … | |
| S4 | US-24 | Dédoublonnage | À faire | … | |
| S4 | US-25 | Golden record | À faire | … | |
| S4 | US-27 | Gold et client actif unique | À faire | … | |
| S4 | US-28 | Traçabilité de trois données | À faire | … | |
| S5 | US-29 | Historique des mesures | À faire | … | |
| S5 | US-30 | Courbes d'évolution | À faire | … | |
| S5 | US-31 | Certificat de qualité | À faire | … | |
| S5 | US-32 | Publication vers le CRM | À faire | … | |
| S5 | US-34 | Catalogue, propriétaires, lineage | À faire | … | |
| S5 | US-35 | Dossier go/no-go | À faire | … | |

Stories d'extension (facultatives) : US-05, US-08, US-20, US-26, US-33. Ajoutez une ligne si vous les traitez.
