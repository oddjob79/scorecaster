# Changes

I've built the database, the data loader and the pre-match stats table on `init-data-populator`. Nothing has contacted the API yet. The 15 tests pass, and the scripts run against a throwaway database.

**How it's set up, based on your answers:** Premier League only, the last 5 seasons by default, one row per team per match, targets are the result and total goals, dependencies are SQLAlchemy, pandas and requests, positions are grouped into fixed bands (1–4, 5–8, 9–12, 13–16, 17–20), and form carries over from the previous season.

## What's in it

- **Database** ([create_db.py](scripts/create_db.py)): one-off script. It creates `data/scorecaster.db` with tables for areas, competitions, seasons, teams and matches. Running it again changes nothing.
- **Loading** ([load_data.py](scripts/load_data.py)):
  - Stored rows are never overwritten. The one exception is a match that hasn't finished: it's updated until the result arrives, then left alone.
  - Every API response is saved in the database, so a re-run makes no requests. A full 5-season load needs about 11 requests.
  - `--refresh` re-requests only the season in progress.
  - The API code sits behind an interface, so api-football can be added later, for example for bookmaker odds.
- **Pre-match stats** ([build_features.py](scripts/build_features.py)): about 150 columns per team per match, covering everything you listed plus a few strong extras:
  - previous results, form over 4/6/8 games (overall, home and away), and goals over longer windows
  - head to head, and record against teams in the opponent's league-position band at the time
  - streaks, season-to-date stats, league position, points gaps to the top and to the drop, and last season's finish
  - Elo rating and attack/defence strength compared with the league average
- **Avoiding hindsight:** matches are replayed day by day, and a day's results only count from the next day. League positions are rebuilt from results, because the API's standings endpoint only gives the current table.
- **Updating as you go:** each run adds new matches and refreshes upcoming fixtures, so those have stats ready for prediction.
- **Opponent's stats:** these come from two views rather than being stored twice. `v_match_features` has one row per match (`home_*` and `away_*` columns plus result, total goals, over 2.5 and both teams to score). `v_team_match_features` has each team's row with the opponent's stats alongside.
- **Export** ([export_dataset.py](scripts/export_dataset.py)): writes the dataset to CSV using pandas.

The [readme](readme.md) covers:

- which factors I added and which I left out, and why
- other analysis techniques: logistic and Poisson regression, LASSO for picking out the important factors from many overlapping ones, Dixon-Coles, and gradient boosting with SHAP
- how to test predictions properly: train on earlier seasons and test on later ones
- other ways to structure this, and why I kept the current one

## Things to know

- The API code follows the published v4 response format but has only been tested on sample JSON I wrote myself. Your first real `load_data.py` run will show any mismatches. If older seasons return 403, your plan doesn't include them.
- Only Premier League games are stored, so `rest_days` misses cup and European games, and promoted teams start with no history. Adding the Championship would fix the second one.
- Your existing api-football note was replaced by the new readme, which mentions it as a future add-on for odds.
- I created a `.venv` in the project; it's gitignored, as is `.env`.

## Suggested next step

An analysis notebook: a basic regression model, a ranking of which factors matter most, and a first check on accuracy.
