
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-002"
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
    t.date_debut,
    c.date_naissance,
    CASE
        WHEN c.client_id IS NULL THEN 'REFERENCE_ABSENTE'
        WHEN c.raison_sociale IS NOT NULL
             AND TRIM(c.raison_sociale) <> ''
            THEN 'NON_APPLICABLE'
        WHEN c.date_naissance IS NULL
            THEN 'NON_EVALUABLE'
        WHEN STR_TO_DATE(t.date_debut, '%Y-%m-%d') IS NULL
            THEN 'NON_EVALUABLE'
        WHEN DATE_ADD(
            c.date_naissance, INTERVAL 18 YEAR
        ) <= STR_TO_DATE(t.date_debut, '%Y-%m-%d')
            THEN 'CONFORME'
        ELSE 'ECHEC'
    END AS statut_rq002
FROM bronze.crm_contrat t
LEFT JOIN crm.client c
    ON t.souscripteur_id = c.client_id
WHERE t._batch_id = :batch_id
""")

with engine.connect() as connection:
    df = pd.read_sql(
        query,
        connection,
        params={"batch_id": BATCH_ID}
    )

# Conserver uniquement les contrats évaluables
evaluables = df[
    df["statut_rq002"].isin(["CONFORME", "ECHEC"])
].copy()

# Great Expectations 0.18.19
validator = gx.from_pandas(evaluables)

result = validator.expect_column_values_to_be_in_set(
    column="statut_rq002",
    value_set=["CONFORME"],
    result_format="COMPLETE",
    meta={"rule_id": RULE_ID}
)

total = len(df)
testees = len(evaluables)
echecs = int((evaluables["statut_rq002"] == "ECHEC").sum())
reussites = testees - echecs
taux = 100 * reussites / testees if testees else 0

print(f"Règle : {RULE_ID}")
print(f"Lot : {BATCH_ID}")
print(f"Contrats totaux : {total}")
print(f"Lignes testées : {testees}")
print(f"Lignes en échec : {echecs}")
print(f"Taux de réussite : {taux:.2f}%")
print(f"Expectation réussie : {result['success']}")
print("Sévérité : BLOQUANTE")

print("\nRépartition des statuts :")
print(df["statut_rq002"].value_counts().to_string())

print("\nStatut de la règle :",
      "GO" if result["success"] and testees > 0 else "NO-GO")
