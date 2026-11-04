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
