# Glossary

Terms used in the code, the docs and `.project/`. Where a term records a decision, the chunk that made it is given.

## Data and loading

**Main league / extra league.** Main leagues (`E0`, `SP1`, …) have one CSV per season on the site, loaded from 2005/06. Extra leagues (`BRA`, `USA`, …) have one CSV holding every season, from about 2012. Set by `file_style` in `LEAGUES`.

**Calendar-year league.** A league whose season runs January to December, labelled `2024` (ARG, BRA, FIN, IRL, NOR, SWE, USA). The rest run August to May, labelled `2024/25`. Set by `calendar_year` in `LEAGUES`.

**Season in progress.** For August–May leagues, the season that started in the most recent July (`current_season_start`: 2026-11-05 → 2026). For calendar-year leagues, the current year.

**Live file.** A downloaded file that can still change: the current season's files, every extra-league file and the fixtures files. `--refresh` re-downloads only these.

**Upsert.** Insert a row, or update it if a row with the same natural key exists. Every load is an upsert, so loading a file twice changes nothing.

**Natural key.** The columns that identify a row in the real world, e.g. a match is (competition, date, home team, away team). Each table has a unique constraint on it.

**Team alias.** A variant spelling of a team name (`Gornik Z.`) mapped to the team it belongs to (`Gornik Zabrze`) in `team_aliases`. The loader resolves aliases before names.

**Unplayed status.** A match without a score is `scheduled` in the season in progress and `void` in any earlier one, i.e. never played (chunk 05).

**Playoff-only appearance.** A team with 4 or fewer games in a league-season: a lower-division team that only played a promotion or relegation tie included in an extra-league file.

## Odds

**1X2.** The three-way market on the result: home win, draw, away win.

**Over/under 2.5.** Whether the match has 3 or more goals (over) or 2 or fewer (under). Stored with `line` 2.5.

**Asian handicap.** A market where one side starts with a goal handicap, removing the draw. `line` is the side's handicap: the file gives the home line (e.g. −0.75) and the away side takes the opposite (+0.75). A quarter line such as −0.75 splits the stake between −0.5 and −1.

**Pre-match / closing.** `pre_match` is the site's snapshot of prices when it collects data, usually Friday afternoon for weekend games and Tuesday for midweek. It is not the opening price. `closing` is the last price before kick-off.

**Margin.** The bookmaker's built-in profit: the implied probabilities (1/price) of all outcomes add up to more than 1. Removing it divides each 1/price by their sum, e.g. 2.00 / 3.50 / 4.00 → 0.48, 0.27, 0.24.

**Market average / market max.** The average and the best price across the bookmakers the site tracks (Betbrain's figures up to 2018/19, the site's own after). Market average pre-match odds drive the `market_*_prob` features, because they exist in every season and in the fixtures; a model input must mean the same thing in training and in use (chunk 10).

**Benchmark odds.** The sharpest available closing price, used to judge a model (phase 04): Pinnacle closing, then Betfair Exchange closing, then market average closing, stored with its source. Pinnacle stops partway through 2025/26.

## Features

**Leakage.** A feature using information not known before kick-off. The builder reads each day's features before applying that day's results; model estimates (Elo move adjustments, any later calibration) use only earlier seasons. A leaking feature makes backtests look better than live results will be.

**Expanding window.** An estimate for season S built from every season before S and none after. Used for the Elo move adjustments.

**Form window.** The last N games of a team (N = 4, 6, 8, …), carried across seasons. A window is empty until the team has played N games, and a stats window is empty unless every game in it has that stat.

**Position band.** Which fifth of its league's table a team is in: `ceil(position × 5 ÷ league size)`, band 1 the top. 20 teams: 1–4 → 1, 17–20 → 5; 24 teams: 5–9 → 2 (chunk 09). Before a team's first game, last season's final band is used; a team new to the league starts in band 5.

**Season phase.** Which fifth of its season a game falls in: `ceil(5 × game number ÷ season length)`, capped at 5. Season length is the most games any team played that season, or the previous season's figure for the season in progress. Premier League: games 1–7 → 1, 31–38 → 5 (chunk 09). Chunk 09a found the market slightly less accurate in phase 1 and late-season results more decisive (fewer draws, more goals).

**Finish percentile.** A final table position scaled to 0 (top) … 1 (bottom): `(position − 1) ÷ (league size − 1)`. Used in chunk 05a.

**First-10 points per game against average.** A newcomer's points per game over its first 10 matches minus the league's average points per game. Used in chunk 05a.

## Evaluation

**Log-loss.** How well probabilities predicted results: the average over matches of −ln(probability given to the actual result). Lower is better. A perfect forecast scores 0; a third on each of home, draw and away scores ln 3 ≈ 1.099; the market's margin-free closing prices score about 1.00 on this data. A confident miss costs a lot: a result given 5% scores 3.0. The main score in phases 02–04, and how chunks 09a and the playoff analysis measured the market.

**Brier score.** Another accuracy score: the mean squared difference between the probabilities and the outcome (1 for what happened, 0 otherwise), summed over home, draw and away. Lower is better; it punishes confident misses less sharply than log-loss.

**Calibration.** Whether probabilities come true at the stated rate: of all results given about 60%, about 60% should happen. A model can have a good log-loss and still be over- or under-confident in places, e.g. in one season phase.

**Sampling error.** How much a figure would move by chance with a different set of matches. For an average over n matches it is about the per-match spread ÷ √n: log-loss varies by about 0.5 per match, so over 30,000 matches its average is good to about ±0.003, over 150 matches only ±0.04. Differences smaller than about twice the sampling error aren't evidence of a real effect.

## Elo

**Elo rating.** A number per team that rises when results beat expectation and falls when they don't. Each division's ratings centre on 1500.

**Expected score.** The rating model's forecast for a team, 0 to 1: `1 / (1 + 10^(−d/400))`, where `d` is the team's rating plus or minus home advantage minus the opponent's. Equal teams: 0.585 at home.

**K.** The size of each update: 20. A result moves both teams by `K × margin multiplier × (actual − expected)`, where actual is 1, 0.5 or 0.

**Home advantage.** 60 rating points added to the home side in the expectation.

**Margin multiplier.** Scales an update by the goal margin: 1 for 0–1 goals, 1.5 for 2, then (11 + margin) ÷ 8.

**Summer regression.** At the start of each season, returning teams move 20% of the way back to 1500, reflecting squad turnover.

**Per-league Elo.** One rating scale per league. A team that changes league starts again from a seed. Used for single-tier countries (Netherlands, Belgium, Portugal, Turkey, Greece) and the extra leagues.

**Pyramid Elo.** Elo across a country's loaded divisions (England, Scotland, Germany, Italy, Spain, France) where a team keeps its own rating when it moves. Chosen in chunk 05a, because promoted and relegated teams vary as much within a group as between groups, so a team's own record beats a group average.

**Design B (convert on move).** The pyramid Elo design in use (chunk 09). Each division keeps its own 1500-centred scale; a moving team arrives with its last rating minus the boundary's adjustment. Chosen over **design A** (one country-wide scale with a fixed anchor per tier) because B can't drift between divisions and its adjustment is one readable number. A suits comparing teams across divisions and cup matches, neither of which the project uses.

**Boundary and direction.** A move between two divisions, e.g. into `E0` from `E1`, either promoted (up) or relegated (down). Each pair has its own adjustment.

**Adjustment.** For a boundary and direction, the mean over earlier movers of (rating at the end of the old season) − (rating after the first 10 games in the new division). Estimated with an expanding window, and used once at least 5 earlier movers exist.

**Fallback seed.** The first rating of a newcomer with nothing to carry (from a league not loaded, or before a boundary has 5 movers): the mean of the N lowest-rated returning teams for promoted or unknown teams, the N highest for relegated teams, where N is the number of newcomers.

## Tests

**Contract test.** A test that loops over a registry (every calculator, table or league), so additions are checked automatically.

**Decision test.** A test pinning a deliberate choice (`test_decision_*.py`). It fails when the decision changes, and is updated as part of that change.

**Tripwire.** A check in the code that raises at the point of misuse: pyramid Elo rejects a team outside the match's division; `create_db.py` stops when model and table columns differ; the builder stops when a calculator returns keys other than its columns.
