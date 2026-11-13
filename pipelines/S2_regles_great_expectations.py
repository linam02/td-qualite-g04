# -*- coding: utf-8 -*-
# ==============================================================================
# S2 : des règles métier en tests automatisés avec Great Expectations, état initial sur bronze     (US-10, 11, 13, 15, en Python)
# Outils : Great Expectations 0.18.19 (validateur pandas), pandas, SQLAlchemy. Ordre des cellules = rythme de la fiche S2 (onglet Séances).
# Prérequis : S1 terminée (bronze alimentée, porte B franchie). Lancez le fichier entier : python pipelines/S2_regles_great_expectations.py
# ou copiez les cellules « # %% » dans votre notebook S2_<groupe>.ipynb. Les observations et les décisions s'écrivent dans livrables/S2_regles_great_expectations.md.
# ==============================================================================

# %% Paramètres, connexion et chargement des données de la couche visée
import sys, os, warnings
sys.path.append("../pipelines")
from aq import *
import great_expectations as gx
warnings.filterwarnings("ignore")

COUCHE = os.environ.get("COUCHE", "BRONZE")        # BRONZE aujourd'hui ; SILVER en S4 (US-23, variable COUCHE=SILVER) : la même suite se relance sans modification, seules les requêtes de chargement changent
DOSSIER = "/home/jovyan/work/reports" if os.path.isdir("/home/jovyan/work/reports") else "reports"
os.makedirs(f"{DOSSIER}/ge", exist_ok=True)

# Les colonnes sont ramenées aux mêmes noms dans les deux couches (client_id, telephone, pays...) : une seule suite pour bronze et silver.
# `cle` est la clé primaire de la table (RQ-020) ; `source_systeme` permet de ne viser que les clients du CRM.
CHARGEMENT = {
 "BRONZE": {
  "crm_client":   ("client",   "SELECT client_id AS cle, client_id, 'crm' AS source_systeme, type_personne, telephone, cp, pays FROM bronze.crm_client WHERE _batch_id = :b"),
  "crm_contrat":  ("contrat",  "SELECT contrat_id AS cle, contrat_id, souscripteur_id, date_debut, date_fin, duree_garantie_mois FROM bronze.crm_contrat WHERE _batch_id = :b"),
  "crm_sinistre": ("sinistre", "SELECT sinistre_id AS cle, sinistre_id FROM bronze.crm_sinistre WHERE _batch_id = :b"),
  "cif_clients":  ("cif",      "SELECT column0 AS cle FROM bronze.cif_clients WHERE _batch_id = :b")},
 "SILVER": {
  "client":   ("client",   "SELECT CONCAT(source_systeme, '|', source_id) AS cle, source_id AS client_id, source_systeme, type_personne, telephone_normalise AS telephone, cp, pays_iso AS pays FROM silver.client"),
  "contrat":  ("contrat",  "SELECT contrat_id AS cle, contrat_id, souscripteur_id, date_debut, date_fin, duree_garantie_mois FROM silver.contrat WHERE :b = :b"),
  "sinistre": ("sinistre", "SELECT sinistre_id AS cle, sinistre_id FROM silver.sinistre WHERE :b = :b")}}
NAISSANCES = {"BRONZE": "SELECT client_id, date_naissance FROM bronze.crm_client WHERE _batch_id = :b",
              "SILVER": "SELECT source_id AS client_id, date_naissance FROM silver.client WHERE source_systeme = 'crm' AND :b = :b"}

def age_a(date, naissance):
    """Âge en années révolues à une date (même calcul que TIMESTAMPDIFF(YEAR, naissance, date) en SQL)."""
    a = date.dt.year - naissance.dt.year
    avant = (date.dt.month < naissance.dt.month) | ((date.dt.month == naissance.dt.month) & (date.dt.day < naissance.dt.day))
    return a - avant.astype(int)

def charger(table):
    nature, requete = CHARGEMENT[COUCHE][table]
    df = lire(requete, b=BATCH)
    if nature == "contrat":
        for c in ["date_debut", "date_fin"]:
            df[c] = pd.to_datetime(df[c], errors="coerce")                      # les dates arrivent en texte depuis bronze
        df["duree_garantie_mois"] = pd.to_numeric(df.duree_garantie_mois, errors="coerce")
        nais = lire(NAISSANCES[COUCHE], b=BATCH).drop_duplicates("client_id")
        nais["date_naissance"] = pd.to_datetime(nais.date_naissance, errors="coerce")
        df = df.merge(nais, how="left", left_on="souscripteur_id", right_on="client_id", suffixes=("", "_s"))
        df["age_debut"] = age_a(df.date_debut, df.date_naissance.fillna(df.date_debut))      # RQ-002 : âge à la date de début (US-13)
        df.loc[df.date_naissance.isna(), "age_debut"] = float("nan")
    return nature, df

DONNEES = {table: charger(table) for table in CHARGEMENT[COUCHE]}
for t, (nature, d) in DONNEES.items():
    print(f"{COUCHE.lower()}.{t:<13} {len(d):>7} lignes")
REGLES = lire("SELECT rule_id, severite, seuil_min FROM dq.regle").set_index("rule_id")      # la sévérité et le seuil viennent de dq.regle, pas du code
CODES_PAYS = lire("SELECT code_pays FROM silver.ref_pays").code_pays.tolist()
def mostly(rule_id):
    return float(REGLES.loc[rule_id, "seuil_min"]) / 100


# %% Great Expectations : le flux de base (contexte fichier, source, batch, suite, checkpoint, Data Docs)
# Le projet gx/ vit dans reports/ge : il est donc conservé hors du conteneur.
context = gx.get_context(mode="file", project_root_dir=f"{DOSSIER}/ge")
source = context.sources.add_or_update_pandas(name="mariadb_df")

def asset(nom):
    """Un actif par table : réutilisé si la cellule est relancée."""
    try:
        return source.get_asset(nom)
    except LookupError:
        return source.add_dataframe_asset(name=nom)

def valider(table, nature, df, ajouter):
    """Construit la suite d'une table (chaque expectation porte son rule_id), lance le checkpoint et rend les résultats expectation par expectation."""
    br = asset(table).build_batch_request(dataframe=df)
    suite = f"assurconnect_{COUCHE.lower()}_{table}_suite"
    context.add_or_update_expectation_suite(suite)
    v = context.get_validator(batch_request=br, expectation_suite_name=suite)
    ajouter(v)
    v.save_expectation_suite(discard_failed_expectations=False)
    cp = context.add_or_update_checkpoint(name=f"dq_{COUCHE.lower()}_{table}", validations=[{"batch_request": br, "expectation_suite_name": suite}])
    return list(cp.run().run_results.values())[0]["validation_result"].results


# %% US-10 · Des règles en tests automatisés : RQ-001, 002, 003, 005, 007, 009, 010 et 020 (chacune porte son identifiant RQ)
SOUSCRIPTEUR_CRM = dict(row_condition='source_systeme == "crm" and type_personne == "souscripteur"', condition_parser="pandas")
FRANCE_CRM       = dict(row_condition='source_systeme == "crm" and pays == "FR"', condition_parser="pandas")
CRM              = dict(row_condition='source_systeme == "crm"', condition_parser="pandas")

def regles_client(v):
    # RQ-003 : téléphone d'un souscripteur ni nul, ni vide, ni blanc : trois cas, deux expectations (les NULL sont ignorés par la seconde)
    v.expect_column_values_to_not_be_null(column="telephone", mostly=mostly("RQ-003"), meta={"rule_id": "RQ-003"}, **SOUSCRIPTEUR_CRM)
    v.expect_column_values_to_match_regex(column="telephone", regex=r"\S", mostly=mostly("RQ-003"), meta={"rule_id": "RQ-003"}, **SOUSCRIPTEUR_CRM)
    # RQ-005 : code postal à 5 chiffres, pour une adresse en France seulement (sinon : faux positifs sur les adresses étrangères)
    v.expect_column_values_to_match_regex(column="cp", regex=r"^\d{5}$", mostly=mostly("RQ-005"), meta={"rule_id": "RQ-005", "nuls_en_echec": True}, **FRANCE_CRM)
    # RQ-007 : pays dans la liste de référence (silver.ref_pays)
    v.expect_column_values_to_be_in_set(column="pays", value_set=CODES_PAYS, meta={"rule_id": "RQ-007", "nuls_en_echec": True}, **CRM)
    # RQ-009 : type de personne parmi les trois valeurs autorisées (minuscules, sans accent, comme dans la base)
    v.expect_column_values_to_be_in_set(column="type_personne", value_set=["prospect", "souscripteur", "assure"], meta={"rule_id": "RQ-009", "nuls_en_echec": True}, **CRM)

def regles_contrat(v):
    # RQ-001 : la date de fin est strictement postérieure à la date de début
    v.expect_column_pair_values_A_to_be_greater_than_B(column_A="date_fin", column_B="date_debut", or_equal=False, meta={"rule_id": "RQ-001"})
    # RQ-002 : le souscripteur a 18 ans ou plus à la date de DÉBUT du contrat (âge calculé dans charger() ; inconnu = non testable)
    v.expect_column_values_to_be_between(column="age_debut", min_value=18, meta={"rule_id": "RQ-002"})
    # RQ-010 : durée de garantie parmi 12, 24, 36, 60 (texte en bronze, converti en nombre au chargement)
    v.expect_column_values_to_be_in_set(column="duree_garantie_mois", value_set=[12, 24, 36, 60], meta={"rule_id": "RQ-010", "nuls_en_echec": True})

def cle_primaire(v):
    # RQ-020 : clé primaire jamais nulle et unique
    v.expect_column_values_to_not_be_null(column="cle", meta={"rule_id": "RQ-020"})
    v.expect_column_values_to_be_unique(column="cle", meta={"rule_id": "RQ-020"})

SUITES = {"client": [regles_client, cle_primaire], "contrat": [regles_contrat, cle_primaire], "sinistre": [cle_primaire], "cif": [cle_primaire]}

def tout_ajouter(nature):
    return lambda v: [f(v) for f in SUITES[nature]]

mesures_ge = []
for table, (nature, df) in DONNEES.items():
    resultats = valider(table, nature, df, tout_ajouter(nature))
    par_regle = {}
    for r in resultats:
        m = r.expectation_config.meta
        n, ko = r.result["element_count"], r.result["unexpected_count"] + (r.result.get("missing_count", 0) if m.get("nuls_en_echec") else 0)
        t0, k0 = par_regle.get(m["rule_id"], (n, 0))
        par_regle[m["rule_id"]] = (t0, k0 + ko)                      # plusieurs expectations pour une règle : on additionne les échecs
    for rule, (n, ko) in par_regle.items():
        mesures_ge.append({"rule_id": rule, "table": table, "testees": int(n), "echecs": int(ko)})
bilan = pd.DataFrame(mesures_ge).sort_values(["rule_id", "table"])
bilan["conformite_pct"] = (100 * (bilan.testees - bilan.echecs) / bilan.testees).round(3)
bilan["seuil_pct"] = [float(REGLES.loc[r, "seuil_min"]) for r in bilan.rule_id]
bilan["severite"] = [REGLES.loc[r, "severite"] for r in bilan.rule_id]
bilan["verdict"] = ["conforme" if c >= s else "sous le seuil" for c, s in zip(bilan.conformite_pct, bilan.seuil_pct)]
print(bilan.to_string(index=False))            # taux de réussite par règle ; RQ-005 : 1 456 écarts sur 95 437 lignes en France
context.build_data_docs()                      # rapport HTML : reports/ge/gx/uncommitted/data_docs/local_site/index.html (à relire comme un non-technicien)


# %% US-11 · Lire les lignes en échec de chaque règle
# Great Expectations rend les lignes fautives avec result_format COMPLETE ; unexpected_index_column_names ajoute l'identifiant de la ligne.
COMPLET = lambda ident: {"result_format": "COMPLETE", "unexpected_index_column_names": [ident]}

def lignes_en_echec(table, ident, expectation, **kwargs):
    """Rejoue une expectation en mode COMPLETE : rend les lignes fautives (identifiant + valeur)."""
    nature, df = DONNEES[table]
    context.add_or_update_expectation_suite("assurconnect_echecs")
    v = context.get_validator(batch_request=asset(f"echecs_{table}").build_batch_request(dataframe=df), expectation_suite_name="assurconnect_echecs")
    return getattr(v, expectation)(result_format=COMPLET(ident), **kwargs).result.get("unexpected_index_list", [])

echecs = []
if COUCHE == "BRONZE":
    t = "crm_client"
    for rule, colonne, motif_txt, exp, kw in [
        ("RQ-003", "telephone", "téléphone nul, vide ou blanc", "expect_column_values_to_not_be_null", SOUSCRIPTEUR_CRM),
        ("RQ-003", "telephone", "téléphone nul, vide ou blanc", "expect_column_values_to_match_regex", dict(regex=r"\S", **SOUSCRIPTEUR_CRM)),
        ("RQ-005", "cp", "code postal : pas 5 chiffres", "expect_column_values_to_match_regex", dict(regex=r"^\d{5}$", **FRANCE_CRM)),
        ("RQ-009", "type_personne", "type_personne hors domaine", "expect_column_values_to_be_in_set", dict(value_set=["prospect", "souscripteur", "assure"], **CRM))]:
        for ligne in lignes_en_echec(t, "client_id", exp, column=colonne, **kw):
            echecs.append({"rule_id": rule, "table": t, "id": ligne["client_id"], "valeur": ligne.get(colonne), "motif": motif_txt})
    t = "crm_contrat"
    for rule, colonne, motif_txt, exp, kw in [("RQ-010", "duree_garantie_mois", "durée de garantie hors liste", "expect_column_values_to_be_in_set", dict(value_set=[12, 24, 36, 60]))]:
        for ligne in lignes_en_echec(t, "contrat_id", exp, column=colonne, **kw):
            echecs.append({"rule_id": rule, "table": t, "id": ligne["contrat_id"], "valeur": ligne.get(colonne), "motif": motif_txt})
    # RQ-001 : lignes où date_fin <= date_debut
    for ligne in lignes_en_echec("crm_contrat", "contrat_id", "expect_column_pair_values_A_to_be_greater_than_B", column_A="date_fin", column_B="date_debut", or_equal=False):
        echecs.append({"rule_id": "RQ-001", "table": "crm_contrat", "id": ligne["contrat_id"], "valeur": f"{ligne.get('date_fin')} <= {ligne.get('date_debut')}", "motif": "date de fin non postérieure au début"})
if COUCHE == "BRONZE":                      # sur silver, la quarantaine a déjà écarté ces lignes : il n'y a plus de ligne en échec à lire
    echecs = pd.DataFrame(echecs)
    os.makedirs(f"{DOSSIER}/echecs", exist_ok=True)
    for rule, sous in echecs.groupby("rule_id"):
        sous.to_csv(f"{DOSSIER}/echecs/lignes_en_echec_{rule}.csv", index=False)               # export : identifiant, valeur, motif
    print(echecs.groupby(["rule_id", "table"]).size().rename("lignes_en_echec"))
    print("\nÉchantillon de 20 lignes à commenter (RQ-009) :\n", echecs[echecs.rule_id == "RQ-009"].sample(20, random_state=1).to_string(index=False))
    print("\nMotifs distincts de RQ-009, avec leur fréquence :\n", echecs[echecs.rule_id == "RQ-009"].valeur.value_counts())


# %% US-13 · L'âge se calcule à la date de début du contrat (RQ-002)
# Comparer la règle « à la date de début du contrat » à la règle « à la date de référence » (qui remplace ici la date du jour, pour un résultat stable).
if COUCHE == "BRONZE":
    nature, ct = DONNEES["crm_contrat"]
    c = ct[ct.age_debut.notna()].copy()
    ref = pd.Timestamp(DATE_REF)
    c["age_reference"] = age_a(pd.Series(ref, index=c.index), c.date_naissance)
    mineur_signature, mineur_reference = c.age_debut < 18, c.age_reference < 18
    print(f"contrats avec souscripteur connu : {len(c)} | mineurs à la signature : {int(mineur_signature.sum())} | "
          f"mineurs à la date de référence : {int(mineur_reference.sum())} | verdict qui change : {int((mineur_signature != mineur_reference).sum())}")
    print(c[mineur_signature != mineur_reference][["contrat_id", "souscripteur_id", "date_naissance", "date_debut", "age_debut", "age_reference"]].head(10).to_string(index=False))
    # À vous : documenter RQ-002 avec sa date de référence, et citer ces exemples.


# %% US-15 · État initial de la qualité sur bronze, historisé dans dq.dq_history
# Les mesures de la porte B (RQ-021, RQ-022) sont déjà écrites par S1 : on ne les touche pas. Rejouer remplace les mesures du lot (pas de doublon).
for m in mesures_ge:
    mesurer(COUCHE, m["rule_id"], m["table"], m["testees"], m["echecs"])
lecture = mesures(COUCHE)
lecture["verdict"] = ["conforme" if t >= s else "sous le seuil" for t, s in zip(lecture.taux_conformite.astype(float), lecture.seuil_min.astype(float))]
print(lecture.to_string(index=False))
print("\nSynthèse par dimension (moyenne des taux de la dernière mesure de chaque règle) :")
print(lire("SELECT dimension, taux_moyen FROM dq.dq_kpi_dimension WHERE batch_id = :b AND couche = :c ORDER BY taux_moyen", b=BATCH, c=COUCHE).to_string(index=False))
# À vous : la lecture commentée « voici la qualité de ce qui nous est livré », dans livrables/S2_regles_great_expectations.md.
# Les règles d'intégrité entre tables (RQ-011, 012, 013, 015, 016, 017) s'ajoutent à cet historique en S3, avec Soda Core.
