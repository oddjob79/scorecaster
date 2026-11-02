# 02 Schema

## Goal

Replace the football-data.org-shaped models with tables built around football-data.co.uk: internal IDs, natural keys and a sport-neutral odds table.

## Depends on

01

## Tables

All in `scorecaster/db/models.py`.

| Table | Columns | Unique key |
|---|---|---|
| `competitions` | id, code (`E0`, `BRA`), country, name, tier, relegation_places | code |
| `seasons` | id, competition_id, label (`2024/25` or `2024`), start_year, end_year | competition_id, label |
| `teams` | id, country, name | country, name |
| `team_aliases` | country, alias, team_id | country, alias |
| `matches` | id, competition_id, season_id, match_date, kickoff_time, status (`finished` / `scheduled`), home_team_id, away_team_id, ft_home, ft_away, ft_result, ht_home, ht_away, ht_result, referee, home/away shots, shots on target, fouls, corners, yellows, reds | competition_id, match_date, home_team_id, away_team_id |
| `downloads` | id, url, fetched_at, body (bytes) | url |
| `odds` | id, match_id, bookmaker, market (`1X2` / `OU` / `AH`), selection (`home` / `draw` / `away` / `over` / `under`), line, timing (`pre_match` / `closing`), price | match_id, bookmaker, market, selection, line, timing |

Notes:

- `matches` holds the stats as columns, empty for leagues and seasons without them.
- The `matches` unique key lets a re-run update rows in place, and lets a fixture become a result when its score arrives.
- `downloads.body` is raw bytes: co.uk files mix encodings, so the parser decodes them.
- `odds.line` is empty for 1X2, `2.5` for over/under, and the handicap for Asian handicap (e.g. `-0.5` home, `0.5` away).

## Steps

1. Replace `Area`, `Competition`, `Season`, `Team`, `SeasonTeam` and `Match` with the tables above.
2. Add `TeamAlias`, `Download` and `Odds`.
3. Update the exports in `scorecaster/db/__init__.py`.
4. Point `scripts/create_db.py` at the new models.

## Expected test failures

- `tests/test_features.py` builds `Match`, `Season` and `SeasonTeam` rows in the football-data.org shape.
- `tests/conftest.py` already fails from chunk 01.

## Scope ledger

**Core**

- steps 1–4

**Optional** (ticked = written)

- none raised
