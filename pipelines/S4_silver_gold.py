# -*- coding: utf-8 -*-
# ==============================================================================
# S4 : construire silver puis gold, rapprocher les identités, retracer une donnée     (US-21 à US-28, en Python)
# Outils : PySpark 3.5 (standardisation et quarantaine), Great Expectations et Soda Core (re-mesure), rapidfuzz (rapprochement), pandas.
# Prérequis : S1 à S3 terminées (bronze alimentée, mesures de base). Lancez le fichier entier : python pipelines/S4_silver_gold.py
# ou copiez les cellules « # %% » dans votre notebook S4_<groupe>.ipynb. Les observations et les décisions s'écrivent dans livrables/S4_silver_gold.md.
# Aucune donnée n'est modifiée en place : silver s'écrit à partir de bronze, gold à partir de silver. Rejouer le fichier reconstruit le lot sans doublon.
# ==============================================================================

# %% Paramètres, session Spark et petites fonctions communes
import sys, os, re, time, subprocess, warnings
sys.path.append("../pipelines")
from aq import *
import numpy as np
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StructType, StructField, StringType, LongType
warnings.filterwarnings("ignore")

os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
spark = (SparkSession.builder.appName("build_silver").master("local[2]")
         .config("spark.sql.session.timeZone", "UTC").config("spark.sql.legacy.timeParserPolicy", "CORRECTED")
         .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "4").getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
print("Session Spark :", spark.version)          # à vérifier avant de commencer (fiche S4, 0:00 – 0:25)

def vers_spark(df):
    """pandas vers Spark. Pas de JDBC dans cette pile : 100 000 lignes passent sans difficulté par pandas."""
    schema = StructType([StructField(c, LongType() if c == "bronze_row_id" else StringType(), True) for c in df.columns])
    return spark.createDataFrame(df.astype(object).where(df.notna(), None), schema)

def depuis_bronze(requete):
    return vers_spark(lire(requete, b=BATCH))

def total(requete, **p):
    return int(lire(requete, **p).iloc[0, 0])


# %% US-21 · Règles de standardisation : majuscules, sans accent, pays ISO, téléphone, code postal (PySpark)
ACC_DE = "ÀÁÂÃÄÅàáâãäåÇçÈÉÊËèéêëÌÍÎÏìíîïÑñÒÓÔÕÖòóôõöÙÚÛÜùúûüÝýÿ"
ACC_A  = "AAAAAAaaaaaaCcEEEEeeeeIIIIiiiiNnOOOOOoooooUUUUuuuuYyy"
PAYS_FR = ["FR", "FRANCE", "F", "FRNACE"]

def sans_accent(c):
    return F.regexp_replace(F.translate(c, ACC_DE, ACC_A), r"[^\x00-\x7F]", "")

def vide_en_null(c):
    return F.when(c.isNotNull() & (c != ""), c)

def maj(c):                       # majuscules, sans accent, espaces compactés ; vide -> NULL
    return vide_en_null(F.trim(F.regexp_replace(F.upper(sans_accent(c)), r"\s+", " ")))

def identite(c):                  # raison sociale ou nom : sans préfixe « société », S.A.R.L. ramené à SARL
    r = F.regexp_replace(maj(c), r"^(SOCIETE|SOC\.?|STE|ETS)\s+", "")
    r = F.regexp_replace(r, r"(?<![A-Z])S\.?\s*A\.?\s*R\.?\s*L\.?(?![A-Z])", "SARL")
    return F.trim(F.regexp_replace(r, r"\s+", " "))

def adresse(c):
    r = maj(c)
    for a, b in [(r"\bR\.\s*", "RUE "), (r"\bAV\.\s*", "AVENUE "), (r"\bBD\s+", "BOULEVARD "), (r"\bCH\.\s*", "CHEMIN "), (r"\bIMP\.\s*", "IMPASSE ")]:
        r = F.regexp_replace(r, a, b)
    return F.trim(F.regexp_replace(r, r"\s+", " "))

def telephone(c):                 # chiffres seulement, +33 et 0033 ramenés à 0
    r = vide_en_null(F.trim(c))
    return F.regexp_replace(F.regexp_replace(r, r"[ .\-()]", ""), r"^(\+33|0033)", "0")

def pays(c):                      # variantes de France ramenées à FR ; une valeur vide ou inconnue n'est pas devinée (RQ-007 la met en quarantaine)
    r = vide_en_null(F.upper(F.trim(c)))
    return F.when(r.isin(PAYS_FR), "FR").otherwise(r)

def courriel(c):
    return vide_en_null(F.lower(F.trim(c)))

def client_crm(b):
    p = pays(F.col("pays"))
    cp0 = F.trim(F.col("cp"))
    zero = F.coalesce(cp0.rlike(r"^[0-9]{4}$") & (p == "FR"), F.lit(False))            # zéro initial perdu : restauré pour la France seulement
    morale = F.col("raison_sociale").isNotNull() & (F.trim(F.col("raison_sociale")) != "")
    return b.select("bronze_row_id", F.lit("crm").alias("source_systeme"), F.col("client_id").alias("source_id"),
        F.when(F.col("type_personne").isin("prospect", "souscripteur", "assure"), F.col("type_personne")).alias("type_personne"),
        identite(F.when(morale, F.col("raison_sociale")).otherwise(F.col("nom"))).alias("identite_normalisee"),
        maj(F.col("prenom")).alias("prenom_normalise"),
        F.to_date("date_naissance", "yyyy-MM-dd").alias("date_naissance"),
        adresse(F.col("adresse")).alias("adresse_normalisee"),
        p.alias("pays_iso"),
        F.when(zero, F.lpad(cp0, 5, "0")).otherwise(cp0).alias("cp"),
        maj(F.col("ville")).alias("ville_normalisee"),
        telephone(F.col("telephone")).alias("telephone_normalise"),
        courriel(F.col("email")).alias("email_normalise"),
        F.when(zero, "A_SURVEILLER").otherwise("VALIDE").alias("statut_qualite"))

def client_cif(c):                # le CIF est anonyme : column0 identifiant, 1 identité, 2 prénom, 3 naissance (jj/mm/aaaa), 4 adresse, 5 code postal, 6 ville, 7 pays, 8 téléphone, 9 e-mail
    p = pays(F.col("column7"))
    cp0 = F.trim(F.col("column5"))
    zero = F.coalesce(cp0.rlike(r"^[0-9]{4}$") & (p == "FR"), F.lit(False))
    return c.select("bronze_row_id", F.lit("cif").alias("source_systeme"), F.col("column0").alias("source_id"), F.lit(None).cast("string").alias("type_personne"),
        identite(F.col("column1")).alias("identite_normalisee"), maj(F.col("column2")).alias("prenom_normalise"),
        F.to_date("column3", "dd/MM/yyyy").alias("date_naissance"), adresse(F.col("column4")).alias("adresse_normalisee"),
        p.alias("pays_iso"), F.when(zero, F.lpad(cp0, 5, "0")).otherwise(cp0).alias("cp"), maj(F.col("column6")).alias("ville_normalisee"),
        telephone(F.col("column8")).alias("telephone_normalise"), courriel(F.col("column9")).alias("email_normalise"),
        F.when(zero, "A_SURVEILLER").otherwise("VALIDE").alias("statut_qualite"))

def contrat_silver(k):
    return k.select("bronze_row_id", "contrat_id", "souscripteur_id",
        F.when(F.col("assure_id") != "0", F.col("assure_id")).alias("assure_id"),                 # la sentinelle '0' devient NULL (US-17)
        "code_type", F.to_date("date_debut", "yyyy-MM-dd").alias("date_debut"), F.to_date("date_fin", "yyyy-MM-dd").alias("date_fin"),
        F.col("duree_garantie_mois").cast("int").alias("duree_garantie_mois"), F.col("prime_annuelle").cast("decimal(10,2)").alias("prime_annuelle"),
        F.to_date("date_derniere_cotisation", "yyyy-MM-dd").alias("date_derniere_cotisation"))

def sinistre_silver(s):
    return s.select("bronze_row_id", "sinistre_id", "contrat_id",
        F.to_date("date_survenance", "yyyy-MM-dd").alias("date_survenance"), F.to_date("date_declaration", "yyyy-MM-dd").alias("date_declaration"),
        "type_sinistre", F.col("montant_estime").cast("decimal(12,2)").alias("montant_estime"),
        adresse(F.col("adresse_sinistre")).alias("adresse_normalisee"), F.col("cp_sinistre").alias("cp"),
        maj(F.col("ville_sinistre")).alias("ville_normalisee"), "canal_saisie")

# Mesure avant / après sur la même colonne : ce que la standardisation change
avant_apres = pd.DataFrame([
    ("variantes de pays (crm)", total("SELECT COUNT(DISTINCT pays) FROM bronze.crm_client WHERE _batch_id = :b", b=BATCH), None),
    ("codes postaux à 4 chiffres, adresse en France (crm)", total("SELECT COUNT(*) FROM bronze.crm_client WHERE _batch_id = :b AND pays = 'FR' AND cp REGEXP '^[0-9]{4}$'", b=BATCH), None)],
    columns=["mesure", "bronze", "silver"])
print(avant_apres.to_string(index=False), "\n(la colonne silver se remplit après la construction, deux cellules plus bas)")


# %% US-21, 22 · Bronze vers silver, pare-feu qualité et quarantaine (une fonction idempotente)
DDL_SILVER = [
 "CREATE TABLE IF NOT EXISTS silver.type_contrat (code_type VARCHAR(10) PRIMARY KEY, libelle VARCHAR(80) NOT NULL, branche VARCHAR(20) NOT NULL)",
 """CREATE TABLE IF NOT EXISTS silver.contrat (
  silver_row_id BIGINT AUTO_INCREMENT PRIMARY KEY, bronze_row_id BIGINT NOT NULL,
  contrat_id VARCHAR(12) NOT NULL, souscripteur_id VARCHAR(12), assure_id VARCHAR(12),
  code_type VARCHAR(10), date_debut DATE, date_fin DATE, duree_garantie_mois INT, prime_annuelle DECIMAL(10,2), date_derniere_cotisation DATE,
  _batch_id VARCHAR(20) NOT NULL, _processed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bronze (bronze_row_id), KEY idx_contrat (contrat_id), KEY idx_souscripteur (souscripteur_id), KEY idx_assure (assure_id))""",
 """CREATE TABLE IF NOT EXISTS silver.sinistre (
  silver_row_id BIGINT AUTO_INCREMENT PRIMARY KEY, bronze_row_id BIGINT NOT NULL,
  sinistre_id VARCHAR(12) NOT NULL, contrat_id VARCHAR(12), date_survenance DATE, date_declaration DATE, type_sinistre VARCHAR(40),
  montant_estime DECIMAL(12,2), adresse_normalisee VARCHAR(160), cp VARCHAR(10), ville_normalisee VARCHAR(80), canal_saisie VARCHAR(30),
  _batch_id VARCHAR(20) NOT NULL, _processed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_bronze (bronze_row_id), KEY idx_contrat (contrat_id))"""]

def rejet(df, entite, source, regle, motif):
    """Lignes écartées : leur identifiant bronze, le code de la règle bloquante et le motif. Rien ne disparaît sans trace."""
    return df.select(F.lit(BATCH).alias("batch_id"), F.lit(entite).alias("entite"), F.lit(source).alias("source_systeme"), "bronze_row_id",
                     F.lit(regle).alias("rule_id"), F.lit("S").alias("porte"), F.lit(motif).alias("motif"))

def construire_silver():
    for ddl in DDL_SILVER:
        executer(ddl)
    for t in ["client", "contrat", "sinistre"]:
        executer(f"DELETE FROM silver.{t} WHERE _batch_id = :b", b=BATCH)          # rejouer remplace le lot : pas de doublon
    executer("DELETE FROM silver.type_contrat")
    executer("DELETE FROM dq.rejets WHERE batch_id = :b AND porte = 'S'", b=BATCH)
    codes_pays = lire("SELECT code_pays FROM silver.ref_pays").code_pays.tolist()
    types = ["prospect", "souscripteur", "assure"]
    rejets, bilan = [], {}

    # client : CRM puis CIF dans la même table, avec la source
    b = depuis_bronze("SELECT bronze_row_id, client_id, type_personne, nom, prenom, raison_sociale, date_naissance, adresse, cp, ville, pays, telephone, email FROM bronze.crm_client WHERE _batch_id = :b")
    s = client_crm(b)
    ko009 = F.col("type_personne").isNull()                                                  # hors domaine (ou absent) : type_personne a été annulé par la normalisation
    ko007 = ~F.coalesce(F.col("pays_iso").isin(*codes_pays), F.lit(False))
    rejets += [rejet(s.filter(ko009), "client", "crm", "RQ-009", "type_personne hors domaine"),
               rejet(s.filter(ko007), "client", "crm", "RQ-007", "pays absent du référentiel après normalisation (non deviné)")]
    valides_crm = s.filter(~(ko007 | ko009))
    c = depuis_bronze("SELECT bronze_row_id, column0, column1, column2, column3, column4, column5, column6, column7, column8, column9 FROM bronze.cif_clients WHERE _batch_id = :b")
    sc = client_cif(c)
    rejets.append(rejet(sc.filter(ko007), "client", "cif", "RQ-007", "pays absent du référentiel après normalisation (non deviné)"))
    valides = valides_crm.unionByName(sc.filter(~ko007)).withColumn("_batch_id", F.lit(BATCH))
    out = valides.toPandas()
    ecrire(out, "silver", "client")
    bilan["client_crm"] = (total("SELECT COUNT(*) FROM bronze.crm_client WHERE _batch_id = :b", b=BATCH), int((out.source_systeme == "crm").sum()))
    bilan["client_cif"] = (total("SELECT COUNT(*) FROM bronze.cif_clients WHERE _batch_id = :b", b=BATCH), int((out.source_systeme == "cif").sum()))

    # contrat
    k = depuis_bronze("SELECT bronze_row_id, contrat_id, souscripteur_id, assure_id, code_type, date_debut, date_fin, duree_garantie_mois, prime_annuelle, date_derniere_cotisation FROM bronze.crm_contrat WHERE _batch_id = :b")
    d = contrat_silver(k)
    ko1 = F.coalesce(F.col("date_fin") <= F.col("date_debut"), F.lit(False))
    ko10 = ~F.coalesce(F.col("duree_garantie_mois").isin(12, 24, 36, 60), F.lit(False))
    rejets += [rejet(d.filter(ko1), "contrat", "crm", "RQ-001", "date_fin <= date_debut"),
               rejet(d.filter(ko10), "contrat", "crm", "RQ-010", "durée de garantie hors 12, 24, 36, 60")]
    out = d.filter(~(ko1 | ko10)).withColumn("_batch_id", F.lit(BATCH)).toPandas()
    ecrire(out, "silver", "contrat")
    bilan["contrat"] = (total("SELECT COUNT(*) FROM bronze.crm_contrat WHERE _batch_id = :b", b=BATCH), len(out))

    # sinistre (aucune règle bloquante de la porte S ne s'y applique : toutes les lignes passent)
    sn = depuis_bronze("SELECT bronze_row_id, sinistre_id, contrat_id, date_survenance, date_declaration, type_sinistre, montant_estime, adresse_sinistre, cp_sinistre, ville_sinistre, canal_saisie FROM bronze.crm_sinistre WHERE _batch_id = :b")
    out = sinistre_silver(sn).withColumn("_batch_id", F.lit(BATCH)).toPandas()
    ecrire(out, "silver", "sinistre")
    bilan["sinistre"] = (total("SELECT COUNT(*) FROM bronze.crm_sinistre WHERE _batch_id = :b", b=BATCH), len(out))

    tc = lire("SELECT code_type, libelle, branche FROM bronze.crm_type_contrat WHERE _batch_id = :b", b=BATCH)
    ecrire(tc, "silver", "type_contrat")

    rej = rejets[0]
    for r in rejets[1:]:
        rej = rej.unionByName(r)
    ecrire(rej.toPandas(), "dq", "rejets")
    return bilan

def signature(table):
    """Somme de contrôle du contenu d'une table silver, sans les colonnes qui changent à chaque reconstruction (silver_row_id, _processed_at)."""
    cols = lire("SELECT column_name AS c FROM information_schema.columns WHERE table_schema = 'silver' AND table_name = :t AND column_name NOT IN ('silver_row_id', '_processed_at') ORDER BY ordinal_position", t=table).c.tolist()
    return lire(f"SELECT COUNT(*) AS n, SUM(CRC32(CONCAT_WS('|', {', '.join(cols)}))) AS crc FROM silver.{table}").iloc[0].tolist()

debut = time.time()
bilan = construire_silver()
print(f"Silver construit en {time.time() - debut:.0f} s")
def rejetees(entite, source):
    return total("SELECT COUNT(DISTINCT bronze_row_id) FROM dq.rejets WHERE batch_id = :b AND porte = 'S' AND entite = :e AND source_systeme = :s", b=BATCH, e=entite, s=source)
conservation = pd.DataFrame([(nom, bilan[nom][0], bilan[nom][1], rejetees(entite, source))
                             for nom, entite, source in [("client_crm", "client", "crm"), ("client_cif", "client", "cif"), ("contrat", "contrat", "crm"), ("sinistre", "sinistre", "crm")]],
                            columns=["table", "bronze", "silver", "rejetees"])
conservation["ecart"] = conservation.bronze - conservation.silver - conservation.rejetees            # RQ-024 : silver + rejetées = bronze
print(conservation.to_string(index=False))
print(lire("SELECT entite, rule_id, COUNT(*) AS lignes FROM dq.rejets WHERE batch_id = :b AND porte = 'S' GROUP BY entite, rule_id ORDER BY entite, rule_id", b=BATCH).to_string(index=False))

avant_apres["silver"] = [total("SELECT COUNT(DISTINCT pays_iso) FROM silver.client WHERE source_systeme = 'crm'"),
                         total("SELECT COUNT(*) FROM silver.client WHERE source_systeme = 'crm' AND pays_iso = 'FR' AND cp REGEXP '^[0-9]{4}$'")]
print(avant_apres.to_string(index=False))


# %% US-21 · Idempotence et traçabilité : relancer donne le même résultat, chaque ligne silver garde son bronze_row_id (RQ-023)
avant = {t: signature(t) for t in ["client", "contrat", "sinistre"]}
construire_silver()
apres = {t: signature(t) for t in ["client", "contrat", "sinistre"]}
print(pd.DataFrame({"premier passage": avant, "second passage": apres}).assign(identique=lambda d: d["premier passage"].astype(str) == d["second passage"].astype(str)))
print("Lignes silver sans ligne bronze d'origine :",
      total("SELECT COUNT(*) FROM silver.client s WHERE NOT EXISTS (SELECT 1 FROM bronze.crm_client b WHERE s.source_systeme = 'crm' AND b.bronze_row_id = s.bronze_row_id) "
            "AND NOT EXISTS (SELECT 1 FROM bronze.cif_clients b WHERE s.source_systeme = 'cif' AND b.bronze_row_id = s.bronze_row_id)"))
# À vous : la liste des règles de normalisation, une ligne par règle, dans livrables/S4_silver_gold.md.


# %% US-23 · Re-mesurer les règles sur silver (porte S) : mêmes suites, même fichiers de checks, autre couche
MESURES_TRACE = {
 "RQ-023": [("client", "SELECT COUNT(*), COALESCE(SUM(NOT EXISTS (SELECT 1 FROM bronze.crm_client b WHERE s.source_systeme = 'crm' AND b.bronze_row_id = s.bronze_row_id) AND NOT EXISTS (SELECT 1 FROM bronze.cif_clients b WHERE s.source_systeme = 'cif' AND b.bronze_row_id = s.bronze_row_id)), 0) FROM silver.client s"),
            ("contrat", "SELECT COUNT(*), COALESCE(SUM(NOT EXISTS (SELECT 1 FROM bronze.crm_contrat b WHERE b.bronze_row_id = s.bronze_row_id)), 0) FROM silver.contrat s"),
            ("sinistre", "SELECT COUNT(*), COALESCE(SUM(NOT EXISTS (SELECT 1 FROM bronze.crm_sinistre b WHERE b.bronze_row_id = s.bronze_row_id)), 0) FROM silver.sinistre s")]}
for rule_id, liste in MESURES_TRACE.items():
    for table, requete in liste:
        n, e = lire(requete).iloc[0]
        mesurer("SILVER", rule_id, table, n, e)
for _, row in conservation.iterrows():
    mesurer("SILVER", "RQ-024", row.table, row.bronze, abs(row.ecart))

# 1. Great Expectations : le fichier S2 se relance tel quel avec COUCHE=SILVER (ses requêtes de chargement savent lire silver).
p = subprocess.run([sys.executable, f"{RACINE}/pipelines/S2_regles_great_expectations.py"], capture_output=True, text=True, env={**os.environ, "COUCHE": "SILVER"})
print("Great Expectations sur silver : code", p.returncode, "" if p.returncode == 0 else p.stderr[-600:])

# 2. Soda Core : les colonnes de silver portent d'autres noms (source_id, pays_iso...), le fichier de checks de silver est donc propre à cette couche.
os.makedirs(f"{SODA}/checks/silver", exist_ok=True)
open(f"{SODA}/checks/silver/integrite_checks.yml", "w", encoding="utf-8").write("""checks for contrat:
  - failed rows:
      name: RQ-011 type de contrat connu
      fail query: |
        SELECT contrat_id FROM contrat WHERE code_type IS NULL OR code_type NOT IN (SELECT code_type FROM type_contrat)
  - failed rows:
      name: RQ-012 souscripteur existant
      fail query: |
        SELECT contrat_id FROM contrat WHERE souscripteur_id IS NULL OR souscripteur_id NOT IN (SELECT source_id FROM client WHERE source_systeme = 'crm')
  - failed rows:
      name: RQ-013 assure existant (sentinelle remplacee par NULL)
      fail query: |
        SELECT contrat_id FROM contrat WHERE assure_id IS NOT NULL AND assure_id NOT IN (SELECT source_id FROM client WHERE source_systeme = 'crm')

checks for client:
  - failed rows:
      name: RQ-015 prospect sans contrat
      fail query: |
        SELECT source_id FROM client WHERE source_systeme = 'crm' AND type_personne = 'prospect' AND source_id IN (SELECT souscripteur_id FROM contrat)
  - failed rows:
      name: RQ-016 souscripteur sans contrat
      fail query: |
        SELECT source_id FROM client WHERE source_systeme = 'crm' AND type_personne = 'souscripteur'
          AND source_id NOT IN (SELECT souscripteur_id FROM contrat WHERE souscripteur_id IS NOT NULL)

checks for sinistre:
  - failed rows:
      name: RQ-017 sinistre hors periode de garantie
      fail query: |
        SELECT s.sinistre_id FROM sinistre s JOIN contrat c ON c.contrat_id = s.contrat_id
        WHERE NOT (s.date_survenance BETWEEN c.date_debut AND c.date_fin)
""")
code, ctl = soda_scan("silver", f"{SODA}/checks/silver/integrite_checks.yml")
print("Soda sur silver : code retour", code, CODES_RETOUR[code])
SODA_SILVER = {
 "RQ-011": ("contrat",  "SELECT COUNT(*) FROM silver.contrat"),
 "RQ-012": ("contrat",  "SELECT COUNT(*) FROM silver.contrat"),
 "RQ-013": ("contrat",  "SELECT COUNT(*) FROM silver.contrat"),
 "RQ-015": ("client",   "SELECT COUNT(*) FROM silver.client WHERE source_systeme = 'crm'"),
 "RQ-016": ("client",   "SELECT COUNT(*) FROM silver.client WHERE source_systeme = 'crm' AND type_personne = 'souscripteur'"),
 "RQ-017": ("sinistre", "SELECT COUNT(*) FROM silver.sinistre s JOIN silver.contrat c ON c.contrat_id = s.contrat_id")}
valeurs = {c["rule_id"]: c["valeur"] for c in ctl}
for rule_id, (table, requete) in SODA_SILVER.items():
    mesurer("SILVER", rule_id, table, total(requete), valeurs[rule_id])

# 3. Tableau bronze contre silver, règle par règle, et verdict de la porte S
m = lire("""SELECT m.rule_id, m.table_cible, m.couche, m.taux_conformite AS taux, r.severite, r.seuil_min, r.porte
            FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id) WHERE m.batch_id = :b AND m.couche IN ('BRONZE', 'SILVER')""", b=BATCH)
m["table_cible"] = m.table_cible.str.replace("^crm_", "", regex=True)
for c in ["taux", "seuil_min"]:
    m[c] = m[c].astype(float)
tableau = m.pivot_table(index=["rule_id", "severite", "porte", "seuil_min"], columns="couche", values="taux", aggfunc="min").reset_index()
tableau["porte_S"] = np.where(tableau.porte == "S", np.where(tableau.SILVER.isna(), "non mesurée", np.where(tableau.SILVER >= tableau.seuil_min, "conforme", "SOUS LE SEUIL")), "")
print(tableau.to_string(index=False))
ouvertes = tableau[(tableau.porte == "S") & (tableau.severite == "BLOQUANTE") & ~(tableau.SILVER >= tableau.seuil_min)].rule_id.tolist()
print("Règles bloquantes de la porte S sous le seuil sur silver :", ouvertes or "aucune : la porte S est franchie")
# Les règles d'intégrité (RQ-011 à 013, 015, 017) se dégradent en silver quand une quarantaine rend des clients absents : c'est l'effet domino, à expliquer, pas à masquer.


# %% US-24 · Rapprochement flou : clé de blocage, score de similarité, zones automatique / revue / rejet (rapidfuzz)
from rapidfuzz import fuzz
SEUIL_AUTO = 85          # ressemblance minimale des identités pour une fusion automatique
SEUIL_REVUE = 70         # en dessous : rejet ; entre les deux : revue manuelle (non fusionné)

def cle_date(d):
    """Clé de naissance insensible à l'inversion jour/mois : (année, plus petit, plus grand)."""
    return None if pd.isna(d) else (d.year, min(d.day, d.month), max(d.day, d.month))

def candidats(df, plafond=400):
    """Paires (i, j) issues de trois clés de blocage : on ne compare que ce qui a une chance d'être la même personne."""
    paires = set()
    cles = {"cp + début d'identité": df.cp.fillna("") + "|" + df.identite_normalisee.fillna("").str[:3],
            "cp + date de naissance": pd.Series([f"{c}|{cle_date(d)}" if cle_date(d) else None for c, d in zip(df.cp.fillna(""), df.date_naissance)], index=df.index),
            "ville + début d'identité": df.ville_normalisee.fillna("") + "|" + df.identite_normalisee.fillna("").str[:4]}
    for nom, k in cles.items():
        for _, idx in pd.Series(np.arange(len(df)), index=df.index).groupby(k.values):
            ix = idx.values
            if 2 <= len(ix) <= plafond:                      # un bloc trop grand n'est pas discriminant : on ne l'explose pas
                a, b = np.triu_indices(len(ix), 1)
                paires.update(zip(ix[a].tolist(), ix[b].tolist()))
    return paires

def noter(df, paires):
    """Score de chaque paire : similarité d'identité (0 à 100) et signaux concordants (adresse, contact, date de naissance)."""
    ident, pren = df.identite_normalisee.fillna("").values, df.prenom_normalise.fillna("").values
    naiss, adr = df.date_naissance.values, df.adresse_normalisee.fillna("").values
    tel, mail, cp = df.telephone_normalise.fillna("").values, df.email_normalise.fillna("").values, df.cp.fillna("").values
    lignes = []
    for i, j in paires:
        sim = fuzz.ratio(ident[i], ident[j])
        if sim < SEUIL_REVUE:
            continue
        if (pren[i] == "") != (pren[j] == ""):               # personne morale contre personne physique : jamais fusionnées
            continue
        if not ((pren[i] == "" and pren[j] == "") or pren[i][:1] == pren[j][:1]):
            continue
        di = cle_date(pd.Timestamp(naiss[i])) if not pd.isna(naiss[i]) else None
        dj = cle_date(pd.Timestamp(naiss[j])) if not pd.isna(naiss[j]) else None
        dob = "inconnue" if di is None or dj is None else ("oui" if di == dj else "non")
        if dob == "non":
            continue
        adr_ok = fuzz.ratio(adr[i], adr[j]) >= 80
        contact = (tel[i] != "" and tel[i] == tel[j]) or (mail[i] != "" and mail[i] == mail[j])
        lignes.append((i, j, sim, dob, int(adr_ok), int(contact), int(adr_ok) + int(contact) + int(dob == "oui"), int(cp[i] == cp[j])))
    return pd.DataFrame(lignes, columns=["i", "j", "sim", "dob", "adresse", "contact", "signaux", "meme_cp"])

def automatiques(S, seuil_auto):
    return S[(S.sim >= seuil_auto) & (S.meme_cp == 1) & (S.signaux >= 1)]

def regrouper(n, paires):
    """Union-find : une paire A-B et une paire B-C donnent le groupe A-B-C. Le groupe porte le plus petit indice."""
    parent = list(range(n))
    def racine(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i, j in paires:
        ri, rj = racine(i), racine(j)
        if ri != rj:
            parent[rj] = ri
    return np.array([racine(x) for x in range(n)])

cl = lire("SELECT * FROM silver.client").sort_values("silver_row_id").reset_index(drop=True)
cl["date_naissance"] = pd.to_datetime(cl.date_naissance)
P = candidats(cl)
S = noter(cl, P)
auto = automatiques(S, SEUIL_AUTO)
cl["groupe"] = regrouper(len(cl), zip(auto.i, auto.j))
print(f"{len(cl)} lignes silver ; {len(P)} paires candidates ; {len(auto)} paires automatiques ; {len(S) - len(auto)} paires à revoir ; {cl.groupe.nunique()} identités uniques")

# Précision et rappel sur les 200 paires étiquetées (prédiction « même personne » = même groupe automatique)
etiq = pd.read_csv(f"{RACINE}/data/referentiels/paires_etiquetees.csv")
def evaluer(groupes):
    g = dict(zip(zip(cl.source_systeme, cl.source_id), groupes))
    paires = [(a, b, c, d, m) for a, b, c, d, m in zip(etiq.gauche_systeme, etiq.gauche_id, etiq.droite_systeme, etiq.droite_id, etiq.meme_personne)
              if (a, b) in g and (c, d) in g]                      # une paire dont une ligne a été mise en quarantaine ne se juge pas
    pred = np.array([g[(a, b)] == g[(c, d)] for a, b, c, d, _ in paires])
    vrai = np.array([m == 1 for *_, m in paires])
    vp, fp, fn = int((pred & vrai).sum()), int((pred & ~vrai).sum()), int((~pred & vrai).sum())
    return {"vrais_positifs": vp, "faux_positifs": fp, "faux_negatifs": fn,
            "precision": round(vp / (vp + fp), 4) if vp + fp else None, "rappel": round(vp / (vp + fn), 4) if vp + fn else None}
print(evaluer(cl.groupe.values))
# Effet du seuil : un seuil plus bas fusionne davantage (le rappel monte, la précision peut baisser)
essais = []
for seuil in (80, 85, 90, 95):
    a = automatiques(S, seuil)
    essais.append({"seuil_auto": seuil, "paires_auto": len(a), **evaluer(regrouper(len(cl), zip(a.i, a.j)))})
print(pd.DataFrame(essais).to_string(index=False))
# Zone « revue » : les paires que la machine ne sait pas décider (à relire une par une)
revue = S[~S.index.isin(auto.index)].sort_values("sim", ascending=False).head(8)
print(pd.DataFrame({"sim": revue.sim.values, "id_a": cl.source_id.values[revue.i], "identite_a": cl.identite_normalisee.values[revue.i],
                    "id_b": cl.source_id.values[revue.j], "identite_b": cl.identite_normalisee.values[revue.j], "signaux": revue.signaux.values}).to_string(index=False))


# %% US-25 · Identifiant client unique (CLI) et golden record : la Société Meunier SARL
ordre = cl.groupby("groupe").silver_row_id.min().sort_values()
cli = {g: f"CLI-{n:06d}" for n, g in enumerate(ordre.index, start=1)}                 # numérotation dans l'ordre de la plus petite ligne silver du groupe
cl["cli_id"] = cl.groupe.map(cli)

# Règle de survie par attribut : priorité à la source CIF (dépôt central), puis CRM ; dans une source, la ligne silver la plus ancienne ; première valeur non nulle.
cl["priorite"] = np.where(cl.source_systeme == "cif", 0, 1)
cl = cl.sort_values(["cli_id", "priorite", "silver_row_id"])
premier = cl.groupby("cli_id").first()
GR = pd.DataFrame({"cli_id": premier.index, "nom_reference": premier.identite_normalisee.fillna("INCONNU").values,
                   "date_naissance": premier.date_naissance.values, "cp": premier.cp.values, "ville": premier.ville_normalisee.values,
                   "pays_iso": premier.pays_iso.values, "telephone": premier.telephone_normalise.values, "email": premier.email_normalise.values})
GR["nb_identifiants_source"] = cl.groupby("cli_id").size().reindex(GR.cli_id).values
GR = GR.reset_index(drop=True)

# Cas pivot : la Société Meunier et ses quatre identifiants (le numéro du CLI dépend de l'ordre de numérotation : on le retrouve par un identifiant source)
cli_meunier = cl[(cl.source_systeme == "crm") & (cl.source_id == "A-4471")].cli_id.iloc[0]
meunier = cl[cl.cli_id == cli_meunier][["cli_id", "source_systeme", "source_id", "identite_normalisee", "cp", "bronze_row_id", "silver_row_id"]]
print(meunier.to_string(index=False))
attendus = {("crm", "A-4471"), ("crm", "H-9012"), ("crm", "S-2208")}
print("Identifiants CRM de la Société Meunier réunis sous un seul CLI :", attendus <= set(zip(meunier.source_systeme, meunier.source_id)),
      "; identifiant CIF réuni :", bool((meunier.source_systeme == "cif").any()))
print("Lignes silver sans CLI :", int(cl.cli_id.isna().sum()), "sur", len(cl))
# À vous : la règle de survie par attribut (qui l'emporte, et pourquoi), à faire valider par le Data Owner.


# %% US-27 · Gold : tables certifiables, quarantaine de la porte G, vue du client actif
DDL_GOLD = [
 """CREATE TABLE IF NOT EXISTS gold.contrat_certifie (
  contrat_id VARCHAR(12) PRIMARY KEY, cli_souscripteur CHAR(10) NOT NULL, cli_assure CHAR(10) NULL, code_type VARCHAR(10) NOT NULL,
  date_debut DATE NOT NULL, date_fin DATE NOT NULL, duree_garantie_mois INT NOT NULL, prime_annuelle DECIMAL(10,2), date_derniere_cotisation DATE,
  bronze_row_id BIGINT NOT NULL, silver_row_id BIGINT NOT NULL, _batch_id VARCHAR(20) NOT NULL, KEY idx_souscripteur (cli_souscripteur))""",
 """CREATE TABLE IF NOT EXISTS gold.sinistre_certifie (
  sinistre_id VARCHAR(12) PRIMARY KEY, contrat_id VARCHAR(12) NOT NULL, date_survenance DATE NOT NULL, date_declaration DATE, type_sinistre VARCHAR(40),
  montant_estime DECIMAL(12,2), adresse_normalisee VARCHAR(160), cp VARCHAR(10), ville_normalisee VARCHAR(80), canal_saisie VARCHAR(30),
  bronze_row_id BIGINT NOT NULL, silver_row_id BIGINT NOT NULL, _batch_id VARCHAR(20) NOT NULL, KEY idx_contrat (contrat_id))"""]
for ddl in DDL_GOLD:
    executer(ddl)
executer("DELETE FROM dq.rejets WHERE batch_id = :b AND porte = 'G'", b=BATCH)
for t in ["sinistre_certifie", "contrat_certifie", "xref_identifiants", "client_unique"]:          # xref référence client_unique : on la vide en premier
    executer(f"DELETE FROM gold.{t}")

def age_a(date, naissance):
    a = date.dt.year - naissance.dt.year
    avant_anniv = (date.dt.month < naissance.dt.month) | ((date.dt.month == naissance.dt.month) & (date.dt.day < naissance.dt.day))
    return a - avant_anniv.astype(int)

ct = lire("SELECT * FROM silver.contrat")
sn = lire("SELECT * FROM silver.sinistre")
types_connus = set(lire("SELECT code_type FROM silver.type_contrat").code_type)
for c in ["date_debut", "date_fin", "date_derniere_cotisation"]:
    ct[c] = pd.to_datetime(ct[c])
for c in ["date_declaration", "date_survenance"]:
    sn[c] = pd.to_datetime(sn[c])

# Contrats : seules les lignes qui franchissent les règles bloquantes de la porte G (RQ-011, 012, 013, 002)
crm = cl[cl.source_systeme == "crm"].set_index("source_id")
ct["cli_souscripteur"] = ct.souscripteur_id.map(crm.cli_id)
ct["cli_assure"] = ct.assure_id.map(crm.cli_id)
naiss = ct.souscripteur_id.map(crm.date_naissance)
mineur = naiss.notna() & (age_a(ct.date_debut, naiss.where(naiss.notna(), ct.date_debut)) < 18)
REGLES_G = {"RQ-011": (~ct.code_type.isin(types_connus), "type de contrat inconnu"),
            "RQ-012": (ct.cli_souscripteur.isna(), "souscripteur absent du client"),
            "RQ-013": (ct.assure_id.notna() & ct.cli_assure.isna(), "assuré absent du client (sentinelle 0 déjà remplacée par NULL)"),
            "RQ-002": (mineur, "souscripteur mineur à la date de début")}
rejets_g, ko = [], np.zeros(len(ct), dtype=bool)
for regle, (masque, motif) in REGLES_G.items():
    rejets_g.append(pd.DataFrame({"batch_id": BATCH, "entite": "contrat", "source_systeme": "crm", "bronze_row_id": ct[masque].bronze_row_id.astype(int).values,
                                  "rule_id": regle, "porte": "G", "motif": motif}))
    ko |= masque.values
gc = ct[~ko]
ecrire(pd.DataFrame({"contrat_id": gc.contrat_id, "cli_souscripteur": gc.cli_souscripteur, "cli_assure": gc.cli_assure, "code_type": gc.code_type,
                     "date_debut": gc.date_debut, "date_fin": gc.date_fin, "duree_garantie_mois": gc.duree_garantie_mois.astype(int),
                     "prime_annuelle": gc.prime_annuelle, "date_derniere_cotisation": gc.date_derniere_cotisation,
                     "bronze_row_id": gc.bronze_row_id, "silver_row_id": gc.silver_row_id, "_batch_id": BATCH}), "gold", "contrat_certifie")

# Sinistres : un sinistre dont le contrat n'est pas dans le gold, ou hors période de garantie, ne passe pas (RQ-017)
cc = gc.set_index("contrat_id")
sn["debut"], sn["fin"] = sn.contrat_id.map(cc.date_debut), sn.contrat_id.map(cc.date_fin)
sans_contrat = sn.debut.isna()
hors = (~sans_contrat) & ~((sn.date_survenance >= sn.debut) & (sn.date_survenance <= sn.fin))
for masque, motif in [(hors, "survenance hors période de garantie"), (sans_contrat, "contrat absent du gold (rejeté en amont)")]:
    rejets_g.append(pd.DataFrame({"batch_id": BATCH, "entite": "sinistre", "source_systeme": "crm", "bronze_row_id": sn[masque].bronze_row_id.astype(int).values,
                                  "rule_id": "RQ-017", "porte": "G", "motif": motif}))
gs = sn[~(sans_contrat | hors)]
ecrire(pd.DataFrame({"sinistre_id": gs.sinistre_id, "contrat_id": gs.contrat_id, "date_survenance": gs.date_survenance, "date_declaration": gs.date_declaration,
                     "type_sinistre": gs.type_sinistre, "montant_estime": gs.montant_estime, "adresse_normalisee": gs.adresse_normalisee, "cp": gs.cp,
                     "ville_normalisee": gs.ville_normalisee, "canal_saisie": gs.canal_saisie, "bronze_row_id": gs.bronze_row_id,
                     "silver_row_id": gs.silver_row_id, "_batch_id": BATCH}), "gold", "sinistre_certifie")
ecrire(pd.concat(rejets_g, ignore_index=True), "dq", "rejets")

# Statut du client, dérivé des contrats certifiés (fiche CD-001 : contrat en cours à la date de référence ET cotisation depuis COTISATION_MIN)
ref, cot = pd.Timestamp(DATE_REF), pd.Timestamp(COTISATION_MIN)
en_cours = (gc.date_debut <= ref) & (gc.date_fin >= ref) & (gc.date_derniere_cotisation >= cot)
actifs, souscripteurs, assures = set(gc[en_cours].cli_souscripteur), set(gc.cli_souscripteur), set(gc.cli_assure.dropna())
GR["statut_client"] = ["ACTIF" if c in actifs else "INACTIF" if c in souscripteurs else "ASSURE" if c in assures else "PROSPECT" for c in GR.cli_id]
GR["_batch_id"] = BATCH
ecrire(GR, "gold", "client_unique")
ecrire(cl[["cli_id", "source_systeme", "source_id", "bronze_row_id", "silver_row_id"]], "gold", "xref_identifiants")
executer("CREATE OR REPLACE VIEW gold.v_client_actif AS SELECT COUNT(*) AS nb_clients_actifs FROM gold.client_unique WHERE statut_client = 'ACTIF'")
print({t: total(f"SELECT COUNT(*) FROM gold.{t}") for t in ["client_unique", "xref_identifiants", "contrat_certifie", "sinistre_certifie"]})
print("Statuts :", GR.statut_client.value_counts().to_dict())
print(lire("SELECT entite, rule_id, COUNT(*) AS lignes FROM dq.rejets WHERE batch_id = :b AND porte = 'G' GROUP BY entite, rule_id ORDER BY entite, rule_id", b=BATCH).to_string(index=False))
print("Client actif (vue gold.v_client_actif, la même pour les trois directions) :", total("SELECT nb_clients_actifs FROM gold.v_client_actif"))


# %% US-27 (suite) · Mesurer les règles sur gold (porte G), historisé dans dq.dq_history (couche GOLD)
MESURES_GOLD = {
 "RQ-001": [("contrat_certifie", "SELECT COUNT(*), COALESCE(SUM(date_fin <= date_debut), 0) FROM gold.contrat_certifie")],
 "RQ-002": [("contrat_certifie", """SELECT COUNT(*), COALESCE(SUM(k.date_naissance IS NOT NULL AND TIMESTAMPDIFF(YEAR, k.date_naissance, c.date_debut) < 18), 0)
              FROM gold.contrat_certifie c LEFT JOIN gold.client_unique k ON k.cli_id = c.cli_souscripteur""")],
 "RQ-003": [("client_unique", "SELECT COUNT(*), COALESCE(SUM(telephone IS NULL), 0) FROM gold.client_unique WHERE statut_client IN ('ACTIF', 'INACTIF')")],
 "RQ-005": [("client_unique", "SELECT COUNT(*), COALESCE(SUM(cp IS NULL OR cp NOT REGEXP '^[0-9]{5}$'), 0) FROM gold.client_unique WHERE pays_iso = 'FR'")],
 "RQ-007": [("client_unique", "SELECT COUNT(*), COALESCE(SUM(pays_iso IS NULL OR pays_iso NOT IN (SELECT code_pays FROM silver.ref_pays)), 0) FROM gold.client_unique")],
 "RQ-010": [("contrat_certifie", "SELECT COUNT(*), COALESCE(SUM(duree_garantie_mois NOT IN (12, 24, 36, 60)), 0) FROM gold.contrat_certifie")],
 "RQ-011": [("contrat_certifie", "SELECT COUNT(*), COALESCE(SUM(code_type NOT IN (SELECT code_type FROM silver.type_contrat)), 0) FROM gold.contrat_certifie")],
 "RQ-012": [("contrat_certifie", "SELECT COUNT(*), COALESCE(SUM(cli_souscripteur NOT IN (SELECT cli_id FROM gold.client_unique)), 0) FROM gold.contrat_certifie")],
 "RQ-013": [("contrat_certifie", "SELECT COUNT(*), COALESCE(SUM(cli_assure IS NOT NULL AND cli_assure NOT IN (SELECT cli_id FROM gold.client_unique)), 0) FROM gold.contrat_certifie")],
 "RQ-015": [("client_unique", "SELECT COUNT(*), COALESCE(SUM(statut_client = 'PROSPECT' AND cli_id IN (SELECT cli_souscripteur FROM gold.contrat_certifie)), 0) FROM gold.client_unique")],
 "RQ-017": [("sinistre_certifie", """SELECT COUNT(*), COALESCE(SUM(NOT (s.date_survenance BETWEEN c.date_debut AND c.date_fin)), 0)
              FROM gold.sinistre_certifie s JOIN gold.contrat_certifie c ON c.contrat_id = s.contrat_id""")],
 "RQ-018": [("client_unique", f"""SELECT COUNT(*), COALESCE(SUM((u.statut_client = 'ACTIF') <> (a.cli IS NOT NULL)), 0)
              FROM gold.client_unique u LEFT JOIN (SELECT DISTINCT cli_souscripteur AS cli FROM gold.contrat_certifie
                   WHERE date_debut <= '{DATE_REF}' AND date_fin >= '{DATE_REF}' AND date_derniere_cotisation >= '{COTISATION_MIN}') a ON a.cli = u.cli_id""")],
 "RQ-019": [("client_unique", """SELECT COUNT(*), COALESCE(SUM(EXISTS (SELECT 1 FROM gold.client_unique b WHERE b.cli_id <> a.cli_id AND b.nom_reference = a.nom_reference
                     AND b.cp <=> a.cp AND b.date_naissance <=> a.date_naissance AND (b.telephone = a.telephone OR b.email = a.email))), 0) FROM gold.client_unique a""")],
 "RQ-020": [("client_unique", "SELECT COUNT(*), COUNT(*) - COUNT(DISTINCT cli_id) FROM gold.client_unique"),
            ("contrat_certifie", "SELECT COUNT(*), COUNT(*) - COUNT(DISTINCT contrat_id) FROM gold.contrat_certifie"),
            ("sinistre_certifie", "SELECT COUNT(*), COUNT(*) - COUNT(DISTINCT sinistre_id) FROM gold.sinistre_certifie")],
 "RQ-023": [("xref_identifiants", "SELECT COUNT(*), COALESCE(SUM(NOT EXISTS (SELECT 1 FROM silver.client s WHERE s.silver_row_id = x.silver_row_id AND s.bronze_row_id = x.bronze_row_id AND s.source_systeme = x.source_systeme)), 0) FROM gold.xref_identifiants x"),
            ("contrat_certifie", "SELECT COUNT(*), COALESCE(SUM(NOT EXISTS (SELECT 1 FROM bronze.crm_contrat b WHERE b.bronze_row_id = g.bronze_row_id)), 0) FROM gold.contrat_certifie g"),
            ("sinistre_certifie", "SELECT COUNT(*), COALESCE(SUM(NOT EXISTS (SELECT 1 FROM bronze.crm_sinistre b WHERE b.bronze_row_id = g.bronze_row_id)), 0) FROM gold.sinistre_certifie g")]}
executer("DELETE FROM dq.dq_history WHERE batch_id = :b AND couche = 'GOLD'", b=BATCH)
for rule_id, liste in MESURES_GOLD.items():
    for table, requete in liste:
        n, e = lire(requete).iloc[0]
        mesurer("GOLD", rule_id, table, n, e)
# Contrôle Soda de l'unicité du CLI sur gold (RQ-019), source de données gold
code, ctl = soda_scan("gold", f"{SODA}/checks/client_unique_checks.yml")
print("Soda sur gold (client_unique_checks.yml) : code retour", code, CODES_RETOUR[code], [(c["controle"], c["resultat"]) for c in ctl])
g = lire("""SELECT m.rule_id, m.table_cible, m.nb_testees, m.nb_echecs, m.taux_conformite, r.severite, r.seuil_min
            FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id) WHERE m.batch_id = :b AND m.couche = 'GOLD' ORDER BY m.rule_id, m.table_cible""", b=BATCH)
g["verdict"] = np.where(g.taux_conformite.astype(float) >= g.seuil_min.astype(float), "conforme", "SOUS LE SEUIL")
print(g.to_string(index=False))
print("Règles bloquantes sous le seuil sur gold :", g[(g.severite == "BLOQUANTE") & (g.verdict != "conforme")].rule_id.tolist() or "aucune : la porte G est franchie")


# %% US-28 · Retracer une donnée de gold jusqu'à la source (trois cas)
# Chaîne : gold.client_unique (cli_id) -> gold.xref_identifiants -> silver.client (silver_row_id) -> bronze.* (bronze_row_id, lot) -> source (identifiant source).
print("Cas 1 · la Société Meunier :", cli_meunier)
print(lire("""SELECT g.cli_id, g.nom_reference, x.source_systeme, x.source_id, x.silver_row_id, x.bronze_row_id, COALESCE(b._batch_id, c._batch_id) AS lot,
       CASE x.source_systeme WHEN 'crm' THEN b.raison_sociale ELSE c.column1 END AS valeur_en_bronze
    FROM gold.client_unique g JOIN gold.xref_identifiants x ON x.cli_id = g.cli_id
    LEFT JOIN bronze.crm_client b ON x.source_systeme = 'crm' AND b.bronze_row_id = x.bronze_row_id
    LEFT JOIN bronze.cif_clients c ON x.source_systeme = 'cif' AND c.bronze_row_id = x.bronze_row_id
    WHERE g.cli_id = :cli ORDER BY x.source_systeme, x.source_id""", cli=cli_meunier).to_string(index=False))
print("\nCas 2 · un code postal dont le zéro initial a été restauré (ligne silver marquée A_SURVEILLER) :")
print(lire("""SELECT x.cli_id, s.source_id, s.cp AS cp_silver, b.cp AS cp_bronze, s.statut_qualite, s.bronze_row_id, b._batch_id
    FROM silver.client s JOIN bronze.crm_client b ON b.bronze_row_id = s.bronze_row_id
    JOIN gold.xref_identifiants x ON x.source_systeme = s.source_systeme AND x.silver_row_id = s.silver_row_id
    WHERE s.source_systeme = 'crm' AND s.statut_qualite = 'A_SURVEILLER' LIMIT 5""").to_string(index=False))
print("\nCas 3 · une adresse de sinistre : gold.sinistre_certifie -> bronze.crm_sinistre -> crm.sinistre (source) :")
print(lire("""SELECT g.sinistre_id, g.adresse_normalisee AS adresse_gold, b.adresse_sinistre AS adresse_bronze, g.silver_row_id, g.bronze_row_id, b._batch_id, s.adresse_sinistre AS adresse_source
    FROM gold.sinistre_certifie g JOIN bronze.crm_sinistre b ON b.bronze_row_id = g.bronze_row_id JOIN crm.sinistre s ON s.sinistre_id = g.sinistre_id
    WHERE g.adresse_normalisee <> UPPER(b.adresse_sinistre) LIMIT 5""").to_string(index=False))
# À vous : la chaîne documentée pour chaque cas, avec identifiants de ligne et de lot, dans livrables/S4_silver_gold.md.


# %% US-26 (Should) · Corriger les adresses de sinistre avec l'extrait local de la BAN (RQ-014)
from rapidfuzz import fuzz
import unicodedata
def maj_pd(s):
    return (s.astype("string").str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii").str.upper()
             .str.replace(r"\s+", " ", regex=True).str.strip())
ban = lire("SELECT numero, voie, code_postal AS cp, commune AS ville FROM silver.ref_ban")
ban["numero"], ban["voie"], ban["ville"] = ban.numero.astype(str), maj_pd(ban.voie), maj_pd(ban.ville)
adr = lire("SELECT silver_row_id, sinistre_id, canal_saisie, cp, ville_normalisee AS ville, adresse_normalisee FROM silver.sinistre")
adr["numero"] = adr.adresse_normalisee.str.extract(r"^(\d+)")[0]
adr["voie"] = adr.adresse_normalisee.str.replace(r"^\d+\s+", "", regex=True).str.strip()

# 26.1 Taux d'erreur AVANT correction : une adresse est reconnue si (code postal, commune, numéro, voie) existe dans la BAN
cles_ban = set(zip(ban.cp, ban.ville, ban.numero, ban.voie))
adr["reconnue"] = [(a, b, c, d) in cles_ban for a, b, c, d in zip(adr.cp, adr.ville, adr.numero, adr.voie)]
avant_ban = 100 * (~adr.reconnue).mean()
print(f"Taux d'erreur avant correction : {avant_ban:.2f} %")
print(adr.groupby("canal_saisie").agg(sinistres=("reconnue", "size"), non_reconnues=("reconnue", lambda x: int((~x).sum()))))      # le Pareto : la ressaisie manuelle domine

# 26.2 Correction proposée : même code postal, même commune, même numéro, voie ressemblante ; corrigeable seulement s'il n'y a qu'un candidat
voies = ban.groupby(["cp", "ville", "numero"]).voie.apply(list).to_dict()
def corriger(ligne):
    candidats_ban = [v for v in voies.get((ligne.cp, ligne.ville, ligne.numero), []) if fuzz.ratio(ligne.voie, v) >= 75]
    return candidats_ban[0] if len(candidats_ban) == 1 else None
a_corriger = adr[~adr.reconnue].copy()
a_corriger["voie_ban"] = a_corriger.apply(corriger, axis=1)
corrigees = a_corriger.voie_ban.notna().sum()
exemples = a_corriger[a_corriger.voie_ban.notna()][["sinistre_id", "canal_saisie", "voie", "voie_ban"]]
print(exemples.sample(min(8, len(exemples)), random_state=1).to_string(index=False))      # à relire : la correction est-elle juste ?

# 26.3 Taux d'erreur APRÈS correction : les adresses sans candidat unique restent en erreur (quarantaine ou revue d'un Data Steward)
apres_ban = 100 * ((~adr.reconnue).sum() - corrigees) / len(adr)
print(f"Taux d'erreur après correction : {apres_ban:.2f} % ({corrigees} adresses corrigées sur {int((~adr.reconnue).sum())} non reconnues)")

# 26.4 Que reste-t-il, et pourquoi ? Chaque adresse non corrigée est classée par cause
couples = set(zip(ban.cp, ban.ville))
def cause(ligne):
    if pd.isna(ligne.numero):
        return "pas de numéro dans l'adresse saisie"
    if (ligne.cp, ligne.ville) not in couples:
        return "couple code postal / commune absent de la BAN"
    if (ligne.cp, ligne.ville, ligne.numero) not in voies:
        return "numéro absent de la BAN pour ce code postal et cette commune"
    candidats_ban = [v for v in voies[(ligne.cp, ligne.ville, ligne.numero)] if fuzz.ratio(ligne.voie, v) >= 75]
    return "voie corrigée (un seul candidat)" if len(candidats_ban) == 1 else "aucun ou plusieurs candidats"
print(a_corriger.apply(cause, axis=1).value_counts().to_string())
# À vous : argumenter l'écart entre le taux obtenu et la cible de 2 % : la BAN seule ne permet pas de retrouver ces adresses (numéro absent, commune ou code postal incohérent).
