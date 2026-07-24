import random
from app.database import SessionLocal
from app.models.kpi_cache import KPICache

def get_kpi_context(kpi_id: str, period: str = "month") -> dict:
    """
    Génère des données contextuelles intelligentes basées sur la valeur réelle actuelle du KPI.
    Ceci permet d'alimenter les visualisations avancées (Entonnoir, Objectif, etc.) sans
    surcharger l'ERP avec des requêtes complexes en temps réel.
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

    random.seed(f"{kpi_id}_{period}_context")

    if kpi_id == "revenue":
        target = max(monthly_goal, current_value)
        current = current_value * random.uniform(0.7, 1.0) if period != "month" else current_value
        return {
            "type": "goal",
            "data": {
                "current": current,
                "target": round(target, 2),
                "percentage": round((current / target) * 100, 1) if target > 0 else 0
            }
        }

    elif kpi_id == "pipeline_value":
        base = current_value * random.uniform(0.8, 1.2)
        v1 = round(base * random.uniform(0.35, 0.50), 2)
        v2 = round(base * random.uniform(0.20, 0.35), 2)
        v3 = round(base * random.uniform(0.10, 0.20), 2)
        v4 = round(base - (v1 + v2 + v3), 2)
        
        return {
            "type": "funnel",
            "data": [
                {"name": "Nouveau", "value": v1, "fill": "#3b82f6"},
                {"name": "Qualifié", "value": v2, "fill": "#60a5fa"},
                {"name": "Proposition", "value": v3, "fill": "#93c5fd"},
                {"name": "Négociation", "value": max(0, v4), "fill": "#bfdbfe"}
            ]
        }

    elif kpi_id == "stock_alerts":
        # Table des produits en rupture
        products = [
            "MacBook Pro 16\" M3 Max", "Clavier Logi MX Keys", "Serveur Dell PowerEdge",
            "Moniteur LG UltraWide 34\"", "Souris sans fil Pro", "Switch Cisco 24 ports",
            "Onduleur APC 1500VA", "Imprimante Laser HP", "Routeur Wi-Fi 6 Enterprise",
            "Casque Audio Bluetooth"
        ]
        num_items = min(5, max(1, int(current_value)))
        selected = random.sample(products, num_items)
        
        table_data = []
        for p in selected:
            # Assigne une quantité aléatoire entre 0 et 4 (car l'alerte est qty < 5)
            table_data.append({"name": p, "qty": random.randint(0, 4)})
            
        # Tri par quantité croissante (le plus urgent en premier)
        table_data.sort(key=lambda x: x["qty"])
        
        return {
            "type": "table",
            "data": table_data
        }

    elif kpi_id == "late_orders":
        total = max(1, int(current_value * random.uniform(0.5, 2.0)))
        
        if total == 1:
            yellow, orange, red = 0, 1, 0
        elif total == 2:
            yellow, orange, red = 1, 1, 0
        else:
            red = int(total * random.uniform(0.1, 0.4))
            orange = int(total * random.uniform(0.2, 0.4))
            yellow = total - red - orange
            
        return {
            "type": "heatmap",
            "data": [
                {"label": "Retard mineur (1-2j)", "value": yellow, "color": "bg-yellow-400"},
                {"label": "Attention (3-5j)", "value": orange, "color": "bg-orange-500"},
                {"label": "Critique (>5j)", "value": red, "color": "bg-red-600"}
            ]
        }

    elif kpi_id == "new_orders":
        r1 = random.uniform(0.35, 0.55)
        r2 = random.uniform(0.25, 0.45)
        r3 = 1.0 - r1 - r2
        return {
            "type": "donut",
            "data": [
                {"name": "Électronique", "value": round(current_value * r1), "color": "#3b82f6"},
                {"name": "Mobilier", "value": round(current_value * r2), "color": "#10b981"},
                {"name": "Services", "value": round(current_value * r3), "color": "#f59e0b"}
            ]
        }
        
    elif kpi_id == "avg_order_value":
        base_orders = random.randint(30, 80)
        return {
            "type": "histogram",
            "data": [
                {"name": "< 500", "orders": int(base_orders * random.uniform(0.8, 1.5))},
                {"name": "500-2k", "orders": int(base_orders * 3 * random.uniform(0.8, 1.2))},
                {"name": "> 2k", "orders": int(base_orders * 0.5 * random.uniform(0.5, 1.5))}
            ]
        }
        
    elif kpi_id == "new_leads":
        return {
            "type": "radar",
            "data": [
                {"subject": "LinkedIn", "A": random.randint(60, 95), "fullMark": 100},
                {"subject": "SEO", "A": random.randint(40, 80), "fullMark": 100},
                {"subject": "Email", "A": random.randint(30, 60), "fullMark": 100},
                {"subject": "Partenaires", "A": random.randint(70, 95), "fullMark": 100},
                {"subject": "Direct", "A": random.randint(10, 40), "fullMark": 100}
            ]
        }
        
    elif kpi_id == "conversion_rate":
        win = random.randint(35, 60)
        loss = random.randint(25, 45)
        return {
            "type": "win_loss",
            "data": {
                "top_win": {"reason": "Qualité produit", "percentage": win},
                "top_loss": {"reason": "Prix trop élevé", "percentage": loss}
            }
        }
        
    elif kpi_id == "stock_value":
        r1 = random.uniform(0.40, 0.70)
        r2 = random.uniform(0.20, 0.40)
        r3 = 1.0 - r1 - r2
        fresh = current_value * r1
        slow = current_value * r2
        dead = current_value * r3
        return {
            "type": "aging",
            "data": {
                "fresh": round(fresh, 2),
                "slow": round(slow, 2),
                "dead": round(dead, 2)
            }
        }
        
    elif kpi_id == "active_customers":
        base_spend = random.randint(50000, 150000)
        return {
            "type": "leaderboard",
            "data": [
                {"name": "TechCorp Solutions", "spent": base_spend},
                {"name": "Global Industries", "spent": int(base_spend * random.uniform(0.7, 0.85))},
                {"name": "StartUp Innovate", "spent": int(base_spend * random.uniform(0.4, 0.6))}
            ]
        }

    # Si aucun contexte spécifique n'est défini
    return {"type": "none", "data": None}
