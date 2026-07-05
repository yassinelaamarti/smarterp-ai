# SmartERP AI

Plateforme SaaS d'Analytics Décisionnel augmentée par un Agent IA pour l'écosystème Odoo.

SmartERP AI se connecte à Odoo en lecture seule afin d'exploiter les données métier (Ventes, CRM, Stock…) et fournir :

- Dashboard temps réel (KPIs)
- Alertes et indicateurs décisionnels
- Agent IA conversationnel (questions métier en langage naturel)
- Interface web moderne

Projet académique réalisé dans le cadre du PFA — MGSI S8 — en partenariat avec UrikaCloud.

---

# Objectifs du projet

Construire une couche d'intelligence au-dessus d'Odoo sans modifier l'installation du client.

Fonctionnalités prévues :

- Connexion Odoo via API
- Extraction des données métier
- Stockage analytique (cache)
- Dashboard décisionnel
- Agent IA conversationnel
- Visualisation des KPIs

---

# Stack technique

| Couche | Technologie |
|---|---|
| Frontend | Next.js 16 + TypeScript |
| UI | Tailwind CSS |
| State Management | Zustand |
| Data Fetching | React Query |
| Charts | Recharts |
| Backend | FastAPI |
| Base de données | PostgreSQL |
| ERP | Odoo 17 |
| IA | Groq API + LLaMA |
| Conteneurisation | Docker |
| Orchestration | Docker Compose |
| Versioning | Git + GitHub |

---

# Architecture

```text
Odoo 17 (lecture seule, XML-RPC)
        │
        ▼
Backend FastAPI
(connecteur Odoo + calcul des KPIs)
        │  synchronisation périodique (15 min)
        ▼
PostgreSQL (cache)
(kpi_cache, revenue_history_cache)
        │  lu directement par l'API, jamais Odoo en direct
        ▼
API REST (/api/kpis/, /api/kpis/revenue-history)
        │
        ├────────► Agent IA (Groq / LLaMA) — à venir
        │
        ▼
Frontend Next.js
(Dashboard + Chat à venir)
```

Point clé : le frontend ne parle jamais à Odoo. Le backend ne lit jamais Odoo au moment d'une requête utilisateur — il lit son cache PostgreSQL, tenu à jour en arrière-plan. Le dashboard reste rapide même si Odoo est temporairement indisponible.

Documentation complète : voir `docs/architecture.md` et le document `SmartERP_AI_Documentation.pdf` partagé avec l'équipe.

---

# Structure du projet

```text
smarterp-ai/
│
├── frontend/
│   └── src/
│       ├── app/                  Pages (App Router) — ex: /dashboard
│       ├── components/
│       │   ├── ui/
│       │   ├── dashboard/         KPICard, KPIGrid, RevenueChart
│       │   └── chat/               Interface du futur chat IA
│       ├── hooks/                 useKpis, useRevenueHistory
│       ├── lib/                    api.ts, utils.ts
│       ├── store/                   Zustand
│       └── types/
│
├── backend/
│   └── app/
│       ├── main.py                 Démarre l'API + la synchro en arrière-plan
│       ├── config.py
│       ├── database.py
│       ├── routers/                 kpis.py
│       ├── services/
│       │   ├── odoo_connector.py      Connexion générique à Odoo (XML-RPC)
│       │   ├── odoo_kpi_reader.py       Lit Odoo (usage interne, appelé par kpi_sync)
│       │   ├── kpi_sync.py                Écrit dans le cache PostgreSQL
│       │   └── kpi_calculator.py            Lit le cache pour répondre à l'API
│       ├── models/                          kpi_cache.py
│       └── schemas/                          kpi.py, revenue.py
│
├── docs/
│   ├── architecture.md
│   ├── business-requirements.md
│   ├── api-contract.md
│   └── sprint-plan.md
│
├── docker-compose.yml
├── .env.example
├── README.md
└── CONTRIBUTING.md
```

---

# Prérequis

Installer :

- Git
- Docker Desktop
- WSL2 (Windows)
- Node.js (optionnel, pour exécution hors Docker)

Vérifier :

```bash
docker --version
docker compose version
```

**Important (Windows)** : lancer les commandes `docker compose ...` depuis **PowerShell**, pas Git Bash — un bug connu de traduction de chemins sous Git Bash peut créer des dossiers parasites.

---

# Installation

## 1. Cloner

```bash
git clone https://github.com/yassinelaamarti/smarterp-ai.git
cd smarterp-ai
```

## 2. Configurer l'environnement

```bash
cp .env.example .env
```

Compléter au minimum :

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=

ODOO_URL=
ODOO_DB=
ODOO_USERNAME=
ODOO_API_KEY=

NEXT_PUBLIC_API_URL=

SYNC_INTERVAL_SECONDS=900
```

## 3. Lancer le projet

Premier lancement :

```bash
docker compose up --build
```

Lancements suivants :

```bash
docker compose up
```

Arrêter :

```bash
CTRL + C
```

Nettoyage complet (supprime aussi les données) :

```bash
docker compose down -v
```

## 4. Créer la base Odoo (une seule fois)

Sur `http://localhost:8069`, créer une base avec les identifiants définis dans `.env` (`ODOO_DB`, `ODOO_USERNAME`, `ODOO_API_KEY`), en cochant **Demo data** pour avoir des données de test.

---

# Services disponibles

| Service | URL |
|---|---|
| Frontend (Dashboard) | http://localhost:3000/dashboard |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Odoo | http://localhost:8069 |
| PostgreSQL | localhost:5432 |

Forcer une synchronisation manuelle du cache : `POST http://localhost:8000/api/kpis/sync`

---

# Organisation de l'équipe

Projet réalisé par une équipe de 3 étudiants.

Mode de travail :

- Collaboration Full-Stack
- Travail direct sur `main` (pas de branches obligatoires, équipe de 3 — voir `CONTRIBUTING.md`)
- Répartition suggérée par zone : Backend / Frontend / IA & Documentation
- Documentation commune

Membres :

| Nom | Rôle |
|---|---|
| Laamarti Yassine | Full-Stack Engineer |
| El Handi Zakariyae | Full-Stack Engineer |
| Zouguari Yassine | Full-Stack Engineer |

---

# État actuel

## MVP — En cours

- [x] Initialisation Git
- [x] Architecture Docker (5 services : app DB, backend, frontend, Odoo, Odoo DB)
- [x] Frontend Next.js
- [x] Backend FastAPI
- [x] PostgreSQL
- [x] Odoo 17
- [x] Intégration Odoo (connecteur XML-RPC, lecture Ventes/CRM/Stock)
- [x] Cache PostgreSQL + synchronisation périodique (toutes les 15 min)
- [x] Dashboard KPI — 6 KPIs sur 10, + graphique d'évolution du CA (Recharts)
- [x] 4 KPIs restants (pipeline CRM, valorisation stock, clients actifs, commandes en retard)
- [x] Tendances réelles (comparaison au mois précédent)
- [x] Agent IA (openai/gpt + interface de chat)
- [ ] Système d'alertes automatiques
- [ ] Authentification
- [ ] Landing page publique

---

# Licence

Projet académique.

Usage interne — Équipe SmartERP AI × UrikaCloud.