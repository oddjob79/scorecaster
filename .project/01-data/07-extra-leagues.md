# 07 Extra leagues

## Goal

Load the extra leagues (`new/*.csv`): results and closing 1X2 odds for every season in each file.

## Depends on

05, 06

## Format differences from the main leagues

- One file per league holding every season, with a `Season` column (`2024` for calendar-year leagues, `2012/2013` for others).
- Columns: `Country, League, Season, Date, Time, Home, Away, HG, AG, Res`, then closing 1X2 odds, e.g. `PSCH/PSCD/PSCA` (Pinnacle), `MaxCH…`, `AvgCH…`, `BFECH…` (Betfair Exchange).
- No half-time score, stats or over/under / Asian handicap odds.

## Steps

1. `read_results` renames `Home`/`Away` to `HomeTeam`/`AwayTeam` (with the existing `HG`/`AG`/`Res` renames), so both file styles parse into the same columns.
2. `SeasonSpan.parse` (`scorecaster/ingest/fdcuk/seasons.py`) turns a `Season` value into a label, start and end: `2024` → (`2024`, 2024, 2024), `2012/2013` → (`2012/13`, 2012, 2013).
3. `CsvLoader` (`scorecaster/ingest/fdcuk/loader.py`) loads a per-season file as one season, and an all-seasons file grouped by `Season`. Each season shares the same team, match and odds upserts. The odds columns carry `C`, so the existing pattern stores them as `closing`.
4. Current season, for unscored matches: a calendar-year season is current when it matches this calendar year; an August–May season is current when it starts in `current_season_start()`.
5. `scripts/load_data.py` includes the extra leagues. `--season` narrows to per-season files only, so it skips the all-seasons files.
6. **Ask the user before** running on one league (BRA), then before the full set.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–5
- step 6: runs, with permission

**Optional** (ticked = written)

- header check, type conversion and progress logging are shared with chunk 05
