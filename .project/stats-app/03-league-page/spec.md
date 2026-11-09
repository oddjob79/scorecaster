# 03 League page

## Goal

The league page for any league-season, as it stood at 23:59 on any date with matches. It has five parts:
- a date slider;
- a table that switches between five stat views (table, form, goals, shots, discipline);
- an overall/home/away split;
- sortable columns;
- rotating top-performer cards.

## Why

- It's the core view of the app, and its table and form chips recur on the team page.
- The date slider exercises every state layer: URL params for the view, the TanStack Query cache per date, prefetching, and component state while dragging.

## Shape of the solution

- **Standings endpoint:** `GET /competitions/{code}/seasons/{season}/standings` with:
  - `date`: optional; counts matches on or before it, so the result is as of 23:59. Defaults to the latest date with matches.
  - `venue`: `overall`, `home` or `away`.

  It returns one row per team with every figure any view needs, so switching views costs no request:
  - **table:** P, W, D, L, GF, GA, GD, Pts;
  - **form window:** the same figures over the last 6 overall or last 4 home/away, plus those matches oldest to newest with date, opponent, home or away, score and result. The chips need these for their hover text, e.g. "Won 2–1 v Arsenal (H) · Sat 25 Jan";
  - **goals:** for and against per game, clean sheets, failed to score, BTTS rate, over-2.5 rate;
  - **shots:** shots, on target, accuracy, shots faced and corners per game;
  - **discipline:** fouls per game, yellows, reds, cards per game;
  - **leader inputs (overall only):** points, goals for and goals against over the last 6, current unbeaten run, home and away points per game.

  Shots and discipline are null where the league-season has no match stats.
- **Computation:** one Python function over finished `matches` up to the date, per team and venue. Table order: points, then goal difference, then goals for.
- **Season dates endpoint:** the dates with matches in the season, and matches played per date, so the slider snaps to matchdays and shows "N of M matches played".
- **Web:**
  - `DateBar`: slider over match dates, previous/next matchday buttons, the "as of 23:59" label and the matches-played count. It debounces while dragging and prefetches neighbouring dates.
  - `StatsTable`: one component; each view is a column definition (key, label, format, default sort). Columns sort on click, in the browser.
  - `FormChips`.
  - View pills: Table, Form, Goals, Shots, Discipline. Venue pills: Overall, Home, Away.
  - `TopPerformers`: eight cards, four at a time. The leaders are computed in the browser from the standings rows by pure functions (best and worst form, most goals and fewest conceded over the last 6, longest unbeaten run, most clean sheets, best home and away points per game). Ties name both teams, or "X and N others".
  - Route `/league/$code?season=&date=&view=&venue=` with a validated search-param schema. The store supplies the last-used league, view and venue when params are missing.
- **Tests chunk** (last):
  - API tests for the standings function: each venue, form windows, date cut-off including same-day matches, tie order, null stats;
  - Vitest tests for the column definitions, sorting and leader functions;
  - RTL tests for the date bar, table and cards, with MSW;
  - URL-schema tests.

## Inputs from phase 01

- `design/league.html` (approved) and `design/league-brief.md`.
- `design/data-queries.md` (league query).

## Open questions

- **Points deductions** aren't in the football-data.co.uk files, so computed tables differ from official ones where points were deducted, e.g. Everton 2023/24, and several clubs in the lower English divisions. Show computed tables with a note, or add a hand-maintained deductions table?
- **Tie-breakers** differ by league: Spain and Italy use head-to-head before goal difference. Use goal difference everywhere (simpler), or per-league rules?
- **Leaders in the browser or the API?** The browser is planned (pure TypeScript functions, unit-tested). A `/leaders` endpoint would keep every calculation in Python instead.
- **Leagues without match stats:** hide the Shots and Discipline pills, or show them with a "no data for this league" state? This applies to the National League, and to parts of some second divisions before 2017/18.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- standings endpoint (date, venue) with all view figures and leader inputs
- season dates endpoint
- `DateBar`, `StatsTable` with five views and click sorting, `FormChips`, view and venue pills
- `TopPerformers` with leader functions and previous/next paging
- league route with validated search params and store defaults
- tests chunk: API standings tests, Vitest column/sort/leader tests, RTL component tests with MSW, URL-schema tests

**Optional**

- slider prefetch of neighbouring dates (web)
- auto-rotation of the top-performer cards every 8 seconds, with pause and reduced-motion handling (web)
- sort column kept in the URL (web)
- hand-maintained points deductions table (pipeline + endpoint)
- per-league tie-breakers (endpoint)
- position movement arrows against the previous matchday (endpoint + table)
- coloured zones for promotion, playoff and relegation places (league config + table)
