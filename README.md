# 🚀 SmartERP AI

> **Plateforme SaaS d'Analytics Décisionnel & Agent IA Augmenté pour Odoo 17**

SmartERP AI est une solution décisionnelle et conversationnelle de niveau entreprise conçue pour s'interposer élégamment au-dessus de l'écosystème ERP **Odoo 17**. En exploitant une architecture de **cache asynchrone non-bloquant**, SmartERP AI extrait et analyse en continu les données métier critiques (Ventes, CRM, Stocks, Recouvrement) sans jamais impacter les performances de l'instance Odoo de production.

---

## 🌟 Aperçu des Fonctionnalités

SmartERP AI transforme la prise de décision métier grâce à des modules intelligents :

### 📊 1. Dashboard Analytics & KPIs Temps Réel
* **Indicateurs clés de performance** : Chiffre d'Affaires, Nouvelles Commandes, Panier Moyen, Marge Brute %, Pipeline CRM, Valorisation du Stock, Clients Actifs, Commandes en Retard, Impayés >60 jours, Objectif Mensuel (MAD).
* **Historisation & Tendances** : Comparaison dynamique des performances par rapport au mois précédent avec détection automatique des tendances.
* **Graphiques interactifs** : Suivi de l'évolution temporelle du chiffre d'affaires et de la ventilation des ventes (Recharts).

### 🤖 2. Agent IA Conversationnel Contextuel
* **Moteur LLM Avancé** : Alimenté par **LLaMA 3.3 70B** (via Groq API / OpenAI), capable de comprendre des requêtes métier complexes en langage naturel.
* **Mémoire & Contextualisation** : Accès direct à l'historique analytique et au contexte des KPIs pour fournir des réponses chiffrées et pertinentes.
* **Exécution d'Actions Odoo** : Capacité de suggérer ou d'initier des actions directes dans Odoo (création de devis, ajustement de stock, relances clients).

### 🩺 3. Moteur de Score de Santé Métier (Business Health Score Engine)
* **Évaluation Globale (0 à 100)** : Algorithme propriétaire calculant un score de santé synthétique de l'entreprise.
* **Décomposition Multidimensionnelle** : Analyse séparée des sous-scores (Ventes, Performance CRM, Santé des Stocks, Recouvrement des Impayés).

### 🔍 4. Analyse des Causes Racines (Root Cause Analysis - RCA)
* **Diagnostic Automatique des Variations** : Identification intelligente des sous-jacents expliquant la baisse ou la hausse soudaine d'un KPI.
* **Recherche Contextuelle** : Analyse croisée des délais de livraison, des annulations de devis ou des blocages de paiements clients.

### 💡 5. Moteur de Recommandations Stratégiques
* **Suggestions Proactives** : Génération de recommandations métier actionnables (ex: réapprovisionnement prioritaire, relance des devis stagnants).
* **Cycle de Vie des Recommandations** : Gestion des états (`Pending`, `Acknowledged`, `Executed`, `Dismissed`) et rappels paramétrables.

### 🔔 6. Alertes & Notifications Configurables
* **Seuils d'Avertissement & Critiques** : Détection temps réel des anomalies (baisse brutale du CA, ruptures de stock, surstockage).
* **Bandeau Interactif (`AlertBanner`)** : Notification visuelle immédiate dans le dashboard et panneau de configuration des seuils.

### 📧 7. Rapports Automatisés par Email
* **Planificateur Intégré (`ReportScheduler`)** : Génération et envoi périodique (journalier, hebdomadaire, mensuel) de bilans décisionnels via SMTP.

---

## 🛠️ Stack Technique

| Couche | Technologie | Description |
| :--- | :--- | :--- |
| **Frontend** | [Next.js 16](https://nextjs.org/) (App Router) | Framework React pour une interface rapide, dynamique et SSR |
| **Langage Frontend**| TypeScript | Typage strict et développement sécurisé |
| **Styling & UI** | Tailwind CSS + Lucide Icons | Design moderne, responsive et composable |
| **State & Data Fetching** | Zustand + React Query (TanStack) | Gestion d'état global et synchronisation du cache React |
| **Visualisation** | Recharts | Visualisation dynamique des graphiques et séries temporelles |
| **Backend API** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+) | API REST asynchrone haute performance |
| **Base de données** | PostgreSQL 16 | Stockage analytique, cache d'historique et persistance des modèles |
| **Moteur ORM** | SQLAlchemy 2.0 + Alembic / Custom Migrations | Modélisation des données analytiques et relationnelles |
| **Connecteur ERP** | XML-RPC (Odoo 17 API) | Connexion sécurisée en lecture seule à Odoo 17 |
| **Intelligence Artificielle** | Groq API / LLaMA 3.3 70B Versatile | LLM pour l'agent conversationnel, les recommandations et le RCA |
| **Conteneurisation** | Docker & Docker Compose | Orchestration multi-services isolée |

---

## 🏗️ Architecture Systémique

SmartERP AI repose sur un principe fondamental : **Le Frontend n'interroge JAMAIS Odoo directement**. Le Backend lit Odoo en arrière-plan via une tâche planifiée et alimente la base de données analytique PostgreSQL.

```text
                                  ┌────────────────────────┐
                                  │   Odoo 17 (ERP Client) │
                                  │ (Ventes, CRM, Stock...)│
                                  └───────────┬────────────┘
                                              │ XML-RPC (Lecture Seule)
                                              ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ SmartERP AI Backend (FastAPI)                                                          │
│                                                                                        │
│   ┌───────────────────────┐    Background Task    ┌────────────────────────────────┐   │
│   │   Odoo KPI Reader     │────────────────────►│ PostgreSQL Cache               │   │
│   │ (Sync / 15 min loop)  │                     │ (kpi_cache, history, alerts)   │   │
│   └───────────────────────┘                     └──────────────┬─────────────────┘   │
│                                                                │                     │
│   ┌───────────────────────┐                                    │ Fast Read Query     │
│   │  Moteurs d'IA & RCA   │◄───────────────────────────────────┤                     │
│   │ (HealthScore/Recs/RCA)│                                    ▼                     │
│   └───────────┬───────────┘                     ┌────────────────────────────────┐   │
│               │                                 │ API REST Services              │   │
│               └────────────────────────────────►│ (/api/kpis, /api/chat, etc.)   │   │
│                                                 └──────────────┬─────────────────┘   │
└────────────────────────────────────────────────────────────────┼───────────────────────┘
                                                                 │ REST / JSON
                                                                 ▼
                                                  ┌────────────────────────────────┐
                                                  │ Next.js Frontend (Dashboard)   │
                                                  │ - Chat Assistant IA            │
                                                  │ - Health Score & RCA Cards     │
                                                  │ - Graphiques & Recommandations │
                                                  └────────────────────────────────┘
```

### Avantages de cette Architecture :
1. **Performance Maximale** : Réponses API en quelques millisecondes (lecture PostgreSQL).
2. **Haute Disponibilité** : Le dashboard reste fonctionnel même si Odoo est indisponible ou en maintenance.
3. **Sécurité & Intégrité** : Connexion en lecture seule — aucun risque de corruption des données d'Odoo.

---

## 📂 Structure du Projet

```text
smarterp-ai/
├── backend/                         # Service Backend FastAPI
│   ├── app/
│   │   ├── main.py                  # Point d'entrée FastAPI, middleware CORS, tâches d'arrière-plan
│   │   ├── config.py                # Gestion centralisée des variables d'environnement (Pydantic)
│   │   ├── database.py              # Connexion SQLAlchemy et gestion des sessions DB
│   │   ├── models/                  # Modèles de base de données (User, Tenant, KPICache, etc.)
│   │   ├── schemas/                 # Schémas Pydantic pour la validation API
│   │   ├── routers/                 # Endpoints REST (kpis, chat, alerts, health_score, etc.)
│   │   ├── services/                # Logique métier, moteurs IA, connecteurs ERP
│   │   │   ├── ai_agent.py          # Agent IA conversationnel (LLaMA 3.3)
│   │   │   ├── alert_engine.py      # Générateur et processeur d'alertes
│   │   │   ├── health_score_engine.py # Calculateur du score de santé (0-100)
│   │   │   ├── kpi_calculator.py    # Calculs analytiques des métriques métier
│   │   │   ├── kpi_sync.py          # Orchestrateur de synchronisation Odoo -> PostgreSQL
│   │   │   ├── odoo_connector.py    # Connecteur XML-RPC bas niveau vers Odoo
│   │   │   ├── odoo_kpi_reader.py   # Extraction des modèles Odoo (sale.order, crm.lead, etc.)
│   │   │   ├── recommendation_generator.py # Générateur de recommandations IA
│   │   │   └── root_cause_analysis.py # Moteur d'analyse des causes racines (RCA)
│   │   └── tests/                   # Tests unitaires et d'intégration
│   ├── Dockerfile                   # Fichier Docker pour le backend
│   └── requirements.txt             # Dépendances Python
│
├── frontend/                        # Application Frontend Next.js
│   ├── src/
│   │   ├── app/                     # Next.js App Router (pages & layouts)
│   │   │   ├── page.tsx             # Landing page / Accueil
│   │   │   ├── login/               # Page d'authentification
│   │   │   └── dashboard/           # Espace Dashboard, Audit, Chat, Settings
│   │   ├── components/              # Composants React réutilisables
│   │   │   ├── ui/                  # Composants d'interface génériques
│   │   │   ├── dashboard/           # KPICard, HealthScoreCard, RootCauseCard, RevenueChart, etc.
│   │   │   ├── chat/                # Interface conversationnelle de l'Agent IA
│   │   │   └── auth/                # Formulaires et gardes d'accès
│   │   ├── hooks/                   # Hooks React personnalisés (useKpis, etc.)
│   │   ├── lib/                     # Clients API, utilitaires et helpers
│   │   ├── store/                   # Stores de gestion d'état (Zustand)
│   │   └── types/                   # Définitions des types TypeScript
│   ├── Dockerfile                   # Fichier Docker pour le frontend
│   └── package.json                 # Dépendances Node.js / NPM
│
├── docs/                            # Documentation technique
│   └── architecture.md              # Spécifications détaillées de l'architecture
├── docker-compose.yml               # Orchestration Docker (5 conteneurs)
├── .env.example                     # Modèle des variables d'environnement
├── README.md                        # Documentation principale du projet
└── CONTRIBUTING.md                  # Guide de contribution de l'équipe
```

---

## 🚀 Guide de Démarrage Rapide

### 1. Prérequis

Assurez-vous d'avoir installé sur votre machine :
* **Git**
* **Docker Desktop** (avec Docker Compose v2)
* **WSL2** (recommandé pour les utilisateurs Windows)

Vérifiez vos installations :
```bash
docker --version
docker compose version
```

> ⚠️ **Note pour Windows** : Exécutez toujours les commandes `docker compose` depuis **PowerShell** ou un terminal WSL2 (évitez Git Bash pour prévenir les conflits de conversion de chemins).

---

### 2. Installation & Lancement

#### Étape 1 : Cloner le dépôt
```bash
git clone https://github.com/yassinelaamarti/smarterp-ai.git
cd smarterp-ai
```

#### Étape 2 : Configurer l'environnement
Copiez le fichier de configuration exemple :
```bash
cp .env.example .env
```
Ouvrez `.env` et ajustez si besoin les identifiants PostgreSQL, Odoo et la clé API Groq (`GROQ_API_KEY`).

#### Étape 3 : Lancer les conteneurs Docker
Pour le premier démarrage (compilation des images) :
```bash
docker compose up --build
```
Pour les démarrages ultérieurs :
```bash
docker compose up -d
```

#### Étape 4 : Initialiser la base Odoo (Premier usage)
1. Rendez-vous sur `http://localhost:8069`.
2. Créez une nouvelle base de données Odoo avec les paramètres définis dans votre `.env` (`ODOO_DB`, `ODOO_USERNAME`, `ODOO_API_KEY`).
3. **Cochez "Demo data"** lors de la création pour charger un jeu de données complet de démonstration.

---

## 🌐 Services Disponibles

Une fois les conteneurs lancés, les services suivants sont accessibles :

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend (Dashboard)** | `http://localhost:3000/dashboard` | Interface utilisateur principale |
| **Backend API (FastAPI)** | `http://localhost:8000` | Service REST API |
| **Documentation Swagger** | `http://localhost:8000/docs` | Interface interactive OpenAPI |
| **Instance Odoo 17** | `http://localhost:8069` | Instance ERP locale |
| **Base de données PostgreSQL** | `localhost:5432` | Base de données analytique |

---

## 🔗 Endpoints API Principaux

Le backend FastAPI expose les modules suivants :

* 📊 **KPIs & Analytics** :
  * `GET /api/kpis` — Récupère l'ensemble des KPIs calculés.
  * `GET /api/kpis/revenue-history` — Historique d'évolution du Chiffre d'Affaires.
  * `POST /api/kpis/sync` — Forcer une synchronisation manuelle du cache depuis Odoo.
* 💬 **Agent IA & Conversation** :
  * `POST /api/chat` — Envoie une question à l'Agent IA (LLaMA 3.3).
  * `GET /api/conversations` — Historique des conversations de l'utilisateur.
* 🩺 **Score de Santé & RCA** :
  * `GET /api/health-score` — Récupère le score de santé global et la décomposition.
  * `GET /api/root-cause` — Génère une analyse des causes racines d'un KPI.
* 💡 **Recommandations & Alertes** :
  * `GET /api/recommendations` — Liste des recommandations stratégiques générées par l'IA.
  * `POST /api/recommendations/{id}/acknowledge` — Acquitter une recommandation.
  * `GET /api/alerts` — Liste des alertes et dépassements de seuils actifs.
  * `GET/POST /api/settings` — Gestion des seuils de tolérance et paramètres.

---

## 👥 Équipe & Contexte Académique

Ce projet est réalisé dans le cadre du **Projet de Fin d'Année (PFA) — MGSI S8**, en partenariat direct avec **UrikaCloud**.

### Membres de l'Équipe :

| Nom & Prénom | Rôle | Contact / GitHub |
| :--- | :--- | :--- |
| **Laamarti Yassine** | Full-Stack Engineer | [@yassinelaamarti](https://github.com/yassinelaamarti) |
| **El Handi Zakariyae** | Full-Stack Engineer | [@ZakariyaeElhandi](https://github.com/ZakariyaeElhandi) |
| **Zouguari Yassine** | Full-Stack Engineer | [@yassinezouguari](https://github.com/yassinezouguari) |

---

## 📜 Licence

Ce projet est sous licence académique et réservé à l'usage interne de l'équipe **SmartERP AI × UrikaCloud**.