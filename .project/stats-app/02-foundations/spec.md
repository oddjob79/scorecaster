# 02 Foundations

## Goal

A running skeleton, all started by Docker Compose:
- `app.db` built from the full database;
- a FastAPI app serving competitions and seasons;
- a React app shell that fetches them through typed API calls.

## Why

- Phases 03–05 each add an endpoint and a page. They need the database, the API, the typed API layer, routing, state and theming in place first.
- Building the plumbing end to end with the smallest endpoint shows every layer works before page logic is added.

## Shape of the solution

- **App database:** `scripts/build_app_db.py` reads `data/scorecaster.db` and writes `data/app.db`. It holds:
  - the 20 competitions, seasons from 2016/17, and their teams and matches;
  - `team_match_features` rows for those matches, copied as-is;
  - market-average odds.

  The build reports row counts and file size. It runs after each weekly `build_features.py`.
- **API (`scorecaster/api/`):**
  - an app factory;
  - a read-only SQLite engine (`file:data/app.db?mode=ro`);
  - Pydantic response models;
  - routers for `GET /competitions`, `GET /competitions/{code}/seasons` and `GET /health`.

  FastAPI serves the OpenAPI schema at `/openapi.json`. Uvicorn runs the app, with `--reload` in development.
- **One origin, no CORS:** the browser only ever talks to the front end's origin, and calls the API with relative `/api/...` URLs.
  - **In development,** Vite's dev server proxies `/api` to uvicorn on `localhost:8000`.
  - **In Docker,** nginx does the same.

  The API has no CORS middleware.
- **Web (`web/`):**
  - Vite + React + strict TypeScript, ESLint + Prettier, npm.
  - Tailwind, themed from `design/style.md` tokens.
  - Types generated from the OpenAPI schema (`npm run gen:api`), with hand-written fetch functions in `src/api/api.ts`.
  - TanStack Query for server data; code-based TanStack Router with the four MVP routes.
  - An app shell with navigation, and URL-driven league and season selects.
- **Client state:** a Zustand store persisted to `localStorage`, holding the theme and the last-used league and season.
- **Docker Compose:**
  - `api`: uvicorn, with `data/app.db` mounted read-only;
  - `web`: a multi-stage build, where Node runs `vite build` and nginx serves `dist/` and proxies `/api` to `api`.
- **Root readme:** how to start the app, and that it needs `data/app.db`.
- **Tests chunk** (last).

## Inputs from phase 01

- `design/style.md` tokens become the Tailwind theme.

## Decisions

- **Python packages:**
  - **`fastapi` and `uvicorn`** are installed explicitly, not `fastapi[standard]`. Uvicorn is the ASGI server that listens on the port and calls the app.
  - **`httpx`** is for tests only: FastAPI's `TestClient` is built on it. The running app doesn't need it.
- **npm, not pnpm:** it comes with Node, and one app doesn't need pnpm's shared store.
- **Vite proxy in development and nginx in Docker,** so there's one origin and no CORS. Front-end code uses relative `/api` URLs in every environment.
- **Built when first needed,** not in this phase:
  - shadcn/ui arrives with the first component a native element can't do well;
  - the ECharts wrapper arrives with the first real chart, in phase 04 (`04-team-page/01-charts.md`).

## Chunks

| # | Chunk | Status |
|---|---|---|
| 01 | [App database](01-app-db.md) | done |
| 02 | [API skeleton](02-api-skeleton.md) | done |
| 03 | [Web scaffold](03-web-scaffold.md) | done |
| 04 | [Typed API client and TanStack Query](04-api-client.md) | done |
| 05 | [Routing and app shell](05-routing-shell.md) | done |
| 06 | [Client state and theme toggle](06-store-theme.md) | done |
| 07 | [Docker Compose, nginx, run instructions, /debug page](07-docker-debug.md) | done |
| 08 | Tests | to plan |

## Open questions

None. The requirements are split in chunk 07: `requirements-api.txt` holds the API's packages, and `requirements.txt` includes it.

## Scope ledger

**Core**

- [x] `build_app_db.py`: scoped copy of competitions, seasons, teams, matches, features, market-average odds
- [x] FastAPI app factory, read-only engine, competitions, seasons and health endpoints
- [x] Vite + React + TypeScript scaffold with the `/api` dev proxy; Tailwind theme from tokens
- [x] typed API calls, TanStack Query, TanStack Router with the four routes
- [x] app shell with URL-driven league and season selects
- [x] Zustand persisted store (theme, last league and season)
- [x] Docker Compose (`api`, `web`)
- [x] root readme run instructions
- [ ] tests chunk

**Optional**

- [x] `/health` endpoint (API)
- [ ] request logging middleware (API)
- [ ] `build_app_db.py --check`: compare counts against the full database (script)
- [ ] path aliases such as `@/components` (web config)
- [x] a `/debug` page holding the API health status and the router devtools, both taken out of `AppShell`, unlinked from the nav (chunk 07)
