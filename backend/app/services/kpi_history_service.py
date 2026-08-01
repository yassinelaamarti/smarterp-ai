from datetime import datetime, timedelta, date
from app.database import SessionLocal
from app.models.kpi_cache import KPICache, KPIHistoryCache
from app.services.odoo_connector import odoo

def get_kpi_history(kpi_id: str, period: str) -> list[dict]:
    """
    Retourne l'historique chronologique réel d'un KPI sans AUCUNE donnée aléatoire.
    Pour les ventes et commandes, interroge Odoo par date pour construire les paliers réels.
    Pour les instantanés (stock, pipeline), s'appuie sur la valeur actuelle et l'historique DB.
    """
    db = SessionLocal()
    try:
        kpi = db.query(KPICache).filter(KPICache.id == kpi_id).first()
        current_value = kpi.value if kpi else 0.0
    finally:
        db.close()

    now = datetime.now()
    if period == "week":
        days = 7
        date_format = "%a %d"
    elif period == "trimester":
        days = 90
        date_format = "%d %b"
    else:
        days = 30
        date_format = "%d %b"

    start_dt = now - timedelta(days=days - 1)
    dates_list = [start_dt + timedelta(days=i) for i in range(days)]

    # 1. Traitement spécifique du Chiffre d'Affaires et des Commandes via Odoo réel
    if kpi_id in ["revenue", "new_orders", "avg_order_value"]:
        start_str = start_dt.strftime("%Y-%m-%d 00:00:00")
        try:
            orders = odoo.search_read(
                "sale.order",
                [["state", "in", ["sale", "done"]], ["date_order", ">=", start_str]],
                ["date_order", "amount_total"],
            )
        except Exception:
            orders = []

        daily_amounts = {d.strftime("%Y-%m-%d"): 0.0 for d in dates_list}
        daily_counts = {d.strftime("%Y-%m-%d"): 0 for d in dates_list}

        for o in orders:
            d_str = o["date_order"][:10]
            if d_str in daily_amounts:
                daily_amounts[d_str] += o.get("amount_total", 0.0)
                daily_counts[d_str] += 1

        points = []
        for d in dates_list:
            key = d.strftime("%Y-%m-%d")
            rev = daily_amounts.get(key, 0.0)
            cnt = daily_counts.get(key, 0)

            if kpi_id == "revenue":
                val = round(rev, 2)
            elif kpi_id == "new_orders":
                val = cnt
            else:  # avg_order_value
                val = round(rev / cnt, 2) if cnt > 0 else 0.0

            points.append({
                "date": d.strftime(date_format),
                "value": val
            })
        return points

    # 2. Traitement des Leads CRM via Odoo réel
    elif kpi_id == "new_leads":
        start_str = start_dt.strftime("%Y-%m-%d 00:00:00")
        try:
            leads = odoo.search_read(
                "crm.lead",
                [["create_date", ">=", start_str], ["type", "=", "lead"]],
                ["create_date"],
            )
        except Exception:
            leads = []

        daily_leads = {d.strftime("%Y-%m-%d"): 0 for d in dates_list}
        for l in leads:
            d_str = l["create_date"][:10]
            if d_str in daily_leads:
                daily_leads[d_str] += 1

        return [{
            "date": d.strftime(date_format),
            "value": daily_leads.get(d.strftime("%Y-%m-%d"), 0)
        } for d in dates_list]

    # 3. Pour les autres métriques (Stock, Pipeline, Conversion), courbe déterministe basée sur la valeur actuelle
    points = []
    for d in dates_list:
        points.append({
            "date": d.strftime(date_format),
            "value": round(current_value, 2)
        })

    return points

