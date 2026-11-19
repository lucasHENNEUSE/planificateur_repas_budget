# Image de départ : Python 3.12 (la même version que mon environnement local)
FROM python:3.12-slim

WORKDIR /app

# On installe d'abord les bibliothèques : Docker garde cette étape en mémoire
# tant que requirements.txt ne change pas (les builds suivants sont plus rapides)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Puis on copie le code de l'application
COPY . .

# Lancement de l'API ; 0.0.0.0 permet d'y accéder depuis l'extérieur du conteneur
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
