# 04 Typed API client and TanStack Query (plan)

## Goal

The front end's API types are generated from FastAPI's OpenAPI schema, and the code that calls the API is hand-written against those types. If an endpoint's response shape changes in Python, `npm run check` fails wherever the front end uses it. TanStack Query fetches and caches the data.

The proof page lists the 20 competitions from `/competitions`, grouped by country, with the health line moved onto the same machinery.

## Depends on

02 (the API), 03 (`web/`).

## The rest of phase 02, one chunk each

| # | Chunk |
|---|---|
| 04 | Typed API client and TanStack Query (this plan) |
| 05 | Routing (TanStack Router), app shell with navigation and pickers, shadcn/ui |
| 06 | Zustand store (persisted) and theme toggle |
| 07 | ECharts wrapper and themes |
| 08 | Docker Compose, nginx, root readme run instructions |
| 09 | Tests |

## Decided: generated types, hand-written fetch (option C)

Three options were weighed:
- **A.** Generate everything: types, an SDK function per endpoint, and a bundled HTTP client.
- **B.** Hand-write everything.
- **C.** Generate the types only; hand-write the fetch code.

C was chosen.
- **Drift is caught at compile time:** a Pydantic change shows up as a type error in the front end.
- **Nothing generated runs in the browser:** the generated file holds only `type` declarations, which disappear at build time. Every line that executes is ours, with no generated client acting as a black box.
- **Why not B:** hand-written types can silently drift from the Python models.

The generator is `@hey-api/openapi-ts` with only its `@hey-api/typescript` plugin. `openapi-typescript` was ruled out because its latest release declares `typescript ^5.x` as a peer, and the project has TypeScript 6.

## Where the schema comes from

`scripts/export_openapi.py` writes FastAPI's schema to `web/openapi.json` without starting a server: it calls `create_app(...).openapi()`. The generator reads that file. Both `openapi.json` and the generated types are committed, so that:
- `npm run build` works without the API running, including inside the Docker build in chunk 08;
- a schema change shows up as a diff in review.

FastAPI names each operation after its route function (`generate_unique_id_function` in `scorecaster/api/main.py`), so the generated per-operation types read e.g. `ListCompetitionsResponse`.

## Packages

| Package | Kind | Installed |
|---|---|---|
| `@tanstack/react-query` | runtime | 5.107.1 |
| `@hey-api/openapi-ts` | dev | 0.99.0 |

## Files that change

- `scorecaster/api/main.py` (done): operation ids from route function names.
- `scripts/export_openapi.py` (done): writes `web/openapi.json`.
- `web/openapi-ts.config.ts` (done): types only, into `src/api/generated/`.
- `web/package.json` (done): `gen:api` runs the export, then the generator.
- `web/.prettierignore`, `web/eslint.config.js` (done): skip `openapi.json` and the generated folder.
- `web/src/api/generated/` (generated, never edited by hand).
- `web/src/api/api.ts` (new, you type it): `getJson` and one function per endpoint.
- `web/src/api/queries.ts` (new, you type it): `queryOptions` for health, competitions and seasons.
- `web/src/main.tsx` (you edit it): wraps the app in `QueryClientProvider`.
- `web/src/App.tsx` (you edit it): `useQuery` instead of the hand-rolled effect, plus the competitions list.

## Order of work

1. You install the packages (done).
2. You run `npm run gen:api`, and we read the generated types together.
3. You type `api.ts`, then `queries.ts`.
4. You wire the provider into `main.tsx`.
5. You rewrite `App.tsx` with `useQuery`.
6. Verify, then add a "TanStack Query and typed API calls" section to `data/frontend-quickstart.md`.

## Code outline

```ts
// web/src/api/api.ts
import type { CompetitionResponse, SeasonResponse } from "./generated";

/** An HTTP error from the API, with FastAPI's "detail" message. */
export class ApiError extends Error {
  // status: e.g. 404; message: e.g. "No competition with code XX"
}

/** Fetch /api<path> and return its JSON as T; throw ApiError on failure. */
async function getJson<T>(path: string): Promise<T> {
  // fetch(`/api${path}`) -> if !response.ok, read {detail} and throw ApiError
  // -> otherwise return (await response.json()) as T
}

/** GET /competitions: every competition, in menu order. */
export const listCompetitions = () =>
  getJson<CompetitionResponse[]>("/competitions");

/** GET /competitions/{code}/seasons: newest first. */
export const listSeasons = (code: string) =>
  getJson<SeasonResponse[]>(`/competitions/${encodeURIComponent(code)}/seasons`);

/** GET /health. */
export const checkHealth = () => getJson<{ status: string }>("/health");
```

```ts
// web/src/api/queries.ts
import { queryOptions } from "@tanstack/react-query";

export const healthQuery = queryOptions({
  queryKey: ["health"],
  queryFn: checkHealth,
});

export const competitionsQuery = queryOptions({
  queryKey: ["competitions"],
  queryFn: listCompetitions,
});

/** One competition's seasons; the code is part of the cache key. */
export const seasonsQuery = (code: string) =>
  queryOptions({
    queryKey: ["competitions", code, "seasons"],
    queryFn: () => listSeasons(code),
  });
```

```tsx
// web/src/main.tsx: provider around <App />
const queryClient = new QueryClient();
// <QueryClientProvider client={queryClient}><App /></QueryClientProvider>
```

```tsx
// web/src/App.tsx
const health = useQuery(healthQuery);              // { data, isPending, isError }
const competitions = useQuery(competitionsQuery);  // data: CompetitionResponse[]
// render: title, health line, competitions grouped by country
```

The type names imported from `./generated` are confirmed against the generated file in step 2, before you type anything.

## Risks

- **`openapi.json` and the generated types go stale** if the API changes and nobody re-runs `npm run gen:api`. The habit is to regenerate whenever a Pydantic model or route changes.
- **`getJson<T>` trusts the server.** `response.json() as T` tells TypeScript the shape without checking it at runtime. The guarantee is that the types match the schema the API publishes, as long as both are generated from the same code.
- **hey-api is pre-1.0.** Its config keys can change between minor versions. `package-lock.json` pins the version installed.
- **Known audit finding, accepted (9 Nov 2026).**
  - **What:** `npm audit` reports 4 high advisories in `js-yaml` 4.x: CPU denial of service from crafted YAML. They come in through `@hey-api/openapi-ts` 0.99.0, whose `json-schema-ref-parser` 1.4.4 pins `js-yaml` 4.2.0. The fix exists only in js-yaml 5.
  - **Why it's accepted:** the generator runs at dev time and reads only our own `openapi.json`. `npm audit --omit=dev` reports 0 vulnerabilities.
  - **Next step:** re-check when hey-api moves to js-yaml 5.
- **hey-api 0.99 needs Node 22.18 or later.** Node was upgraded with `nvm install 22`.

## Proof

- `npm run gen:api` writes `src/api/generated/` with no errors.
- With the API running, `npm run dev` shows the health line and the 20 competitions grouped by country, England first.
- Rename a field in `CompetitionResponse` (e.g. `tier` → `level`), regenerate, and `npm run check` fails where `App.tsx` uses `tier`. Then undo it.
- `npm run check` and `npm run build` pass.

## Expected test failures

None. Naming operations after their functions changes only the OpenAPI schema, not any route's behaviour.

## Scope ledger

**Core**

- export script, types-only generator config, `gen:api` script, operation ids
- `api.ts` (`getJson`, `ApiError`, three endpoint functions)
- `queries.ts`, the provider, `App.tsx` on `useQuery`

**Optional** (ticked = written)

- [ ] TanStack Query Devtools (dev-only package)
- [ ] `QueryClient` defaults tuned for this data, e.g. `staleTime` (main.tsx); revisit in phase 03
- [x] `npm run gen:api` runs the Python export and the generator in one command (package.json)
