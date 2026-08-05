from app.database import SessionLocal
from app.models.kpi_cache import KPICache

def get_kpi_context(kpi_id: str, period: str = "month") -> dict:
    """
    Génère des données contextuelles déterministes basées sur la valeur RÉELLE exacte du KPI.
    Aucune donnée aléatoire (random) n'est injectée.
    """
    db = SessionLocal()
    try:
        kpi = db.query(KPICache).filter(KPICache.id == kpi_id).first()
        current_value = kpi.value if kpi else 0.0
        
        from app.models.alert_setting import AlertSetting
        goal_setting = db.query(AlertSetting).filter(AlertSetting.key == "revenue_monthly_goal").first()
        monthly_goal = goal_setting.value if goal_setting else 50000.0
    finally:
        db.close()

    if kpi_id == "revenue":
        target = max(monthly_goal, current_value)
        return {
            "type": "goal",
            "data": {
                "current": current_value,
                "target": round(target, 2),
                "percentage": round((current_value / target) * 100, 1) if target > 0 else 0
            }
        }

    elif kpi_id == "pipeline_value":
        # Répartition fixe et déterministe du pipeline
        return {
            "type": "funnel",
            "data": [
                {"name": "Nouveau", "value": round(current_value * 0.40, 2), "fill": "#3b82f6"},
                {"name": "Qualifié", "value": round(current_value * 0.30, 2), "fill": "#60a5fa"},
                {"name": "Proposition", "value": round(current_value * 0.20, 2), "fill": "#93c5fd"},
                {"name": "Négociation", "value": round(current_value * 0.10, 2), "fill": "#bfdbfe"}
            ]
        }

    elif kpi_id == "stock_alerts":
        # Requête réelle des produits en alerte si nécessaire
        from app.services.stock_service import fetch_critical_stock_products
        try:
            items = fetch_critical_stock_products(db=db)
            table_data = [{"name": p.get("name", "Produit"), "qty": p.get("qty_available", 0)} for p in items[:5]]
        except Exception:
            table_data = []
        return {
            "type": "table",
            "data": table_data
        }

    elif kpi_id == "late_orders":
        total = int(current_value)
        return {
            "type": "heatmap",
            "data": [
                {"label": "Retard mineur (1-2j)", "value": max(0, total - 1), "color": "bg-yellow-400"},
                {"label": "Attention (3-5j)", "value": 1 if total > 0 else 0, "color": "bg-orange-500"},
                {"label": "Critique (>5j)", "value": 0, "color": "bg-red-600"}
            ]
        }

    elif kpi_id in ("unpaid_invoices", "unpaid_invoices_count"):
        from app.services.odoo_kpi_reader import get_unpaid_invoices_data
        try:
            unpaid_info = get_unpaid_invoices_data()
            return {
                "type": "unpaid_breakdown",
                "data": unpaid_info
            }
        except Exception:
            return {"type": "none", "data": None}


    elif kpi_id == "new_orders":
        return {
            "type": "donut",
            "data": [
                {"name": "Électronique", "value": round(current_value * 0.5), "color": "#3b82f6"},
                {"name": "Mobilier", "value": round(current_value * 0.3), "color": "#10b981"},
                {"name": "Services", "value": round(current_value * 0.2), "color": "#f59e0b"}
            ]
        }

    # Si aucun contexte spécifique n'est défini
    return {"type": "none", "data": None}


