import os
import json
import time
from typing import Optional
from google import genai
from google.genai import types

# --- CONFIGURATION INITIALE ---
# Récupération de la clé API et initialisation du client Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gemini_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
CLOUD_AI_MODEL = 'gemini-3.5-flash-lite'

def appeler_gemini_json(prompt: str) -> Optional[dict]:
    """
    Envoie un prompt au modèle Gemini et force une réponse au format JSON.
    Si Gemini est surchargé (erreur 503), on réessaie jusqu'à 3 fois.
    Retourne None si l'appel échoue.
    """
    if not gemini_client:
        print("Erreur : Clé API Google non trouvée.")
        return None

    for essai in range(3):
        try:
            response = gemini_client.models.generate_content(
                model=CLOUD_AI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Erreur lors de l'appel LLM Gemini : {str(e)}")
            if "503" not in str(e):
                return None   
            time.sleep(3)     # Gemini surchargé : on attend un peu avant de réessayer
    return None

# --- FONCTIONS MÉTIERS (Prompts) ---

def obtenir_magasins_depuis_llm(city: str):
    """
    Demande à l'IA de trouver des magasins Leclerc et Carrefour dans une ville.
    Retourne une liste de magasins (nom et adresse).
    """
    prompt = f"""
Trouve 2 à 4 supermarchés réels situés dans la ville de {city}.
RÈGLES STRICTES :
1. Limite-toi EXCLUSIVEMENT aux enseignes "E.Leclerc" et "Carrefour".
2. Réponds STRICTEMENT sous format JSON valide (tableau d'objets avec clés 'nom' et 'adresse').
3. Aucun texte avant ou après.
"""
    try:
        return appeler_gemini_json(prompt)
    except Exception:
        return None

def rediger_recette_depuis_llm(meal_name: str, total_people: int):
    """
    Demande à l'IA les ingrédients et les étapes d'un plat.
    Retourne {"ingredients": [...], "etapes": [...]}, ou None si l'IA échoue.
    """
    prompt = f"""Rédige une recette simple et réaliste, en français, pour : "{meal_name}", pour {total_people} personnes.
Donne des quantités réalistes et 4 à 7 étapes claires (avec temps et températures de cuisson).
Réponds uniquement en JSON, de cette forme :
{{"ingredients": ["800 g de filet de poulet", "300 g de riz"], "etapes": ["Préchauffer le four à 200 °C.", "Cuire le riz 12 minutes."]}}"""
    return appeler_gemini_json(prompt)