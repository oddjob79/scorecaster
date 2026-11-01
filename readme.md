# Scorecaster

A local SQLite store of football results from the [football-data.org v4 API](https://docs.football-data.org/general/v4/index.html), plus a table of **pre-match team features** for finding out which factors drive a match result and total goals.

The scope is the Premier League, over the last 3–5 seasons, using team data only.

## Quick start

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/create_db.py                              # one-off: creates data/scorecaster.db and the raw tables
.venv/bin/python scripts/load_data.py --seasons 2021 2022 2023 2024 2025
.venv/bin/python scripts/build_features.py                         # builds / updates team_match_features
.venv/bin/python scripts/export_dataset.py data/matches.csv        # modelling dataset (finished matches)
.venv/bin/python scripts/export_dataset.py data/upcoming.csv --upcoming
.venv/bin/python -m pytest -q
```

To keep things up to date as the season goes on:

```bash
.venv/bin/python scripts/load_data.py --seasons 2025 --refresh && .venv/bin/python scripts/build_features.py
```

Settings are read from `.env` or the environment:

| Variable | Default |
|---|---|
| `FOOTBALL_DATA_KEY` | required for `load_data.py` |
| `SCORECASTER_DB_PATH` | `data/scorecaster.db` |
| `SCORECASTER_COMPETITION` | `PL` |
| `FOOTBALL_DATA_RPM` | `10` (free-tier limit) |

Feature settings such as windows, bands and Elo parameters are in `FeatureConfig` in `scorecaster/config.py`.

## What's been built

```
scorecaster/
  config.py             Settings (env) and FeatureConfig (feature parameters)
  db/                   SQLAlchemy models and the Database (engine + sessions, schema created without dropping anything)
  api/
    base.py             JsonClient and FootballDataProvider abstractions
    http.py             RateLimiter, HttpJsonClient (retries on 429), CachedJsonClient (stores responses in the DB)
    football_data.py    FootballDataParser (JSON -> records), FootballDataOrgProvider
  ingest/
    records.py          Records that don't depend on the provider (the boundary between the API and the DB)
    repository.py       RawDataRepository: insert-only; the only updates are to matches that aren't finished yet
    loader.py           HistoricalLoader: competition -> seasons -> teams and matches
  features/
    state.py            LeagueState: team histories, rebuilt league tables, Elo, position bands
    calculators.py      One FeatureCalculator class per feature group
    schema.py           Wide feature table and views, generated from the calculators' columns
    builder.py          FeatureBuilder: replays matches in date order and writes rows incrementally
  analysis/dataset.py   DatasetLoader: loads the views into pandas
scripts/                create_db, load_data, build_features, export_dataset
tests/                  Offline tests using hand-made v4-shaped JSON fixtures
```

### Design notes

- **Raw data is never overwritten.** `create_db` only creates tables that are missing. The repository skips rows that already exist. The one exception is a match that isn't `FINISHED` yet: it's updated until its result arrives, and then it's frozen.
- **API responses are cached.** Every response is stored in `api_responses`. A re-run is served from the cache, so it makes no requests, and only seasons that are still in progress are re-requested when you pass `--refresh`. A full 5-season load needs about 11 requests.
- **No future data leaks into features.** The builder replays matches grouped by calendar day. It computes features for every match on a day before applying any of that day's results. Positions are rebuilt from results, because the API's standings endpoint only returns the current table.
- **The feature table is derived and can be rebuilt.** `build_features.py` adds new matches and refreshes rows computed before the result was known, which includes upcoming fixtures. If you add or change a calculator, run `--rebuild` to regenerate the table.
- **SOLID in practice:**
  - Adding a feature means adding a `FeatureCalculator`; the builder doesn't change.
  - The loader depends on `FootballDataProvider`, so an api-football provider can be added later (for odds, for example) without touching storage.
  - Caching is a decorator around `JsonClient`.

## Database

**Raw tables:** `areas`, `competitions`, `seasons`, `teams`, `season_teams`, `matches` (full-time and half-time score, status, referee), `api_responses`.

**`team_match_features`** has one row per team per match, so two rows per match. Each row holds:

- **Keys and context:** `match_id`, `team_id`, `opponent_id`, `season_id`, `match_date`, `matchday`, `is_home`, `is_finished`.
- **Targets:** `goals_for`, `goals_against`, `result_pts`. These are NULL for upcoming fixtures.
- **Features:** about 150 numeric columns, all known before kick-off. A feature is NULL when there isn't enough history; for example, `form_8_*` needs 8 prior games.

| Group | Columns (N = window) |
|---|---|
| Experience | `matches_played_total`, `matches_played_season`, `rest_days` |
| Previous result | `prev_pts`, `prev_gf`, `prev_ga`, `prev_home_pts`, `prev_away_pts` |
| Form | `form_N_{pts,wins,draws,losses}` for N = 4, 6, 8, plus `home_form_N_*` and `away_form_N_*` |
| Goals | `goals_N_{gf,ga,clean_sheets,failed_to_score,btts,over25}` for N = 4, 6, 8, 10, 20, plus home and away versions for 4, 6, 8 |
| Streaks | `streak_{wins,unbeaten,winless,losses,scoring,clean_sheets}` |
| Season to date | `season_{pts,ppg,gf_pg,ga_pg,gd,home_ppg,away_ppg}` |
| Table | `league_position`, `position_band` (1–4, 5–8, 9–12, 13–16, 17–20), `points_to_top`, `points_above_relegation`, `prev_season_position` |
| Strength | `elo`, `elo_expected`, `attack_strength`, `defence_strength` (compared with the league average) |
| Head to head | `h2h_*` over the last 6 meetings, and `h2h_venue_*` over the last 3 at the same venue |
| Similar opponents | `opponent_band`, `vs_band_{played,ppg,gf_pg,ga_pg}`: record against teams that were in the opponent's current band at the time they were played |

**Views:**

- `v_team_match_features` is each team row plus the opponent's features, prefixed `opp_`.
- `v_match_features` is one row per match, with `home_*` and `away_*` features and the targets `result` (H/D/A), `total_goals`, `over_2_5` and `btts`. Use this one for modelling.

**Form across seasons.** Rolling form carries over from last season. Season-to-date columns and `matches_played_season` show where a new season starts. Before a team's first game of the season, its band comes from last season's finishing position; promoted teams get the bottom band. Elo regresses 20% towards the mean between seasons, and newcomers start at the average rating of the lowest-rated teams.

### Factors included, and factors left out

**Included because they're known to matter:**

- Team strength ratings (Elo), which are usually the strongest single signal after bookmaker odds.
- Home advantage.
- Goal-based attack and defence strength, which is the basis of Poisson models.
- League position and points gaps, which reflect motivation near the top and bottom.
- Rest days.

**Kept for now, but expected to be weak:**

- Head to head. Samples are small, and team strength usually explains it better.
- Streaks, which are largely captured by form.

**Left out:**

- Day of week and kick-off time.
- Weather.
- Attendance.
- Referee: it's stored in `matches` but not used as a feature.
- All-time head-to-head beyond the last 6 meetings.

**Not available from the free API, but worth adding later:**

- Bookmaker odds. These are the best benchmark and a strong feature; api-football offers them.
- xG.
- Cup and European fixtures, which would make `rest_days` accurate.

## Finding the most influential factors

"Regression analysis" is the right term. Useful techniques, from simplest to more advanced:

1. **Multinomial or ordinal logistic regression** for H/D/A, and **Poisson or negative binomial regression** for goals (`statsmodels`). Their coefficients and p-values are easy to interpret.
2. **Regularised regression** (LASSO, elastic net). This is the practical way to select features from about 300 columns that are highly correlated with each other (for example, `form_4` and `form_6`). LASSO drops weak features to zero.
3. **Dixon-Coles / bivariate Poisson.** This is the standard model for football scores. It estimates attack, defence and home strengths and gives probabilities for results and over/under.
4. **Gradient-boosted trees** (LightGBM, XGBoost) or random forests, combined with **permutation importance** or **SHAP values**. These capture non-linear effects and interactions and rank the features.
5. **Screening:** correlation, mutual information, and checking the variance inflation factor (VIF) to remove redundant features before modelling.
6. **Bayesian hierarchical models** (PyMC), which share strength across teams and seasons.

How to evaluate:

- Always split by time: train on earlier seasons and test on later ones. Never shuffle.
- Score models with log-loss, the Brier score or the ranked probability score (RPS), not just accuracy.
- Benchmark against "always home" and against Elo on its own.

## Other ways to structure this

- **Compute features on the fly** with SQL window functions or pandas `groupby().rolling().shift(1)` instead of storing them. There's nothing to keep in sync, but it's harder to get position-at-the-time and similar-opponent features right. The current table can be treated as a cache that can always be regenerated.
- **Long (EAV) feature store** with columns `match_id, team_id, feature, value`. Adding a feature needs no schema change, but pivoting before modelling is awkward. The wide table plus `--rebuild` gives most of that flexibility.
- **Raw JSON as the source of truth**, with re-parsing into tables. This is partly in place already through `api_responses`.
- **DuckDB or Parquet** instead of SQLite, for faster analytical queries once there are several leagues and many seasons. For one league, SQLite is fine.

## Known limitations and next steps

- The parsers follow the published v4 schema and have only been tested against hand-made fixtures. Check them on your first real run. If older seasons return 403, your plan doesn't include them.
- Only the configured competition is loaded, so `rest_days` ignores cup and European games, and promoted teams have no history from their previous league. Adding the Championship (`ELC`) would fix the second point.
- Next steps:
  - Write an analysis notebook: a baseline logistic regression and a Poisson model, a LASSO feature ranking, and SHAP on a gradient-boosted model.
  - Add an api-football provider for odds, which needs a mapping between the two APIs' team IDs.
