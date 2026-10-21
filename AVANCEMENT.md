# Avancement du groupe

Groupe : [À COMPLÉTER]

Mettez à jour ce tableau à chaque fin de séance (et dès qu'une story change d'état). Statut : `À faire`, `En cours`, `Fait`, `Bloqué`. La preuve est un chemin du dépôt (notebook, fichier de checks, requête) ou une commande ; pas de preuve, pas de `Fait`.

| Séance | Story | Intitulé | Statut | Preuve (chemin ou commande) | Remarque |
|---|---|---|---|---|---|
| S1 | US-01 | Inventorier les sources | Fait | `pipelines/S1_g04_mesures.py` (US-01), `reports/s1/S1_resultats.md` | 7 tables, 0 doublon de clé |
| S1 | US-02 | Alimenter bronze | Fait | `pipelines/S1_g04_mesures.py` (US-02) | lot L-2026-10-01, 4 métadonnées par ligne |
| S1 | US-03 | Porte B : réconcilier source et bronze | Fait | `pipelines/S1_g04_mesures.py` (US-03, épreuves 1 à 3), `dq.dq_history` | 0 écart sur 7 tables, écart volontaire détecté |
| S1 | US-04 | Dictionnaire du CIF | Fait | `livrables/S1_bronze_profilage.md` section 4 | 10 colonnes clients + 4 compte |
| S1 | US-06 | Profil de crm.client | En cours | `reports/ydata_profiling_client.html`, `livrables/S1_bronze_profilage.md` section 3 | section YData à compléter |
| S1 | US-07 | Motifs code postal, téléphone, pays | Fait | `pipelines/S1_g04_mesures.py` (US-07) | RQ-005 : 1 456 sur 95 437 |
| S1 | US-09 | Trois définitions du client actif | Fait | `pipelines/S1_g04_mesures.py` (US-09) | 50 508 / 44 116 / 38 049 |
| S2 | US-10 | Règles en tests Great Expectations | À faire | … | |
| S2 | US-11 | Lignes en échec | À faire | … | |
| S2 | US-13 | Âge à la date de début du contrat | À faire | … | |
| S2 | US-15 | Mesure de référence sur bronze | À faire | … | |
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
