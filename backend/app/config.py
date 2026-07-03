from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    odoo_url: str
    odoo_db: str
    odoo_username: str
    odoo_api_key: str  # mot de passe/clé API Odoo

    class Config:
        env_file = ".env"
        extra = "ignore"  # ignore les autres variables du .env (POSTGRES_*, GROQ_*, etc.)


settings = Settings()
