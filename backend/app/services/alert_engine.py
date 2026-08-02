"""
Détection d'alertes à partir des KPIs déjà calculés (cache PostgreSQL).

Aucun appel Odoo ici : on réutilise les valeurs et tendances déjà
disponibles via kpi_calculator.get_kpis(), donc cette évaluation
est quasi instantanée.

Deux types de règles :
- Seuils absolus (ex: trop de produits en stock bas)
- Seuils sur tendance (ex: chute du CA par rapport au mois précédent)
"""

from typing import Optional
from app.schemas.kpi import KPI
from app.schemas.alert import Alert, AlertSourceData

RuleResult = Optional[tuple[str, str]]  # (severity, message)


def _check_stock_alerts(kpi: KPI, settings: dict[str, float]) -> RuleResult:
    critical = settings.get("stock_critical", 10.0)
    warning = settings.get("stock_warning", 0.0)
    if kpi.value > critical:
        return "critical", f"{int(kpi.value)} produits en stock critique — réapprovisionnement urgent recommandé."
    if kpi.value > warning:
        return "warning", f"{int(kpi.value)} produit(s) en stock bas à surveiller."
    return None


def _check_late_orders(kpi: KPI, settings: dict[str, float]) -> RuleResult:
    critical = settings.get("late_orders_critical", 5.0)
    warning = settings.get("late_orders_warning", 0.0)
    if kpi.value > critical:
        return "critical", f"{int(kpi.value)} commandes en retard de livraison — risque pour la satisfaction client."
    if kpi.value > warning:
        return "warning", f"{int(kpi.value)} commande(s) en retard de livraison."
    return None


def _check_trend_drop(kpi: KPI, critical_at: float, warning_at: float, label: str) -> RuleResult:
    """critical_at / warning_at sont des seuils négatifs, ex: -15 pour -15%."""
    if kpi.change_percent is None:
        return None
    if kpi.change_percent <= critical_at:
        return "critical", f"{label} a chuté de {abs(kpi.change_percent)}% par rapport au mois précédent."
    if kpi.change_percent <= warning_at:
        return "warning", f"{label} est en baisse de {abs(kpi.change_percent)}% par rapport au mois précédent."
    return None


from sqlalchemy.orm import Session
from app.models.kpi_cache import KPIHistoryCache
from app.services.date_utils import current_month_str

def _check_unpaid_invoices(kpi: KPI, settings: dict[str, float]) -> RuleResult:
    critical = settings.get("unpaid_invoices_60_plus_critical", 40.0)
    warning = settings.get("unpaid_invoices_60_plus_warning", 20.0)

    pct_60 = 0.0
    try:
        from app.services.odoo_kpi_reader import get_unpaid_invoices_data
        unpaid_data = get_unpaid_invoices_data()
        breakdown = unpaid_data.get("aging_breakdown", [])
        tot = unpaid_data.get("total_amount", 1) or 1
        item_60 = next((b for b in breakdown if isinstance(b, dict) and b.get("key") == "overdue_60_plus"), None)
        if item_60:
            pct_60 = (item_60.get("amount", 0) / tot) * 100.0
    except Exception as e:
        logger.warning(f"Impossible de lire le détail des impayés pour l'évaluation des alertes: {e}")

    if pct_60 >= critical:
        return "critical", f"Encours très ancien élevé : {pct_60:.1f}% des factures impayées ont plus de 60 jours de retard."
    if pct_60 >= warning:
        return "warning", f"Encours ancien à surveiller : {pct_60:.1f}% des factures impayées ont plus de 60 jours de retard."
    return None



def evaluate_alerts(kpis: list[KPI], settings: dict[str, float] | None = None, db: Session | None = None) -> list[Alert]:
    if settings is None:
        settings = {
            "stock_critical": 10.0,
            "stock_warning": 0.0,
            "late_orders_critical": 5.0,
            "late_orders_warning": 0.0,
            "unpaid_invoices_60_plus_critical": 40.0,
            "unpaid_invoices_60_plus_warning": 20.0,
            "revenue_critical": -15.0,
            "revenue_warning": -5.0,
            "new_orders_critical": -30.0,
            "new_orders_warning": -20.0,
            "conversion_rate_critical": -30.0,
            "conversion_rate_warning": -20.0,
            "pipeline_value_critical": -40.0,
            "pipeline_value_warning": -30.0,
            "active_customers_critical": -30.0,
            "active_customers_warning": -20.0,
        }

    alerts = []
    for kpi in kpis:
        threshold_info = ""
        if kpi.id == "stock_alerts":
            result = _check_stock_alerts(kpi, settings)
            critical = settings.get("stock_critical", 10.0)
            warning = settings.get("stock_warning", 0.0)
            threshold_info = f"Seuils configurés : Critique > {critical}, Avertissement > {warning}"
        elif kpi.id == "late_orders":
            result = _check_late_orders(kpi, settings)
            critical = settings.get("late_orders_critical", 5.0)
            warning = settings.get("late_orders_warning", 0.0)
            threshold_info = f"Seuils configurés : Critique > {critical}, Avertissement > {warning}"
        elif kpi.id == "unpaid_invoices":
            result = _check_unpaid_invoices(kpi, settings)
            critical = settings.get("unpaid_invoices_60_plus_critical", 40.0)
            warning = settings.get("unpaid_invoices_60_plus_warning", 20.0)
            threshold_info = f"Seuils configurés pour impayés >60j : Critique >= {critical}%, Avertissement >= {warning}%"
        elif kpi.id == "revenue":
            critical = settings.get("revenue_critical", -15.0)
            warning = settings.get("revenue_warning", -5.0)
            result = _check_trend_drop(kpi, critical, warning, "Le chiffre d'affaires")
            threshold_info = f"Seuils de baisse configurés : Critique <= {critical}%, Avertissement <= {warning}%"
        elif kpi.id == "new_orders":
            critical = settings.get("new_orders_critical", -30.0)
            warning = settings.get("new_orders_warning", -20.0)
            result = _check_trend_drop(kpi, critical, warning, "Le nombre de nouvelles commandes")
            threshold_info = f"Seuils de baisse configurés : Critique <= {critical}%, Avertissement <= {warning}%"
        elif kpi.id == "conversion_rate":
            critical = settings.get("conversion_rate_critical", -30.0)
            warning = settings.get("conversion_rate_warning", -20.0)
            result = _check_trend_drop(kpi, critical, warning, "Le taux de conversion")
            threshold_info = f"Seuils de baisse configurés : Critique <= {critical}%, Avertissement <= {warning}%"
        elif kpi.id == "pipeline_value":
            critical = settings.get("pipeline_value_critical", -40.0)
            warning = settings.get("pipeline_value_warning", -30.0)
            result = _check_trend_drop(kpi, critical, warning, "La valeur du pipeline CRM")
            threshold_info = f"Seuils de baisse configurés : Critique <= {critical}%, Avertissement <= {warning}%"
        elif kpi.id == "active_customers":
            critical = settings.get("active_customers_critical", -30.0)
            warning = settings.get("active_customers_warning", -20.0)
            result = _check_trend_drop(kpi, critical, warning, "Le nombre de clients actifs")
            threshold_info = f"Seuils de baisse configurés : Critique <= {critical}%, Avertissement <= {warning}%"
        else:
            continue


        if result:
            severity, message = result
            
            # Calculer RCA
            from app.services.root_cause_analysis import get_root_cause_analysis, format_root_causes_text
            rca_list = get_root_cause_analysis(kpi.id, kpi.value, kpi.change_percent)
            rca_text = format_root_causes_text(rca_list)
            message = message + rca_text
            
            root_causes_formatted = []
            for rc in rca_list:
                sign = "+" if rc["delta"] > 0 else ""
                root_causes_formatted.append(f"{rc['dimension']} '{rc['segment']}' : {sign}{rc['delta']} {rc['unit']}")

            source_data = None
            if kpi.source_data:
                source_data = AlertSourceData(
                    kpi_label=kpi.label,
                    kpi_value=kpi.value,
                    kpi_unit=kpi.unit,
                    model=kpi.source_data.model,
                    domain=kpi.source_data.domain,
                    formula=kpi.source_data.formula,
                    threshold_info=threshold_info,
                    root_causes=root_causes_formatted if root_causes_formatted else None
                )
            alerts.append(Alert(
                id=kpi.id,
                kpi_id=kpi.id,
                severity=severity,
                message=message,
                is_anomaly=False,
                source_data=source_data
            ))

    # Détection d'anomalies statistiques par l'IA
    if db is not None:
        cur_month = current_month_str()
        for kpi in kpis:
            # Récupérer l'historique des mois précédents uniquement (exclure le mois en cours)
            history_records = (
                db.query(KPIHistoryCache)
                .filter(KPIHistoryCache.kpi_id == kpi.id, KPIHistoryCache.month != cur_month)
                .all()
            )
            history_values = [r.value for r in history_records]

            if len(history_values) >= 3:
                import math
                n = len(history_values)
                mean = sum(history_values) / n
                variance = sum((x - mean) ** 2 for x in history_values) / n
                std_dev = math.sqrt(variance)

                if std_dev > 0:
                    z_score = (kpi.value - mean) / std_dev
                    # Seuil d'anomalie à 1.8 pour les petits échantillons de démo
                    if abs(z_score) >= 1.8:
                        severity = "critical" if abs(z_score) >= 2.2 else "warning"
                        direction = "Hausse" if z_score > 0 else "Baisse"
                        message = f"[Anomalie IA] {direction} anormale détectée pour {kpi.label.lower()} : la valeur actuelle ({kpi.value} {kpi.unit or ''}) s'écarte significativement de l'historique (Z-score: {z_score:+.2f}, moyenne: {mean:.1f})."
                        
                        # Calculer RCA
                        from app.services.root_cause_analysis import get_root_cause_analysis, format_root_causes_text
                        # Pour les anomalies, on peut estimer un pseudo change_percent basé sur l'écart à la moyenne
                        pseudo_change = ((kpi.value - mean) / abs(mean) * 100) if mean != 0 else None
                        rca_list = get_root_cause_analysis(kpi.id, kpi.value, pseudo_change)
                        rca_text = format_root_causes_text(rca_list)
                        message = message + rca_text

                        root_causes_formatted = []
                        for rc in rca_list:
                            sign = "+" if rc["delta"] > 0 else ""
                            root_causes_formatted.append(f"{rc['dimension']} '{rc['segment']}' : {sign}{rc['delta']} {rc['unit']}")

                        source_data = None
                        if kpi.source_data:
                            source_data = AlertSourceData(
                                kpi_label=kpi.label,
                                kpi_value=kpi.value,
                                kpi_unit=kpi.unit,
                                model=kpi.source_data.model,
                                domain=kpi.source_data.domain,
                                formula=kpi.source_data.formula,
                                threshold_info=f"Anomalie statistique détectée : Z-score absolu |{z_score:.2f}| >= 1.8. Écart significatif par rapport à la moyenne historique ({mean:.1f}).",
                                history_values=history_values,
                                z_score=z_score,
                                mean=mean,
                                root_causes=root_causes_formatted if root_causes_formatted else None
                            )
                        
                        alerts.append(Alert(
                            id=f"anomaly_{kpi.id}",
                            kpi_id=kpi.id,
                            severity=severity,
                            message=message,
                            is_anomaly=True,
                            source_data=source_data
                        ))

    return alerts



