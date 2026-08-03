import json
import logging
from sqlalchemy import text
from app.services.odoo_connector import odoo
from app.services.kpi_sync import sync_all
from app.database import SessionLocal

logger = logging.getLogger(__name__)

MAPPING_LOG = {
    "partners": {
        "Azure Interior": "Atlas Distribution SARL (Casablanca)",
        "Gemini Furniture": "Maroc BTP & Matériaux (Rabat)",
        "Wood Corner": "Société Maghrébine de Négoce (Tanger)",
        "Acme Corporation": "TechMaroc Solutions (Casablanca)",
        "Lumber Inc": "Compagnie Marocaine de Logistique (Marrakech)",
        "Ready Mat": "Industries du Nord SARL (Fès)",
        "The Jackson Group": "Atlas Commerce & Distribution (Agadir)",
        "My Company (San Francisco)": "SmartERP PME Siège (Casablanca)",
        "My Company (Chicago)": "SmartERP PME Succursale (Rabat)",
    },
    "states": {
        "California (US)": "Casablanca-Settat",
        "California": "Casablanca-Settat",
        "Illinois (US)": "Rabat-Salé-Kénitra",
        "Illinois": "Rabat-Salé-Kénitra",
    },
    "users": {
        "Mitchell Admin": "Karim Benjelloun",
        "Marc Demo": "Youssef El Amrani",
        "Joel Willis": "Sofia Tazi",
    },
    "products": {
        "Customizable Desk (White)": "Bureau Ergonomique Blanc (Maroc)",
        "Customizable Desk (Custom)": "Bureau Ergonomique Sur-Mesure",
        "Office Chair Black": "Chaise de Direction Executive Noire",
        "Cabinet with doors": "Armoire de Rangement Métallique",
        "Corner Desk Right Sit": "Bureau d'Angle Modulable",
        "Large Cabinet": "Grande Armoire de Classement",
    }
}


def run_moroccan_renaming():
    print("=================================================================")
    print("=== MAROCANISATION SÉCURISÉE DES DONNÉES ODOO 17 ===")
    print("=================================================================")

    # 1. Renommage des Régions (res.country.state)
    print("\n1. Mise à jour des régions / états Odoo...")
    states = odoo.search_read("res.country.state", [], ["id", "name"]) or []
    for s in states:
        old_name = s["name"]
        if old_name in MAPPING_LOG["states"]:
            new_name = MAPPING_LOG["states"][old_name]
            odoo.write("res.country.state", [s["id"]], {"name": new_name})
            print(f"  [State ID {s['id']}] '{old_name}' -> '{new_name}'")

    # 2. Renommage des Clients / Sociétés (res.partner)
    print("\n2. Mise à jour des clients / sociétés Odoo...")
    partners = odoo.search_read("res.partner", [], ["id", "name"]) or []
    for p in partners:
        old_name = p["name"]
        if old_name in MAPPING_LOG["partners"]:
            new_name = MAPPING_LOG["partners"][old_name]
            odoo.write("res.partner", [p["id"]], {"name": new_name})
            print(f"  [Partner ID {p['id']}] '{old_name}' -> '{new_name}'")

    # 3. Renommage des Commerciaux (res.users - CHAMP name UNIQUEMENT, logins intacts)
    print("\n3. Mise à jour des noms d'affichage des commerciaux Odoo (logins API intacts)...")
    users = odoo.search_read("res.users", [], ["id", "name", "login"]) or []
    for u in users:
        old_name = u["name"]
        if old_name in MAPPING_LOG["users"]:
            new_name = MAPPING_LOG["users"][old_name]
            odoo.write("res.users", [u["id"]], {"name": new_name})
            print(f"  [User ID {u['id']}] '{old_name}' (login: {u['login']}) -> '{new_name}'")

    # 4. Renommage des Produits
    print("\n4. Mise à jour des désignations produits Odoo...")
    products = odoo.search_read("product.template", [], ["id", "name"]) or []
    for pr in products:
        old_name = pr["name"]
        for old_pattern, new_pname in MAPPING_LOG["products"].items():
            if old_pattern in old_name:
                odoo.write("product.template", [pr["id"]], {"name": new_pname})
                print(f"  [Product ID {pr['id']}] '{old_name}' -> '{new_pname}'")
                break

    # 5. Resynchronisation du Cache PostgreSQL SmartERP AI
    print("\n5. Resynchronisation du cache PostgreSQL SmartERP AI (sync_all)...")
    sync_all()
    print("[OK] Cache PostgreSQL réactualisé avec les données Odoo marocaines.")

    # 6. Actualisation des textes de recommandations en SQL direct
    print("\n6. Actualisation des textes de recommandations existantes...")
    db = SessionLocal()
    try:
        for old_text, new_text in MAPPING_LOG["partners"].items():
            db.execute(
                text("UPDATE ai_recommendation SET title = REPLACE(title, :old, :new), explanation = REPLACE(explanation, :old, :new)"),
                {"old": old_text, "new": new_text}
            )
        for old_text, new_text in MAPPING_LOG["users"].items():
            db.execute(
                text("UPDATE ai_recommendation SET title = REPLACE(title, :old, :new), explanation = REPLACE(explanation, :old, :new)"),
                {"old": old_text, "new": new_text}
            )
        for old_text, new_text in MAPPING_LOG["states"].items():
            db.execute(
                text("UPDATE ai_recommendation SET title = REPLACE(title, :old, :new), explanation = REPLACE(explanation, :old, :new)"),
                {"old": old_text, "new": new_text}
            )
        db.commit()
        print("[OK] Recommandations mises à jour avec succès.")
    except Exception as e:
        logger.warning(f"Note recommandations SQL update: {e}")
    finally:
        db.close()

    print("\n=================================================================")
    print("=== MAROCANISATION RÉUSSIE AVEC SÉCURITÉ TOTALE ===")
    print("=================================================================")


def run_revert_moroccan_renaming():
    """Restaure l'intégralité des données Odoo à leurs noms d'origine."""
    from app.services.root_cause_analysis import _rca_cache
    from app.models.ai_recommendation import AIRecommendation, RecommendationStatus
    import app.main

    print("=================================================================")
    print("=== RESTAURATION SÉCURISÉE DES DONNÉES ODOO D'ORIGINE ===")
    print("=================================================================")

    restored_log = []

    # Inversion des mappings
    reverse_states = {v: k for k, v in MAPPING_LOG["states"].items()}
    reverse_partners = {v: k for k, v in MAPPING_LOG["partners"].items()}
    reverse_users = {v: k for k, v in MAPPING_LOG["users"].items()}
    reverse_products = {v: k for k, v in MAPPING_LOG["products"].items()}

    # 1. Régions / États
    states = odoo.search_read("res.country.state", [], ["id", "name"]) or []
    for s in states:
        curr = s["name"]
        if curr in reverse_states:
            orig = reverse_states[curr]
            odoo.write("res.country.state", [s["id"]], {"name": orig})
            restored_log.append(f"State ID {s['id']}: '{curr}' -> '{orig}'")
            print(f"  [State ID {s['id']}] '{curr}' -> '{orig}'")

    # 2. Clients / Sociétés
    partners = odoo.search_read("res.partner", [], ["id", "name"]) or []
    for p in partners:
        curr = p["name"]
        if curr in reverse_partners:
            orig = reverse_partners[curr]
            odoo.write("res.partner", [p["id"]], {"name": orig})
            restored_log.append(f"Partner ID {p['id']}: '{curr}' -> '{orig}'")
            print(f"  [Partner ID {p['id']}] '{curr}' -> '{orig}'")

    # 3. Commerciaux / Utilisateurs
    users = odoo.search_read("res.users", [], ["id", "name"]) or []
    for u in users:
        curr = u["name"]
        if curr in reverse_users:
            orig = reverse_users[curr]
            odoo.write("res.users", [u["id"]], {"name": orig})
            restored_log.append(f"User ID {u['id']}: '{curr}' -> '{orig}'")
            print(f"  [User ID {u['id']}] '{curr}' -> '{orig}'")

    # 4. Produits
    products = odoo.search_read("product.template", [], ["id", "name"]) or []
    for pr in products:
        curr = pr["name"]
        for moroccan_name, orig in reverse_products.items():
            if moroccan_name in curr or curr == moroccan_name:
                odoo.write("product.template", [pr["id"]], {"name": orig})
                restored_log.append(f"Product ID {pr['id']}: '{curr}' -> '{orig}'")
                print(f"  [Product ID {pr['id']}] '{curr}' -> '{orig}'")
                break

    # 5. Purge du cache RCA et des recommandations pending
    _rca_cache.clear()
    db = SessionLocal()
    try:
        pending_recs = db.query(AIRecommendation).filter(AIRecommendation.status == RecommendationStatus.pending).all()
        for r in pending_recs:
            db.delete(r)
        db.commit()
        print(f"[OK] Cache RCA vidé et {len(pending_recs)} recommandations pending purgées.")
    finally:
        db.close()

    # 6. Resynchronisation totale
    print("\nResynchronisation complète via sync_all()...")
    sync_all()
    print("[OK] Données Odoo d'origine restaurées et synchronisées avec succès.")

    return restored_log


if __name__ == "__main__":
    run_moroccan_renaming()
