# 05 Staking and backtest

## Goal

Decide how much to stake on each value bet, then replay past seasons as if betting, to see the profit, the swings and how long losing runs last.

## Why

- An edge only becomes money with sensible stakes.
- Stakes that are too big turn a winning model into a broke bankroll during a bad run.
- Stakes that are too small waste the edge.

## Shape of the solution

- **Kelly criterion:** stake = bankroll × (p × odds − 1) / (odds − 1), where p is the model's probability. Example: p = 48%, odds 2.50 → stake 13.3% of bankroll.
- **Fractional Kelly:** stake a fraction of that, for example a quarter. This cuts the swings a lot for a small loss of growth, and allows for the model's probabilities being a bit off.
- **Backtest:** step through past matchdays in order with a starting bankroll. On each matchday: take value flags from phase 04, stake, settle at the closing or best price, and update the bankroll.
- **Costs:** exchange commission applied to winnings when backtesting against exchange prices.
- **Results:**
  - profit and ROI (return on stakes)
  - maximum drawdown (biggest fall from a peak)
  - longest losing run
  - number of bets
- **Portfolio with HiGHS (later):** when several bets fall on one weekend, choose which to place and how much under rules such as a total weekly budget, a maximum number of bets, a maximum per match and whole-pound stakes. MILP (mixed-integer linear programming: optimising with yes/no and whole-number choices) handles these rules; HiGHS is the solver.

## Open questions

- Which Kelly fraction to start with?
- Settle backtests at Pinnacle closing, best available, or a typical UK bookmaker's price? Only the last one is a realistic price for a UK punter.
- Stake every flag independently, or only the strongest N per week?
- Does `highspy` (HiGHS' Python package) need adding now, or only once simple Kelly is in place? Installing it needs permission.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- fractional Kelly stake per value flag
- walk-forward backtest with a bankroll
- profit, ROI and maximum drawdown

**Optional**

- exchange commission model (settlement)
- longest losing run and other risk stats (results)
- HiGHS weekly portfolio optimiser (new module)
- Monte Carlo runs (re-sampling results to see the range of outcomes) (analysis)
- bankroll charts (analysis notebook)
