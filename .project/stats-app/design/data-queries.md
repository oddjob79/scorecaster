# Mockup data queries

The queries behind each mockup's numbers, run read-only against `data/scorecaster.db`. They're a starting point for the phase 03–05 endpoints.

## League page (`league.html`)

Every finished Premier League 2024/25 match with its score and match stats. The mockup computes the table, form table, stat views and top performers from these rows in the browser, for any date (matches on or before the date, i.e. as of 23:59).

```sql
SELECT m.match_date AS d, h.name AS h, a.name AS a,
       m.ft_home AS hg, m.ft_away AS ag,
       m.home_shots AS hs, m.away_shots AS as_,
       m.home_shots_on_target AS hst, m.away_shots_on_target AS ast,
       m.home_corners AS hc, m.away_corners AS ac,
       m.home_fouls AS hf, m.away_fouls AS af,
       m.home_yellows AS hy, m.away_yellows AS ay,
       m.home_reds AS hr, m.away_reds AS ar
FROM matches m
JOIN competitions c ON c.id = m.competition_id
JOIN seasons s ON s.id = m.season_id
JOIN teams h ON h.id = m.home_team_id
JOIN teams a ON a.id = m.away_team_id
WHERE c.code = 'E0' AND s.start_year = 2024 AND m.status = 'finished'
ORDER BY m.match_date, h.name;
```

380 rows, none missing match stats.

## Team page (`team.html`)

- **Season charts and header:** the league page query. Positions, home/away records, form and goals are computed from those rows in the browser.
- **Elo journey:** Elo before every finished match since 2016/17 for the 20 teams in the 2024/25 Premier League, with the competition each match was in.

```sql
WITH t AS (
  SELECT DISTINCT m.home_team_id AS id
  FROM matches m
  JOIN competitions c ON c.id = m.competition_id
  JOIN seasons s ON s.id = m.season_id
  WHERE c.code = 'E0' AND s.start_year = 2024
)
SELECT tm.name AS team, f.match_date, ROUND(f.elo) AS elo, c.code
FROM team_match_features f
JOIN t ON t.id = f.team_id
JOIN teams tm ON tm.id = f.team_id
JOIN competitions c ON c.id = f.competition_id
JOIN seasons s ON s.id = f.season_id
WHERE s.start_year >= 2016 AND f.is_finished
ORDER BY tm.name, f.match_date;
```

8,082 rows covering E0, E1 and E2.

## Matches (`matches.html`)

Every finished 2024/25 match in the 20 competitions up to 9 Feb 2025 (4,498 rows), so that positions before and after each match can be calculated. Matches from 24 Jan to 9 Feb (538) also carry kick-off time, half-time score, referee, match stats and market-average odds (pre-match and closing, all markets). The mockup treats 1 Feb 2025 as "today", so later matches show as upcoming.

```sql
SELECT c.code, c.name, c.country, c.tier, m.match_date, h.name AS home, a.name AS away,
       m.ft_home, m.ft_away, m.kickoff_time, m.ht_home, m.ht_away, m.referee,
       m.home_shots, m.away_shots, m.home_shots_on_target, m.away_shots_on_target,
       m.home_corners, m.away_corners, m.home_fouls, m.away_fouls,
       m.home_yellows, m.away_yellows, m.home_reds, m.away_reds,
       (SELECT GROUP_CONCAT(o.market || ':' || o.selection || ':' || o.timing || ':' || o.line || ':' || o.price, '|')
        FROM odds o WHERE o.match_id = m.id AND o.bookmaker = 'market_avg') AS odds
FROM matches m
JOIN competitions c ON c.id = m.competition_id
JOIN seasons s ON s.id = m.season_id
JOIN teams h ON h.id = m.home_team_id
JOIN teams a ON a.id = m.away_team_id
WHERE s.start_year = 2024
  AND c.country IN ('England', 'Scotland', 'France', 'Germany', 'Spain', 'Italy', 'Portugal', 'Netherlands', 'Belgium')
  AND m.status = 'finished' AND m.match_date <= '2025-02-09'
ORDER BY m.match_date, c.code, m.kickoff_time;
```

## Landing page (`landing.html`)

- **Current Elo:** each team's Elo before its latest finished 2026/27 match, by competition.

```sql
WITH cur AS (
  SELECT f.team_id, f.competition_id, f.elo, f.match_date,
         ROW_NUMBER() OVER (PARTITION BY f.team_id ORDER BY f.match_date DESC) AS rn
  FROM team_match_features f
  JOIN seasons s ON s.id = f.season_id
  JOIN competitions c ON c.id = f.competition_id
  WHERE s.start_year = 2026 AND f.is_finished
    AND c.country IN ('England', 'Scotland', 'France', 'Germany', 'Spain', 'Italy', 'Portugal', 'Netherlands', 'Belgium')
)
SELECT c.country, c.code, c.tier, t.name AS team, ROUND(cur.elo) AS elo, cur.match_date
FROM cur
JOIN teams t ON t.id = cur.team_id
JOIN competitions c ON c.id = cur.competition_id
WHERE rn = 1
ORDER BY c.country, c.tier, cur.elo DESC;
```

- **Elo gap between divisions:** for each boundary in a pyramid, the mean of (Elo before a mover's last match in the old division) − (Elo before its 11th match in the new one), by direction, e.g. Premier League / Championship: 205 up, 187 down. The landing page doesn't use this. It's recorded for phase 04's open question on one Elo scale. The pipeline learns these adjustments in `MoveAdjustments` but doesn't store them.

```sql
WITH g AS (
  SELECT f.team_id, c.code, c.country, c.tier, s.start_year AS y, f.elo,
         ROW_NUMBER() OVER (PARTITION BY f.team_id, f.season_id ORDER BY f.match_date) AS n,
         ROW_NUMBER() OVER (PARTITION BY f.team_id, f.season_id ORDER BY f.match_date DESC) AS nr
  FROM team_match_features f
  JOIN competitions c ON c.id = f.competition_id
  JOIN seasons s ON s.id = f.season_id
  WHERE f.is_finished AND c.country IN ('England', 'Scotland', 'Germany', 'Spain', 'Italy', 'France')
)
SELECT o.country, o.code || '->' || e.code AS boundary,
       CASE WHEN e.tier < o.tier THEN 'up' ELSE 'down' END AS direction,
       COUNT(*) AS movers, ROUND(AVG(o.elo - e.elo)) AS shift
FROM (SELECT * FROM g WHERE nr = 1) o
JOIN (SELECT * FROM g WHERE n = 11) e
  ON e.team_id = o.team_id AND e.y = o.y + 1 AND e.country = o.country AND e.code <> o.code
GROUP BY 1, 2, 3;
```

- **Season metrics** per competition per season from 2016/17:
  - results: home win, draw and away win rates;
  - goals: per game, over 2.5, both teams scored;
  - match stats: shots, shots on target, corners, yellow and red cards per game;
  - market: favourite won, and bookmaker margin, both from market-average pre-match 1X2 prices.

  Stats and market figures are blank for a season when fewer than 80% of its matches carry them.

```sql
WITH o AS (
  SELECT match_id,
         MAX(CASE WHEN selection = 'home' THEN price END) AS ph,
         MAX(CASE WHEN selection = 'draw' THEN price END) AS pd,
         MAX(CASE WHEN selection = 'away' THEN price END) AS pa
  FROM odds
  WHERE bookmaker = 'market_avg' AND market = '1X2' AND timing = 'pre_match'
  GROUP BY match_id
),
m AS (
  SELECT m.*, c.code, s.start_year AS y, o.ph, o.pd, o.pa
  FROM matches m
  JOIN competitions c ON c.id = m.competition_id
  JOIN seasons s ON s.id = m.season_id
  LEFT JOIN o ON o.match_id = m.id
  WHERE c.country IN ('England', 'Scotland', 'France', 'Germany', 'Spain', 'Italy', 'Portugal', 'Netherlands', 'Belgium')
    AND s.start_year >= 2016 AND m.status = 'finished'
)
SELECT code, y, COUNT(*) AS n,
       ROUND(100.0 * AVG(ft_result = 'H'), 1) AS home_win_pct,
       ROUND(100.0 * AVG(ft_result = 'D'), 1) AS draw_pct,
       ROUND(100.0 * AVG(ft_result = 'A'), 1) AS away_win_pct,
       ROUND(AVG(ft_home + ft_away), 2) AS goals,
       ROUND(100.0 * AVG(ft_home + ft_away > 2), 1) AS over_2_5_pct,
       ROUND(100.0 * AVG(ft_home > 0 AND ft_away > 0), 1) AS btts_pct,
       SUM(home_shots IS NOT NULL) AS with_stats,
       ROUND(AVG(home_yellows + away_yellows), 2) AS yellows,
       ROUND(AVG(home_reds + away_reds), 3) AS reds,
       ROUND(AVG(home_shots + away_shots), 1) AS shots,
       ROUND(AVG(home_shots_on_target + away_shots_on_target), 1) AS shots_on_target,
       ROUND(AVG(home_corners + away_corners), 1) AS corners,
       SUM(ph IS NOT NULL) AS with_odds,
       ROUND(100.0 * AVG(CASE WHEN ph IS NULL THEN NULL
                              WHEN ph <= pd AND ph <= pa THEN ft_result = 'H'
                              WHEN pa < ph AND pa <= pd THEN ft_result = 'A'
                              ELSE ft_result = 'D' END), 1) AS favourite_won_pct,
       ROUND(100.0 * AVG(CASE WHEN ph IS NULL THEN NULL ELSE 1 / ph + 1 / pd + 1 / pa - 1 END), 2) AS margin_pct
FROM m
GROUP BY code, y
ORDER BY code, y;
```

## Style tiles (`style*.html`)

- **Premier League table on 1 Feb 2025:** the same rows as above, filtered to `match_date < '2025-02-01'` and aggregated per team.
- **Leeds Elo:** the last `team_match_features.elo` per season for Leeds from 2016/17, with each season's competition code.
