# 02 Baseline goals model

## Goal

A simple, well-known goals model that gives a probability for every goal market and is the bar every later model has to beat.

## Why

- A goals model (predicts each team's goals) gives H/D/A, over/under at any line, Asian handicap, both teams to score and correct score from one prediction, so the markets always agree with each other.
- Without a baseline there's no way to tell whether the 150 features add anything.

## Shape of the solution

- **Model:** Dixon-Coles. Each team has an attack and a defence strength plus a home advantage; goals follow a Poisson distribution (the standard model for counts of rare events), with a correction for low scores such as 0-0 and 1-1. Recent matches carry more weight than old ones (time decay).
- **Fitting:** refit before each matchday using only matches before it, so no future information leaks in.
- **Output:** a score-probability grid per match (P(0-0), P(1-0), …), turned into market probabilities: 1X2, over/under 2.5, Asian handicap lines and both teams to score.
- **Storage:** a predictions table: match, model, market, selection, line, probability, created-at. Sport-neutral, shared with phases 03–06.
- **Evaluation:** walk-forward (train on earlier seasons, test on later ones). Scores:
  - log-loss: punishes confident wrong probabilities
  - Brier score: mean squared error of the probabilities
  - calibration: do 60% predictions come true about 60% of the time?

## Open questions

- Fit one model per league, or one across leagues with league-level home advantage?
- Time-decay rate: fixed from the literature or tuned on held-out seasons?
- Elo-Poisson as a second baseline?
- Which library: hand-written with scipy, statsmodels, or the `penaltyblog` package? Each needs permission to install.

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- Dixon-Coles fit with time decay
- walk-forward refit per matchday
- score grid → market probabilities (1X2, over/under 2.5, Asian handicap)
- predictions table
- log-loss and Brier score on held-out seasons

**Optional**

- calibration plots (analysis notebook)
- Elo-Poisson second baseline (new model module)
- both teams to score and correct-score probabilities (score-grid conversion)
- time-decay tuning (fitting)
- per-league result breakdown (evaluation)
