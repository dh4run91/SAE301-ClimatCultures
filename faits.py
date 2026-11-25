"""Ecriture des faits dans la table Fact_Indicateur.

SAE 3.01 Climat & Cultures, equipe 9, pole DATA. Issue #80.

Le calcul et l'ecriture sont separes :

- calculer_faits() produit les lignes, sans base de donnees. Elle est testee
  par test/test_indicateurs.py.
- ecrire_faits() les insere dans MySQL. Le connecteur est importe a
  l'interieur de la fonction : sans lui, le reste du fichier fonctionne.

Lancement, depuis la racine du projet :

    python faits.py            calcule et affiche les lignes du jeu de test
    python faits.py --ecrire   les ecrit aussi en base (parametres dans .env)
"""

import os
import sys
from datetime import date

import indicateurs as ind


# Seules cultures dont tous les seuils sont tranches et sources.
# Le ble et le tournesol ont encore des seuils ouverts.
CULTURES_TRAITEES = ("MAIS_GRAIN", "VIGNE")

# Jeu de test par defaut : Reims, horizon 2041-2050, annee 2049.
# Commune et horizon sont ceux des colonnes du CSV ; la latitude est celle
# de Reims dans Dim_Commune (sql/02-insertion-dimensions.sql).
COMMUNE_DEFAUT = "51454"
HORIZON_DEFAUT = "PROJ_2041_2050"
LATITUDE_DEFAUT = 49.2535

SQL_DELETE = (
    "DELETE FROM Fact_Indicateur "
    "WHERE id_commune = %(id_commune)s "
    "AND id_culture = %(id_culture)s "
    "AND id_horizon = %(id_horizon)s"
)

SQL_INSERT = (
    "INSERT INTO Fact_Indicateur "
    "(id_commune, id_culture, id_horizon, id_modele, indicateur, "
    "valeur, unite, nb_annees, date_calcul) "
    "VALUES (%(id_commune)s, %(id_culture)s, %(id_horizon)s, %(id_modele)s, "
    "%(indicateur)s, %(valeur)s, %(unite)s, %(nb_annees)s, %(date_calcul)s)"
)


def calculer_faits(id_commune, id_culture, id_horizon, series, latitude):
    """Calcule les lignes de Fact_Indicateur pour une selection.

    series : dictionnaire modele -> liste de jours, comme le renvoie
    indicateurs.lire_csv_contrat. Renvoie une liste de dictionnaires, un par
    (modele, indicateur), dont les cles sont les colonnes de la table.

    valeur et nb_annees sont ceux du module : la valeur est la moyenne de
    l'indicateur calcule annee par annee, nb_annees le nombre d'annees
    moyennees.

    Un indicateur dont la fenetre traverse le 31 decembre (mois_debut >
    mois_fin dans FENETRES) recoit valeur None et nb_annees None, quel que
    soit le nombre d'annees de la serie : il n'est pas calculable. Il n'est
    jamais ecrit 0.
    """
    if id_culture not in CULTURES_TRAITEES:
        raise ValueError(f"{id_culture} : culture non traitee. "
                         f"Cultures traitees : {', '.join(CULTURES_TRAITEES)}.")

    lignes = []
    for id_modele, serie in series.items():
        for nom, valeur, unite, nb_annees in ind.indicateurs_culture(
                serie, id_culture, latitude, avertir=False):
            # Pluie et ET0 sont calculees sur la fenetre du bilan hydrique.
            cle = "bilan_hydrique" if nom in ("precipitations", "et0_hargreaves") else nom
            debut, fin, _ = ind.FENETRES[(id_culture, cle)]

            # Fenetre a cheval sur deux annees : la moyenne du module groupe
            # par annee civile (par_annee), donc chaque hiver serait coupe au
            # 31 decembre et la moyenne porterait sur des demi-hivers. Sur une
            # seule annee, elle renverrait un 0 trompeur. On ecrit NULL.
            # Limite a lever quand la moyenne groupera par annee agricole et
            # non plus par annee civile.
            if debut > fin:
                valeur, nb_annees = None, None

            lignes.append({
                "id_commune": id_commune,
                "id_culture": id_culture,
                "id_horizon": id_horizon,
                "id_modele": id_modele,
                "indicateur": nom,
                "valeur": valeur,
                "unite": unite,
                "nb_annees": nb_annees,
                "date_calcul": date.today(),
            })
    return lignes


def ecrire_faits(lignes):
    """Ecrit les lignes dans Fact_Indicateur : DELETE puis INSERT.

    Le DELETE ne porte que sur les selections (commune, culture, horizon)
    presentes dans les lignes. Tout se fait dans une seule transaction :
    en cas d'erreur, rien n'est modifie. Renvoie le nombre de lignes ecrites.

    Les parametres de connexion sont lus dans .env : DB_HOST, DB_USER,
    DB_PASSWORD, DB_NAME.
    """
    # Imports ici et pas en tete de fichier : les tests tournent sans eux.
    import mysql.connector
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
    connexion = mysql.connector.connect(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
    )
    try:
        curseur = connexion.cursor()
        selections = {(l["id_commune"], l["id_culture"], l["id_horizon"]) for l in lignes}
        for id_commune, id_culture, id_horizon in selections:
            curseur.execute(SQL_DELETE, {"id_commune": id_commune,
                                         "id_culture": id_culture,
                                         "id_horizon": id_horizon})
        curseur.executemany(SQL_INSERT, lignes)
        connexion.commit()
    except Exception:
        connexion.rollback()
        raise
    finally:
        connexion.close()
    return len(lignes)


def main():
    """Calcule et affiche les faits du jeu de test ; les ecrit avec --ecrire."""
    series = ind.lire_csv_contrat(ind.DEFAUT)

    lignes = []
    for id_culture in CULTURES_TRAITEES:
        lignes += calculer_faits(COMMUNE_DEFAUT, id_culture, HORIZON_DEFAUT,
                                 series, LATITUDE_DEFAUT)
    sys.stderr.flush()

    print(f"{'culture':<11} {'modele':<14} {'indicateur':<17} "
          f"{'valeur':>8} {'unite':<13} nb_annees")
    for l in lignes:
        valeur = "NULL" if l["valeur"] is None else l["valeur"]
        nb = "NULL" if l["nb_annees"] is None else l["nb_annees"]
        print(f"{l['id_culture']:<11} {l['id_modele']:<14} {l['indicateur']:<17} "
              f"{valeur:>8} {l['unite']:<13} {nb}")
    print()
    print(f"{len(lignes)} lignes calculees, date_calcul {date.today()}.")

    if "--ecrire" in sys.argv[1:]:
        print(f"{ecrire_faits(lignes)} lignes ecrites dans Fact_Indicateur.")
    else:
        print("Rien n est ecrit en base. Pour ecrire : python faits.py --ecrire")
    return 0


if __name__ == "__main__":
    sys.exit(main())
