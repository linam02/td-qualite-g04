
-- US-09 : Definitions du client actif
-- Date de reference : 2026-10-01
-- Population : souscripteurs distincts

-- Definition commerciale : contrat en vigueur
SELECT 'Commerciale' AS definition,
       COUNT(DISTINCT souscripteur_id) AS nb_clients
FROM crm.contrat
WHERE date_debut <= '2026-10-01'
  AND (date_fin IS NULL OR date_fin >= '2026-10-01')

UNION ALL

-- Definition sinistres : declaration dans les 12 derniers mois
SELECT 'Sinistres',
       COUNT(DISTINCT c.souscripteur_id)
FROM crm.contrat c
JOIN crm.sinistre s ON s.contrat_id = c.contrat_id
WHERE s.date_declaration > '2025-10-01'
  AND s.date_declaration <= '2026-10-01'

UNION ALL

-- Definition risques : contrat en vigueur et sinistre recent
SELECT 'Risques',
       COUNT(DISTINCT c.souscripteur_id)
FROM crm.contrat c
JOIN crm.sinistre s ON s.contrat_id = c.contrat_id
WHERE c.date_debut <= '2026-10-01'
  AND (c.date_fin IS NULL OR c.date_fin >= '2026-10-01')
  AND s.date_declaration > '2025-10-01'
  AND s.date_declaration <= '2026-10-01';


-- Définition officielle CD-001 / RQ-018
-- Date de référence : 2026-10-01
-- Résultat observé : 38049 clients actifs

SELECT COUNT(DISTINCT souscripteur_id) AS clients_actifs_cd001
FROM crm.contrat
WHERE date_debut <= '2026-10-01'
  AND (date_fin IS NULL OR date_fin >= '2026-10-01')
  AND date_derniere_cotisation BETWEEN
      DATE_SUB('2026-10-01', INTERVAL 3 MONTH)
      AND '2026-10-01';