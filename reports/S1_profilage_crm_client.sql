-- TD AssurConnect - Groupe 04
-- US-06/07 : Profilage de crm.client

-- 1. Unicite et completude
SELECT
    COUNT(*) AS total_clients,
    COUNT(DISTINCT client_id) AS ids_distincts,
    SUM(email IS NULL OR TRIM(email) = '') AS emails_vides,
    SUM(telephone IS NULL OR TRIM(telephone) = '') AS telephones_vides,
    SUM(nom IS NULL OR TRIM(nom) = '') AS noms_vides,
    SUM(prenom IS NULL OR TRIM(prenom) = '') AS prenoms_vides,
    SUM(date_naissance IS NULL) AS naissances_vides
FROM crm.client;

-- 2. Modalites de type_personne
SELECT type_personne, COUNT(*) AS nb_clients
FROM crm.client
GROUP BY type_personne
ORDER BY nb_clients DESC;

-- 3. Personnes physiques / morales presumees
SELECT
    CASE
        WHEN raison_sociale IS NOT NULL
             AND TRIM(raison_sociale) <> ''
        THEN 'PERSONNE_MORALE_PRESUMEE'
        ELSE 'PERSONNE_PHYSIQUE_PRESUMEE'
    END AS categorie,
    COUNT(*) AS nb_clients,
    SUM(nom IS NULL OR TRIM(nom) = '') AS noms_vides,
    SUM(prenom IS NULL OR TRIM(prenom) = '') AS prenoms_vides,
    SUM(date_naissance IS NULL) AS naissances_vides
FROM crm.client
GROUP BY categorie;

-- 4. Controle des formats
SELECT
    COUNT(*) AS total_clients,
    SUM(
        email IS NOT NULL AND TRIM(email) <> ''
        AND email NOT REGEXP
        '^[^@[:space:]]+@[^@[:space:]]+[.][^@[:space:]]+$'
    ) AS emails_format_invalide,
    SUM(
        telephone IS NOT NULL AND TRIM(telephone) <> ''
        AND telephone NOT REGEXP '^0[0-9]{9}$'
    ) AS telephones_hors_format_fr,
    SUM(
        cp IS NOT NULL AND TRIM(cp) <> ''
        AND cp NOT REGEXP '^[0-9]{5}$'
    ) AS cp_hors_format_fr,
    COUNT(DISTINCT pays) AS nb_pays
FROM crm.client;

-- 5. Analyse par pays
SELECT
    pays,
    COUNT(*) AS nb_clients,
    SUM(
        telephone IS NOT NULL AND TRIM(telephone) <> ''
        AND telephone NOT REGEXP '^0[0-9]{9}$'
    ) AS telephones_hors_format_fr,
    SUM(
        cp IS NOT NULL AND TRIM(cp) <> ''
        AND cp NOT REGEXP '^[0-9]{5}$'
    ) AS cp_hors_format_fr
FROM crm.client
GROUP BY pays
ORDER BY telephones_hors_format_fr DESC;

-- 6. Simulation de normalisation des telephones
WITH t AS (
    SELECT
        telephone,
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(TRIM(telephone), ' ', ''),
                    '.', ''
                ),
                '-', ''
            ),
            '/', ''
        ) AS tel_nettoye
    FROM crm.client
),
n AS (
    SELECT
        telephone,
        CASE
            WHEN tel_nettoye LIKE '+33%'
            THEN CONCAT('0', SUBSTRING(tel_nettoye, 4))
            ELSE tel_nettoye
        END AS tel_normalise
    FROM t
)
SELECT
    SUM(
        telephone IS NOT NULL AND TRIM(telephone) <> ''
        AND telephone NOT REGEXP '^0[0-9]{9}$'
    ) AS hors_format_initial,
    SUM(
        telephone IS NOT NULL AND TRIM(telephone) <> ''
        AND telephone NOT REGEXP '^0[0-9]{9}$'
        AND tel_normalise REGEXP '^0[0-9]{9}$'
    ) AS corrigibles,
    SUM(
        telephone IS NOT NULL AND TRIM(telephone) <> ''
        AND tel_normalise NOT REGEXP '^0[0-9]{9}$'
    ) AS restent_hors_format
FROM n;