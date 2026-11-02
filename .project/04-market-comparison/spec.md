# 04 Compare with the market

## Goal

Measure whether the model's probabilities beat the bookmakers', by league and by market, before any money is involved.

## Why

- Pinnacle's closing odds are the sharpest widely available forecast.
- A model that can't beat them over thousands of matches has no reliable edge, however accurate it looks on its own.

## Shape of the solution

- **Implied probability:** odds of 2.50 imply 1 / 2.50 = 40%. Bookmakers' implied probabilities add up to more than 100%; the excess is their margin. Removing the margin gives a fair market probability.
- **Head to head:** for each match and market, compare model probability, fair Pinnacle closing probability and the result. Score both with log-loss. The model beats the market where its log-loss is lower.
- **Value flags:** a selection is value when the model's probability × the best available price > 1. For example, 48% × 2.50 = 1.20.
- **Closing line value (CLV):** for each value flag, did the price shorten (drop) by kick-off? Regularly beating the closing price is the earliest reliable sign of an edge.
- **Breakdown:** results by league, market and odds range, to find where any edge sits. See `../markets.md`.

## Open questions

- Which margin-removal method: proportional, Shin, or power? They differ most on longshots.
- Compare with opening odds as well as closing odds? Opening odds are softer and closer to what's available early in the week.
- Minimum edge before a flag counts, for example 3%?

## Scope ledger

Ticked once this phase is broken into chunks.

**Core**

- implied and fair probability from odds
- model vs Pinnacle closing log-loss by league and market
- value flags against the best available price
- CLV for each value flag

**Optional**

- several margin-removal methods compared (probability conversion)
- opening-odds comparison (comparison step)
- breakdown by odds range (report)
- charts of edge by league and market (analysis notebook)
