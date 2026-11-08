# 05 Matches and landing pages

## Goal

The last two MVP pages, end-to-end tests across all four pages, and screenshots for the readme.

## Why

- The Matches page shows each day's results and the coming days' fixtures across the chosen competitions. Every match opens to its details, and fixtures open to a side-by-side comparison of the two teams.
- The landing page is the entry point. It shows what the data covers and links into the other pages.
- With all four pages in place, browser tests and screenshots cover the finished MVP.

## Shape of the solution

- **Data:** `app.db` also carries the scheduled matches from co.uk's fixtures files and their market-average pre-match odds. Refreshing them is `load_data.py --fixtures-only --refresh`, then `build_app_db.py`.
- **Match dates endpoint:** `GET /matches/dates?competitions=` returns the dates with matches and the last date with fixtures. That date is the forward limit for the day strip.
- **Day endpoint:** `GET /matches?date=&competitions=` returns the matches on one date across the chosen competitions: competition, kick-off, teams, status and score.
- **Match endpoint:** `GET /matches/{id}`.
  - **For a result:** half-time score, referee, match stats, both teams' positions before and after the match, and market-average odds (1X2, over/under 2.5, Asian handicap) pre-match and closing.
  - **For a fixture:** both teams' position, points, goal difference and form (6 overall, 4 home, 4 away), plus pre-match odds.

  The comparison chart reuses phase 04's team season endpoint, once per team.
- **Web:**
  - `DayStrip`: seven days, a month grid, previous/next buttons and the forward limit, with a line explaining that fixtures are published a few days ahead.
  - `CompetitionFilter`: a checkbox per competition and per country (part-selected shows as indeterminate), plus top divisions / all / none. The selection is kept in the Zustand store, so it follows you between visits.
  - `MatchList`: grouped by competition. `MatchRow` is an accordion row, collapsed on first load and on every change of day.
  - `ResultDetail`: match box, mirrored stat bars, and an odds table with the outcomes that happened highlighted.
  - `FixtureDetail`, laid out on the same column grid as the row so the teams line up:
    - a versus panel;
    - a 3 × 3 odds grid (home | draw | away; handicaps and over/under in the outer columns);
    - an overlay chart (position, home/away, form, goals; home team in `accent`, away team in `series-2`, a team's second series dashed).
  - Route `/matches?date=` with a validated schema.
- **Season metrics table:** `build_app_db.py` writes one row per competition-season with the 13 landing metrics. Building it scans the odds, so it's precomputed rather than run per request. Each row also carries its match-stats and odds coverage, so the API can blank seasons below 80%.
- **Landing endpoints:**
  - **season metrics:** `GET /competitions/{code}/season-metrics`, plus the all-competitions average per season (weighted by matches);
  - **Elo top 10:** `GET /competitions/{code}/elo-top`: each team's latest Elo in one division, for teams playing in the current season.
- **Landing page:**
  - a hero with the title and tagline;
  - the about text;
  - **Season by season:** country and competition pills, a metric select, bars per season and a dashed all-competitions line. Its option builder is a pure function.
  - **Strongest teams right now:** country and division pills, the top 10, and a "What is Elo?" `<details>` explainer.
- **End-to-end:** Playwright tests driving the running app: pick a league, move the slider, open a team, open Matches, change day, expand a result and a fixture.
- **Readme:** screenshots or a short screen recording of the four pages.
- **Tests chunk** (last):
  - API tests for the dates, day, match and landing endpoints, including the forward limit and positions before and after;
  - Vitest tests for the filter logic, the odds grid and the overlay option builders;
  - RTL tests for the day strip, filter and accordion, with MSW;
  - the Playwright suite.

## Inputs from phase 01

- `design/matches.html` (approved) and `design/calendar-brief.md`.
- `design/landing.html` (approved) and `design/landing-brief.md`.
- `design/data-queries.md` (matches and landing queries, including the season metrics query).

## Open questions

- **Stale fixtures:** a fixture stays `scheduled` until the next refresh loads its result. Show it as "result to come", or hide fixtures dated before today?

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- scheduled matches and their pre-match odds in `app.db`
- match dates, day and match endpoints
- Matches page: `DayStrip`, `CompetitionFilter` (store-backed), `MatchList`, `ResultDetail`, `FixtureDetail`, validated URL
- season metrics table in `build_app_db.py`
- landing endpoints: season metrics with the all-competitions average, Elo top 10 per division
- landing page: hero, about, Season by season chart, Elo top 10 with the explainer
- Playwright end-to-end tests across the MVP
- readme screenshots or recording
- tests chunk: API, Vitest, RTL and Playwright as above

**Optional**

- competition selection in the URL as well, so a filtered day is shareable (web)
- a dedicated match page instead of the accordion (route + page)
- favourite teams pinned on the landing page (needs phase 04 favourites)
- coverage summary on the landing page: leagues, seasons, match counts (endpoint + card)
- more market metrics on Season by season: calibration, Pinnacle against market-average margin, closing-line movement (summary table + metric list)
