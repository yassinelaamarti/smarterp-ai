# Guide de contribution — SmartERP AI

Ce document définit les règles de travail de l'équipe pour garder le projet propre et professionnel.

## 1. Stratégie de branches

On utilise un modèle simplifié type **GitHub Flow** :

- `main` → toujours stable, déployable. Personne ne push directement dessus.
- `develop` → branche d'intégration (optionnel si le projet reste petit ; sinon on merge direct sur `main` via PR).
- `feature/<nom-courte-description>` → une branche par fonctionnalité.
  - Exemples : `feature/dashboard-kpis`, `feature/odoo-connector`, `feature/ai-agent-chat`
- `fix/<nom-courte-description>` → correction de bug.
- `docs/<nom>` → documentation uniquement.

**Règle d'or : jamais de commit direct sur `main`.** Toujours passer par une Pull Request, même seul.

## 2. Convention de commits

On suit **Conventional Commits** :

```
<type>(<scope>): <description courte>

[corps optionnel]
```

Types autorisés :
- `feat` : nouvelle fonctionnalité
- `fix` : correction de bug
- `docs` : documentation
- `style` : formatage, pas de changement de logique
- `refactor` : refactoring sans changement de comportement
- `test` : ajout/modification de tests
- `chore` : tâches diverses (config, dépendances, CI)

Exemples :
```
feat(dashboard): ajout du graphique évolution des ventes
fix(backend): correction du calcul du KPI marge brute
docs(readme): mise à jour instructions Docker
chore(ci): ajout du workflow de lint
```

## 3. Pull Requests

- Une PR = une fonctionnalité ou un correctif clair, pas un fourre-tout.
- Titre de la PR = même convention que les commits.
- Description : quoi, pourquoi, comment tester.
- Au moins **1 relecture par un autre membre de l'équipe** avant merge (même équipe de 3 → règle simple : jamais on ne merge sa propre PR sans qu'un autre ait au moins jeté un œil).
- Utiliser le template automatique (`.github/PULL_REQUEST_TEMPLATE.md`).

## 4. Issues & gestion de projet

- Toute tâche (feature, bug, tâche de recherche) = une Issue GitHub.
- Utiliser les labels : `frontend`, `backend`, `ia`, `docs`, `bug`, `enhancement`, `priority:high/medium/low`.
- Utiliser le **GitHub Project (Kanban)** avec les colonnes : `Backlog`, `To Do`, `In Progress`, `In Review`, `Done`.
- Assigner chaque issue à un membre + un milestone (ex : `Sprint 1`, `MVP Dashboard`, `MVP Agent IA`).

## 5. Environnement & secrets

- Ne **jamais** commit de fichier `.env` réel, clés API (Groq, Odoo) ou credentials.
- Toujours mettre à jour `.env.example` quand une nouvelle variable est ajoutée.

## 6. Code style

- Frontend : ESLint + Prettier (config par défaut Next.js).
- Backend : `black` + `ruff` pour Python.
- Un check CI basique doit passer avant merge (voir `.github/workflows/ci.yml`).
