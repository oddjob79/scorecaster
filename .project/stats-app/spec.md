# Stats app: spec (draft 3)

Responds to `intent.md`. Section 11 lists everything still open.

## 1. Purpose, audience and data scope

**Decided:** a stats site with a market lens. It covers historical team and league stats, plus odds treated as data (what the market implied, and what happened). There's no betting advice until phase 02's model exists.

**MVP goal:** *Explore any team's or league's history across Europe's core leagues over the last decade, and see how well the betting market priced it.*

### Leagues

**Decided:** 20 competitions in 9 countries.

| Country | Divisions | Pyramid Elo |
|---|---|---|
| England | E0–E3, National League (EC) | Yes |
| Scotland | SC0–SC3 | Yes |
| Germany | D1, D2 | Yes |
| Italy | I1, I2 | Yes |
| Spain | SP1, SP2 | Yes |
| France | F1, F2 | Yes |
| Portugal | P1 | No (one division) |
| Netherlands | N1 | No (one division) |
| Belgium | B1 | No (one division) |

Coverage within these: referees are recorded only for English and Scottish leagues, and the National League (EC) has match stats for 3% of matches.

### Seasons

**Decided:** 2016/17 to the current season inclusive (2026/27 today). All 20 competitions run August–May.

Elo and form features need history from before the window. They're copied from the full feature table (built from 2005/06), so 2016/17 opens with established ratings.

## 2. MVP

### Pages

1. **Landing page:** league and season picker. Headline charts: current Elo top 10 per pyramid (a Championship side can rank above a Premier League side) and home advantage by league over the decade.
2. **League page:** league table and form table (below), with a date slider.
3. **Team page:** position, form, splits and the Elo journey (below).
4. **Compare page:** league position by matchday for chosen teams (below).

### League page: tables

One table component with three controls:

| Control | Values | Effect |
|---|---|---|
| View | **Table**, **Form** | Table: all matches in the season so far. Form: each team's last N matches only, ranked by points from those matches. |
| Venue | **Overall**, **Home**, **Away** | Home counts only home matches; away only away matches. |
| Date slider | Any date in the season | Everything is computed from matches before that date. |

Columns in every combination: Pos, Team, P, W, D, L, GF, GA, GD, Pts, and **Form** as W/D/L chips for the last N matches in that venue, oldest to newest (e.g. `W W L D W L`). N defaults to 6, the usual length of a form table.

Example: *Form · Home · 1 Feb 2025* ranks teams by points from their last 6 home matches before 1 February 2025 and shows those 6 results as chips.

The table and form tables are both computed from `matches` in the API. The feature table's `form_*` columns are pre-kick-off values at fixed windows (4, 6, 8) and don't carry the W/D/L sequence, so they don't fit here.

### Team page

- **Header:** current league, position, points, and form chips for the last 6 matches overall, home and away (three rows).
- **Season record:** P W D L GF GA Pts, split overall/home/away, for a chosen season.
- **Position chart:** league position by matchday for the chosen season. It's the compare page's chart with one team.
- **Goals for and against** per match over the season, with a rolling average.
- **Elo journey:** Elo across all seasons in range, with background bands for the division the team was in each season and a zoom slider. Up to 2 overlay teams from the same pyramid.
- **"Add to compare"** button (section 5.3).

### Compare page

League position by matchday for up to 6 teams from one league-season. The y axis is inverted (1st at the top), and a team's line ends at its last match. Teams come from the compare basket or a picker. A form table filtered to just those teams sits below the chart, with Overall/Home/Away tabs.

**Scope change from draft 2:** position is the only metric on the compare page. Elo lives on the team page, and points and goals are in the tables. This removes the metric picker, the hardest part of the old performance chart.

### Effort (1 = an afternoon, 10 = several weeks; scaffolding not included)

| Piece | Effort | Notes |
|---|---|---|
| Table and form endpoints (overall/home/away, as at date) | 3 | One Python function: matches before date → per-team rows. Form adds "last N" per team and the chip sequence. |
| Table component with view, venue and slider | 3 | One component, one set of URL params. Prefetches neighbouring dates. |
| Position-by-matchday endpoint and chart | 3 | Positions after each matchday per team; one ECharts option builder shared by team and compare pages. |
| Team page | 4 | Mostly reuses the above. Elo journey is the one new chart. |
| Compare page + basket | 2 | Position chart + filtered form table + Zustand basket. |
| Landing page | 2 | Two aggregate queries, two charts. |

Changing to form tables is a small overhaul. No code exists yet, and it simplifies the MVP: the free multi-metric chart (effort 6) becomes a position chart and a table that several pages share (about 3 + 3).

### Extensions (in order)

1. **Market section:** calibration chart, bookmaker margins by source and season, biggest upsets; this week's fixtures with head-to-head and both teams' form tables.
2. **MCP server** (section 6).
3. **Chat page** (section 6).
4. **Model pages** once phase 02 exists.

## 3. Repository

**Decided:** shared repo.

```
scorecaster/        existing package
scorecaster/api/    FastAPI app: routers, Pydantic response models, queries
web/                Vite + React + TypeScript front end (own package.json)
docker/             Dockerfiles, nginx config
compose.yaml
```

## 4. Back end

**Decided:** FastAPI, Pydantic, SQLAlchemy. No authentication.

- The API reads `data/app.db` (section 7) through a read-only connection (`file:...?mode=ro`).
- Pydantic response models generate the OpenAPI schema, and the front end's TypeScript types are generated from it.
- Security baseline: parameterised queries, Pydantic validation of every parameter, CORS limited to the front end's origin, no secrets in the repo.

## 5. Front end

**Decided:** React, Vite, TanStack Router, TanStack Query, Zustand, Vitest + React Testing Library, Tailwind + shadcn/ui, ECharts, strict TypeScript, ESLint + Prettier, `openapi-typescript` + `openapi-fetch`, dark mode. No Next.js.

### 5.3 State: one owner per value

| Where | Holds | Example |
|---|---|---|
| **TanStack Query cache** | Data from the API | E0 2024/25 form table, home, as at 2025-02-01 |
| **URL search params** | What the current page shows | `/league/E0?season=2024&view=form&venue=home&date=2025-02-01` |
| **Zustand, persisted to `localStorage`** | What follows you between pages and visits | Compare basket, favourite teams, form length N, last-used league and venue, theme, recently viewed teams |
| **Component state** | Transient UI | Slider position mid-drag, open dropdown |

The store holds defaults, and the URL owns the current view. Opening `/league` with no params fills them from the store's last-used values; from then on the URL is the owner.

### 5.6 Component libraries

There are three layers: styling (Tailwind), accessible behaviour primitives (Radix), and all-in-one styled libraries (MUI, Mantine). Tailwind is chosen for styling. shadcn/ui copies Radix-based components styled with Tailwind into the repo, giving accessible widgets with one styling system and code you own.

### 5.7 Charts: ECharts

- **Options object, not React components.** Charts are typed `EChartsOption` objects built by pure functions, which is what gets unit-tested.
- **A `<EChart>` wrapper component** handles creating the chart, updating it, resizing, theme switching and disposal.
- **Light and dark themes** come from the same colour tokens as Tailwind.
- **Modular imports** from `echarts/core` keep the bundle small.

## 6. AI integration

**Decided:** MCP server first, as an extension. Ollama is out of scope.

- **MCP server:** tool functions (`get_head_to_head`, `get_league_table`, `get_form_table`, …) exposed through the Python MCP SDK.
- **Chat page:** a FastAPI tool-use loop against the Claude API, using the same tool functions, streaming to a React page; each person supplies their own API key.

Both run locally against your own database.

## 7. Data terms, the app database and distribution

### What football-data.co.uk says

The disclaimer page covers liability and gambling only. The terms on use are on the data page (`football-data.co.uk/data.php`, read 2026-11-06):

> "it's all FREE, however its use is intended for private individuals only, NOT commerical or data training products using automated bots/scrapers/AI."

No other page found states copyright, licence or redistribution terms. 

**Decided:** the repo doesn't distribute data and doesn't help anyone obtain it (section "Distribution" below).

### The app database

**Decided:** option B. `scripts/build_app_db.py` reads the full database and writes `data/app.db` with:

- the 20 competitions, seasons from 2016/17, and their teams and matches;
- `team_match_features` rows for those matches, copied as-is;
- market-average odds only;
- market summary tables computed from the full odds.

Estimated ~180 MB, roughly 50–60 MB compressed. The build reports the real size. The API only reads `app.db`.

### Distribution

**Decided:** no data in the repo, no download link and no stats-app instructions or helpers for getting data. The stats-app README section says:

- the data comes from football-data.co.uk, credited with a link;
- the data isn't the author's to redistribute, so none is included;
- the app needs `data/app.db` to run;
- anyone wanting to run it should obtain the data themselves and ask football-data.co.uk for permission. This should abide by the spirit of the website's disclaimer.

README screenshots and a screen recording show the app to readers who don't run it.

### READMEs

**Decided:** two READMEs, set up as the first step of the stats-app work.

| README | Covers |
|---|---|
| `readme.md` (root) | Brief introduction to the project as a whole. Stats app: screenshots or recording, tech stack, how to run it (needs `data/app.db`), data credit and the not-redistributed note. Link to `scorecaster/readme.md`. |
| `scorecaster/readme.md` | The data and model side: the current root README moved here (quick start, cache, database, features, data quality), with relative links fixed (`docs/glossary.md` → `../docs/glossary.md`) and a note that commands run from the repo root. |

## 8. Design workflow

**Decided:**

Each page...
1. Provide a written spec
2. Mockups are then created
3. Iterative refinement takes place
4. Briefs and final mockups go in `.project/stats-app/design/`.

## 9. Known gaps

- **Fixtures:** co.uk publishes only the next round.
- **Coverage:** referees only in English and Scottish leagues; National League match stats 3%; about 90% match-stat coverage in some divisions. Pages show "no data" states.
- **Elo comparability:** valid within a pyramid, not between countries.

## 10. Scope ledger

**Core**

- `scripts/build_app_db.py`: the app database (option B).
- `scorecaster/api/`: FastAPI app; read-only session on `app.db`; Pydantic response models; routers for:
  - competitions and seasons;
  - table and form table (view, venue, N, date);
  - positions by matchday;
  - team summary;
  - Elo journey;
  - landing headlines.
- `web/`: Vite + React + TypeScript; TanStack Router, TanStack Query, Zustand (persisted); generated API client; ECharts wrapper; the 4 pages; Tailwind + shadcn/ui components.
- Vitest + React Testing Library tests: option builders, store, URL schemas, components (one pass at the end).
- READMEs: current README moved to `scorecaster/readme.md`; new root README with the stats app, data credit and not-redistributed note (section 7).

**Optional, chosen**

- Docker Compose: `compose.yaml`, `docker/`.
- README screenshots or screen recording.
- MSW API mocks for component tests: `web/src/test/`.
- Playwright end-to-end tests: `web/e2e/`.
- pytest tests for the API: `tests/api/`.
- Market summary tables: inside `build_app_db.py` (needed for Extension 1).
- Dark mode toggle.
- MCP server: `scorecaster/mcp/` (Extension 2).
- Chat page with the Claude API: `scorecaster/api/chat.py`, `web/src/pages/chat` (Extension 3).

**Out of scope**

- Authentication of any kind.
- CI and deployment pipelines.
- Ollama.
- Leagues outside the 9 countries; seasons before 2016/17.

## 11. Open decisions

1. Form table length: fixed at 6, or user-selectable (4, 6, 8)? (section 2)
2. First page brief to write. (section 8)
