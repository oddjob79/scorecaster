# 08 Fixtures

## Goal

Load upcoming matches and their current odds from football-data.co.uk's fixtures files, so the feature builder and later phases can see next week's games.

## Depends on

05, 06

## Steps

1. Add the fixtures URLs to the download list: `fixtures.csv` (main leagues) and the site's extra-league fixtures file (name taken from the data page).
2. Parse with the chunk 05 and 07 parsers. Fixtures share the results files' columns, without scores.
3. Upsert matches with status `scheduled`. When the result arrives in a later season file, the same unique key updates the row to `finished`.
4. Upsert the fixtures' odds as `pre_match`.
5. Add fixtures to `scripts/load_data.py`.
6. **Ask the user before** the first fixtures fetch.

## Notes

- The fixtures files cover roughly the coming week and are refreshed a few times a week, so they need `--refresh` (chunk 04).
- A postponed fixture stays `scheduled` until a later fixtures file or result replaces it.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–5
- step 6: fetch, with permission

**Optional** (ticked = written)

- none raised
