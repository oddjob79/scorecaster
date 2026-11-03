# 05 Main-league results and stats

## Goal

Parse the cached main-league CSVs into `seasons`, `teams` and `matches` (scores and stats).

## Depends on

04

## Steps

1. In `scorecaster/ingest/fdcuk.py`, read a cached body into a DataFrame (`results_df`):
   - decode as UTF-8 with BOM, falling back to cp1252
   - drop blank trailing rows and unnamed empty columns
   - trim empty fields beyond the header width (e.g. SP2 2007/08 rows ending `,,,`), and log and skip rows whose extra fields hold data
   - parse `Date` in both `dd/mm/yy` (older seasons) and `dd/mm/yyyy`
2. Check the header: list the result and stats columns each file lacks in its progress line. Unknown columns are reported in chunk 06, once the odds column map exists; until then every odds column would show up as unknown.
3. Convert numeric columns with pandas, and log the values that fail to convert (league, season, row, column, value).
4. Upsert the season (`2024/25`, start 2024, end 2025).
5. Resolve each team name: look in `team_aliases` for (country, name), then `teams`, otherwise insert a new team.
6. Upsert matches on (competition, date, home, away) with status `finished`, full-time and half-time score and result, referee, kick-off time where present, and stats columns where present.
7. Log one line per file: league, season, rows loaded.
8. Add `scripts/load_data.py`, which runs the download cache and then this parser for the whole config:
   - `--refresh` re-downloads the live files (`CsvFile.is_live`)
   - `--league` and `--season` narrow the run, e.g. `--league E0 --season 2024`
   - a 404 for the season in progress is logged and skipped, because the site publishes a new season's file a few weeks into it. A 404 for any other season stops the run.
9. **Ask the user before** running on E0 2024/25. Read the loaded rows back and compare them with the CSV.
10. **Ask the user before** running the full config.

## Column map (from `notes.txt`)

`Div, Date, Time, HomeTeam, AwayTeam, FTHG, FTAG, FTR, HTHG, HTAG, HTR, Referee, HS, AS, HST, AST, HF, AF, HC, AC, HY, AY, HR, AR`. Some older files use `HG`/`AG`/`Res` for the full-time columns.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1, 4–6, 8: parse, resolve teams, upsert seasons and matches, load script
- steps 9–10: runs, with permission

**Optional** (ticked = written)

- [x] step 2: header check
- [x] step 3: pandas type conversion with failed-value report
- [x] step 7: progress logging
