# Notre modèle de données — l'essentiel

SAÉ 3.01 « Climat & Cultures » · pôle DATA

---

## L'idée en une phrase

> **On ne stocke pas de la météo. On stocke des réponses à des questions.**

La météo brute reste dans l'API. Ce qu'on garde en base, c'est le résultat du
croisement entre cette météo et les seuils d'une plante.

---

## Une donnée seule ne dit rien

« −3 °C le 5 avril » → c'est grave ou pas ? **Impossible à dire.**

Ajoutez « la vigne gèle sous −2 °C au débourrement », et vous obtenez une information
utile : **« gel dommageable pour la vigne »**.

```
  −3 °C le 5 avril    ⊗    vigne : −2 °C    =    gel dommageable
     (l'API)                 (l'IFV)            (ce qu'on stocke)
```

**Toute notre base n'est que la mise en tables de ce schéma.**

---

## Quatre dimensions, parce que la question a quatre morceaux

> « Pourrai-je planter **de la vigne** *(quoi)* **à Reims** *(où)* **en 2050** *(quand)* ? »

| Dimension | Répond à | Contient |
|---|---|---|
| `Dim_Culture` | quoi ? | les seuils de chaque plante |
| `Dim_Commune` | où ? | les coordonnées, l'altitude |
| `Dim_Temps` | quand ? | les horizons (périodes de ~10 ans) |
| `Dim_Modele` | selon quelle simulation ? | les modèles climatiques |

Au centre, **`Fact_Indicateur`** contient les résultats calculés.

```
              Dim_Commune
                   │
  Dim_Culture ──► FACT_INDICATEUR ◄── Dim_Temps
                   │
              Dim_Modele
```

---

## Pourquoi la 4e dimension ? (notre preuve)

Même commune, même culture, même année. Seul le modèle change :

| Reims, 2049 | MRI_AGCM3_2_S | CMCC_CM2_VHR4 |
|---|---|---|
| Jours de gel | **28** | **11** |

Sans le modèle dans la clé, les deux lignes se contredisent et il faudrait en effacer
une. **Cet écart n'est pas un défaut : c'est la mesure de l'incertitude.** On affiche
une fourchette, pas un chiffre.

---

## Trois choses qu'on a vérifiées nous-mêmes

**Les chiffres des modèles sont faux.** Ils sous-estiment le gel d'un facteur 2. On
affiche donc l'**évolution** entre deux périodes, jamais un chiffre brut seul.

**L'ET0 contredit nos documents.** Ils disent qu'elle n'existe pas dans l'API ; on l'a
trouvée. Mais ses valeurs semblent trop élevées → on la recalculera autrement.

**Les seuils fournis ne sont pas sourcés.** Presque tous portent `a_completer`. D'où une
table à part qui trace source, URL, date et niveau de confiance.

---

## Le vocabulaire à ne pas confondre

| | Quoi | Stocké ? | Par qui |
|---|---|---|---|
| **Série climatique** | données brutes de l'API | non | DEV |
| **Fait** | indicateur calculé | oui | DATA |

> **DEV produit les séries, DATA produit les faits.**

---

## À retenir pour la soutenance

1. Une donnée brute ne dit rien — l'info naît du croisement donnée × règle métier.
2. Le climat ne dépend pas de la culture : la culture est une grille de lecture.
3. Un indicateur = une règle **et** une période (le gel de janvier ne compte pas).
4. Deux modèles ne disent pas la même chose — et ça s'affiche.
5. Les chiffres sont faux, la tendance ne l'est pas.
