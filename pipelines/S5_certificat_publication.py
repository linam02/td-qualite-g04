# -*- coding: utf-8 -*-
# ==============================================================================
# S5 : certifier, publier vers le CRM, gouverner     (US-29 à US-35, en Python)
# Outils : pandas, matplotlib, hashlib (SHA-256), SQLAlchemy. La décision du certificat reprend la requête SQL de l'onglet Médaillon ;
# la publication reprend le script pipelines/05_publish_to_crm.py de ce même onglet (trois refus, chargement en une transaction, RQ-025).
# Prérequis : S1 à S4 terminées (bronze, silver, gold construites et mesurées). Lancez le fichier entier : python pipelines/S5_certificat_publication.py
# ou copiez les cellules « # %% » dans votre notebook S5_<groupe>.ipynb. Les décisions s'écrivent dans livrables/S5_certificat_publication.md et livrables/DOSSIER_GO_NOGO.md.
# Les épreuves de refus ne modifient jamais le gold de façon durable : la ligne touchée est restaurée dans un bloc try/finally.
# ==============================================================================

# %% Paramètres, connexion
import sys, os, json, warnings
sys.path.append("../pipelines")
from aq import *
import numpy as np
import matplotlib
matplotlib.use("Agg")                          # tracé dans un fichier (pas de fenêtre) ; dans Jupyter, retirer cette ligne pour voir le graphique en ligne
import matplotlib.pyplot as plt
warnings.filterwarnings("ignore")
os.makedirs(f"{RACINE}/reports", exist_ok=True)
COUCHES = ["BRONZE", "SILVER", "GOLD", "CRM"]
COUCHE_DE_PORTE = {"B": "BRONZE", "S": "SILVER", "G": "GOLD", "C": "CRM"}


# %% US-29 · L'historique des mesures : une mesure par règle et par couche (bronze, silver, gold)
# dq.dq_history est alimentée par S1 (porte B), S2 et S3 (état initial sur bronze) et S4 (silver et gold) ; cette cellule les met côte à côte.
# Quand une règle porte sur plusieurs tables, on affiche le pire taux de la couche.
H = lire("""SELECT m.rule_id, r.dimension, r.severite, r.porte, m.couche, m.table_cible, m.taux_conformite AS taux
            FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id) WHERE m.batch_id = :b""", b=BATCH)
H["taux"] = H.taux.astype(float)
historique = (H.pivot_table(index=["rule_id", "dimension", "severite", "porte"], columns="couche", values="taux", aggfunc="min")
               .reindex(columns=COUCHES).reset_index())
print(historique.to_string(index=False))

# Complétude de l'historique : une règle sans mesure à la couche de sa porte est un trou (la porte C n'a de mesure qu'après la publication, US-32)
regles = lire("SELECT rule_id, porte, severite FROM dq.regle ORDER BY rule_id")
regles["couche_attendue"] = regles.porte.map(COUCHE_DE_PORTE)
mesurees = set(zip(H.rule_id, H.couche))
regles["mesures"] = [int((r, c) in mesurees) for r, c in zip(regles.rule_id, regles.couche_attendue)]
print("\nRègles sans mesure à la couche de leur porte :", regles[(regles.mesures == 0) & (regles.porte != "C")][["rule_id", "porte", "severite"]].values.tolist())
# Les règles RQ-004, RQ-006, RQ-008 et RQ-014 relèvent des extensions (US-20, US-26) : leur absence est à expliquer dans le dossier, pas à masquer.


# %% US-30 · Évolution de la qualité : une courbe par dimension, d'une couche à l'autre
K = lire("SELECT dimension, couche, taux_moyen FROM dq.dq_kpi_dimension WHERE batch_id = :b", b=BATCH)
K["taux_moyen"] = K.taux_moyen.astype(float)
courbe = K.pivot(index="dimension", columns="couche", values="taux_moyen").reindex(columns=["BRONZE", "SILVER", "GOLD"])
print(courbe.round(2).to_string())

fig, ax = plt.subplots(figsize=(9, 5))
for dimension, ligne in courbe.iterrows():
    ax.plot(ligne.index, ligne.values, marker="o", label=dimension)
ax.axhline(98, color="grey", linestyle="--", linewidth=1)
ax.text(0.02, 98.1, "seuil des règles d'avertissement (98 %)", fontsize=8, color="grey")
ax.set_ylabel("taux de conformité moyen (%)"); ax.set_title(f"Qualité par dimension et par couche, lot {BATCH}")
ax.legend(fontsize=8, ncol=2, loc="lower right"); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(f"{RACINE}/reports/courbe_qualite.png", dpi=130); plt.close(fig)
print("Courbe enregistrée :", f"{RACINE}/reports/courbe_qualite.png")

# Courbe « plate tant que rien ne change » : toutes les mesures historisées, regroupées par instant de mesure
dans_le_temps = lire("""SELECT DATE_FORMAT(h.mesure_le, '%Y-%m-%d %H:%i') AS instant, h.couche, ROUND(AVG(h.taux_conformite), 2) AS taux_moyen
                        FROM dq.dq_history h WHERE h.batch_id = :b GROUP BY instant, h.couche ORDER BY h.couche, instant""", b=BATCH)
print(dans_le_temps.groupby("couche").taux_moyen.agg(["count", "min", "max"]))
# À vous : un paragraphe lisible par un non-technicien, sous la courbe, dans livrables/S5_certificat_publication.md ; relancez une mesure sans rien changer pour obtenir la courbe plate.


# %% US-31 · Le certificat de qualité : décision par requête, empreinte SHA-256 du gold
DECISION = """
SELECT IF(SUM(m.taux_conformite < r.seuil_min) = 0, 'GO', 'NO_GO') AS decision,
       COUNT(*) AS nb_testees, COALESCE(SUM(m.taux_conformite >= r.seuil_min), 0) AS nb_ok
FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id)
WHERE m.batch_id = :lot AND r.severite = 'BLOQUANTE' AND r.porte IN ('B', 'S', 'G')
  AND m.couche = ELT(FIELD(r.porte, 'B', 'S', 'G'), 'BRONZE', 'SILVER', 'GOLD')"""
EN_ECHEC = """
SELECT m.rule_id, m.table_cible, m.taux_conformite, r.seuil_min
FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id)
WHERE m.batch_id = :lot AND r.severite = 'BLOQUANTE' AND r.porte IN ('B', 'S', 'G')
  AND m.couche = ELT(FIELD(r.porte, 'B', 'S', 'G'), 'BRONZE', 'SILVER', 'GOLD') AND m.taux_conformite < r.seuil_min"""

def emettre(lot, signataire="Data Owner"):
    """GO si toutes les règles BLOQUANTES des portes B, S et G sont conformes à leur seuil, mesurées sur la couche de LEUR porte.
    Le certificat est lié à l'état exact du gold par l'empreinte SHA-256 : si une ligne change après l'émission, il n'est plus valable."""
    d = lire(DECISION, lot=lot).iloc[0]
    ko = lire(EN_ECHEC, lot=lot)
    commentaire = "Aucune regle bloquante en echec" if d.decision == "GO" else "Regles en echec : " + ", ".join(f"{r.rule_id} ({r.table_cible})" for r in ko.itertuples())
    empreinte = empreinte_gold()
    executer("""INSERT INTO dq.certificat_qualite (certificat_id, batch_id, nb_bloquantes_testees, nb_bloquantes_ok, empreinte_gold, decision, signataire, commentaire)
                VALUES (:i, :b, :nt, :nok, :e, :d, :s, :c)
                ON DUPLICATE KEY UPDATE emis_le = NOW(), nb_bloquantes_testees = :nt, nb_bloquantes_ok = :nok, empreinte_gold = :e, decision = :d, signataire = :s, commentaire = :c""",
             i=f"CERT-{lot}", b=lot, nt=int(d.nb_testees), nok=int(d.nb_ok), e=empreinte, d=d.decision, s=signataire, c=commentaire[:500])
    return ko

ko = emettre(BATCH)
print(lire("SELECT certificat_id, decision, nb_bloquantes_ok, nb_bloquantes_testees, LEFT(empreinte_gold, 16) AS empreinte_debut, signataire, commentaire FROM dq.certificat_qualite WHERE batch_id = :b", b=BATCH).to_string(index=False))
print("Mesures bloquantes sous leur seuil :", ko.rule_id.tolist() or "aucune")

# Épreuve : un lot volontairement dégradé produit NO_GO. On clone les mesures du lot sous un autre identifiant (L-TEST) en dégradant une règle bloquante ;
# rien n'est modifié dans le lot réel.
executer("DELETE FROM dq.dq_history WHERE batch_id = 'L-TEST'")
executer("""INSERT INTO dq.dq_history (batch_id, couche, rule_id, table_cible, nb_testees, nb_echecs)
            SELECT 'L-TEST', couche, rule_id, table_cible, nb_testees, IF(rule_id = 'RQ-012', 10, nb_echecs) FROM dq.v_derniere_mesure WHERE batch_id = :b""", b=BATCH)
emettre("L-TEST")
print(lire("SELECT certificat_id, decision, nb_bloquantes_ok, nb_bloquantes_testees, commentaire FROM dq.certificat_qualite WHERE batch_id = 'L-TEST'").to_string(index=False))


# %% US-32 · Publier vers le CRM cible : refus sans certificat valide, chargement en une transaction, réconciliation (RQ-025)
CIBLE = {"client_unique": "client", "contrat_certifie": "contrat", "sinistre_certifie": "sinistre"}

class Refus(Exception):
    pass

def colonnes(table, techniques=False):
    cols = lire("SELECT column_name AS c FROM information_schema.columns WHERE table_schema = 'gold' AND table_name = :t ORDER BY ordinal_position", t=table).c.tolist()
    return cols if techniques else [c for c in cols if not c.startswith("_")]

def publier(certificat_id):
    """Trois refus : aucun certificat, décision NO_GO, empreinte différente. Le chargement se fait en une seule transaction : tout ou rien."""
    cert = lire("SELECT certificat_id, decision, empreinte_gold FROM dq.certificat_qualite WHERE certificat_id = :i", i=certificat_id)
    if cert.empty:
        raise Refus("REFUS : aucun certificat de qualité")
    cert = cert.iloc[0]
    if cert.decision != "GO":
        raise Refus(f"REFUS : décision {cert.decision} sur {cert.certificat_id}")
    if cert.empreinte_gold != empreinte_gold():
        raise Refus("REFUS : le gold a changé depuis l'émission du certificat")
    for t, cible in CIBLE.items():                                       # la structure d'abord (un DDL valide la transaction en cours)
        executer(f"CREATE TABLE IF NOT EXISTS crm_cible.{cible} LIKE gold.{t}")
    with eng().begin() as cx:                                            # chargement : une seule transaction, rien de partiel
        for t, cible in CIBLE.items():
            cols = ", ".join(colonnes(t, techniques=True))
            cx.execute(text(f"DELETE FROM crm_cible.{cible}"))
            cx.execute(text(f"INSERT INTO crm_cible.{cible} ({cols}) SELECT {cols} FROM gold.{t}"))
    for t, cible in CIBLE.items():                                       # RQ-025 : même comptage et même somme de contrôle, gold contre crm_cible (couche CRM)
        crc = "SUM(CRC32(CONCAT_WS('|', " + ", ".join(colonnes(t)) + ")))"
        g = lire(f"SELECT COUNT(*) AS n, COALESCE({crc}, 0) AS crc FROM gold.{t}").iloc[0]
        c = lire(f"SELECT COUNT(*) AS n, COALESCE({crc}, 0) AS crc FROM crm_cible.{cible}").iloc[0]
        mesurer("CRM", "RQ-025", cible, g.n, abs(int(g.n) - int(c.n)) + (1 if g.crc != c.crc else 0))
    return f"PUBLIÉ : {cert.certificat_id}"

def essayer(libelle, certificat_id):
    try:
        print(f"{libelle:<34} -> {publier(certificat_id)}")
    except Refus as r:
        print(f"{libelle:<34} -> {r}")

essayer("Refus 1 · certificat absent", "CERT-INEXISTANT")
essayer("Refus 2 · décision NO_GO", "CERT-L-TEST")
cli = lire("SELECT cli_id, telephone FROM gold.client_unique ORDER BY cli_id LIMIT 1").iloc[0]
executer("UPDATE gold.client_unique SET telephone = '0000000000' WHERE cli_id = :c", c=cli.cli_id)          # une ligne du gold change après l'émission...
try:
    essayer("Refus 3 · empreinte différente", f"CERT-{BATCH}")
finally:
    executer("UPDATE gold.client_unique SET telephone = :t WHERE cli_id = :c", t=None if pd.isna(cli.telephone) else cli.telephone, c=cli.cli_id)      # ... puis elle est restaurée
essayer("Publication du lot certifié", f"CERT-{BATCH}")
print(lire("SELECT rule_id, table_cible, nb_testees, nb_echecs, taux_conformite FROM dq.dq_history WHERE batch_id = :b AND couche = 'CRM' ORDER BY table_cible", b=BATCH).to_string(index=False))
essayer("Republication (idempotente)", f"CERT-{BATCH}")
# Nettoyage de l'épreuve de S5 · US-31 : le lot L-TEST n'existe que pour démontrer le refus 2
executer("DELETE FROM dq.dq_history WHERE batch_id = 'L-TEST'")
executer("DELETE FROM dq.certificat_qualite WHERE batch_id = 'L-TEST'")


# %% US-34 · Catalogue : propriétaire, steward, définition et lineage (option A de l'onglet Gouvernance, priorité Should)
from sqlalchemy import inspect
COUCHES_CATALOGUE = {"cif": "source", "crm": "source", "bronze": "bronze", "silver": "silver", "gold": "gold", "dq": "qualité"}
inspecteur = inspect(eng())
catalogue = {"tables": [], "glossary": [], "lineage": []}
for schema, couche in COUCHES_CATALOGUE.items():
    for nom in inspecteur.get_table_names(schema=schema):
        catalogue["tables"].append({"name": f"{schema}.{nom}", "couche": couche, "columns": [c["name"] for c in inspecteur.get_columns(nom, schema=schema)],
                                    "owner": "Claire Dumontier" if nom.endswith("client") or nom == "client_unique" else "Yanis Belkacem", "steward": "Yanis Belkacem"})
catalogue["glossary"].append({"term": "Client actif", "definition": "Contrat en cours ET à jour de cotisation sur 3 mois glissants (fiche CD-001)",
                              "owner": "Claire Dumontier", "validated": "2026-04-01"})
catalogue["lineage"] = [
    {"from": "crm.client",           "to": "bronze.crm_client",     "via": "ingestion (porte B, RQ-021)"},
    {"from": "cif.clients",          "to": "bronze.cif_clients",    "via": "ingestion (porte B, RQ-021)"},
    {"from": "crm.contrat",          "to": "bronze.crm_contrat",    "via": "ingestion (porte B, RQ-021)"},
    {"from": "crm.sinistre",         "to": "bronze.crm_sinistre",   "via": "ingestion (porte B, RQ-021)"},
    {"from": "bronze.crm_client",    "to": "silver.client",         "via": "standardisation et quarantaine (porte S)"},
    {"from": "bronze.cif_clients",   "to": "silver.client",         "via": "standardisation et quarantaine (porte S)"},
    {"from": "bronze.crm_contrat",   "to": "silver.contrat",        "via": "standardisation et quarantaine (porte S)"},
    {"from": "bronze.crm_sinistre",  "to": "silver.sinistre",       "via": "standardisation (porte S)"},
    {"from": "silver.client",        "to": "gold.client_unique",    "via": "dédoublonnage (porte G, RQ-019)"},
    {"from": "silver.client",        "to": "gold.xref_identifiants", "via": "traçabilité des identifiants (RQ-023)"},
    {"from": "silver.contrat",       "to": "gold.contrat_certifie", "via": "règles bloquantes de la porte G (RQ-011, 012, 013)"},
    {"from": "silver.sinistre",      "to": "gold.sinistre_certifie", "via": "règle RQ-017"},
    {"from": "gold.client_unique",   "to": "crm_cible.client",      "via": "publication sous certificat (RQ-025)"}]
os.makedirs(f"{RACINE}/catalogue", exist_ok=True)
json.dump(catalogue, open(f"{RACINE}/catalogue/catalog.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"Catalogue généré : {len(catalogue['tables'])} tables documentées")

def remonter(table, niveau=1):
    """Lineage d'une table jusqu'aux sources : on remonte les liens « from -> to » tant qu'il y en a."""
    for lien in [l for l in catalogue["lineage"] if l["to"] == table]:
        print("  " * niveau + f"{table} <- {lien['from']}   [{lien['via']}]")
        remonter(lien["from"], niveau + 1)
remonter("gold.client_unique")
fiche = next(t for t in catalogue["tables"] if t["name"] == "gold.client_unique")
print({k: fiche[k] for k in ("name", "couche", "owner", "steward")}, "; colonnes :", len(fiche["columns"]))
print(lire("""SELECT m.rule_id, r.libelle, r.severite, m.couche, m.taux_conformite FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id)
              WHERE m.batch_id = :b AND m.table_cible = 'client_unique' ORDER BY m.rule_id""", b=BATCH).to_string(index=False))
# L'interface : streamlit run catalogue/app.py --server.port 8502 --server.address 0.0.0.0   (onglet Gouvernance). À vous : la définition en une phrase de gold.client_unique.


# %% US-33 · Planifier la chaîne quotidienne : le DAG se lit, l'échec bloquant se propage (priorité Could)
# Le DAG de l'onglet Orchestration s'exécute dans Airflow ; ici on en reproduit la logique, avec les portes comme barrières.
# executer=False : on affiche l'ordre des tâches et l'état actuel de chaque porte, sans rien relancer.
def porte_ouverte(porte):
    """Une porte est ouverte quand toutes ses règles bloquantes, mesurées sur sa couche, sont conformes à leur seuil."""
    ko = lire("""SELECT m.rule_id FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id)
                 WHERE m.batch_id = :b AND r.severite = 'BLOQUANTE' AND r.porte = :p AND m.couche = :c AND m.taux_conformite < r.seuil_min""", b=BATCH, p=porte, c=COUCHE_DE_PORTE[porte])
    return ko.empty, ko.rule_id.tolist()

CHAINE = [("ingest_bronze", "S1_bronze_profilage.py", None), ("porte_B", None, "B"),
          ("build_silver", "S4_silver_gold.py (cellules US-21 à US-23)", None), ("porte_S", None, "S"),
          ("build_gold", "S4_silver_gold.py (cellules US-24 à US-27)", None), ("porte_G", None, "G"),
          ("certifier", "S5_certificat_publication.py (US-31)", None), ("publier_crm", "S5_certificat_publication.py (US-32)", None)]
bloque = False
for tache, script, porte in CHAINE:
    if bloque:
        print(f"{tache:<14} non exécutée (échec bloquant en amont)")
        continue
    if porte:
        ok, regles_ko = porte_ouverte(porte)
        print(f"{tache:<14} porte {porte} : {'ouverte' if ok else 'FERMÉE ' + str(regles_ko)}")
        bloque = not ok
    else:
        print(f"{tache:<14} {script}")
# Dans Airflow : ingest_bronze >> porte_B >> build_silver >> porte_S >> build_gold >> porte_G >> certifier >> publier_crm  (une tâche en échec ferme toutes les suivantes)


# %% US-35 · Les éléments chiffrés du dossier go/no-go
# 35.1 Les seuils : par règle, sévérité et seuil de conformité
seuils = lire("SELECT rule_id, libelle, dimension, porte, severite, seuil_min FROM dq.regle ORDER BY rule_id")
print(seuils[["rule_id", "dimension", "porte", "severite", "seuil_min"]].to_string(index=False))

# 35.2 Les écarts à expliquer : mesures sous leur seuil, bloquantes d'abord
ecarts = lire("""SELECT m.rule_id, r.severite, m.couche, m.table_cible, m.nb_echecs, m.taux_conformite, r.seuil_min
                 FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id)
                 WHERE m.batch_id = :b AND m.taux_conformite < r.seuil_min ORDER BY FIELD(r.severite, 'BLOQUANTE', 'AVERTISSEMENT'), m.rule_id, m.couche""", b=BATCH)
print(ecarts.to_string(index=False))

# 35.3 Les anomalies résiduelles : lignes écartées en quarantaine, par porte, entité et règle ; avertissements restants sur le gold
quarantaine = lire("SELECT porte, entite, rule_id, COUNT(*) AS lignes_en_quarantaine FROM dq.rejets WHERE batch_id = :b GROUP BY porte, entite, rule_id ORDER BY porte, entite, rule_id", b=BATCH)
print(quarantaine.to_string(index=False))
avertissements = lire("""SELECT m.rule_id, r.libelle, m.nb_echecs, m.taux_conformite FROM dq.v_derniere_mesure m JOIN dq.regle r USING (rule_id)
                         WHERE m.batch_id = :b AND m.couche = 'GOLD' AND r.severite = 'AVERTISSEMENT' AND m.taux_conformite < r.seuil_min""", b=BATCH)
print(avertissements.to_string(index=False))

# 35.4 Le certificat à joindre, et la réconciliation finale
certificat = lire("SELECT * FROM dq.certificat_qualite WHERE batch_id = :b", b=BATCH)
reconciliation = lire("SELECT * FROM dq.dq_history WHERE batch_id = :b AND couche = 'CRM'", b=BATCH)
print(certificat.T.to_string(header=False))
print(reconciliation[["rule_id", "table_cible", "nb_testees", "nb_echecs", "taux_conformite"]].to_string(index=False))

# Export des chiffres pour le dossier (reports/go_nogo_*.csv)
for nom, df in [("seuils", seuils), ("ecarts", ecarts), ("quarantaine", quarantaine), ("historique", historique), ("reconciliation", reconciliation)]:
    df.to_csv(f"{RACINE}/reports/go_nogo_{nom}.csv", index=False)
# La décision, le commentaire et la signature du Data Owner s'écrivent dans livrables/DOSSIER_GO_NOGO.md.
