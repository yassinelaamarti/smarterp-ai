from pydantic import BaseModel
from typing import Literal, Optional, List


class AlertSourceData(BaseModel):
    kpi_label: str
    kpi_value: float
    kpi_unit: Optional[str] = None
    model: str
    domain: str
    formula: str
    threshold_info: str
    history_values: Optional[List[float]] = None
    z_score: Optional[float] = None
    mean: Optional[float] = None
    root_causes: Optional[List[str]] = None
    partner_id: Optional[int] = None
    partner_ids: Optional[List[int]] = None
    lead_id: Optional[int] = None



class Alert(BaseModel):
    id: str
    kpi_id: str
    severity: Literal["warning", "critical", "info"]
    message: str
    is_anomaly: bool = False
    is_positive_trend: Optional[bool] = False
    source_data: Optional[AlertSourceData] = None



