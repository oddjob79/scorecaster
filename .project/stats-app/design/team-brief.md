# Who the page is for
General users of the site to view stats per league

# The 2–3 questions it answers
What are the performance details of the team in question per given time?
How has that performance changed over time?

# Its components in priority order
Competition selector
Season selector
Team selector
Date slider
Header with league, position, points and form chips (6 overall, 4 home, 4 away)
Chart component showing team metrics over time:
    - League position
    - Home / Away record
    - Form (H/A)
    - Goals F/A
    - ELO journey

# The data each component shows
Competition selector - List of competitions
Season selector - list of years available
Team selector - List of teams in competition
Date slider - dates in selected season
Header with league, position, points and form chips (6 overall, 4 home, 4 away)
Chart component showing team metrics over time:
    - League position
    - Home / Away record
    - Form (H/A)
    - Goals F/A
    - ELO journey

# Interactions and what they change (URL params, store)
Competition selector (filters seasons)
Season selector (filters teams)
Team selector (filters all info in page)
Date selector same as League page
Selector for what is shown in chart

# Out of scope
Other team's information overlaid on chart
Betting data
