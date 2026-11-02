import os
import json
from typing import Optional
from google import genai
from google.genai import types

# --- CONFIGURATION INITIALE ---
# Récupération de la clé API et initialisation du client Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
gemini_client = genai.Client(api_key=GOOGLE_API_KEY) if GOOGLE_API_KEY else None
CLOUD_AI_MODEL = 'gemini-3.8-flash'

def appeler_gemini_json(prompt: str) -> Optional[dict]:
    """
    Envoie un prompt au modèle Gemini et force une réponse au format JSON.
    Gère aussi le nettoyage si l'IA rajoute des balises Markdown par erreur.
    """
    if not gemini_client:
        print("Erreur : Clé API Google non trouvée.")
        return None
    
    try:
        # Demande à Gemini de répondre uniquement en JSON
        response = gemini_client.models.generate_content(
            model=CLOUD_AI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        
        content = response.text.strip()
        
        # Nettoyage des balises de code Markdown si présentes
        if content.startswith("```json"):
            content = content[7:-3].strip()
        elif content.startswith("```"):
            content = content[3:-3].strip()
            
        return json.loads(content)
        
    except Exception as e:
        print(f"Erreur lors de l'appel LLM Gemini : {str(e)}")
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
    Demande à l'IA de rédiger les ingrédients et étapes pour un plat spécifique.
    Retourne un objet contenant la recette, ou une recette par défaut en cas d'erreur.
    """
    prompt = f"""Rédige la recette pour : "{meal_name}" pour {total_people} personnes.
Réponds STRICTEMENT sous format JSON valide :
{{
  "ingredients": ["1 kg de poulet", "800g de pommes de terre"],
  "etapes": ["Préchauffer le four.", "Cuire 1 heure."]
}}"""
    try:
        resultat = appeler_gemini_json(prompt)
        if resultat:
            return resultat
    except Exception:
        pass
        
    # Plan de secours si le LLM échoue à rédiger la recette
    return {
        "ingredients": ["Ingrédients standard du magasin"],
        "etapes": ["Préparer les ingrédients", "Cuire à feu moyen", "Servir chaud"]
    }