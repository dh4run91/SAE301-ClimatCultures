"""Verification automatique des valeurs attendues du jeu de test.

SAE 3.01 Climat & Cultures, equipe 9, pole DATA.

Ce script verifie que les fonctions de indicateurs.py retrouvent exactement
les valeurs annoncees dans data/test/README.md, ainsi que les chiffres cites
dans les commentaires des scripts SQL.

Lancement, depuis la racine du projet :

    python tests/test_indicateurs.py

Le script fonctionne aussi avec pytest, s'il est installe :

    pytest tests/
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import indicateurs as ind  # noqa: E402

MARS = os.path.join(RACINE, "data", "test", "series-reims-mars-2049.csv")
ANNEE = os.path.join(RACINE, "data", "test", "series-reims-2049-complete.csv")

MRI = "MRI_AGCM3_2_S"
CMCC = "CMCC_CM2_VHR4"

# Le README raisonne sur une fenetre mars a mai : tout l'extrait est retenu.
MARS_A_MAI = (3, 5)


def _mars():
    return ind.lire_csv_contrat(MARS)


def _annee():
    return ind.lire_csv_contrat(ANNEE)


def test_taille_des_jeux():
    """730 lignes pour l'annee complete, 62 pour l'extrait de mars."""
    annee, mars = _annee(), _mars()
    assert len(annee[MRI]) == 365 and len(annee[CMCC]) == 365
    assert len(mars[MRI]) == 31 and len(mars[CMCC]) == 31


def test_jours_de_gel_selon_le_seuil():
    """README : 0 / 1 / 4 chez MRI et 0 / 0 / 0 chez CMCC."""
    s = _mars()
    attendu = {MRI: (0, 1, 4), CMCC: (0, 0, 0)}
    for modele, valeurs in attendu.items():
        obtenu = tuple(ind.jours_de_gel(s[modele], seuil, *MARS_A_MAI)
                       for seuil in (-4.0, -2.0, 0.0))
        assert obtenu == valeurs, (modele, obtenu, valeurs)


def test_degres_jours_selon_base_et_plafond():
    """README : ble base 0, mais base 6 plafond 30, vigne base 10."""
    s = _mars()
    attendu = {MRI: (218.6, 53.5, 7.7), CMCC: (291.5, 105.8, 24.3)}
    for modele, valeurs in attendu.items():
        obtenu = (ind.degres_jours(s[modele], 0.0, None, *MARS_A_MAI),
                  ind.degres_jours(s[modele], 6.0, 30.0, *MARS_A_MAI),
                  ind.degres_jours(s[modele], 10.0, None, *MARS_A_MAI))
        assert obtenu == valeurs, (modele, obtenu, valeurs)


def test_cumul_precipitations():
    """README : 72,6 mm chez MRI et 80,3 mm chez CMCC sur mars 2049."""
    s = _mars()
    assert ind.cumul_precipitations(s[MRI], *MARS_A_MAI) == 72.6
    assert ind.cumul_precipitations(s[CMCC], *MARS_A_MAI) == 80.3


def test_chiffres_cites_dans_le_sql():
    """Commentaires de 01-creation-base.sql et 02-insertion-dimensions.sql."""
    s = _annee()
    # 28 et 11 jours de gel sur l'annee entiere, dont 22 en janvier-fevrier chez MRI
    assert ind.jours_de_gel(s[MRI], 0.0, 1, 12) == 28
    assert ind.jours_de_gel(s[CMCC], 0.0, 1, 12) == 11
    assert ind.jours_de_gel(s[MRI], 0.0, 1, 2) == 22
    # Avec la fenetre du debourrement et son seuil, l'ecart tombe a 1 contre 0
    assert ind.jours_de_gel(s[MRI], -2.0, 3, 5) == 1
    assert ind.jours_de_gel(s[CMCC], -2.0, 3, 5) == 0
    # 16 et 28 jours au-dessus de 30 degres
    assert ind.jours_echaudage(s[MRI], 30.0, 1, 12) == 16
    assert ind.jours_echaudage(s[CMCC], 30.0, 1, 12) == 28


def test_fenetre_a_cheval_sur_deux_annees():
    """La fenetre (11, 2) couvre novembre, decembre, janvier et fevrier."""
    assert ind.mois_de_fenetre(11, 2) == [11, 12, 1, 2]
    assert ind.dans_fenetre(12, 11, 2) and ind.dans_fenetre(1, 11, 2)
    assert not ind.dans_fenetre(3, 11, 2)


if __name__ == "__main__":
    tests = [(nom, f) for nom, f in sorted(globals().items())
             if nom.startswith("test_") and callable(f)]
    echecs = 0
    for nom, f in tests:
        try:
            f()
            print(f"OK     {nom}")
        except AssertionError as e:
            echecs += 1
            print(f"ECHEC  {nom} : {e}")
    print()
    print(f"{len(tests) - echecs} / {len(tests)} tests reussis")
    sys.exit(1 if echecs else 0)
