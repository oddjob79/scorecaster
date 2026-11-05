# 09 Port the feature builder

## Goal

Run the existing feature calculators across every loaded league on the new schema, with position bands and Elo that work for any league size, plus a season-phase column.

## Depends on

05, 05a (08 for upcoming-match rows)

## Steps

1. `MatchSource` (`scorecaster/features/builder.py`):
   - read `matches` with status `finished` or `scheduled`, ordered by `match_date`, id
   - derive season membership from the teams in each season's matches, replacing `SeasonTeam`
   - keep the previous season per competition, ordered by `start_year`
2. `FeatureBuilder._rows_for`: read `match_date` and `status`, and drop `matchday` from the row and from `CONTEXT_COLUMNS` in `scorecaster/features/schema.py`. co.uk has no matchday; `matches_played_season` covers it.
3. `MatchContext` and `LeagueState.apply_day` (`scorecaster/features/state.py`): use the new field names.
4. **Proportional position bands:** `PositionBands.band_of(position, league_size)` returns `ceil(position × band_count ÷ league_size)`. `FeatureConfig.position_bands` becomes `position_band_count = 5`. A 20-team league keeps 1–4, 5–8 … 17–20.
5. **Elo, as decided in chunk 05a:**
   - **pyramid Elo** for England, Scotland, Germany, Italy, Spain and France: one `EloRatings` per country covering every loaded division. A team keeps its rating when it moves division. Each division has an offset on the shared scale (the rating gap between adjacent tiers), estimated only from seasons before the one being rated, so backtests see no later outcomes.
   - **per-league Elo** for single-tier countries (N1, B1, P1, T1, G1) and the extra leagues: one `EloRatings` per competition
   - `new_season` runs once per pyramid- or league-season, which fixes the repeated-regression bug
   - **fallback** for a team with no rating (entering from a league that isn't loaded, or a league's first season): the average rating of the N lowest-rated teams in its new division, where N is the number of newcomers this season
   - **design (user, 2026-11-04): option B, convert on move.** Each division keeps its own 1500-centred Elo scale. A team that changes division brings its last rating, minus a learned `adjustment[boundary, direction]`:
     - the adjustment is the mean, over earlier movers on that boundary and direction, of (rating at the end of the old season) − (rating after the first 10 games in the new division)
     - expanding window: only seasons before the one being rated
     - until a boundary and direction has at least 5 earlier movers, the fallback applies: the average of the N lowest-rated (promoted) or N highest-rated (relegated) teams in the new division
     - a comparable country-wide number, if ever needed, is the division rating plus the adjustments up the pyramid
   - option A (one shared scale with tier anchors) was not chosen. It gives comparable ratings across divisions and handles cup matches, neither of which this plan uses, but it needs drift management.
6. **Remove relegation:** drop `points_above_relegation` from `TableCalculator` (`scorecaster/features/calculators.py`) and `relegation_places` from `FeatureConfig` (`scorecaster/config.py`).
7. **Season phase:** add `season_phase` (1–5) to `ExperienceCalculator`: `ceil(5 × game_number ÷ season_games)`, where `game_number` is this team's game number this season and `season_games` is the most games any team played in that league-season (the previous season's value for the season in progress). e.g. Premier League, 38 games: games 1–7 → 1, 8–15 → 2, 16–22 → 3, 23–30 → 4, 31–38 → 5.
8. **Ask the user before** running `scripts/adhoc/sample_feature_build.py` (a build of chosen leagues in an in-memory copy; default: the English pyramid), then `scripts/build_features.py --rebuild` on everything.

## Also in this chunk

- The feature package is split by job: `history.py`, `table.py`, `elo.py`, `pyramid.py`, `source.py`, `state.py`, `calculators.py`, `schema.py`, `builder.py`, all in the python-style skill.
- `FeatureBuilder.build()` and `rebuild()` replace `build(rebuild=...)`, and rows are written in batches of 20,000, since the full history is about 444,000 rows.
- Summer Elo regression pulls returning teams toward 1500, each division's centre, instead of toward the pool mean.

## Expected test failures

- `tests/test_features.py`: the fixtures use the old models, `PositionBands` takes a league size, `FeatureConfig(relegation_places=1)` no longer exists, and the expected feature columns change.

## Scope ledger

**Core**

- steps 1–3: builder and state on the new schema
- step 4: proportional bands
- step 5: Elo as chosen by 05a, which also fixes the repeated-regression bug
- step 6: remove relegation
- step 7: season phase
- step 8: runs, with permission

**Optional** (ticked = written)

- none raised
