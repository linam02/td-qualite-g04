# S3 · Soda Core : intégrité entre tables, portes en SodaCL

Groupe : g04  ·  Date : 13/11/2026  ·  Rédacteur : Lina Merazga·  Étiquette : `seance-3`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

**Preuve commune** : `pipelines/S3_integrite_soda.py` (relançable de bout en bout : `docker exec -it dq_jupyter python pipelines/S3_integrite_soda.py`), lot `L-2026-10-01`, couche BRONZE. Rôles en S3 : Data Owner = Amadou Macka Diallo ; Data Steward, Ingénieur qualité, Rédacteur : [À COMPLÉTER].

## 1. Checks et configuration (US-12)

Fichiers (chemins) : configuration `soda/configuration.yml` (une source de données par couche : crm, bronze, silver, gold) ; checks client `soda/checks/client_checks.yml` ; contrat `soda/checks/contrat_checks.yml` ; sinistre `soda/checks/sinistre_checks.yml`. Les versions bronze (`soda/checks/bronze/*.yml`) sont générées par le script à partir des mêmes fichiers, en changeant seulement le nom des tables (`client` → `crm_client`…) ; contrôles d'intégrité ajoutés : `soda/checks/bronze/integrite_checks.yml`. Résultats JSON : `soda/reports/bronze_*.json`.

| Règle | Fichier de checks | Couche mesurée | Résultat Soda (PASSED, WARN, FAILED) | Valeur mesurée | Code retour du scan |
|---|---|---|---|---|---|
| RQ-003 téléphone du souscripteur | client_checks.yml | BRONZE | FAILED | 5 989 | 2 |
| RQ-005 code postal FR | client_checks.yml | BRONZE | FAILED | 1 456 | 2 |
| RQ-007 pays dans le référentiel | client_checks.yml | BRONZE | FAILED | 3 050 | 2 |
| RQ-009 type de personne | client_checks.yml | BRONZE | FAILED | 200 | 2 |
| RQ-015 prospect sans contrat | client_checks.yml | BRONZE | FAILED | 479 | 2 |
| RQ-020 clé client unique et renseignée | client_checks.yml | BRONZE | PASSED | 0 | 2 |
| RQ-001 date de fin > date de début | contrat_checks.yml | BRONZE | FAILED | 800 | 2 |
| RQ-010 durée de garantie | contrat_checks.yml | BRONZE | FAILED | 600 | 2 |
| RQ-011 type de contrat connu | contrat_checks.yml | BRONZE | FAILED | 200 | 2 |
| RQ-012 souscripteur existant | contrat_checks.yml | BRONZE | FAILED | 1 000 | 2 |
| RQ-013 assuré existant (sentinelle exclue) | contrat_checks.yml | BRONZE | FAILED | 300 | 2 |
| RQ-018 écart client actif (Commerciale − CD-001) | contrat_checks.yml | BRONZE | FAILED (seuil d'échec : > 5 000) | 11 878 | 2 |
| RQ-014 code postal de sinistre | sinistre_checks.yml | BRONZE | PASSED | 0 | 2 |
| RQ-014 taux d'adresses de sinistre absentes de la BAN | sinistre_checks.yml | BRONZE | FAILED (warn > 3 %, fail > 10 %) | 12,1 % | 2 |
| RQ-017 sinistre hors période de garantie | sinistre_checks.yml | BRONZE | FAILED | 1 200 | 2 |
| RQ-020 identifiant de sinistre unique | sinistre_checks.yml | BRONZE | PASSED | 0 | 2 |
| RQ-016 souscripteur sans contrat | integrite_checks.yml | BRONZE | WARN | 955 | 1 |
| Relation sinistre → contrat | integrite_checks.yml | BRONZE | PASSED | 0 | 1 |

Code retour de la porte (le plus élevé des quatre fichiers) : **2 (échec)**. Règles bloquantes en échec : RQ-001, 007, 009, 010, 011, 012, 013, 015, 017.

Un avertissement et un échec : à quelle condition le code retour du scan devient-il non nul ? Un fichier renvoie 0 si tous ses contrôles passent, 1 si au moins un contrôle est en avertissement (`warn`) et aucun en échec, 2 dès qu'un contrôle est en échec (`fail`), 3 en cas d'erreur d'exécution. Exemple mesuré : `integrite_checks.yml` ne contient qu'un avertissement (RQ-016, 955) et renvoie 1 ; `client_checks.yml` contient des échecs et renvoie 2. Dans un pipeline, l'étape se termine par `sys.exit(code_porte)` : tout code non nul arrête la suite. Un avertissement déclaré par `warn` suffit donc à rendre le code non nul : la sévérité d'une règle doit se traduire par `warn` (avertissement) ou `fail` (bloquante) dans le fichier de checks.

Les valeurs Soda sont-elles cohérentes avec celles de Great Expectations en S2 ? Écarts et explication : oui, sans aucun écart sur les six règles mesurées par les deux outils : RQ-001 800, RQ-003 5 989, RQ-005 1 456, RQ-007 3 050, RQ-009 200, RQ-010 600 (`livrables/S2_regles_great_expectations.md`, section 1). Même lot, même couche et mêmes définitions : la condition `TRIM(telephone) = ''` de Soda couvre le vide et le blanc, comme les deux expectations de GE ; le code postal est filtré sur `pays = 'FR'` dans les deux outils.

## 2. Bilan d'intégrité (US-16)

Aucune clé étrangère n'est déclarée dans la base : chaque relation est à vérifier.

| Relation | Lignes testées | Orphelins | Taux | Conclusion (anomalie, sentinelle, normal) |
|---|---|---|---|---|
| contrat.souscripteur_id vers client (RQ-012) | 100 000 | 1 000 | 1,00 % | Anomalie : identifiants absents de crm.client (ex. CT0000031 → H-97935, CT0000046 → S-97321), probablement des clients supprimés ou jamais migrés. Quarantaine en silver ; le contrat ne peut pas compter dans le client actif |
| contrat.assure_id vers client (RQ-013) | 60 000 (sentinelle `'0'` exclue) | 300 | 0,50 % | Anomalie réelle une fois la sentinelle écartée (voir section 3) : assurés inconnus, quarantaine en silver |
| contrat.code_type vers type_contrat (RQ-011) | 100 000 | 200 | 0,20 % | Anomalie : code absent du référentiel de 12 types (produit retiré ou non référencé). Quarantaine ; compléter le référentiel est une décision du Data Owner |
| sinistre.contrat_id vers contrat | 100 000 | 0 | 0,00 % | Normal : tout sinistre est rattaché à un contrat existant |
| client.pays vers ref_pays (RQ-007) | 100 000 | 3 050 | 3,05 % | Anomalie de saisie corrigeable : 3 000 variantes de la France ou valeurs vides (`France` 1 200, `F` 600, `fr` 400, `Frnace` 400, `''` 400, mesure S1) + 50 codes inconnus (`UK` 20…). Table de correspondance en silver |

## 3. Valeur sentinelle (US-17)

| Contrôle | Orphelins | Preuve |
|---|---|---|
| Sur `assure_id`, avant traitement de la sentinelle | 40 300 sur 100 000 (40,3 %) | `soda/checks/bronze/sentinelle_avant.yml`, généré et lancé par `pipelines/S3_integrite_soda.py` (cellule US-17) |
| Sur `assure_id`, après traitement | 300 (0,3 % des contrats ; 0,5 % des 60 000 contrats testés) | `soda/checks/contrat_checks.yml`, filtre `assure_renseigne` (`assure_id <> '0'`) |

Écart chiffré et convention écrite (comment la valeur sentinelle est traitée, par qui, dans quelle couche) : l'écart est de 40 000 orphelins, exactement le nombre de contrats où `assure_id = '0'`. Convention : `'0'` signifie « pas d'assuré distinct du souscripteur » ; ce n'est pas un identifiant de client. Bronze conserve `'0'` tel quel (copie fidèle de la source) ; les contrôles d'intégrité l'excluent par un filtre ; silver le remplace par NULL (US-21). Convention proposée par le Data Steward et validée par le Data Owner, consignée dans `livrables/JOURNAL_DECISIONS.md` (décision n° 6).

Pourquoi le premier contrôle est trompeur : il annonce 40,3 % de contrats rattachés à un assuré inexistant, soit une base apparemment inutilisable, alors que 99,3 % de ces « orphelins » sont une convention de saisie. Et il noie les 300 vrais orphelins dans 40 000 faux : impossible de les voir et de les traiter.

## 4. Statuts et garantie (US-18, US-19)

| Règle | Couche | Lignes testées | Échecs | Taux |
|---|---|---|---|---|
| RQ-015 (prospect sans contrat) | BRONZE | 100 000 clients | 479 prospects titulaires d'au moins un contrat | 99,521 % (seuil 100 %, bloquante) |
| RQ-016 (souscripteur avec au moins un contrat) | BRONZE | 49 898 souscripteurs | 955 sans contrat | 98,086 % (seuil 98 %, avertissement : au-dessus du seuil) |
| RQ-017 (sinistre hors garantie) | BRONZE | 100 000 sinistres rattachés | 1 200 | 98,800 % (seuil 100 %, bloquante) |

Constats :
- RQ-015 : les 479 « prospects » détiennent jusqu'à 5 contrats, signés entre 2015 et 2025 (ex. A-35996, 5 contrats depuis le 06/07/2019). Ce ne sont pas des prospects : leur statut n'a pas été mis à jour à la signature.
- RQ-016 : 955 souscripteurs sans contrat (ex. A-10025, A-10324 ; A-1070 sans nom ni prénom, une personne morale). Une partie peut s'expliquer par les 1 000 contrats dont le souscripteur est absent de crm.client (RQ-012) : identifiants désynchronisés entre les deux tables. Le contrôle Soda est déclaré `warn: when > 0`, alors que la règle a un seuil de 98 % dans `dq.regle` : la mesure (98,086 %) est conforme au seuil, mais le scan signale quand même un avertissement.
- RQ-017 : sur 1 200 sinistres hors période, 344 (28,7 %) tombent dans la période d'un autre contrat du même souscripteur : vraisemblablement des sinistres rattachés au mauvais contrat (ancien contrat au lieu du renouvellement), donc des faux positifs de gestion. Les 856 autres sont des sinistres réellement survenus hors garantie : à vérifier par la gestion des sinistres avant tout paiement.

Règle de correction du statut proposée au Data Owner (texte, rôle, date) : « En silver, un client de type `prospect` qui détient au moins un contrat devient `souscripteur`, avec pour date d'effet la date de début de son premier contrat (479 clients concernés) ; un souscripteur sans contrat n'est pas rétrogradé automatiquement (955 clients, avertissement), il est signalé à la direction commerciale. » Proposée par le Data Steward de la séance, validée par le Data Owner (Amadou Macka Diallo) le 13/11/2026. Reportée dans `JOURNAL_DECISIONS.md` (décision n° 7).

## 5. Définition unique du client actif (US-14)

Requête (chemin) : vue `dq.v_client_actif_bronze`, créée par `pipelines/S3_integrite_soda.py` (cellule US-14) :
`SELECT DISTINCT souscripteur_id AS client_id FROM bronze.crm_contrat WHERE date_debut <= '2026-10-01' AND date_fin >= '2026-10-01' AND date_derniere_cotisation >= '2026-07-01' AND souscripteur_id IS NOT NULL` (fiche CD-001, règle RQ-018). Elle sera republiée en gold (`gold.v_client_actif`, US-27). Adoption de cette définition unique par les trois directions : décision du Data Owner (n° 8 du journal).

| Direction | Chiffre obtenu avec la requête unique |
|---|---|
| Commerciale | 38 049 |
| Sinistres | 38 049 |
| Risques | 38 049 |

En S1, chaque direction calculait son propre chiffre : 50 508 (Commerciale), 44 116 (Sinistres), 38 049 (Risques = CD-001). En interrogeant la même vue, elles obtiennent toutes 38 049.

Contrôle RQ-018 (écart entre définitions) : le contrôle `ecart_client_actif` de `soda/checks/contrat_checks.yml` mesure l'écart entre la définition Commerciale (au moins un contrat) et CD-001 : 11 878 clients, au-dessus du seuil d'échec (5 000) : FAILED. Il ne correspond pas exactement à l'écart de S1 (50 508 − 38 049 = 12 459) : la requête Soda joint `crm.client` et écarte donc les souscripteurs absents de la table client (RQ-012), ce que ne faisait pas le comptage de S1 ; l'écart de 581 est à vérifier par une requête dédiée. Tant que les directions gardent leurs propres requêtes, l'écart reste au-dessus du seuil : la porte ne s'ouvrira que lorsque la vue unique sera la seule source (US-27).

## 6. Critères de fin

- [x] Un scan renvoie un code retour non nul quand une règle bloquante échoue. (code 2 sur `client_checks`, `contrat_checks` et `sinistre_checks`, section 1)
- [ ] Chaque contrôle porte l'identifiant de sa règle et la couche mesurée. (partiel : la couche est donnée par la source de données du scan, mais cinq contrôles n'ont pas d'identifiant RQ dans leur nom : `duplicate_count` et `missing_count` des clés (RQ-020), `ecart_client_actif` (RQ-018), `taux_erreur_adresse` (RQ-014) et la relation sinistre → contrat ; à corriger en ajoutant un `name:` avec l'identifiant)
- [x] Les trois directions obtiennent le même chiffre avec la requête unique. (38 049, section 5)
- [x] La valeur sentinelle est expliquée et traitée. (section 3)

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : compréhension de ce qui est attendu (une seule ligne de code à compléter, `CONDITION_CD001`, le reste étant de la lecture et de la décision), environ 20 min ; commit incomplet (fichiers modifiés mais non enregistrés dans VS Code, puis `git add` oublié avant `git commit`), environ 15 min.

Point de reprise utilisé (oui / non, lequel) : non.

Ce que nous ferions autrement : donner à chaque contrôle Soda un `name:` portant l'identifiant de sa règle (RQ-020, RQ-018, RQ-014), pour cocher le deuxième critère de fin ; aligner le contrôle RQ-016 sur le seuil de 98 % de `dq.regle` au lieu de `warn: when > 0` ; mesurer l'écart RQ-018 de 581 clients par une requête dédiée ; vérifier `git status` avant chaque commit.

## Annexe · Dépendance code postal / commune (US-20, Should)

Mesuré sur les 95 437 adresses `pays = 'FR'` de bronze.crm_client et `silver.ref_postal` (cellule US-20) :
- Règle brute « une commune a un seul code postal » : elle échoue massivement (Lyon 37 codes postaux distincts, Paris 38, Beaumont 14), mais le référentiel montre que certaines communes en ont réellement plusieurs (Lyon 9, Paris 9, Marseille 3, Beaumont 2) : faux positifs.
- Règle recalée (zéro initial restauré, couple code postal + commune cherché dans le référentiel) : 94 755 couples valides, 682 absents (0,71 %).
- Cas Beaumont : deux communes homonymes, toutes deux valides (74160 : 566 lignes ; 07110 : 534 lignes, plus 37 lignes `7110` validées après restauration du zéro) ; 11 autres codes à une seule ligne chacun sont de vraies erreurs.
