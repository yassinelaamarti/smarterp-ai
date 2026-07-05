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
    # llama-3.3-70b-versatile a été déprécié par Groq le 17 juin 2026.
    # openai/gpt-oss-120b est le modèle de remplacement recommandé par Groq.
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"

    # Authentification JWT
    secret_key: str = "changeme-generate-a-random-secret"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 jours

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
