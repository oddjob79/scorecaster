# 09a Season-phase analysis

## Goal

Find out whether results are skewed or harder to predict in some fifths of a season, to decide whether phase 02 adjusts probabilities by season phase.

## Depends on

06, 07, 09 (results, odds and `season_phase` in the feature table)

## Steps

1. Add `scripts/adhoc/season_phase_analysis.py`, read-only. Join finished matches to the home team's `season_phase` from the feature table and to Pinnacle closing 1X2 odds (`phase_df`).
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

Run 2026-11-04: 154,880 finished matches with Pinnacle closing 1X2 odds (2012/13–2025/26, all leagues). Phase is the home team's.

| Phase | Matches | Home | Draw | Away | Goals | Log-loss |
|---|---|---|---|---|---|---|
| 1 | 30,873 | 0.434 | 0.271 | 0.295 | 2.63 | 1.011 |
| 2 | 32,412 | 0.437 | 0.267 | 0.296 | 2.67 | 1.009 |
| 3 | 31,077 | 0.440 | 0.265 | 0.295 | 2.65 | 1.005 |
| 4 | 30,956 | 0.439 | 0.265 | 0.296 | 2.59 | 1.002 |
| 5 | 29,562 | 0.446 | 0.251 | 0.303 | 2.72 | 0.992 |

Sampling error on each phase's log-loss is roughly ±0.003, since the per-match spread is about 0.5 over about 30,000 matches. Per league it is about ±0.015, so single league-phase cells are mostly noise.

**Are any phases less predictable?** Only mildly, and only at the start. The market's log-loss falls steadily from phase 1 (1.011) to phase 5 (0.992). The first fifth of a season is the hardest to call, which fits uncertainty about team strength after the summer (transfers, promoted teams). The last fifth is the easiest, not the hardest.

**Are results skewed?** Yes, at the end. Phase 5 has fewer draws (25.1% against 26.5–27.1%), more goals (2.72) and a few more home and away wins. Results are more decisive late in the season. The market prices this well, since phase 5 has its lowest log-loss.

**Is the market worse anywhere, i.e. possible mispricing?** Slightly worse in phase 1. The gap from phase 1 to phase 3 is about 0.006, two to three times the sampling error, so it is real but small. There's no sign of a large, exploitable weakness by phase.

**For phase 02:**
- No per-phase probability adjustment up front.
- Add per-phase calibration and log-loss to the phase 02 evaluation, for our model next to the market. If our model is notably worse than the market in phase 1, the planned shrinkage toward base rates is applied there (fitted on earlier seasons only).
- The late-season shift (fewer draws, more goals) is a distribution change, not lost predictability. `season_phase` as an input feature (phase 03) lets the model learn it, rather than widening probabilities.
