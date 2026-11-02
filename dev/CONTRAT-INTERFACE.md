# Contrat d'interface DEV ↔ DATA

SAÉ 3.01 « Climat & Cultures », équipe 9.


## 1. Grain retenu : commune ET région

On stocke les données à l'échelle de la **commune** — c'est ce
que demande l'énoncé et c'est la granularité naturelle de l'API
Open-Meteo. Mais on permet aussi une vue par **région** pour
comparer les territoires entre eux.

Concrètement : la base ne change pas, on ajoute simplement une
colonne `id_region` dans `Dim_Commune`. L'agrégation par région
se fait ensuite par une requête SQL sur les communes de référence
appartenant à cette région — pas besoin de stocker quoi que ce
soit de plus.

**Ce que ça change pour chaque pôle :**
- **DATA** : ajouter `id_region` (code région INSEE sur 2 chiffres)
  dans `Dim_Commune` et écrire la requête d'agrégation.
- **DEV** : prévoir dans l'IHM un double point d'entrée —
  recherche par commune ou sélection par région.

La clé principale reste le **code INSEE commune sur 5 caractères**
dans toute la base et tous les échanges.

---

## 2. Format d'échange des séries

DEV fournit à DATA les séries climatiques brutes issues de l'API,
au format suivant — un fichier CSV par commune et par horizon,
les deux modèles dedans.

```
id_commune;date;id_horizon;id_modele;t_min;t_max;t_moy;precip
51454;2049-03-01;PROJ_2041_2050;MRI_AGCM3_2_S;-3.1;2.0;-0.6;6.20
```

| Champ | Type | Règle |
|---|---|---|
| `id_commune` | texte, 5 caractères | code INSEE, **zéro initial conservé** — `05023` et jamais `5023` |
| `date` | ISO 8601 | format `AAAA-MM-JJ`, jamais le format français |
| `id_horizon` | texte | `REF_2011_2020` ou `PROJ_2041_2050`, clés de `Dim_Temps` |
| `id_modele` | texte | `MRI_AGCM3_2_S` ou `CMCC_CM2_VHR4`, clés de `Dim_Modele` |
| `t_min`, `t_max`, `t_moy` | décimal | degrés Celsius, séparateur **point** |
| `precip` | décimal | millimètres par jour |

Quelques règles importantes à ne pas oublier :
- Séparateur **point-virgule**, encodage **UTF-8**.
- Une valeur manquante = **case vide**, jamais un zéro.
  Zéro degré est une température réelle, pas une absence de mesure.
- Le champ `elevation` renvoyé par l'API est transmis à DATA
  séparément — il sert à vérifier l'altitude dans `Dim_Commune`.
- **L'ET0 n'est pas dans les séries.** C'est DATA qui l'estime
  via la méthode Hargreaves à partir de `t_min` et `t_max`.
  DEV n'a pas à la calculer.

Un exemple complet est disponible dans
`data/test/series-reims-2049-complete.csv`.

---

## 3. Qui fait quoi

**DEV s'occupe des séries** : appel à l'API Open-Meteo Climate
(https://climate-api.open-meteo.com/v1/climate, sans clé),
mise en forme au format ci-dessus, gestion du quota et du cache.

**DATA s'occupe des faits** : calcul des indicateurs à partir
des séries, alimentation de `Fact_Indicateur`, référentiel
des seuils agronomiques et des fenêtres de calcul.

Pour être clair sur ce que chaque pôle ne fait pas :
- DATA ne stocke pas les séries brutes — seuls les indicateurs
  calculés vont en base.
- DEV ne touche pas aux seuils agronomiques ni aux fenêtres
  de calcul — ça vient entièrement du référentiel DATA.

Tant que le client API de DEV n'est pas prêt, DATA travaille
sur le jeu de test dans `data/test/` — c'est tout l'intérêt
d'avoir fixé ce format dès maintenant.

---

## 4. Conventions à respecter des deux côtés

Quelques pièges qui arrivent souvent en intégration et qu'on
évite en les écrivant ici :

**Noms de tables** : toujours avec les majuscules —
`Dim_Commune`, `Fact_Indicateur`, `Fenetre_Calcul`. MySQL sous
Windows ne fait pas la différence entre majuscules et minuscules,
mais AlwaysData (Linux) si. Une requête qui marche en local peut
planter en production pour cette seule raison.

**Code INSEE** : toujours stocké en texte, jamais en entier.
Convertir en nombre fait disparaître le zéro initial des
départements 01 à 09.

**Coordonnées** : l'API Géo renvoie les coordonnées dans l'ordre
`[longitude, latitude]`, c'est l'inverse d'Open-Meteo.
Toujours vérifier le sens avant un appel.

**Dates** : format ISO (`AAAA-MM-JJ`) partout — dans les fichiers,
dans la base, dans les URL d'API.

---

## 5. Intégration au jalon 3 (S48)

La fiche de parcours prévoit qu'en S48 DEV intègre le module
de calcul de DATA et que l'application affiche un vrai indicateur.
On pose la question maintenant pour que personne ne la découvre
en S48.

Piste de départ : DATA expose une fonction
`indicateurs_culture(serie, id_culture, latitude)` et une fonction
`verdict(serie, id_culture, latitude)` dans `indicateurs.py`.
À préciser et valider ensemble avant le sprint 1.

---

## Validation

Ce contrat engage les deux pôles. Toute modification se fait
par une nouvelle version datée, annoncée aux six membres
de l'équipe.

| Équipier | Pôle | Date | Accord |
|---|---|---|---|
| Sabiledine BOUAFIA | | | |
| Remy CHAMBI LEBLANC | | | |
| Adrien CREPIEUX | | | |
| Sebastien MARDAUS | | | |
| Rakul PARIMELALAGAN | | | |
| Dharun SINOUVASSANE | | | |
