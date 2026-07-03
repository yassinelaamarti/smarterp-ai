"""
Service de calcul des KPIs — cette fois à partir des vraies données Odoo
(Ventes, CRM, Stock), via app/services/odoo_connector.py.

Chaque fonction get_xxx() ci-dessous fait un appel Odoo précis.
get_kpis() les assemble en une liste de KPI prête à être renvoyée
par l'API (voir routers/kpis.py).
"""

from datetime import date
from app.schemas.kpi import KPI
from app.services.odoo_connector import odoo


def _first_day_of_month() -> str:
    today = date.today()
    return today.replace(day=1).strftime("%Y-%m-%d 00:00:00")


def get_monthly_revenue() -> float:
    """Somme des commandes de vente confirmées depuis le début du mois."""
    orders = odoo.search_read(
        "sale.order",
        [["state", "in", ["sale", "done"]], ["date_order", ">=", _first_day_of_month()]],
        ["amount_total"],
    )
    return round(sum(o["amount_total"] for o in orders), 2)


def get_new_orders_count() -> int:
    return odoo.search_count(
        "sale.order",
        [["date_order", ">=", _first_day_of_month()]],
    )


def get_avg_order_value(revenue: float, orders_count: int) -> float:
    if orders_count == 0:
        return 0.0
    return round(revenue / orders_count, 2)


def get_stock_alerts_count() -> int:
    """Nombre de produits dont le stock disponible est bas (seuil simple : < 5)."""
    return odoo.search_count(
        "product.product",
        [["qty_available", "<", 5], ["type", "=", "product"]],
    )


def get_new_leads_count() -> int:
    return odoo.search_count(
        "crm.lead",
        [["create_date", ">=", _first_day_of_month()], ["type", "=", "lead"]],
    )


def get_conversion_rate() -> float:
    """Pourcentage d'opportunités gagnées parmi toutes les opportunités créées ce mois-ci."""
    total = odoo.search_count(
        "crm.lead",
        [["create_date", ">=", _first_day_of_month()], ["type", "=", "opportunity"]],
    )
    if total == 0:
        return 0.0
    won = odoo.search_count(
        "crm.lead",
        [
            ["create_date", ">=", _first_day_of_month()],
            ["type", "=", "opportunity"],
            ["stage_id.is_won", "=", True],
        ],
    )
    return round((won / total) * 100, 1)


def get_kpis() -> list[KPI]:
    revenue = get_monthly_revenue()
    orders_count = get_new_orders_count()

    return [
        KPI(
            id="revenue",
            label="Chiffre d'affaires (mois)",
            value=revenue,
            unit="MAD",
        ),
        KPI(
            id="new_orders",
            label="Nouvelles commandes",
            value=orders_count,
            unit="commandes",
        ),
        KPI(
            id="avg_order_value",
            label="Panier moyen",
            value=get_avg_order_value(revenue, orders_count),
            unit="MAD",
        ),
        KPI(
            id="stock_alerts",
            label="Alertes stock bas",
            value=get_stock_alerts_count(),
            unit="produits",
        ),
        KPI(
            id="new_leads",
            label="Nouveaux leads CRM",
            value=get_new_leads_count(),
            unit="leads",
        ),
        KPI(
            id="conversion_rate",
            label="Taux de conversion",
            value=get_conversion_rate(),
            unit="%",
        ),
    ]
