# 11a Tests

## Goal

Replace the obsolete test suite with one that guards what the pipeline promises, and fails loudly when a later change, such as new match details, cup competitions, new features or a revised Elo rule, breaks one of those promises.

## Depends on

01–11 (all code chunks). Written in one pass, last before the docs, per the user's testing rule.

## Principle

Test what is easy to get wrong and expensive when wrong, not everything the code does. Tests over registries (`default_calculators()`, the models, `LEAGUES`) cover anything added later. Tests that pin a decision live apart and say which decision they pin.

## Steps

1. **Clear out the obsolete suite:** delete `tests/test_ingest.py` and `tests/fixtures/*.json`, which test the deleted football-data.org code. Rewrite `tests/conftest.py` with an in-memory `Database` fixture and small hand-written CSV fixtures in `tests/fixtures/`, each holding the source quirks: a BOM, a row ending `,,,`, a two-digit year, a split handicap line, a junk cell, an extra-league file, a fixtures file.
2. **Tripwires in the code:**
   - `PyramidElo.update` raises if either team isn't in the match's division, so cross-division matches such as cups can't corrupt ratings silently
   - `scripts/create_db.py` compares model columns with database columns and stops with a list of differences, so a new column on an existing table needs an explicit migration
   - `FeatureBuilder` raises if a calculator returns keys other than its `columns()`, naming the calculator
3. **Pure-function tests:** `parse_dates`, `decode_csv`, `_trim_extra_fields`, `SeasonSpan`, `current_season_start`, `season_for`, `OddsColumn.parse`, odds lines (1X2 0, Asian handicap away negated), `band_of`, `season_phase`, Elo maths, `MoveAdjustments` (earlier seasons only, minimum samples), `_fallback`, `LeagueConfig` validation.
4. **Contract tests over registries:**
   - every calculator: returns exactly its `columns()`; no name clashes; handles a first match with empty history; **no leakage** (changing a match's result leaves that match's features unchanged)
   - every model: has a unique key; re-loading the same rows doesn't duplicate them
   - every league in `LEAGUES`: validates and builds a well-formed URL
   - the tripwires in step 2 raise when triggered
5. **Data-safety tests (in-memory database):**
   - loading the same file twice is idempotent
   - `void` in past seasons, `scheduled` in the current one
   - a fixtures reload never overwrites a finished match
   - `DownloadCache` fetches once and `refresh` fetches again (fake HTTP session)
   - `load_data.fetch` 404 rules
   - end to end: a mini CSV goes through load and feature build, checking row counts and a handful of values
6. **Decision tests**, one file per decision, named `test_decision_*.py`, with the decision and where it was made in the docstring: Elo maths, pyramid design B (convert on move, at least 5 movers, 10 games, fallback), proportional fifths, `void`/`scheduled`, season phase. They fail when the decision is changed, and are updated as part of that change.
7. **Ask the user before** running the suite.

## Not covered by design

- whether a new feature means the right thing, e.g. whether rest days count cup games; that's a design judgement
- pandas or SQLAlchemy behaviour, all 160 feature columns one by one, the real database, network access, a coverage percentage
- schema migrations: adding columns to tables that already hold data needs `ALTER TABLE` or a tool such as Alembic. The step 2 tripwire forces that decision when the first such change comes.

## Files

| File | Covers |
|---|---|
| `tests/conftest.py` | in-memory `db`, `loaded_db` (mini season), `featured_db`; `read_fixture`, `season_file`, `scalar`, `rows` |
| `tests/fixtures/mini_E0.csv` | 4 teams, 12 matches, 2024/25, with stats and odds |
| `tests/fixtures/mini_BRA.csv`, `mini_fixtures.csv` | an extra-league file over two calendar seasons; a fixtures file repeating one finished match |
| `test_reader.py` | BOM and cp1252, 2/4-digit years, `,,,` rows, extra-data rows, junk numbers, bad dates, renamed columns |
| `test_odds.py` | `OddsColumn.parse`, `unknown_columns`, lines, handicap negation and split lines, empty prices |
| `test_seasons_and_leagues.py` | `SeasonSpan`, `current_season_start`, `season_for`, `season_dir`, `LeagueConfig` validation, every league's URLs |
| `test_contracts.py` | unique feature names; every calculator on a first match; **no leakage**; every table has a natural key; idempotent load |
| `test_data_safety.py` | void/scheduled, extra-league load, fixture guard, download cache, 404 rule, the three tripwires, end to end |
| `test_decision_elo.py` | Elo maths |
| `test_decision_pyramid_design_b.py` | adjustments, fallback, move rating, 10-game measurement |
| `test_decision_bands_phase_status.py` | proportional fifths, season phase, unplayed status |

## Expected size

About 40–60 tests, running in a few seconds.

## Scope ledger

**Core**

- steps 1, 3–6: obsolete suite cleared, fixtures, pure-function, contract, data-safety and decision tests
- step 7: run, with permission

**Optional** (ticked = written)

- [x] Elo division check (step 2)
- [x] schema drift check (step 2)
- [x] calculator key check (step 2)
- [ ] coverage report (`pytest-cov`, new dependency)
- [ ] decision-test log in the docs

## Result (2026-11-05)

81 tests, all passing in under a second. The first run found a real bug: when a CSV's first data row had extra trailing fields, pandas took them as an index and shifted every column, skipping our extra-field rule. `_parse_csv` now reads rows with the csv module. All 500 cached files read identically before and after.
