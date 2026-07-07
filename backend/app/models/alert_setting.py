from sqlalchemy import Column, String, Float

from app.database import Base


class AlertSetting(Base):
    """Configuration des seuils de déclenchement des alertes."""

    __tablename__ = "alert_settings"

    key = Column(String, primary_key=True)
    value = Column(Float, nullable=False)
    label = Column(String, nullable=False)
