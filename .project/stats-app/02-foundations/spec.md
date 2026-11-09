# 02 Foundations

## Goal

A running skeleton: `app.db` built from the full database, a FastAPI app serving competitions and seasons, and a React app shell that fetches them through a generated, typed client, all started by Docker Compose.

## Why

- Phases 03–05 each add an endpoint and a page. They need the database, the API, the client generation, routing, state, theming and the chart wrapper in place first.
- Building the plumbing end to end with the smallest endpoint shows every layer works before page logic is added.

## Shape of the solution

- **App database:** `scripts/build_app_db.py` reads `data/scorecaster.db` and writes `data/app.db` using the same SQLAlchemy models. It holds:
  - the 20 competitions, seasons from 2016/17, and their teams and matches;
  - `team_match_features` rows for those matches, copied as-is;
  - market-average odds.

  The build reports row counts and file size. It runs after each weekly `build_features.py`.
- **API (`scorecaster/api/`):**
  - an app factory;
  - a read-only SQLite engine (`file:data/app.db?mode=ro`);
  - Pydantic response models;
  - routers for `GET /competitions` and `GET /competitions/{code}/seasons`.

  FastAPI serves the OpenAPI schema at `/openapi.json`. Uvicorn runs the app, with `--reload` in development.
- **One origin, no CORS:** the browser only ever talks to the front end's origin, and calls the API with relative `/api/...` URLs.
  - **In development,** Vite's dev server proxies `/api` to uvicorn on `localhost:8000`.
  - **In Docker,** nginx does the same.

  The API has no CORS middleware.
- **Web (`web/`):**
  - Vite + React + strict TypeScript, with ESLint + Prettier; packages managed with npm.
  - `vite.config.ts` proxies `/api` to `http://localhost:8000`, stripping the prefix.
  - Tailwind, with its theme built from `design/style.md` tokens, plus shadcn/ui initialised.
  - TanStack Router with the four MVP routes as placeholders, and TanStack Query.
  - `npm run gen:api`: `openapi-typescript` turns `/openapi.json` into `src/api/schema.ts`, and `openapi-fetch` wraps it as the typed client.
  - App shell: navigation, and a league and season picker fed by the two endpoints.
- **Client state:** a Zustand store persisted to `localStorage`. Phase 02 gives it the theme and the last-used league and season. Phases 03–05 add the rest (spec section 5.3).
- **Charts:** an `<EChart option>` wrapper (create, update, resize, dispose, theme switch), and light and dark ECharts themes from the same tokens as Tailwind.
- **Docker Compose:**
  - `api`: uvicorn, with `data/app.db` mounted read-only;
  - `web`: a multi-stage build, where Node runs `vite build` and nginx serves `dist/` and proxies `/api` to `api`.
- **Root readme:** how to start the app and that it needs `data/app.db`.
- **Tests chunk** (last): API tests for the two endpoints and the read-only connection; Vitest tests for the store and the theme switch.

## Inputs from phase 01

- `design/style.md` tokens become the Tailwind and ECharts themes.
- `design/components.md` names the shared components phases 03–05 build.

## Decisions

- **Python packages:**
  - **`fastapi` and `uvicorn`** are installed explicitly, not `fastapi[standard]`. Uvicorn is the ASGI server that listens on the port and calls the app.
  - **`httpx`** is for tests only: FastAPI's `TestClient` is built on it. The running app doesn't need it.
- **npm, not pnpm:** it comes with Node (v22.17.1, npm 10.9.2), and one app doesn't need pnpm's shared store.
- **Vite proxy in development and nginx in Docker,** so there's one origin and no CORS. Front-end code uses relative `/api` URLs in every environment.

## Open questions

- Where the new Python packages are listed: `requirements.txt`, or separate `requirements-api.txt` (fastapi, uvicorn) and `requirements-dev.txt` (httpx, pytest) so the pipeline's environment stays lean? Each package still needs your permission to install.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- `build_app_db.py`: scoped copy of competitions, seasons, teams, matches, features, market-average odds
- FastAPI app factory, read-only engine, competitions and seasons endpoints
- Vite + React + TypeScript scaffold (npm) with the `/api` dev proxy; Tailwind theme from tokens; shadcn/ui init
- TanStack Router (4 placeholder routes), TanStack Query, generated typed client
- app shell with league and season picker
- Zustand persisted store (theme, last league and season)
- ECharts wrapper and themes
- Docker Compose (`api`, `web`)
- root readme run instructions
- tests chunk: pytest API tests, Vitest store tests

**Optional**

- `/health` endpoint for the Compose healthcheck (API)
- request logging middleware (API)
- `build_app_db.py --check`: compare counts against the full database (script)
- path aliases such as `@/components` (web config)
