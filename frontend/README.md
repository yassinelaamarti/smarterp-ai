# Frontend — SmartERP AI

Frontend de **SmartERP AI**, développé avec **Next.js + TypeScript**.

Objectif : fournir une interface moderne pour :
- 📊 Dashboard analytique (KPIs, graphiques, alertes)
- 🤖 Agent IA conversationnel
- 🔐 Authentification et espace sécurisé
- 📡 Communication avec le backend via API

---

# Installation

Se placer dans le dossier frontend :

```bash
cd frontend
```

Créer le projet (à exécuter une seule fois si le frontend n'existe pas encore) :

```bash
npx create-next-app@latest . --typescript --tailwind --app --eslint --src-dir --import-alias "@/*"
```

Installer les dépendances :

```bash
npm install recharts axios zustand @tanstack/react-query
npm install lucide-react clsx tailwind-merge
```

Installer toutes les dépendances du projet :

```bash
npm install
```

---

## Stack technique

| Domaine | Technologie |
|----------|-------------|
| Framework | Next.js (App Router) |
| Langage | TypeScript |
| Styling | Tailwind CSS |
| API Client | Axios |
| Data Fetching | React Query |
| State Management | Zustand |
| Graphiques | Recharts |
| UI Utilities | clsx + tailwind-merge |
| Icônes | Lucide React |

---

# Structure du projet

```
frontend/src/
├── app/
│   ├── (auth)/              # Pages login/signup (à venir)
│   ├── (dashboard)/         # Zone protégée : dashboard, KPIs, chat IA
│   │   ├── dashboard/
│   │   └── layout.tsx        # Layout avec sidebar/navbar
│   ├── layout.tsx
│   └── page.tsx               # Landing page publique
├── components/
│   ├── ui/                     # Boutons, cards, inputs réutilisables
│   ├── dashboard/               # KPICard, ChartWidget, AlertBanner
│   └── chat/                     # ChatWindow, MessageBubble, ChatInput
├── lib/
│   ├── api.ts                    # Instance axios configurée (base URL)
│   └── utils.ts                   # Helpers (cn(), formatage nombres/devises)
├── hooks/
│   └── useKpis.ts                 # Hooks React Query pour appeler le backend
├── store/
│   └── useDashboardStore.ts        # Zustand : filtres actifs, période, etc.
└── types/
    └── index.ts                    # Types partagés (KPI, User, ChatMessage...)
```

## Variables d'environnement utilisées

- `NEXT_PUBLIC_API_URL` — URL du backend FastAPI (définie dans le `.env` à la racine du repo)

## Lancer en local (hors Docker)

```bash
npm install
npm run dev
```
→ http://localhost:3000

## Lancer via Docker (depuis la racine du repo)

```bash
docker compose up --build
```

## Conventions de code

- Composants réutilisables et génériques → `components/ui/`
- Composants spécifiques à une fonctionnalité → `components/dashboard/` ou `components/chat/`
- Tout appel API passe par `lib/api.ts` + un hook dans `hooks/` — jamais d'URL en dur dans un composant
- Types partagés dans `types/index.ts`