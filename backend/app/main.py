import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import kpis, chat, auth, alerts
from app.services.kpi_sync import sync_all
from app.models.user import User
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
    except Exception as e:
        logger.error(f"Error seeding default admin user: {e}")
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


@app.get("/")
def read_root():
    return {"status": "ok", "service": "SmartERP AI backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
