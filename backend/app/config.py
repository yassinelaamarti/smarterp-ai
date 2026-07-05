from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Odoo
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_api_key: str

    # Base de données (cache)
    database_url: str

    # Synchronisation en arrière-plan
    sync_interval_seconds: int = 900

    # Agent IA (Groq)
    groq_api_key: str
    groq_model: str = "llama-3.3-70b-versatile"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
