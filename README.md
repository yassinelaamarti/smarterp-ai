# SmartERP AI

Plateforme SaaS d'Analytics Décisionnel dotée d'un Agent IA, conçue pour l'ERP Odoo 17.

Connexion en lecture via API Odoo (Ventes, CRM, Stock) sans altérer l'installation existante du client. Tableau de bord temps réel (10 KPIs clés + alertes) et Agent IA conversationnel en français pour interroger les données métier en langage naturel.

## Contexte

Projet de Fin d'Année — MGSI S8 — Équipe de 3 étudiants, en partenariat avec UrikaCloud.

## Stack technique

| Couche         | Technologie          |
|----------------|-----------------------|
| Frontend       | Next.js 14 (App Router) |
| Styles         | Tailwind CSS          |
| Graphiques     | Recharts              |
| Backend / API  | FastAPI (Python)      |
| Base de données| PostgreSQL            |
| Agent IA       | Groq API — LLaMA 3.3   |
| Déploiement    | Docker Compose         |

## Architecture (vue d'ensemble)

```
Odoo 17 (client) --API XML-RPC/JSON-RPC--> Backend FastAPI --> PostgreSQL (cache/analytics)
                                                |
                                                v
                                         Agent IA (Groq/LLaMA 3.3)
                                                |
                                                v
                                    Frontend Next.js (Dashboard + Chat)
```

Détails complets dans [`docs/architecture.md`](docs/architecture.md).

## Structure du repo

```
smarterp-ai/
├── frontend/          # Application Next.js 14
├── backend/           # API FastAPI + logique métier + connecteur Odoo
├── docs/              # Documentation technique et fonctionnelle
├── docker-compose.yml # Orchestration des services (dev)
├── .env.example        # Variables d'environnement à copier en .env
└── .github/            # Templates Issues/PR + workflows CI
```

## Démarrage rapide (dev)

```bash
# 1. Cloner le repo
git clone https://github.com/yassinelaamarti/smarterp-ai.git
cd smarterp-ai

# 2. Copier les variables d'environnement
cp .env.example .env

# 3. Lancer avec Docker Compose
docker compose up --build
```

- Frontend : http://localhost:3000
- Backend (docs Swagger) : http://localhost:8000/docs

## Équipe

| Nom | Rôle |
|-----|------|
| À compléter | Frontend Lead (Next.js/Dashboard) |
| À compléter | Backend Lead (FastAPI/Odoo connector) |
| À compléter | IA / Data Lead (Agent conversationnel, KPIs) |

## Workflow de contribution

Voir [`CONTRIBUTING.md`](CONTRIBUTING.md) pour les conventions de branches, de commits et le processus de Pull Request.

## Licence

Projet académique — usage interne à l'équipe et à UrikaCloud. Tous droits réservés.
