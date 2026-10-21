
-- ============================================================
-- TD ASSURCONNECT - GROUPE 04
-- SESSION 1 - US-04 : DICTIONNAIRE DU CIF
-- Source : cif.clients
-- ============================================================

-- 1. Nombre de lignes et unicite de l'identifiant client
SELECT
    COUNT(*) AS total_lignes,
    COUNT(DISTINCT column0) AS id_distincts,
    SUM(column0 IS NULL OR TRIM(column0) = '') AS id_vides
FROM cif.clients;


-- 2. Completude des 10 colonnes
SELECT
    COUNT(*) AS total_lignes,
    SUM(column0 IS NULL OR TRIM(column0) = '') AS id_vides,
    SUM(column1 IS NULL OR TRIM(column1) = '') AS noms_vides,
    SUM(column2 IS NULL OR TRIM(column2) = '') AS prenoms_vides,
    SUM(column3 IS NULL OR TRIM(column3) = '') AS dates_naissance_vides,
    SUM(column4 IS NULL OR TRIM(column4) = '') AS adresses_vides,
    SUM(column5 IS NULL OR TRIM(column5) = '') AS codes_postaux_vides,
    SUM(column6 IS NULL OR TRIM(column6) = '') AS villes_vides,
    SUM(column7 IS NULL OR TRIM(column7) = '') AS pays_vides,
    SUM(column8 IS NULL OR TRIM(column8) = '') AS telephones_vides,
    SUM(column9 IS NULL OR TRIM(column9) = '') AS emails_vides
FROM cif.clients;


-- 3. Controle des formats
SELECT
    COUNT(*) AS total_lignes,

    SUM(
        column3 IS NOT NULL
        AND TRIM(column3) <> ''
        AND column3 NOT REGEXP '^[0-9]{2}/[0-9]{2}/[0-9]{4}$'
    ) AS dates_format_invalide,

    SUM(
        column5 IS NOT NULL
        AND TRIM(column5) <> ''
        AND column5 NOT REGEXP '^[0-9]{5}$'
    ) AS codes_postaux_format_fr_invalide,

    SUM(
        column8 IS NOT NULL
        AND TRIM(column8) <> ''
        AND column8 NOT REGEXP '^0[0-9]{9}$'
    ) AS telephones_format_invalide,

    COUNT(DISTINCT column7) AS nb_codes_pays
FROM cif.clients;


-- 4. Codes postaux hors format francais, par pays
SELECT
    column7 AS code_pays,
    COUNT(*) AS nb_codes_postaux_hors_format,
    MIN(column5) AS exemple_code_postal
FROM cif.clients
WHERE column5 IS NOT NULL
  AND TRIM(column5) <> ''
  AND column5 NOT REGEXP '^[0-9]{5}$'
GROUP BY column7
ORDER BY nb_codes_postaux_hors_format DESC;


-- 5. Repartition des clients par pays
SELECT
    column7 AS code_pays,
    COUNT(*) AS nb_clients
FROM cif.clients
GROUP BY column7
ORDER BY nb_clients DESC;


-- 6. Integrite referentielle avec cif.pays
SELECT
    c.column7 AS code_pays,
    COUNT(*) AS nb_clients,
    CASE
        WHEN p.code_pays IS NULL
            THEN 'ABSENT DU REFERENTIEL'
        ELSE 'PRESENT'
    END AS statut
FROM cif.clients c
LEFT JOIN cif.pays p
    ON c.column7 = p.code_pays
GROUP BY c.column7, p.code_pays
ORDER BY nb_clients DESC;


-- 7. Synthese des anomalies de referentiel
SELECT
    COUNT(*) AS nb_clients_sans_pays_reference
FROM cif.clients c
LEFT JOIN cif.pays p
    ON c.column7 = p.code_pays
WHERE p.code_pays IS NULL;


-- ============================================================
-- DECISIONS US-04
-- column0 : identifiant client (cle metier candidate)
-- column3 : date de naissance, conversion DATE en Silver
-- column5 : code postal en VARCHAR, validation selon le pays
-- column7 : code pays, reference cif.pays
-- column8 : telephone en VARCHAR
-- column9 : email nullable
-- ============================================================
