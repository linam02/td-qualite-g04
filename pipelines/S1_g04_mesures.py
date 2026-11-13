# -*- coding: utf-8 -*-
# %% [markdown]
# # S1 · Inventaire, bronze, porte B, profilage, dictionnaire du CIF, client actif
#
# Stories : US-01, 02, 03, 04, 06, 07, 09. Livrable : `livrables/S1_bronze_profilage.md`.
#
# Lancement de bout en bout (depuis la racine du dépôt) :
#
#     docker exec -it dq_jupyter python pipelines/S1_g04_mesures.py
#     docker exec -it dq_jupyter python pipelines/S1_g04_mesures.py --ydata   # + rapport YData-Profiling
#
# Ou cellule par cellule dans VS Code (cellules `# %%`, noyau Jupyter du conteneur).
# Toutes les sorties chiffrées sont écrites dans `reports/s1/` (S1_resultats.md et s1_resultats.json) :
# ce sont les preuves citées dans le livrable. Aucune donnée source n'est modifiée ; bronze n'est écrit
# que pour le lot BATCH_ID (relance idempotente : le lot est remplacé, jamais dupliqué).

# %% Paramètres et connexion
import os, sys, json, re, hashlib, datetime as dt
from collections import Counter
import pandas as pd
from sqlalchemy import create_engine, text

URL = os.environ.get("DQ_DB_URL", "mysql+pymysql://root:root@mariadb:3306")   # host = mariadb, jamais localhost
BATCH_ID = os.environ.get("BATCH_ID", "L-2026-10-01")                          # lot de référence du TD (même valeur que pipelines/aq.py)
DATE_REF = "2026-10-01"                                                        # date de référence du lot (fiche CD-001, pipelines/aq.py)
COTISATION_MIN = "2026-07-01"                                                  # date de référence moins trois mois (fiche CD-001)
try:
    BASE = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
except NameError:                                                              # exécution cellule par cellule
    BASE = os.path.abspath(os.getcwd() if os.path.isdir(os.path.join(os.getcwd(), "pipelines")) else os.path.join(os.getcwd(), ".."))
REPORTS = os.path.join(BASE, "reports", "s1")
os.makedirs(REPORTS, exist_ok=True)

eng = create_engine(URL + "?charset=utf8mb4" if "?" not in URL else URL)
NUL = "\\N"          # marqueur de NULL dans l'empreinte (même convention que les CSV du TD)
SEP = "|"

def q(sql, **p):
    with eng.connect() as cx:
        return pd.read_sql(text(sql), cx, params=p)

def scal(sql, **p):
    with eng.connect() as cx:
        return cx.execute(text(sql), p).scalar()

RESULTATS = {"batch_id": BATCH_ID, "date_ref": DATE_REF, "cotisation_min": COTISATION_MIN, "execute_le": dt.datetime.now().isoformat(timespec="seconds")}
MD = [f"# Résultats S1 (générés par pipelines/S1_g04_mesures.py)\n",
      f"Lot `{BATCH_ID}` · date de référence `{DATE_REF}` · exécuté le {RESULTATS['execute_le']}\n"]

def md_table(df, titre):
    MD.append(f"\n## {titre}\n")
    MD.append(df.to_markdown(index=False) if hasattr(df, "to_markdown") and _has_tabulate() else _md(df))
    MD.append("")

def _has_tabulate():
    try:
        import tabulate  # noqa
        return True
    except ImportError:
        return False

def _md(df):
    cols = [str(c) for c in df.columns]
    lignes = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        lignes.append("| " + " | ".join("" if v is None else str(v).replace("|", "\\|") for v in r) + " |")
    return "\n".join(lignes)

def montrer(df, titre):
    print(f"\n=== {titre} ===")
    with pd.option_context("display.max_columns", 50, "display.width", 200, "display.max_colwidth", 60):
        print(df.to_string(index=False))
    md_table(df, titre)

# Les sept tables : (source, table source, table bronze)
TABLES = [("crm", "client", "crm_client"), ("crm", "contrat", "crm_contrat"), ("crm", "sinistre", "crm_sinistre"),
          ("crm", "type_contrat", "crm_type_contrat"), ("cif", "clients", "cif_clients"), ("cif", "compte", "cif_compte"),
          ("cif", "pays", "cif_pays")]

def colonnes(schema, table):
    return q("SELECT COLUMN_NAME c FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=:s AND TABLE_NAME=:t ORDER BY ORDINAL_POSITION",
             s=schema, t=table)["c"].tolist()

def cle_primaire(schema, table):
    return q("SELECT COLUMN_NAME c FROM information_schema.STATISTICS WHERE TABLE_SCHEMA=:s AND TABLE_NAME=:t AND INDEX_NAME='PRIMARY' ORDER BY SEQ_IN_INDEX",
             s=schema, t=table)["c"].tolist()

print("Connexion :", scal("SELECT VERSION()"), "· lot", BATCH_ID, "· date de référence", DATE_REF)

# %% [markdown]
# ## US-01 · Inventaire des sources (comptages par requête, clé primaire, observation chiffrée)

# %% US-01
inv = []
for src, t, _ in TABLES:
    cols = colonnes(src, t)
    pk = cle_primaire(src, t)
    n = scal(f"SELECT COUNT(*) FROM {src}.`{t}`")
    pkc = ", ".join(f"`{c}`" for c in pk)
    doublons_pk = n - scal(f"SELECT COUNT(DISTINCT {pkc}) FROM {src}.`{t}`") if pk else None
    nuls = q("SELECT " + ", ".join(f"SUM(`{c}` IS NULL) AS `{c}`" for c in cols) + f" FROM {src}.`{t}`").iloc[0].fillna(0).astype(int)
    cols_nulles = {c: int(v) for c, v in nuls.items() if v > 0}
    if cols_nulles:
        top = sorted(cols_nulles.items(), key=lambda kv: -kv[1])[:3]
        obs = "NULL : " + ", ".join(f"{c} {v} ({100*v/n:.1f} %)" for c, v in top)
    else:
        obs = "aucun NULL"
    obs += f" ; doublons de clé : {doublons_pk}"
    inv.append({"Source": src, "Table": t, "Lignes": n, "Colonnes": len(cols), "Clé primaire": ", ".join(pk) or "aucune",
                "Doublons de clé": doublons_pk, "Observation chiffrée": obs})
inv = pd.DataFrame(inv)
montrer(inv, "US-01 · Inventaire des sources")
RESULTATS["us01_inventaire"] = inv.to_dict(orient="records")

# Observations complémentaires utiles au livrable
obs_sup = pd.DataFrame([
    {"Observation": "contrat.assure_id = '0' (valeur sentinelle)", "Valeur": scal("SELECT COUNT(*) FROM crm.contrat WHERE assure_id = '0'")},
    {"Observation": "contrat.souscripteur_id absent de crm.client",
     "Valeur": scal("SELECT COUNT(*) FROM crm.contrat c LEFT JOIN crm.client k ON k.client_id = c.souscripteur_id WHERE c.souscripteur_id IS NOT NULL AND k.client_id IS NULL")},
    {"Observation": "contrat.code_type absent de type_contrat",
     "Valeur": scal("SELECT COUNT(*) FROM crm.contrat c LEFT JOIN crm.type_contrat t ON t.code_type = c.code_type WHERE c.code_type IS NOT NULL AND t.code_type IS NULL")},
    {"Observation": "sinistre.contrat_id absent de contrat",
     "Valeur": scal("SELECT COUNT(*) FROM crm.sinistre s LEFT JOIN crm.contrat c ON c.contrat_id = s.contrat_id WHERE s.contrat_id IS NOT NULL AND c.contrat_id IS NULL")},
    {"Observation": "cif.compte.column1 absent de cif.clients.column0",
     "Valeur": scal("SELECT COUNT(*) FROM cif.compte k LEFT JOIN cif.clients c ON c.column0 = k.column1 WHERE k.column1 IS NOT NULL AND c.column0 IS NULL")},
    {"Observation": "crm.client : personnes morales (raison_sociale renseignée, nom NULL)",
     "Valeur": scal("SELECT COUNT(*) FROM crm.client WHERE raison_sociale IS NOT NULL AND nom IS NULL")},
])
montrer(obs_sup, "US-01 · Observations complémentaires (sources)")
RESULTATS["us01_observations"] = obs_sup.to_dict(orient="records")

# %% [markdown]
# ## US-02 · Ingestion en bronze
#
# Méthode : (1) lecture de la source avec chaque colonne convertie en texte par MariaDB (`CAST(... AS CHAR)`),
# pour que dates, décimales et NULL gardent exactement leur représentation source ; (2) aucune autre conversion :
# NULL reste NULL, '' reste '', '   ' reste '   ' ; (3) quatre métadonnées par ligne : `_batch_id`, `_source_system`,
# `_ingested_at`, `_row_hash` (16 premiers caractères hexadécimaux du SHA-256 des valeurs jointes par « | », NULL écrit `\N`) ;
# (4) relance du même lot : les lignes du lot sont supprimées puis réécrites dans la même transaction, donc aucun doublon.

# %% US-02 : fonctions d'ingestion
def row_hash(valeurs):
    s = SEP.join(NUL if v is None else str(v) for v in valeurs)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]

def expr_concat(cols, cast):
    morceaux = [f"COALESCE(CAST(`{c}` AS CHAR), '\\\\N')" if cast else f"COALESCE(`{c}`, '\\\\N')" for c in cols]
    return f"CONCAT_WS('{SEP}', {', '.join(morceaux)})"

def ingerer(src, t, bronze, batch=BATCH_ID):
    cols = colonnes(src, t)
    sel = ", ".join(f"CAST(`{c}` AS CHAR) AS `{c}`" for c in cols)
    with eng.begin() as cx:
        df = pd.read_sql(text(f"SELECT {sel} FROM {src}.`{t}`"), cx, dtype=object)
        df = df.astype(object).where(df.notna(), None)
        df["_row_hash"] = [row_hash(r) for r in df[cols].itertuples(index=False, name=None)]
        df["_batch_id"] = batch
        df["_source_system"] = src
        df["_ingested_at"] = dt.datetime.now().replace(microsecond=0)
        supprimees = cx.execute(text(f"DELETE FROM bronze.`{bronze}` WHERE _batch_id = :b"), {"b": batch}).rowcount
        df.to_sql(bronze, cx, schema="bronze", if_exists="append", index=False, method="multi", chunksize=2000)
    return len(df), supprimees

def ingerer_tout(batch=BATCH_ID):
    with eng.begin() as cx:
        cx.execute(text("INSERT INTO dq.lot_ingestion (batch_id, statut) VALUES (:b, 'EN_COURS') "
                        "ON DUPLICATE KEY UPDATE started_at = NOW(), finished_at = NULL, statut = 'EN_COURS'"), {"b": batch})
    lignes = []
    try:
        for src, t, b in TABLES:
            n, sup = ingerer(src, t, b, batch)
            lignes.append({"Table bronze": b, "Lignes écrites": n, "Lignes du lot remplacées": sup})
            print(f"  bronze.{b:<17} {n:>7} lignes (lot remplacé : {sup})")
        statut = "TERMINE"
    except Exception:
        statut = "ECHEC"
        raise
    finally:
        with eng.begin() as cx:
            cx.execute(text("UPDATE dq.lot_ingestion SET finished_at = NOW(), statut = :s WHERE batch_id = :b"), {"s": statut, "b": batch})
    return pd.DataFrame(lignes)

# %% US-02 : ingestion du lot
print("Ingestion du lot", BATCH_ID)
ing = ingerer_tout()
montrer(ing, "US-02 · Ingestion bronze")
RESULTATS["us02_ingestion"] = ing.to_dict(orient="records")

# %% [markdown]
# ## US-03 · Porte B : la copie bronze est-elle fidèle ?
#
# - **RQ-021** (réconciliation) : comptage source = comptage bronze du lot, ET somme de contrôle identique
#   (SUM(CRC32) de la ligne en texte, calculée par MariaDB des deux côtés), ET comparaison ligne à ligne des empreintes
#   recalculées des deux côtés. `nb_echecs` = lignes source sans jumelle en bronze + lignes bronze sans jumelle en source.
# - **RQ-022** (traçabilité) : chaque ligne bronze du lot porte ses quatre métadonnées, et l'empreinte stockée
#   correspond au contenu (recalcul SQL).

# %% US-03 : fonctions de la porte
def porte_b(src, t, bronze, batch=BATCH_ID, ecrire=True, couche="BRONZE"):
    cols = colonnes(src, t)
    e_src, e_br = expr_concat(cols, True), expr_concat(cols, False)
    n_src = scal(f"SELECT COUNT(*) FROM {src}.`{t}`")
    n_br = scal(f"SELECT COUNT(*) FROM bronze.`{bronze}` WHERE _batch_id = :b", b=batch)
    ck_src = scal(f"SELECT COALESCE(SUM(CRC32({e_src})), 0) FROM {src}.`{t}`")
    ck_br = scal(f"SELECT COALESCE(SUM(CRC32({e_br})), 0) FROM bronze.`{bronze}` WHERE _batch_id = :b", b=batch)
    h_src = Counter(q(f"SELECT LEFT(SHA2({e_src}, 256), 16) h FROM {src}.`{t}`")["h"])
    h_br = Counter(q(f"SELECT LEFT(SHA2({e_br}, 256), 16) h FROM bronze.`{bronze}` WHERE _batch_id = :b", b=batch)["h"])
    manquantes, en_trop = sum((h_src - h_br).values()), sum((h_br - h_src).values())
    meta_ko = scal(f"""SELECT COUNT(*) FROM bronze.`{bronze}` WHERE _batch_id = :b AND (
                          _source_system IS NULL OR TRIM(_source_system) = '' OR _ingested_at IS NULL
                          OR _row_hash IS NULL OR CHAR_LENGTH(_row_hash) <> 16 OR _row_hash <> LEFT(SHA2({e_br}, 256), 16))""", b=batch)
    res = {"Table bronze": bronze, "Lignes source": n_src, "Lignes bronze": n_br, "Écart de comptage": n_br - n_src,
           "Somme de contrôle source": int(ck_src), "Somme de contrôle bronze": int(ck_br), "Écart de somme de contrôle": int(ck_br) - int(ck_src),
           "Lignes sans jumelle": manquantes + en_trop, "RQ-022 lignes sans métadonnées valides": meta_ko,
           "Porte B": "OK" if (n_br == n_src and ck_br == ck_src and manquantes + en_trop == 0 and meta_ko == 0) else "ÉCHEC"}
    if ecrire:
        with eng.begin() as cx:
            for r in ("RQ-021", "RQ-022"):
                cx.execute(text("DELETE FROM dq.dq_history WHERE batch_id=:b AND couche=:c AND rule_id=:r AND table_cible=:t"),
                           {"b": batch, "c": couche, "r": r, "t": f"bronze.{bronze}"})
            ins = text("INSERT INTO dq.dq_history (batch_id, couche, rule_id, table_cible, nb_testees, nb_echecs) VALUES (:b, :c, :r, :t, :n, :e)")
            cx.execute(ins, {"b": batch, "c": couche, "r": "RQ-021", "t": f"bronze.{bronze}", "n": n_src, "e": manquantes + en_trop})
            cx.execute(ins, {"b": batch, "c": couche, "r": "RQ-022", "t": f"bronze.{bronze}", "n": n_br, "e": meta_ko})
    return res

# %% US-03 : porte B sur les sept tables, mesures écrites dans dq.dq_history
porte = pd.DataFrame([porte_b(src, t, b) for src, t, b in TABLES])
montrer(porte, "US-03 · Porte B (RQ-021 comptage + somme de contrôle + lignes, RQ-022 métadonnées)")
RESULTATS["us03_porte_b"] = porte.to_dict(orient="records")
print("PORTE B :", "FRANCHIE" if (porte["Porte B"] == "OK").all() else "FERMÉE")

hist = q("SELECT id, batch_id, couche, rule_id, table_cible, nb_testees, nb_echecs, taux_conformite, mesure_le "
         "FROM dq.v_derniere_mesure WHERE batch_id = :b AND rule_id IN ('RQ-021','RQ-022') ORDER BY rule_id, table_cible", b=BATCH_ID)
hist["mesure_le"] = hist["mesure_le"].astype(str)
montrer(hist, "US-03 · Dernières mesures dans dq.dq_history (couche BRONZE)")

# %% [markdown]
# ### Épreuve 1 : relancer le même lot ne crée aucun doublon

# %% Épreuve 1
avant = {b: scal(f"SELECT COUNT(*) FROM bronze.`{b}` WHERE _batch_id = :x", x=BATCH_ID) for _, _, b in TABLES}
total_avant = {b: scal(f"SELECT COUNT(*) FROM bronze.`{b}`") for _, _, b in TABLES}
for src, t, b in TABLES:
    ingerer(src, t, b, BATCH_ID)          # relance du MÊME lot
apres = {b: scal(f"SELECT COUNT(*) FROM bronze.`{b}` WHERE _batch_id = :x", x=BATCH_ID) for _, _, b in TABLES}
doublons = {b: scal(f"SELECT COALESCE(SUM(n - 1), 0) FROM (SELECT COUNT(*) n FROM bronze.`{b}` WHERE _batch_id = :x GROUP BY bronze_row_id IS NOT NULL, _row_hash HAVING n > 1) d", x=BATCH_ID)
            for _, _, b in TABLES}
dup_src = {}
for src, t, b in TABLES:
    e = expr_concat(colonnes(src, t), True)
    dup_src[b] = scal(f"SELECT COALESCE(SUM(n - 1), 0) FROM (SELECT COUNT(*) n FROM {src}.`{t}` GROUP BY LEFT(SHA2({e}, 256), 16) HAVING n > 1) d")
ep1 = pd.DataFrame([{"Table bronze": b, "Lignes du lot avant relance": avant[b], "Après relance": apres[b],
                     "Lignes créées par la relance": apres[b] - avant[b],
                     "Empreintes en double dans le lot": doublons[b], "dont doublons déjà présents en source": dup_src[b]} for _, _, b in TABLES])
montrer(ep1, "Épreuve 1 · Relance du même lot")
RESULTATS["epreuve1_relance"] = ep1.to_dict(orient="records")

# %% [markdown]
# ### Épreuve 2 : un écart introduit volontairement, sur une COPIE, fait-il échouer la porte ?
# On copie le lot de bronze.crm_client dans une table d'épreuve, on modifie une valeur et on supprime une ligne,
# puis on rejoue la porte sur la copie (sans écrire dans dq.dq_history). Bronze n'est jamais modifié.

# %% Épreuve 2
COPIE = "epreuve_crm_client"
with eng.begin() as cx:
    cx.execute(text(f"DROP TABLE IF EXISTS bronze.{COPIE}"))
    cx.execute(text(f"CREATE TABLE bronze.{COPIE} LIKE bronze.crm_client"))
    cx.execute(text(f"INSERT INTO bronze.{COPIE} SELECT * FROM bronze.crm_client WHERE _batch_id = :b"), {"b": BATCH_ID})
    id_mod = cx.execute(text(f"SELECT MIN(bronze_row_id) FROM bronze.{COPIE}")).scalar()
    id_sup = cx.execute(text(f"SELECT MAX(bronze_row_id) FROM bronze.{COPIE}")).scalar()
    cx.execute(text(f"UPDATE bronze.{COPIE} SET ville = CONCAT(COALESCE(ville, ''), 'X') WHERE bronze_row_id = :i"), {"i": id_mod})
    cx.execute(text(f"DELETE FROM bronze.{COPIE} WHERE bronze_row_id = :i"), {"i": id_sup})
r2 = porte_b("crm", "client", COPIE, ecrire=False)
with eng.begin() as cx:
    cx.execute(text(f"DROP TABLE bronze.{COPIE}"))
ep2 = pd.DataFrame([r2])
montrer(ep2, "Épreuve 2 · Porte B sur une copie altérée (1 valeur modifiée, 1 ligne supprimée)")
RESULTATS["epreuve2_ecart_volontaire"] = r2

# %% [markdown]
# ### Épreuve 3 : un problème de conversion (lecture naïve en pandas)
# Lecture « naïve » : `pd.read_sql("SELECT * ...")` puis conversion en texte. On compare chaque cellule à la lecture
# retenue (`CAST AS CHAR` par MariaDB). Les écarts typiques : entier avec NULL devenu flottant (`12.0`), NULL devenu
# `None`/`nan`/`NaT`, dates devenues `2020-01-01 00:00:00`.

# %% Épreuve 3
ep3 = []
for src, t, _ in TABLES:
    cols = colonnes(src, t)
    sel = ", ".join(f"CAST(`{c}` AS CHAR) AS `{c}`" for c in cols)
    pk = cle_primaire(src, t)
    bon = q(f"SELECT {sel} FROM {src}.`{t}` ORDER BY " + ", ".join(f"`{c}`" for c in pk))
    naif = q(f"SELECT * FROM {src}.`{t}` ORDER BY " + ", ".join(f"`{c}`" for c in pk)).astype(str)
    for c in cols:
        b = bon[c].astype(object).where(bon[c].notna(), "\\N").astype(str)
        diff = (b != naif[c])
        if diff.any():
            i = diff.idxmax()
            ep3.append({"Table": f"{src}.{t}", "Colonne": c, "Cellules altérées": int(diff.sum()),
                        "Valeur source (\\N = NULL)": b[i], "Lecture naïve": naif[c][i]})
ep3 = pd.DataFrame(ep3) if ep3 else pd.DataFrame([{"Table": "-", "Colonne": "-", "Cellules altérées": 0, "Valeur source (\\N = NULL)": "-", "Lecture naïve": "-"}])
montrer(ep3, "Épreuve 3 · Écarts d'une lecture naïve (SELECT * puis astype(str)) par rapport à la source")
RESULTATS["epreuve3_conversion"] = ep3.to_dict(orient="records")

# %% [markdown]
# ## US-06 · Profil de crm.client (mesuré sur bronze, lot BATCH_ID)
# NULL, vide ('') et blanc (que des espaces) sont comptés séparément.

# %% US-06
CL = "bronze.crm_client"
cols_cl = colonnes("crm", "client")
prof = []
n_cl = scal(f"SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b", b=BATCH_ID)
for c in cols_cl:
    r = q(f"""SELECT SUM(`{c}` IS NULL) nuls, SUM(`{c}` = '') vides, SUM(`{c}` <> '' AND TRIM(`{c}`) = '') blancs,
                     SUM(`{c}` <> TRIM(`{c}`) AND TRIM(`{c}`) <> '') espaces_parasites,
                     COUNT(DISTINCT `{c}`) distincts, MIN(CHAR_LENGTH(`{c}`)) lg_min, MAX(CHAR_LENGTH(`{c}`)) lg_max
              FROM {CL} WHERE _batch_id = :b""", b=BATCH_ID).iloc[0]
    prof.append({"Colonne": c, "Lignes": n_cl, **{k: (None if pd.isna(v) else int(v)) for k, v in r.items()}})
prof = pd.DataFrame(prof)
prof["% nuls"] = (100 * prof["nuls"] / n_cl).round(2)
montrer(prof, "US-06 · Profil colonne par colonne de crm.client (BRONZE)")
RESULTATS["us06_profil"] = prof.to_dict(orient="records")

def compte(sql):
    return scal(sql.replace("{CL}", CL), b=BATCH_ID)

tp = q(f"SELECT COALESCE(type_personne, '(NULL)') valeur, COUNT(*) lignes FROM {CL} WHERE _batch_id = :b GROUP BY type_personne ORDER BY lignes DESC", b=BATCH_ID)
montrer(tp, "US-06 · Domaine de type_personne (attendu : prospect, souscripteur, assure)")
pays_top = q(f"SELECT CONCAT('[', COALESCE(pays, 'NULL'), ']') valeur, COUNT(*) lignes FROM {CL} WHERE _batch_id = :b GROUP BY pays ORDER BY lignes DESC LIMIT 15", b=BATCH_ID)
montrer(pays_top, "US-06 · Valeurs de pays (crochets pour voir les espaces)")

constats = pd.DataFrame([
    {"Colonne": "type_personne", "Indicateur": "hors domaine {prospect, souscripteur, assure} (NULL inclus)",
     "Valeur": compte("SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND (type_personne IS NULL OR type_personne NOT IN ('prospect','souscripteur','assure'))")},
    {"Colonne": "telephone", "Indicateur": "NULL / vide / blanc",
     "Valeur": " / ".join(str(compte(s)) for s in [
         "SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND telephone IS NULL",
         "SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND telephone = ''",
         "SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND telephone <> '' AND TRIM(telephone) = ''"])},
    {"Colonne": "nom / raison_sociale", "Indicateur": "personnes morales (nom NULL, raison_sociale renseignée)",
     "Valeur": compte("SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND nom IS NULL AND raison_sociale IS NOT NULL")},
    {"Colonne": "nom / raison_sociale", "Indicateur": "ni nom ni raison sociale",
     "Valeur": compte("SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND (nom IS NULL OR TRIM(nom) = '') AND (raison_sociale IS NULL OR TRIM(raison_sociale) = '')")},
    {"Colonne": "date_naissance", "Indicateur": "personnes physiques sans date de naissance",
     "Valeur": compte("SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND raison_sociale IS NULL AND date_naissance IS NULL")},
    {"Colonne": "date_naissance", "Indicateur": "min / max",
     "Valeur": " / ".join(str(v) for v in q(f"SELECT MIN(date_naissance) a, MAX(date_naissance) z FROM {CL} WHERE _batch_id = :b", b=BATCH_ID).iloc[0])},
    {"Colonne": "date_naissance", "Indicateur": f"postérieure à la date de référence {DATE_REF} ou avant 1900",
     "Valeur": scal(f"SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND (date_naissance > :d OR date_naissance < '1900-01-01')", b=BATCH_ID, d=DATE_REF)},
    {"Colonne": "client_id", "Indicateur": "hors motif ^[AHS]-[0-9]+$",
     "Valeur": compte("SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND (client_id IS NULL OR client_id NOT REGEXP '^[AHS]-[0-9]+$')")},
    {"Colonne": "pays", "Indicateur": "valeurs distinctes (NULL exclu)",
     "Valeur": compte("SELECT COUNT(DISTINCT pays) FROM {CL} WHERE _batch_id = :b")},
    {"Colonne": "email", "Indicateur": "renseigné mais hors motif simple x@y.zz",
     "Valeur": compte("SELECT COUNT(*) FROM {CL} WHERE _batch_id = :b AND email IS NOT NULL AND TRIM(email) <> '' AND email NOT REGEXP '^[^@[:space:]]+@[^@[:space:]]+\\\\.[A-Za-z]{2,}$'")},
    {"Colonne": "nom + prenom + date_naissance", "Indicateur": "lignes en double, NULL écartés (personnes physiques)",
     "Valeur": compte("SELECT COALESCE(SUM(n - 1), 0) FROM (SELECT COUNT(*) n FROM {CL} WHERE _batch_id = :b AND nom IS NOT NULL AND prenom IS NOT NULL AND date_naissance IS NOT NULL GROUP BY nom, prenom, date_naissance HAVING n > 1) d")},
    {"Colonne": "nom + prenom + date_naissance", "Indicateur": "même calcul SANS écarter les NULL (piège : les personnes morales se comptent entre elles)",
     "Valeur": int(pd.read_sql(text(f"SELECT nom, prenom, date_naissance FROM {CL} WHERE _batch_id = :b"), eng.connect(), params={"b": BATCH_ID}).duplicated(keep="first").sum())},
])
montrer(constats, "US-06 · Constats chiffrés sur crm.client (BRONZE)")
RESULTATS["us06_constats"] = constats.to_dict(orient="records")

# %% [markdown]
# ## US-07 · Motifs : code postal, téléphone, pays
# - Code postal (adresse en France, `pays` = 'FR' après TRIM/UPPER, ou 'FRANCE') : `^[0-9]{5}$`.
# - Téléphone : brut `^0[1-9][0-9]{8}$`, puis normalisé (espaces, points, tirets retirés ; +33 et 0033 → 0).
# - Pays : code ISO à deux lettres majuscules présent dans `cif.pays` (référentiel des pays).

# %% US-07
FR = "UPPER(TRIM(pays)) IN ('FR', 'FRANCE', 'FRA')"
TEL_N = "REGEXP_REPLACE(REGEXP_REPLACE(REGEXP_REPLACE(telephone, '[ .()-]', ''), '^\\\\+33', '0'), '^0033', '0')"

def motif(nom, motif_txt, perimetre, conforme, exemple_ko):
    n = compte(f"SELECT COUNT(*) FROM {{CL}} WHERE _batch_id = :b AND {perimetre}")
    ok = compte(f"SELECT COUNT(*) FROM {{CL}} WHERE _batch_id = :b AND {perimetre} AND {conforme}")
    ex = q(f"SELECT CONCAT('[', COALESCE({exemple_ko}, 'NULL'), ']') v, COUNT(*) n FROM {CL} WHERE _batch_id = :b AND {perimetre} AND NOT COALESCE({conforme}, 0) GROUP BY v ORDER BY n DESC LIMIT 3", b=BATCH_ID)
    return {"Attribut": nom, "Motif testé": motif_txt, "Périmètre (lignes)": n, "Conformes": ok, "Non conformes": n - ok,
            "% conformes": round(100 * ok / n, 2) if n else None,
            "Exemples non conformes (fréquence)": "; ".join(f"{r.v} ×{r.n}" for r in ex.itertuples())}

mot = pd.DataFrame([
    motif("Code postal (RQ-005)", "^[0-9]{5}$, pays = 'FR' exactement", "pays = 'FR'", "cp REGEXP '^[0-9]{5}$'", "cp"),
    motif("Code postal", "^[0-9]{5}$, adresse en France (FR, France, fr après TRIM/UPPER)", FR, "cp REGEXP '^[0-9]{5}$'", "cp"),
    motif("Code postal", "^[0-9]{5}$, toutes adresses", "1=1", "cp REGEXP '^[0-9]{5}$'", "cp"),
    motif("Téléphone (brut)", "^0[1-9][0-9]{8}$, adresse en France", FR, "telephone REGEXP '^0[1-9][0-9]{8}$'", "telephone"),
    motif("Téléphone (normalisé)", "^0[1-9][0-9]{8}$ après nettoyage, adresse en France", FR, f"{TEL_N} REGEXP '^0[1-9][0-9]{{8}}$'", "telephone"),
    motif("Pays (format)", "^[A-Z]{2}$", "1=1", "pays REGEXP '^[A-Z]{2}$'", "pays"),
    motif("Pays (référentiel)", "code présent dans silver.ref_pays", "1=1", "pays IN (SELECT code_pays FROM silver.ref_pays)", "pays"),
])
detail_cp = pd.DataFrame([
    {"Code postal, adresse en France": "NULL", "Lignes": compte(f"SELECT COUNT(*) FROM {{CL}} WHERE _batch_id = :b AND {FR} AND cp IS NULL")},
    {"Code postal, adresse en France": "vide ou blanc", "Lignes": compte(f"SELECT COUNT(*) FROM {{CL}} WHERE _batch_id = :b AND {FR} AND cp IS NOT NULL AND TRIM(cp) = ''")},
    {"Code postal, adresse en France": "4 chiffres (zéro initial perdu ?)", "Lignes": compte(f"SELECT COUNT(*) FROM {{CL}} WHERE _batch_id = :b AND {FR} AND cp REGEXP '^[0-9]{{4}}$'")},
    {"Code postal, adresse en France": "autre format", "Lignes": compte(f"SELECT COUNT(*) FROM {{CL}} WHERE _batch_id = :b AND {FR} AND TRIM(cp) <> '' AND cp NOT REGEXP '^[0-9]{{4,5}}$'")},
])
montrer(mot, "US-07 · Motifs (BRONZE, crm.client)")
montrer(detail_cp, "US-07 · Détail des codes postaux non conformes (adresse en France)")
RESULTATS["us07_motifs"] = mot.to_dict(orient="records")
RESULTATS["us07_detail_cp"] = detail_cp.to_dict(orient="records")

# %% [markdown]
# ## US-04 · Dictionnaire du CIF : deviner le sens des colonnes anonymes
# Pour chaque colonne : taux de NULL, distincts, unicité, longueurs, et taux de valeurs conformes à des formats candidats.
# Le nom proposé est celui du format le mieux vérifié ; la justification est chiffrée. **Relisez chaque proposition**.

# %% US-04
FORMATS = {
    "identifiant (unique, chiffres)": r"^[0-9]+$",
    "date JJ/MM/AAAA": r"^[0-3][0-9]/[01][0-9]/(19|20)[0-9]{2}$",
    "date AAAA-MM-JJ": r"^(19|20)[0-9]{2}-[01][0-9]-[0-3][0-9]$",
    "code postal 5 chiffres": r"^[0-9]{5}$",
    "téléphone": r"^(\+|00)?[0-9 .-]{9,}$",
    "e-mail": r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$",
    "code pays ISO2": r"^[A-Z]{2}$",
    "adresse (numéro + voie)": r"^[0-9]+\s*(bis|ter)?,?\s+\D+",
    "code 1 caractère": r"^[A-Z]$",
    "texte alphabétique": r"^[A-Za-zÀ-ÿ' -]+$",
}

def profil_cif(table, base="bronze"):
    df = pd.read_sql(text(f"SELECT * FROM {base}.`{table}` WHERE _batch_id = :b"), eng.connect(), params={"b": BATCH_ID}, dtype=object)
    df = df[[c for c in df.columns if c.startswith("column")]]
    lignes = []
    for c in df.columns:
        s = df[c].dropna().astype(str)
        s = s[s.str.strip() != ""]
        n = len(df)
        taux = {f: round(100 * s.str.match(p).mean(), 1) if len(s) else 0.0 for f, p in FORMATS.items()}
        r = {"Colonne": c, "Lignes": n, "% NULL ou vide": round(100 * (n - len(s)) / n, 1) if n else None,
             "Distincts": int(s.nunique()), "% uniques": round(100 * s.nunique() / len(s), 1) if len(s) else 0,
             "Long. min-max": f"{s.str.len().min()}-{s.str.len().max()}" if len(s) else "-",
             **{f"% {f}": v for f, v in taux.items()}}
        lignes.append((r, s, taux))
    return lignes

def proposer(colonne, s, taux, contexte):
    """Règles de décision, dans l'ordre : le premier format vérifié par au moins 80 % des valeurs renseignées l'emporte."""
    uniq = s.nunique() / len(s) if len(s) else 0
    regles = [
        ("e-mail", "email", "VARCHAR(150)", lambda t: f"{t} % au motif x@y.zz"),
        ("date JJ/MM/AAAA", "date_naissance" if contexte == "clients" else "date_ouverture", "DATE (texte JJ/MM/AAAA à convertir)",
         lambda t: f"{t} % au format JJ/MM/AAAA, années {s.str[-4:].min()} à {s.str[-4:].max()}"),
        ("date AAAA-MM-JJ", "date_naissance" if contexte == "clients" else "date_ouverture", "DATE",
         lambda t: f"{t} % au format AAAA-MM-JJ, de {s.min()} à {s.max()}"),
        ("code postal 5 chiffres", "code_postal", "CHAR(5)", lambda t: f"{t} % de valeurs à 5 chiffres, {s.nunique()} distincts"),
        ("téléphone", "telephone", "VARCHAR(20)", lambda t: f"{t} % de valeurs numériques de 9 caractères ou plus, {round(100*s.str.match(r'^0[1-9][0-9]{8}$').mean(),1)} % au format 0X XX XX XX XX"),
        ("code pays ISO2", "code_pays", "CHAR(2)", lambda t: f"{t} % de codes à 2 majuscules, {round(100*s.isin(contexte_pays).mean(),1)} % présents dans cif.pays, {s.nunique()} distincts"),
        ("adresse (numéro + voie)", "adresse", "VARCHAR(255)", lambda t: f"{t} % commencent par un numéro suivi d'un libellé de voie"),
        ("code 1 caractère", "statut", "CHAR(1)", lambda t: f"{t} % d'un seul caractère ; domaine : " + ", ".join(f"{k}={v}" for k, v in s.value_counts().head(4).items())),
    ]
    for fmt, nom, typ, j in regles:
        if taux.get(fmt, 0) >= 80:
            return nom, typ, j(taux[fmt])
    if uniq >= 0.999:                                  # aucune forme reconnue mais toutes les valeurs sont uniques : identifiant
        return "id_cif", "VARCHAR(10) (clé)", f"{round(100*uniq,2)} % de valeurs uniques, {s.nunique()} distincts, longueur {s.str.len().min()}-{s.str.len().max()}, aucun format métier reconnu"
    return None, None, None

contexte_pays = set(q("SELECT code_pays FROM cif.pays")["code_pays"])
dico = []
noms_crm = set(q("SELECT DISTINCT UPPER(nom) v FROM crm.client WHERE nom IS NOT NULL")["v"])
prenoms_crm = set(q("SELECT DISTINCT UPPER(prenom) v FROM crm.client WHERE prenom IS NOT NULL")["v"])
villes_crm = set(q("SELECT DISTINCT UPPER(ville) v FROM crm.client WHERE ville IS NOT NULL")["v"])
ids_clients = set(q("SELECT column0 v FROM cif.clients")["v"])
profils = {}
for table in ("cif_clients", "cif_compte"):
    ctx = "clients" if table == "cif_clients" else "compte"
    lignes = profil_cif(table)
    profils[table] = pd.DataFrame([r for r, _, _ in lignes])
    for r, s, taux in lignes:
        nom, typ, just = proposer(r["Colonne"], s, taux, ctx)
        if nom is None:
            up = s.str.upper()
            recouv = {"nom ou raison sociale": up.isin(noms_crm).mean(), "prenom": up.isin(prenoms_crm).mean(), "ville": up.isin(villes_crm).mean()}
            meilleur = max(recouv, key=recouv.get)
            nom = {"nom ou raison sociale": "nom_ou_raison_sociale", "prenom": "prenom", "ville": "ville"}[meilleur]
            typ = "VARCHAR"
            just = (f"{taux.get('texte alphabétique', 0)} % alphabétique, {s.nunique()} distincts ; recouvrement avec crm.client : "
                    + ", ".join(f"{k} {round(100*v,1)} %" for k, v in recouv.items()))
        if ctx == "compte" and r["Colonne"] != "column0" and s.isin(ids_clients).mean() > 0.9:
            nom, typ = "id_cif", "VARCHAR (clé étrangère vers cif.clients.column0)"
            just = f"{round(100*s.isin(ids_clients).mean(),1)} % des valeurs existent dans cif.clients.column0 ; {round(100*s.nunique()/len(s),1)} % uniques (plusieurs comptes par client)"
        elif ctx == "compte" and r["Colonne"] == "column0":
            nom, typ = "id_compte", "VARCHAR (clé primaire)"
            just = f"{r['% uniques']} % de valeurs uniques, longueur {r['Long. min-max']}"
        dico.append({"Table": f"cif.{ctx if ctx == 'compte' else 'clients'}", "Colonne d'origine": r["Colonne"], "Nom proposé": nom, "Type": typ,
                     "Justification chiffrée": just, "% NULL ou vide": r["% NULL ou vide"]})
for table, p in profils.items():
    montrer(p, f"US-04 · Profil des colonnes anonymes de {table} (BRONZE)")
dico = pd.DataFrame(dico)
montrer(dico, "US-04 · Dictionnaire proposé du CIF (à relire et valider par le Data Steward)")
RESULTATS["us04_dictionnaire"] = dico.to_dict(orient="records")

# %% [markdown]
# ## US-09 · Trois définitions du « client actif »
# Les définitions ci-dessous sont des paramètres : **recopiez celles de l'onglet User Stories (US-09)** si elles diffèrent.
# On compte des souscripteurs distincts (NULL écartés) à la date de référence du lot.

# %% US-09
EN_COURS = "c.date_debut <= :d AND c.date_fin >= :d"
COTIS_3M = "c.date_derniere_cotisation >= :m"
# Définitions de la fiche CD-001 (onglet Gouvernance du TD, reprises dans pipelines/S1_bronze_profilage.py du dépôt modèle)
DEFINITIONS = {
    "Commerciale": ("au moins un contrat (quel que soit son état)",
                    "SELECT DISTINCT c.souscripteur_id id FROM crm.contrat c WHERE c.souscripteur_id IS NOT NULL AND :d = :d AND :m = :m"),
    "Sinistres": ("un contrat en cours à la date de référence (début ≤ date ≤ fin)",
                  f"SELECT DISTINCT c.souscripteur_id id FROM crm.contrat c WHERE c.souscripteur_id IS NOT NULL AND {EN_COURS} AND :m = :m"),
    "Risques": ("CD-001 : un contrat en cours ET une cotisation à jour sur les trois derniers mois",
                f"SELECT DISTINCT c.souscripteur_id id FROM crm.contrat c WHERE c.souscripteur_id IS NOT NULL AND {EN_COURS} AND {COTIS_3M}"),
}
CD001 = DEFINITIONS["Risques"]
ens = {k: set(q(v[1], d=DATE_REF, m=COTISATION_MIN)["id"]) for k, v in DEFINITIONS.items()}
cd = ens["Risques"]
ca = pd.DataFrame([{"Direction": k, "Définition utilisée": DEFINITIONS[k][0], "Nombre de clients": len(s),
                    "Écart avec CD-001": len(s) - len(cd), "Dans la direction mais pas CD-001": len(s - cd), "Dans CD-001 mais pas la direction": len(cd - s)}
                   for k, s in ens.items()])
ca["Rapport à la plus large"] = (ca["Nombre de clients"] / ca["Nombre de clients"].max()).round(3)
montrer(ca, f"US-09 · Client actif au {DATE_REF}, cotisation depuis le {COTISATION_MIN} (souscripteurs distincts, crm)")
bornes = q("SELECT MIN(date_debut) debut_min, MAX(date_debut) debut_max, MAX(date_fin) fin_max, MAX(date_derniere_cotisation) cotis_max FROM crm.contrat").astype(str)
montrer(bornes, "US-09 · Bornes des dates de crm.contrat (pour vérifier que la date de référence est cohérente)")
RESULTATS["us09_client_actif"] = ca.to_dict(orient="records")
RESULTATS["us09_requetes"] = {k: v[1] for k, v in DEFINITIONS.items()}

# %% [markdown]
# ## (Option) Rapport YData-Profiling de crm.client : `--ydata`

# %% YData
if "--ydata" in sys.argv:
    from ydata_profiling import ProfileReport
    dfp = pd.read_sql(text(f"SELECT {', '.join('`'+c+'`' for c in cols_cl)} FROM {CL} WHERE _batch_id = :b"), eng.connect(), params={"b": BATCH_ID})
    sortie = os.path.join(BASE, "reports", "ydata_profiling_client.html")
    ProfileReport(dfp, title=f"AssurConnect — crm.client (bronze, lot {BATCH_ID})", minimal=True).to_file(sortie)
    print("Rapport :", sortie)

# %% Écriture des preuves
with open(os.path.join(REPORTS, "S1_resultats.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(MD) + "\n")
with open(os.path.join(REPORTS, "s1_resultats.json"), "w", encoding="utf-8") as f:
    json.dump(RESULTATS, f, ensure_ascii=False, indent=1, default=str)
print("\nPreuves écrites :", os.path.join(REPORTS, "S1_resultats.md"), "et s1_resultats.json")
