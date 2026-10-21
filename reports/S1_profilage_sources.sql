
-- US-01 : Inventaire des sources
-- Groupe 04

-- Nombre de lignes par table source
SELECT 'crm.client' AS table_source, COUNT(*) AS lignes
FROM crm.client
UNION ALL
SELECT 'crm.contrat', COUNT(*) FROM crm.contrat
UNION ALL
SELECT 'crm.sinistre', COUNT(*) FROM crm.sinistre
UNION ALL
SELECT 'crm.type_contrat', COUNT(*) FROM crm.type_contrat
UNION ALL
SELECT 'cif.clients', COUNT(*) FROM cif.clients
UNION ALL
SELECT 'cif.compte', COUNT(*) FROM cif.compte
UNION ALL
SELECT 'cif.pays', COUNT(*) FROM cif.pays;

-- Cles primaires declarees
SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA IN ('crm', 'cif')
  AND CONSTRAINT_NAME = 'PRIMARY'
ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION;