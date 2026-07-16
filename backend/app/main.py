import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import kpis, chat, auth, alerts, settings, conversations, health_score
from app.services.kpi_sync import sync_all
from app.models.user import User
from app.models.alert_setting import AlertSetting
from app.models.kpi_cache import KPIHistoryCache
from app.services.auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_background_task: asyncio.Task | None = None


async def _sync_loop():
    while True:
        await asyncio.sleep(settings.sync_interval_seconds)
        await asyncio.to_thread(sync_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    
    # Seeder l'utilisateur admin par défaut s'il n'y a pas d'utilisateurs
    db = SessionLocal()
    try:
        user_exists = db.query(User).first()
        if not user_exists:
            hashed_pw = get_password_hash("adminpassword")
            default_admin = User(
                email="admin@smarterp.ai",
                hashed_password=hashed_pw,
                full_name="Yassine Laamarti",
                role="admin",
                is_active=True
            )
            db.add(default_admin)
            db.commit()
            logger.info("Default admin user created: admin@smarterp.ai / adminpassword")

        # Seeder les paramètres d'alerte par défaut s'il n'y en a pas
        setting_exists = db.query(AlertSetting).first()
        if not setting_exists:
            default_settings = [
                AlertSetting(key="stock_critical", value=10.0, label="Seuil critique de stock bas"),
                AlertSetting(key="stock_warning", value=0.0, label="Seuil d'avertissement de stock bas"),
                AlertSetting(key="late_orders_critical", value=5.0, label="Seuil critique de commandes en retard"),
                AlertSetting(key="late_orders_warning", value=0.0, label="Seuil d'avertissement de commandes en retard"),
                AlertSetting(key="revenue_critical", value=-15.0, label="Seuil critique de baisse du CA (%)"),
                AlertSetting(key="revenue_warning", value=-5.0, label="Seuil d'avertissement de baisse du CA (%)"),
                AlertSetting(key="new_orders_critical", value=-30.0, label="Seuil critique de baisse des nouvelles commandes (%)"),
                AlertSetting(key="new_orders_warning", value=-20.0, label="Seuil d'avertissement de baisse des nouvelles commandes (%)"),
                AlertSetting(key="conversion_rate_critical", value=-30.0, label="Seuil critique de baisse du taux de conversion (%)"),
                AlertSetting(key="conversion_rate_warning", value=-20.0, label="Seuil d'avertissement de baisse du taux de conversion (%)"),
                AlertSetting(key="pipeline_value_critical", value=-40.0, label="Seuil critique de baisse du pipeline CRM (%)"),
                AlertSetting(key="pipeline_value_warning", value=-30.0, label="Seuil d'avertissement de baisse du pipeline CRM (%)"),
                AlertSetting(key="active_customers_critical", value=-30.0, label="Seuil critique de baisse des clients actifs (%)"),
                AlertSetting(key="active_customers_warning", value=-20.0, label="Seuil d'avertissement de baisse des clients actifs (%)"),
            ]
            db.add_all(default_settings)
            db.commit()
            logger.info("Default alert settings seeded.")

        # Seeder l'historique de démo s'il est vide
        history_exists = db.query(KPIHistoryCache).first()
        if not history_exists:
            from app.services.kpi_sync import seed_demo_history
            seed_demo_history(db)
            logger.info("Demo KPI history seeded for anomaly detection.")
    except Exception as e:
        logger.error(f"Error during seeding: {e}")
    finally:
        db.close()

    await asyncio.to_thread(sync_all)

    global _background_task
    _background_task = asyncio.create_task(_sync_loop())

    yield

    if _background_task:
        _background_task.cancel()


app = FastAPI(
    title="SmartERP AI API",
    description="API d'analytics décisionnel et d'agent IA pour Odoo 17",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(kpis.router)
app.include_router(chat.router)
app.include_router(alerts.router)
app.include_router(settings.router)
app.include_router(conversations.router)
app.include_router(health_score.router)



@app.get("/")
def read_root():
    return {"status": "ok", "service": "SmartERP AI backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
