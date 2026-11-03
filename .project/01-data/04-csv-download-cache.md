# 04 CSV download cache

## Goal

Download each football-data.co.uk CSV once into `downloads`, so re-runs and re-parses make no requests.

## Depends on

02, 03

## Steps

1. In `scorecaster/ingest/download.py`, build the URL list from the league config:
   - main: `https://www.football-data.co.uk/mmz4281/{yyyy}/{code}.csv`, e.g. `mmz4281/2425/E0.csv`
   - extra: `https://www.football-data.co.uk/new/{code}.csv`
2. For each URL, serve the stored body when `downloads` has the URL, otherwise fetch it and store the bytes.
3. Wait on `RateLimiter` (from chunk 01) before each fetch, at 1–2 seconds per request.
4. Log one line per file: URL, cached or fetched, size.
5. Refresh: `DownloadCache.get(url, refresh=True)` re-fetches and replaces the stored body. `CsvFile.is_live()` marks the files that can still change: the season in progress and the all-seasons extra-league files. The `--refresh` flag that uses them is part of `scripts/load_data.py` (chunk 05), and fixtures files join the list in chunk 08.
6. **Ask the user before** the first real fetch: E0 2024/25 only.

## Notes

- The site is blocked on Windows. Every fetch runs from WSL.
- Extra-league files hold every season, so `--refresh` re-fetches them whole.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–2: URL list and fetch-once cache
- step 6: first fetch, with permission

**Optional** (ticked = written)

- [x] step 3: polite delay between fetches
- [x] step 4: progress logging
- [x] step 5: `--refresh`
