# Jeu de séries de test

SAÉ 3.01 « Climat & Cultures », équipe 9, pôle DATA. Jalon 2.

## Ce que contient ce dossier

| Fichier | Contenu |
|---|---|
| `series-reims-2049-complete.csv` | Reims, année 2049, les deux modèles. 730 lignes |
| `series-reims-mars-2049.csv` | Extrait de mars 2049, 62 lignes, vérifiable à la main |
| `series-reims-2049-mars-valeurs-manquantes.csv` | Mars 2049, les deux modèles, cinq cases vidées chez MRI. 62 lignes |
| `series-reims-2049-ete-sans-gel.csv` | Juin à août 2049, les deux modèles, sans aucune case vide. 184 lignes |
| `README.md` | Les valeurs attendues et comment les contrôler |

Les données sont réelles : elles proviennent de l'API Open-Meteo Climate,
interrogée le 30 septembre 2026 sur le centroïde de Reims (49.2535 / 4.0551).
La maille renvoyée est centrée sur 49.30 / 4.00, à 93 mètres d'altitude.

## Format

C'est le format du contrat d'interface DEV vers DATA.

```
id_commune;date;id_horizon;id_modele;t_min;t_max;t_moy;precip
51454;2049-03-01;PROJ_2041_2050;MRI_AGCM3_2_S;-3.1;2.0;-0.6;6.20
```

| Champ | Type | Règle |
|---|---|---|
| `id_commune` | texte, 5 caractères | code INSEE, zéro initial conservé |
| `date` | ISO 8601 | `AAAA-MM-JJ`, jamais le format français |
| `id_horizon` | texte | clé de `Dim_Temps` |
| `id_modele` | texte | clé de `Dim_Modele` |
| `t_min`, `t_max`, `t_moy` | décimal | degrés Celsius, séparateur point |
| `precip` | décimal | millimètres par jour |

Séparateur point-virgule, encodage UTF-8, une valeur manquante se note par
une case vide et jamais par un zéro.

## Pourquoi mars 2049

L'extrait court n'est pas choisi au hasard. Mars 2049 contient quatre jours
sous zéro degré chez MRI, dont **un seul** sous moins deux degrés. C'est donc
le mois qui démontre que le seuil change la réponse.

Jours sous zéro chez MRI_AGCM3_2_S :

| Date | t_min |
|---|---|
| 2049-03-01 | −3,1 °C |
| 2049-03-20 | −0,4 °C |
| 2049-03-21 | −0,7 °C |
| 2049-03-22 | −0,5 °C |

CMCC_CM2_VHR4 n'en compte aucun sur le même mois.

## Valeurs attendues, sur l'extrait de mars 2049

Ces valeurs testent les **formules**, pas les fenêtres de chaque culture.
Elles sont toutes calculées sur une même fenêtre, mars à mai : tout
l'extrait est donc retenu, et seul le seuil (ou la base) change d'une ligne
à l'autre.

Les cultures citées dans les tableaux indiquent d'où vient chaque seuil.
Elles ne veulent pas dire que le module applique ces calculs à ces dates : en
production, chaque culture a sa propre fenêtre (table `Fenetre_Calcul`). Le
gel du maïs, par exemple, y est compté en septembre et octobre.

### Jours de gel, selon le seuil

| Seuil | Culture concernée | MRI | CMCC |
|---|---|---|---|
| −4 °C | blé tendre, gel d'épi | **0** | **0** |
| −2 °C | vigne, débourrement | **1** | **0** |
| 0 °C | maïs, dégâts aux feuilles | **4** | **0** |

C'est le test le plus parlant du jeu. La même série, le même mois, trois
réponses différentes selon le seuil. Un programme qui renverrait le même
nombre pour les trois serait faux.

### Degrés-jours, selon la base et le plafond

| Base | Plafond | Culture | MRI | CMCC |
|---|---|---|---|---|
| 0 | aucun | blé tendre | **218,6** | **291,5** |
| 6 | 30 | maïs | **53,5** | **105,8** |
| 10 | aucun | vigne | **7,7** | **24,3** |

### Cumul de précipitations

| | MRI | CMCC |
|---|---|---|
| mars 2049 | **72,6 mm** | **80,3 mm** |

## Cas limites

Quatre cas limites sont couverts : la canicule, aucun jour sous le seuil
de gel, la valeur manquante et la fenêtre que la série ne couvre pas.

### La canicule

Couverte par les 16 et 28 jours au-dessus de 30 °C sur l'année complète
(voir plus bas, chiffres cités dans le SQL).

### Aucun jour sous le seuil de gel

Aucune donnée inventée : CMCC_CM2_VHR4 ne compte **aucun** jour à −4 °C ou
moins sur toute l'année 2049. Ce n'est pas une année sans gel : son minimum
est −2,5 °C, donc à −2 °C il compte un jour. Le résultat dépend du seuil
autant que du modèle.

| Seuil | MRI | CMCC |
|---|---|---|
| −4 °C, année entière | 4 | **0** |
| −2 °C, année entière | 8 | 1 |
| 0 °C, année entière | 28 | 11 |

Le gel compte en strict : un jour est compté si `t_min` est **strictement
inférieur** au seuil. Chez MRI, deux jours valent exactement un seuil : le
12 février (−2,0 °C) et le 23 février (−4,0 °C). Ils comptaient avant le
changement d'opérateur (issue #75), d'où 9 et 5 jours en comptage « inférieur
ou égal » ; ils ne comptent plus, d'où 8 et 4. À 0 °C aucun jour ne tombe
pile, et chez CMCC aucun non plus : ces valeurs ne changent pas.

Le module doit renvoyer l'entier `0`, pas `None`. Zéro jour sous le seuil
est une mesure réelle. `None` voudrait dire « non calculable », et finirait en
`NULL` dans `Fact_Indicateur`.

### La valeur manquante

`series-reims-2049-mars-valeurs-manquantes.csv` reprend les 62 lignes de mars
2049, les deux modèles. Les valeurs présentes sont celles de l'export ; cinq
cases ont été vidées, toutes chez MRI :

| Date | Champ vidé | Valeur d'origine | Cas couvert |
|---|---|---|---|
| 2049-03-01 | `t_max` | 2,0 | `t_max` vide, `t_min` valide et sous zéro (−3,1) |
| 2049-03-03 | `t_min` | 0,4 | `t_min` vide, qui ne doit pas devenir 0 |
| 2049-03-04 | `t_min` | 0,4 | idem |
| 2049-03-05 | `t_max` | 10,3 | `t_max` vide, `t_min` valide au-dessus de zéro |
| 2049-03-07 | `precip` | 19,16 | pluie vide sur un jour aux deux températures |

CMCC_CM2_VHR4 n'a aucune case vide dans ce fichier : c'est le témoin.

Une ligne n'est écartée que si `t_min` et `t_max` manquent toutes les deux.
Ce n'est le cas d'aucune ligne ici. Chaque indicateur ne lit que ce dont il a
besoin : le gel lit `t_min`, l'échaudage lit `t_max`, les degrés-jours et
l'ET0 ont besoin des deux et sautent le jour s'il en manque une.

| Contrôle (MRI, mars) | Attendu | Pourquoi | Nature |
|---|---|---|---|
| `precip` du 7 mars | **None** | une case vide ne devient jamais 0 | contrat, définitif |
| `t_min` des 3 et 4 mars | **None** | idem | contrat, définitif |
| jours lus | **31** | aucune ligne n'a ses deux températures vides | comportement actuel |
| gel à −2 °C | **1** | le 1er mars garde sa `t_min` de −3,1 | comportement actuel |
| gel à 0 °C | **4** | les 3 et 4 mars ne comptent pas, faute de `t_min` | comportement actuel |
| cumul de pluie | **53,4 mm** | 72,6 − 19,16 | comportement actuel |
| degrés-jours base 0 | **203,4** | 218,6 moins les 1er, 3, 4 et 5 mars, sautés | comportement actuel |
| gel à 0 °C chez CMCC | **0** | témoin sans lacune | contrat, définitif |

Avant la correction du module, une seule température vide faisait jeter la
ligne entière. On lisait alors 27 jours, 0 jour de gel à −2 °C, 3 à 0 °C et
37,5 mm de pluie : les quatre lignes incomplètes emportaient 15,89 mm avec
elles, et le seul jour sous −2 °C disparaissait sans signal.

Les lignes « contrat » sont vérifiées par `test_valeur_manquante_jamais_lue_comme_zero`,
`test_precipitation_vide_ignoree_dans_le_cumul`, `test_tmax_vide_tmin_valide_compte_pour_le_gel`,
`test_tmin_vide_jamais_lue_comme_zero` et `test_modele_sans_lacune_intact`.
Les lignes « comportement actuel » sont isolées dans
`test_comportement_actuel_lacunes_a_corriger_j3`. Elles figent un défaut
qui reste connu : les degrés-jours sautent les jours incomplets **sans
avertissement**, et le résultat a l'air complet alors qu'il ne l'est pas.
Ce test devra échouer volontairement quand le contrôle de couverture
arrivera au jalon 3.

### La fenêtre que la série ne couvre pas

`series-reims-2049-ete-sans-gel.csv` contient juin, juillet et août 2049,
les deux modèles, sans case vide. Calculé sur la fenêtre mars à mai, le gel
vaut **0** et le module émet un avertissement de fenêtre non couverte. Le
zéro seul ne suffit pas : c'est l'avertissement qui dit qu'il ne mesure
rien. Vérifié par `test_fenetre_vide_zero_et_avertissement`.

Ces valeurs ont été recalculées par un comptage `awk` indépendant du
module, et concordent.

### Un jour posé exactement sur le seuil

Les séries réelles ne contiennent presque aucun jour à la valeur exacte d'un
seuil, donc elles ne montrent pas le sens de la comparaison. Ce cas est testé
sur des séries minimales aux valeurs choisies à la main, pas sur ce jeu :

| Test | Valeurs | Strict | Large |
|---|---|---|---|
| `test_gel_jour_pose_sur_le_seuil` | t_min −4,1 / −4,0 / −3,9 / 0,0, seuil −4,0 | 1 jour (`<`) | 2 jours (`<=`) |
| `test_stress_jour_pose_sur_le_seuil` | t_max 34,9 / 35,0 / 35,1, seuil 35,0 | 1 jour (`>`) | 2 jours (`>=`) |

`test_operateurs_des_cultures_dans_indicateurs_culture` vérifie que chaque
culture applique l'opérateur de son référentiel au bord de son seuil, et
`test_operateur_inconnu_leve_une_erreur` qu'un sens inconnu ou vide n'est
jamais remplacé en silence. Un opérateur « indetermine » (la source ne dit
pas le sens) est compté en strict, par convention du cours et non d'après une
source.

## Comment vérifier à la main

Ouvrez `series-reims-mars-2049.csv` dans un tableur, filtrez sur un modèle.

**Les jours de gel** se comptent directement : combien de lignes ont `t_min`
strictement inférieur au seuil. Quatre lignes sous zéro chez MRI, une seule sous
moins deux.

**Les degrés-jours** se calculent ligne à ligne :

```
contribution du jour = max( (t_min + min(t_max, plafond)) / 2 - base , 0 )
```

Pour le 1er mars chez MRI, base 10 : `(-3,1 + 2,0) / 2 - 10 = -10,55`, donc
une contribution de zéro. Une journée froide ne retire jamais de degrés-jours.

Pour le 7 mars chez MRI, `t_min = 4,3` et `t_max = 13,7`, base 10 :
`(4,3 + 13,7) / 2 - 10 = -1`, encore zéro.

Pour le 9 mars, `t_min = 6,7` et `t_max = 15,1` : `(6,7 + 15,1) / 2 - 10 = 0,9`.
Celui-là compte.

La somme des 31 contributions donne 7,7.

## Reproduire avec le module

Les valeurs ci-dessus se vérifient automatiquement, depuis la racine du
projet :

```
python test/test_indicateurs.py
```

Le script appelle les fonctions du module avec la fenêtre mars à mai et
compare chaque résultat aux tableaux de ce fichier. Il contrôle aussi les
chiffres cités dans les commentaires SQL (28 et 11 jours de gel sur
l'année, dont 22 en janvier-février chez MRI). Les fonctions doivent
retrouver exactement ces valeurs. Si elles en donnent d'autres, c'est le
module qui a tort, pas le jeu de test.

La commande suivante, elle, applique les vraies fenêtres de chaque culture
sur l'année complète. Elle ne réaffiche donc pas les tableaux ci-dessus :

```
python indicateurs.py data/test/series-reims-2049-complete.csv
```

Sur l'extrait de mars seul, la plupart des fenêtres ne sont pas couvertes.
Le module le signale par un avertissement, et les verdicts affichés n'ont
alors pas de sens.

## Deux limites assumées

**Une seule année.** Un horizon se moyenne sur dix ans. Ce jeu sert à
valider les formules, pas à produire un résultat publiable. Les indicateurs
qui portent sur une fenêtre à cheval sur deux années, comme les degrés-jours
du blé d'octobre à juillet ou le gel de la vigne en dormance de novembre à
février, ne sont pas calculables ici : le module émet un avertissement dans
ce cas.

**Les modèles sous-estiment le gel.** D'environ un facteur deux, parce que
les séries sont corrigées sur les moyennes et adoucissent les nuits froides.
Ces comptages servent à comparer deux horizons entre eux, jamais à annoncer
un nombre de jours de gel en valeur absolue.
