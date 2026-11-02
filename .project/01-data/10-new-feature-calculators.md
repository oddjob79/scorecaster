# 10 New feature calculators

## Goal

Add shot, card and odds-derived columns to the feature table for phase 03.

## Depends on

06, 09

## Steps

1. **Stats calculator** in `scorecaster/features/calculators.py`: per team over the existing form windows, the averages for and against of shots, shots on target, corners, fouls, yellows and reds. Empty when the window has no stats (extra leagues, missing seasons).
2. Add the stats columns to `TeamMatchRecord` and `LeagueState.apply_day` (`scorecaster/features/state.py`).
3. **Odds calculator:** implied probabilities for 1X2 and over/under 2.5 from `pre_match` odds, with the bookmaker margin removed (each price's 1/odds divided by their sum).
4. Register both in `default_calculators`.
5. **Ask the user before** rebuilding the feature table.

## Trap

Only `pre_match` odds go into features. Closing odds are only known at kick-off, so using them would leak information a bettor doesn't have.

## Open question for this chunk

Which bookmaker's pre-match odds drive the odds calculator: Pinnacle (sharpest, from about 2012/13) or the market average (`AvgH` / `BbAvH`, longer history)?

## Expected test failures

- `tests/test_features.py`: feature column counts change.

## Scope ledger

**Core**

- steps 1–5 (both calculators were ticked as optional at phase level)

**Optional** (ticked = written)

- none raised
