import uuid
from sqlalchemy import Column, String, UUID
from app.database import Base


class Tenant(Base):
    """Représente un locataire (PME cliente) de SmartERP AI."""

    __tablename__ = "tenant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
