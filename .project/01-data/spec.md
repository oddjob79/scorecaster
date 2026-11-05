# 01 Data: history, stats and odds from football-data.co.uk

## Goal

Load many seasons of results, match stats and bookmaker odds for every league football-data.co.uk covers into the SQLite database. football-data.co.uk is the only data source.

## Why

- The models need far more than 5 Premier League seasons to avoid fitting noise.
- Value can only be found and tested with odds: historical odds for backtesting, current odds for live use.
- Pinnacle's closing odds are the benchmark for phase 04.

## Source

- **football-data.co.uk**: free CSVs, one file per league per season, for example `mmz4281/2425/E0.csv` (Premier League 2024/25). The extra leagues come as one file per league holding every season, for example `new/BRA.csv`. `fixtures.csv` holds the coming week's matches with current odds.
- **Columns** (documented in the site's `notes.txt`):
  - result and half-time score
  - shots, shots on target, corners, fouls and cards
  - pre-match and closing odds from several bookmakers for 1X2, over/under 2.5 and Asian handicap, including Pinnacle
- The column set varies by season and league (closing odds start around 2019/20, older seasons carry fewer bookmakers). Extra leagues carry results and closing 1X2 odds only.
- All fetching runs from WSL; the site is blocked on Windows.

## Shape of the solution

- **Loader:** downloads each CSV once into the database (`downloads`) and parses it into records. A re-run makes no requests; `--refresh` re-downloads the season in progress and the fixtures.
- **Matches and stats:** one `matches` table with internal IDs, keyed by competition, date and teams. Stats are columns on `matches`.
- **Teams:** `teams` keyed by (country, name), with a hand-maintained `team_aliases` table for spelling changes.
- **Odds table (sport-neutral):** one row per match, bookmaker, market, selection, line and timing, for example `(match 123, Pinnacle, OU, over, 2.5, closing, 1.91)`. Timings are `pre_match` (co.uk's collection-time snapshot) and `closing`.
- **League config:** a pydantic-validated list of leagues with tier and file style.
- **Feature builder:** ported to the new schema, with proportional position bands and a season-phase column. Elo newcomers are rated from a promotion and relegation analysis.

## Decisions

- football-data.co.uk is the only source. The football-data.org code is deleted. Paid sources (live odds, Betfair, API-Football) are considered at phase 06, or earlier if a phase 02/03 learning curve is still rising at full data.
- SQLite stays as the database.
- Leagues: all 22 main leagues from 2005/06, plus every extra league.
- Upcoming fixtures come from co.uk's fixtures files.
- The feature calculators run unchanged. Builder and state are ported in this phase.
- Position bands are proportional fifths of each league's table: `ceil(position × 5 ÷ league size)`.
- Elo: pyramid Elo (one scale per country, division offsets) for England, Scotland, Germany, Italy, Spain and France; per-league elsewhere. Chosen from chunk 05a's analysis, where promoted teams struggle more the higher the tier, with a wide spread between individual teams. Offsets use only earlier seasons.
- `points_above_relegation` and `relegation_places` are removed. The Elo fallback counts newcomers from the data.
- `season_phase` (1–5, fifths of each team's season) goes into the feature table. Chunk 09a measures whether results are skewed or less predictable by phase.
- Motivation metrics (promotion and European races, games remaining, deductions, split leagues, manager changes) are out of scope. The existing table features are ported unchanged, and phase 03 decides whether they stay. Season-phase uncertainty (first and last games of a season) is measured and handled as a calibration question, not modelled as motivation.
- Validation: header check and pandas type conversion for the CSVs, pydantic for the league config.

## Chunks

| # | Chunk |
|---|---|
| 01 | [Remove the football-data.org code](01-remove-football-data-org.md) |
| 02 | [Schema](02-schema.md) |
| 03 | [League config](03-league-config.md) |
| 04 | [CSV download cache](04-csv-download-cache.md) |
| 05 | [Main-league results and stats](05-main-league-results.md) |
| 05a | [Promotion and relegation analysis](05a-promotion-relegation-analysis.md) |
| 06 | [Odds](06-odds.md) |
| 07 | [Extra leagues](07-extra-leagues.md) |
| 08 | [Fixtures](08-fixtures.md) |
| 09 | [Port the feature builder](09-port-feature-builder.md) |
| 09a | [Season-phase analysis](09a-season-phase-analysis.md) |
| 10 | [New feature calculators](10-new-feature-calculators.md) |
| 11 | [Data-quality report](11-data-quality-report.md) |
| 11a | [Tests](11a-tests.md) |
| 12 | [Docs](12-docs.md) |

## Scope ledger

**Core**

- [x] remove the football-data.org code (01)
- [x] schema: competitions, seasons, teams, team aliases, matches with stats, downloads, odds (02)
- [x] league and season config (03)
- [x] CSV loader with download cache (04)
- [x] matches and stats loaded for the configured leagues and seasons (05, 07)
- [x] sport-neutral odds table: 1X2, over/under 2.5 and Asian handicap, pre-match and closing (06, 07)
- [x] upcoming fixtures (08)
- [x] promotion and relegation analysis deciding Elo scope (05a): pyramid Elo chosen
- [x] feature builder ported, with proportional bands, pyramid Elo and season phase (09)
- [x] season-phase analysis (09a)

**Optional**

- [x] `--refresh` for the season in progress and fixtures (04)
- [x] polite delay between downloads, reusing `RateLimiter` (01, 04)
- [x] progress logging (04, 05)
- [x] header check and pandas type conversion (05)
- [x] pydantic league config (03)
- [x] shot, card and odds-derived feature calculators (10)
- [x] data-quality report (11)
- [x] fuzzy team-name hints in the report, confirmed by hand (11)
- [x] extra leagues with closing odds only (07)
- [x] readme and changes update (12)
- [x] test suite: pure-function, contract, data-safety and decision tests (11a)
- [x] tripwires: Elo division check, schema drift check, calculator key check (11a)
- [x] 05a extras: spread, previous-finish split, era split
- [ ] 05a charts (needs matplotlib)
- [ ] Understat xG scraper (later phase, new loader)
