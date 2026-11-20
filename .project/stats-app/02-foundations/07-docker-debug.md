# 07 Docker Compose, nginx, run instructions and the /debug page (plan)

## Goal

`docker compose up --build` runs the whole stats app on `http://localhost:8080`: the front end served by nginx, and the API behind it, reading `data/app.db`. The root readme says how to run it, both in development and in Docker.

The API health status and the router devtools move off the main site onto an unlinked `/debug` page.

## Depends on

01–06.

## How it fits together

```
browser ──> :8080  web container (nginx)
                    ├── /           -> the built front end (web/dist), any unknown path -> index.html
                    └── /api/...    -> http://api:8000/...  (prefix stripped)
                                       api container (uvicorn + FastAPI)
                                       └── reads /app/data/app.db (your data/ folder, mounted read-only)
```

- `web` publishes port 8080 for the app. `nginx` reaches `api` on Compose's private network under the hostname `api`.
- **`api` also publishes `127.0.0.1:8001` → 8000, for local troubleshooting** (decided 2026-11-20). It gives direct access to the API and its interactive docs at `http://localhost:8001/docs`; the docs page doesn't work through nginx's `/api/` prefix. It's bound to localhost so nothing else on the network can reach it, and uses 8001 so it doesn't clash with the development uvicorn on 8000. A real deployment leaves it out.
- The browser sees one origin, so there's no CORS, exactly as in development with the Vite proxy.

## Open choices

**1. Python requirements. Decided: A, split.**

The API imports only `fastapi`, `uvicorn`, `SQLAlchemy` and `pydantic`. The pipeline's `pandas` and `requests` aren't needed in the image.

| Option | Trade-off |
|---|---|
| **A. Split** (recommended) | `requirements-api.txt` lists the four API packages, and the image installs only that. `requirements.txt` starts with `-r requirements-api.txt`, then adds the pipeline's packages, so your local setup is unchanged. The image is smaller and builds faster. |
| **B. One file** | The image installs `pandas` and the rest too: bigger, slower to build, nothing gained. |

**2. Who writes what. Decided as below.**

- **Claude writes:** the Dockerfiles, `compose.yaml`, `nginx.conf`, `.dockerignore` and the requirements split. These are infrastructure, which you know from the back-end side.
- **You type:** the `/debug` page and the `AppShell` change, which are front-end. You run every command.


## Files that change

- `requirements-api.txt` (new) and `requirements.txt` (edited): the split.
- `docker/api.Dockerfile` (new): Python 3.13 slim, installs `requirements-api.txt`, copies `scorecaster/`, runs uvicorn on `0.0.0.0:8000`.
- `docker/web.Dockerfile` (new): two stages. Node 22 runs `npm ci` and `npm run build`; nginx serves the output.
- `docker/nginx.conf` (new): static files, the `/api/` proxy, and the fallback that serves `index.html` for app routes.
- `compose.yaml` (new): the two services, the read-only `data/` mount, the API health check, and port 8080.
- `.dockerignore` (new): keeps `node_modules`, `data/`, `.git` and build output out of the build context.
- `readme.md` (edited): a "Running the stats app" section.
- `web/src/pages/DebugPage.tsx` (new, you type it): API health, and the router devtools.
- `web/src/router.ts` (you edit it): a `/debug` route.
- `web/src/components/AppShell.tsx` (you edit it): health and devtools removed.

## Order of work

1. You type the `/debug` page and its route, and trim `AppShell`.
2. I write the requirements split; you install nothing new: the same packages are already installed.
3. I write the Docker files and `compose.yaml`; you run `docker compose up --build`.
4. I add the readme section; you check it reads right.
5. Verify, then add a "Docker" section to the quickstart guide.

## Code outline

```dockerfile
# docker/api.Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements-api.txt .
RUN pip install --no-cache-dir -r requirements-api.txt   # cached layer: only reruns when the file changes
COPY scorecaster/ scorecaster/
# Settings.app_db_path resolves to /app/data/app.db; compose mounts data/ there
CMD ["uvicorn", "scorecaster.api.main:create_default_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# docker/web.Dockerfile
FROM node:22-alpine AS build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci                      # exact versions from the lockfile
COPY web/ .
RUN npm run build               # tsc -b && vite build -> /web/dist (generated API types are committed)

FROM nginx:alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
```

```nginx
# docker/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    location /api/ { proxy_pass http://api:8000/; }   # trailing slash strips /api
    location / { try_files $uri /index.html; }        # /team/12 -> index.html; the router takes over
}
```

```yaml
# compose.yaml
services:
  api:
    build: { context: ., dockerfile: docker/api.Dockerfile }
    volumes:
      - ./data/app.db:/app/data/app.db:ro
  web:
    build: { context: ., dockerfile: docker/web.Dockerfile }
    ports: ["8080:80"]
    depends_on: [api]
```

```tsx
// web/src/pages/DebugPage.tsx
/** Render diagnostics: the API's health and the router devtools. */
export function DebugPage() {
  // the health query and its status, moved from AppShell
  // <TanStackRouterDevtools />, moved from AppShell
}
```

## Risks

- **The devtools render nothing in the Docker build.** It's a production build, and the package switches itself off there. On `/debug`, Docker shows the health status only; development shows both.
- **`depends_on` controls only start order,** not readiness. nginx may start before uvicorn is listening, and the first `/api` request can fail with a 502 for a second. The optional health check makes `web` wait for `api`.
- **The `data/` folder is mounted, not the single `app.db` file.**
  - **Why:** a single-file bind mount pins the file's original inode. `build_app_db.py` replaces `app.db` by renaming a new file over it, so a single-file mount would keep serving the old copy until the container restarted. A folder mount shows the renamed file.
  - **Cost:** the container can also read `scorecaster.db`, read-only.
- **`data/app.db` must exist before `docker compose up`.** Without it, `/health` fails, so the API's health check fails and `web` doesn't start. The readme says to run `build_app_db.py` first.

## Proof

- `docker compose up --build` starts both services. `http://localhost:8080` shows the app; navigation, league selects, theme toggle and remembered league all work.
- A deep link such as `http://localhost:8080/league/SP1?season=2020`, pasted into a new tab, loads the page, which proves the `index.html` fallback.
- `/debug` shows API "ok", in Docker and in development; the devtools appear in development only. The app bar shows neither.
- `docker compose ps` shows `web` on `0.0.0.0:8080` and `api` on `127.0.0.1:8001` only; `http://localhost:8001/docs` opens the API docs.
- `npm run check` passes.

## Expected test failures

None. The requirements split changes no code.

## Scope ledger

**Core**

- requirements split (option A)
- `api.Dockerfile`, `web.Dockerfile`, `nginx.conf`, `compose.yaml`, `.dockerignore`
- readme "Running the stats app" section
- `/debug` page and route; health and devtools removed from `AppShell`

**Optional** (ticked = written)

- [x] a health check on `api` (polling `/health`) with `web` waiting for it, so nginx never proxies to an API that isn't ready (compose.yaml)
- [x] long-lived cache headers for `/assets/` in nginx, since Vite's hashed file names change whenever content does (nginx.conf)
- [x] gzip compression for JavaScript, CSS and JSON responses (nginx.conf)
- [x] the API container running as a non-root user (api.Dockerfile)
