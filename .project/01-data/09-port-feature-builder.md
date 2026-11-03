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
5. **Elo newcomer ratings, as chunk 05a's conclusion decides:**
   - **per-league:** one `EloRatings` per competition. `new_season` runs once per league-season, and newcomers are seeded from 05a's values per (boundary, direction, previous finish)
   - **pyramid:** one `EloRatings` per country pyramid. Teams carry their rating across divisions, and division offsets come from 05a's values per boundary. Extra leagues stay one scale per league.
   - both variants: seeds or offsets are estimated only from seasons before the one being rated (expanding window), so backtests see no later outcomes
   - fallback, used when no 05a value exists (top tiers, divisions fed from leagues that aren't loaded): newcomers get the average rating of the N lowest-rated teams, where N is the number of newcomers this season (teams in the league this season that weren't in it last season)
6. **Remove relegation:** drop `points_above_relegation` from `TableCalculator` (`scorecaster/features/calculators.py`) and `relegation_places` from `FeatureConfig` (`scorecaster/config.py`).
7. **Season phase:** add `season_phase` (1–5) to `ExperienceCalculator`: `ceil(5 × game_number ÷ season_games)`, where `game_number` is this team's game number this season and `season_games` is the most games any team played in that league-season (the previous season's value for the season in progress). e.g. Premier League, 38 games: games 1–7 → 1, 8–15 → 2, 16–22 → 3, 23–30 → 4, 31–38 → 5.
8. **Ask the user before** running `scripts/build_features.py` on E0, then on everything.

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
