# 12 Docs

## Goal

Describe the football-data.co.uk pipeline in the readme and changes log.

## Depends on

01–11

## Steps

1. `readme.md`: data source, league config, how to run `create_db.py`, `load_data.py` (with `--refresh`), `build_features.py` and `data_quality.py`, the table list, and the `pre_match` / `closing` odds timings.
2. `readme.md`, a section **"How downloads and the cache work"**, in plain, direct technical terms with no analogies (the user asked for this). It covers:
   - each file is downloaded once and its raw bytes are kept in the `downloads` table, so the database is its own copy of the site
   - loading reads those stored bytes, never the website, so re-running or re-parsing after a code fix needs no internet and costs the site nothing
   - only "live" files (the season in progress, the extra-league files and the fixtures) can change, and `--refresh` re-downloads just those
   - the two-second pause between downloads, and why
   - a short worked example: first run, second run, weekly refresh
3. `readme.md` (or `docs/glossary.md` if long), a **glossary** in direct technical terms (the user asked for this). It covers at least:
   - Elo: rating, expected score, K, home advantage, goal-difference multiplier, summer regression
   - per-league Elo, pyramid Elo, and why option B (convert on move) was chosen over option A (shared scale with anchors)
   - boundary, direction, adjustment, expanding window, fallback seed
   - finish percentile, first-10 points per game against average (from 05a)
   - position band (proportional fifths), season phase
   - odds terms: 1X2, over/under, Asian handicap and its line, pre_match against closing, market average and max, margin
   - leakage: why every estimate uses only earlier seasons
4. `changes.md`: one entry summarising phase 01.

## Expected test failures

None new.

## Scope ledger

**Core**

- steps 1–4 (ticked as optional at phase level)

**Optional** (ticked = written)

- none raised
