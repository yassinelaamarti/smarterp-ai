from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class User(Base):
    """Représente un utilisateur de SmartERP AI."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)  # ex: "admin", "user"
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Configuration des rapports programmés
    report_schedule = Column(String, default="none", nullable=False)  # "none", "daily", "weekly", "monthly"
    report_email = Column(String, nullable=True)
    last_report_sent = Column(String, nullable=True)  # ex: "2026-07-16"

