"""Name the football-data.co.uk columns and what each one holds.

Every CSV on the site follows one naming scheme. This module is the only place
that knows it: which columns hold results and stats, and how an odds column
name such as ``PSCH`` breaks down into bookmaker, timing and selection.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

# Older files and the extra-league files name some columns differently.
RENAMED_COLUMNS = {
    "HG": "FTHG",
    "AG": "FTAG",
    "Res": "FTR",
    "Home": "HomeTeam",
    "Away": "AwayTeam",
}

REQUIRED_COLUMNS = ["Date", "HomeTeam", "AwayTeam"]

# CSV column -> matches table column
NUMBER_COLUMNS = {
    "FTHG": "ft_home",
    "FTAG": "ft_away",
    "HTHG": "ht_home",
    "HTAG": "ht_away",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_on_target",
    "AST": "away_shots_on_target",
    "HF": "home_fouls",
    "AF": "away_fouls",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellows",
    "AY": "away_yellows",
    "HR": "home_reds",
    "AR": "away_reds",
}
TEXT_COLUMNS = {
    "FTR": "ft_result",
    "HTR": "ht_result",
    "Referee": "referee",
}

# Read for context (Time, Season, handicap lines) or deliberately ignored.
OTHER_COLUMNS = {
    "Div", "Time", "Country", "League", "Season",
    "AHh", "AHCh", "BbAHh",
    "Bb1X2", "BbOU", "BbAH",
    "HxG", "AxG", "HFKC", "AFKC",
}

# Odds column prefix -> bookmaker name stored in the odds table
STORED_BOOKMAKERS = {
    "PS": "pinnacle",       # 1X2
    "P": "pinnacle",        # over/under and Asian handicap
    "B365": "bet365",
    "BFE": "betfair_exchange",
    "Avg": "market_avg",
    "BbAv": "market_avg",   # Betbrain average, to 2018/19
    "Max": "market_max",
    "BbMx": "market_max",   # Betbrain maximum, to 2018/19
}
SKIPPED_BOOKMAKERS = [
    "1XB", "BFD", "BMGM", "SKB", "BW", "IW", "LB", "WH",
    "VC", "SJ", "SB", "GB", "BS", "BF", "BV", "CL", "PP",
]

# Selection code at the end of an odds column -> (market, selection)
SELECTIONS = {
    "H": ("1X2", "home"),
    "D": ("1X2", "draw"),
    "A": ("1X2", "away"),
    ">2.5": ("OU", "over"),
    "<2.5": ("OU", "under"),
    "AHH": ("AH", "home"),
    "AHA": ("AH", "away"),
}


def _odds_pattern(prefixes: list[str]) -> re.Pattern[str]:
    """Build the regex for ``{prefix}{C if closing}{selection}`` names."""
    longest_first = sorted(prefixes, key=len, reverse=True)
    selections = sorted(SELECTIONS, key=len, reverse=True)
    return re.compile(
        rf"^({'|'.join(map(re.escape, longest_first))})"
        rf"(C?)"
        rf"({'|'.join(map(re.escape, selections))})$"
    )


_STORED_ODDS = _odds_pattern(list(STORED_BOOKMAKERS))
_SKIPPED_ODDS = _odds_pattern(SKIPPED_BOOKMAKERS)


@dataclass(frozen=True)
class OddsColumn:
    """One stored odds column, decoded.

    ``PSCH`` -> pinnacle, closing, 1X2, home
    """

    name: str
    bookmaker: str
    timing: str
    market: str
    selection: str

    @classmethod
    def parse(cls, name: str) -> OddsColumn | None:
        """Decode a stored bookmaker's odds column, else return None."""
        match = _STORED_ODDS.match(name)
        if match is None:
            return None
        prefix, closing, code = match.groups()
        market, selection = SELECTIONS[code]
        timing = "closing" if closing else "pre_match"
        return cls(name, STORED_BOOKMAKERS[prefix], timing, market, selection)


def unknown_columns(columns: list[str]) -> list[str]:
    """Return the columns this package neither reads nor deliberately skips.

    A non-empty result means the site has added something new, e.g.
    ``['Div', 'PSH', 'XYZ'] -> ['XYZ']``.
    """
    known = {*REQUIRED_COLUMNS, *NUMBER_COLUMNS, *TEXT_COLUMNS, *OTHER_COLUMNS}
    return [
        name for name in columns
        if name not in known
        and not _STORED_ODDS.match(name)
        and not _SKIPPED_ODDS.match(name)
    ]
