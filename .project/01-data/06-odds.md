# 06 Odds

## Goal

Load five odds sources from the main-league CSVs into the sport-neutral `odds` table: 1X2, over/under 2.5 and Asian handicap, pre-match and closing.

## Depends on

05

## Sources stored

| Bookmaker | Column prefixes | Seasons | Used for |
|---|---|---|---|
| `pinnacle` | `PS` (1X2), `P` (OU, AH) | 2012/13 – 2025/26 | benchmark (phase 04) |
| `market_avg` | `BbAv` (to 2018/19), `Avg` (2019/20 on) | all | features, fallback benchmark |
| `market_max` | `BbMx` (to 2018/19), `Max` (2019/20 on) | all | upper bound on the bet price |
| `bet365` | `B365` | all | realistic bet price (phase 05) |
| `betfair_exchange` | `BFE` | 2024/25 on | substitute benchmark after Pinnacle |

Other bookmakers' columns are recognised and skipped. Adding one is one entry in `ODDS_SOURCES` plus a re-parse from the cache.

## Traps

- **Pre-match is not opening.** co.uk's non-closing odds are snapshots taken when the site collects data (Friday afternoon for weekend games, Tuesday for midweek). The timing label is `pre_match`, not `opening`.
- **Pinnacle stops after 2025/26.** 2026/27 files have no Pinnacle columns. Phase 04 needs a substitute benchmark (Betfair Exchange closing, then market average closing), stored with its source.
- **Closing odds start in 2019/20**, except Pinnacle's (`PSC*`, from 2012/13).
- **SP2 2009/10 writes 10 Asian handicap lines as split pairs** (`BbAHh = "-0.5,-1"`, meaning −0.75). They fail number conversion, so those matches have no Betbrain AH prices. This is the only file that does it.

## Steps

1. In `scorecaster/ingest/fdcuk/columns.py` (`OddsColumn`), recognise odds columns with one pattern: `{prefix}{C if closing}{H|D|A|>2.5|<2.5|AHH|AHA}`, e.g. `PSCH` → (pinnacle, closing, 1X2, home) and `BbAv>2.5` → (market_avg, pre_match, OU, over).
2. `build_odds_rows` melts each file's odds columns into one row per price (`odds_df`):
   - `line` is 0 for 1X2 and 2.5 for over/under
   - Asian handicap: home takes `AHh` (or `BbAHh` before 2019/20) for pre-match and `AHCh` for closing, away takes the negative, and rows with no line are dropped
   - empty prices are dropped
3. `SeasonWriter.write` (`scorecaster/ingest/fdcuk/loader.py`) upserts the odds on (match, bookmaker, market, selection, line, timing) after the matches, in the same transaction.
4. Header check: `unknown_columns` reports any column that isn't a result, stat, known odds column or listed extra (`Bb1X2`, `HxG`, …).
5. **Ask the user before** running on E0 2024/25. Check one match's Pinnacle closing 1X2 against the CSV by hand.
6. **Ask the user before** re-running the full config, which re-parses from the cache with no downloads.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–3: column pattern, melt with AH lines, upsert
- steps 5–6: runs, with permission

**Optional** (ticked = written)

- [x] step 4: unknown-column report (the header check from chunk 05)
