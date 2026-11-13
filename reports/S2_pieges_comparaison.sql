-- SEANCE 2 - US-10
-- Preuves des pieges rencontres
-- Lot : S1_G04_001

-- RQ-003 : NULL uniquement vs NULL, vide et blanc
SELECT
    'RQ-003' AS regle,
    SUM(CASE WHEN c.telephone IS NULL THEN 1 ELSE 0 END) AS avant_correction,
    SUM(CASE WHEN c.telephone IS NULL OR TRIM(c.telephone) = '' THEN 1 ELSE 0 END) AS apres_correction
FROM bronze.crm_contrat t
JOIN bronze.crm_client c
    ON t.souscripteur_id = c.client_id
    AND t._batch_id = c._batch_id
WHERE t._batch_id = 'S1_G04_001';

-- RQ-005 : Tous les pays vs France uniquement
SELECT
    'RQ-005' AS regle,
    SUM(CASE WHEN cp IS NULL OR NOT (cp REGEXP '^[0-9]{5}$') THEN 1 ELSE 0 END) AS avant_correction,
    SUM(CASE WHEN LOWER(TRIM(pays)) IN ('fr','france','f','frnace')
        AND (cp IS NULL OR NOT (cp REGEXP '^[0-9]{5}$'))
        THEN 1 ELSE 0 END) AS apres_correction
FROM bronze.crm_client
WHERE _batch_id = 'S1_G04_001';

-- RQ-009 : Comparaison souple vs comparaison exacte
SELECT
    'RQ-009' AS regle,
    SUM(CASE WHEN type_personne IS NULL
        OR LOWER(TRIM(type_personne)) COLLATE utf8mb4_unicode_ci
        NOT IN ('prospect','souscripteur','assure')
        THEN 1 ELSE 0 END) AS avant_correction,
    SUM(CASE WHEN type_personne IS NULL
        OR BINARY type_personne NOT IN
        (BINARY 'prospect', BINARY 'souscripteur', BINARY 'assure')
        THEN 1 ELSE 0 END) AS apres_correction
FROM bronze.crm_client
WHERE _batch_id = 'S1_G04_001';
