"""
auth_service.py : Gestion de la sécurité et de l'authentification (OWASP).
Utilisation directe de 'bcrypt' pour un hachage robuste, simple et sans bug.
"""
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Clé secrète pour signer les jetons (à cacher dans un fichier .env en production)
SECRET_KEY = os.getenv("SECRET_KEY", "super_cle_secrete_eco_frigo_2026")
ALGORITHM = "HS256"

# Schéma de sécurité FastAPI pour intercepter les requêtes
security = HTTPBearer()


# ==========================================
# GESTION DES MOTS DE PASSE (BCRYPT NATIF)
# ==========================================

def get_password_hash(password: str) -> str:
    """Hache le mot de passe de manière sécurisée avec bcrypt."""
    # bcrypt a besoin d'être au format informatique pur (bytes), d'où le .encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    # On le re-transforme en texte classique pour le stocker facilement dans MongoDB
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe tapé correspond au mot de passe crypté de la base de données."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))



# GESTION DES JETONS DE CONNEXION (JWT)


def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=2)):
    """Crée un jeton d'accès temporaire (valable 2 heures)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Vérifie si le jeton fourni par l'utilisateur est valide et non expiré."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Votre session a expiré. Veuillez vous reconnecter.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Jeton de sécurité invalide.")