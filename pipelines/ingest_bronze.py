
# -*- coding: utf-8 -*-
"""
TD AssurConnect - Groupe 04
US-02 : Ingestion des donnees SOURCES vers BRONZE

Objectifs :
- Copier les 7 tables CRM et CIF vers BRONZE
- Conserver les valeurs sources sans nettoyage
- Ajouter les 4 metadonnees d'ingestion
- Calculer une empreinte SHA-256 sur chaque ligne
- Eviter les doublons lors de la relance du meme lot
- Utiliser une transaction independante par table
"""

import hashlib
import json
from datetime import date, datetime

from sqlalchemy import create_engine, inspect, text


# ============================================================
# 1. CONFIGURATION
# ============================================================

import os

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
# 2. CONVERSION DES VALEURS
# ============================================================

def convertir(valeur):
    """
    Convertit une valeur source en texte pour BRONZE.

    NULL reste NULL.
    Les dates sont converties au format ISO.
    Les chaines vides et les espaces sont conserves.
    """

    if valeur is None:
        return None

    if isinstance(valeur, (date, datetime)):
        return valeur.isoformat()

    return str(valeur)


# ============================================================
# 3. CALCUL DE L'EMPREINTE DE LIGNE
# ============================================================

def calculer_hash(ligne, colonnes):
    """
    Calcule une empreinte SHA-256 tronquee a 16 caracteres.

    Les colonnes sont prises dans un ordre fixe.
    La representation JSON conserve la distinction
    entre NULL, chaine vide et espaces.
    """

    valeurs = [
        convertir(ligne[colonne])
        for colonne in colonnes
    ]

    contenu = json.dumps(
        valeurs,
        ensure_ascii=False,
        separators=(",", ":")
    )

    empreinte = hashlib.sha256(
        contenu.encode("utf-8")
    ).hexdigest()[:16]

    return empreinte


# ============================================================
# 4. INGESTION D'UNE TABLE
# ============================================================

def ingerer_table(schema, table, table_bronze):
    """
    Charge une table source dans BRONZE.

    Une transaction est utilisee pour chaque table.
    En cas d'erreur, les insertions de cette table
    sont annulees.
    """

    print(f"\n--- {schema}.{table} -> bronze.{table_bronze} ---")

    with engine.begin() as conn:

        # Recuperer les colonnes de la table source
        colonnes = [
            colonne["name"]
            for colonne in inspect(conn).get_columns(
                table,
                schema=schema
            )
        ]

        noms_colonnes = ", ".join(
            f"`{colonne}`"
            for colonne in colonnes
        )

        # Compter les lignes sources
        nb_source = conn.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM `{schema}`.`{table}`"
            )
        ).scalar_one()

        # Verifier si le lot existe deja
        nb_bronze = conn.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM bronze.`{table_bronze}` "
                f"WHERE _batch_id = :batch"
            ),
            {"batch": BATCH_ID}
        ).scalar_one()

        if nb_bronze > 0:

            if nb_bronze != nb_source:
                raise RuntimeError(
                    f"Lot incomplet pour {table_bronze} : "
                    f"{nb_bronze}/{nb_source}"
                )

            print(
                f"Lot deja present : {nb_bronze} lignes. "
                "Aucune insertion."
            )

            return

        # Preparer les colonnes pour INSERT
        colonnes_insert = colonnes + [
            "_batch_id",
            "_source_system",
            "_row_hash"
        ]

        champs_sql = ", ".join(
            f"`{colonne}`"
            for colonne in colonnes_insert
        )

        parametres_sql = ", ".join(
            f":{colonne}"
            for colonne in colonnes_insert
        )

        requete_insert = text(
            f"INSERT INTO bronze.`{table_bronze}` "
            f"({champs_sql}) "
            f"VALUES ({parametres_sql})"
        )

        # Lire les donnees sources
        resultat = conn.execute(
            text(
                f"SELECT {noms_colonnes} "
                f"FROM `{schema}`.`{table}`"
            )
        ).mappings()

        total = 0

        # Inserer par groupes de 1000 lignes
        while True:

            lignes = resultat.fetchmany(1000)

            if not lignes:
                break

            donnees = []

            for ligne in lignes:

                ligne_bronze = {
                    colonne: convertir(ligne[colonne])
                    for colonne in colonnes
                }

                # Metadonnees BRONZE
                ligne_bronze["_batch_id"] = BATCH_ID

                ligne_bronze["_source_system"] = schema

                ligne_bronze["_row_hash"] = calculer_hash(
                    ligne,
                    colonnes
                )

                # _ingested_at est rempli automatiquement
                # par MariaDB avec CURRENT_TIMESTAMP

                donnees.append(ligne_bronze)

            conn.execute(
                requete_insert,
                donnees
            )

            total += len(donnees)

        resultat.close()

        # Verification du nombre de lignes inserees
        if total != nb_source:
            raise RuntimeError(
                f"Ecart de comptage pour {table_bronze} : "
                f"{total}/{nb_source}"
            )

        print(
            f"Ingestion reussie : "
            f"{total} lignes chargees."
        )


# ============================================================
# 5. EXECUTION PRINCIPALE
# ============================================================

def main():

    print("=" * 55)
    print("ASSURCONNECT - INGESTION BRONZE")
    print(f"Batch ID : {BATCH_ID}")
    print("=" * 55)

    for schema, table, table_bronze in TABLES:

        ingerer_table(
            schema,
            table,
            table_bronze
        )

    print("\n" + "=" * 55)
    print("INGESTION BRONZE TERMINEE")
    print("=" * 55)


if __name__ == "__main__":
    main()
