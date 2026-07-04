"""
Lecture des données brutes depuis Odoo (Ventes, CRM, Stock).

Important : ce fichier est le SEUL endroit du backend qui doit encore
appeler Odoo pour les KPIs. Il n'est utilisé que par services/kpi_sync.py,
en arrière-plan — jamais directement par une route API.
"""

import logging
from datetime import date
from app.schemas.kpi import KPI
from app.services.odoo_connector import odoo

logger = logging.getLogger(__name__)

_MONTHS_FR = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]


def _first_day_of_month() -> str:
    today = date.today()
    return today.replace(day=1).strftime("%Y-%m-%d 00:00:00")


def _add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    return date(year, month, 1)


# ---------------------------------------------------------------------
# 6 premiers KPIs (déjà en place)
# ---------------------------------------------------------------------

def get_monthly_revenue() -> float:
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


# ---------------------------------------------------------------------
# 4 nouveaux KPIs
# ---------------------------------------------------------------------

def get_pipeline_value() -> float:
    """Valeur totale des opportunités CRM encore ouvertes (ni gagnées, ni perdues)."""
    opportunities = odoo.search_read(
        "crm.lead",
        [
            ["type", "=", "opportunity"],
            ["active", "=", True],
            ["stage_id.is_won", "=", False],
        ],
        ["expected_revenue"],
    )
    return round(sum(o["expected_revenue"] for o in opportunities), 2)


def get_stock_valuation() -> float:
    """Valeur totale de l'inventaire actuel (quantité disponible x coût de revient)."""
    products = odoo.search_read(
        "product.product",
        [["type", "=", "product"]],
        ["qty_available", "standard_price"],
    )
    total = sum(p["qty_available"] * p["standard_price"] for p in products)
    return round(total, 2)


def get_active_customers_count() -> int:
    """Nombre de clients distincts ayant passé au moins une commande ce mois-ci."""
    orders = odoo.search_read(
        "sale.order",
        [["date_order", ">=", _first_day_of_month()]],
        ["partner_id"],
    )
    partner_ids = {o["partner_id"][0] for o in orders if o.get("partner_id")}
    return len(partner_ids)


def get_late_orders_count() -> int:
    """Commandes confirmées dont la date de livraison prévue est déjà dépassée."""
    today_str = date.today().strftime("%Y-%m-%d")
    return odoo.search_count(
        "sale.order",
        [
            ["state", "in", ["sale", "done"]],
            ["commitment_date", "<", today_str],
        ],
    )


# ---------------------------------------------------------------------
# Historique du CA (pour le graphique)
# ---------------------------------------------------------------------

def get_monthly_revenue_history(months: int = 6) -> list[dict]:
    current_month_start = date.today().replace(day=1)
    history = []

    for i in range(months - 1, -1, -1):
        start = _add_months(current_month_start, -i)
        end = _add_months(start, 1)

        orders = odoo.search_read(
            "sale.order",
            [
                ["state", "in", ["sale", "done"]],
                ["date_order", ">=", start.strftime("%Y-%m-%d 00:00:00")],
                ["date_order", "<", end.strftime("%Y-%m-%d 00:00:00")],
            ],
            ["amount_total"],
        )
        revenue = round(sum(o["amount_total"] for o in orders), 2)

        history.append({
            "month": start.strftime("%Y-%m"),
            "label": f"{_MONTHS_FR[start.month - 1]} {start.year}",
            "revenue": revenue,
        })

    return history


# ---------------------------------------------------------------------
# Assemblage des 10 KPIs
# ---------------------------------------------------------------------

def get_kpis() -> list[KPI]:
    """Recalcule les 10 KPIs en interrogeant Odoo en direct (coûteux, usage interne uniquement)."""
    try:
        revenue = get_monthly_revenue()
    except Exception as e:
        logger.error(f"Error calculating monthly revenue: {e}")
        revenue = 0.0

    try:
        orders_count = get_new_orders_count()
    except Exception as e:
        logger.error(f"Error calculating new orders count: {e}")
        orders_count = 0.0

    try:
        avg_order_value = get_avg_order_value(revenue, orders_count)
    except Exception as e:
        logger.error(f"Error calculating avg order value: {e}")
        avg_order_value = 0.0

    try:
        stock_alerts = get_stock_alerts_count()
    except Exception as e:
        logger.error(f"Error calculating stock alerts count: {e}")
        stock_alerts = 0.0

    try:
        new_leads = get_new_leads_count()
    except Exception as e:
        logger.error(f"Error calculating new leads count: {e}")
        new_leads = 0.0

    try:
        conversion_rate = get_conversion_rate()
    except Exception as e:
        logger.error(f"Error calculating conversion rate: {e}")
        conversion_rate = 0.0

    try:
        pipeline_value = get_pipeline_value()
    except Exception as e:
        logger.error(f"Error calculating CRM pipeline: {e}")
        pipeline_value = 0.0

    try:
        stock_value = get_stock_valuation()
    except Exception as e:
        logger.error(f"Error calculating stock valuation: {e}")
        stock_value = 0.0

    try:
        active_customers = get_active_customers_count()
    except Exception as e:
        logger.error(f"Error calculating active customers: {e}")
        active_customers = 0

    try:
        late_orders = get_late_orders_count()
    except Exception as e:
        logger.error(f"Error calculating late orders: {e}")
        late_orders = 0

    return [
        KPI(id="revenue", label="Chiffre d'affaires (mois)", value=revenue, unit="MAD"),
        KPI(id="new_orders", label="Nouvelles commandes", value=orders_count, unit="commandes"),
        KPI(
            id="avg_order_value",
            label="Panier moyen",
            value=avg_order_value,
            unit="MAD",
        ),
        KPI(id="stock_alerts", label="Alertes stock bas", value=stock_alerts, unit="produits"),
        KPI(id="new_leads", label="Nouveaux leads CRM", value=new_leads, unit="leads"),
        KPI(id="conversion_rate", label="Taux de conversion", value=conversion_rate, unit="%"),
        KPI(id="pipeline_value", label="Pipeline CRM ouvert", value=pipeline_value, unit="MAD"),
        KPI(id="stock_value", label="Valorisation du stock", value=stock_value, unit="MAD"),
        KPI(id="active_customers", label="Clients actifs (mois)", value=active_customers, unit="clients"),
        KPI(id="late_orders", label="Commandes en retard", value=late_orders, unit="commandes"),
    ]
