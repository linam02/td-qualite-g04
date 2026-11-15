# S3 · Soda Core : intégrité entre tables, portes en SodaCL

Groupe : [À COMPLÉTER]  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-3`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Checks et configuration (US-12)

Fichiers (chemins) : configuration [À COMPLÉTER] ; checks client [À COMPLÉTER] ; contrat [À COMPLÉTER] ; sinistre [À COMPLÉTER]

| Règle | Fichier de checks | Couche mesurée | Résultat Soda (PASSED, WARN, FAILED) | Valeur mesurée | Code retour du scan |
|---|---|---|---|---|---|
| … | … | … | … | … | … |
| … | … | … | … | … | … |
| … | … | … | … | … | … |
| … | … | … | … | … | … |
| … | … | … | … | … | … |

Un avertissement et un échec : à quelle condition le code retour du scan devient-il non nul ? [À COMPLÉTER]

Les valeurs Soda sont-elles cohérentes avec celles de Great Expectations en S2 ? Écarts et explication : [À COMPLÉTER]

## 2. Bilan d'intégrité (US-16)

Aucune clé étrangère n'est déclarée dans la base : chaque relation est à vérifier.

| Relation | Lignes testées | Orphelins | Taux | Conclusion (anomalie, sentinelle, normal) |
|---|---|---|---|---|
| contrat.souscripteur_id vers client | … | … | … | … |
| contrat.assure_id vers client | … | … | … | … |
| contrat.code_type vers type_contrat | … | … | … | … |
| sinistre.contrat_id vers contrat | … | … | … | … |
| … | … | … | … | … |

## 3. Valeur sentinelle (US-17)

| Contrôle | Orphelins | Preuve |
|---|---|---|
| Sur `assure_id`, avant traitement de la sentinelle | 40 300 sur 100 000 contrats (40,3 %) | `notebooks/S3_integrite_soda.ipynb`, cellule US-17 ; `soda/checks/bronze/sentinelle_avant.yml` |
| Sur `assure_id`, après traitement | 300 sur 60 000 contrats testés (0,5 %) | `notebooks/S3_integrite_soda.ipynb`, cellule US-17 ; filtre `assure_renseigne` de `soda/checks/contrat_checks.yml` |

Écart chiffré et convention écrite : l'écart est de 40 000 orphelins, exactement le nombre de contrats où `assure_id` vaut « 0 » (40 000 sur 100 000). Ce « 0 » n'est pas un identifiant client mais une **valeur sentinelle** qui signifie « l'assuré est le souscripteur lui-même » : aucun contrat ne porte un `assure_id` égal à son `souscripteur_id`, la source écrit « 0 » à la place. 

Convention : la sentinelle est conservée telle quelle en bronze (copie fidèle), exclue des contrôles de clé par le filtre `assure_id <> '0'`, puis remplacée par NULL en silver. Proposée par le Data Steward, validée par le Data Owner (voir `JOURNAL_DECISIONS.md`).

Pourquoi le premier contrôle est trompeur : il traite « 0 » comme un identifiant client et cherche un client « 0 » qui n'existe pas. Il annonce donc 40,3 % de contrats en anomalie alors que seuls 300 contrats (0,3 %) pointent réellement vers un assuré inconnu (ex. H-91322, S-96271, clients probablement supprimés ou jamais chargés). Une valeur conventionnelle doit être identifiée et traitée **avant** de mesurer l'intégrité, sinon la mesure surestime le problème d'un facteur 134 et masque les vraies anomalies.

## 4. Statuts et garantie (US-18, US-19)

| Règle | Couche | Lignes testées | Échecs | Taux |
|---|---|---|---|---|
| RQ-015 (prospect sans contrat) | … | … | … | … |
| RQ-016 | … | … | … | … |
| RQ-017 (sinistre hors garantie) | … | … | … | … |

Règle de correction du statut proposée au Data Owner (texte, rôle, date) : [À COMPLÉTER]. Reportez-la dans `JOURNAL_DECISIONS.md`.

## 5. Définition unique du client actif (US-14)

Requête (chemin) : [À COMPLÉTER]

| Direction | Chiffre obtenu avec la requête unique |
|---|---|
| Commerciale | … |
| Sinistres | … |
| Risques | … |

Contrôle RQ-018 (écart entre définitions) : [À COMPLÉTER]

## 6. Critères de fin

- [ ] Un scan renvoie un code retour non nul quand une règle bloquante échoue.
- [ ] Chaque contrôle porte l'identifiant de sa règle et la couche mesurée.
- [ ] Les trois directions obtiennent le même chiffre avec la requête unique.
- [ ] La valeur sentinelle est expliquée et traitée.

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
