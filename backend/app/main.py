import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings as config_settings
from app.database import engine, Base, SessionLocal
from app.routers import kpis, chat, auth, alerts, settings, conversations, health_score, recommendations, root_cause
from app.services.kpi_sync import sync_all
from app.models.user import User
from app.models.tenant import Tenant
from app.models.alert_setting import AlertSetting
from app.models.kpi_cache import KPIHistoryCache
from app.models.ai_recommendation import AIRecommendation, AIActionLog
from app.models.root_cause_analysis import RootCauseAnalysis
from app.services.auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_background_task: asyncio.Task | None = None


async def _sync_loop():
    while True:
        await asyncio.sleep(config_settings.sync_interval_seconds)
        await asyncio.to_thread(sync_all)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Nettoyage de l'ancienne table ai_recommendations (pluriel) si elle existe
    db_init = SessionLocal()
    try:
        from sqlalchemy import text
        db_init.execute(text("DROP TABLE IF EXISTS ai_recommendations CASCADE"))
        db_init.commit()
        logger.info("Ancienne table ai_recommendations nettoyée.")
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage de l'ancienne table ai_recommendations: {e}")
    finally:
        db_init.close()

    Base.metadata.create_all(bind=engine)
    
    # Auto-migration des colonnes et des enums PostgreSQL
    db_mig = SessionLocal()
    try:
        from sqlalchemy import text
        for val in ['pending', 'executed', 'dismissed', 'failed', 'expired', 'acknowledged']:
            try:
                db_mig.execute(text(f"ALTER TYPE recommendationstatus ADD VALUE IF NOT EXISTS '{val}'"))
                db_mig.commit()
            except Exception:
                db_mig.rollback()

        for col_name, col_type in [
            ("report_schedule", "VARCHAR DEFAULT 'none'"),
            ("report_email", "VARCHAR"),
            ("last_report_sent", "VARCHAR")
        ]:
            try:
                db_mig.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                db_mig.commit()
                logger.info(f"Colonne {col_name} ajoutée avec succès à la table users.")
            except Exception:
                db_mig.rollback()

        try:
            db_mig.execute(text("ALTER TABLE ai_recommendation ADD COLUMN acknowledged_at TIMESTAMPTZ"))
            db_mig.commit()
            logger.info("Colonne acknowledged_at ajoutée avec succès à la table ai_recommendation.")
        except Exception:
            db_mig.rollback()
    except Exception as e:
        logger.error(f"Erreur lors de la migration de la base de données: {e}")
    finally:
        db_mig.close()

    
    # Seeder le tenant et l'utilisateur admin par défaut s'il n'y a pas d'utilisateurs
    db = SessionLocal()
    try:
        # Seeder le tenant par défaut
        import uuid
        DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
        tenant_exists = db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()
        if not tenant_exists:
            default_tenant = Tenant(
                id=DEFAULT_TENANT_ID,
                name="Tenant Principal PME"
            )
            db.add(default_tenant)
            db.commit()
            logger.info("Tenant principal par défaut créé.")
    except Exception as e:
        logger.error(f"Erreur lors du seeding du tenant par défaut: {e}")
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
                AlertSetting(key="recommendation_acknowledgment_ttl_hours", value=24.0, label="Délai de rappel des recommandations acquittées (heures)"),
            ]
            db.add_all(default_settings)
            db.commit()
            logger.info("Default alert settings seeded.")
        else:
            goal_exists = db.query(AlertSetting).filter(AlertSetting.key == "revenue_monthly_goal").first()
            if not goal_exists:
                db.add(AlertSetting(key="revenue_monthly_goal", value=50000.0, label="Objectif mensuel (MAD)"))
                db.commit()
                logger.info("Added missing revenue_monthly_goal setting.")

            unpaid_warn = db.query(AlertSetting).filter(AlertSetting.key == "unpaid_invoices_60_plus_warning").first()
            if not unpaid_warn:
                db.add(AlertSetting(key="unpaid_invoices_60_plus_warning", value=20.0, label="Impayés >60j (Avertissement %)"))
                db.add(AlertSetting(key="unpaid_invoices_60_plus_critical", value=40.0, label="Impayés >60j (Critique %)"))
                db.commit()
                logger.info("Added missing unpaid_invoices settings.")

            ttl_setting = db.query(AlertSetting).filter(AlertSetting.key == "recommendation_acknowledgment_ttl_hours").first()
            if not ttl_setting:
                db.add(AlertSetting(key="recommendation_acknowledgment_ttl_hours", value=24.0, label="Délai de rappel des recommandations acquittées (heures)"))
                db.commit()
                logger.info("Added missing recommendation_acknowledgment_ttl_hours setting.")


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

    # Initialisation du planificateur de rapports
    from app.services.report_scheduler import setup_scheduler
    setup_scheduler(app)

    yield

    # Arrêt du planificateur de rapports
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        app.state.scheduler.shutdown()
        logger.info("Planificateur de rapports arrêté.")

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"],
    allow_origin_regex=r"http://.*",
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
app.include_router(recommendations.router)
app.include_router(root_cause.router)



@app.get("/")
def read_root():
    return {"status": "ok", "service": "SmartERP AI backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
