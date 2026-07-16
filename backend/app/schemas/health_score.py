from pydantic import BaseModel


class HealthScoreFactor(BaseModel):
    label: str
    impact: float  # positif = bonus, négatif = pénalité


class HealthScore(BaseModel):
    score: int  # 0 à 100
    label: str
    factors: list[HealthScoreFactor]
