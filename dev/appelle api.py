import os
import requests
from dotenv import load_dotenv
import json

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
    print(json.dumps(data, indent=4))
else:
    print("Erreur :", response.text)
    print(response.text)