# S4 · PySpark : construire silver puis gold

Groupe : [À COMPLÉTER]  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-4`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Silver et quarantaine (US-21, US-22)

Scripts ou notebooks (chemins) : [À COMPLÉTER]

Traitements appliqués (pays, code postal, identité, autres), avec le nombre de lignes touchées par chacun :

| Traitement | Table | Lignes modifiées | Garde-fou (ce que le traitement ne doit pas faire) |
|---|---|---|---|
| … | … | … | … |
| … | … | … | … |
| … | … | … | … |

Invariant silver + rejets = bronze :

| Table | Lignes bronze | Lignes silver | Lignes rejetées | Écart |
|---|---|---|---|---|
| client (crm) | … | … | … | … |
| client (cif) | … | … | … | … |
| contrat | … | … | … | … |
| sinistre | … | … | … | … |

Rejets par règle (`dq.rejets`) :

| Règle | Table | Lignes rejetées | Raison métier |
|---|---|---|---|
| … | … | … | … |
| … | … | … | … |

Idempotence : le traitement relancé deux fois donne le même résultat (preuve) : [À COMPLÉTER]

## 2. Porte S : bronze contre silver (US-23)

| Règle | Sévérité | Taux bronze | Taux silver | Écart | Explication de l'écart |
|---|---|---|---|---|---|
| … | … | … | … | … | … |
| … | … | … | … | … | … |
| … | … | … | … | … | … |
| … | … | … | … | … | … |
| … | … | … | … | … | … |

Toute règle dont le taux baisse de bronze à silver doit être expliquée : [À COMPLÉTER]

Règles bloquantes de la porte S toutes conformes sur silver ? Sinon, lesquelles et pourquoi : [À COMPLÉTER]

## 3. Dédoublonnage et golden record (US-24, US-25)

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| Normalisation appliquée avant comparaison | … | … |
| Clé(s) de blocage | … | … |
| Mesure de similarité | … | … |
| Seuil de fusion automatique | … | … |
| Seuil de la zone de revue | … | … |

| Mesure | Valeur |
|---|---|
| Groupes de doublons trouvés | … |
| Paires fusionnées automatiquement | … |
| Paires en zone de revue | … |
| Précision sur les 200 paires étiquetées | … |
| Rappel sur les 200 paires étiquetées | … |
| Identités distinctes obtenues | … |

Golden record de la Société Meunier :

| Identifiant source | Système | CLI attribué |
|---|---|---|
| … | … | … |
| … | … | … |
| … | … | … |
| … | … | … |

Règle de survie par attribut :

| Attribut | Source retenue | Règle (priorité, plus récent, non nul) | Cas où la règle se trompe |
|---|---|---|---|
| Nom | … | … | … |
| Adresse | … | … | … |
| Téléphone | … | … | … |
| Courriel | … | … | … |

Reportez les seuils et la règle de survie dans `JOURNAL_DECISIONS.md`, avec le rôle qui les a décidés.

## 4. Gold et client actif (US-27)

| Table gold | Lignes | Lignes écartées (porte G) | Règles responsables |
|---|---|---|---|
| client_unique | 120 480 | 0 (650 clients CRM déjà mis en quarantaine en porte S) | Porte S : RQ-007 (450), RQ-009 (200) |
| xref_identifiants | 139 350 | 0 | – (99 350 identifiants CRM + 40 000 CIF, tous rattachés à un CLI) |
| contrat_certifie | 95 866 | 2 734 contrats sur 98 600 (2 745 rejets, certains contrats violent deux règles) | RQ-012 (1 595), RQ-013 (657), RQ-002 (294), RQ-011 (199) |
| sinistre_certifie | 96 532 | 3 468 sur 100 000 | RQ-017 : 2 308 dont le contrat est absent du gold, 1 160 hors période de garantie |

Orphelins dans gold (contrat sans client, sinistre sans contrat) : **0**. Aucun contrat certifié dont le souscripteur ou l'assuré est absent de `gold.client_unique`, aucun sinistre certifié dont le contrat est absent de `gold.contrat_certifie`. Porte G franchie : toutes les règles bloquantes mesurées sur gold sont à 100 % (RQ-001, 002, 007, 010 à 013, 015, 017 à 020, 023). Seule RQ-003 (avertissement, téléphone renseigné) reste sous son seuil : 89,9 % pour 98 % attendus. Preuve : `notebooks/S4_silver_gold.ipynb`, cellules US-27 et US-27 (suite) ; `dq.dq_history`, couche GOLD ; `dq.rejets`, porte G.

Client actif publié par la vue `v_client_actif` : **35 985** clients (`gold.v_client_actif`, la même vue pour les trois directions). Écart avec la définition de la fiche CD-001 : **0 sur gold**. RQ-018 vérifie que le statut ACTIF de chaque client correspond exactement à la condition CD-001 recalculée sur les contrats certifiés (120 480 clients testés, 0 écart). L'écart de 2 064 avec les 38 049 clients actifs calculés sur bronze en S3 ne vient pas de la définition. Il a deux causes : le dédoublonnage (plusieurs identifiants souscripteur d'une même personne ne comptent plus qu'une fois sous un seul CLI) et les contrats écartés en porte S et G, qui ne peuvent plus rendre un client actif.

Effet de la quarantaine sur l'intégrité en aval : oui, un client écarté laisse des contrats orphelins, que la porte G écarte à leur tour (effet domino). Sur les 1 595 contrats rejetés par RQ-012, 1 000 étaient déjà orphelins en bronze (S3), mais **595** ont un souscripteur présent en bronze et mis en quarantaine en silver (pays hors référentiel ou type de personne invalide). De même, RQ-013 écarte 657 contrats contre 300 orphelins en bronze, et **2 308** sinistres sont écartés uniquement parce que leur contrat a été rejeté en amont. C'est pourquoi RQ-012 et RQ-013 se dégradent de bronze à silver (99,0 % → 98,4 % ; 99,7 % → 99,3 %). Le gold reste cohérent (0 orphelin), mais au prix de lignes perdues : corriger à la source les 650 clients en quarantaine récupérerait jusqu'à 595 contrats et les sinistres qui en dépendent.

## 5. Traçabilité de trois données (US-28)

| Donnée | Valeur dans gold | Silver (identifiants de ligne) | Bronze (identifiants de ligne, lot) | Source (table, clé) |
|---|---|---|---|---|
| Société Meunier | … | … | … | … |
| Un code postal à zéro initial | … | … | … | … |
| Une adresse de sinistre | … | … | … | … |

Requête de traçabilité (chemin) : [À COMPLÉTER]

## 6. Critères de fin

- [ ] Pour chaque table, silver + rejets = bronze, sans suppression silencieuse.
- [ ] Relancer le traitement deux fois donne le même résultat.
- [ ] Les règles bloquantes de la porte S sont conformes sur silver.
- [ ] Le gold ne contient aucun orphelin ; le client actif est publié par une seule vue.
- [ ] Les trois traces remontent du gold à la source avec identifiants de ligne et de lot.

## 7. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel, à quel moment) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
