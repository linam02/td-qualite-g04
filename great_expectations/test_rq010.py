
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-010"
BATCH_ID = os.getenv("DQ_BATCH_ID", "S1_G04_001")
DB_URL = os.getenv(
    "DQ_DB_URL",
    "mysql+pymysql://root:root@mariadb:3306"
)

engine = create_engine(DB_URL)

query = text("""
SELECT
    contrat_id,
    duree_garantie_mois
FROM bronze.crm_contrat
WHERE _batch_id = :batch_id
""")

with engine.connect() as connection:
    df = pd.read_sql(
        query,
        connection,
        params={"batch_id": BATCH_ID}
    )

# Bronze contient des VARCHAR : comparaison exacte
# sans conversion numérique automatique.
valeurs_autorisees = ["12", "24", "36", "60"]

# NULL, vide et valeurs inconnues sont non conformes.
df["rq010_valide"] = (
    df["duree_garantie_mois"]
    .isin(valeurs_autorisees)
    .astype(int)
)

validator = gx.from_pandas(df)

result = validator.expect_column_values_to_be_in_set(
    column="rq010_valide",
    value_set=[1],
    mostly=1.0,
    result_format="COMPLETE",
    meta={"rule_id": RULE_ID}
)

total = len(df)
echecs = int((df["rq010_valide"] == 0).sum())
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
    df.loc[
        df["rq010_valide"] == 0,
        "duree_garantie_mois"
    ]
    .fillna("<NULL>")
    .value_counts()
    .to_string()
)

print(
    "\nStatut de la règle :",
    "GO" if result["success"] and total > 0 else "NO-GO"
)
