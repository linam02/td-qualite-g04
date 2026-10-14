# Journal des décisions

Une ligne par décision de seuil, de sévérité, de définition ou de règle de survie. Une décision sans rôle ni justification chiffrée n'est pas une décision. Ce journal alimente la partie « La décision » du dossier go/no-go.

| N° | Date | Séance | Règle ou objet | Décision (ce qui est arrêté) | Justification chiffrée (preuve) | Rôle décideur | Alternative écartée |
# Journal des décisions

Une ligne par décision de seuil, de sévérité, de définition ou de règle de survie. Une décision sans rôle ni justification chiffrée n'est pas une décision. Ce journal alimente la partie « La décision » du dossier go/no-go.

| N° | Date | Séance | Règle ou objet | Décision (ce qui est arrêté) | Justification chiffrée (preuve) | Rôle décideur | Alternative écartée |
|---|---|---|---|---|---|---|---|
| 1 | 14/10/2026 | S1 | Lot d'ingestion bronze | Le lot de référence est `L-2026-10-01` (date de référence 01/10/2026, comme `pipelines/aq.py`). Le lot d'essai `L-2026-10-14` est supprimé de bronze, de `dq.dq_history` et de `dq.lot_ingestion`, puis le bon lot est réingéré par `pipelines/S1_g04_mesures.py` | Deux lots coexistants doublaient bronze (200 000 lignes au lieu de 100 000 dans crm_client) et faussaient les scripts qui lisent bronze sans filtre de lot ; après réingestion : porte B à 0 écart sur les 7 tables, RQ-005 = 1 456 écarts sur 95 437 (`reports/s1/S1_resultats.md`) | Ingénieur qualité (Amadou Macka Diallo) | Conserver les deux lots et filtrer partout par `_batch_id` : écarté, car les scripts de référence S1 à S5 ne filtrent pas tous |
| 2 | … | … | … | … | … | … | … |
| 3 | … | … | … | … | … | … | … |
| 4 | … | … | … | … | … | … | … |
| 5 | … | … | … | … | … | … | … |
| 6 | … | … | … | … | … | … | … |
| 7 | … | … | … | … | … | … | … |
| 8 | … | … | … | … | … | … | … |

Ajoutez des lignes autant que nécessaire. Exemples de décisions attendues : sévérité d'une règle, seuil d'avertissement, définition unique du client actif, convention de la valeur sentinelle, seuils de rapprochement, règle de survie par attribut, seuil de la porte G.

Ajoutez des lignes autant que nécessaire. Exemples de décisions attendues : sévérité d'une règle, seuil d'avertissement, définition unique du client actif, convention de la valeur sentinelle, seuils de rapprochement, règle de survie par attribut, seuil de la porte G.
