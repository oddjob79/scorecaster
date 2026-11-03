# 03 League config

## Goal

List every league and season to load in one validated config, and write it into `competitions`.

## Depends on

02

## Contents

- **Main leagues**, one CSV per season (`mmz4281/{yyyy}/{code}.csv`), from 2005/06 to the current season:
  - England: E0, E1, E2, E3, EC
  - Scotland: SC0, SC1, SC2, SC3
  - Germany D1, D2 · Italy I1, I2 · Spain SP1, SP2 · France F1, F2
  - N1, B1, P1, T1, G1
- **Extra leagues**, one CSV holding every season (`new/{code}.csv`): ARG, AUT, BRA, DNK, FIN, IRL, JPN, MEX, NOR, POL, ROU, SWE, SWZ, USA. RUS and CHN are excluded as not reliably bettable in the UK. The codes are unconfirmed until chunk 04's first fetch.
- Per league: code, country, name, tier, file style (`season` / `all_seasons`), relegation places (fallback for the season in progress, see chunk 09).
- `relegation_places` counts automatic plus playoff relegation places, e.g. Bundesliga 3 (17th and 18th down, 16th in a playoff).

## Steps

1. Ask the user to add `pydantic` to `requirements.txt` and install it into the `scorecaster` pyenv virtualenv.
2. Add a pydantic `LeagueConfig` model in `scorecaster/config.py`, with tier ≥ 1, relegation places ≥ 0, file style one of the two values, and start season no later than the current season.
3. Write the league list as a module-level constant `LEAGUES` beside it, with `current_season_start()` for the season in progress.
4. Upsert the config into `competitions` (`Database.upsert_competitions`), called from `scripts/create_db.py`.

## Expected test failures

None new.

## Scope ledger

**Core**

- league list with code, country, name, tier, file style, relegation places
- upsert into `competitions`

**Optional** (ticked = written)

- [x] pydantic validation of the config (steps 1–2)
