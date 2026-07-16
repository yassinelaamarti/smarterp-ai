from pydantic import BaseModel

class AlertSettingSchema(BaseModel):
    key: str
    value: float
    label: str

    class Config:
        from_attributes = True

from typing import Literal

class AlertSettingsUpdate(BaseModel):
    settings: list[AlertSettingSchema]

class ReportScheduleSchema(BaseModel):
    report_schedule: Literal["none", "daily", "weekly", "monthly"]
    report_email: str | None = None

