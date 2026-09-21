# Repérage des sources — pôle DATA (J0)

SAÉ 3.01 Climat & Cultures
Auteurs : MARDAUS, PARIMELALAGAN, SINOUVASSANE
Mise à jour : 21/09/2026

Ce document liste d'où viennent nos données et ce qu'elles valent.
Les variables retenues sont détaillées dans `J1-variables-meteo-necessaires.md`,
le modèle de données dans `MODELE-DIMENSIONNEL-esquisse.md`.


## 1. Données climatiques

### Open-Meteo Climate API

Adresse : https://climate-api.open-meteo.com/v1/climate

C'est la source principale de l'application. L'API est gratuite et ne demande pas de
clé. Elle fournit des projections journalières de 1950 à 2050, issues des modèles CMIP6
et ramenées à une résolution d'environ 10 km. Les données sont sous licence CC BY 4.0 :
il faudra créditer Open-Meteo dans l'interface.

### Nos tests

Premier test le 11/09/2026 sur Créteil, modèle MRI_AGCM3_2_S, année 2049.

URL de l'appel : ___

L'API a renvoyé 365 lignes, sans aucune valeur manquante. Nous avions demandé le point
48,79 / 2,45 ; l'API a répondu pour le point 48,80 / 2,50, qui correspond au centre de
la maille utilisée, soit un écart d'environ 3,8 km. Elle renvoie aussi l'altitude de la
maille (38 m). Les températures sont en °C, les précipitations et l'ET0 en mm.

Deuxième test le 14/09/2026 sur Reims, avec deux modèles (MRI_AGCM3_2_S et
CMCC_CM2_VHR4), année 2049. Altitude renvoyée : 93 m.

En exportant ce test en CSV, nous avons remarqué trois choses à prévoir dans le
contrat d'interface avec le pôle DEV : le séparateur est un point-virgule, les dates
sont au format JJ/MM/AAAA, et le nom du modèle est ajouté à la fin de chaque colonne
quand on demande plusieurs modèles.

### Le quota

L'API est limitée à 10 000 appels par jour, comptés par adresse IP. À l'IUT, toutes les
équipes partagent donc probablement le même quota. Un appel coûte plus cher quand il
porte sur une longue période : environ 26 unités pour une année, et environ 520 pour une
commune sur deux périodes de 10 ans.

Nous nous fixons trois règles : tester sur une seule année, demander toutes les
variables dans le même appel, et garder les réponses en cache.

### Sources pour valider nos résultats

- DRIAS (Météo-France) : projections officielles pour la France, drias-climat.fr
- Le projet ORACLE, sur DRIAS : formules officielles des indicateurs agricoles, avec
  leur période de calcul
- Climadiag Agriculture (Météo-France) : indicateurs déjà calculés,
  climadiag-agriculture.fr


## 2. Données agronomiques (les seuils des cultures)

Il n'existe pas de base officielle qui regroupe tous les seuils. Les valeurs changent
selon la variété, le stade de la plante et la région. Il faut donc croiser au moins
deux sources et toujours les citer.

| Source | Ce qu'elle donne | Fiabilité |
|---|---|---|
| ECOCROP (FAO) | températures min, optimales et max | moyenne : base arrêtée vers 2015, données mondiales |
| FAO-56 | coefficients pour calculer les besoins en eau | élevée : document de référence |
| STICS (INRAE) | paramètres par culture | élevée, mais demande une calibration |
| ARVALIS | blé, orge, maïs, pomme de terre | élevée |
| Terres Inovia | colza, tournesol, soja | élevée |
| IFV | vigne | élevée |
| ITB | betterave | élevée |
| France Olive | olivier | à vérifier |
| Chambres d'agriculture | valeurs régionales | moyenne : valable localement seulement |

### Ce que nous avons appris en cherchant

Les instituts publient gratuitement des conseils de saison, mais leurs tableaux de
référence sont souvent dans des publications payantes. Pour le maïs, nous avons
consulté une douzaine de pages ARVALIS sans trouver de besoin en eau de référence.

Les fiches accidents d'ARVALIS sont en revanche utiles pour les seuils de gel, car
elles donnent le stade concerné. Elles précisent aussi qu'une température de 0 °C sous
abri peut correspondre à −2 °C au champ, ce qui compte pour nous puisque les données
Open-Meteo sont mesurées à 2 m.

Terres Inovia et l'ITB publient des guides de culture complets en accès libre.

Nous avons écarté les sites de semenciers, de fournisseurs d'engrais, de logiciels
agricoles et de jardineries : ils ne citent pas leurs sources et ont un intérêt
commercial.

Nous avons aussi appris à vérifier qu'on compare bien la même chose. Le maïs fourrage
n'est pas le maïs grain, le tournesol semé après une céréale n'est pas le tournesol
classique, et la conservation des betteraves après récolte ne dit rien de leur
résistance au gel au champ.


## 3. Données géographiques (les communes)

- API Géo (geo.api.gouv.fr) : code INSEE, nom, coordonnées du centre, population
- Open-Meteo : l'altitude, que l'API Géo ne donne pas
- INSEE : liste officielle des communes

Test de l'API Géo réalisé le ___ :

https://geo.api.gouv.fr/communes?code=___&fields=nom,code,centre,population&format=json

Trois points à respecter :

1. Le code INSEE doit être stocké en texte sur 5 caractères. Certains codes contiennent
   une lettre (2A004 en Corse) ou commencent par un zéro (01053), qui disparaîtrait
   dans un champ numérique.
2. L'API Géo donne les coordonnées dans l'ordre longitude puis latitude. Open-Meteo
   attend l'ordre inverse. Une inversion ne provoque aucune erreur, elle donne juste un
   point au mauvais endroit.
3. Les communes choisies doivent être éloignées d'au moins 10 km, sinon elles tombent
   dans la même maille et donnent les mêmes résultats.


## 4. Limites des données

### Les modèles sous-estiment le gel

D'après la documentation du projet, les modèles annoncent environ 15 jours de gel par
an à Toulouse sur 2011-2020, alors qu'il y en a eu environ 31. Les séries sont
ajustées sur les températures moyennes, ce qui adoucit les nuits les plus froides.

Notre indicateur de jours de gel sera donc faux en valeur absolue. En revanche,
l'évolution entre deux périodes reste utilisable. L'application montrera d'abord
l'évolution, affichera un avertissement, et comparera toujours deux modèles.

### Deux modèles ne donnent pas le même résultat

Sur Reims en 2049, avec les mêmes paramètres :

| | MRI_AGCM3_2_S | CMCC_CM2_VHR4 |
|---|---|---|
| Température moyenne | 12,1 °C | 12,8 °C |
| Jours de gel (sous 0 °C) | 28 | 11 |
| Jours sous −2 °C | 9 | 1 |
| Jours au-dessus de 30 °C | 16 | 28 |
| Précipitations | 806 mm | 762 mm |

Les moyennes sont proches, mais les valeurs extrêmes sont très différentes. Or ce sont
elles qui décident si une culture est viable. C'est pour cela que nous afficherons une
fourchette plutôt qu'un seul chiffre.

### La définition compte

Sur Créteil en 2049, on trouve 17 jours de gel si on compte les jours strictement sous
0 °C, et 21 si on inclut les jours à 0 °C. Chaque indicateur doit donc avoir une
définition précise.

### L'évapotranspiration (ET0)

La documentation du projet indique que l'API ne fournit pas l'ET0. Nos tests montrent
le contraire : elle est disponible sous le nom `et0_fao_evapotranspiration_sum`.

Les valeurs semblent cependant trop élevées : 1 405 mm sur l'année à Créteil, avec des
pointes à 12,5 mm par jour, alors qu'on attendrait plutôt 700 à 800 mm (ordre de
grandeur à confirmer par une source). Nous calculerons donc l'ET0 avec la méthode de
Hargreaves et comparerons les deux.

### Autres limites

- L'API ne propose qu'un seul scénario d'émissions : nous comparons des modèles, pas
  des scénarios.
- La maille de 10 km lisse le relief.
- Les données passées sont elles aussi des simulations, pas des mesures réelles.
- La disponibilité des variables peut changer selon le modèle. EC_Earth3P_HR a déjà
  renvoyé des données vides : il faudra le tester avant de l'utiliser.


## 5. Cultures retenues

Les 10 cultures et leurs seuils sont dans `referentiel-cultures-v2.csv`. Nous les
avons choisies pour avoir des comportements variés (cultures d'hiver, d'été,
pérennes), des cultures importantes en France, et un institut de référence pour
chacune.

Question en suspens : l'olivier n'a pas de somme de températures définie, car c'est
une culture pérenne. Nous devons décider si nous le gardons.


## 6. Questions pour la suite

- Où stocker les périodes de calcul de chaque indicateur ? Le gel n'est dangereux pour
  la vigne qu'au débourrement, pas en hiver.
- Faut-il une table séparée pour les sources ? Pour le maïs, les seuils viennent de
  trois organismes différents.
- Le besoin en eau dépend du climat local : peut-on vraiment le stocker comme une
  valeur fixe ?
- Quelle base de données choisir ? Le choix change la façon d'écrire les requêtes sur
  les dates.
- Faut-il ajouter un indicateur de vernalisation pour le blé d'hiver ?


## 7. Documents non reçus

Demandés à l'encadrement le ___ :
- le fichier communes-reference.csv (16 communes)
- le kit de démarrage (scripts de vérification et de test)
- la version à jour du document sur les modèles climatiques
