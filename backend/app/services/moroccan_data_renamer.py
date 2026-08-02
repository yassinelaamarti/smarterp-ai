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

if __name__ == "__main__":
    run_moroccan_renaming()
