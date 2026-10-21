
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-009"
BATCH_ID = os.getenv("DQ_BATCH_ID", "S1_G04_001")
DB_URL = os.getenv(
    "DQ_DB_URL",
    "mysql+pymysql://root:root@mariadb:3306"
)

engine = create_engine(DB_URL)

query = text("""
SELECT
    client_id,
    type_personne
FROM bronze.crm_client
WHERE _batch_id = :batch_id
""")

with engine.connect() as connection:
    df = pd.read_sql(
        query,
        connection,
        params={"batch_id": BATCH_ID}
    )

# Comparaison stricte en Python :
# les majuscules et les accents sont significatifs.
valeurs_autorisees = [
    "prospect",
    "souscripteur",
    "assure"
]

validator = gx.from_pandas(df)

result = validator.expect_column_values_to_be_in_set(
    column="type_personne",
    value_set=valeurs_autorisees,
    mostly=1.0,
    result_format="COMPLETE",
    meta={"rule_id": RULE_ID}
)

# Compter les valeurs NULL comme des echecs.
valides = df["type_personne"].isin(valeurs_autorisees)

total = len(df)
echecs = int((~valides).sum())
reussites = total - echecs
taux = 100 * reussites / total if total else 0

print(f"Règle : {RULE_ID}")
print(f"Lot : {BATCH_ID}")
print(f"Lignes testées : {total}")
print(f"Lignes en échec : {echecs}")
print(f"Taux de réussite : {taux:.2f}%")
print("Seuil requis : 100.00%")
print(f"Expectation réussie : {result['success']}")
print("Sévérité : BLOQUANTE")

print("\nValeurs non conformes :")
print(
    df.loc[~valides, "type_personne"]
    .fillna("<NULL>")
    .value_counts()
    .to_string()
)

print(
    "\nStatut de la règle :",
    "GO" if echecs == 0 and total > 0 else "NO-GO"
)
