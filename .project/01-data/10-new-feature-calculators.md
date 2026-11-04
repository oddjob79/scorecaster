# 10 New feature calculators

## Goal

Add match-stats form and odds-implied probabilities to the feature table for phase 03.

## Depends on

06, 09

## Decisions

- **Odds features use the market average's pre-match odds** (`BbAv` up to 2018/19, `Avg` after), user 2026-11-04. It is the one source present in every main-league season, the current season and the live fixtures. A model input must mean the same thing in training and in use: a sharpest-available ladder (Pinnacle, then Betfair Exchange) would change source between training seasons and live matches. The sharpest-available rule belongs to the phase 04 benchmark, which uses closing odds.
- **Only pre-match odds are read.** Closing odds are set at kick-off, so they would leak.
- **xG isn't in this chunk.** `HxG`/`AxG` exist for 2026/27 only, aren't stored, and have no history to learn from.

## Steps

1. `MatchStats` (`scorecaster/features/history.py`): one side's shots, shots on target, corners, fouls, yellows and reds. `TeamMatchRecord` carries `stats_for` and `stats_against`, filled from `matches` in `LeagueState`.
2. `StatsCalculator`: per-game averages, for and against, over the form windows (4, 6, 8), giving 36 columns named `stats_{n}_{stat}_{for|against}_pg`. A window is empty unless every game in it has that stat.
3. `remove_margin` / `market_probabilities` (`scorecaster/features/market.py`): 1/odds divided by their sum. `MatchSource.market()` reads each match's market-average pre-match 1X2 and over/under 2.5 prices.
4. `OddsCalculator`: from the team's side, `market_win_prob`, `market_draw_prob`, `market_loss_prob` and `market_over25_prob`.
5. Both are registered in `default_calculators`. The feature columns change, so `build_features.py --rebuild` is needed.
6. **Ask the user before** the sample build and the full rebuild.

## Expected test failures

- `tests/test_features.py`: feature column counts change.

## Scope ledger

**Core**

- steps 1–6

**Optional** (ticked = written)

- none raised
