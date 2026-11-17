# Identification des variables météo nécessaires

SAÉ 3.01 « Climat & Cultures » — Pôle DATA — J1 (S39)
Source : Open-Meteo Climate API — `https://climate-api.open-meteo.com/v1/climate`

---

## 1. Quelles variables ?

Quatre variables suffisent à couvrir l'ensemble des indicateurs prévus. Une cinquième est utile mais son statut demande une vérification (voir §4).

| Nom exact du paramètre API | Unité | Rôle |
|---|---|---|
| `temperature_2m_min` | °C | température minimale journalière (Tn) |
| `temperature_2m_max` | °C | température maximale journalière (Tx) |
| `temperature_2m_mean` | °C | température moyenne journalière |
| `precipitation_sum` | mm | cumul de précipitations journalier |
| `et0_fao_evapotranspiration_sum` | mm | évapotranspiration de référence — plausibilité à vérifier (voir §4) |

Ces variables sont demandées via le paramètre `daily` de l'appel :

```
daily=temperature_2m_min,temperature_2m_max,temperature_2m_mean,
      precipitation_sum,et0_fao_evapotranspiration_sum
```

**Disponibilité selon les modèles** : les quatre premières variables sont disponibles sur les sept modèles proposés par l'API. Le choix des modèles à comparer n'est donc pas contraint par les besoins des indicateurs. D'autres variables exposées par l'API (humidité relative, vent, rayonnement, humidité du sol, neige, pression, point de rosée) présentent en revanche une disponibilité inégale selon les modèles, mais aucune n'est nécessaire aux indicateurs retenus.

---

## 2. Sur quelle période ?

| Élément | Valeur |
|---|---|
| Couverture de l'API | 1950 → 2050, au pas journalier |
| Horizon de référence (climat actuel) | à définir en J2 dans `Dim_Temps` |
| Horizon cible du projet | 2050 |

La comparaison entre un horizon de référence et l'horizon 2050 est ce qui produit la valeur du projet : le décalage des zones de culture.

**Les fenêtres de calcul diffèrent selon l'indicateur.** Un indicateur ne se calcule pas sur l'année entière mais sur la période où la culture y est sensible : le gel n'est critique qu'au débourrement, l'échaudage qu'au remplissage du grain. Ces fenêtres sont détaillées au §3 et devront être portées par la dimension temps.

---

## 3. Pour quels indicateurs ?

| Indicateur | Variables mobilisées | Seuil croisé (`Dim_Culture`) | Fenêtre de calcul |
|---|---|---|---|
| GDD / maturité | `temperature_2m_min` + `temperature_2m_max` (ou `temperature_2m_mean`) | `t_base_c`, `gdd_maturite_cj` | saison de culture ; octobre → juillet pour le blé |
| Jours de gel | `temperature_2m_min` | `seuil_gel_c` | fenêtre sensible : débourrement, floraison |
| Stress thermique / échaudage | `temperature_2m_max` | `seuil_stress_thermique_c` | 1er avril → 30 juin pour les céréales |
| Bilan hydrique | `precipitation_sum` + ET0 | `besoin_eau_mm` | 1er avril → 31 octobre |
| Décalage des zones de culture | combinaison des précédents | combinaison | par horizon comparé |

Formules retenues, publiées par le portail DRIAS dans le cadre du projet ORACLE et transposées à la nomenclature Open-Meteo :

- GDD base 0 (blé) : `max((Tn + Tx)/2 − 0, 0)`
- GDD base 6 avec plafonnement (maïs) : `max((Tn + min(Tx, 30))/2 − 6, 0)`
- Jours de gel : nombre de jours où `Tn ≤ seuil_gel_c`
- Échaudage : nombre de jours où `Tx > seuil_stress_thermique_c`
- Bilan hydrique : `Σ (precipitation_sum − ET0)` comparé à `besoin_eau_mm`

Le plafonnement de Tx à 30 °C pour le maïs traduit le fait qu'au-delà de ce seuil la chaleur ne contribue plus à la croissance. Sur une journée à Tn = 14 °C et Tx = 38 °C, l'écart entre les deux méthodes atteint 4 degrés-jours (20 sans plafond contre 16 avec), écart qui se cumule sur une saison comportant plusieurs épisodes caniculaires.

---

## 4. Point de vérification sur l'ET0

La documentation du projet indique que `et0_fao_evapotranspiration` renvoie une valeur nulle sur tous les modèles, et recommande de l'estimer par la méthode de Hargreaves.

Le test réalisé ne confirme pas ce constat. La variable renvoie des valeurs exploitables sur les deux modèles interrogés et sur toute l'année testée, sans aucune valeur manquante (1er janvier 2049 : 1,09 mm pour MRI_AGCM3_2_S, 1,17 mm pour CMCC_CM2_VHR4).

**Hypothèse la plus probable : un nom de paramètre différent.** La colonne renvoyée par l'API s'intitule `et0_fao_evapotranspiration_sum`, avec un suffixe. Un test portant sur `et0_fao_evapotranspiration`, sans suffixe, interrogerait un paramètre inexistant — ce qui expliquerait le constat de la documentation sans qu'il y ait eu d'évolution de l'API. La question est portée à l'attention de l'encadrement.

**Mais la disponibilité ne vaut pas plausibilité.** Sur Créteil, année 2049, modèle MRI_AGCM3_2_S, le cumul annuel atteint 1 405 mm, avec des maxima journaliers à 12,55 mm. Pour un climat tempéré océanique du Bassin parisien, l'ET0 de référence annuelle attendue se situe plutôt entre 700 et 800 mm, et les pointes estivales dépassent rarement 5 à 6 mm par jour. Les valeurs renvoyées paraissent donc surestimées d'un facteur proche de 2.

Ce constat rejoint le biais documenté sur les extrêmes de température : une variable peut être servie par l'API sans être directement exploitable.

**Décision retenue.** L'ET0 native n'est pas utilisée en l'état. L'ET0 sera estimée par la méthode de Hargreaves à partir des seules températures, et les deux séries seront comparées sur un cas de test avant d'arbitrer. Le bilan hydrique sera assorti d'une mention de l'incertitude sur l'ET0, quelle que soit la méthode retenue.

## 5. Choix des modèles climatiques

Deux modèles sont retenus, conformément à l'exigence de comparer au moins deux simulations pour mesurer l'incertitude des projections.

| Modèle | Origine | Résolution native | Justification du choix |
|---|---|---|---|
| **MRI_AGCM3_2_S** | Meteorological Research Institute, Japon | 20 km | Modèle de référence : le plus complet en variables disponibles, et la résolution native la plus fine des sept modèles proposés. Recommandé par défaut dans la documentation du projet. |
| **CMCC_CM2_VHR4** | Centro Euro-Mediterraneo sui Cambiamenti Climatici, Italie | 30 km | Modèle de comparaison : développé par une équipe distincte, avec des choix de paramétrisation indépendants. Fournit l'intégralité des variables nécessaires aux indicateurs retenus. |

Le choix d'un second modèle issu d'une autre institution est délibéré : comparer deux simulations partageant les mêmes hypothèses de modélisation reviendrait à sous-estimer l'incertitude réelle.

### Ce que révèle la comparaison — exemple sur Reims, année 2049

| Grandeur | MRI_AGCM3_2_S | CMCC_CM2_VHR4 | Écart |
|---|---|---|---|
| Température moyenne annuelle | 12,1 °C | 12,8 °C | 0,7 °C |
| Jours de gel (Tn < 0 °C) | 28 jours | 11 jours | **17 jours** |
| Jours chauds (Tx > 30 °C) | 16 jours | 28 jours | **12 jours** |
| Cumul de précipitations | 806 mm | 762 mm | 44 mm |

Cet exemple illustre pourquoi un modèle unique ne suffit pas. Sur la moyenne annuelle, les deux simulations sont proches et pourraient laisser croire à un consensus. Sur les extrêmes, en revanche, elles divergent fortement — et dans des directions opposées selon l'indicateur : CMCC_CM2_VHR4 projette un climat nettement moins gélif mais plus chaud en été, quand MRI_AGCM3_2_S décrit une année aux amplitudes plus marquées.

Or ce sont précisément les extrêmes, et non les moyennes, qui déterminent la viabilité d'une culture. Un verdict fondé sur le seul CMCC_CM2_VHR4 conclurait à un risque de gel printanier faible pour la vigne ; le même verdict fondé sur MRI_AGCM3_2_S serait bien plus prudent. L'application devra donc restituer une fourchette plutôt qu'une valeur unique, et expliciter que cette fourchette traduit un désaccord entre modèles, non une imprécision de mesure.


## 6. Qualité des données et limites connues de l'API

**Un seul scénario d'émission (≈ RCP 8.5)** — on compare des 
modèles entre eux pour mesurer l'incertitude, pas des scénarios. 
Pour comparer des scénarios RCP différents, il faudrait DRIAS.

**Résolution spatiale ~10 km** — le relief est lissé. Deux communes 
proches peuvent tomber dans la même maille et recevoir les mêmes 
valeurs. À signaler à l'utilisateur.

**Disponibilité variable selon les modèles** — EC_Earth3P_HR a déjà 
renvoyé des données vides. La disponibilité de chaque variable doit 
être vérifiée pour chaque modèle avant de lancer les calculs.
