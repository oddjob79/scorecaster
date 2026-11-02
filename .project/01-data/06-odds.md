# 06 Odds

## Goal

Load every bookmaker price in the main-league CSVs into the sport-neutral `odds` table: 1X2, over/under 2.5 and Asian handicap, pre-match and closing.

## Depends on

05

## Trap: pre-match is not opening

co.uk's non-closing odds are snapshots taken when the site collects data (Friday afternoon for weekend games, Tuesday for midweek), not opening odds. The timing label is `pre_match`, not `opening`.

## Steps

1. Read `notes.txt` (one cached download, **ask the user first**) and write a column map: column → (bookmaker, market, selection, line source, timing). Examples:
   - `PSH` → (Pinnacle, 1X2, home, –, pre_match)
   - `PSCH` → (Pinnacle, 1X2, home, –, closing)
   - `B365>2.5` → (Bet365, OU, over, 2.5, pre_match)
   - `PCAHH` → (Pinnacle, AH, home, `AHCh`, closing)
   - `AvgH` / `MaxH` → (market_avg / market_max, 1X2, home, –, pre_match)
   - older aggregates: `BbAvH`, `BbMxH`, `BbAHh`
2. In `scorecaster/ingest/fdcuk.py`, melt each file's odds columns into long rows (`odds_df`) using the map.
3. Set `line` for Asian handicap: home gets `AHh` (or `AHCh` for closing), away gets the negative.
4. Drop empty prices, then upsert on (match, bookmaker, market, selection, line, timing).
5. Add the odds step to `scripts/load_data.py` after results.
6. **Ask the user before** running on E0 2024/25. Check one match's Pinnacle closing 1X2 against the CSV by hand.
7. **Ask the user before** running the full config.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–5: column map, melt, AH lines, upsert, load script
- steps 6–7: runs, with permission

**Optional** (ticked = written)

- header check and type conversion are shared with chunk 05
