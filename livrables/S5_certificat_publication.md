# S5 · Certifier, publier vers le CRM, gouverner

Groupe : [À COMPLÉTER]  ·  Date : [À COMPLÉTER]  ·  Rédacteur : [À COMPLÉTER]  ·  Étiquette : `seance-5`

Un constat = un chiffre mesuré (règle, couche) + la preuve qui le reproduit + ce que cela change. Voir `README.md`.

## 1. Historique des mesures (US-29, US-30)

Une ligne par règle mesurée ; laissez vide la couche où la règle ne s'applique pas, et dites pourquoi.

| Règle | Dimension | Taux bronze | Taux silver | Taux gold | Évolution (monte, stable, descend) | Explication |
|---|---|---:|---:|---:|---|---|
| RQ-001 | Cohérence | 99,200 % | 100 % | 100 % | Monte puis stable | La cohérence des contrats est rétablie dans Silver. |
| RQ-002 | Validité métier | 99,699 % | 99,702 % | 100 % | Monte | La conformité métier des contrats progresse jusqu'à Gold. |
| RQ-003 | Complétude | 87,998 % | 88,006 % | 89,938 % | Monte légèrement | Les téléphones manquants restent présents malgré une légère amélioration. |
| RQ-005 | Validité format | 98,474 % | 100 % | 100 % | Monte puis stable | Les formats sont normalisés dans Silver. |
| RQ-007 | Intégrité référentielle | 96,950 % | 100 % | 100 % | Monte | Les références clients non conformes sont traitées avant Gold. |
| RQ-009 | Validité domaine | 99,800 % | 100 % | — | Monte | Mesure disponible en Bronze et Silver ; pas de mesure Gold enregistrée. |
| RQ-010 | Validité domaine | 99,400 % | 100 % | 100 % | Monte puis stable | La conformité du domaine est rétablie dans Silver. |
| RQ-011 | Intégrité référentielle | 99,800 % | 99,798 % | 100 % | Stable puis monte | L'écart en Silver est très faible, puis la conformité atteint 100 % dans Gold. |
| RQ-012 | Intégrité référentielle | 99,000 % | 98,382 % | 100 % | Descend puis monte | La conformité baisse en Silver, puis atteint 100 % dans Gold. |
| RQ-013 | Intégrité référentielle | 99,700 % | 99,334 % | 100 % | Descend puis monte | La conformité baisse en Silver, puis atteint 100 % dans Gold. |
| RQ-015 | Cohérence de statut | 99,521 % | 99,524 % | 100 % | Stable puis monte | La cohérence des statuts est conservée puis atteint 100 % dans Gold. |
| RQ-016 | Cohérence de statut | 98,086 % | 97,700 % | — | Descend | Mesure absente en Gold ; le taux Silver passe sous le seuil d'avertissement de 98 %. |
| RQ-017 | Cohérence inter-tables | 98,800 % | 98,800 % | 100 % | Stable puis monte | La conformité reste stable en Silver puis atteint 100 % dans Gold. |
| RQ-018 | Cohérence de définition | — | — | 100 % | — | Règle mesurée uniquement en Gold. |
| RQ-019 | Unicité | — | — | 100 % | — | Règle mesurée uniquement en Gold. |
| RQ-020 | Unicité | 100 % | 100 % | 100 % | Stable | Les clés primaires restent uniques et non nulles sur les trois couches. |
| RQ-021 | Complétude, intégrité | 100 % | — | — | — | Règle mesurée uniquement en Bronze. |
| RQ-022 | Traçabilité | 100 % | — | — | — | Règle mesurée uniquement en Bronze. |
| RQ-023 | Traçabilité | — | 100 % | 100 % | Stable | Règle mesurée en Silver et Gold. |
| RQ-024 | Complétude | — | 100 % | — | — | Règle mesurée uniquement en Silver. |

Courbes (chemin des images) : 

Toute règle qui descend d'une couche à l'autre : cause (filtre mal posé, conversion, effet de la quarantaine) et preuve :

- **RQ-012** : le taux passe de 99,000 % en Bronze à 98,382 % en Silver. La mesure montre 1 000 échecs en Bronze et 1 595 en Silver sur la règle d'intégrité référentielle des contrats. La quarantaine en porte G concerne 1 595 contrats.
- **RQ-013** : le taux passe de 99,700 % en Bronze à 99,334 % en Silver. La mesure montre 300 échecs en Bronze et 657 en Silver. La quarantaine en porte G concerne 657 contrats.
- **RQ-016** : le taux passe de 98,086 % en Bronze à 97,700 % en Silver. La mesure indique 1 143 échecs en Silver. La mesure Gold n'est pas disponible.

## 2. Certificat de qualité (US-31)

| Élément | Valeur |
|---|---|
| Numéro du certificat | … |
| Lot | … |
| Décision (GO ou NO_GO) | … |
| Règles bloquantes testées | … |
| Règles bloquantes conformes | … |
| Écarts connus (avertissements) | … |
| Empreinte du gold | … |
| Signataire (rôle) | … |

Requête de décision (chemin) : [À COMPLÉTER]

Épreuve du NO_GO : lot volontairement dégradé (comment), décision obtenue, preuve : [À COMPLÉTER]

Règles bloquantes non mesurées par votre pipeline et donc non couvertes par le certificat : [À COMPLÉTER]

## 3. Publication vers le CRM (US-32)

Script (chemin) : [À COMPLÉTER]

| Scénario | Message obtenu | Chargement effectué ? | Preuve |
|---|---|---|---|
| Sans certificat | … | … | … |
| Certificat NO_GO | … | … | … |
| Gold modifié après émission du certificat | … | … | … |
| Certificat GO et gold intact | … | … | … |

Réconciliation après chargement (RQ-025) :

| Table | Lignes gold | Lignes CRM cible | Somme de contrôle gold | Somme de contrôle CRM cible | Écart |
|---|---|---|---|---|---|
| client | … | … | … | … | … |
| contrat | … | … | … | … | … |
| sinistre | … | … | … | … | … |

Le chargement est-il tout-ou-rien ? Comment l'avez-vous vérifié : [À COMPLÉTER]

## 3 bis. Gouvernance (US-34)

Fiche de catalogue de `gold.client_unique` (chemin) : [À COMPLÉTER]

| Élément | Valeur |
|---|---|
| Propriétaire (Data Owner) | … |
| Steward (Data Steward) | … |
| Définition de « client actif » rattachée à la fiche | … |
| Règles RQ rattachées à la table | … |

Lineage de `gold.client_unique` jusqu'aux sources (liste ou schéma) : [À COMPLÉTER]

## 4. Décisions de la séance

Reportez dans `JOURNAL_DECISIONS.md` chaque seuil, sévérité ou règle de survie arrêté, avec son rôle. Nombre de décisions ajoutées en S5 : [À COMPLÉTER]

## 5. Critères de fin

- [ ] Un lot volontairement dégradé produit un NO_GO, le lot nominal un GO.
- [ ] La publication refuse sans certificat, avec une décision NO_GO, et quand le gold a changé.
- [ ] Après un chargement réussi, comptage et somme de contrôle sont égaux entre gold et CRM cible.
- [ ] Chaque décision de seuil ou de sévérité est attribuée à un rôle.

## 6. Difficultés, écarts avec l'attendu, reprise

Difficultés rencontrées et temps perdu : [À COMPLÉTER]

Point de reprise utilisé (oui / non, lequel) : [À COMPLÉTER]

Ce que nous ferions autrement : [À COMPLÉTER]
