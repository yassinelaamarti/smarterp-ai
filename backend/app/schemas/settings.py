from pydantic import BaseModel

class AlertSettingSchema(BaseModel):
    key: str
    value: float
    label: str

    class Config:
        from_attributes = True

class AlertSettingsUpdate(BaseModel):
    settings: list[AlertSettingSchema]
