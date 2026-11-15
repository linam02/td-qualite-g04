# Journal des décisions

Une ligne par décision de seuil, de sévérité, de définition ou de règle de survie. Une décision sans rôle ni justification chiffrée n'est pas une décision. Ce journal alimente la partie « La décision » du dossier go/no-go.

| N° | Date | Séance | Règle ou objet | Décision (ce qui est arrêté) | Justification chiffrée (preuve) | Rôle décideur | Alternative écartée |
|---|---|---|---|---|---|---|---|
| 1 | 15/11/2026 | S3 | RQ-013 valeur sentinelle de assure_id | « 0 » = assuré identique au souscripteur : exclu des contrôles de clé en bronze, remplacé par NULL en silver | 40 000 contrats à « 0 » ; orphelins 40 300 avant traitement, 300 après ; aucun contrat avec assure_id = souscripteur_id (`notebooks/S3_integrite_soda.ipynb`, US-17) | Data Owner | Compter « 0 » comme orphelin : 40 000 fausses anomalies, RQ-013 à 59,7 % au lieu de 99,7 % |
| 2 | 15/11/2026 | S4 | Porte G, quarantaine en cascade (RQ-012, RQ-013, RQ-017) | Un contrat dont le souscripteur ou l'assuré est en quarantaine est écarté du gold, ainsi que les sinistres de ce contrat : aucun orphelin n'est publié | 595 contrats écartés par ricochet (souscripteur en quarantaine), 2 308 sinistres écartés car leur contrat est rejeté ; 0 orphelin en gold (`notebooks/S4_silver_gold.ipynb`, US-27) | Data Owner | Publier ces contrats avec un CLI vide : gold incohérent, RQ-012 sous le seuil, porte G fermée |
| 3 | 15/11/2026 | S4 | RQ-018 client actif | Le client actif est publié par une seule vue `gold.v_client_actif`, calculée sur les contrats certifiés avec la définition CD-001 | 35 985 clients actifs ; RQ-018 à 100 % sur gold ; écart de 2 064 avec bronze expliqué par le dédoublonnage et les contrats écartés | Data Owner | Laisser chaque direction calculer son chiffre : 50 508 / 44 116 / 38 049 en S1 |

Ajoutez des lignes autant que nécessaire. Exemples de décisions attendues : sévérité d'une règle, seuil d'avertissement, définition unique du client actif, convention de la valeur sentinelle, seuils de rapprochement, règle de survie par attribut, seuil de la porte G.
