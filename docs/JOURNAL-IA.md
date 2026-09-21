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
| MARDAUS | ___ | ___ | ___ |
| PARIMELALAGAN | ___ | ___ | ___ |
| SINOUVASSANE | ___ | ___ | ___ |
| CREPIEUX | ___ | ___ | ___ |
| BOUAFIA | ___ | ___ | ___ |
| CHAMBI LEBLANC | ___ | ___ | ___ |

*Aucun assistant ambiant utilisé ? Écrivez-le explicitement : « Aucun » — une case vide n'est pas une déclaration.*

---

## Journal

| Date | Équipier | Outil/modèle | Tâche / contexte | Prompt (résumé) | Sortie IA | Gardé/modifié/rejeté | Justification (vérif. / correction / test) | Tokens (≈) |
|---|---|---|---|---|---|---|---|---|
| 11/09 | ___ | Claude Opus 5 (claude.ai) | Organisation du J0 DATA | étapes de la semaine à partir des documents | plan en 5 étapes | **modifié** | plan réorganisé à mesure des amorçages reçus | non mesurable |
| 11/09 | ___ | Claude Opus 5 (claude.ai) | Test API Open-Meteo (Créteil) | régler l'appel, analyser le CSV exporté | paramètres d'appel, statistiques de contrôle | **modifié** | appel réalisé par nous ; ET0 trouvée sous `_sum`, contredit la doc. ___ | non mesurable |
| 11/09 | ___ | Claude Opus 5 (claude.ai) | Structure de traçabilité des seuils | créer la table `Source_Seuil` | `sources-seuils.csv` vide (70 lignes) | **gardé** | structure recommandée par l'amorçage DATA ; aucune source remplie par l'IA | non mesurable |
| 11-14/09 | ___ | Claude Opus 5 (claude.ai) | Recherche des seuils du maïs | où trouver chaque seuil ; cette page est-elle fiable | pistes : ARVALIS, fiches accidents, FAO-56, ECOCROP | **modifié** | chaque page ouverte et lue par nous ; pages écartées (semenciers, maïs fourrage). ___ | non mesurable |
| 14/09 | ___ | Claude Opus 5 (claude.ai) | Test API Reims, 2 modèles | comparer les deux modèles à partir du CSV | tableau MRI / CMCC | **gardé** | appel réalisé par nous ; 28 jours de gel contre 11. ___ | non mesurable |
| 14/09 | ___ | Claude Opus 5 (claude.ai) | Cahier E2 | corriger la logique de la réponse | réponse reformulée | **modifié** | contradiction avec l'architecture (centroïde) corrigée | non mesurable |
| 14/09 | ___ | Claude Opus 5 (claude.ai) | Identifier les dimensions (J1) | esquisse du schéma en étoile | `MODELE-DIMENSIONNEL-esquisse.md` + versions simplifiées | ___ | ___ | non mesurable |
| 14/09 | ___ | Claude Opus 5 (claude.ai) | Document variables météo | vérifier le document | nom de variable corrigé, partie ET0 réécrite | **modifié** | ___ | non mesurable |

*(Ajoutez autant de lignes que nécessaire.)*

---

## 🌱 Synthèse environnementale (à compléter pour le rendu final)

> Méthode et exemple de calcul : voir `poc-empreinte-ia.py`. Manier avec **esprit critique** (forte incertitude).

- **Total tokens** sur le projet : `[…]` (entrée : `[…]` / sortie : `[…]`)
- **Énergie estimée** : `[…]` Wh
- **CO₂e estimé** : `[…]` g
- **Équivalence parlante** : ≈ `[…]` (ex. m/km en voiture, via facteur ADEME)
- **Hypothèses retenues** : `[Wh/1k tokens, intensité carbone du réseau, modèle…]`
- **Périmètre de la mesure** : `[quels usages ai-je pu compter, lesquels non ?]`
  > ℹ️ La colonne **Tokens** n'est renseignable que pour le compte API fourni. Un usage sur ChatGPT, Gemini ou Copilot n'expose pas ses tokens : **écrivez « non mesurable »** dans la colonne et dites-le ici. Annoncer ce qu'on n'a **pas** pu mesurer fait partie d'une mesure honnête — c'est valorisé, pas pénalisé.
- **Discussion de l'incertitude** : `[pourquoi ces chiffres varient d'un facteur ~10 ?]`
- **Regard coût/bénéfice** : `[cet usage de l'IA en valait-il la peine ? où aurait-on pu être plus sobre ?]`
