# 05a Promotion and relegation analysis

## Goal

Measure how teams do in their first season after changing division, by tier boundary and direction, to choose how chunk 09 rates newcomers in Elo: per-league with seeds, or pyramid with division offsets.

## Depends on

05 (main-league results loaded)

## Hypothesis under test

Promoted teams are relatively stronger the lower down the pyramid they arrive, e.g. National League → League Two or League Two → League One versus Championship → Premier League. Relegated teams arrive strong, especially from the top tier.

## Steps

1. Add `scripts/adhoc/promotion_analysis.py`, read-only, covering main leagues in completed seasons. For each league-season, find newcomers: teams whose previous season was in a different tier of the same country. Record boundary (`E3 ← EC`), direction (promoted / relegated) and season.
2. For each newcomer, compute:
   - **finish percentile** in the new league: `(position − 1) ÷ (league size − 1)`, 0 = top, 1 = bottom. e.g. 5th of 24 → 0.17
   - **first-10 ppg vs average:** points per game over the first 10 matches minus the league's average points per game. e.g. 1.9 − 1.37 → +0.53
3. Group by boundary and direction (`newcomers_df` → `boundary_summary_df`): number of seasons, mean finish percentile, mean first-10 ppg vs average.
4. Add the spread for each group: standard deviation, minimum and maximum.
5. Split each group by previous finish:
   - promoted: champion, other top places, from below (playoff), from outside (into the bottom tier from a league we don't load)
   - relegated: bottom place, other
   - there is no promotion-places config, so "from below (playoff)" means: n teams went up from that league-season and this one finished below nth
6. Split each group by era: 2005/06–2012/13 and 2013/14 onward.
7. **Ask the user before** running it.
8. Write the conclusion at the end of this file:
   - does the hypothesis hold?
   - do the gaps differ enough by boundary to need per-boundary values?
   - does previous finish matter within a boundary?
   - the chunk 09 choice: per-league with seeds per (boundary, direction, previous finish), or pyramid with offsets per boundary

## Traps

- Tables are rebuilt from results (points, goal difference, goals scored). Points deductions and split-league playoff rounds aren't modelled, so a few finishing positions are approximate.
- These results set Elo seeds or offsets, which phase 02–05 backtests then use. Values estimated from all seasons leak later outcomes into earlier predictions. Chunk 09 estimates them only from seasons before the one being rated. This analysis can use every season, because it's only for making the decision.

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

Run 2026-11-04: 1,695 newcomers across 462 main-league seasons, 2005/06–2025/26. Finish percentile: 0 = top, 1 = bottom. Mean shown.

**1. The hypothesis holds, for promoted and relegated teams.**

| Promoted into | England | Elsewhere |
|---|---|---|
| tier 1 | E0 0.77 | D1 0.72, F1 0.74, I1 0.77, SP1 0.74, SC0 0.65 |
| tier 2 | E1 0.64 | D2 0.63, F2 0.61, I2 0.53, SP2 0.64, SC1 0.61 |
| tier 3 | E2 0.55 | SC2 0.58 |
| tier 4 | E3 0.50 | — |

Promoted teams finish lower the higher the tier they join. First-10 points per game against the league average fall the same way: E0 −0.42, E1 −0.17, E2 −0.05, E3 −0.05. Relegated teams arrive strong from the top tier (E1 ← E0 0.30, other second tiers 0.31–0.35). That advantage fades lower down: E3 ← E2 0.49, SC3 ← SC2 0.49.

**2. The gap depends on tier more than on country.** The top-tier entries cluster at 0.72–0.77 and the second-tier entries at 0.53–0.64, so per-boundary values are needed and the tier explains most of the difference.

**3. Previous finish matters, especially lower down.** League champions do clearly better than playoff winners in the lower tiers: E2 ← E3 0.48 against 0.69, SC1 ← SC2 0.47 against 0.70, SC2 ← SC3 0.46 against 0.80. At the top the gap is smaller (E0 ← E1 0.73 against 0.81). Teams relegated from bottom place do a little worse than other relegated teams.

**4. The spread within each group is wide.** Standard deviations are 0.2–0.3, as large as the differences between boundaries. A group-average seed would leave most newcomers mis-rated by a similar amount.

**5. Some drift between eras.** Joining Serie A and the Premier League got harder from 2013 (I1 0.69 → 0.81, E0 0.74 → 0.79), and SC1 ← SC2 became easier (0.78 → 0.48). Estimating from earlier seasons only, as already planned, keeps up with this.

**Recommendation for chunk 09: pyramid Elo** for countries with more than one loaded tier (England, Scotland, Germany, Italy, Spain, France). Each team keeps its own rating across divisions, so the champion-against-playoff difference (point 3) and the individual spread (point 4) are handled by the team's own record, not a group average. Tier offsets, i.e. the rating gap between adjacent divisions, come from the per-tier gaps in point 2, estimated from earlier seasons only. Single-tier countries (N1, B1, P1, T1, G1) and the extra leagues stay per-league. Their promoted-from-outside teams finish around 0.66–0.77, so the fallback seed (average of the lowest-rated N) fits them.

**Decision (user, 2026-11-04):** pyramid Elo for England, Scotland, Germany, Italy, Spain and France, with tier offsets estimated from earlier seasons only. Per-league Elo with the lowest-rated-N fallback everywhere else.
