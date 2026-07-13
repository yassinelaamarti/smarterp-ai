from pydantic import BaseModel
from typing import Literal, Optional


class KPI(BaseModel):
    id: str
    label: str
    value: float
    unit: Optional[str] = None
    trend: Optional[Literal["up", "down", "stable"]] = None
    change_percent: Optional[float] = None


class AISummaryResponse(BaseModel):
    summary: str

