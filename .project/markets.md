# Markets and sports

Where scorecaster looks for value, and how other sports fit in.

## Which markets give the best chance

Bookmakers' odds are a forecast shaped by money. The more money a market attracts, the sharper (more accurate) its prices, and the harder it is to beat. Where you bet matters more than what you bet on.

**Hardest to beat**

- 1X2 (home / draw / away), over/under 2.5 and Asian handicap (one team gets a goal start, which removes the draw) in the Premier League and the other big European leagues. These take the most money and have the sharpest prices.

**Better chances**

- **Smaller and lower leagues**, for example English League One, League Two and the National League, the Scottish divisions, and the second tiers in Germany, Spain, Italy and France. Less money and attention mean less sharp prices. Bookmakers accept smaller stakes there.
- **Side markets** such as both teams to score and correct score. The bookmaker's cut is bigger, but these get less attention, so mispricing lasts longer.

**How this shapes the plan**

A goals model (one that predicts how many goals each team scores) gives probabilities for every goal market at once: 1X2, over/under at any line, Asian handicap, both teams to score and correct score. The market doesn't need choosing up front. The goals model is backtested against the odds football-data.co.uk holds (1X2, over/under 2.5 and Asian handicap), and the results show where the edge is.

## Things to know before betting real money

- **Accounts get restricted.** UK bookmakers commonly cut the maximum stake for customers who win steadily.
- **Exchanges don't restrict winners.** On a betting exchange you bet against other customers rather than the bookmaker; examples are Betfair, Smarkets and Matchbook. They charge commission on winnings instead, so the edge has to be bigger than the commission.
- **Route:** start with whichever of bookmakers or exchanges gives the better prices, and move to exchanges once bookmakers start restricting the account.
- **The closing line is the real test.** Pinnacle's odds just before kick-off are the sharpest widely available prices. Pinnacle doesn't take UK customers, but football-data.co.uk records its closing odds. Probabilities that regularly beat Pinnacle's closing price are the strongest early evidence of an edge, and that evidence shows long before profit and loss becomes reliable.

## Wider leagues

football-data.co.uk covers about 22 main leagues across 11 countries, with match stats and odds from several bookmakers. It also has extra leagues (for example Brazil, the USA and the Scandinavian leagues) with results and closing odds only. All of them share one CSV format, so adding a league is mostly configuration.

The scope is any league with collectable data that can be reliably bet on in the UK.

## Other sports

If football shows no value, other sports are an option.

**Design**

- **The betting layer is sport-neutral:** odds, markets, predictions, bets, staking and backtesting. A bet is a price, a probability and a stake, whatever the sport.
- **Football-specific code lives in its own package:** loaders, feature calculators and the goals model.
- **A second sport gets its own package beside football.** Shared pieces are pulled out once there are two real examples to design from, not before.

**What to expect**

- **More predictable doesn't mean more profitable.** The odds already reflect how predictable a sport is. A tennis favourite who wins 80% of the time is priced at about 1.25.
- **Tennis** is the most practical second sport. tennis-data.co.uk, run by the same person as football-data.co.uk, has free ATP and WTA results with bookmaker odds going back to the early 2000s.
- **NFL** markets are among the sharpest there are.
- **Rugby** markets are smaller, so less sharp, but there's less free data.
- **Golf** outrights (betting on the winner of a whole tournament) have huge fields and big bookmaker margins, which makes golf a hard place to start.
