from pydantic import BaseModel
from typing import Literal, Optional


class KPISourceData(BaseModel):
    model: str
    domain: str
    formula: str


class KPI(BaseModel):
    id: str
    label: str
    value: float
    unit: Optional[str] = None
    trend: Optional[Literal["up", "down", "stable"]] = None
    change_percent: Optional[float] = None
    source_data: Optional[KPISourceData] = None


class AISummaryResponse(BaseModel):
    summary: str


