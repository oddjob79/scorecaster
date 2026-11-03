# 09a Season-phase analysis

## Goal

Find out whether results are skewed or harder to predict in some fifths of a season, to decide whether phase 02 adjusts probabilities by season phase.

## Depends on

06, 07, 09 (results, odds and `season_phase` in the feature table)

## Steps

1. Add `scripts/season_phase_analysis.py`, read-only. Join finished matches to the home team's `season_phase` from the feature table and to Pinnacle closing 1X2 odds (`phase_df`).
2. Turn the odds into probabilities with the bookmaker margin removed: each price's 1/odds divided by the sum of all three. e.g. 2.00 / 3.50 / 4.00 → 0.50, 0.29, 0.25 → ÷ 1.04 → 0.48, 0.27, 0.24.
3. For each season phase (1–5), overall and by league:
   - home win, draw and away win rates, and average goals
   - log-loss of the closing-odds probabilities: how well the market predicted that phase
4. **Ask the user before** running it.
5. Write the conclusion at the end of this file:
   - are any phases less predictable than the middle of the season?
   - is the market worse there, a sign of possible mispricing?
   - does phase 02 need a per-phase probability adjustment?

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–3: phase table with result rates, goals and market log-loss
- step 4: run, with permission
- step 5: written conclusion

**Optional** (ticked = written)

- none raised yet

## Conclusion

To be written after the run.
