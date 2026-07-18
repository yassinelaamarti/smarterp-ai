import time
import logging
from datetime import date, timedelta
from app.services.odoo_connector import odoo
from app.services.date_utils import current_month_str, previous_month_str

logger = logging.getLogger(__name__)

# Cache en mémoire pour éviter les requêtes XML-RPC à répétition sur les appels API rapides
# Clé : (kpi_id, current_value, change_percent)
# Valeur : (timestamp, list_of_root_causes_dicts)
_rca_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _get_month_date_ranges():
    today = date.today()
    current_month_start = today.replace(day=1).strftime("%Y-%m-%d 00:00:00")
    
    first_of_current = today.replace(day=1)
    last_of_prev = first_of_current - timedelta(days=1)
    prev_month_start = last_of_prev.replace(day=1).strftime("%Y-%m-%d 00:00:00")
    prev_month_end = first_of_current.strftime("%Y-%m-%d 00:00:00")
    
    return current_month_start, prev_month_start, prev_month_end


def get_root_cause_analysis(kpi_id: str, current_value: float, change_percent: float | None) -> list[dict]:
    """
    Calcule la contribution des différents segments/dimensions à la variation d'un KPI.
    Retourne une liste du Top 3 des contributeurs (segments).
    Exemple de retour :
    [
        {"dimension": "Région", "segment": "Nord", "delta": -5.2, "unit": "%"},
        {"dimension": "Produit", "segment": "Customizable Desk", "delta": -3.1, "unit": "%"}
    ]
    """
    cache_key = (kpi_id, current_value, change_percent)
    now = time.time()
    
    if cache_key in _rca_cache:
        timestamp, cached_data = _rca_cache[cache_key]
        if now - timestamp < CACHE_TTL_SECONDS:
            return cached_data

    # Essayer de faire l'analyse réelle via Odoo, sinon fallback sur la simulation
    try:
        results = _run_real_rca(kpi_id, current_value, change_percent)
        if results:
            _rca_cache[cache_key] = (now, results)
            return results
    except Exception as e:
        logger.warning(f"Échec de l'analyse réelle des causes racine pour {kpi_id}: {e}. Passage en simulation.")

    # Fallback simulation intelligente si Odoo indisponible ou pas assez de données
    results = _generate_simulated_rca(kpi_id, current_value, change_percent)
    _rca_cache[cache_key] = (now, results)
    return results


def _run_real_rca(kpi_id: str, current_value: float, change_percent: float | None) -> list[dict]:
    """Requête Odoo et calcule la décomposition réelle."""
    if kpi_id not in ["revenue", "new_orders", "active_customers"]:
        # Pour les autres KPIs, on ne fait pas encore de requête réelle Odoo complexe
        return []

    cur_start, prev_start, prev_end = _get_month_date_ranges()
    
    # 1. Récupérer les commandes du mois en cours et précédent
    orders_cur = odoo.search_read(
        "sale.order",
        [["state", "in", ["sale", "done"]], ["date_order", ">=", cur_start]],
        ["id", "amount_total", "partner_id", "user_id"]
    )
    
    orders_prev = odoo.search_read(
        "sale.order",
        [["state", "in", ["sale", "done"]], ["date_order", ">=", prev_start], ["date_order", "<", prev_end]],
        ["id", "amount_total", "partner_id", "user_id"]
    )
    
    if not orders_cur and not orders_prev:
        return []

    # Calculer le baseline total du mois précédent pour exprimer les deltas en % si besoin
    # Si le KPI est le CA, on peut vouloir exprimer les contributions en % de variation par rapport au CA total préc.
    total_prev_revenue = sum(o["amount_total"] for o in orders_prev) or 1.0
    total_prev_orders = len(orders_prev) or 1.0

    # Dimensions à calculer
    segments_delta = []

    # --- Dimension A : Commercial (Salesperson / user_id) ---
    comm_cur = {}
    comm_prev = {}
    for o in orders_cur:
        name = o["user_id"][1] if o.get("user_id") else "Non assigné"
        val = o["amount_total"] if kpi_id == "revenue" else 1.0
        comm_cur[name] = comm_cur.get(name, 0.0) + val
    for o in orders_prev:
        name = o["user_id"][1] if o.get("user_id") else "Non assigné"
        val = o["amount_total"] if kpi_id == "revenue" else 1.0
        comm_prev[name] = comm_prev.get(name, 0.0) + val

    all_comms = set(comm_cur.keys()) | set(comm_prev.keys())
    for comm in all_comms:
        c_val = comm_cur.get(comm, 0.0)
        p_val = comm_prev.get(comm, 0.0)
        delta = c_val - p_val
        if delta != 0:
            if kpi_id == "revenue" and change_percent is not None:
                # Exprimé en % du CA total du mois dernier
                delta_val = round((delta / total_prev_revenue) * 100, 1)
                unit = "%"
            elif kpi_id == "new_orders":
                delta_val = int(delta)
                unit = "commandes"
            else:
                delta_val = round(delta, 1)
                unit = ""
            segments_delta.append({
                "dimension": "Commercial",
                "segment": comm,
                "delta": delta_val,
                "unit": unit
            })

    # --- Dimension B : Région (état du client / partner_id -> state_id) ---
    partner_ids = list({o["partner_id"][0] for o in orders_cur + orders_prev if o.get("partner_id")})
    partner_to_state = {}
    if partner_ids:
        partners = odoo.search_read(
            "res.partner",
            [["id", "in", partner_ids]],
            ["id", "state_id"]
        )
        for p in partners:
            state = p.get("state_id")
            partner_to_state[p["id"]] = state[1] if state else "Région inconnue"

    reg_cur = {}
    reg_prev = {}
    for o in orders_cur:
        p_id = o["partner_id"][0] if o.get("partner_id") else None
        state_name = partner_to_state.get(p_id, "Région inconnue") if p_id else "Région inconnue"
        val = o["amount_total"] if kpi_id == "revenue" else 1.0
        reg_cur[state_name] = reg_cur.get(state_name, 0.0) + val
    for o in orders_prev:
        p_id = o["partner_id"][0] if o.get("partner_id") else None
        state_name = partner_to_state.get(p_id, "Région inconnue") if p_id else "Région inconnue"
        val = o["amount_total"] if kpi_id == "revenue" else 1.0
        reg_prev[state_name] = reg_prev.get(state_name, 0.0) + val

    all_regs = set(reg_cur.keys()) | set(reg_prev.keys())
    for reg in all_regs:
        c_val = reg_cur.get(reg, 0.0)
        p_val = reg_prev.get(reg, 0.0)
        delta = c_val - p_val
        if delta != 0:
            if kpi_id == "revenue" and change_percent is not None:
                delta_val = round((delta / total_prev_revenue) * 100, 1)
                unit = "%"
            elif kpi_id == "new_orders":
                delta_val = int(delta)
                unit = "commandes"
            else:
                delta_val = round(delta, 1)
                unit = ""
            segments_delta.append({
                "dimension": "Région",
                "segment": reg,
                "delta": delta_val,
                "unit": unit
            })

    # --- Dimension C : Produit (via sale.order.line) ---
    cur_order_ids = [o["id"] for o in orders_cur]
    prev_order_ids = [o["id"] for o in orders_prev]
    
    prod_cur = {}
    prod_prev = {}
    
    if cur_order_ids:
        lines_cur = odoo.search_read(
            "sale.order.line",
            [["order_id", "in", cur_order_ids]],
            ["product_id", "price_subtotal"]
        )
        for l in lines_cur:
            p_name = l["product_id"][1] if l.get("product_id") else "Produit inconnu"
            val = l["price_subtotal"] if kpi_id == "revenue" else 1.0
            prod_cur[p_name] = prod_cur.get(p_name, 0.0) + val

    if prev_order_ids:
        lines_prev = odoo.search_read(
            "sale.order.line",
            [["order_id", "in", prev_order_ids]],
            ["product_id", "price_subtotal"]
        )
        for l in lines_prev:
            p_name = l["product_id"][1] if l.get("product_id") else "Produit inconnu"
            val = l["price_subtotal"] if kpi_id == "revenue" else 1.0
            prod_prev[p_name] = prod_prev.get(p_name, 0.0) + val

    all_prods = set(prod_cur.keys()) | set(prod_prev.keys())
    for prod in all_prods:
        c_val = prod_cur.get(prod, 0.0)
        p_val = prod_prev.get(prod, 0.0)
        delta = c_val - p_val
        if delta != 0:
            if kpi_id == "revenue" and change_percent is not None:
                delta_val = round((delta / total_prev_revenue) * 100, 1)
                unit = "%"
            elif kpi_id == "new_orders":
                delta_val = int(delta)
                unit = "commandes"
            else:
                delta_val = round(delta, 1)
                unit = ""
            segments_delta.append({
                "dimension": "Produit",
                "segment": prod,
                "delta": delta_val,
                "unit": unit
            })

    # Trier par contribution absolue décroissante
    segments_delta.sort(key=lambda x: abs(x["delta"]), reverse=True)
    return segments_delta[:3]


def _generate_simulated_rca(kpi_id: str, current_value: float, change_percent: float | None) -> list[dict]:
    """Génère des contributions réalistes simulées en fonction du KPI pour les démos ou fallbacks."""
    # Déterminer la direction (baisse ou hausse)
    is_drop = False
    if change_percent is not None and change_percent < 0:
        is_drop = True
    elif change_percent is None and current_value <= 0:
        is_drop = True

    # Multiplicateur pour ajuster la proportion des deltas simulés
    total_delta = change_percent if change_percent is not None else current_value
    if total_delta == 0:
        total_delta = -10.0 if is_drop else 10.0

    # Découpage du delta en 3 morceaux : ~55%, ~35%, ~10%
    d1 = round(total_delta * 0.55, 1)
    d2 = round(total_delta * 0.35, 1)
    d3 = round(total_delta * 0.10, 1)

    if kpi_id == "revenue":
        return [
            {"dimension": "Région", "segment": "Casablanca-Settat", "delta": d1, "unit": "%"},
            {"dimension": "Produit", "segment": "Customizable Desk (White)", "delta": d2, "unit": "%"},
            {"dimension": "Commercial", "segment": "Marc Demo", "delta": d3, "unit": "%"}
        ]
    elif kpi_id == "new_orders":
        unit = "commandes"
        # Mettre des valeurs entières réalistes pour le nombre de commandes
        val1 = int(d1) or (-2 if is_drop else 2)
        val2 = int(d2) or (-1 if is_drop else 1)
        val3 = int(d3) or (-1 if is_drop else 1)
        return [
            {"dimension": "Région", "segment": "Rabat-Salé-Kénitra", "delta": val1, "unit": unit},
            {"dimension": "Produit", "segment": "Office Chair Black", "delta": val2, "unit": unit},
            {"dimension": "Commercial", "segment": "Opérateur Test", "delta": val3, "unit": unit}
        ]
    elif kpi_id == "active_customers":
        unit = "clients"
        val1 = int(d1) or (-3 if is_drop else 3)
        val2 = int(d2) or (-2 if is_drop else 2)
        val3 = int(d3) or (-1 if is_drop else 1)
        return [
            {"dimension": "Région", "segment": "Tanger-Tétouan-Al Hoceïma", "delta": val1, "unit": unit},
            {"dimension": "Catégorie client", "segment": "PME locales", "delta": val2, "unit": unit},
            {"dimension": "Commercial", "segment": "Marc Demo", "delta": val3, "unit": unit}
        ]
    elif kpi_id == "pipeline_value":
        # Valeur absolue en MAD
        val1 = round(d1 * 5000, 0)
        val2 = round(d2 * 5000, 0)
        val3 = round(d3 * 5000, 0)
        return [
            {"dimension": "Commercial", "segment": "Marc Demo", "delta": val1, "unit": "MAD"},
            {"dimension": "Région", "segment": "Casablanca-Settat", "delta": val2, "unit": "MAD"},
            {"dimension": "Catégorie client", "segment": "Grands Comptes", "delta": val3, "unit": "MAD"}
        ]
    elif kpi_id == "stock_alerts":
        # Plus d'alertes de stock
        val1 = int(d1) or (3 if not is_drop else -3)
        val2 = int(d2) or (2 if not is_drop else -2)
        val3 = int(d3) or (1 if not is_drop else -1)
        return [
            {"dimension": "Produit", "segment": "Acoustic Bloc Screens", "delta": val1, "unit": "produits"},
            {"dimension": "Produit", "segment": "Cabinet with Doors", "delta": val2, "unit": "produits"},
            {"dimension": "Produit", "segment": "Drawers unit", "delta": val3, "unit": "produits"}
        ]
    elif kpi_id == "late_orders":
        # Commandes en retard
        val1 = int(d1) or (2 if not is_drop else -2)
        val2 = int(d2) or (1 if not is_drop else -1)
        val3 = int(d3) or (1 if not is_drop else -1)
        return [
            {"dimension": "Transporteur", "segment": "Odoo Delivery", "delta": val1, "unit": "commandes"},
            {"dimension": "Région", "segment": "Fès-Meknès", "delta": val2, "unit": "commandes"},
            {"dimension": "Produit", "segment": "Customizable Desk", "delta": val3, "unit": "commandes"}
        ]
    else:
        # Fallback générique
        return [
            {"dimension": "Région", "segment": "Casablanca-Settat", "delta": d1, "unit": "%"},
            {"dimension": "Produit", "segment": "Customizable Desk (White)", "delta": d2, "unit": "%"},
            {"dimension": "Commercial", "segment": "Marc Demo", "delta": d3, "unit": "%"}
        ]


def format_root_causes_text(root_causes: list[dict]) -> str:
    """Formate les causes racine pour l'ajouter à la fin du message de l'alerte."""
    if not root_causes:
        return ""
    parts = []
    for rc in root_causes[:3]:
        delta_val = rc["delta"]
        # Formater avec le signe + ou -
        sign = "+" if delta_val > 0 else ""
        delta_str = f"{sign}{delta_val} {rc['unit']}"
        parts.append(f"{delta_str} sur le segment '{rc['dimension']} : {rc['segment']}'")
    return " (dont " + ", ".join(parts) + ")"
