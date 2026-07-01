# Architecture — SmartERP AI

## 1. Vue d'ensemble

```
┌─────────────┐      API (XML-RPC/JSON-RPC, lecture seule)
│   Odoo 17    │ ───────────────────────────────┐
│  (client)    │                                  │
└─────────────┘                                  ▼
                                        ┌───────────────────┐
                                        │  Backend FastAPI    │
                                        │  - Connecteur Odoo   │
                                        │  - Calcul des KPIs    │
                                        │  - Orchestration IA    │
                                        └─────────┬──────────┘
                                                  │
                             ┌────────────────────┼────────────────────┐
                             ▼                                        ▼
                   ┌──────────────────┐                    ┌──────────────────┐
                   │   PostgreSQL       │                    │  Groq API           │
                   │  (cache analytics)  │                    │  LLaMA 3.3            │
                   └──────────────────┘                    └──────────────────┘
                             ▲
                             │ REST/JSON
                             │
                   ┌──────────────────┐
                   │  Frontend Next.js   │
                   │  Dashboard + Chat IA │
                   └──────────────────┘
```

## 2. Principes clés

- **Non intrusif** : aucune modification de l'installation Odoo du client. Connexion en lecture seule via l'API standard d'Odoo.
- **Multi-tenant (cible future)** : chaque client PME a ses propres credentials Odoo stockés de façon sécurisée.
- **Cache analytique** : les données lues depuis Odoo sont synchronisées périodiquement vers PostgreSQL pour accélérer les KPIs et réduire la charge sur l'ERP client.
- **Agent IA contextualisé** : l'agent ne répond pas dans le vide — il reçoit en contexte les KPIs et données agrégées pertinentes avant de générer une réponse (pattern RAG léger, pas de fine-tuning).

## 3. Modules fonctionnels (MVP)

| Module | Description |
|--------|-------------|
| Connecteur Odoo | Authentification + récupération Ventes/CRM/Stock |
| Moteur de KPIs | Calcul des 10 KPIs clés + détection d'anomalies (alertes) |
| Dashboard | Visualisation temps réel (Recharts) |
| Agent IA | Chat en français, questions/réponses sur les données, recommandations |

## 4. À définir par l'équipe

- Liste précise des 10 KPIs (à valider avec UrikaCloud / cas d'usage PME)
- Fréquence de synchronisation Odoo → PostgreSQL (temps réel via webhook vs polling périodique)
- Stratégie d'authentification multi-client (si plusieurs PME utilisent la plateforme)
