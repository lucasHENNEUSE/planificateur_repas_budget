import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Initialisation de l'application FastAPI (Référentiel C5 - API REST)
app = FastAPI(
    title="Eco-Frigo API",
    description="API de planification de repas et de gestion intelligente du frigo",
    version="1.0.0"
)

templates = Jinja2Templates(directory="templates")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

# Importation des routes de l'API depuis le module dédié pour un code modulaire
from api.api_routes import router as api_router
app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)