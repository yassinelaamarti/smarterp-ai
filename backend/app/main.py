import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.routers import kpis, chat
from app.services.kpi_sync import sync_all

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

app.include_router(kpis.router)
app.include_router(chat.router)


@app.get("/")
def read_root():
    return {"status": "ok", "service": "SmartERP AI backend"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
