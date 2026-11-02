"""
Service d'ingestion massive Open Food Facts (Big Data).
Garantit le remplissage de la base MongoDB (même si l'API est capricieuse).
"""
import requests
from data.database import save_products, count_products, get_store_products

def scrape_store_catalog(store_name: str, catalog_url: str = "") -> list[dict]:
    # Objectif : Au moins 400 produits pour un RAG performant
    cible_produits = 400
    
    if count_products(store_name) < cible_produits:
        store_tag = "carrefour" if "carrefour" in store_name.lower() else "leclerc"
        produits_recuperes = []
        headers = {"User-Agent": "EcoFrigoApp/1.0 - Projet Etudiant"}
        
        # --- PLAN A : Recherche par tag de magasin ---
        for page in range(1, 4): 
            url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&tagtype_0=stores&tag_contains_0=contains&tag_0={store_tag}&json=true&page_size=150&page={page}"
            try:
                print(f"--- RECHERCHE OFF ({store_tag.upper()} - PAGE {page}) ---")
                response = requests.get(url, headers=headers, timeout=8)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("products", []):
                        nom = item.get("product_name_fr") or item.get("product_name")
                        if nom and len(nom) > 2:
                            rayon = item.get("categories", "Épicerie").split(",")[0].strip()
                            # Prix varié pour simuler la réalité
                            prix_varie = round(1.5 + (len(nom) % 4) * 0.5, 2)
                            produits_recuperes.append({
                                "nom": nom.strip(),
                                "prix": prix_varie, 
                                "rayon": rayon,
                                "enseigne": store_name
                            })
            except Exception as e:
                print(f"Erreur API Plan A : {e}")

        # --- PLAN B (SÉCURITÉ INFALLIBLE) : Si on a récupéré moins de 50 produits ---
        # (Cas typique où Open Food Facts n'a pas la donnée ou bugge sur Carrefour)
        if len(produits_recuperes) < 50:
            print(f"--- ⚠️ PEU DE RÉSULTATS POUR {store_tag.upper()}. ACTIVATION DU PLAN B (Alimentation large) ---")
            mots_cles = ["france", "bio", "légumes", "viande"]
            for mot in mots_cles:
                url_secours = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={mot}&search_simple=1&action=process&json=1&page_size=150"
                try:
                    resp = requests.get(url_secours, headers=headers, timeout=8)
                    if resp.status_code == 200:
                        for item in resp.json().get("products", []):
                            nom = item.get("product_name_fr") or item.get("product_name")
                            if nom and len(nom) > 2:
                                prix_varie = round(1.5 + (len(nom) % 4) * 0.5, 2)
                                produits_recuperes.append({
                                    "nom": nom.strip(),
                                    "prix": prix_varie,
                                    "rayon": "Général",
                                    "enseigne": store_name
                                })
                except Exception as e:
                    print(f"Erreur API Plan B : {e}")

        # --- SAUVEGARDE : C'est ici que MongoDB va ENFIN créer la collection ! ---
        if produits_recuperes:
            save_products(store_name, produits_recuperes)
            print(f"✅ SUCCÈS TOTAL : {len(produits_recuperes)} produits enregistrés pour {store_name} !")
        else:
            print("❌ ÉCHEC : Aucun produit trouvé.")

    return get_store_products(store_name)