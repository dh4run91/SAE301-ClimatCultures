"""Module de calcul des indicateurs agroclimatiques.

SAE 3.01 Climat & Cultures, equipe 9, pole DATA.

Le module lit une serie climatique journaliere (un ou plusieurs modeles) et
calcule, pour chaque culture, les indicateurs definis dans FENETRES : degres-
jours, jours de gel, jours de stress thermique et bilan hydrique.

Les seuils et les fenetres reprennent exactement les tables Dim_Culture et
Fenetre_Calcul de la base (sql/02-insertion-dimensions.sql).
"""

import csv
import json
import math
import os
import sys
from datetime import date, datetime


# (id_culture, indicateur) -> (mois_debut, mois_fin, seuil_specifique)
# Copie de la table Fenetre_Calcul. Un seuil a None renvoie a celui de CULTURES.
FENETRES = {
    ("BLE_TENDRE_H", "gdd"):             (10, 7, None),
    ("BLE_TENDRE_H", "gel"):             (3, 5, -4.0),
    ("BLE_TENDRE_H", "echaudage"):       (4, 6, None),
    ("BLE_TENDRE_H", "bilan_hydrique"):  (4, 10, None),
    ("MAIS_GRAIN",   "gdd"):             (4, 10, None),
    ("MAIS_GRAIN",   "gel"):             (9, 10, 0.0),
    ("MAIS_GRAIN",   "stress_thermique"):(7, 8, None),
    ("MAIS_GRAIN",   "bilan_hydrique"):  (4, 10, None),
    ("VIGNE",        "gdd"):             (4, 9, None),
    ("VIGNE",        "gel"):             (3, 5, -2.0),
    ("VIGNE",        "gel_dormance"):    (11, 2, -8.0),
    ("VIGNE",        "stress_thermique"):(7, 8, None),
    ("VIGNE",        "bilan_hydrique"):  (4, 10, None),
    ("TOURNESOL",    "gdd"):             (4, 9, None),
    ("TOURNESOL",    "gel"):             (4, 5, -1.0),
    ("TOURNESOL",    "stress_thermique"):(7, 8, None),
    ("TOURNESOL",    "bilan_hydrique"):  (4, 10, None),
}


# Seuils agronomiques des cultures du MVP, copie de Dim_Culture.
CULTURES = {
    "BLE_TENDRE_H": {"t_base": 0.0,  "t_plafond": None, "gel": -4.0, "stress": 30.0, "gdd_maturite": 2150},
    "MAIS_GRAIN":   {"t_base": 6.0,  "t_plafond": 30.0, "gel":  0.0, "stress": 35.0, "gdd_maturite": 1600},
    "VIGNE":        {"t_base": 10.0, "t_plafond": None, "gel": -2.0, "stress": 35.0, "gdd_maturite": 1300},
    "TOURNESOL":    {"t_base": 6.0,  "t_plafond": None, "gel": -1.0, "stress": 34.0, "gdd_maturite": 1550},
}


def mois_de_fenetre(mois_debut, mois_fin):
    """Renvoie la liste des mois couverts par une fenetre, dans l'ordre.

    Une fenetre peut passer par decembre : (11, 2) donne [11, 12, 1, 2].
    """
    if mois_debut <= mois_fin:
        return list(range(mois_debut, mois_fin + 1))
    return list(range(mois_debut, 13)) + list(range(1, mois_fin + 1))


def dans_fenetre(mois, mois_debut, mois_fin):
    """Indique si un mois (1 a 12) tombe dans la fenetre [mois_debut, mois_fin].

    Une fenetre dont le debut est apres la fin, comme (10, 7), passe par
    decembre : elle couvre octobre a decembre puis janvier a juillet.
    """
    if mois_debut <= mois_fin:
        return mois_debut <= mois <= mois_fin
    return mois >= mois_debut or mois <= mois_fin


def filtrer(serie, mois_debut, mois_fin):
    """Garde uniquement les jours de la serie qui tombent dans la fenetre."""
    return [j for j in serie if dans_fenetre(j["date"].month, mois_debut, mois_fin)]


def avertir_si_annee_unique(serie, mois_debut, mois_fin, etiquette=""):
    """Avertit si une fenetre a cheval sur deux annees est calculee sur une seule.

    Sur une seule annee, une fenetre comme octobre-juillet melange la fin et le
    debut de la meme annee civile : ce n'est pas un cycle de culture reel.
    Renvoie True si un avertissement a ete emis.
    """
    if mois_debut <= mois_fin:
        return False
    annees = {j["date"].year for j in serie}
    if len(annees) < 2:
        print(f"  ATTENTION {etiquette}: fenetre {mois_debut}-{mois_fin} a cheval sur "
              f"deux annees, mais la serie n en couvre qu une ({annees.pop()}). "
              f"Le resultat n est pas un cycle reel.", file=sys.stderr)
        return True
    return False


def avertir_si_fenetre_non_couverte(serie, mois_debut, mois_fin, etiquette=""):
    """Avertit si des mois de la fenetre sont absents de la serie.

    Sans cet avertissement, une fenetre vide donne 0 degre-jour et un verdict
    « insuffisant », ce qui ressemble a un resultat alors que ce n'en est pas un.
    Renvoie True si un avertissement a ete emis.
    """
    presents = {j["date"].month for j in serie}
    manquants = [m for m in mois_de_fenetre(mois_debut, mois_fin) if m not in presents]
    if manquants:
        print(f"  ATTENTION {etiquette}: la serie ne couvre pas les mois "
              f"{', '.join(str(m) for m in manquants)} de la fenetre "
              f"{mois_debut}-{mois_fin}. Le resultat est incomplet.", file=sys.stderr)
        return True
    return False


def verifier_fenetres(serie, id_culture):
    """Emet, une seule fois par culture, les avertissements sur ses fenetres."""
    for (culture, nom), (debut, fin, _) in FENETRES.items():
        if culture != id_culture:
            continue
        etiquette = f"{id_culture} / {nom}"
        avertir_si_annee_unique(serie, debut, fin, etiquette)
        avertir_si_fenetre_non_couverte(serie, debut, fin, etiquette)


def degres_jours(serie, t_base, t_plafond=None, mois_debut=1, mois_fin=12):
    """Somme des degres-jours sur la fenetre.

    Contribution d'un jour : max((t_min + min(t_max, plafond)) / 2 - t_base, 0).
    Sans plafond, t_max est pris tel quel. Une journee froide ne retire jamais
    de degres-jours. Resultat arrondi a 0,1.
    """
    total = 0.0
    for j in filtrer(serie, mois_debut, mois_fin):
        tmax = j["t_max"] if t_plafond is None else min(j["t_max"], t_plafond)
        total += max((j["t_min"] + tmax) / 2.0 - t_base, 0.0)
    return round(total, 1)


def jours_de_gel(serie, seuil, mois_debut, mois_fin):
    """Nombre de jours de la fenetre ou t_min est inferieure ou egale au seuil."""
    return sum(1 for j in filtrer(serie, mois_debut, mois_fin) if j["t_min"] <= seuil)


def jours_echaudage(serie, seuil, mois_debut, mois_fin):
    """Nombre de jours de la fenetre ou t_max depasse strictement le seuil.

    Sert a la fois pour l'echaudage du ble et pour le stress thermique.
    """
    return sum(1 for j in filtrer(serie, mois_debut, mois_fin) if j["t_max"] > seuil)


def cumul_precipitations(serie, mois_debut, mois_fin):
    """Cumul des precipitations de la fenetre, en mm, valeurs manquantes ignorees."""
    return round(sum(j["precip"] for j in filtrer(serie, mois_debut, mois_fin)
                     if j["precip"] is not None), 1)


def rayonnement_extraterrestre(latitude_deg, jour_annee):
    """Rayonnement extraterrestre Ra en MJ/m2/jour (FAO-56, equation 21).

    latitude_deg : latitude en degres decimaux ; jour_annee : 1 a 366.
    """
    GSC = 0.0820
    phi = math.radians(latitude_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * jour_annee / 365.0)
    delta = 0.409 * math.sin(2 * math.pi * jour_annee / 365.0 - 1.39)

    x = -math.tan(phi) * math.tan(delta)
    x = max(-1.0, min(1.0, x))
    omega = math.acos(x)

    return (24 * 60 / math.pi) * GSC * dr * (
        omega * math.sin(phi) * math.sin(delta)
        + math.cos(phi) * math.cos(delta) * math.sin(omega))


def et0_hargreaves(t_min, t_max, latitude_deg, jour_annee):
    """Evapotranspiration de reference ET0 en mm/jour (formule de Hargreaves).

    Ra est converti en mm d'eau equivalents (facteur 0,408). Renvoie None si
    t_max < t_min, ce qui signale une donnee incoherente.
    """
    if t_max < t_min:
        return None
    ra_mm = rayonnement_extraterrestre(latitude_deg, jour_annee) * 0.408
    t_moy = (t_min + t_max) / 2.0
    return 0.0023 * (t_moy + 17.8) * math.sqrt(t_max - t_min) * ra_mm


def bilan_hydrique(serie, latitude_deg, mois_debut, mois_fin):
    """Bilan pluie moins ET0 sur la fenetre.

    Renvoie le triplet (bilan, pluie, et0) en mm, arrondis a 0,1. Une pluie
    manquante compte pour zero dans ce bilan.
    """
    pluie = et0 = 0.0
    for j in filtrer(serie, mois_debut, mois_fin):
        pluie += j["precip"] or 0.0
        e = et0_hargreaves(j["t_min"], j["t_max"], latitude_deg, j["date"].timetuple().tm_yday)
        if e is not None:
            et0 += e
    return round(pluie - et0, 1), round(pluie, 1), round(et0, 1)


def indicateurs_culture(serie, id_culture, latitude_deg, avertir=True):
    """Calcule tous les indicateurs d'une culture sur une serie.

    Renvoie une liste de triplets (indicateur, valeur, unite), dans l'ordre
    d'affichage. Si avertir vaut True, les avertissements sur les fenetres
    sont emis ; main() les emet une seule fois par culture et passe False.
    """
    seuils = CULTURES[id_culture]
    faits = []

    if avertir:
        verifier_fenetres(serie, id_culture)

    def fenetre(nom):
        return FENETRES.get((id_culture, nom))

    f = fenetre("gdd")
    if f:
        faits.append(("gdd", degres_jours(serie, seuils["t_base"], seuils["t_plafond"],
                                          f[0], f[1]), "degres-jours"))

    for nom in ("gel", "gel_dormance"):
        f = fenetre(nom)
        if f:
            seuil = f[2] if f[2] is not None else seuils["gel"]
            faits.append((nom, jours_de_gel(serie, seuil, f[0], f[1]), "jours"))

    for nom, cle in (("echaudage", "stress"), ("stress_thermique", "stress")):
        f = fenetre(nom)
        if f:
            seuil = f[2] if f[2] is not None else seuils[cle]
            faits.append((nom, jours_echaudage(serie, seuil, f[0], f[1]), "jours"))

    f = fenetre("bilan_hydrique")
    if f:
        bilan, pluie, et0 = bilan_hydrique(serie, latitude_deg, f[0], f[1])
        faits.append(("bilan_hydrique", bilan, "mm"))
        faits.append(("precipitations", pluie, "mm"))
        faits.append(("et0_hargreaves", et0, "mm"))

    return faits


def verdict(serie, id_culture, latitude_deg):
    """Compare les degres-jours de la culture a ceux necessaires a maturite.

    Renvoie (gdd, "viable" ou "insuffisant"), ou (None, None) si la culture
    n'a pas de fenetre de degres-jours.
    """
    f = FENETRES.get((id_culture, "gdd"))
    if not f:
        return None, None
    s = CULTURES[id_culture]
    gdd = degres_jours(serie, s["t_base"], s["t_plafond"], f[0], f[1])
    return gdd, ("viable" if gdd >= s["gdd_maturite"] else "insuffisant")


def lire_json(chemin):
    """Lit la reponse JSON de l'API Open-Meteo Climate.

    Renvoie (series, latitude, altitude), ou series associe a chaque modele la
    liste de ses jours. Les jours sans t_min ou t_max sont ignores.
    """
    with open(chemin, encoding="utf-8") as f:
        d = json.load(f)
    jours = d["daily"]["time"]
    modeles = sorted({k.replace("temperature_2m_min_", "")
                      for k in d["daily"] if k.startswith("temperature_2m_min_")})
    series = {}
    for m in modeles:
        s = []
        tmin, tmax = d["daily"][f"temperature_2m_min_{m}"], d["daily"][f"temperature_2m_max_{m}"]
        pr = d["daily"].get(f"precipitation_sum_{m}", [None] * len(jours))
        for i, jour in enumerate(jours):
            if tmin[i] is None or tmax[i] is None:
                continue
            s.append({"date": datetime.strptime(jour, "%Y-%m-%d").date(),
                      "t_min": tmin[i], "t_max": tmax[i], "precip": pr[i]})
        series[m] = s
    return series, d.get("latitude"), d.get("elevation")


def lire_csv_contrat(chemin):
    """Lit un CSV au format du contrat d'interface DEV vers DATA.

    Separateur point-virgule, dates ISO, une case vide pour une valeur
    manquante. Les lignes sans t_min ou t_max sont ignorees, une pluie vide
    devient None. Renvoie un dictionnaire modele -> jours tries par date.
    """
    with open(chemin, encoding="utf-8-sig", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))

    series = {}
    for l in lignes:
        m = l["id_modele"].strip()
        try:
            t_min, t_max = float(l["t_min"]), float(l["t_max"])
        except (ValueError, TypeError):
            continue
        precip = l.get("precip", "").strip()
        series.setdefault(m, []).append({
            "date": date.fromisoformat(l["date"].strip()),
            "t_min": t_min, "t_max": t_max,
            "precip": float(precip) if precip else None})

    for s in series.values():
        s.sort(key=lambda j: j["date"])
    return series


def format_contrat(chemin):
    """Indique si le fichier est au format du contrat (en-tete id_commune;...)."""
    with open(chemin, encoding="utf-8-sig") as f:
        return f.readline().strip().lower().startswith("id_commune;")


def lire_csv_openmeteo(chemin):
    """Lit un CSV exporte depuis le site Open-Meteo.

    Ce format a des lignes de metadonnees avant l'en-tete « time; », et des
    dates au format JJ/MM/AAAA. Renvoie (series, latitude, None).
    """
    with open(chemin, encoding="utf-8") as f:
        brut = f.read().splitlines()
    meta = brut[1].split(";")
    latitude = float(meta[0])
    i_entete = next(i for i, l in enumerate(brut) if l.startswith("time;"))
    entete = brut[i_entete].split(";")

    cols = {}
    for i, c in enumerate(entete):
        for prefixe, cle in (("temperature_2m_min_", "t_min"),
                             ("temperature_2m_max_", "t_max"),
                             ("precipitation_sum_", "precip")):
            if c.startswith(prefixe):
                modele = c[len(prefixe):].split(" ")[0]
                cols.setdefault(modele, {})[cle] = i

    series = {m: [] for m in cols}
    for ligne in brut[i_entete + 1:]:
        champs = ligne.split(";")
        if not champs or not champs[0].strip():
            continue
        d = datetime.strptime(champs[0], "%d/%m/%Y").date()
        for m, c in cols.items():
            series[m].append({"date": d,
                              "t_min": float(champs[c["t_min"]]),
                              "t_max": float(champs[c["t_max"]]),
                              "precip": float(champs[c["precip"]]) if "precip" in c else None})
    return series, latitude, None


DEFAUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "data", "test", "series-reims-2049-complete.csv")


def usage():
    """Affiche l'aide de la ligne de commande et renvoie le code de sortie 1."""
    print("Module de calcul des indicateurs agroclimatiques.")
    print("SAE 3.01 Climat & Cultures, equipe 9, pole DATA.")
    print()
    print("Usage :  python indicateurs.py [fichier] [latitude]")
    print()
    print("Sans argument, le jeu de test par defaut est utilise :")
    print("  " + DEFAUT)
    print()
    print("Trois formats sont acceptes, detectes automatiquement :")
    print("  - JSON renvoye par l API Open-Meteo Climate")
    print("  - CSV au format du contrat d interface DEV vers DATA")
    print("  - CSV exporte depuis le site Open-Meteo")
    print()
    print("La latitude ne sert qu au calcul de l ET0. Par defaut, Reims.")
    return 1


def main():
    """Point d'entree : lit le fichier, puis affiche les indicateurs par culture."""
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help", "/?"):
        return usage()

    if len(sys.argv) > 1:
        chemin = sys.argv[1]
    elif os.path.exists(DEFAUT):
        chemin = DEFAUT
        print("Aucun fichier indique, jeu de test par defaut.")
        print("Pour en traiter un autre : python indicateurs.py <fichier>")
        print()
    else:
        print("Aucun fichier indique, et le jeu de test est introuvable :")
        print("  " + DEFAUT)
        print()
        return usage()

    latitude_arg = float(sys.argv[2]) if len(sys.argv) > 2 else 49.2535

    if chemin.lower().endswith(".json"):
        series, latitude, altitude = lire_json(chemin)
    elif format_contrat(chemin):
        series, latitude, altitude = lire_csv_contrat(chemin), latitude_arg, None
    else:
        series, latitude, altitude = lire_csv_openmeteo(chemin)

    print(f"Fichier   : {chemin}")
    print(f"Latitude  : {latitude}" + (f"   altitude de la maille : {altitude} m" if altitude else ""))
    for m, s in series.items():
        print(f"Modele    : {m:<16} {len(s)} jours, du {s[0]['date']} au {s[-1]['date']}")
    print()

    premiere = next(iter(series.values()))
    for id_culture in ("VIGNE", "BLE_TENDRE_H", "MAIS_GRAIN", "TOURNESOL"):
        # Les modeles couvrent les memes dates : un seul controle par culture.
        sys.stdout.flush()
        verifier_fenetres(premiere, id_culture)
        sys.stderr.flush()

        print(f"=== {id_culture} " + "=" * (56 - len(id_culture)))
        noms = [f[0] for f in indicateurs_culture(premiere, id_culture, latitude, avertir=False)]
        entete = f"{'indicateur':<18}" + "".join(f"{m[:14]:>16}" for m in series)
        print(entete)
        print("-" * len(entete))
        par_modele = {m: dict((f[0], (f[1], f[2])) for f in
                              indicateurs_culture(s, id_culture, latitude, avertir=False))
                      for m, s in series.items()}
        for nom in noms:
            ligne = f"{nom:<18}"
            for m in series:
                v, u = par_modele[m][nom]
                ligne += f"{v:>12} {u[:3]:<3}"
            print(ligne)
        v = {m: verdict(s, id_culture, latitude) for m, s in series.items()}
        print(f"{'verdict':<18}" + "".join(f"{v[m][1]:>16}" for m in series))
        print()

    print("Rappel : un seul scenario d emissions, environ RCP 8.5. Les modeles")
    print("sous-estiment le gel d un facteur 2 environ. Les ecarts entre modeles")
    print("se lisent comme une fourchette, jamais comme un chiffre unique.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
