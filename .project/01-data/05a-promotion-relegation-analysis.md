# 05a Promotion and relegation analysis

## Goal

Measure how teams do in their first season after changing division, by tier boundary and direction, to choose how chunk 09 rates newcomers in Elo: per-league with seeds, or pyramid with division offsets.

## Depends on

05 (main-league results loaded)

## Hypothesis under test

Promoted teams are relatively stronger the lower down the pyramid they arrive, e.g. National League → League Two or League Two → League One versus Championship → Premier League. Relegated teams arrive strong, especially from the top tier.

## Steps

1. Add `scripts/promotion_analysis.py`, read-only. For each league-season, find newcomers: teams whose previous season was in a different tier of the same country. Record boundary (`E3 ← EC`), direction (promoted / relegated) and season.
2. For each newcomer, compute:
   - **finish percentile** in the new league: `(position − 1) ÷ (league size − 1)`, 0 = top, 1 = bottom. e.g. 5th of 24 → 0.17
   - **first-10 ppg vs average:** points per game over the first 10 matches minus the league's average points per game. e.g. 1.9 − 1.37 → +0.53
3. Group by boundary and direction (`newcomers_df` → `boundary_summary_df`): number of seasons, mean finish percentile, mean first-10 ppg vs average.
4. Add the spread for each group: standard deviation, minimum and maximum.
5. Split each group by previous finish:
   - promoted: champion, other automatic promotion, playoff winner
   - relegated: bottom place, other relegation places
6. Split each group by era: 2005/06–2012/13 and 2013/14 onward.
7. **Ask the user before** running it.
8. Write the conclusion at the end of this file:
   - does the hypothesis hold?
   - do the gaps differ enough by boundary to need per-boundary values?
   - does previous finish matter within a boundary?
   - the chunk 09 choice: per-league with seeds per (boundary, direction, previous finish), or pyramid with offsets per boundary

## Trap

These results set Elo seeds or offsets, which phase 02–05 backtests then use. Values estimated from all seasons leak later outcomes into earlier predictions. Chunk 09 estimates them only from seasons before the one being rated. This analysis can use every season, because it's only for making the decision.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–3: newcomers, two measures, boundary summary
- step 7: run, with permission
- step 8: written conclusion

**Optional** (ticked = written)

- [x] step 4: spread
- [x] step 5: previous-finish split
- [x] step 6: era split
- [ ] charts (needs matplotlib)

## Conclusion

To be written after the run.
