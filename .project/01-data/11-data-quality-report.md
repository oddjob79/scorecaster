# 11 Data-quality report

## Goal

List what is wrong or missing in the loaded data, so team aliases and gaps get fixed by hand.

## Depends on

05–08

## Steps

1. Add `scripts/data_quality.py`, read-only, printing one section per check:
   - **split teams:** teams whose matches start or stop in the middle of a season, and teams that appear for one season only
   - **fuzzy alias hints:** for each split team, the most similar team names in the same country (stdlib `difflib`), for the user to confirm and add to `team_aliases` by hand. Never merged automatically.
   - **stale fixtures:** matches still `scheduled` with a date in the past (postponed fixtures whose result was loaded under a new date)
   - **season style:** extra leagues whose latest stored season label doesn't match `LeagueConfig.calendar_year` (a league has switched calendars)
   - **missing odds:** finished matches per league-season with no Pinnacle closing 1X2, or no odds at all
   - **duplicate matches:** the same two teams on the same date in more than one competition
   - **unconverted values:** a count of the values chunk 05 logged as failing to convert
2. **Ask the user before** running it.

## Expected test failures

None new.

## Scope ledger

**Core**

- step 1: split teams, stale fixtures, season style, missing odds, duplicate matches, unconverted values
- step 2: run, with permission

**Optional** (ticked = written)

- [x] fuzzy alias hints

## Refinements after the first run (2026-11-05)

- Mid-season checks compare each team with its season's **median** first and last match, so playoff rounds don't stretch the season and flag every team.
- Teams with **4 or fewer** games in a season go in a separate **playoff-only appearances** section.
- Stale fixtures are flagged only **more than 7 days** after their date.
- Unconverted-value warnings print once, inside their section.

## Result (2026-11-05)

First run findings:
- **Spelling splits merged** with `scripts/adhoc/merge_teams.py` (matches re-pointed, alias added, variant team deleted, features rebuilt): Colon Santa FE → Colon Santa Fe, Ham-Kam → HamKam, Gornik Z. → Gornik Zabrze, Din. Bucuresti → Dinamo Bucuresti, U Craiova → Univ. Craiova (U Craiova 1948 is a different club), Osters → Oster (Östersunds FK is a different club), Leonesa → Cultural Leonesa, Telford United → AFC Telford United.
- **Extra-league files include promotion and relegation playoff ties** against lower-division teams (e.g. Dinamo Bucuresti v FC Argeș 2023, Ull/Kisa in Norway 2012). They count as league matches in tables and Elo.
- **Pinnacle closing odds stop partway through 2025/26** (45–77% missing per league that season), and never covered SC2/SC3 in 2012/13–2015/16.
- The 14 "stale" fixtures were the 3 Nov round, awaiting a `--refresh`.
- No duplicate matches. The 14 unconverted values are the known ones.
