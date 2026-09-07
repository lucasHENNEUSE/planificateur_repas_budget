import os
from dotenv import load_dotenv
from google import genai
from PIL import Image
import pydantic
from typing import List

# 1. Charger la configuration et l'API Key
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# 2. Définir la structure exacte que l'on attend de l'IA (grâce à Pydantic)
class AnalyseFrigo(pydantic.BaseModel):
    ingredients_detectes: List[str]
    conseil_chef: str

# 3. Charger l'image du frigo
photo_frigo = Image.open("frigo.jpg")

# 4. Demander à l'IA de répondre STRICTEMENT au format structuré
print("Analyse du frigo et structuration des données en JSON...\n")
response = client.models.generate_content(
    model='gemini-3.6-flash',
    contents=[
        photo_frigo,
        "Analyse ce frigo et donne-moi la liste des ingrédients ainsi qu'un court conseil de chef."
    ],
    config={
        'response_mime_type': 'application/json',
        'response_schema': AnalyseFrigo,
    },
)

# 5. Afficher le résultat JSON brut
print("--- RÉSULTAT JSON STRUCTURÉ ---")
print(response.text)