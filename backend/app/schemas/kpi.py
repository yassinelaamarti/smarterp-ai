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
    sample_size: Optional[int] = None
    sample_warning_threshold: Optional[int] = 5
    sample_unit_label: Optional[str] = None
    criticality: Optional[Literal["normal", "attention", "critical"]] = "normal"


class AISummaryResponse(BaseModel):
    summary: str



