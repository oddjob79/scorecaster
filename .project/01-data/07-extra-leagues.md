# 07 Extra leagues

## Goal

Load the extra leagues (`new/*.csv`): results and closing 1X2 odds for every season in each file.

## Depends on

05, 06

## Format differences from the main leagues

- One file per league holding every season, with a `Season` column (`2024` for calendar-year leagues, `2012/2013` for others).
- Columns: `Country, League, Season, Date, Time, Home, Away, HG, AG, Res`, then closing 1X2 odds: `PSCH/PSCD/PSCA` (Pinnacle), `MaxCH...`, `AvgCH...`, `BFECH...` (Betfair Exchange).
- No half-time score, stats or over/under / Asian handicap odds.

## Steps

1. Add a second parser in `scorecaster/ingest/fdcuk.py` that maps these columns onto the same match and odds records as chunks 05–06.
2. Turn each `Season` value into a season label, start year and end year (`2024` → `2024`, 2024, 2024).
3. Reuse team resolution, match upsert and odds upsert from chunks 05–06, with all extra-league odds stored as `closing`.
4. Add the extra leagues to `scripts/load_data.py`.
5. **Ask the user before** running on one league (BRA), then before the full set.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–4
- step 5: runs, with permission

**Optional** (ticked = written)

- header check, type conversion and progress logging are shared with chunk 05
