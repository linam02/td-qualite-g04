START TRANSACTION;

DELETE FROM dq.dq_history
WHERE batch_id = 'S1_G04_001'
  AND couche = 'BRONZE'
  AND rule_id IN ('RQ-001','RQ-002','RQ-003','RQ-005','RQ-009','RQ-010','RQ-020');

INSERT INTO dq.dq_history
(batch_id, couche, rule_id, table_cible, nb_testees, nb_echecs)
VALUES
('S1_G04_001','BRONZE','RQ-001','crm_contrat',100000,800),
('S1_G04_001','BRONZE','RQ-002','crm_contrat',92996,301),
('S1_G04_001','BRONZE','RQ-003','crm_contrat',99000,12024),
('S1_G04_001','BRONZE','RQ-005','crm_client',98037,1493),
('S1_G04_001','BRONZE','RQ-009','crm_client',100000,200),
('S1_G04_001','BRONZE','RQ-010','crm_contrat',100000,600),
('S1_G04_001','BRONZE','RQ-020','crm_client',100000,0),
('S1_G04_001','BRONZE','RQ-020','crm_contrat',100000,0),
('S1_G04_001','BRONZE','RQ-020','crm_sinistre',100000,0),
('S1_G04_001','BRONZE','RQ-020','crm_type_contrat',12,0),
('S1_G04_001','BRONZE','RQ-020','cif_clients',40000,0),
('S1_G04_001','BRONZE','RQ-020','cif_compte',45000,0),
('S1_G04_001','BRONZE','RQ-020','cif_pays',250,0);

COMMIT;
