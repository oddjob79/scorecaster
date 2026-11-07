# 05 Compare and landing pages

## Goal

The last two MVP pages, end-to-end tests across all four pages, and screenshots for the readme.

## Why

- The compare page shows several teams' seasons side by side, using the basket built in phase 04.
- The landing page is the entry point. It shows what the data covers and links into the other pages.
- With all four pages in place, browser tests and screenshots cover the finished MVP.

## Shape of the solution

- **Compare page:**
  - the positions-by-matchday endpoint (phase 04) called for up to 6 teams from one league-season;
  - teams come from the basket or a picker;
  - a position chart with one line per team;
  - a form table filtered to those teams, with Overall/Home/Away tabs.

  `/compare?code=&season=&teams=` with a validated schema.
- **Landing endpoints:**
  - **Elo top 10 per pyramid:** each team's latest Elo, for teams playing in the current season;
  - **home advantage per league per season:** 2016/17 onwards.
- **Landing page:** league and season picker, the two headline charts, and favourite teams if chosen in phase 04.
- **End-to-end:** Playwright tests driving the running app: pick a league, move the slider, open a team, add two teams to compare, check the compare chart and the URL.
- **Readme:** screenshots or a short screen recording of the four pages.
- **Tests chunk** (last): API tests for the landing endpoints; Vitest and RTL tests for the compare page and the landing charts; the Playwright suite.

## Inputs from phase 01

- `design/compare.html`, `design/landing.html` and their briefs.
- `design/data-queries.md` (compare and landing queries).

## Open questions

- **Home advantage metric:** home win rate, or home points per game minus away points per game? The second also counts draws.
- **Single-division leagues** (P1, N1, B1) have no pyramid. Show a top 10 per league for them, or leave them off the Elo chart?
- **Teams from different league-seasons on one compare chart:** allowed (aligned by matchday), or one league-season only, as the spec says?

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- compare page: multi-team positions chart, basket and picker, filtered form table, validated URL
- landing endpoints: Elo top 10 per pyramid, home advantage per league-season
- landing page with picker and the two charts
- Playwright end-to-end tests across the MVP
- readme screenshots or recording
- tests chunk: API landing tests, Vitest/RTL compare and landing tests

**Optional**

- share button copying the compare URL (web)
- favourite teams pinned on the landing page (needs phase 04 favourites)
- coverage summary on the landing page: leagues, seasons, match counts (endpoint + card)
