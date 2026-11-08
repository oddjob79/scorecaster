# 01 Design: visual direction and MVP page mockups

## Goal

An approved visual direction and an approved HTML mockup for each of the four MVP pages (league, team, matches, landing), before any app code.

## Why

- Phases 02–05 build what the mockups show. Layout and content changes cost minutes in a mockup and hours in React.
- The table, form chips and position chart appear on several pages. Designing all four pages first shows which components are shared, so phase 02 builds them once.

## Shape of the solution

- **Per page:** you write a brief from `design/brief-template.md`; a mockup is produced from it; you review it; it is revised until you approve it.
- **Mockups:** one standalone HTML file per page in `.project/stats-app/design/`, opened in a browser. Numbers are real, taken from `data/scorecaster.db` with read-only queries, so layouts are tested against real team names, table lengths and score ranges.
- **Mockups are references, not code.** Phase 02 onwards builds the real components; nothing is ported from the mockup files.

## Decisions

- **Order:** visual direction, then league, team, Matches and landing pages. The league page goes first because its table and form chips recur on the other pages. The landing page goes last because it summarises the others.
- **The brief is yours** and records the page's purpose and priorities. The mockup follows the brief.
- **Viewport and theme:** each mockup is drawn at desktop (1280px) and phone (390px) width, in light and dark themes.
- **Charts** in mockups are static SVG.
- **Viewing:** each mockup is also published as a private Artifact, for viewing and commenting.

## Chunks

| # | Chunk |
|---|---|
| 01 | [Visual direction](01-visual-direction.md) |
| 02 | [League page](02-league-page.md) |
| 03 | [Team page](03-team-page.md) |
| 04 | [Matches page](04-matches-page.md) |
| 05 | [Landing page](05-landing-page.md) |

This phase has no tests chunk: it produces no code.

## Scope ledger

**Core**

- [x] brief template (01)
- [x] style tile and colour and type tokens (01)
- [x] league page brief and mockup (02)
- [x] team page brief and mockup (03)
- [x] Matches page brief and mockup (04)
- [x] landing page brief and mockup (05)

**Optional** (ticked = written)

- [x] two or three alternative visual directions to choose from, not one (01)
- [x] dark-theme version of each mockup
- [x] phone-width (390px) version of each mockup
- [ ] mockup charts drawn with ECharts loaded from a CDN, so they look like the real charts (otherwise static SVG)
- [x] each mockup also published as a private Artifact for viewing and commenting
- [x] `design/data-queries.md`: the query behind each mockup's numbers, as a starting point for phases 03–05 endpoints
- [x] `design/components.md`: inventory of shared components with their props and states, from the approved mockups (after 05)
