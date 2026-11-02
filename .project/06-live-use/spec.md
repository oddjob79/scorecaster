# 06 Live use

## Goal

Run the whole pipeline each week on upcoming fixtures: paper trading first (recording bets without placing them), then real stakes once paper results back up the backtest.

## Why

- Backtests flatter. Prices move, odds aren't always available at the quoted price, and data arrives late.
- Paper trading shows the real-world gap before money is at risk.

## Shape of the solution

- **Weekly run:** refresh data → refit models → predict upcoming fixtures → fetch current odds → flag value → size stakes → write a bet slip.
- **Current odds:** football-data.co.uk's `fixtures.csv` carries odds for the coming weekend. A live odds source (an odds API or an exchange API) gives fresher prices.
- **Bet log (sport-neutral):** every suggested bet with model probability, price taken, stake, closing price and result. The same table serves paper and real bets, with a flag for which is which.
- **Review:** paper results compared with the backtest's expectations: CLV, ROI and drawdown, after a set number of bets.
- **Go/no-go rule:** a pre-agreed threshold for moving from paper to real money, for example positive CLV over 500 bets.

## Open questions

- Which live odds source? Betfair's Exchange API is free with an account; odds aggregator APIs are mostly paid.
- How often to run: once on a fixed day, or again close to kick-off when team news is in?
- Run manually from WSL, or on a schedule (cron in WSL)?
- What's the go/no-go threshold?

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- weekly run script: refresh, refit, predict, flag, stake
- current odds from football-data.co.uk `fixtures.csv`
- bet log table with paper/real flag
- results settled into the bet log

**Optional**

- live odds API or Betfair Exchange API (new loader)
- scheduled run with cron (WSL)
- notification of the week's bet slip, for example by email (new script)
- paper vs backtest review report (analysis notebook)
- second run close to kick-off (weekly run)
