# Identification des dimensions nécessaires

SAÉ 3.01 « Climat & Cultures » — Pôle DATA — J1 (S40)

---

## Rappel de l'architecture

Le datamart en étoile repose sur une table de faits centrale, `Fact_Indicateur`, entourée de 4 dimensions. Chacune répond à une question simple : pour quelle culture (`Dim_Culture`), dans quelle commune (`Dim_Commune`), sur quel horizon (`Dim_Temps`), avec quel modèle climatique (`Dim_Modele`).

Une table annexe, `Fenetre_Calcul`, complète le schéma : elle indique sur quelle période de l'année chaque indicateur doit être calculé, culture par culture.

---

## Dim_Culture — la culture et ses seuils agronomiques

C'est la grille de lecture agronomique du projet : sans elle une température brute ne veut rien dire. C'est elle qui transforme « il a fait 28°C » en « c'est dangereux pour cette culture-là, à ce stade-là ».

| Colonne | Type | Description |
|---|---|---|
| `id_culture` | VARCHAR | Identifiant unique (ex. BLE_TENDRE_H) |
| `nom` | VARCHAR | Nom lisible (ex. Blé tendre d'hiver) |
| `type` | VARCHAR | Catégorie (céréale_hiver, oléagineux_été…) |
| `t_base_c` | FLOAT | Température de base / zéro de végétation (°C) |
| `t_plafond_gdd_c` | FLOAT | Plafond de température pour le calcul des GDD (°C) — 30 °C pour le maïs, vide sinon |
| `gdd_maturite_cj` | FLOAT | Somme de températures nécessaire à la maturité (°C·j) — vide pour l'olivier |
| `seuil_gel_c` | FLOAT | Température en dessous de laquelle la culture gèle (°C) |
| `besoin_eau_mm` | FLOAT | Besoin en eau sur le cycle (mm) |
| `t_opt_min_c` | FLOAT | Température optimale minimale (°C) |
| `t_opt_max_c` | FLOAT | Température optimale maximale (°C) |
| `seuil_stress_thermique_c` | FLOAT | Température au-delà de laquelle la culture stresse (°C) |
| `stade_concerne` | VARCHAR | Stade auquel s'appliquent les seuils de gel et de stress |
| `source_institut` | VARCHAR | Institut de référence pour la culture |
| `url_t_base`, `url_gdd`, `url_gel`, `url_eau`, `url_t_opt`, `url_stress` | VARCHAR | Une URL par seuil |
| `date_consultation` | DATE | Date de consultation des sources |
| `confiance` | VARCHAR | Niveau de confiance (élevée / moyenne / faible) |
| `remarque` | TEXT | Notes et nuances importantes |

**Contenu :** 10 cultures.

**Source :** `referentiel-cultures-v2.csv`.

**Pourquoi une URL par seuil ?** En sourçant le maïs, nous avons constaté que ses seuils ne viennent pas tous du même endroit : la température de base vient d'ARVALIS, le besoin en eau de la FAO, les températures optimales d'ECOCROP. Une seule colonne source ne pouvait pas le dire..

**Pourquoi `t_plafond_gdd_c` ?** La formule officielle du maïs plafonne la température maximale à 30 °C : au-delà, la chaleur ne fait plus pousser la plante. Sans cette colonne, le plafond serait écrit en dur dans le code pour une seule culture.

---

## Dim_Commune — le territoire

Cette dimension existe pour une raison très concrète : l'API Open-Meteo s'interroge par coordonnées, pas par nom de commune. Il faut donc pour chaque commune retenue connaître son centroïde.

| Colonne | Type | Description |
|---|---|---|
| `id_commune` | CHAR(5) | Code INSEE officiel |
| `nom` | VARCHAR | Nom de la commune |
| `latitude` | FLOAT | Latitude du centroïde (degrés décimaux) |
| `longitude` | FLOAT | Longitude du centroïde (degrés décimaux) |
| `altitude_m` | INT | Altitude de la maille climatique (m) |
| `zone_climatique` | VARCHAR | Zone climatique (océanique, continental…) |
| `departement` | CHAR(3) | Département d'appartenance |

Le code INSEE est stocké en texte de 5 caractères, pas en nombre : certains codes contiennent une lettre (2A004 en Corse) ou commencent par un zéro (01053), qui disparaîtrait dans un champ numérique.

On vise un échantillon de communes aux climats contrastés, espacées d'au moins 10 km pour être sûr qu'elles tombent dans des mailles climatiques différentes — pas besoin de couvrir les 35 000 communes de France pour que l'application ait du sens.

**Sources** : l'API Géo (geo.api.gouv.fr) pour les coordonnées et les codes INSEE. L'altitude n'est pas fournie par l'API Géo, mais Open-Meteo la renvoie dans chaque réponse (champ `elevation` : 38 m à Créteil, 93 m à Reims). Il s'agit de l'altitude de la maille, pas de l'altitude moyenne de la commune.


**Une limite à garder en tête** : la résolution de l'API climat est d'environ 10 km. Deux communes trop proches peuvent tomber dans la même maille et recevoir exactement les mêmes valeurs climatiques — ce n'est pas un bug, c'est une limite qu'il faudra expliquer dans l'application.

---

## Dim_Temps — les horizons

Cette dimension sert à comparer un climat de référence à l'horizon 2050. C'est cette comparaison qui fait la valeur du projet : les chiffres bruts des modèles sont biaisés, mais l'évolution entre deux périodes reste exploitable.

Un horizon n'est pas une année. Dans une projection, 2049 n'est pas une prévision de l'année 2049, c'est une année plausible parmi d'autres. Seule une moyenne sur plusieurs années a un sens climatique. Une ligne de `Dim_Temps` correspond donc à une période, et c'est à ce niveau que sont calculés les indicateurs.

| Colonne | Type | Description |
|---|---|---|
| `id_horizon` | VARCHAR | Identifiant (ex. REF, H2050) |
| `libelle` | VARCHAR | Nom affiché (ex. « Référence 2011-2020 ») |
| `annee_debut` | INT | Première année de la période |
| `annee_fin` | INT | Dernière année de la période |
| `type` | VARCHAR | reference ou projection |

**Horizons retenus :**

| Horizon | Période | Rôle |
|---|---|---|
| Référence | 2011–2020 | Climat récent, simulé par le même modèle |
| 2050 | 2041–2050 | Horizon cible du projet |

Trois raisons à ce choix :

- **Même durée des deux côtés.** Comparer une moyenne sur 30 ans à une moyenne sur 20 ans ne serait pas rigoureux.
- **La borne de l'API.** Les données s'arrêtent en 2050 : l'horizon ne peut pas aller au-delà.
- **Le quota.** Deux périodes de 10 ans coûtent environ 520 appels par commune et par modèle. Une référence de 30 ans ferait plus que doubler ce coût, sur un quota de 10 000 appels par jour partagé par tout l'IUT.

La période de référence est une **sortie de modèle**, pas une mesure. Ce n'est donc pas une normale climatique au sens de l'OMM, qui décrit le climat observé : on compare le modèle à lui-même, avant et après.

---

## Fenetre_Calcul — la bonne période pour chaque indicateur

Le gel n'est un problème qu'au débourrement, pas en plein hiver ; l'échaudage ne compte qu'au remplissage du grain. Sans cette information, on calculerait juste, mais au mauvais moment.

Ces périodes ne peuvent pas être stockées dans `Dim_Temps`, pour deux raisons. D'abord, elles dépendent de la culture : les GDD du blé se comptent d'octobre à juillet, ceux du maïs d'avril à octobre. Ensuite, un même jour appartient à plusieurs fenêtres à la fois : le 15 avril compte pour le gel, l'échaudage, le bilan hydrique et les GDD du maïs. D'où une table séparée.

| Colonne | Type | Description |
|---|---|---|
| `id_culture` | VARCHAR | Culture concernée |
| `indicateur` | VARCHAR | GDD, gel, échaudage, bilan hydrique |
| `mois_debut` | INT | Début de la fenêtre |
| `mois_fin` | INT | Fin de la fenêtre |
| `seuil_specifique` | FLOAT | Seuil propre à cette période, s'il diffère de `Dim_Culture` |

**Fenêtres de calcul par indicateur :**

| Indicateur | Culture | Fenêtre |
|---|---|---|
| GDD | blé | octobre → juillet |
| GDD | maïs | avril → octobre |
| Jours de gel critiques | selon la culture | février → mai (débourrement, floraison) |
| Échaudage | céréales | 1er avril → 30 juin |
| Bilan hydrique | toutes | 1er avril → 31 octobre |

La colonne `seuil_specifique` sert pour les cultures dont le seuil change avec le stade. La vigne, par exemple, supporte −8 °C quand les bourgeons dorment mais seulement −2 °C au débourrement.

---

## Dim_Modele — le modèle climatique

Chaque indicateur calculé doit garder la trace du modèle climatique qui a produit les données sous-jacentes — sans ça, impossible de comparer les modèles entre eux, et donc impossible de montrer l'incertitude.

| Colonne | Type | Description |
|---|---|---|
| `id_modele` | VARCHAR | Code du modèle (ex. MRI_AGCM3_2_S) |
| `nom_complet` | VARCHAR | Nom complet du modèle |
| `institution` | VARCHAR | Institution qui le développe |
| `pays` | VARCHAR | Pays d'origine |
| `resolution_native_km` | INT | Résolution native (km) |
| `variables_disponibles` | TEXT | Variables confirmées disponibles |
| `date_verification` | DATE | Date du dernier test de disponibilité |
| `remarque` | TEXT | Notes (ex. EC_Earth3P_HR à tester) |

**Modèles retenus actuellement :**

| Modèle | Institution | Résolution | Statut |
|---|---|---|---|
| MRI_AGCM3_2_S | Meteorological Research Institute, Japon | 20 km | Modèle de référence |
| CMCC_CM2_VHR4 | CMCC, Italie | 30 km | Modèle de comparaison |

Pourquoi deux modèles, et pas un seul ? Parce qu'un modèle unique donne une fausse impression de certitude. C'est l'écart entre les deux qui traduit l'incertitude réelle des projections — et c'est cette fourchette-là que l'application devra montrer à l'utilisateur, plutôt qu'un chiffre unique qui laisserait croire à une précision qu'on n'a pas.

Notre test sur Reims en 2049 le confirme : 28 jours de gel avec MRI_AGCM3_2_S, 11 avec CMCC_CM2_VHR4, pour la même commune et la même année.

La colonne `date_verification` existe parce qu'une disponibilité constatée un jour n'est pas garantie : EC_Earth3P_HR a déjà renvoyé des données vides par le passé.

---

## Récapitulatif — ce que chaque dimension apporte à Fact_Indicateur

| Dimension | Question | Clé étrangère dans Fact_Indicateur |
|---|---|---|
| Dim_Culture | Pour quelle culture ? | `id_culture` |
| Dim_Commune | Pour quelle commune ? | `id_commune` |
| Dim_Temps | Sur quel horizon ? | `id_horizon` |
| Dim_Modele | Avec quel modèle climatique ? | `id_modele` |

Un fait dans `Fact_Indicateur` est donc toujours identifié par la combinaison commune × culture × horizon × modèle. `Fenetre_Calcul` n'est pas une clé du fait : elle sert au moment du calcul, pour savoir quels jours prendre en compte.
