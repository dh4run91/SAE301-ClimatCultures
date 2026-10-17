# 📓 Journal d'usage de l'IA — Équipe `9`

> **SAÉ 3.01 « Climat & Cultures »** — à tenir **au fil de l'eau**, versionné dans le dépôt Git, annexé au livrable final.
> Membres : 

 `[Sabiledine BOUAFIA]`  
 `[Remy CHAMBI LEBLANC]`  
 `[Adrien CREPIEUX]`  
 `[Sebastien MARDAUS]`  
 `[Rakul PARIMELALAGAN]`  
 `[Dharun SINOUVASSANE]`  

## Rappel express des règles
- L'IA est un **copilote, pas un sous-traitant**. 🔑 *« Si tu ne peux pas l'expliquer, tu ne peux pas le rendre. »*
- **Tout outil est autorisé** (Claude fourni, ChatGPT, Gemini, Copilot…) — **à condition d'être déclaré**.
- **Une ligne par usage significatif** (code/requête/texte intégré, debug qui change la solution, choix orienté, tests, refactor).
- **Nominatif** : chaque ligne identifie son auteur.
- **Jamais** de données personnelles dans les prompts.
- La colonne **Justification** est le cœur : *pourquoi* + ce que vous avez **vérifié / corrigé / testé**.

---

## ⌨️ Déclaration permanente — assistants ambiants

> **À remplir en J0, une fois pour toutes.** Un assistant d'autocomplétion (Copilot, Tabnine, IA intégrée à l'IDE…) produit des suggestions **en continu** : impossible de les journaliser une par une. On le déclare donc **globalement** ici.
> ⚠️ La règle d'or continue de s'appliquer : ce que vous intégrez, vous devez savoir l'expliquer.

| Équipier | Outil ambiant utilisé | Où (IDE / éditeur) | Depuis quand |
|---|---|---|---|
| MARDAUS | Claude | VS Code | 09/09/2026 |
| PARIMELALAGAN | Claude | VS Code | 09/09/2026 |
| SINOUVASSANE | Claude | VS Code| 09/09/2026|
| CREPIEUX | Claude | VS Code | 09/09/2026 |
| BOUAFIA | Claude | VS Code | 09/09/2026 |
| CHAMBI LEBLANC | Claude | VS Code | 09/09/2026 |

*Aucun assistant ambiant utilisé ? Écrivez-le explicitement : « Aucun » — une case vide n'est pas une déclaration.*

### Outils utilisés par l’équipe

- **Claude** : assistance à la recherche, à la compréhension des indicateurs agroclimatiques, à la rédaction, à la génération de tests et au débogage. Les réponses ont été vérifiées, corrigées ou testées avant leur intégration.
- **Visual Studio Code (VS Code)** : écriture, modification et exécution du code Python, ainsi que consultation des fichiers du projet.
- **GitHub** : hébergement et versionnement du code, des données et de la documentation, avec suivi des modifications.
- **Discord** : communication entre les membres de l’équipe et coordination du travail.

Claude est utilisé comme un outil d’assistance et non comme une source d’autorité. Les résultats intégrés au projet sont confrontés aux sources officielles, aux données de l’API ou à des tests indépendants lorsque cela est pertinent.

---

## Critère de sélection des lignes

Une ligne par usage significatif, au sens du gabarit : code, requête ou texte
intégré à un livrable, débogage ayant changé la solution, choix orienté, test,
refactorisation.

**Usages volontairement non journalisés**, parce qu'ils n'ont produit ni
livrable ni décision : questions de vocabulaire, demandes d'organisation du
travail, reformulations de consignes, aide à l'installation de WampServer et
de phpMyAdmin. Ces échanges ont eu lieu, ils n'ont rien changé au rendu.

---

## Journal

| Date | Équipier | Outil/modèle | Tâche / contexte | Prompt (résumé) | Sortie IA | Gardé/modifié/rejeté | Justification (vérif. / correction / test) | Tokens (≈) |
|---|---|---|---|---|---|---|---|---|
| 08/09 | Dharun | Claude Sonnet 5.5 (claude.ai, compte perso) | C9 : indicateur agro-climatique officiel français | « trouve un indicateur officiel, sa formule, ses seuils, sa période » | réponse complète : somme de températures base 6 du maïs (DRIAS), plafond de Tx à 30 °C, comparaison avec la formule générique | **modifié** | formule recoupée avec la note « Logique des indicateurs » de l'amorçage DATA (même formule) ; date de consultation et rubrique « ce que ça change » corrigées ; réponse raccourcie | non mesurable |
| 08/09 | Dharun | Claude Sonnet 5.5 (claude.ai, compte perso) | C10 : indicateur le plus simple à calculer | « lequel est le plus simple de bout en bout ? » | réponse : le GDD (Tmin/Tmax seulement), confiance moyenne | **modifié** | réponse raccourcie ; question de jugement sans source externe, la conclusion dépend des champs réellement renvoyés par l'API (confiance moyenne conservée) | non mesurable |
| 10/09 | Dharun | Claude Sonnet 5.5 (claude.ai, compte perso) | C5 : ET0 et méthode de repli | « l'API fournit-elle l'ET0 ? sinon quelle méthode avec les seules températures ? » | formule Hargreaves-Samani ; hypothèse « ET0 absente de la Climate API » | **modifié** | hypothèse invalidée ensuite par le test API réel de l'équipe (11/09 : ET0 trouvée sous `_sum`) ; Hargreaves gardé uniquement comme repli ; réponse C5 à corriger dans le cahier | non mesurable |
| 11/09 | Dharun | Claude Sonnet 5.5 (claude.ai, compte perso) | Première liste de communes (grandes villes puis 10 communes rurales agricoles) | « propose des communes agricoles réelles pour vigne, maïs, blé, tournesol » | 10 communes avec code INSEE, coordonnées, altitude issus de recherches web | **rejeté** | valeurs non vérifiées sur l'API Géo ; remplacées par les 16 communes officielles de l'amorçage ; les 10 communes gardées en réserve pour une piste d'enrichissement | non mesurable |
| 14/09 | ___ | Claude Opus 5 (claude.ai) | Test API Reims, 2 modèles | comparer les deux modèles à partir du CSV | tableau MRI / CMCC | **gardé** | appel réalisé par nous ; 28 jours de gel contre 11. ___ | non mesurable |
| 21/09 | Dharun | Claude Sonnet 5.5 (claude.ai, compte perso) | Vérification des 16 communes officielles (INSEE, lat/lon, altitude) | « comment vérifier ces données ? » | URL `geo.api.gouv.fr/communes?nom=…&fields=nom,code,centre`, méthode min/max Wikipédia pour l'altitude, colonnes de traçabilité | **modifié** | requêtes exécutées par moi pour les 16 communes et comparées au CSV (15 concordantes ; Dijon refait ; signe de la longitude de Brest corrigé) ; altitude de Lille relevée sur Wikipédia (18 à 46 m) ; l'IA n'a fourni aucune valeur retenue | non mesurable |
| 06/10 | `[NOM]` | Claude Opus 5 (claude.ai) | Traçabilité des seuils | confronter chaque seuil du référentiel à sa source | `sources-seuils.csv`, 62 vérifications | gardé | 12 seuils sont contredits par leur propre source et sont signalés comme tels plutôt que corrigés en silence. `[À COMPLÉTER]` | non mesurable |
| 13/10 | `[NOM]` | Claude Opus 5 (claude.ai) | Jeu de séries de test | produire un jeu de test avec résultats attendus | `data/test/`, 2 CSV et un README | modifié | Données issues de notre propre export Open-Meteo, reformaté. Les valeurs attendues avaient d'abord été produites par le module lui-même, donc circulaires ; recalculées le 17/10 par un programme séparé depuis l'export d'origine, les 14 concordent. | non mesurable |
| 17/10 | `[NOM]` | Claude Opus 5 (claude.ai) | Document du schéma | reprendre notre capture et rédiger une légende | `schema-dimensionnel.docx` | modifié | Légende raccourcie et réécrite par nous. `[À COMPLÉTER : ce que vous avez changé]` | non mesurable |
| 17/10 | `[NOM]` | Claude Opus 5 (claude.ai) | Débogage et allègement de `indicateurs.py` | le script affiche `None`, pointe vers un fichier inexistant, et contient trop de commentaires | message d'usage réécrit, fichier de test par défaut, version sans commentaires | gardé | Deux défauts du code produit par l'IA, repérés par nous à l'exécution. Corrections testées depuis deux répertoires. Sortie de la version allégée comparée à celle de la version commentée : identique. Contrepartie acceptée : les références de formules FAO-56 et ARVALIS ne sont plus dans le code. | non mesurable |
| 17/10 | Dharun | claude-haiku-4-5 (API fournie par l'équipe) | Test de la clé API | « Dis bonjour. » (max_tokens=50) | une courte réponse de bienvenue | **gardé** | test technique réussi ; tokens relevés avec `reponse.parse().usage` | 56 (13 entrée + 43 sortie) |

*(Ajoutez autant de lignes que nécessaire.)*

---

## 🌱 Synthèse environnementale (à compléter pour le rendu final)

> Méthode et exemple de calcul : voir `poc-empreinte-ia.py`. Manier avec **esprit critique** (forte incertitude).

- **Total tokens** sur le projet : non mesurable pour les usages via claude.ai ; mesuré sur le compte API fourni : 56 (entrée : 13 / sortie : 43)
- **Énergie estimée** : `[…]` Wh
- **CO₂e estimé** : `[…]` g
- **Équivalence parlante** : ≈ `[…]` (ex. m/km en voiture, via facteur ADEME)
- **Hypothèses retenues** : `[Wh/1k tokens, intensité carbone du réseau, modèle…]`
- **Périmètre de la mesure** : mes usages via claude.ai n'exposent pas les tokens (non mesurables) ; seul le test de la clé du compte API fourni (claude-haiku-4-5) est mesuré : 56 tokens (13 entrée + 43 sortie).
  > ℹ️ La colonne **Tokens** n'est renseignable que pour le compte API fourni. Un usage sur ChatGPT, Gemini ou Copilot n'expose pas ses tokens : **écrivez « non mesurable »** dans la colonne et dites-le ici. Annoncer ce qu'on n'a **pas** pu mesurer fait partie d'une mesure honnête — c'est valorisé, pas pénalisé.
- **Discussion de l'incertitude** : `[pourquoi ces chiffres varient d'un facteur ~10 ?]`
- **Regard coût/bénéfice** : `[cet usage de l'IA en valait-il la peine ? où aurait-on pu être plus sobre ?]`