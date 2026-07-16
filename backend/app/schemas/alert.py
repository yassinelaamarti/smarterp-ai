from pydantic import BaseModel
from typing import Literal


class Alert(BaseModel):
    id: str
    kpi_id: str
    severity: Literal["warning", "critical"]
    message: str
    is_anomaly: bool = False

