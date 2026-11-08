# 04 Matches page

## Goal

An approved brief and mockup for the Matches page: each day's results and fixtures across the chosen competitions, with details for every match.

## Depends on

02, 03 (reuses the form chips, positions and style)

## Steps

1. You write `design/calendar-brief.md` from the template.
2. Query real data for the 20 competitions around one date, e.g. 2024/25 up to 9 Feb 2025, with match details for the fortnight around it.
3. Produce `design/matches.html`.
4. You review it; revise until approved.

## Proof

- You approve `matches.html`.
- Its results match the queried data.

## Outcome

Approved 2026-11-08. The mockup treats Sat 1 Feb 2025 as "today", with fixtures running to Tue 4 Feb.

- **Name:** the page is called Matches, not Calendar.
- **Day strip:** seven days with no match counts, plus a month grid. It stops at the last day with fixtures, and a line under the strip says so.
- **Competition filter:** checkboxes per competition and per country; it opens on the top divisions.
- **Match rows:** expand as an accordion. Every row starts collapsed, on first load and on each change of day.
- **Result details:**
  - half-time score, kick-off and referee;
  - positions before and after the match;
  - mirrored match-stat bars;
  - a table of pre-match and closing odds, with the outcomes that happened highlighted.
- **Fixture details:**
  - the two teams side by side with "vs", lined up under the teams in the row;
  - pre-match odds in three equal columns (home, draw, away);
  - an overlaid season chart: position, home/away, form, goals.
- **Style:** `series-2` added to `style.md` for the second team.

## Scope ledger

**Core**

- steps 1–4
