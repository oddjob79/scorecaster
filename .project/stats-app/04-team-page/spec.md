# 04 Team page

## Goal

The team page for any team in a league-season, as it stood at 23:59 on any date with matches. It shows:
- the team's position, points, goal difference, matches played and form;
- one chart panel with five views: league position, home and away table positions, form, goals, and the Elo journey since 2016/17.

## Why

- It answers "how is this team doing, and how has that changed?" in one place.
- The Elo journey is the view most specific to this project: it follows a club through promotions and relegations.
- It reuses phase 03's date bar and form chips, and adds the first ECharts views with tooltips.

## Shape of the solution

- **Teams endpoint:** `GET /competitions/{code}/seasons/{season}/teams`, which feeds the team picker.
- **Team season endpoint:** `GET /competitions/{code}/seasons/{season}/teams/{team_id}/matches?date=`. It returns one row per finished match up to the date (as of 23:59) with:
  - the date, opponent, home or away, score and result;
  - the team's position after that day in three tables: overall, home-only and away-only. Every team's matches up to that day count.

  The header figures (position, points, goal difference, played, form chips 6/4/4) and four of the chart views come from these rows.
- **Computation:** one pass over the season's matches in date order. It keeps running overall, home and away tallies for every team and ranks all three after each date, with phase 03's table order.
- **Elo journey endpoint:** `GET /teams/{team_id}/elo`. It returns Elo before each finished match since 2016/17 from `team_match_features`, with the competition each match was in.
- **Web:**
  - Cascading pickers: competition, then season, then team. Each choice filters the next.
  - `DateBar` from phase 03.
  - `TeamHeader`: stat tiles, and form chips for the last 6, home 4 and away 4 with each row's points.
  - `TeamChart`: one ECharts panel with view pills.

  Each view's `EChartsOption` comes from a pure builder:
  - **League position:** position after each match (1st at the top). The tooltip gives the position and result, e.g. "3rd · Won 1–0 v Liverpool (H)".
  - **Home / away:** home-table and away-table positions after each match. The tooltip names the table and the result.
  - **Form:** rolling points per game over the last 6 overall and last 4 home and away. The tooltip gives the figure and result.
  - **Goals:** scored above the axis and conceded below it, with 6-match averages. No tooltip.
  - **Elo journey:** all seasons since 2016/17, with division bands (`markArea`) and the selected date marked (`markLine`). No tooltip.

  Route: `/team/$teamId?code=&season=&date=&chart=` with a validated search-param schema. The store supplies the last-used competition and season.
- **Tests chunk** (last):
  - API tests for the team season function: the three table positions, same-day matches, a team's first home or away match, and tie order;
  - API tests for the Elo endpoint;
  - Vitest tests for each option builder and its tooltip text;
  - RTL tests for the pickers, header and chart panel, with MSW.

## Inputs from phase 01

- `design/team.html` (approved) and `design/team-brief.md`.
- `design/data-queries.md` (team and Elo queries).

## Decisions from the design

- Position is taken after each of the team's matches, counting every match played that day.
- Home / away shows table positions, not cumulative points.
- Elo is the one view that spans seasons; the others follow the selected season up to the date.
- No compare button and no overlay teams on the charts.

## Open questions

- **Elo scale across divisions:** pyramid Elo (design B) keeps a separate 1500-centred scale per division, so a club's line drops on promotion and rises on relegation. Leeds, for example, ends 2019/20 at 1663 in the Championship and ends 2020/21 at 1559 in the Premier League. For the journey, should the chart convert every value onto one scale (the top division's) using the per-boundary adjustments the pyramid already learns? Or show the raw values with the division bands explaining the jumps?
- **Gaps in the journey:** a team that drops below the lowest covered division (National League, Scottish League Two) or leaves a single-division league (P1, N1, B1) has seasons missing. Leave gaps in the line, or join across them?
- **Teams that moved mid-history:** the team picker lists teams in the chosen league-season. Should the Elo journey still show their seasons in other divisions? It does in the mockup.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- teams, team season (three table positions per match) and Elo journey endpoints
- cascading competition, season and team pickers
- `TeamHeader` with stat tiles and form chips with result tooltips
- `TeamChart` with five views and pure option builders; tooltips on position, home/away and form
- team route with validated search params and store defaults
- tests chunk: API tests, Vitest option-builder tests, RTL tests with MSW

**Optional**

- zoom slider (`dataZoom`) on the Elo journey (web)
- recently viewed teams in the team picker (store)
- favourite teams toggle (store)
- match list for the season with scores (table)
- head-to-head summary against a chosen opponent (endpoint + section)
