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


from datetime import date, timedelta
from app.schemas.kpi import KPI
from app.services.odoo_connector import odoo

logger = logging.getLogger(__name__)

_MONTHS_FR = [
    "janv.", "févr.", "mars", "avr.", "mai", "juin",
    "juil.", "août", "sept.", "oct.", "nov.", "déc.",
]


def _rolling_start_date(days: int = 30) -> str:
    """Retourne la date de début de la fenêtre glissante (ex: aujourd'hui - 30 jours)."""
    start_date = date.today() - timedelta(days=days)
    return start_date.strftime("%Y-%m-%d 00:00:00")


def _first_day_of_month() -> str:
    today = date.today()
    return today.replace(day=1).strftime("%Y-%m-%d 00:00:00")


def _add_months(d: date, months: int) -> date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    return date(year, month, 1)


# ---------------------------------------------------------------------
# KPIs de flux (Fenêtre glissante de 30 jours par défaut)
# ---------------------------------------------------------------------

def get_monthly_revenue(days: int = 30) -> float:
    """Chiffre d'affaires sur la fenêtre glissante (30 jours par défaut)."""
    orders = odoo.search_read(
        "sale.order",
        [["state", "in", ["sale", "done"]], ["date_order", ">=", _rolling_start_date(days)]],
        ["amount_total"],
    )
    return round(sum(o["amount_total"] for o in orders), 2)


def get_new_orders_count(days: int = 30) -> int:
    """Nombre de nouvelles commandes sur la fenêtre glissante (30 jours par défaut)."""
    return odoo.search_count(
        "sale.order",
        [["date_order", ">=", _rolling_start_date(days)]],
    )


def get_avg_order_value(revenue: float, orders_count: int) -> float:
    if orders_count == 0:
        return 0.0
    return round(revenue / orders_count, 2)


def get_stock_alerts_count(db=None) -> int:
    from app.services.stock_service import count_critical_stock_products
    return count_critical_stock_products(db=db)


def get_new_leads_count(days: int = 30) -> int:
    """Nombre de nouveaux leads CRM sur 30 jours."""
    return odoo.search_count(
        "crm.lead",
        [["create_date", ">=", _rolling_start_date(days)], ["type", "=", "lead"]],
    )


def get_conversion_rate(days: int = 30) -> float:
    """Taux de conversion des opportunités CRM sur 30 jours."""
    total = odoo.search_count(
        "crm.lead",
        [["create_date", ">=", _rolling_start_date(days)], ["type", "=", "opportunity"]],
    )
    if total == 0:
        return 0.0
    won = odoo.search_count(
        "crm.lead",
        [
            ["create_date", ">=", _rolling_start_date(days)],
            ["type", "=", "opportunity"],
            ["stage_id.is_won", "=", True],
        ],
    )
    return round((won / total) * 100, 1)


# ---------------------------------------------------------------------
# KPIs d'instantanés & Opérations
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


def get_active_customers_count(days: int = 30) -> int:
    """Nombre de clients distincts ayant passé au moins une commande sur 30 jours."""
    orders = odoo.search_read(
        "sale.order",
        [["date_order", ">=", _rolling_start_date(days)]],
        ["partner_id"],
    )
    partner_ids = {o["partner_id"][0] for o in orders if o.get("partner_id")}
    return len(partner_ids)


def get_late_orders_count() -> int:
    """
    Bons de livraison clients (stock.picking) non encore livrés (non 'done' ou 'cancel')
    dont la date de livraison prévue (scheduled_date) est déjà dépassée.
    Se baser sur stock.picking garantit que les commandes déjà livrées ne sont pas comptées.
    """
    now_str = date.today().strftime("%Y-%m-%d 23:59:59")
    try:
        late_pickings = odoo.search_count(
            "stock.picking",
            [
                ["picking_type_id.code", "=", "outgoing"],
                ["state", "not in", ["done", "cancel"]],
                ["scheduled_date", "<", now_str],
            ],
        )
        return late_pickings
    except Exception as e:
        logger.warning(f"Fallback sur sale.order pour late_orders: {e}")
        today_str = date.today().strftime("%Y-%m-%d")
        return odoo.search_count(
            "sale.order",
            [
                ["state", "=", "sale"],
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
# Assemblage des 10 KPIs Canoniques
# ---------------------------------------------------------------------

def get_kpis() -> list[KPI]:
    """Recalcule les 10 KPIs en interrogeant Odoo en direct."""
    try:
        revenue = get_monthly_revenue(30)
    except Exception as e:
        logger.error(f"Error calculating revenue: {e}")
        revenue = 0.0

    try:
        orders_count = get_new_orders_count(30)
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
        new_leads = get_new_leads_count(30)
    except Exception as e:
        logger.error(f"Error calculating new leads count: {e}")
        new_leads = 0.0

    try:
        conversion_rate = get_conversion_rate(30)
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
        active_customers = get_active_customers_count(30)
    except Exception as e:
        logger.error(f"Error calculating active customers: {e}")
        active_customers = 0

    try:
        late_orders = get_late_orders_count()
    except Exception as e:
        logger.error(f"Error calculating late orders: {e}")
        late_orders = 0

    return [
        KPI(id="revenue", label="Chiffre d'affaires (30j)", value=revenue, unit="MAD"),
        KPI(id="new_orders", label="Nouvelles commandes (30j)", value=orders_count, unit="commandes"),
        KPI(
            id="avg_order_value",
            label="Panier moyen (30j)",
            value=avg_order_value,
            unit="MAD",
        ),
        KPI(id="stock_alerts", label="Alertes stock bas", value=stock_alerts, unit="produits"),
        KPI(id="new_leads", label="Nouveaux leads CRM (30j)", value=new_leads, unit="leads"),
        KPI(id="conversion_rate", label="Taux de conversion (30j)", value=conversion_rate, unit="%"),
        KPI(id="pipeline_value", label="Pipeline CRM ouvert", value=pipeline_value, unit="MAD"),
        KPI(id="stock_value", label="Valorisation du stock", value=stock_value, unit="MAD"),
        KPI(id="active_customers", label="Clients actifs (30j)", value=active_customers, unit="clients"),
        KPI(id="late_orders", label="Commandes en retard", value=late_orders, unit="commandes"),
    ]

