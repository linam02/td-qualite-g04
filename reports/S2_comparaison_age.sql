-- SEANCE 2 - US-13 : Comparaison de l'age
-- Regle RQ-002
-- Lot : S1_G04_001

-- 1. Comparaison : date de debut vs date du jour
SELECT
    COUNT(*) AS nb_testees,
    SUM(
        CASE WHEN DATE_ADD(c.date_naissance, INTERVAL 18 YEAR)
             > STR_TO_DATE(t.date_debut, '%Y-%m-%d')
        THEN 1 ELSE 0 END
    ) AS mineurs_date_debut,
    SUM(
        CASE WHEN DATE_ADD(c.date_naissance, INTERVAL 18 YEAR)
             > CURDATE()
        THEN 1 ELSE 0 END
    ) AS mineurs_aujourdhui
FROM bronze.crm_contrat t
JOIN crm.client c
    ON t.souscripteur_id = c.client_id
WHERE t._batch_id = 'S1_G04_001'
  AND (c.raison_sociale IS NULL OR TRIM(c.raison_sociale) = '')
  AND c.date_naissance IS NOT NULL
  AND STR_TO_DATE(t.date_debut, '%Y-%m-%d') IS NOT NULL;

-- 2. Exemple concret : contrat CT0000387
SELECT
    t.contrat_id,
    c.date_naissance,
    t.date_debut,
    TIMESTAMPDIFF(
        YEAR, c.date_naissance,
        STR_TO_DATE(t.date_debut, '%Y-%m-%d')
    ) AS age_debut,
    TIMESTAMPDIFF(
        YEAR, c.date_naissance, CURDATE()
    ) AS age_aujourdhui
FROM bronze.crm_contrat t
JOIN crm.client c
    ON t.souscripteur_id = c.client_id
WHERE t._batch_id = 'S1_G04_001'
  AND t.contrat_id = 'CT0000387';
