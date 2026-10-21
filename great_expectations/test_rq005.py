
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-005"
BATCH_ID = os.getenv("DQ_BATCH_ID", "S1_G04_001")
DB_URL = os.getenv(
    "DQ_DB_URL",
    "mysql+pymysql://root:root@mariadb:3306"
)

engine = create_engine(DB_URL)

query = text("""
SELECT
    client_id,
    pays,
    cp,
    CASE
        WHEN LOWER(TRIM(pays)) IN
             ('fr', 'france', 'f', 'frnace')
        THEN
            CASE
                WHEN cp REGEXP '^[0-9]{5}$'
                    THEN 'CONFORME'
                ELSE 'ECHEC'
            END
        WHEN pays IS NULL OR TRIM(pays) = ''
            THEN 'PAYS_INCONNU'
        ELSE 'NON_APPLICABLE'
    END AS statut_rq005
FROM bronze.crm_client
WHERE _batch_id = :batch_id
""")

with engine.connect() as connection:
    df = pd.read_sql(
        query,
        connection,
        params={"batch_id": BATCH_ID}
    )

evaluables = df[
    df["statut_rq005"].isin(["CONFORME", "ECHEC"])
].copy()

validator = gx.from_pandas(evaluables)

result = validator.expect_column_values_to_be_in_set(
    column="statut_rq005",
    value_set=["CONFORME"],
    mostly=0.98,
    result_format="COMPLETE",
    meta={"rule_id": RULE_ID}
)

total = len(df)
testees = len(evaluables)
echecs = int((evaluables["statut_rq005"] == "ECHEC").sum())
reussites = testees - echecs
taux = 100 * reussites / testees if testees else 0

print(f"Règle : {RULE_ID}")
print(f"Lot : {BATCH_ID}")
print(f"Clients totaux : {total}")
print(f"Lignes testées : {testees}")
print(f"Lignes en échec : {echecs}")
print(f"Taux de réussite : {taux:.2f}%")
print("Seuil requis : 98.00%")
print(f"Expectation réussie : {result['success']}")
print("Sévérité : AVERTISSEMENT")

print("\nRépartition des statuts :")
print(df["statut_rq005"].value_counts().to_string())

print(
    "\nStatut de la règle :",
    "GO" if result["success"] and testees > 0 else "NO-GO"
)
