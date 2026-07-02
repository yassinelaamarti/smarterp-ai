# SmartERP AI

Plateforme SaaS d’Analytics Décisionnel augmentée par un Agent IA pour l’écosystème Odoo.

SmartERP AI se connecte à Odoo en lecture seule afin d’exploiter les données métier (Ventes, CRM, Stock…) et fournir :

- Dashboard temps réel (KPIs)
- Alertes et indicateurs décisionnels
- Agent IA conversationnel (questions métier en langage naturel)
- Interface web moderne

Projet académique réalisé dans le cadre du PFA — MGSI S8 — en partenariat avec UrikaCloud.

---

# Objectifs du projet

Construire une couche d’intelligence au-dessus d’Odoo sans modifier l’installation du client.

Fonctionnalités prévues :

- Connexion Odoo via API
- Extraction des données métier
- Stockage analytique
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
Odoo 17
(API XML-RPC / JSON-RPC)
        │
        ▼
Backend FastAPI
(ETL + Analytics)
        │
        ▼
PostgreSQL
(Cache + KPIs)
        │
        ├────────► Agent IA (Groq / LLaMA)
        │
        ▼
Frontend Next.js
(Dashboard + Chat)
```

Documentation complète :

```text
docs/architecture.md
```

---

# Structure du projet

```text
smarterp-ai/
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── store/
│   │   └── types/
│
├── backend/
│
├── docs/
│   ├── architecture.md
│   ├── business-requirements.md
│   ├── api-contract.md
│   └── sprint-plan.md
│
├── .github/
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
- Node.js (optionnel pour exécution hors Docker)

Vérifier :

```bash
docker --version
docker compose version
```

---

# Installation

## 1. Cloner

```bash
git clone https://github.com/yassinelaamarti/smarterp-ai.git

cd smarterp-ai
```

---

## 2. Configurer l’environnement

Créer :

```bash
cp .env.example .env
```

Compléter :

```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

NEXT_PUBLIC_API_URL=
```

---

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

Nettoyage complet :

```bash
docker compose down -v
```

---

# Services disponibles

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Odoo | http://localhost:8069 |
| PostgreSQL | localhost:5432 |

---

# Organisation de l’équipe

Projet réalisé par une équipe de 3 étudiants.

Mode de travail :

- Collaboration Full-Stack
- Responsabilité partagée
- Revue collective des Pull Requests
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
- [x] Architecture Docker
- [x] Frontend Next.js
- [x] Backend FastAPI
- [x] PostgreSQL
- [x] Odoo 17
- [ ] Dashboard KPI
- [ ] Agent IA
- [ ] Intégration Odoo
- [ ] Authentification

---

# Licence

Projet académique.

Usage interne — Équipe SmartERP AI × UrikaCloud.