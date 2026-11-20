"""
database.py : Gestion de la base de données MongoDB.
Centralise la donnée dans deux grandes collections (Leclerc et Carrefour)
et filtre à l'intérieur par magasin/ville.
"""
import os
from pymongo import MongoClient

# Connexion à MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27019/")
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

db = client["planificateur_repas_db"]
menus_collection = db["menus_sauvegardes"]

def creer_index():
    """
    Crée les index MongoDB au démarrage de l'application (sans effet s'ils existent déjà).
    Un index accélère les recherches ; un index unique empêche aussi les doublons.
    """
    db["users"].create_index("email", unique=True)               # un seul compte par e-mail
    menus_collection.create_index([("type", 1), ("key", 1)])     # caches des menus et des recettes
    menus_collection.create_index([("type", 1), ("city", 1)])    # cache des magasins

def get_store_collection(store_name: str):
    """
    Analyse le nom du magasin et range la donnée dans l'un des 2 "gros tiroirs".
    """
    nom_lower = store_name.lower()
    if "carrefour" in nom_lower:
        return db["produits_carrefour"]
    else:
        # Si c'est Leclerc (ou par défaut)
        return db["produits_leclerc"]

def save_products(store_name: str, products: list[dict]):
    """Enregistre les produits dans la grande collection, en gardant la trace de la ville."""
    col = get_store_collection(store_name)
    for produit in products:
        # Upsert : On vérifie le nom ET l'enseigne exacte (la ville) pour ne pas mélanger
        col.update_one(
            {"nom": produit["nom"], "enseigne": store_name}, 
            {"$set": produit}, 
            upsert=True
        )

def get_store_products(store_name: str, limit: int = 200) -> list[dict]:
    """
    Va dans la grande collection (ex: produits_leclerc) et TRIE pour ne récupérer 
    QUE les produits de la ville demandée.
    """
    col = get_store_collection(store_name)
    # Le filtre {"enseigne": store_name} fait le tri exact !
    return list(col.find({"enseigne": store_name}, {"_id": 0}).limit(limit))

def count_products(store_name: str) -> int:
    """Compte uniquement les produits liés à la ville demandée dans la grande collection."""
    col = get_store_collection(store_name)
    return col.count_documents({"enseigne": store_name})