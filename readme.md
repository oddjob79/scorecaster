# Scorecaster

Football results, match stats and bookmaker odds for European leagues, turned into pre-match team features for forecasting results and goals, and explored through a stats app.

## Parts

| Part | Where | Status |
|---|---|---|
| **Data and models**: SQLite store, download cache, feature builder, data-quality report | [`scorecaster/readme.md`](scorecaster/readme.md) | Data pipeline complete; models planned |
| **Stats app**: league tables and form tables on any date, team histories, an Elo journey across divisions, team comparisons | [`.project/stats-app/spec.md`](.project/stats-app/spec.md) | In design |

The stats app is built with FastAPI, Pydantic and SQLAlchemy on the back end, and React, TypeScript, Vite, TanStack Router and Query, Zustand, Tailwind and ECharts on the front end.

## Data

All match, stats and odds data comes from [football-data.co.uk](https://www.football-data.co.uk). It isn't ours to redistribute, so the repository contains none: `data/` is git-ignored. To run anything here you need that data, so obtain it yourself and ask football-data.co.uk for permission.

## Repository

```
scorecaster/     data and model package (readme inside)
scripts/         pipeline scripts and one-task scripts (scripts/adhoc/)
tests/           pytest suite
docs/            glossary
.project/        intent, specs and chunk plans for each phase, and for the stats app
changes.md       what each phase delivered
```
