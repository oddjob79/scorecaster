1. You write `design/calendar-brief.md` from the template. Starting points:
   - competition and season pickers, as on the team page;
   - a month view with the days that had matches marked, and each day's results listed;
   - filtering to one team's matches;
   - links from a date to the league page as at that date, and from a team to its team page.
2. Query real data for one league-season, e.g. Premier League 2024/25: every match with date, kick-off time, teams, full-time and half-time score.
3. Produce `design/calendar.html`.
4. You review it; revise until approved.

# Key info
bbc.co.uk/football and myfootballfacts.com both have scrolling calendars which show today and the next couple of days, as well as the ability to "go back in time". This looks nice with mff.com but the bbc allows for calendar use which is nicer. This kind of setup is what we should be looking for

# Who the page is for
General users of the site to view previously completed and upcoming matches

# The 2–3 questions it answers
What games were / will be played on a particular day?
What were the scores?
What was the key game stats?

# Its components in priority order
Calendar picker
Competition filter (multiple checkboxes)
Matches (scores, if in the past) - Click to open accordion showing match stats
Match stats (hidden behind accordion)

# The data each component shows
Calendar picker
Competition filter (multiple checkboxes)
Matches (scores, if in the past) - Click to open accordion showing match stats
Match stats (hidden behind accordion)
    If in past:
    - h/t scorep, shots, corners, cards and referee, and its pre-match and closing odds
    - (nice to have) - team's starting / ending league position
    If in future:
    - current team info next to one another (with a nice vs in the middle!) - as per the team page without the slider
    - chart with league position, home record, form, goals etc for both teams overlaid with eachother


# Interactions and what they change (URL params, store)
Open details of each match - suggested accordion component, but could be new page instead (which may work better)

# Out of scope
