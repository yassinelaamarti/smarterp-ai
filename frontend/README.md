# Frontend — SmartERP AI

Ce dossier contiendra l'application Next.js 14.

## Initialisation (à faire par le Frontend Lead)

Depuis la racine du dossier `frontend/` (supprimer d'abord ce README ou le garder après) :

```bash
npx create-next-app@latest . --typescript --tailwind --app --eslint
```

Répondre aux prompts :
- App Router : Yes
- src/ directory : Yes (recommandé)
- Import alias : garder `@/*` par défaut

Puis installer les dépendances additionnelles :

```bash
npm install recharts axios
```

## Structure cible

```
frontend/
├── src/
│   ├── app/              # Routes (App Router)
│   ├── components/       # Composants réutilisables (KPI cards, charts, chat UI)
│   ├── lib/               # Client API, helpers
│   └── types/              # Types TypeScript
├── public/
├── package.json
└── Dockerfile
```
