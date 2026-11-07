# 04 Team page

## Goal

The team page: a team's current standing and form, its season record, its league position through a season, its goals, and its Elo journey across divisions since 2016/17.

## Why

- It answers "how is this team doing, and where has it been?" in one place.
- The Elo journey is the view most specific to this project: pyramid Elo puts a club's seasons in different divisions on one scale.
- It introduces the compare basket, the main piece of cross-page client state.

## Shape of the solution

- **Endpoints:**
  - **team summary:** current league, position, points, form sequences (6 overall, 4 home, 4 away) and season records split overall, home and away;
  - **positions by matchday:** for a team and season. It also serves several teams for the compare page in phase 05;
  - **goals series:** goals for and against per match in a season;
  - **Elo journey:** Elo after each match from `team_match_features`, the team's division per season, and up to 2 overlay teams from the same pyramid.
- **Web:**
  - header with form chips;
  - season record table;
  - position chart (inverted y axis);
  - goals chart with a rolling average;
  - Elo journey chart with division bands (`markArea`) and a zoom slider (`dataZoom`);
  - team search combobox, with recently viewed teams from the store;
  - "Add to compare" writing to the Zustand basket.

  Each chart's `EChartsOption` comes from a pure builder function.
- **Tests chunk** (last):
  - API tests for each endpoint;
  - Vitest tests for each option builder and for the basket actions in the store;
  - RTL tests for the page sections, with MSW.

## Inputs from phase 01

- `design/team.html` and `team-brief.md`.
- `design/data-queries.md` (team queries).

## Open questions

- **Gaps in the journey:** a team that drops below the lowest covered division (National League, Scottish League Two) or leaves a single-division league (P1, N1, B1) has seasons missing. Leave gaps in the line, or join across them?
- **Matchday:** is position taken after the team's Nth match, or after each round date? This must match the compare page and phase 03's slider decision.
- **Overlays:** chosen freely within the same pyramid, or suggested, e.g. teams that shared a division with this one?

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- team summary, positions by matchday, goals series and Elo journey endpoints
- team page sections and the three charts
- team search combobox
- "Add to compare" and the Zustand basket
- tests chunk: API endpoint tests, Vitest option-builder and store tests, RTL page tests with MSW

**Optional**

- recently viewed teams in search (store)
- favourite teams toggle (store)
- head-to-head summary against a chosen opponent (endpoint + section)
- match list for the season with scores (endpoint + table)
