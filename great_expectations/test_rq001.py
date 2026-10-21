
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-001"
BATCH_ID = os.getenv("DQ_BATCH_ID", "S1_G04_001")
DB_URL = os.getenv(
    "DQ_DB_URL",
    "mysql+pymysql://root:root@mariadb:3306"
)

engine = create_engine(DB_URL)

# Charger les dates du lot Bronze.
# La comparaison utilise des dates SQL, pas des chaînes de caractères.
query = text("""
    SELECT
        contrat_id,
        date_debut,
        date_fin,
        CASE
            WHEN date_debut IS NOT NULL
             AND date_fin IS NOT NULL
             AND STR_TO_DATE(date_fin, '%Y-%m-%d')
                 > STR_TO_DATE(date_debut, '%Y-%m-%d')
            THEN 1
            ELSE 0
        END AS rq001_valide
    FROM bronze.crm_contrat
    WHERE _batch_id = :batch_id
""")

with engine.connect() as connection:
    df = pd.read_sql(
        query,
        connection,
        params={"batch_id": BATCH_ID}
    )

# Great Expectations 0.18.19
validator = gx.from_pandas(df)

result = validator.expect_column_values_to_be_in_set(
    column="rq001_valide",
    value_set=[1],
    result_format="COMPLETE",
    meta={"rule_id": RULE_ID}
)

total = len(df)
echecs = int((df["rq001_valide"] != 1).sum())
reussites = total - echecs
taux = 100 * reussites / total if total else 0

print(f"Règle : {RULE_ID}")
print(f"Lot : {BATCH_ID}")
print(f"Lignes testées : {total}")
print(f"Lignes en échec : {echecs}")
print(f"Taux de réussite : {taux:.2f}%")
print(f"Expectation réussie : {result['success']}")
print(f"Sévérité : BLOQUANTE")

if echecs:
    print("Statut de la règle : NO-GO")
else:
    print("Statut de la règle : GO")
