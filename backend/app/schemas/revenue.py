from pydantic import BaseModel


class RevenuePoint(BaseModel):
    month: str   # ex: "2026-05" (utile pour trier/débugger)
    label: str   # ex: "mai 2026" (affiché sur le graphique)
    revenue: float
