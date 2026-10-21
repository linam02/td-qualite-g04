
-- ============================================================
-- TD ASSURCONNECT - GROUPE 04
-- SEANCE 1 - US-03 : CONTROLES GATE B
-- Batch : S1_G04_001
--
-- RQ-021 : Reconciliation SOURCES / BRONZE
-- RQ-022 : Verification des metadonnees Bronze
--
-- Les index sont crees uniquement s'ils n'existent pas.
-- Les requetes de controle ne modifient pas les donnees.
-- ============================================================


-- ============================================================
-- 1. INDEX POUR OPTIMISER LA RECONCILIATION RQ-021
-- ============================================================
-- Ces index ont ete ajoutes pendant les tests.
-- Verifier leur existence avant toute creation.

SELECT
    TABLE_NAME,
    INDEX_NAME,
    SEQ_IN_INDEX,
    COLUMN_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'bronze'
  AND INDEX_NAME LIKE 'idx_gateb%'
ORDER BY
    TABLE_NAME,
    INDEX_NAME,
    SEQ_IN_INDEX;

-- Commandes utilisees lors de la preparation :
--
-- CREATE INDEX idx_gateb_batch_sinistre
-- ON bronze.crm_sinistre (_batch_id, sinistre_id);
--
-- CREATE INDEX idx_gateb_batch_client
-- ON bronze.cif_clients (_batch_id, column0);
--
-- CREATE INDEX idx_gateb_batch_compte
-- ON bronze.cif_compte (_batch_id, column0);
--
-- CREATE INDEX idx_gateb_batch_pays
-- ON bronze.cif_pays (_batch_id, code_pays);


-- ============================================================
-- 2. RQ-021 : RECONCILIATION DES COMPTAGES
-- ============================================================

SELECT 'crm_client' AS table_cible,
       (SELECT COUNT(*) FROM crm.client) AS nb_source,
       (SELECT COUNT(*) FROM bronze.crm_client
        WHERE _batch_id = 'S1_G04_001') AS nb_bronze

UNION ALL

SELECT 'crm_contrat',
       (SELECT COUNT(*) FROM crm.contrat),
       (SELECT COUNT(*) FROM bronze.crm_contrat
        WHERE _batch_id = 'S1_G04_001')

UNION ALL

SELECT 'crm_sinistre',
       (SELECT COUNT(*) FROM crm.sinistre),
       (SELECT COUNT(*) FROM bronze.crm_sinistre
        WHERE _batch_id = 'S1_G04_001')

UNION ALL

SELECT 'crm_type_contrat',
       (SELECT COUNT(*) FROM crm.type_contrat),
       (SELECT COUNT(*) FROM bronze.crm_type_contrat
        WHERE _batch_id = 'S1_G04_001')

UNION ALL

SELECT 'cif_clients',
       (SELECT COUNT(*) FROM cif.clients),
       (SELECT COUNT(*) FROM bronze.cif_clients
        WHERE _batch_id = 'S1_G04_001')

UNION ALL

SELECT 'cif_compte',
       (SELECT COUNT(*) FROM cif.compte),
       (SELECT COUNT(*) FROM bronze.cif_compte
        WHERE _batch_id = 'S1_G04_001')

UNION ALL

SELECT 'cif_pays',
       (SELECT COUNT(*) FROM cif.pays),
       (SELECT COUNT(*) FROM bronze.cif_pays
        WHERE _batch_id = 'S1_G04_001');


-- Le controle detaille des hash est realise par :
-- pipelines/check_gate_b.py


-- ============================================================
-- 3. RQ-022 : VERIFICATION DES METADONNEES
-- ============================================================

SELECT
    table_cible,
    nb_testees,
    nb_echecs
FROM (
    SELECT 'crm_client' AS table_cible,
           COUNT(*) AS nb_testees,
           SUM(
               CASE WHEN
                   _batch_id IS NULL
                   OR _batch_id <> 'S1_G04_001'
                   OR _source_system IS NULL
                   OR _source_system <> 'crm'
                   OR _ingested_at IS NULL
                   OR _row_hash IS NULL
                   OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
               THEN 1 ELSE 0 END
           ) AS nb_echecs
    FROM bronze.crm_client

    UNION ALL

    SELECT 'crm_contrat', COUNT(*),
           SUM(CASE WHEN
               _batch_id IS NULL
               OR _batch_id <> 'S1_G04_001'
               OR _source_system IS NULL
               OR _source_system <> 'crm'
               OR _ingested_at IS NULL
               OR _row_hash IS NULL
               OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
           THEN 1 ELSE 0 END)
    FROM bronze.crm_contrat

    UNION ALL

    SELECT 'crm_sinistre', COUNT(*),
           SUM(CASE WHEN
               _batch_id IS NULL
               OR _batch_id <> 'S1_G04_001'
               OR _source_system IS NULL
               OR _source_system <> 'crm'
               OR _ingested_at IS NULL
               OR _row_hash IS NULL
               OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
           THEN 1 ELSE 0 END)
    FROM bronze.crm_sinistre

    UNION ALL

    SELECT 'crm_type_contrat', COUNT(*),
           SUM(CASE WHEN
               _batch_id IS NULL
               OR _batch_id <> 'S1_G04_001'
               OR _source_system IS NULL
               OR _source_system <> 'crm'
               OR _ingested_at IS NULL
               OR _row_hash IS NULL
               OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
           THEN 1 ELSE 0 END)
    FROM bronze.crm_type_contrat

    UNION ALL

    SELECT 'cif_clients', COUNT(*),
           SUM(CASE WHEN
               _batch_id IS NULL
               OR _batch_id <> 'S1_G04_001'
               OR _source_system IS NULL
               OR _source_system <> 'cif'
               OR _ingested_at IS NULL
               OR _row_hash IS NULL
               OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
           THEN 1 ELSE 0 END)
    FROM bronze.cif_clients

    UNION ALL

    SELECT 'cif_compte', COUNT(*),
           SUM(CASE WHEN
               _batch_id IS NULL
               OR _batch_id <> 'S1_G04_001'
               OR _source_system IS NULL
               OR _source_system <> 'cif'
               OR _ingested_at IS NULL
               OR _row_hash IS NULL
               OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
           THEN 1 ELSE 0 END)
    FROM bronze.cif_compte

    UNION ALL

    SELECT 'cif_pays', COUNT(*),
           SUM(CASE WHEN
               _batch_id IS NULL
               OR _batch_id <> 'S1_G04_001'
               OR _source_system IS NULL
               OR _source_system <> 'cif'
               OR _ingested_at IS NULL
               OR _row_hash IS NULL
               OR _row_hash NOT REGEXP '^[0-9a-fA-F]{16}$'
           THEN 1 ELSE 0 END)
    FROM bronze.cif_pays
) AS controles;


-- ============================================================
-- 4. HISTORIQUE DES CONTROLES GATE B
-- ============================================================

SELECT
    batch_id,
    couche,
    rule_id,
    table_cible,
    nb_testees,
    nb_echecs,
    taux_conformite
FROM dq.dq_history
WHERE batch_id = 'S1_G04_001'
  AND couche = 'BRONZE'
  AND rule_id IN ('RQ-021', 'RQ-022')
ORDER BY rule_id, table_cible;


-- ============================================================
-- 5. DECISION GATE B
-- ============================================================

SELECT
    CASE
        WHEN COUNT(*) = 14
         AND SUM(
             CASE
                 WHEN nb_echecs = 0
                  AND taux_conformite >= 100
                 THEN 0 ELSE 1
             END
         ) = 0
        THEN 'GO'
        ELSE 'NO-GO'
    END AS decision_gate_b
FROM dq.dq_history
WHERE batch_id = 'S1_G04_001'
  AND couche = 'BRONZE'
  AND rule_id IN ('RQ-021', 'RQ-022');
