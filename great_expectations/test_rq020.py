
import os
import pandas as pd
import great_expectations as gx
from sqlalchemy import create_engine, text

RULE_ID = "RQ-020"
BATCH_ID = os.getenv("DQ_BATCH_ID", "S1_G04_001")
DB_URL = os.getenv(
    "DQ_DB_URL",
    "mysql+pymysql://root:root@mariadb:3306"
)

TABLES = {
    "crm_client": "client_id",
    "crm_contrat": "contrat_id",
    "crm_sinistre": "sinistre_id",
    "crm_type_contrat": "code_type",
    "cif_clients": "column0",
    "cif_compte": "column0",
    "cif_pays": "code_pays",
}

engine = create_engine(DB_URL)

print(f"Règle : {RULE_ID}")
print(f"Lot : {BATCH_ID}")
print("Sévérité : BLOQUANTE")
print("Seuil requis : 100.00%")

total_global = 0
echecs_global = 0

for table_name, pk_column in TABLES.items():

    # Les noms de tables et colonnes proviennent
    # exclusivement de la liste autorisée TABLES.
    query = text(f"""
        SELECT `{pk_column}` AS cle_primaire
        FROM bronze.`{table_name}`
        WHERE _batch_id = :batch_id
    """)

    with engine.connect() as connection:
        df = pd.read_sql(
            query,
            connection,
            params={"batch_id": BATCH_ID}
        )

    # Une clé est invalide si elle est NULL,
    # vide ou composée uniquement d'espaces.
    cles_manquantes = (
        df["cle_primaire"].isna()
        | df["cle_primaire"].astype("string").str.strip().eq("")
    ).fillna(True)

    # Chaque occurrence d'une clé dupliquée est
    # considérée comme non conforme.
    cles_dupliquees = df["cle_primaire"].duplicated(
        keep=False
    )

    df["rq020_valide"] = (
        ~(cles_manquantes | cles_dupliquees)
    ).astype(int)

    validator = gx.from_pandas(df)

    result = validator.expect_column_values_to_be_in_set(
        column="rq020_valide",
        value_set=[1],
        mostly=1.0,
        result_format="COMPLETE",
        meta={
            "rule_id": RULE_ID,
            "table": f"bronze.{table_name}",
            "primary_key": pk_column
        }
    )

    total = len(df)
    echecs = int((df["rq020_valide"] == 0).sum())
    reussites = total - echecs
    taux = 100 * reussites / total if total else 0

    total_global += total
    echecs_global += echecs

    statut = (
        "GO"
        if result["success"] and total > 0
        else "NO-GO"
    )

    print(f"\nTable : bronze.{table_name}")
    print(f"Clé primaire : {pk_column}")
    print(f"Lignes testées : {total}")
    print(f"Lignes en échec : {echecs}")
    print(f"Taux de réussite : {taux:.2f}%")
    print(f"Expectation réussie : {result['success']}")
    print(f"Statut : {statut}")

taux_global = (
    100 * (total_global - echecs_global) / total_global
    if total_global else 0
)

print("\n===== BILAN RQ-020 =====")
print(f"Lignes testées : {total_global}")
print(f"Lignes en échec : {echecs_global}")
print(f"Taux de réussite : {taux_global:.2f}%")
print(
    "Statut global :",
    "GO" if echecs_global == 0 and total_global > 0
    else "NO-GO"
)

