
# -*- coding: utf-8 -*-
"""
TD AssurConnect - Groupe 04
US-03 : Controle de qualite Gate B
RQ-021 : Reconciliation SOURCES / BRONZE

Controles :
1. Comptage des lignes Sources / Bronze
2. Hash calcule depuis Sources
3. Hash recalcule depuis les donnees Bronze
4. Comparaison avec _row_hash stocke
5. Detection des cles absentes ou supplementaires
6. Detection des doublons de cles dans Bronze

Ce script ne modifie aucune donnee.
"""

import os
import hashlib
import json
from datetime import date, datetime

from sqlalchemy import create_engine, inspect, text


# ============================================================
# 1. CONFIGURATION
# ============================================================

DB_URL = os.environ.get("DQ_DB_URL")

if not DB_URL:
    raise RuntimeError("Variable DQ_DB_URL manquante")

BATCH_ID = "S1_G04_001"

TABLES = [
    ("crm", "type_contrat", "crm_type_contrat"),
    ("crm", "client", "crm_client"),
    ("crm", "contrat", "crm_contrat"),
    ("crm", "sinistre", "crm_sinistre"),
    ("cif", "clients", "cif_clients"),
    ("cif", "compte", "cif_compte"),
    ("cif", "pays", "cif_pays"),
]

engine = create_engine(DB_URL)


# ============================================================
# 2. FONCTIONS DE CALCUL DU HASH
# ============================================================

def convertir(valeur):
    """Normaliser une valeur avant le calcul du hash."""

    if valeur is None:
        return None

    if isinstance(valeur, (date, datetime)):
        return valeur.isoformat()

    return str(valeur)


def calculer_hash(ligne, colonnes):
    """
    Reproduire l'algorithme de hash de ingest_bronze.py.
    L'ordre des colonnes doit etre identique.
    """

    valeurs = [
        convertir(ligne[c])
        for c in colonnes
    ]

    contenu = json.dumps(
        valeurs,
        ensure_ascii=False,
        separators=(",", ":")
    )

    return hashlib.sha256(
        contenu.encode("utf-8")
    ).hexdigest()[:16]


# ============================================================
# 3. CONTROLE D'UNE TABLE
# ============================================================

def verifier_table(schema, table, table_bronze):

    print(
        f"\nVerification : {schema}.{table} "
        f"-> bronze.{table_bronze}",
        flush=True
    )

    with engine.connect() as conn:

        inspector = inspect(conn)

        colonnes = [
            c["name"]
            for c in inspector.get_columns(
                table,
                schema=schema
            )
        ]

        pk = inspector.get_pk_constraint(
            table,
            schema=schema
        )["constrained_columns"]

        if not pk:
            raise RuntimeError(
                f"Cle primaire introuvable : {schema}.{table}"
            )

        # ----------------------------------------------------
        # 3.1 Comptages
        # ----------------------------------------------------

        nb_source = conn.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM `{schema}`.`{table}`"
            )
        ).scalar_one()

        nb_bronze = conn.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM bronze.`{table_bronze}` "
                f"WHERE _batch_id = :batch"
            ),
            {"batch": BATCH_ID}
        ).scalar_one()

        ecart_comptage = nb_bronze - nb_source

        # ----------------------------------------------------
        # 3.2 Construire la jointure Sources / Bronze
        # ----------------------------------------------------

        conditions = " AND ".join(
            f"s.`{c}` <=> b.`{c}`"
            for c in pk
        )

        colonnes_source = ", ".join(
            f"s.`{c}` AS `source_{c}`"
            for c in colonnes
        )

        colonnes_bronze = ", ".join(
            f"b.`{c}` AS `bronze_{c}`"
            for c in colonnes
        )

        sql = text(f"""
            SELECT
                {colonnes_source},
                {colonnes_bronze},
                b._row_hash AS hash_bronze_stocke,
                b.bronze_row_id AS id_bronze
            FROM `{schema}`.`{table}` s
            LEFT JOIN bronze.`{table_bronze}` b
              ON {conditions}
             AND b._batch_id = :batch
        """)

        # ----------------------------------------------------
        # 3.3 Comparaison des trois hash
        # ----------------------------------------------------

        nb_jointures = 0
        nb_absents = 0
        nb_hash_differents = 0

        resultat = conn.execution_options(
            stream_results=True
        ).execute(
            sql,
            {"batch": BATCH_ID}
        ).mappings()

        try:
            for ligne in resultat:

                nb_jointures += 1

                if ligne["id_bronze"] is None:
                    nb_absents += 1
                    continue

                donnees_source = {
                    c: ligne[f"source_{c}"]
                    for c in colonnes
                }

                donnees_bronze = {
                    c: ligne[f"bronze_{c}"]
                    for c in colonnes
                }

                hash_source = calculer_hash(
                    donnees_source,
                    colonnes
                )

                hash_bronze_recalcule = calculer_hash(
                    donnees_bronze,
                    colonnes
                )

                hash_bronze_stocke = ligne[
                    "hash_bronze_stocke"
                ]

                if not (
                    hash_source
                    == hash_bronze_recalcule
                    == hash_bronze_stocke
                ):
                    nb_hash_differents += 1

        finally:
            resultat.close()

        # ----------------------------------------------------
        # 3.4 Detecter les doublons Bronze
        # ----------------------------------------------------

        colonnes_pk = ", ".join(
            f"`{c}`"
            for c in pk
        )

        sql_doublons = text(f"""
            SELECT COALESCE(
                SUM(nb - 1),
                0
            )
            FROM (
                SELECT
                    COUNT(*) AS nb
                FROM bronze.`{table_bronze}`
                WHERE _batch_id = :batch
                GROUP BY {colonnes_pk}
                HAVING COUNT(*) > 1
            ) AS doublons
        """)

        nb_doublons = conn.execute(
            sql_doublons,
            {"batch": BATCH_ID}
        ).scalar_one()

        nb_doublons = int(nb_doublons or 0)

        # ----------------------------------------------------
        # 3.5 Detecter les lignes Bronze sans source
        # ----------------------------------------------------

        conditions_inverse = " AND ".join(
            f"b.`{c}` <=> s.`{c}`"
            for c in pk
        )

        # Une colonne de PK source est toujours non NULL.
        pk_source = pk[0]

        sql_supplementaires = text(f"""
            SELECT COUNT(*)
            FROM bronze.`{table_bronze}` b
            LEFT JOIN `{schema}`.`{table}` s
              ON {conditions_inverse}
            WHERE b._batch_id = :batch
              AND s.`{pk_source}` IS NULL
        """)

        nb_supplementaires = conn.execute(
            sql_supplementaires,
            {"batch": BATCH_ID}
        ).scalar_one()

        # ----------------------------------------------------
        # 3.6 Resultat
        # ----------------------------------------------------

        conforme = (
            ecart_comptage == 0
            and nb_absents == 0
            and nb_supplementaires == 0
            and nb_doublons == 0
            and nb_hash_differents == 0
            and nb_jointures == nb_source
        )

        print(
            f"  Source               : {nb_source}",
            flush=True
        )
        print(
            f"  Bronze               : {nb_bronze}",
            flush=True
        )
        print(
            f"  Ecart comptage       : {ecart_comptage}",
            flush=True
        )
        print(
            f"  Lignes absentes      : {nb_absents}",
            flush=True
        )
        print(
            f"  Lignes supplementaires: {nb_supplementaires}",
            flush=True
        )
        print(
            f"  Doublons Bronze      : {nb_doublons}",
            flush=True
        )
        print(
            f"  Echecs hash          : {nb_hash_differents}",
            flush=True
        )
        print(
            f"  Statut               : "
            f"{'CONFORME' if conforme else 'NON CONFORME'}",
            flush=True
        )

        return conforme


# ============================================================
# 4. EXECUTION GENERALE
# ============================================================

def main():

    print("=" * 65)
    print("ASSURCONNECT - GROUPE 04")
    print("US-03 : CONTROLE RQ-021")
    print(f"Batch : {BATCH_ID}")
    print("=" * 65)

    resultats = []

    for schema, table, table_bronze in TABLES:

        conforme = verifier_table(
            schema,
            table,
            table_bronze
        )

        resultats.append(conforme)

    print("\n" + "=" * 65)

    if all(resultats):
        print("RQ-021 : CONFORME")
    else:
        print("RQ-021 : NON CONFORME")

    print("=" * 65)

    print(
        "RQ-022 : verification des metadonnees "
        "a effectuer separement."
    )


if __name__ == "__main__":
    main()
