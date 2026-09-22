import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENMETEO_API_KEY")

if not api_key:
    print("Clé OPENMETEO_API_KEY introuvable")
    exit()

print("Clé API trouvée")

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": 48.8566,
    "longitude": 2.3522,
    "current": "temperature_2m"
}

response = requests.get(url, params=params)

print("Status :", response.status_code)

if response.ok:
    data = response.json()
    print("Appel Open-Meteo réussi")
    print("Température :", data["current"]["temperature_2m"], "°C")
else:
    print("Erreur :", response.text)
    print(response.text)