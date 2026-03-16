---
## 📌 Project Overview

- Type: Telegram Mini App (WebApp inside Telegram)
- Frontend stack:
  - React
  - TypeScript
  - Tailwind CSS
  - TanStack Router (routing)
  - Zod
- Build tool: Vite
- Backend: Already implemented in Python (not part of this repo)
- Architecture: [Feature-Sliced Design (FSD)](https://feature-sliced.design/)
- The app is a SPA loaded inside Telegram WebView.

---

## 📂 Project Structure (FSD)

```
src/
  app/              # App initialization, providers, global router
    main.tsx
    main.css
    App.css
    App.tsx
    providers/
  shared/           # Reusable UI, libs, configs, and API clients
    api/
    lib/
    ui/
    config/
  entities/         # Business entities (user, chat, product)
    user/
      model/
      api/
      ui/
  features/         # User scenarios (auth, payments, forms)
    game/
    forecast/
    results/
  widgets/          # Compositions of features and entities (topbar, sidebar)
  pages/            # Page-level screens
    home/
    profile/
```

## 🎨 Code Style

### General

- Use **TypeScript** with strict typing. Avoid `any`.
- Always use **arrow function components**:
- Imports use **aliases** defined in `vite.config.ts`:
- Component names: `PascalCase`
- Variables and functions: `camelCase`
- **Dependency rule**: imports flow only **downwards**  
  (`shared → entities → features → widgets → pages → app`)

### Formatting

- Indentation: 2 spaces
- Quotes: **single**
- No semicolons
- Run ESLint + Prettier before commit

## 🌐 API Layer

- All HTTP requests use the `http` instance from `@/shared/api/http.ts` (axios).
- Validate responses with **Zod**.

## 📝 Commit Conventions

- `feat:` – new feature
- `fix:` – bug fix
- `refactor:` – code restructuring without feature changes
- `chore:` – tooling, configs, maintenance
- `docs:` – documentation only

## 📖 Special Instructions

When assisting with tasks:

1. Respect the **FSD structure** – place new code in the correct layer.
2. Follow **coding style** strictly (arrow functions, TS, Tailwind).
3. Ensure **typed API calls** (with Zod validation).
4. Prefer **small, self-contained changes** per task.
5. Always generate code **in English** (comments, naming, docstrings).
