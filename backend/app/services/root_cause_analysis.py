import json
import time
import logging
from datetime import date, timedelta
from typing import Optional

from groq import Groq
from app.config import settings
from app.services.odoo_connector import odoo

logger = logging.getLogger(__name__)

# Cache en mémoire
_rca_cache = {}
CACHE_TTL_SECONDS = 300  # 5 minutes

KPI_LABELS = {
    "revenue": "Chiffre d'affaires",
    "new_orders": "Nouvelles commandes",
    "active_customers": "Clients actifs",
    "new_leads": "Nouveaux leads CRM",
    "pipeline_value": "Valeur du pipeline CRM",
    "stock_alerts": "Alertes de stock bas",
    "late_orders": "Commandes en retard",
    "conversion_rate": "Taux de conversion",
}


def format_segment_label(dimension: str, segment_raw: str) -> str:
    """
    Fonction unique de formatage des libellés de segments.
    Nettoie les préfixes (ex: 'Région Casablanca-Settat' -> 'Casablanca-Settat', 'California (US)' -> 'California').
    """
    if not segment_raw:
        return ""
    
    clean = str(segment_raw).strip()
    for prefix in [
        "Catégorie client : Client : ", "Catégorie client : ", "Client : ", "Client ",
        "Catégorie : ", "Catégorie ", "Région : ", "Région ", "Commercial : ", "Commercial ", "Étape : ", "Produit : ", "Produit "
    ]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):].strip()

    if clean.endswith(" (US)"):
        clean = clean[:-5].strip()

    return clean


def _get_month_date_ranges():
    today = date.today()
    current_month_start = today.replace(day=1).strftime("%Y-%m-%d 00:00:00")
    
    first_of_current = today.replace(day=1)
    last_of_prev = first_of_current - timedelta(days=1)
    prev_month_start = last_of_prev.replace(day=1).strftime("%Y-%m-%d 00:00:00")
    prev_month_end = first_of_current.strftime("%Y-%m-%d 00:00:00")
    
    return current_month_start, prev_month_start, prev_month_end


def compute_root_cause_data(
    kpi_id: str,
    current_value: float = 0.0,
    change_percent: Optional[float] = None,
    period_current: str = "Mois en cours",
    period_previous: str = "Mois précédent"
) -> dict:
    """
    Calcule la décomposition réelle d'un KPI depuis Odoo.
    Si la décomposition n'est pas calculable pour cette entité (pas de décomposition par segment ou ID non reconnu),
    retourne un résultat explicite avec breakdown vide et message clair.
    """
    kpi_name = KPI_LABELS.get(kpi_id, kpi_id)
    try:
        real_data = _run_real_rca_decomposition(kpi_id, current_value, change_percent, period_current, period_previous)
        if real_data and real_data.get("breakdown"):
            return real_data
    except Exception as e:
        logger.warning(f"Note décomposition réelle Odoo pour {kpi_id}: {e}.")

    return {
        "kpi_name": kpi_name,
        "period_current": period_current,
        "period_previous": period_previous,
        "delta_total": 0.0,
        "delta_total_pct": 0.0,
        "breakdown": [],
        "residual_pct": 0.0,
        "message": "Aucune décomposition disponible pour cette entité"
    }


def _run_real_rca_decomposition(
    kpi_id: str,
    current_value: float,
    change_percent: Optional[float],
    period_current: str,
    period_previous: str
) -> Optional[dict]:
    ALLOWED_RCA_KPIS = {"revenue", "new_orders", "active_customers", "new_leads", "late_orders", "unpaid_invoices"}
    if kpi_id not in ALLOWED_RCA_KPIS:
        return None

    kpi_name = KPI_LABELS.get(kpi_id, kpi_id)
    comp_id = settings.odoo_company_id
    cur_start, prev_start, prev_end = _get_month_date_ranges()

    # A. Nouveaux Leads CRM (crm.lead)
    if kpi_id == "new_leads":
        leads_cur = odoo.search_read(
            "crm.lead",
            [
                ["type", "=", "lead"],
                ["create_date", ">=", cur_start],
                ["company_id", "in", [False, comp_id]],
            ],
            ["id", "name", "user_id", "partner_id"]
        ) or []

        leads_prev = odoo.search_read(
            "crm.lead",
            [
                ["type", "=", "lead"],
                ["create_date", ">=", prev_start],
                ["create_date", "<", prev_end],
                ["company_id", "in", [False, comp_id]],
            ],
            ["id", "name", "user_id", "partner_id"]
        ) or []

        if not leads_cur and not leads_prev:
            return None

        cur_total = float(len(leads_cur))
        prev_total = float(len(leads_prev))
        delta_total = cur_total - prev_total

        user_cur, user_prev = {}, {}
        for l in leads_cur:
            u_name = l["user_id"][1] if l.get("user_id") else "Non assigné"
            user_cur[u_name] = user_cur.get(u_name, 0.0) + 1.0
        for l in leads_prev:
            u_name = l["user_id"][1] if l.get("user_id") else "Non assigné"
            user_prev[u_name] = user_prev.get(u_name, 0.0) + 1.0

        all_segments = []
        for u in set(user_cur.keys()) | set(user_prev.keys()):
            delta = user_cur.get(u, 0.0) - user_prev.get(u, 0.0)
            if delta != 0:
                all_segments.append({"dimension": "sales_rep", "segment": format_segment_label("sales_rep", u), "delta": delta})

        all_segments.sort(key=lambda x: abs(x["delta"]), reverse=True)
        top3 = all_segments[:3]

        breakdown = []
        explained_pct_sum = 0.0
        total_abs = sum(abs(s["delta"]) for s in all_segments) or 1.0
        for s in top3:
            contrib = round((s["delta"] / delta_total) * 100.0, 1) if abs(delta_total) > 1e-6 else round((s["delta"] / total_abs) * 100.0, 1)
            contrib = max(-100.0, min(100.0, contrib))
            explained_pct_sum += abs(contrib)
            breakdown.append({
                "dimension": s["dimension"],
                "segment": s["segment"],
                "delta": round(s["delta"], 2),
                "contribution_pct": contrib
            })

        return {
            "kpi_name": kpi_name,
            "period_current": period_current,
            "period_previous": period_previous,
            "delta_total": round(delta_total, 2),
            "delta_total_pct": round(change_percent or 0.0, 1),
            "breakdown": breakdown,
            "residual_pct": round(max(0.0, 100.0 - explained_pct_sum), 1)
        }

    # B. Factures Impayées
    if kpi_id in ["unpaid_invoices", "unpaid_invoices_count"]:
        invoices = odoo.search_read(
            "account.move",
            [
                ["move_type", "=", "out_invoice"],
                ["state", "=", "posted"],
                ["payment_state", "in", ["not_paid", "partial"]],
                ["company_id", "=", comp_id],
            ],
            ["name", "partner_id", "amount_residual", "invoice_user_id"],
        ) or []

        if not invoices:
            return None

        total_res = sum(i.get("amount_residual", 0.0) for i in invoices)
        total_cnt = float(len(invoices))
        delta_total = total_res if kpi_id == "unpaid_invoices" else total_cnt

        part_map, user_map = {}, {}
        for inv in invoices:
            p_name = inv["partner_id"][1] if inv.get("partner_id") else "Client inconnu"
            u_name = inv["invoice_user_id"][1] if inv.get("invoice_user_id") else "Non assigné"
            val = inv.get("amount_residual", 0.0) if kpi_id == "unpaid_invoices" else 1.0

            part_map[p_name] = part_map.get(p_name, 0.0) + val
            user_map[u_name] = user_map.get(u_name, 0.0) + val

        all_segments = []
        for p, val in part_map.items():
            all_segments.append({"dimension": "customer_category", "segment": format_segment_label("customer", p), "delta": val})
        for u, val in user_map.items():
            all_segments.append({"dimension": "sales_rep", "segment": format_segment_label("sales_rep", u), "delta": val})

        all_segments.sort(key=lambda x: abs(x["delta"]), reverse=True)
        top3 = all_segments[:3]

        breakdown = []
        sum_pct = 0.0
        for s in top3:
            contrib = round((s["delta"] / delta_total) * 100.0, 1) if delta_total > 0 else 0.0
            contrib = max(-100.0, min(100.0, contrib))
            sum_pct += abs(contrib)
            breakdown.append({
                "dimension": s["dimension"],
                "segment": s["segment"],
                "delta": round(s["delta"], 2),
                "contribution_pct": contrib,
            })

        residual_pct = round(max(0.0, 100.0 - sum_pct), 1)
        return {
            "kpi_name": kpi_name,
            "period_current": period_current,
            "period_previous": period_previous,
            "delta_total": round(delta_total, 2),
            "delta_total_pct": round(change_percent or 0.0, 1),
            "breakdown": breakdown,
            "residual_pct": residual_pct,
        }

    # C. Commandes en Retard
    if kpi_id == "late_orders":
        now_str = date.today().strftime("%Y-%m-%d 23:59:59")
        late_pickings = odoo.search_read(
            "stock.picking",
            [
                ["picking_type_id.code", "=", "outgoing"],
                ["state", "not in", ["done", "cancel"]],
                ["scheduled_date", "<", now_str],
                ["company_id", "=", comp_id],
            ],
            ["name", "partner_id", "user_id"],
        ) or []

        if not late_pickings:
            return None

        total_cnt = float(len(late_pickings))
        part_map = {}
        for p in late_pickings:
            p_name = p["partner_id"][1] if p.get("partner_id") else "Client inconnu"
            part_map[p_name] = part_map.get(p_name, 0.0) + 1.0

        all_segments = []
        for p, cnt in part_map.items():
            all_segments.append({"dimension": "customer_category", "segment": format_segment_label("customer", p), "delta": cnt})

        all_segments.sort(key=lambda x: abs(x["delta"]), reverse=True)
        top3 = all_segments[:3]

        breakdown = []
        sum_pct = 0.0
        for s in top3:
            contrib = round((s["delta"] / total_cnt) * 100.0, 1) if total_cnt > 0 else 0.0
            contrib = max(-100.0, min(100.0, contrib))
            sum_pct += abs(contrib)
            breakdown.append({
                "dimension": s["dimension"],
                "segment": s["segment"],
                "delta": round(s["delta"], 2),
                "contribution_pct": contrib,
            })

        residual_pct = round(max(0.0, 100.0 - sum_pct), 1)
        return {
            "kpi_name": kpi_name,
            "period_current": period_current,
            "period_previous": period_previous,
            "delta_total": round(total_cnt, 2),
            "delta_total_pct": round(change_percent or 0.0, 1),
            "breakdown": breakdown,
            "residual_pct": residual_pct,
        }

    # D. Alertes Stock Bas
    if kpi_id == "stock_alerts":
        stock_prods = odoo.search_read(
            "product.product",
            [
                ["type", "=", "product"],
                ["qty_available", "<", 5],
            ],
            ["name", "categ_id", "qty_available"],
        ) or []

        if not stock_prods:
            return None

        total_cnt = float(len(stock_prods))
        cat_map = {}
        for p in stock_prods:
            cat = p["categ_id"][1] if p.get("categ_id") else "Sans catégorie"
            cat_map[cat] = cat_map.get(cat, 0.0) + 1.0

        all_segments = []
        for cat, cnt in cat_map.items():
            all_segments.append({"dimension": "product", "segment": format_segment_label("product", cat), "delta": cnt})

        all_segments.sort(key=lambda x: abs(x["delta"]), reverse=True)
        top3 = all_segments[:3]

        breakdown = []
        sum_pct = 0.0
        for s in top3:
            contrib = round((s["delta"] / total_cnt) * 100.0, 1) if total_cnt > 0 else 0.0
            contrib = max(-100.0, min(100.0, contrib))
            sum_pct += abs(contrib)
            breakdown.append({
                "dimension": s["dimension"],
                "segment": s["segment"],
                "delta": round(s["delta"], 2),
                "contribution_pct": contrib,
            })

        residual_pct = round(max(0.0, 100.0 - sum_pct), 1)
        return {
            "kpi_name": kpi_name,
            "period_current": period_current,
            "period_previous": period_previous,
            "delta_total": round(total_cnt, 2),
            "delta_total_pct": round(change_percent or 0.0, 1),
            "breakdown": breakdown,
            "residual_pct": residual_pct,
        }

    # E. CA, Nouvelles Commandes, Clients Actifs (sale.order)
    orders_cur = odoo.search_read(
        "sale.order",
        [
            ["state", "in", ["sale", "done"]],
            ["date_order", ">=", cur_start],
            ["company_id", "=", comp_id],
        ],
        ["id", "amount_total", "partner_id", "user_id"]
    ) or []

    orders_prev = odoo.search_read(
        "sale.order",
        [
            ["state", "in", ["sale", "done"]],
            ["date_order", ">=", prev_start],
            ["date_order", "<", prev_end],
            ["company_id", "=", comp_id],
        ],
        ["id", "amount_total", "partner_id", "user_id"]
    ) or []

    if not orders_cur and not orders_prev:
        return None

    if kpi_id == "revenue":
        cur_total = sum(o["amount_total"] for o in orders_cur)
        prev_total = sum(o["amount_total"] for o in orders_prev)
    elif kpi_id == "active_customers":
        cur_partners = {o["partner_id"][0] for o in orders_cur if o.get("partner_id")}
        prev_partners = {o["partner_id"][0] for o in orders_prev if o.get("partner_id")}
        cur_total = float(len(cur_partners))
        prev_total = float(len(prev_partners))
    else:
        cur_total = float(len(orders_cur))
        prev_total = float(len(orders_prev))

    delta_total = cur_total - prev_total
    delta_total_pct = ((delta_total / prev_total) * 100.0) if prev_total > 0 else (change_percent or 0.0)

    # 1. Commercial (salesperson)
    comm_cur, comm_prev = {}, {}

    if kpi_id == "active_customers":
        # Pour Clients Actifs : décompte strict des partner_id UNIQES par commercial
        for o in orders_cur:
            if o.get("partner_id") and o.get("user_id"):
                name = o["user_id"][1]
                pid = o["partner_id"][0]
                comm_cur.setdefault(name, set()).add(pid)
        for o in orders_prev:
            if o.get("partner_id") and o.get("user_id"):
                name = o["user_id"][1]
                pid = o["partner_id"][0]
                comm_prev.setdefault(name, set()).add(pid)
    else:
        for o in orders_cur:
            name = o["user_id"][1] if o.get("user_id") else "Non assigné"
            val = o["amount_total"] if kpi_id == "revenue" else 1.0
            comm_cur[name] = comm_cur.get(name, 0.0) + val
        for o in orders_prev:
            name = o["user_id"][1] if o.get("user_id") else "Non assigné"
            val = o["amount_total"] if kpi_id == "revenue" else 1.0
            comm_prev[name] = comm_prev.get(name, 0.0) + val

    all_segments = []
    for comm in set(comm_cur.keys()) | set(comm_prev.keys()):
        if kpi_id == "active_customers":
            c_val = float(len(comm_cur.get(comm, set())))
            p_val = float(len(comm_prev.get(comm, set())))
        else:
            c_val = comm_cur.get(comm, 0.0)
            p_val = comm_prev.get(comm, 0.0)
        delta = c_val - p_val
        if delta != 0:
            all_segments.append({"dimension": "sales_rep", "segment": format_segment_label("sales_rep", comm), "delta": delta})

    # 2. Région (partner state_id)
    partner_ids = list({o["partner_id"][0] for o in orders_cur + orders_prev if o.get("partner_id")})
    partner_to_state = {}
    if partner_ids:
        partners = odoo.search_read("res.partner", [["id", "in", partner_ids]], ["id", "state_id"]) or []
        for p in partners:
            st = p.get("state_id")
            partner_to_state[p["id"]] = st[1] if st else "Région inconnue"

    reg_cur, reg_prev = {}, {}

    if kpi_id == "active_customers":
        # Pour Clients Actifs : décompte strict des partner_id UNIQUES par région
        for o in orders_cur:
            if o.get("partner_id"):
                p_id = o["partner_id"][0]
                st_name = partner_to_state.get(p_id, "Région inconnue")
                reg_cur.setdefault(st_name, set()).add(p_id)
        for o in orders_prev:
            if o.get("partner_id"):
                p_id = o["partner_id"][0]
                st_name = partner_to_state.get(p_id, "Région inconnue")
                reg_prev.setdefault(st_name, set()).add(p_id)
    else:
        for o in orders_cur:
            p_id = o["partner_id"][0] if o.get("partner_id") else None
            st_name = partner_to_state.get(p_id, "Région inconnue") if p_id else "Région inconnue"
            val = o["amount_total"] if kpi_id == "revenue" else 1.0
            reg_cur[st_name] = reg_cur.get(st_name, 0.0) + val
        for o in orders_prev:
            p_id = o["partner_id"][0] if o.get("partner_id") else None
            st_name = partner_to_state.get(p_id, "Région inconnue") if p_id else "Région inconnue"
            val = o["amount_total"] if kpi_id == "revenue" else 1.0
            reg_prev[st_name] = reg_prev.get(st_name, 0.0) + val

    for reg in set(reg_cur.keys()) | set(reg_prev.keys()):
        if kpi_id == "active_customers":
            c_val = float(len(reg_cur.get(reg, set())))
            p_val = float(len(reg_prev.get(reg, set())))
        else:
            c_val = reg_cur.get(reg, 0.0)
            p_val = reg_prev.get(reg, 0.0)
        delta = c_val - p_val
        if delta != 0:
            all_segments.append({"dimension": "region", "segment": format_segment_label("region", reg), "delta": delta})

    if not all_segments:
        return None

    all_segments.sort(key=lambda x: abs(x["delta"]), reverse=True)
    top3 = all_segments[:3]

    breakdown = []
    explained_pct_sum = 0.0
    total_abs_segment_deltas = sum(abs(s["delta"]) for s in all_segments) or 1.0

    use_abs_reference = abs(delta_total) < max(1.0, 0.05 * abs(cur_total))

    for s in top3:
        if not use_abs_reference and abs(delta_total) > 1e-6:
            raw_contrib = (s["delta"] / delta_total) * 100.0
        else:
            raw_contrib = (abs(s["delta"]) / total_abs_segment_deltas) * 100.0 * (1.0 if s["delta"] >= 0 else -1.0)
        
        contrib = round(max(-100.0, min(100.0, raw_contrib)), 1)
        explained_pct_sum += abs(contrib)
        breakdown.append({
            "dimension": s["dimension"],
            "segment": s["segment"],
            "delta": round(s["delta"], 2),
            "contribution_pct": contrib
        })

    residual_pct = round(max(0.0, 100.0 - explained_pct_sum), 1)

    return {
        "kpi_name": KPI_LABELS.get(kpi_id, kpi_id),
        "period_current": period_current,
        "period_previous": period_previous,
        "delta_total": round(delta_total, 2),
        "delta_total_pct": round(delta_total_pct, 1),
        "breakdown": breakdown,
        "residual_pct": residual_pct
    }





def generate_rca_explanation(rca_result: dict) -> str:
    """Génère une explication concise pour un dirigeant PME via Groq LLM avec fallback sécurisé."""
    kpi_name = rca_result.get("kpi_name", "KPI")
    delta_total_pct = rca_result.get("delta_total_pct", 0.0)
    delta_total = rca_result.get("delta_total", 0.0)
    breakdown = rca_result.get("breakdown", [])
    residual_pct = rca_result.get("residual_pct", 0.0)

    for b in breakdown:
        b["segment"] = format_segment_label(b.get("dimension", ""), b.get("segment", ""))

    prompt = f"""Tu rédiges une explication business-friendly d'une variation de KPI pour un dirigeant PME.

Contexte fourni :
- KPI: {kpi_name}
- Variation totale: {delta_total_pct}% ({delta_total} en valeur absolue)
- Décomposition (3 facteurs principaux qui expliquent {round(100.0 - residual_pct, 1)}% de la variation) :
  {json.dumps(breakdown, ensure_ascii=False)}
- Part non expliquée par ces 3 facteurs: {residual_pct}%

Consignes :
- Explique la variation en citant les 3 facteurs par ordre d'impact décroissant.
- Utilise des termes métier, pas de jargon statistique (jamais "delta", "z-score", "contribution").
- Si residual_pct dépasse 40%, mentionne explicitement qu'une part significative de la variation reste diffuse sur d'autres facteurs plutôt que de prétendre à une explication complète.
- Ne déduis et n'invente AUCUN chiffre qui n'est pas dans les données fournies.
- Format : 3-4 phrases maximum."""

    try:
        client = Groq(api_key=settings.groq_api_key)
        completion = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )
        text = completion.choices[0].message.content.strip()
        if text:
            return text
    except Exception as e:
        logger.warning(f"Impossible de contacter le LLM pour l'explication RCA ({e}). Utilisation du fallback métier.")

    sign = "baisse" if delta_total_pct < 0 else "hausse"
    abs_pct = abs(delta_total_pct)
    factors_str = []
    for b in breakdown[:3]:
        clean_seg = format_segment_label(b["dimension"], b["segment"])
        factors_str.append(f"{clean_seg} ({abs(b['contribution_pct'])}%)")

    factors_text = ", ".join(factors_str) if factors_str else "divers facteurs"
    fallback_text = f"La {sign} de {abs_pct}% du {kpi_name} s'explique principalement par {factors_text}."
    if residual_pct > 40.0:
        fallback_text += f" Une part importante ({residual_pct}%) de la variation reste toutefois répartie sur d'autres facteurs secondaires."
    else:
        fallback_text += " Ces éléments couvrent la presque totalité de la variation observée."

    return fallback_text


def get_root_cause_analysis(kpi_id: str, current_value: float, change_percent: float | None) -> list[dict]:
    rca_data = compute_root_cause_data(kpi_id, current_value, change_percent)
    result = []
    unit_map = {
        "revenue": "MAD",
        "stock_value": "MAD",
        "pipeline_value": "MAD",
        "unpaid_invoices": "MAD",
        "new_orders": "commandes",
        "late_orders": "commandes",
        "unpaid_invoices_count": "factures",
        "active_customers": "clients",
        "new_leads": "leads",
        "stock_alerts": "produits",
        "conversion_rate": "points",
    }
    unit = unit_map.get(kpi_id, "")

    for b in rca_data.get("breakdown", []):
        clean_seg = format_segment_label(b["dimension"], b["segment"])
        dim_fr = {"region": "Région", "product": "Produit", "sales_rep": "Commercial", "customer_category": "Client"}.get(b["dimension"], b["dimension"])
        result.append({
            "dimension": dim_fr,
            "segment": clean_seg,
            "delta": b["delta"],
            "contribution_pct": b["contribution_pct"],
            "unit": unit
        })
    return result


def format_root_causes_text(root_causes: list[dict], kpi_unit: str = "", is_positive_trend: bool = False) -> str:
    """Formate les causes racine en phrase lisible sans jargon, avec explicitation des compensations."""
    if not root_causes:
        return ""

    pos_parts = []
    neg_parts = []

    for rc in root_causes[:3]:
        delta_val = rc.get("delta", 0)
        unit = rc.get("unit") or kpi_unit
        unit_str = f" {unit}".rstrip() if unit else ""
        seg_label = format_segment_label(rc.get("dimension", ""), rc.get("segment", ""))

        if delta_val > 0:
            pos_parts.append(f"+{delta_val}{unit_str} sur {seg_label}")
        elif delta_val < 0:
            neg_parts.append(f"-{abs(delta_val)}{unit_str} sur {seg_label}")

    if pos_parts and neg_parts:
        if is_positive_trend:
            return f" (porté par {', '.join(pos_parts)}, malgré un repli de {', '.join(neg_parts)})"
        else:
            return f" (notamment {', '.join(neg_parts)}, malgré {', '.join(pos_parts)})"
    elif pos_parts:
        return f" (dont {', '.join(pos_parts)})"
    elif neg_parts:
        return f" (dont {', '.join(neg_parts)})"
    
    return ""
