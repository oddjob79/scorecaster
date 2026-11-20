# Scorecaster

Football results, match stats and bookmaker odds for European leagues, turned into pre-match team features for forecasting results and goals, and explored through a stats app.

## Parts

| Part | Where | Status |
|---|---|---|
| **Data and models**: SQLite store, download cache, feature builder, data-quality report | [`scorecaster/readme.md`](scorecaster/readme.md) | Data pipeline complete; models planned |
| **Stats app**: league and form tables on any date, team histories with an Elo journey across divisions, daily results and fixtures | [`.project/stats-app/spec.md`](.project/stats-app/spec.md) | Foundations built; pages in progress |

The stats app is built with:
- **back end:** FastAPI, Pydantic and SQLAlchemy;
- **front end:** React, TypeScript, Vite, TanStack Router and Query, Zustand and Tailwind.

## Data

All match, stats and odds data comes from [football-data.co.uk](https://www.football-data.co.uk). It isn't ours to redistribute, so the repository contains none: `data/` is git-ignored. To run anything here you need that data, so obtain it yourself and ask football-data.co.uk for permission.

## Running the stats app

The app reads `data/app.db`, a read-only copy of the database cut down to what the app shows. Build it from `data/scorecaster.db` (see [`scorecaster/readme.md`](scorecaster/readme.md)) and rebuild it after each data update:

```bash
python scripts/build_app_db.py
```

### With Docker

```bash
docker compose up --build
```

| URL | What |
|---|---|
| `http://localhost:8080` | The app. nginx serves the front end and forwards `/api/...` to the API. |
| `http://localhost:8001/docs` | The API's interactive docs, reached directly. Bound to this machine only, for troubleshooting. |
| `http://localhost:8080/debug` | API health status. Not linked from the app. |

The API waits for its health check, then the front end starts. Both read `data/` read-only, so `build_app_db.py` can rebuild `app.db` while they run.

### For development

Start the API, with auto-reload, from the repo root:

```bash
uvicorn scorecaster.api.main:create_default_app --factory --reload
```

In a second terminal, start the front end's dev server, which proxies `/api` to the API:

```bash
cd web && npm install && npm run dev
```

Then open `http://localhost:5173`. `/debug` also shows the router devtools in development.

- **After changing a Pydantic model or route,** regenerate the front end's API types: `npm run gen:api` in `web/`.
- **Before committing front-end changes:** `npm run format`, then `npm run check` (type check, lint and formatting).
- **Python packages:** `requirements-api.txt` lists what the API needs. `requirements.txt` includes it, plus the pipeline's packages.

## Repository

```
scorecaster/     data and model package (readme inside); scorecaster/api/ is the stats app's API
web/             the stats app's front end
docker/          Dockerfiles and nginx config; compose.yaml is at the root
scripts/         pipeline scripts and one-task scripts (scripts/adhoc/)
tests/           pytest suite
docs/            glossary
.project/        intent, specs and chunk plans for each phase, and for the stats app
changes.md       what each phase delivered
```
