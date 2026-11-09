# Who the page is for
General users of the site to view stats per league

# The 2–3 questions it answers
What is the current league position per team?
What statistics are available for us to show per team? (e.g. goals for/against, form (H/A), etc)
Current top performers (Over last 6 - 8 games, most goals scored / conceded, best / worst form)
Same stats but at different points in time

# Its components in priority order
Competition selector
Season selector
"Current time" date slider
League table
Different stats table (goals, form, etc)
"Top performers" displays

# The data each component shows
Competition selector - List of competitions
Season selector - list of years available
Date slider - should allow you to show what the stats were on any given date. Would be best as a slider probably, but could be different alternatives
League table - initially shows league table with standard data (P, W, D. L, F, A, Pts)
Stat selector - Allows changing the League table to different statistics picked from our features data table (Goals, form, cards, etc)
"Top performer" - A few cards that could tell the user the top performing team(s) in various metrics at the "current state date". These could rotate to make it a bit interesting

# Interactions and what they change (URL params, store)
Date slider will change the date the data is relevant for (we should make it as of 23:59 that evening to be clear that the games of that day have been played. Any games transitioning calendar days will not have been completed at that point)
Stat selector - Allow display of different "features" to list the teams instead of as a standard league table

# Out of scope
Player data
Betting data
