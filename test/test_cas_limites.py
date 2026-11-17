"""Tests des cas limites : annee sans gel et valeurs manquantes.

SAE 3.01 Climat & Cultures, equipe 9, pole DATA.

Les deux jeux sont fabriques a la main (data/test/) et leurs valeurs attendues
ont ete calculees a la main, puis recontrolees par un programme qui ne lit que
le CSV et n'importe pas indicateurs.py. Elles sont ecrites en dur ici : le
module ne peut donc pas valider ses propres resultats.

Lancement, depuis la racine du projet :

    python test/test_cas_limites.py
"""

import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import indicateurs as ind  # noqa: E402

SANS_GEL = os.path.join(RACINE, "data", "test", "series-sans-gel-2049.csv")
MANQUANTES = os.path.join(RACINE, "data", "test", "series-valeurs-manquantes-mars-2049.csv")

MRI = "MRI_AGCM3_2_S"
MARS_A_MAI = (3, 5)


def _sans_gel():
    return ind.lire_csv_contrat(SANS_GEL)[MRI]


def _manquantes():
    return ind.lire_csv_contrat(MANQUANTES)[MRI]


# ---------------------------------------------------------------------------
# Annee sans gel : t_min 3.0 / t_max 12.0 / precip 1.0 chaque jour, sauf le
# 14 fevrier (nuit a +0.1, juste au-dessus de zero).
# ---------------------------------------------------------------------------

def test_sans_gel_taille():
    """Une annee complete : 365 jours."""
    assert len(_sans_gel()) == 365


def test_sans_gel_aucun_jour_de_gel():
    """Zero jour de gel a -4, -2 et 0 degre, et un vrai zero (pas None)."""
    s = _sans_gel()
    for seuil in (-4.0, -2.0, 0.0):
        n = ind.jours_de_gel(s, seuil, 1, 12)
        assert n == 0 and n is not None, (seuil, n)


def test_sans_gel_degres_jours_et_pluie():
    """Mars a mai = 92 jours. Base 0 : 92 x 7.5. Base 6 : 92 x 1.5. Base 10 : 0."""
    s = _sans_gel()
    assert ind.degres_jours(s, 0.0, None, *MARS_A_MAI) == 690.0
    assert ind.degres_jours(s, 6.0, 30.0, *MARS_A_MAI) == 138.0
    assert ind.degres_jours(s, 10.0, None, *MARS_A_MAI) == 0.0
    assert ind.cumul_precipitations(s, *MARS_A_MAI) == 92.0


# ---------------------------------------------------------------------------
# Valeurs manquantes : 10 jours de mars. Le 3 mars n'a pas de t_min, le 5 mars
# pas de t_max, le 4 mars pas de precipitation.
# ---------------------------------------------------------------------------

def test_manquantes_lignes_sans_temperature_ignorees():
    """Dix lignes dans le fichier, huit retenues (3 et 5 mars ecartes)."""
    s = _manquantes()
    assert len(s) == 8
    dates = {j["date"].isoformat() for j in s}
    assert "2049-03-03" not in dates and "2049-03-05" not in dates


def test_manquantes_jamais_comptees_comme_zero():
    """Si la t_min vide du 3 mars valait 0, le gel a 0 degre passerait de 4 a 5."""
    s = _manquantes()
    obtenu = tuple(ind.jours_de_gel(s, seuil, *MARS_A_MAI) for seuil in (-4.0, -2.0, 0.0))
    assert obtenu == (0, 2, 4), obtenu


def test_manquantes_degres_jours():
    """Base 0 : 39.0. Base 6 : 10.0. Base 10 : 0.5."""
    s = _manquantes()
    assert ind.degres_jours(s, 0.0, None, *MARS_A_MAI) == 39.0
    assert ind.degres_jours(s, 6.0, 30.0, *MARS_A_MAI) == 10.0
    assert ind.degres_jours(s, 10.0, None, *MARS_A_MAI) == 0.5


def test_manquantes_precipitation_vide_ignoree():
    """La pluie vide du 4 mars devient None et n'entre pas dans le cumul : 10.0 mm."""
    s = _manquantes()
    j4 = next(j for j in s if j["date"].isoformat() == "2049-03-04")
    assert j4["precip"] is None
    assert ind.cumul_precipitations(s, *MARS_A_MAI) == 10.0


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
