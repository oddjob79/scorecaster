# 01 Remove the football-data.org code

## Goal

Delete the football-data.org loader so football-data.co.uk is the only data source in the repo.

## Depends on

Nothing.

## Steps

1. Move `RateLimiter` from `scorecaster/api/http.py` into `scorecaster/ingest/download.py`, the module chunk 04 builds the CSV download cache in.
2. Delete `scorecaster/api/` (`base.py`, `football_data.py`, `http.py`, `__init__.py`).
3. Delete `scorecaster/ingest/loader.py`, `records.py` and `repository.py`.
4. Delete `scripts/load_data.py`.
5. Remove the `ApiResponse` model from `scorecaster/db/models.py` and its export from `scorecaster/db/__init__.py`.
6. Remove the football-data.org token and base-URL fields from `Settings` in `scorecaster/config.py`. Tell the user which key in `.env` is now unused; they edit `.env` themselves.

## Expected test failures

- `tests/conftest.py` imports `scorecaster.api.base`, so test collection fails for every test until the end-of-phase test pass.
- `tests/test_ingest.py` and `tests/fixtures/*.json` test deleted code. They get removed in the test pass.

## Scope ledger

**Core**

- steps 2–6: delete the football-data.org code and settings

**Optional** (ticked = written)

- [x] step 1: keep `RateLimiter` for the polite download delay (chunk 04)
