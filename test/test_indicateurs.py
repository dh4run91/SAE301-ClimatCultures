"""Verification automatique des valeurs attendues du jeu de test.

SAE 3.01 Climat & Cultures, equipe 9, pole DATA.

Ce script verifie que les fonctions de indicateurs.py retrouvent exactement
les valeurs annoncees dans data/test/README.md, ainsi que les chiffres cites
dans les commentaires des scripts SQL.

Lancement, depuis la racine du projet :

    python test/test_indicateurs.py

Le script fonctionne aussi avec pytest, s'il est installe :

    pytest test/
"""

import io
import json
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

import indicateurs as ind  # noqa: E402

MARS = os.path.join(RACINE, "data", "test", "series-reims-mars-2049.csv")
ANNEE = os.path.join(RACINE, "data", "test", "series-reims-2049-complete.csv")
MANQUANTES = os.path.join(RACINE, "data", "test", "series-reims-2049-mars-valeurs-manquantes.csv")
ETE = os.path.join(RACINE, "data", "test", "series-reims-2049-ete-sans-gel.csv")

MRI = "MRI_AGCM3_2_S"
CMCC = "CMCC_CM2_VHR4"

# Le README raisonne sur une fenetre mars a mai : tout l'extrait est retenu.
MARS_A_MAI = (3, 5)


def _mars():
    return ind.lire_csv_contrat(MARS)


def _annee():
    return ind.lire_csv_contrat(ANNEE)


def _manquantes():
    return ind.lire_csv_contrat(MANQUANTES)


def _ete():
    return ind.lire_csv_contrat(ETE)


def test_taille_des_jeux():
    """730 lignes pour l'annee, 62 pour mars, 62 pour mars a trous, 184 pour l'ete."""
    annee, mars, manquantes, ete = _annee(), _mars(), _manquantes(), _ete()
    assert len(annee[MRI]) == 365 and len(annee[CMCC]) == 365
    assert len(mars[MRI]) == 31 and len(mars[CMCC]) == 31
    assert len(manquantes[MRI]) == 31 and len(manquantes[CMCC]) == 31
    assert len(ete[MRI]) == 92 and len(ete[CMCC]) == 92


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


def test_aucun_jour_sous_moins_4_chez_cmcc():
    """Cas limite : CMCC n'a aucun jour a -4 degres ou moins sur l'annee 2049.

    Ce n'est pas une annee sans gel : le minimum de CMCC est -2,5 degres, donc
    a -2 il compte des jours. Le resultat depend du seuil autant que du modele.
    Le resultat attendu est l'entier 0, pas None : None signifierait « non
    calculable ».
    """
    s = _annee()
    assert ind.jours_de_gel(s[CMCC], -4.0, 1, 12) == 0
    faits = dict((nom, v) for nom, v, _ in
                 ind.indicateurs_culture(s[CMCC], "BLE_TENDRE_H", 49.2535, avertir=False))
    assert faits["gel"] == 0 and faits["gel"] is not None


def test_valeur_manquante_jamais_lue_comme_zero():
    """Contrat d'interface : une case vide n'est jamais lue comme un zero.

    series-reims-2049-mars-valeurs-manquantes.csv reprend mars 2049 avec
    cinq cases videes chez MRI : t_max du 1er et du 5 mars, t_min du 3 et du
    4 mars, precip du 7 mars (19,16 dans l'export).
    """
    s = _manquantes()[MRI]
    jour = {j["date"].day: j for j in s}
    assert jour[7]["precip"] is None
    assert jour[1]["t_max"] is None and jour[5]["t_max"] is None
    assert jour[3]["t_min"] is None and jour[4]["t_min"] is None


def test_precipitation_vide_ignoree_dans_le_cumul():
    """La pluie vide du 7 mars n'entre pas dans le cumul : 72,6 - 19,16 = 53,4."""
    s = _manquantes()[MRI]
    assert ind.cumul_precipitations(s, *MARS_A_MAI) == 53.4


def test_tmax_vide_tmin_valide_compte_pour_le_gel():
    """1er mars : t_max vide mais t_min a -3,1. Le jour compte a -2 degres."""
    s = _manquantes()[MRI]
    assert ind.jours_de_gel(s, -2.0, *MARS_A_MAI) == 1


def test_tmin_vide_jamais_lue_comme_zero():
    """3 et 4 mars : t_min vide (0,4 dans l'export). Lue comme 0, le gel
    a 0 degre passerait de 4 a 6."""
    s = _manquantes()[MRI]
    assert ind.jours_de_gel(s, 0.0, *MARS_A_MAI) == 4


def test_modele_sans_lacune_intact():
    """CMCC n'a aucune case vide : toujours 0 jour de gel a 0 degre en mars."""
    s = _manquantes()[CMCC]
    assert ind.jours_de_gel(s, 0.0, *MARS_A_MAI) == 0


def test_fenetre_vide_zero_et_avertissement():
    """La serie d'ete ne couvre pas mars a mai : 0 jour, et un avertissement."""
    s = _ete()[MRI]
    tampon = io.StringIO()
    with redirect_stderr(tampon):
        averti = ind.avertir_si_fenetre_non_couverte(s, *MARS_A_MAI, "test")
    assert ind.jours_de_gel(s, 0.0, *MARS_A_MAI) == 0
    assert averti is True


def test_comportement_actuel_lacunes_a_corriger_j3():
    """Fige le comportement ACTUEL du module face aux lacunes, pas le bon.

    Une ligne n'est plus ecartee que si t_min et t_max manquent toutes les
    deux. Mais rien ne signale encore les trous : les degres-jours sautent
    les jours incomplets sans avertissement et le resultat a l'air complet.
    Ce test devra echouer volontairement quand le controle de couverture
    arrivera au jalon 3.
    """
    s = _manquantes()[MRI]
    # Aucune ligne n'a ses deux temperatures vides : 31 jours lus sur 31.
    assert len(s) == 31
    # Le 1er mars (t_min -3,1, t_max vide) est garde : il compte a -2 et a 0.
    assert ind.jours_de_gel(s, -2.0, *MARS_A_MAI) == 1
    assert ind.jours_de_gel(s, 0.0, *MARS_A_MAI) == 4
    # 72,6 - 19,16 (case vide) = 53,4. Avant la correction : 37,5, car les
    # quatre lignes incompletes emportaient 15,89 mm de pluie.
    assert ind.cumul_precipitations(s, *MARS_A_MAI) == 53.4
    # Base 0 : 203,4 au lieu de 218,6. Les 1er, 3, 4 et 5 mars sont sautes
    # en silence, c'est le defaut que le controle de couverture traitera.
    assert ind.degres_jours(s, 0.0, None, *MARS_A_MAI) == 203.4


def test_lire_json_sans_modele_leve_une_erreur():
    """Cles sans suffixe de modele, comme dans le cache de DEV : erreur, pas {}.

    Le fichier est vide de donnees : seul le nom des cles compte ici.
    """
    daily = {"time": [], "temperature_2m_min": [], "temperature_2m_max": [],
             "temperature_2m_mean": [], "precipitation_sum": []}
    with tempfile.TemporaryDirectory() as dossier:
        chemin = os.path.join(dossier, "sans_suffixe.json")
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump({"latitude": 49.3, "elevation": 94.0, "daily": daily}, f)
        try:
            ind.lire_json(chemin)
        except ValueError as e:
            assert "temperature_2m_min_<modele>" in str(e)
        else:
            assert False, "lire_json aurait du lever ValueError"


def test_main_serie_vide_message_et_pas_de_plantage():
    """Un CSV au format du contrat sans aucune ligne : code 1, message, pas de trace."""
    with tempfile.TemporaryDirectory() as dossier:
        chemin = os.path.join(dossier, "vide.csv")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("id_commune;date;id_horizon;id_modele;t_min;t_max;t_moy;precip\n")
        r = subprocess.run([sys.executable, os.path.join(RACINE, "indicateurs.py"), chemin],
                           capture_output=True, text=True)
    assert r.returncode == 1, r.returncode
    assert "aucune serie lisible" in r.stderr
    assert "Traceback" not in r.stderr


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
