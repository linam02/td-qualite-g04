
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-003"
BATCH_ID = os.getenv("DQ_BATCH_ID", "S1_G04_001")
DB_URL = os.getenv(
    "DQ_DB_URL",
    "mysql+pymysql://root:root@mariadb:3306"
)

engine = create_engine(DB_URL)

query = text("""
SELECT
    t.contrat_id,
    t.souscripteur_id,
    c.telephone,
    CASE
        WHEN c.client_id IS NULL
            THEN 'REFERENCE_ABSENTE'
        WHEN c.telephone IS NULL
             OR TRIM(c.telephone) = ''
            THEN 'ECHEC'
        ELSE 'CONFORME'
    END AS statut_rq003
FROM bronze.crm_contrat t
LEFT JOIN bronze.crm_client c
    ON t.souscripteur_id = c.client_id
    AND t._batch_id = c._batch_id
WHERE t._batch_id = :batch_id
""")

with engine.connect() as connection:
    df = pd.read_sql(
        query,
        connection,
        params={"batch_id": BATCH_ID}
    )

evaluables = df[
    df["statut_rq003"].isin(["CONFORME", "ECHEC"])
].copy()

validator = gx.from_pandas(evaluables)

# RQ-003 : seuil minimum de conformité de 98 %
result = validator.expect_column_values_to_be_in_set(
    column="statut_rq003",
    value_set=["CONFORME"],
    mostly=0.98,
    result_format="COMPLETE",
    meta={"rule_id": RULE_ID}
)

total = len(df)
testees = len(evaluables)
echecs = int((evaluables["statut_rq003"] == "ECHEC").sum())
reussites = testees - echecs
taux = 100 * reussites / testees if testees else 0

print(f"Règle : {RULE_ID}")
print(f"Lot : {BATCH_ID}")
print(f"Contrats totaux : {total}")
print(f"Lignes testées : {testees}")
print(f"Lignes en échec : {echecs}")
print(f"Taux de réussite : {taux:.2f}%")
print(f"Seuil requis : 98.00%")
print(f"Expectation réussie : {result['success']}")
print("Sévérité : AVERTISSEMENT")

print("\nRépartition des statuts :")
print(df["statut_rq003"].value_counts().to_string())

statut = (
    "GO"
    if result["success"] and testees > 0
    else "NO-GO"
)
print(f"\nStatut de la règle : {statut}")
