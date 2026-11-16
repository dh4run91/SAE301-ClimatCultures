# SAE301-ClimatCultures

SAÉ 3.01 « Climat & Cultures », BUT Informatique, IUT Créteil-Vitry, équipe 9.

Application qui croise des projections climatiques avec des seuils
agronomiques, pour dire quelles cultures restent viables dans une commune
française à l'horizon 2050.

## Organisation du dépôt

| Dossier | Contenu |
|---|---|
| `data/` | données de référence : référentiel des cultures, communes, audit des sources |
| `data/test/` | jeu de séries climatiques de test, avec ses valeurs attendues |
| `sql/` | les quatre scripts de la base |
| `test/` | la suite de tests du module de calcul |
| `docs/` | documents du projet : analyse, conception RGPD, journal IA, schéma |
| `dev/` | travail du pôle DEV, client API et maquettes |
| `indicateurs.py` | module de calcul des indicateurs, à la racine |

Règle de nommage pour les documents et les données : pas d'espace, pas
d'accent, pas de trait de soulignement. Des traits d'union, et la casse déjà
en place dans chaque dossier. Les fichiers Python gardent le trait de
soulignement : un nom de module avec un trait d'union ne peut pas être
importé.

## Charger la base

L'ordre n'est pas interchangeable :

1. `sql/01-creation-base.sql`
2. `sql/02-insertion-dimensions.sql`
3. `sql/03-tables-rgpd.sql`
4. `sql/04-agregation-region.sql`

Comptages attendus après chargement : 16 communes réparties sur 10 régions,
10 cultures, 2 horizons, 2 modèles, 17 fenêtres de calcul.

## Lancer les tests

```
python test/test_indicateurs.py
```

Sortie attendue : `9 / 9 tests reussis`.

Le fichier a son propre lanceur : pytest n'est pas nécessaire, il n'y a rien
à installer. `pytest test/` échoue à la collecte à cause de
`test/test_cle.py`, un script qui vérifie la clé API et non un test
unitaire.

Ce lanceur n'attrape que les `AssertionError`. Un run qui ne finit pas par
un bilan est un run à ne pas commiter, quelle qu'en soit la raison.

## Lancer le module

```
python indicateurs.py
python indicateurs.py <fichier>
```

Sans argument, il traite `data/test/series-reims-2049-complete.csv`. Avec un
argument, le fichier indiqué.

`indicateurs.py` n'utilise que la bibliothèque standard : `csv`, `json`,
`math`, `os`, `sys`, `datetime`.

## Source des données

Données issues de l'API Open-Meteo Climate,
`https://climate-api.open-meteo.com/v1/climate`, sans clé. Projections CMIP6
descendues à environ 10 km, de 1950 à 2050. Licence CC BY 4.0, attribution
obligatoire.

Deux modèles retenus : `MRI_AGCM3_2_S` et `CMCC_CM2_VHR4`.

Ce sont des projections, pas des prévisions.
