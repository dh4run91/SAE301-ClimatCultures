# 📋 Backlog priorisé — SAÉ 3.01 « Climat & Cultures »

> Méthode MoSCoW : **M**ust have (indispensable) · **S**hould have (important) · **C**ould have (si le temps permet) · **W**on't have (hors périmètre, assumé)

## Must have — indispensable pour que l'application ait un sens

- [ ] Sélection d'une commune parmi les 16 de référence
- [ ] Sélection d'une culture parmi les 4 retenues (blé tendre, maïs, vigne, tournesol)
- [ ] Sélection d'un horizon (aujourd'hui vs 2050)
- [ ] Appel réel à l'API Open-Meteo Climate (back-end, jamais depuis le navigateur)
- [ ] Calcul d'**un seul indicateur simple** : jours de gel critiques
- [ ] Affichage du résultat (tableau ou graphique simple)
- [ ] Schéma en étoile déployé sur AlwaysData (4 dimensions + Fact_Indicateur)
- [ ] Référentiel cultures/seuils sourcé (au moins nos 4 cultures)
- [ ] Jeu d'essais de données (vérifier un GDD/gel à la main sur une commune connue)

## Should have — important, mais pas bloquant pour un MVP fonctionnel

- [ ] Indicateur GDD (maturité de la culture)
- [ ] Indicateur stress thermique
- [ ] Indicateur bilan hydrique (P − ET0 via Hargreaves)
- [ ] Comparaison entre 2 modèles climatiques (incertitude)
- [ ] Comptes utilisateurs (session anonyme + compte persistant)
- [ ] Favoris (communes/cultures)
- [ ] Gestion des erreurs API (timeout, retry, cache)
- [ ] Ergonomie & accessibilité de base
- [ ] Conception RGPD (anonymisation, minimisation)

## Could have — si le temps le permet (effet « waouh »)

- [ ] Carte du décalage des zones de culture à l'horizon 2050
- [ ] Recherche libre de n'importe quelle commune (pas seulement les 16), calcul à la demande
- [ ] Visualisation de l'incertitude (fourchette entre modèles plutôt qu'un chiffre unique)
- [ ] Courbes d'évolution temporelle (pas juste un instantané 2050)
- [ ] Indicateur de vernalisation pour le blé (angle mort identifié dans l'amorçage)

## Won't have — explicitement hors périmètre (assumé, pas oublié)

- Comparaison de communes dans un rayon géographique (idée intéressante, mais complexité ajoutée : formule de distance, calcul multiplié par le nombre de communes dans le rayon)
- Couverture des ~35 000 communes de France (l'énoncé le déconseille explicitement)
- Comparaison de scénarios d'émission (RCP) — l'API Open-Meteo n'en propose qu'un seul (≈RCP 8.5) ; nécessiterait DRIAS, hors périmètre pour ce projet
- Cultures au-delà des 4 retenues (bien que le référentiel officiel en propose 10, sourcer le reste demanderait un temps disproportionné)

---

*Document vivant : à revoir à chaque jalon (fin J1, J2...) plutôt que figé une fois pour toutes.*
