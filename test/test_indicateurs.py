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
import faits  # noqa: E402

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
    faits = dict((nom, v) for nom, v, *_ in
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


def _jours_mars(annee, t_mins):
    """Une serie minimale : un jour de mars par valeur de t_min donnee."""
    from datetime import date
    return [{"date": date(annee, 3, i + 1), "t_min": tm, "t_max": 10.0, "precip": 1.0}
            for i, tm in enumerate(t_mins)]


def test_moyenne_sur_deux_annees_et_nb_annees():
    """4 jours de gel en 2041, 2 en 2042 : la moyenne est 3, sur 2 annees."""
    serie = (_jours_mars(2041, [-3.0, -3.0, -3.0, -3.0, 5.0])
             + _jours_mars(2042, [-3.0, -3.0, 5.0, 5.0, 5.0]))
    valeur, n = ind.moyenne_sur_annees(
        serie, lambda j: ind.jours_de_gel(j, -2.0, *MARS_A_MAI))
    assert (valeur, n) == (3.0, 2)


def test_une_seule_annee_valeur_inchangee_et_nb_annees_egal_1():
    """Jeu de test sur 2049 seule : la valeur ne change pas, nb_annees vaut 1."""
    s = _annee()[MRI]
    direct = ind.jours_de_gel(s, -2.0, 3, 5)
    valeur, n = ind.moyenne_sur_annees(s, lambda j: ind.jours_de_gel(j, -2.0, 3, 5))
    assert valeur == direct and n == 1
    faits = {nom: (v, u, nb) for nom, v, u, nb in
             ind.indicateurs_culture(s, "VIGNE", 49.2535, avertir=False)}
    assert faits["gel"][0] == ind.jours_de_gel(s, -2.0, 3, 5)
    assert all(nb == 1 for _, _, nb in faits.values())


def test_serie_vide_non_calculable_pas_zero():
    """Aucune annee : None et 0 annee, jamais un 0 qui passerait pour un resultat."""
    assert ind.moyenne_sur_annees([], lambda j: 0) == (None, 0)


def _jours_en(mois, t_mins=None, t_maxs=None):
    """Une serie minimale de 2049 : un jour du mois donne par valeur."""
    from datetime import date
    valeurs = t_mins if t_mins is not None else t_maxs
    return [{"date": date(2049, mois, i + 1),
             "t_min": t_mins[i] if t_mins is not None else 5.0,
             "t_max": t_maxs[i] if t_maxs is not None else 10.0,
             "precip": 0.0} for i in range(len(valeurs))]


def test_gel_jour_pose_sur_le_seuil():
    """Un jour a exactement -4,0 : compte avec <=, pas avec <.

    Valeurs choisies a la main : -4,1 est sous le seuil, -4,0 est dessus,
    -3,9 et 0,0 sont au-dessus. Strict : 1 jour. Large : 2 jours.
    """
    s = _jours_en(3, t_mins=[-4.1, -4.0, -3.9, 0.0])
    assert ind.jours_de_gel(s, -4.0, *MARS_A_MAI) == 1
    assert ind.jours_de_gel(s, -4.0, *MARS_A_MAI, "<") == 1
    assert ind.jours_de_gel(s, -4.0, *MARS_A_MAI, "<=") == 2
    assert ind.jours_de_gel(s, -4.0, *MARS_A_MAI, "indetermine") == 1


def test_stress_jour_pose_sur_le_seuil():
    """Un jour a exactement 35,0 : compte avec >=, pas avec >.

    34,9 est sous le seuil, 35,0 est dessus, 35,1 est au-dessus. Strict : 1
    jour. Large : 2 jours.
    """
    s = _jours_en(7, t_maxs=[34.9, 35.0, 35.1])
    assert ind.jours_echaudage(s, 35.0, 7, 8) == 1
    assert ind.jours_echaudage(s, 35.0, 7, 8, ">") == 1
    assert ind.jours_echaudage(s, 35.0, 7, 8, ">=") == 2
    assert ind.jours_echaudage(s, 35.0, 7, 8, "indetermine") == 1


def test_operateur_inconnu_leve_une_erreur():
    """Un sens inconnu ou vide n'est jamais remplace en silence."""
    s = _jours_en(3, t_mins=[-5.0])
    for mauvais in ("=>", "", None, "egal"):
        for fonction in (ind.jours_de_gel, ind.jours_echaudage):
            try:
                fonction(s, 0.0, 3, 5, mauvais)
            except ValueError as e:
                assert "operateur inconnu" in str(e)
            else:
                assert False, f"{fonction.__name__} : {mauvais!r} aurait du lever ValueError"


def test_operateurs_des_cultures_dans_indicateurs_culture():
    """Chaque culture compte au bord de son seuil selon son operateur CULTURES.

    Un seul jour pose exactement sur le seuil, dans la fenetre de l'indicateur.
    Ble gel (<) et echaudage (>) : 0. Mais gel (<) : 0, mais stress (>=) : 1.
    Vigne gel (indetermine, donc <) : 0, vigne stress (>=) : 1.
    """
    def faits(serie, id_culture):
        return {nom: v for nom, v, *_ in
                ind.indicateurs_culture(serie, id_culture, 49.2535, avertir=False)}

    assert faits(_jours_en(3, t_mins=[-4.0]), "BLE_TENDRE_H")["gel"] == 0
    assert faits(_jours_en(5, t_maxs=[30.0]), "BLE_TENDRE_H")["echaudage"] == 0
    assert faits(_jours_en(9, t_mins=[0.0]), "MAIS_GRAIN")["gel"] == 0
    assert faits(_jours_en(7, t_maxs=[35.0]), "MAIS_GRAIN")["stress_thermique"] == 1
    assert faits(_jours_en(4, t_mins=[-2.0]), "VIGNE")["gel"] == 0
    assert faits(_jours_en(7, t_maxs=[35.0]), "VIGNE")["stress_thermique"] == 1


def test_operateurs_valides_pour_toutes_les_cultures():
    """op_gel et op_stress de CULTURES sont tous lisibles par comparateur()."""
    for id_culture, seuils in ind.CULTURES.items():
        ind.comparateur(seuils["op_gel"], ind.REPLI_GEL)
        ind.comparateur(seuils["op_stress"], ind.REPLI_STRESS)


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
