   # test_cle.py : vérifie que la clé API de l'équipe fonctionne
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()  # charge la clé depuis .env (à appeler AVANT de créer le client)

reponse = Anthropic().messages.with_raw_response.create(
    model="claude-haiku-4-5",  # seul modèle ouvert sur le compte fourni
    max_tokens=50,             # petit : on économise l'enveloppe de l'équipe
    messages=[{"role": "user", "content": "Dis bonjour."}],
)
print(reponse.headers.get("anthropic-workspace-id"))  # doit afficher wrkspc_...

usage = reponse.parse().usage  # à noter dans le journal IA
print("tokens entrée :", usage.input_tokens, "| sortie :", usage.output_tokens)
