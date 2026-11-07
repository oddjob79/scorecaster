### GOAL: Build a stats app to visualise the data brought in to the scorecaster back-end

The app is a stats site with a market lens: explore any team's or league's history across Europe's core leagues over the last decade, and see how well the betting market priced it.
It should be:
- Attractive
- Informative
- Secure
- Focused on simple but clear messaging

# Technical choices
- Shared repo with Scorecaster or separate repository.
    I would lean towards a shared repo as the API and front-end will be completely dependent on the data portion of scorecaster anyway, but am open to be convinced otherwise. It would also allow us to build functionality in the front-end around the models once they are completed
- Back-end stack
    Pretty much settled on FastAPI / Pydantic / SQLAlchemy
- Front-end stack
    I'm thinking Typescript, React, Vite. TanStack Query for State management & Tailwind for css. Tell me the merits of any alternatives
- LLM
    - I'd like to consider building an MCP which can read off the stats in the database, as a learning project.
    - We should also consider integrating chat functionality as an interface for querying the data

# Suggested Content - Ideas
Give me a very rough effort estimate on a scale of 1-10 (10 being highest) on each of these suggestions

- League tables for any season, plus how a table looked on any date. The second is a nice state-handling exercise: a date slider driving a recomputed table.

- A chart showing league performance over a period of time. Select different teams to add their "performance line" to the graph. Ability to add different metrics such as form, goals scored / conceded. Could get complicated, but could look great. A balance is needed.

- Team pages: form, home/away splits, goals for and against over time (line charts)

- Upcoming fixture information giving stats on previous meetings (head to head) as well as overview of team data

- Market views: odds-implied probability (the chance the odds imply, 1 / decimal odds) against actual outcome rates. A calibration chart (shows whether events priced at, say, 40% really happen 40% of the time) is a strong visual. It also leads naturally into the value-betting work later.

- Bookmaker margin (how much a bookmaker’s prices overcharge in total) across bookmakers and seasons, from the 5 odds sources you store.

Interrogate the features page and surface other key features I might have missed.

Focus on the core goal of the project and use ideas to realise that goal. Ask questions, if necessary

# MVP
Develop as a core minimum viable product with additional features logged as extensions
