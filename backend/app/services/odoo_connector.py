"""
Connecteur Odoo — couche unique qui sait parler à Odoo via XML-RPC.

Aucune autre partie du backend ne doit importer xmlrpc directement :
tout passe par les fonctions de ce fichier, pour que la logique de
connexion reste à un seul endroit (facile à changer si un jour on
passe à une vraie instance client, ou à l'API JSON-RPC).
"""

import xmlrpc.client
from app.config import settings


class OdooConnector:
    def __init__(self):
        self.url = settings.odoo_url
        self.db = settings.odoo_db
        self.username = settings.odoo_username
        self.password = settings.odoo_api_key
        self._uid = None

    def _get_uid(self) -> int:
        """Authentifie une seule fois et met le résultat en cache."""
        if self._uid is None:
            common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self._uid = common.authenticate(self.db, self.username, self.password, {})
            if not self._uid:
                raise ConnectionError(
                    "Authentification Odoo échouée — vérifie ODOO_DB, "
                    "ODOO_USERNAME et ODOO_API_KEY dans .env"
                )
        return self._uid

    def _models(self):
        return xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")

    def search_read(self, model: str, domain: list, fields: list, limit: int = 0) -> list[dict]:
        """
        Équivalent d'un SELECT filtré sur un modèle Odoo.
        Exemple : search_read("sale.order", [["state", "=", "sale"]], ["amount_total"])
        """
        uid = self._get_uid()
        kwargs = {"context": {"lang": "fr_FR"}}
        if limit:
            kwargs["limit"] = limit

        return self._models().execute_kw(
            self.db, uid, self.password,
            model, "search_read",
            [domain, fields],
            kwargs,
        )

    def search_count(self, model: str, domain: list) -> int:
        """Compte le nombre d'enregistrements correspondant au filtre."""
        uid = self._get_uid()
        return self._models().execute_kw(
            self.db, uid, self.password,
            model, "search_count",
            [domain],
            {"context": {"lang": "fr_FR"}},
        )


    def create(self, model: str, vals: dict) -> int:
        """
        Crée un nouvel enregistrement dans Odoo.
        Exemple : create("purchase.order", {"partner_id": 1, "state": "draft"})
        """
        uid = self._get_uid()
        return self._models().execute_kw(
            self.db, uid, self.password,
            model, "create",
            [vals],
        )


# Instance unique réutilisée par tout le backend
odoo = OdooConnector()
