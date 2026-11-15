# Journal des décisions

Une ligne par décision de seuil, de sévérité, de définition ou de règle de survie. Une décision sans rôle ni justification chiffrée n'est pas une décision. Ce journal alimente la partie « La décision » du dossier go/no-go.

| N° | Date | Séance | Règle ou objet | Décision (ce qui est arrêté) | Justification chiffrée (preuve) | Rôle décideur | Alternative écartée |
|---|---|---|---|---|---|---|---|
| 1 | 15/11/2026 | S3 | RQ-013 valeur sentinelle de assure_id | « 0 » = assuré identique au souscripteur : exclu des contrôles de clé en bronze, remplacé par NULL en silver | 40 000 contrats à « 0 » ; orphelins 40 300 avant traitement, 300 après ; aucun contrat avec assure_id = souscripteur_id (`notebooks/S3_integrite_soda.ipynb`, US-17) | Data Owner | Compter « 0 » comme orphelin : 40 000 fausses anomalies, RQ-013 à 59,7 % au lieu de 99,7 % |

Ajoutez des lignes autant que nécessaire. Exemples de décisions attendues : sévérité d'une règle, seuil d'avertissement, définition unique du client actif, convention de la valeur sentinelle, seuils de rapprochement, règle de survie par attribut, seuil de la porte G.
