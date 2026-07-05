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
