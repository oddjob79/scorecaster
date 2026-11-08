# 03 Team page

## Goal

An approved brief and mockup for the team page.

## Depends on

02 (reuses its table and form chips)

## Steps

1. You write `design/team-brief.md` from the template. Starting points from the spec (section 2):
   - header with league, position, points and form chips (6 overall, 4 home, 4 away);
   - season record split overall/home/away;
   - position chart;
   - goals for and against;
   - Elo journey with division bands and up to 2 overlay teams;
   - "Add to compare".
2. Query real data for one team whose Elo journey crosses divisions, e.g. Leeds United from 2016/17.
3. Produce `design/team.html`.
4. You review it; revise until approved.

## Proof

- You approve `team.html`.
- Its numbers match the queried data.

## Outcome

Approved 2026-11-08, built on Premier League 2024/25 with Nottingham Forest as the default team.

The brief replaced three of the starting points:
- the season record table;
- "Add to compare";
- overlay teams.

In their place it added:
- cascading pickers;
- a date slider;
- a five-view chart panel, with home/away shown as table positions and result tooltips.

`04-team-page/spec.md` has the detail.

## Scope ledger

**Core**

- steps 1–4
