"""Controle de coherence des seuils des cultures du MVP.

SAE 3.01 Climat & Cultures, equipe 9, pole DATA.

Compare, pour les quatre cultures du MVP, les valeurs trouvees dans :
  1. data/referentiel-cultures-v2.csv
  2. sql/02-insertion-dimensions.sql (INSERT INTO Dim_Culture)
  3. indicateurs.py (dictionnaire CULTURES)

Il compare aussi le sens de la comparaison (operateur_gel, operateur_stress du
CSV, op_gel et op_stress du module). Le SQL ne porte pas ces colonnes.

Lecture seule : ce script ne modifie aucun fichier.

Lancement, depuis la racine du projet :

    python controle_seuils.py

Code de sortie : 0 si les trois sources concordent, 1 sinon.
"""

import csv
import os
import re
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RACINE)

import indicateurs as ind  # noqa: E402

CHEMIN_CSV = os.path.join(RACINE, "data", "referentiel-cultures-v2.csv")
CHEMIN_SQL = os.path.join(RACINE, "sql", "02-insertion-dimensions.sql")

# nom du champ commun -> colonne du CSV
COLONNES_CSV = {
    "t_base": "t_base_c",
    "t_plafond": "t_plafond_gdd_c",
    "gdd_maturite": "gdd_maturite_cj",
    "gel": "seuil_gel_c",
    "stress": "seuil_stress_thermique_c",
}

# nom du champ du module -> colonne du CSV, pour les operateurs de comparaison.
OPERATEURS_CSV = {
    "op_gel": "operateur_gel",
    "op_stress": "operateur_stress",
}

# Un nombre SQL : entier, decimal, negatif, ou NULL.
NOMBRE = r"(-?\d+(?:\.\d+)?|NULL)"

# Debut d'une ligne de l'INSERT Dim_Culture : identifiant, nom, type, puis
# t_base, t_plafond, gdd_maturite, seuil_gel, besoin_eau, t_opt_min, t_opt_max,
# seuil_stress.
MOTIF_LIGNE_SQL = re.compile(
    r"\('([A-Z_]+)',\s*'(?:[^']|'')*',\s*'[a-z_]+',\s*"
    + r",\s*".join([NOMBRE] * 8)
)


def en_nombre(texte):
    """Convertit un texte en float, ou None si vide ou NULL."""
    if texte is None:
        return None
    texte = str(texte).strip()
    if texte == "" or texte.upper() == "NULL":
        return None
    return float(texte.replace(",", "."))


def lire_csv():
    """Renvoie {id_culture: {champ: valeur}} depuis le referentiel CSV."""
    resultat = {}
    with open(CHEMIN_CSV, encoding="utf-8-sig", newline="") as f:
        for ligne in csv.DictReader(f, delimiter=";"):
            resultat[ligne["id_culture"]] = {
                champ: en_nombre(ligne[colonne])
                for champ, colonne in COLONNES_CSV.items()
            }
    return resultat


def lire_operateurs_csv():
    """Renvoie {id_culture: {champ: texte}} pour les operateurs du referentiel.

    Une colonne absente du CSV donne « absent » ; une case vide donne « vide ».
    """
    resultat = {}
    with open(CHEMIN_CSV, encoding="utf-8-sig", newline="") as f:
        for ligne in csv.DictReader(f, delimiter=";"):
            resultat[ligne["id_culture"]] = {
                champ: (ligne[colonne].strip() or "vide") if colonne in ligne else "absent"
                for champ, colonne in OPERATEURS_CSV.items()
            }
    return resultat


def lire_sql():
    """Renvoie {id_culture: {champ: valeur}} depuis le script SQL."""
    with open(CHEMIN_SQL, encoding="utf-8") as f:
        texte = f.read()
    resultat = {}
    for m in MOTIF_LIGNE_SQL.finditer(texte):
        (id_culture, t_base, t_plafond, gdd, gel, _eau,
         _opt_min, _opt_max, stress) = m.groups()
        resultat[id_culture] = {
            "t_base": en_nombre(t_base),
            "t_plafond": en_nombre(t_plafond),
            "gdd_maturite": en_nombre(gdd),
            "gel": en_nombre(gel),
            "stress": en_nombre(stress),
        }
    return resultat


def lire_module():
    """Renvoie {id_culture: {champ: valeur}} depuis le dictionnaire CULTURES."""
    return {
        id_culture: {champ: en_nombre(valeurs[champ]) for champ in COLONNES_CSV}
        for id_culture, valeurs in ind.CULTURES.items()
    }


def controler_operateurs():
    """Compare les operateurs du CSV a ceux du module. Renvoie le nombre d'ecarts."""
    csv_ops = lire_operateurs_csv()
    nb_ecarts = 0
    for id_culture, valeurs in ind.CULTURES.items():
        print(f"=== operateurs {id_culture} " + "=" * (28 - len(id_culture)))
        for champ in OPERATEURS_CSV:
            module = valeurs[champ]
            fichier = csv_ops.get(id_culture, {}).get(champ, "absent")
            if module == fichier:
                etat = "OK     "
            else:
                etat = "ECART  "
                nb_ecarts += 1
            print(f"{etat}{champ:<13} csv={fichier}  module={module}  sql=non porte")
        print()
    return nb_ecarts


def montrer(valeur):
    return "vide" if valeur is None else f"{valeur:g}"


def main():
    sources = {"csv": lire_csv(), "sql": lire_sql(), "module": lire_module()}
    nb_ecarts = 0

    for id_culture in ind.CULTURES:
        print(f"=== {id_culture} " + "=" * (40 - len(id_culture)))
        for champ in COLONNES_CSV:
            valeurs = {}
            for nom, donnees in sources.items():
                if id_culture not in donnees:
                    valeurs[nom] = "absent"
                else:
                    valeurs[nom] = donnees[id_culture][champ]
            if len({str(v) for v in valeurs.values()}) == 1:
                etat = "OK     "
            else:
                etat = "ECART  "
                nb_ecarts += 1
            detail = "  ".join(
                f"{nom}={v if isinstance(v, str) else montrer(v)}"
                for nom, v in valeurs.items()
            )
            print(f"{etat}{champ:<13} {detail}")
        print()

    nb_ecarts += controler_operateurs()

    if nb_ecarts == 0:
        print("Les trois sources concordent.")
        return 0
    print(f"{nb_ecarts} ecart(s) a reporter dans les trois endroits.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
