# 08 Tests (plan)

## Goal

One pass of tests over what phase 02 built, before the phase merges.
- **Python (pytest),** in the existing suite: the app-database build and the API endpoints.
- **Front end (Vitest),** a new suite in `web/`: the pure logic, the store, and the API calls against mocked HTTP.

## Depends on

01–07.

## What gets tested

### Python: `tests/` (Claude writes these, in the existing suite's style)

| Test | Proves |
|---|---|
| **App database build:** the mini Premier League fixture loaded into a *file* database (`ATTACH` needs a file), built into `app.db` in `tmp_path` | the scope (20 competitions, the 2024/25 season, 12 matches, 4 teams, 24 feature rows, market-average odds only), no `.tmp` left behind, and the old file kept when a check fails |
| **API, through FastAPI's `TestClient`** on the built `app.db`: `/competitions` | 20 competitions, England first, divisions by tier |
| `/competitions/E0/seasons` and `/competitions/XX/seasons` | E0's season, then a 404 with "No competition with code XX" |
| `/health` | `{"status": "ok"}` |
| **Read-only engine** | a write through `create_default_app`'s connection settings fails |

`TestClient` needs `httpx`, which goes into `requirements.txt` beside `pytest`, so it's a dev-only package.

### Front end: `web/src/**/*.test.ts(x)` (you type these)

| Test | Proves |
|---|---|
| **Search validation:** `?season=2024` → `{ season: 2024 }`; `"abc"`, `1.5` or missing → `{}`; dates likewise | the URL boundary turns input into typed values or drops it |
| **`groupByCountry`** | grouping keeps the API's menu order |
| **The preferences store:** `setTheme` and `setLastLeague`; the persisted JSON in `localStorage`; `applyTheme` setting and removing `data-theme` | the store's behaviour and saved format |
| **`api.ts` against MSW:** success returns typed JSON; a 404 throws `ApiError` with FastAPI's `detail`; a non-JSON 500 throws with the status text | the only code that talks to the API |

**MSW** (Mock Service Worker) intercepts `fetch` inside the test process and answers with canned responses, so these tests need no running API.

## Decisions

**1. Make the pure functions importable. Decided: A.** The search validators are inline in `router.ts`, and `groupByCountry` is private to `LeaguePage.tsx`. To test them directly:
- **A (recommended):** move them, unchanged, to `web/src/lib/search.ts` and `web/src/lib/groupByCountry.ts`, exported. `router.ts` and `LeaguePage.tsx` import them. Behaviour is the same; they just become testable on their own.
- **B:** test them only indirectly, through the router and the page. That means fewer, heavier tests and no source changes.

**2. Component tests now, or with the pages. Decided: A, with the pages.**
- **A (recommended):** none now. The phase 02 pages are placeholders that phases 03–05 replace, so component tests written now would be thrown away. Each page phase's own tests chunk tests its components with React Testing Library.
- **B:** one now: `LeaguePage`'s selects, rendered in a memory-history router with MSW, asserting that choosing La Liga moves the URL to `/league/SP1`. It sets up the component-test harness early, against a page that phase 03 rewrites.

## Packages (each needs your go-ahead)

| Package | Kind | Latest now | For |
|---|---|---|---|
| `httpx` (Python) | dev | 0.28.1 | FastAPI's `TestClient` |
| `vitest` | dev | 5.1.1 | the test runner; reuses `vite.config.ts` (supports Vite 8) |
| `jsdom` | dev | 31.0.1 | a simulated browser (DOM, `localStorage`) for tests |
| `msw` | dev | 3.0.7 | HTTP mocking for the `api.ts` tests |
| `@vitest/coverage-v8` | dev | 5.1.1 | coverage reports |

## Files that change

- `requirements.txt`: adds `httpx`.
- `tests/test_app_db.py` and `tests/test_api.py` (new, Claude writes them).
- `web/vite.config.ts` (Claude edits it): a `test` block (environment `jsdom`, setup file).
- `web/src/test/setup.ts` (new, Claude writes it): starts and resets the MSW server around each test, and clears `localStorage`.
- `web/package.json` (Claude edits it): a `test` script; `check` also runs the tests.
- `web/src/lib/search.ts` and `web/src/lib/groupByCountry.ts` (choice 1A, you type them), and `router.ts` and `LeaguePage.tsx` importing them.
- `web/src/**/*.test.ts` (new, you type them).

## Order of work

1. Python: you install `httpx`; I write the two test files; you run `python -m pytest -q`.
2. Front end: you install the packages; I read their installed types and write the Vitest config and setup.
3. You move the pure functions (choice 1A) and type their tests.
4. You type the store tests, then the `api.ts` tests with MSW.
5. You run `npm test` and `npm run check`.
6. Add a "Tests" section to the quickstart guide; record the outcome.

## Risks

- **The store persists between tests in the same file.** Zustand stores are module-level, so one test's `setTheme("dark")` leaks into the next. The setup file clears `localStorage`, and each store test resets the state with `usePreferences.setState(...)`.
- **MSW intercepts by full URL,** while `api.ts` fetches relative `/api/...` paths. jsdom resolves relative URLs against its page URL (`http://localhost:3000` by default), so handlers are registered for that origin. This is confirmed against MSW 3's docs in step 2.
- **Phase 02's existing pytest suite must still pass.** The new tests add fixtures to `conftest.py` without changing existing ones.

## Proof

- `python -m pytest -q` passes, the existing 85 tests plus the new ones.
- `npm test` passes.
- `npm run check` (now including the tests) passes.

## Expected test failures

None in the existing suite.

## Scope ledger

**Core**

- `httpx`; `tests/test_app_db.py`; `tests/test_api.py`
- Vitest with jsdom and MSW; setup file; `test` script
- tests for search validation, `groupByCountry`, the store and `api.ts`
- choice 1A: pure functions moved, unchanged, to `web/src/lib/`

**Optional** (ticked = written)

- [x] coverage reports: `@vitest/coverage-v8`, `npm run test:coverage`, an HTML report in `web/coverage/` (git-ignored) (package.json, vite.config.ts)
- [x] `npm run check` runs the tests too (package.json)
