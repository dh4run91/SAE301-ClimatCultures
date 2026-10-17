# Jeu de séries de test

SAÉ 3.01 « Climat & Cultures », équipe 9, pôle DATA. Jalon 2.

## Ce que contient ce dossier

| Fichier | Contenu |
|---|---|
| `series-reims-2049-complete.csv` | Reims, année 2049, les deux modèles. 730 lignes |
| `series-reims-mars-2049.csv` | Extrait de mars 2049, 62 lignes, vérifiable à la main |
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

## Comment vérifier à la main

Ouvrez `series-reims-mars-2049.csv` dans un tableur, filtrez sur un modèle.

**Les jours de gel** se comptent directement : combien de lignes ont `t_min`
inférieur ou égal au seuil. Quatre lignes sous zéro chez MRI, une seule sous
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
python tests/test_indicateurs.py
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
