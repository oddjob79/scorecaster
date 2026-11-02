### Scorecaster Project for forecasting outcomes of upcoming football matches and their probablilities of success

The end goal of this project is to use historical football results in association with related factors to be able to create a model that will allow us to:

a) predict the outcome of an upcoming fixture (home win, away win, draw)
b) predict total goals per game (above or below 2.5 goals)
c) estimate a probability of each prediction
d) utilise this in association with betting odds to locate good value bets with a high probability of success
e) suggest a strategy of which bets to place in any given week to give the highest chance of financial reward


# Initial project scope to achieve this below

What needs to be done:
Create a database to house football statistics
Why?
To use metrics to analyse and discover the most likely factors influencing the result of an upcoming fixture.
The end goal is to be able to more accurately predict outcomes of upcoming fixtures using these factors.
How will this be done?
To capture enough historical data to be able to retrospectively analyse the relevant data, to be able to determine what factors most influenced the result.
Limitations:
We will omit player data at this stage, using only team data. Relying on prior results and data drawn from this, such as prior meetings (head to head), form, home and away form, attacking / defensive record, etc.
What data needs to be captured?
The data will be captured from the football-data.org v4 API
Area
Competition
Teams
Matches

Start off by building a script which will create a sqlite database and relevant tables to house this data. Once stored, it should remain where it is without being overwritten, so this should be a one-off job.
I want to be able to query the data from the local tables rather than having to access the API each time to save on the number of requests I’m sending.
We need an additional table to store all the stats relating to each team which they would have had prior to the match played. So, all relevant data gathered for dates prior to the date of the match will need to be consolidated into relevant fields and stored. We don’t know which factors will impact the game most, so I think we should store a wide range of data here.
For example, we would want to store the team’s previous result, previous home result, previous away result, previous total form (over 4 games, 6 games, 8 games) previous home form (4, 6, 8 games), how many wins in these periods, how many goals scored and conceded in this period and longer, prior form against this opposition, prior form against teams in a similar league position as to where their opponents would sit at that time, opponents’ form (similar to above).
Add in any other factors that are known to have a high impact and dismiss those that don’t.
The end result of this table is that we will need to perform some regression analysis (I think that’s what it’s called) to identify what are the most prominent factors impacting the result. I want to know what other techniques are available to do this.
Then I want a set of python scripts which will extrapolate the prior results from the database and build this table up as we go.
I want alternative suggestions to this architecture if there are better ways to handle it.
Ask me questions to clarify the problem before spending additional time and resources on it
Do not contact the API at this point. If any sample data is needed to provide a complete answer then ask for clarification.
Build as much of the solution as possible inside the /percy directory using the init-data-populator branch
Leave concise docstrings on the methods / functions, but do not leave massive explanations. A readme should be provided showing what has been done.
Try to make as much of the code into classes as possible using OOP and SOLID principles

# Next steps and review

After the initial skeleton project has been created and a path forward has been suggested, let's take stock and make sure we have the correct building blocks in place to achieve our ends

- Are we collecting the right data needed to make accurate predictions and to calculate their probabilities?
- Are there other tools we can use to help us achieve what we want, that we have not considered yet?
- Should we consider a multi-step path to achieve what we want?
- Paid for APIs can be considered, but the initial PoC should be based on free services. Web scrapers can be considered as an intermediary opportunity to gather stats
- Additional stats that have been more and more prevalent in recent years (such as xG, running stats, possession stats, touches in opponents box, etc) can be sourced if these are thought to have enough of a bearing on the success of this project
- I'm happy to consider the use of MILP tools such as HiGHS to assist in generating these probabilities

