from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import kpis

app = FastAPI(
    title="SmartERP AI API",
    description="API d'analytics décisionnel et d'agent IA pour Odoo 17",
    version="0.1.0",
)

# Autoriser le frontend (localhost:3000) à appeler cette API pendant le développement.
# À restreindre à un domaine précis en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(kpis.router)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "SmartERP AI backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
