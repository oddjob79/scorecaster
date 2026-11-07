# 03 League page

## Goal

The league page: a season table and a form table for any league-season, as they stood on any date, split overall, home or away.

## Why

- It's the core view of the app, and its table and form chips recur on the team and compare pages.
- The date slider exercises every state layer: URL params for the view, the TanStack Query cache per date, prefetching, and component state while dragging.

## Shape of the solution

- **Endpoint:** `GET /competitions/{code}/seasons/{season}/table` with:
  - `view`: `table` or `form`;
  - `venue`: `overall`, `home` or `away`;
  - `date`: optional, defaults to today or the season's end.

  It returns one row per team: position, P, W, D, L, GF, GA, GD, Pts and the form sequence (e.g. `["W","W","L","D","W","L"]`).
- **Computation:** one Python function over `matches` finished before `date`. Table view counts every match. Form view counts each team's last 6 overall, or last 4 home or away, and ranks by points from those. Ties are broken by goal difference, then goals for.
- **Season dates endpoint:** first and last match dates, and the dates with matches, so the slider snaps to matchdays.
- **Web:**
  - `LeagueTable` and `FormChips` components;
  - view and venue toggles;
  - date slider: debounced, and it prefetches neighbouring dates.

  `/league/$code?season=&view=&venue=&date=` with a validated search-param schema; the store supplies defaults when params are missing.
- **Tests chunk** (last):
  - API tests for the table function: table and form, each venue, date cut-off, tie order;
  - Vitest and RTL tests for the components and the URL schema, with MSW for API responses.

## Inputs from phase 01

- `design/league.html` and `league-brief.md`.
- `design/data-queries.md` (league queries).

## Open questions

- **Points deductions** aren't in the football-data.co.uk files, so computed tables differ from official ones where points were deducted, e.g. Everton 2023/24, and several clubs in the lower English divisions. Show computed tables with a note, or add a hand-maintained deductions table?
- **Tie-breakers** differ by league: Spain and Italy use head-to-head before goal difference. Use goal difference everywhere (simpler), or per-league rules?
- Should the slider move by date or by matchday? Postponed matches make "matchday N" fuzzy, while dates are always exact.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- table/form endpoint (view, venue, date)
- season dates endpoint
- `LeagueTable`, `FormChips`, view and venue toggles, date slider
- league route with validated search params and store defaults
- tests chunk: API table tests, Vitest/RTL component and URL-schema tests with MSW

**Optional**

- slider prefetch of neighbouring dates (web)
- hand-maintained points deductions table (pipeline + endpoint)
- per-league tie-breakers (endpoint)
- position movement arrows against the previous matchday (endpoint + table)
- coloured zones for promotion, playoff and relegation places (league config + table)
