# 08 Fixtures

## Goal

Load upcoming matches and their current odds from football-data.co.uk's fixtures files, so the feature builder and later phases can see next week's games.

## Depends on

05, 06, 07

## The two files

- `fixtures.csv`: main leagues, all in one file. Each row's `Div` is the league code. It has the same columns as the season files, with the closing columns empty.
- `new_league_fixtures.csv`: extra leagues. Columns are `Country, League, Date, Time, Home, Away`, then **pre-match** 1X2 odds (`PS*`, `Max*`, `Avg*`, `BFE*`, `B365*`). There's no `Season` or league code. These are the only pre-match odds for extra leagues; their season files carry closing odds only.

## Trap: fixtures repeat recent matches

The files include matches from the last day or two, which may already be loaded with a result. An upsert of those rows would replace the score with empties and set the status back to `scheduled`. `SeasonWriter.without_finished` drops rows whose match is already stored as `finished` before anything is written.

## Steps

1. `LeagueConfig.calendar_year` (`scorecaster/leagues.py`) marks the leagues that run January–December: ARG, BRA, FIN, IRL, NOR, SWE, USA.
2. `FIXTURES_URLS` (`scorecaster/ingest/fdcuk/files.py`) lists both files.
3. `FixturesLoader` (`scorecaster/ingest/fdcuk/fixtures.py`):
   - reads a file with the shared `read_results`
   - maps each row to a league: `Div` for main leagues, `Country` for extra leagues; rows in leagues that aren't configured are counted and skipped
   - assigns a season from the fixture date and the league's style (`season_for`): calendar year → the date's year, August–May → the season started by that date
   - writes each league-season through `SeasonWriter` with unplayed status `scheduled`, after dropping already-finished matches; odds are stored as `pre_match`
4. `scripts/load_data.py` loads both fixtures files after the season files on an unfiltered run, or on their own with `--fixtures-only`. With `--refresh`, both are re-downloaded first.
5. **Ask the user before** the first fixtures load. Check the scheduled rows and their odds against the files.

## Known gap

A postponed fixture keeps its original date. When the match is played on a new date, the results file adds a second row with that date, and the old row stays `scheduled`. The data-quality report (chunk 11) lists `scheduled` matches dated in the past.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–4
- step 5: run, with permission

**Optional** (ticked = written)

- none raised
