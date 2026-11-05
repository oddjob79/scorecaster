# Scorecaster

A local SQLite store of football results, match stats and bookmaker odds from [football-data.co.uk](https://www.football-data.co.uk), plus a table of **pre-match team features** for modelling results and goals.

It covers 22 main European leagues from 2005/06 and 14 extra leagues (Americas, Scandinavia, Japan and others) from about 2012, roughly 222,000 matches and 6 million prices. Terms used below are defined in the [glossary](docs/glossary.md). Each phase's plan and decisions are in `.project/`.

## Quick start

The project uses a pyenv virtualenv called `scorecaster`, activated inside the repo by `.python-version`.

```bash
pyenv virtualenv 3.13.12 scorecaster          # once per machine
pip install -r requirements.txt
python scripts/create_db.py                   # create tables, sync the league list
python scripts/load_data.py                   # download (once) and load every file, then the fixtures
python scripts/build_features.py --rebuild    # build team_match_features from scratch
python scripts/data_quality.py                # report what is wrong or missing
python -m pytest -q                           # run the tests
```

`load_data.py` narrows with `--league E0` and `--season 2024` (both repeatable; `--season` skips the extra-league files). The first full load downloads about 500 files at one every 2 seconds, roughly 17 minutes.

### Weekly update

```bash
python scripts/load_data.py --refresh         # re-download the live files, load the changes and fixtures
python scripts/build_features.py              # add new matches, refresh scheduled ones
```

`python scripts/load_data.py --fixtures-only --refresh` updates just the coming round.

### Exporting the modelling dataset

`python scripts/export_dataset.py data/matches.csv` writes the `v_match_features` view to CSV: one row per finished match, with every feature for both sides (`home_*`, `away_*`) and the targets `result`, `total_goals`, `over_2_5` and `btts`. It's the table models train on, as a file for notebooks or other tools. `--upcoming` writes the scheduled fixtures instead (the rows to predict); `--per-team` writes two rows per match with the opponent's features as `opp_*`.

### Settings

`.env` or the environment may set `SCORECASTER_DB_PATH` (default `data/scorecaster.db`). Feature parameters (form windows, band count, Elo constants) are in `FeatureConfig` in `scorecaster/config.py`; the league list is `LEAGUES` in `scorecaster/leagues.py`.

## How downloads and the cache work

- **Storage.** The `downloads` table has one row per URL: `url` (unique), `body` (the raw response bytes) and `fetched_at`.
- **`DownloadCache.get(url)`** (`scorecaster/ingest/download.py`) selects the row for that URL. If it exists, the stored bytes are returned and no request is made (logged `cached`). If not, it calls `refresh`.
- **`DownloadCache.refresh(url)`** waits on the rate limiter, sends the HTTP request, stores or replaces the row, and returns the bytes (logged `fetched`).
- **Loading reads only stored bytes.** `CsvLoader` parses the bytes `get` returns and upserts seasons, teams, matches and odds. Re-running a load, or re-parsing everything after a parser fix, makes no requests: the site sees each historical file requested once.
- **Live files** are the ones that can still change: the current season's per-season files, every all-seasons extra-league file (they include the current season) and the two fixtures files. `--refresh` calls `refresh` for those and `get` for everything else.
- **Rate limit.** At most one request every 2 seconds (`SECONDS_BETWEEN_FETCHES`). The site is free and run by one person; a first full load spaced this way takes about 17 minutes instead of hammering it.
- **Upserts.** Every table write is an insert-or-update on the table's natural key (e.g. matches on competition, date, home and away), so loading the same file again changes nothing.

Worked example:

| Run | Requests | What happens |
|---|---|---|
| First `load_data.py` | ~500 | every file fetched and stored, then parsed |
| Second `load_data.py` | 0 | every file read from `downloads` and re-parsed; rows updated in place |
| Weekly `load_data.py --refresh` | ~38 | the live files re-fetched; new results and fixtures upserted |

## Layout

```
scorecaster/
  config.py            Settings (.env) and FeatureConfig
  leagues.py           LeagueConfig, LEAGUES, current_season_start
  db/                  models, Database (engine, sessions, schema checks), upsert
  ingest/
    download.py        RateLimiter, DownloadCache
    fdcuk/             football-data.co.uk: files, columns, reader, seasons, odds, loader, fixtures
  features/            history, table, elo, pyramid, source, state, market, calculators, schema, builder
  analysis/dataset.py  DatasetLoader: the feature views as DataFrames
scripts/               create_db, load_data, build_features, export_dataset, data_quality
scripts/adhoc/         one-task scripts: fetch_files, show_cached_file, check_fixtures,
                       merge_teams, sample_feature_build, promotion_analysis,
                       season_phase_analysis, playoff_analysis
tests/                 pytest suite with small hand-written CSV fixtures
docs/glossary.md       terms and decisions
```

## Database

| Table | One row per | Notes |
|---|---|---|
| `competitions` | league | code (`E0`, `BRA`), country, name, tier; synced from `LEAGUES` |
| `seasons` | league-season | label `2024/25` or `2024`, start and end year |
| `teams` | team | unique by country and name |
| `team_aliases` | alternative spelling | maps a variant name to its team at load time |
| `matches` | match | date, kick-off, status (`finished`, `scheduled`, `void`), scores, results, referee, shots, shots on target, fouls, corners, cards |
| `downloads` | URL | raw file bytes, see above |
| `odds` | price | match, bookmaker, market, selection, line, timing, price |
| `team_match_features` | team per match | derived; rebuilt by `build_features.py` |

**Odds.** Five sources are stored: `pinnacle`, `market_avg`, `market_max`, `bet365` and `betfair_exchange`, for 1X2, over/under 2.5 and Asian handicap. `timing` is `pre_match` (the site's snapshot before the round, usually Friday or Tuesday) or `closing` (just before kick-off; from 2019/20, Pinnacle from 2012/13). `line` is 0 for 1X2, 2.5 for over/under and the handicap for Asian handicap. Extra leagues carry closing 1X2 odds only, plus pre-match odds in their fixtures.

**Match status.** A match without a score is `scheduled` in the season in progress and `void` in any earlier season (never played).

## Feature table

`team_match_features` has two rows per match (one per team), 200 columns: keys and context, targets (`goals_for`, `goals_against`, `result_pts`, empty for fixtures), and the features below. Every feature uses only what was known before kick-off; see *leakage* in the glossary.

| Group | Columns (N = window) |
|---|---|
| Experience | `matches_played_total`, `matches_played_season`, `rest_days`, `season_phase` |
| Previous result | `prev_pts`, `prev_gf`, `prev_ga`, `prev_home_pts`, `prev_away_pts` |
| Form | `form_N_{pts,wins,draws,losses}` for N = 4, 6, 8, plus `home_form_N_*` and `away_form_N_*` |
| Goals | `goals_N_{gf,ga,clean_sheets,failed_to_score,btts,over25}` for N = 4, 6, 8, 10, 20, plus home and away for 4, 6, 8 |
| Streaks | `streak_{wins,unbeaten,winless,losses,scoring,clean_sheets}` |
| Season to date | `season_{pts,ppg,gf_pg,ga_pg,gd,home_ppg,away_ppg}` |
| Table | `league_position`, `position_band`, `points_to_top`, `prev_season_position` |
| Strength | `elo`, `elo_expected` (pyramid Elo), `attack_strength`, `defence_strength` |
| Head to head | `h2h_*` over the last 6 meetings, `h2h_venue_*` over the last 3 at this venue |
| Similar opponents | `opponent_band`, `vs_band_{played,ppg,gf_pg,ga_pg}` |
| Match stats | `stats_N_{shots,shots_on_target,corners,fouls,yellows,reds}_{for,against}_pg` for N = 4, 6, 8 |
| Market | `market_{win,draw,loss,over25}_prob`, from market-average pre-match odds, margin removed |

Views: `v_team_match_features` adds the opponent's features as `opp_*`; `v_match_features` has one row per match with `home_*` and `away_*` features and the targets `result`, `total_goals`, `over_2_5` and `btts`.

## Data quality

`scripts/data_quality.py` (read-only) reports teams that start or stop mid-season or appear once (with alias hints), playoff-only appearances, fixtures still scheduled a week after their date, extra leagues whose calendar doesn't match `LEAGUES`, league-seasons missing odds, duplicate matches, and values in the cached files that failed to parse. Confirmed spelling splits are merged with `scripts/adhoc/merge_teams.py`, which moves the matches, records the alias and deletes the variant team; rebuild the features afterwards.

## Tests

`python -m pytest -q` runs the suite in about a second, entirely in memory. There are four kinds of test:

- **Pure functions:** CSV quirks, dates, odds columns and lines, seasons, the league config.
- **Contracts over the registries:** every calculator returns exactly its columns, handles a first match, and never sees its own match's result; every table has a natural key; reloading changes nothing. New calculators, tables and leagues are checked automatically.
- **Data safety:** void and scheduled status, the fixtures guard, the download cache, the 404 rule, and three tripwires: pyramid Elo rejects a team from another division, `create_db.py` stops when model and table columns differ, and the builder stops when a calculator returns the wrong keys.
- **Decisions** (`test_decision_*.py`): the Elo formula, pyramid Elo design B, proportional bands, season phase and unplayed status. These fail when a decision is changed, and are updated with it.

## Known limitations

- **Fixtures cover the next round only.** The site's fixtures files are a rolling window of a few days, not the season's schedule.
- **Pinnacle stops partway through 2025/26.** Later seasons need another benchmark (Betfair Exchange closing, then market average).
- **Playoff matches count as league matches.** Extra-league files include promotion and relegation ties against lower-division teams (181 matches), and MLS and Liga MX files include their post-season (258). Together that is 0.2% of matches, and the market prices them about as well as other matches (`scripts/adhoc/playoff_analysis.py`, 2026-11-05). Phase 02 leaves them out of training and evaluation.
- **Match stats** start in 2017/18 in most second tiers and smaller leagues; the extra leagues have none.
- **xG** (`HxG`/`AxG`) appears in 2026/27 files only and isn't stored.
- **Schema changes** to tables that already hold data need a migration; `create_db.py` reports the differences and stops.
