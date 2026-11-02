# 09 Port the feature builder

## Goal

Run the existing feature calculators across every loaded league on the new schema, with position bands and Elo that work for any league size.

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
   - top tiers, and divisions fed from leagues that aren't loaded, use the lowest-rated-teams rule when no value exists
6. **Relegation places per league-season:**
   - derive from the data: teams in tier *t* in season *s* that are absent from tiers ≤ *t* in season *s+1*
   - fall back to the competition's config value for the season in progress
   - use the result in `TableCalculator.points_above_relegation` and in Elo newcomer ratings, replacing `FeatureConfig.relegation_places`
7. **Ask the user before** running `scripts/build_features.py` on E0, then on everything.

## Expected test failures

- `tests/test_features.py`: the fixtures use the old models, and `PositionBands` takes a league size.

## Scope ledger

**Core**

- steps 1–3: builder and state on the new schema
- step 4: proportional bands
- step 5: Elo as chosen by 05a, which also fixes the repeated-regression bug
- relegation places from the competition config
- step 7: runs, with permission

**Optional** (ticked = written)

- [x] step 6: relegation places derived per league-season from the data