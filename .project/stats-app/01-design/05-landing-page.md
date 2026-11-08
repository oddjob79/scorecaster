# 05 Landing page

## Goal

An approved brief and mockup for the landing page: league and season picker, the current Elo top 10 per pyramid, and home advantage by league over the decade.

## Depends on

02, 03, 04 (links to and summarises them)

## Steps

1. You write `design/landing-brief.md` from the template.
2. Query real data:
   - current Elo top 10 for one pyramid;
   - home win rate per league per season, 2016/17 onwards.
3. Produce `design/landing.html`.
4. You review it; revise until approved.

## Proof

- You approve `landing.html`.
- Its numbers match the queried data.

## Outcome

Approved 2026-11-08. Sections in order:

- **Hero:** "Scorecaster" with the tagline "Football Results and Stats Site", and nothing else.
- **About this site:** your paragraph, the football-data.co.uk credit, and links to the league, team and Matches pages.
- **Season by season:** a country and competition selector, plus a metric select with 13 metrics:
  - **Results:** home win, draw, away win rate.
  - **Goals:** per game, over 2.5, both teams scored.
  - **Match stats:** shots, shots on target, corners per game.
  - **Discipline:** yellow and red cards per game.
  - **Market:** favourite won, bookmaker margin.

  Bars per season, with a dashed line for the average across all 20 competitions. Seasons with less than 80% coverage are left blank.
- **Strongest teams right now:** the Elo top 10 for one division, chosen by country and division, with a "What is Elo?" explainer.

Changes from the starting points:
- No league and season picker in the hero.
- Elo ranks one division at a time, not a whole pyramid, because each division keeps its own scale. A converted "whole pyramid" view was tried and dropped.
- The home-advantage heatmap became the season metrics chart.

## Scope ledger

**Core**

- steps 1–4
