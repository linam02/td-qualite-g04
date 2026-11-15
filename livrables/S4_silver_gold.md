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

# US-24 — Dédoublonnage : paramètres et mesures

## Paramètres retenus

| Paramètre | Valeur retenue | Justification |
|---|---|---|
| Normalisation avant comparaison | Identité normalisée, code postal, ville normalisée et date de naissance normalisée. La date est rendue tolérante à l’inversion jour/mois. | Réduire les différences de casse, d’accents, d’espaces et de formats avant la comparaison. |
| Clés de blocage | 1. Code postal + 3 premiers caractères de l’identité normalisée. 2. Code postal + date de naissance normalisée. 3. Ville normalisée + 4 premiers caractères de l’identité. | Limiter les comparaisons aux enregistrements susceptibles de désigner la même personne. |
| Mesure de similarité | `rapidfuzz.fuzz.ratio`, score de 0 à 100. | Mesurer la proximité des chaînes de caractères. |
| Seuil de fusion automatique | 85/100, avec code postal identique et au moins un signal complémentaire. | Éviter une fusion sur la seule ressemblance du nom. |
| Seuil de la zone de revue | 70/100. | Les candidats non fusionnés automatiquement sont soumis à une vérification humaine. |

### Règles complémentaires

- Les blocs de candidats de taille inférieure à 2 ou supérieure à 400 sont ignorés.
- Les candidats dont la similarité est inférieure à 70 sont écartés.
- Des contrôles complémentaires portent notamment sur l’initiale du prénom, la date de naissance et les coordonnées.
- Les signaux complémentaires comprennent une similarité d’adresse d’au moins 80, un téléphone ou un courriel identique non vide, ou une date de naissance identique.
- La fusion automatique exige un score d’au moins 85, un code postal identique et au moins un signal complémentaire.

## Mesures obtenues

| Mesure | Valeur |
|---|---:|
| Lignes clients dans Silver | 139 350 |
| Paires candidates | 2 782 840 |
| Groupes de doublons trouvés | 18 237 |
| Lignes appartenant à un groupe de doublons | 37 107 |
| Taille maximale d’un groupe | 4 |
| Paires fusionnées automatiquement | 19 505 |
| Paires candidates non fusionnées automatiquement | 2 120 |
| Identités distinctes obtenues | 120 480 |

### Précision et rappel

Sur les paires étiquetées évaluables — c’est-à-dire celles dont les deux enregistrements sont présents dans Silver — le résultat mesuré est :

- Vrais positifs : 100
- Faux positifs : 0
- Faux négatifs : 0
- Précision : 100 %
- Rappel : 100 %

**Attention :** les paires dont au moins un enregistrement a été mis en quarantaine ne sont pas évaluées. Le résultat de 100 % porte donc sur les paires étiquetées évaluables, et non nécessairement sur la totalité des 200 paires du fichier de référence.

### Sensibilité au seuil

| Seuil automatique | Paires automatiques | Précision | Rappel |
|---:|---:|---:|---:|
| 80 | 19 509 | 100 % | 100 % |
| 85 | 19 505 | 100 % | 100 % |
| 90 | 19 194 | 100 % | 91 % |
| 95 | 18 415 | 100 % | 87 % |

Le seuil de 85 est retenu : il conserve les résultats observés en précision et en rappel, tandis qu’un seuil plus élevé fait baisser le rappel.

## Zone de revue — règle de décision proposée

Toute paire candidate qui atteint le seuil de similarité de 70 mais ne satisfait pas les conditions de fusion automatique est placée en revue manuelle.

1. Le Data Steward examine les informations disponibles : identité, date de naissance, adresse, téléphone et courriel.
2. Si les éléments concordent, il propose la fusion au Data Owner.
3. Si les éléments sont contradictoires ou insuffisants, les identités restent séparées.
4. La décision et sa justification sont consignées dans le journal des décisions afin d’assurer la traçabilité.

---

# US-25 — Golden record de la Société Meunier et règle de survie

## Identifiants sources réunis sous un même CLI

Les quatre identifiants de la Société Meunier sont regroupés sous le CLI **CLI-033758**.

| Identifiant source | Système | CLI attribué |
|---|---|---|
| K471226 | CIF | CLI-033758 |
| A-4471 | CRM | CLI-033758 |
| H-9012 | CRM | CLI-033758 |
| S-2208 | CRM | CLI-033758 |

Les quatre lignes correspondent à l’identité normalisée **MEUNIER SARL**, code postal **69003**.

## Règle de survie par attribut

La règle actuellement implémentée donne la priorité à la source CIF, puis au CRM. À l’intérieur d’une même source, la ligne Silver ayant le plus petit `silver_row_id` est prioritaire. La première valeur non nulle est retenue pour chaque champ.

| Attribut | Source retenue | Règle | Cas où la règle peut se tromper |
|---|---|---|---|
| Nom | CIF en priorité, puis CRM | Première valeur non nulle après tri par priorité de source, puis par `silver_row_id` croissant. | Le nom CIF peut être ancien ou moins à jour que le nom CRM. |
| Adresse | Non intégrée dans le Golden Record actuel | Le champ adresse n’est pas sélectionné dans la construction du GR. | Une adresse récente présente dans le CRM ne sera pas publiée dans le GR actuel. |
| Téléphone | CIF en priorité, puis CRM | Première valeur non nulle après tri par priorité de source, puis par `silver_row_id` croissant. | Le téléphone CIF peut être obsolète alors que le CRM contient le numéro actuel. |
| Courriel | CIF en priorité, puis CRM | Première valeur non nulle après tri par priorité de source, puis par `silver_row_id` croissant. | Le courriel CIF peut être obsolète alors que le CRM contient une adresse électronique plus récente. |

## Constitution du Golden Record

Le Golden Record construit par le traitement contient notamment :

- `cli_id`
- `nom_reference`
- `date_naissance`
- `cp`
- `ville`
- `pays_iso`
- `telephone`
- `email`
- `nb_identifiants_source`

L’adresse n’est pas incluse dans cette construction.

## Contrôle et gouvernance

- 139 350 lignes Silver sont traitées.
- 0 ligne Silver ne reste sans CLI.
- La règle de survie est une décision de gouvernance : elle doit être validée par le Data Owner.
- Le Data Steward peut documenter les écarts constatés et soumettre une proposition d’évolution de la règle.
- La priorité CIF peut être inadaptée lorsque les données CRM sont plus récentes. Une évolution possible serait d’intégrer une date de mise à jour fiable par attribut, si elle est disponible et validée.



## 4. Gold et client actif (US-27)

| Table gold | Lignes | Lignes écartées (porte G) | Règles responsables |
|---|---|---|---|
| client_unique | … | … | … |
| xref_identifiants | … | … | … |
| contrat_certifie | … | … | … |
| sinistre_certifie | … | … | … |

Orphelins dans gold (contrat sans client, sinistre sans contrat) : [À COMPLÉTER]

Client actif publié par la vue `v_client_actif` : [À COMPLÉTER]. Écart avec la définition de la fiche CD-001 : [À COMPLÉTER]

Effet de la quarantaine sur l'intégrité en aval (un client écarté laisse-t-il des contrats orphelins ?) : [À COMPLÉTER]

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
