import os
import json
import time
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = os.path.join("data", "cache")
MODELES_CONTRAT = ("MRI_AGCM3_2_S", "CMCC_CM2_VHR4")
HORIZONS_CONTRAT = ("REF_2011_2020", "PROJ_2041_2050")


def formater_insee(id_commune: str) -> str:
    """Garantit un code INSEE texte sur 5 caractères avec zéro initial conservé."""
    code = str(id_commune).strip()
    if len(code) < 5 and code.isdigit():
        code = code.zfill(5)
    if len(code) != 5:
        raise ValueError(f"Code INSEE invalide '{id_commune}' : doit faire 5 caractères.")
    return code


def formater_valeur(val, decimales: int = 1) -> str:
    """Formate un flottant avec un point, ou renvoie une chaîne vide pour les valeurs manquantes."""
    if val is None:
        return ""
    return f"{float(val):.{decimales}f}"


def _chemin_cache(params_cache: dict) -> str:
    """Génère le chemin du fichier de cache à partir de l'empreinte MD5 des paramètres."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    empreinte = hashlib.md5(json.dumps(params_cache, sort_keys=True).encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{empreinte}.json")


def _appeler_openmeteo(latitude: float, longitude: float, start_date: str, end_date: str, id_modele: str) -> dict:
    """Appelle l'API Open-Meteo via requests (ou lit le cache local)."""
    params = {
        "latitude": round(float(latitude), 4),
        "longitude": round(float(longitude), 4),
        "start_date": start_date,
        "end_date": end_date,
        "models": id_modele,
        "daily": "temperature_2m_min,temperature_2m_max,temperature_2m_mean,precipitation_sum",
        "timezone": "Europe/Paris"
    }

    fichier_cache = _chemin_cache(params)
    if os.path.exists(fichier_cache):
        with open(fichier_cache, "r", encoding="utf-8") as f:
            return json.load(f)

    api_key = os.getenv("OPENMETEO_API_KEY")
    base_url = "https://customer-climate-api.open-meteo.com/v1/climate" if api_key else "https://climate-api.open-meteo.com/v1/climate"

    if api_key:
        params["apikey"] = api_key

    for tentative in range(1, 4):
        try:
            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code == 429 and tentative < 3:
                time.sleep(2 ** tentative)
                continue

            if response.status_code == 401:
                raise RuntimeError(
                    "Erreur 401 : Clé API non autorisée. Vérifiez la variable OPENMETEO_API_KEY dans votre fichier .env.")

            response.raise_for_status()
            data = response.json()
            break

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Erreur réseau avec l'API Open-Meteo : {e}")

    with open(fichier_cache, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    return data


def exporter_series_csv(
        id_commune: str, latitude: float, longitude: float, start_date: str, end_date: str,
        id_horizon: str = "PROJ_2041_2050", chemin_csv: str = "data/test/series-export.csv"
):
    code_insee = formater_insee(id_commune)
    lignes = ["id_commune;date;id_horizon;id_modele;t_min;t_max;t_moy;precip"]
    elevation = None

    for id_modele in MODELES_CONTRAT:
        data = _appeler_openmeteo(latitude, longitude, start_date, end_date, id_modele)
        if elevation is None and "elevation" in data:
            elevation = data["elevation"]

        daily = data.get("daily", {})
        dates = daily.get("time", [])
        t_mins = daily.get("temperature_2m_min", [])
        t_maxs = daily.get("temperature_2m_max", [])
        t_moys = daily.get("temperature_2m_mean", [])
        precips = daily.get("precipitation_sum", [])

        for i in range(len(dates)):
            ligne = ";".join([
                code_insee, dates[i], id_horizon, id_modele,
                formater_valeur(t_mins[i], 1), formater_valeur(t_maxs[i], 1),
                formater_valeur(t_moys[i], 1), formater_valeur(precips[i], 2)
            ])
            lignes.append(ligne)

    os.makedirs(os.path.dirname(chemin_csv), exist_ok=True)
    with open(chemin_csv, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lignes) + "\n")

    chemin_elevation = os.path.join(os.path.dirname(chemin_csv), f"elevation-{code_insee}.json")
    with open(chemin_elevation, "w", encoding="utf-8") as f:
        json.dump({"id_commune": code_insee, "elevation": elevation}, f, ensure_ascii=False, indent=2)

    return chemin_csv


if __name__ == "__main__":
    csv_genere = exporter_series_csv(
        id_commune="51454", latitude=49.2583, longitude=4.0317,
        start_date="2049-01-01", end_date="2049-12-31",
        chemin_csv="data/test/series-reims-2049-complete.csv"
    )
    print(f"Export réussi : {csv_genere}")