from datetime import date, datetime

from sqlalchemy import func, select

from scorecaster.api import FootballDataOrgProvider, FootballDataParser
from scorecaster.api.http import CachedJsonClient, RateLimiter
from scorecaster.db import ApiResponse, Area, Match, SeasonTeam, Team
from scorecaster.ingest.loader import HistoricalLoader


def test_parser_maps_match_fields(fake_client):
    doc = fake_client.get("competitions/PL/matches", {"season": 2023})
    m = FootballDataParser().match(doc["matches"][0], 2021, 1564)
    assert (m.id, m.home_team_id, m.away_team_id, m.ft_home, m.ft_away, m.ht_home) == (435943, 57, 351, 2, 1, 2)
    assert m.utc_date == datetime(2023, 8, 12, 12, 0)
    assert m.referee == "Michael Oliver" and m.season_id == 1564


def test_parser_maps_competition_and_seasons(fake_client):
    comp = FootballDataParser().competition(fake_client.get("competitions/PL"))
    assert comp.area.code == "ENG"
    assert {s.start_year for s in comp.seasons} == {2022, 2023}
    assert next(s for s in comp.seasons if s.start_year == 2022).winner_team_id == 65


def test_loader_is_idempotent_and_updates_only_unfinished(db, fake_client):
    loader = HistoricalLoader(FootballDataOrgProvider(fake_client), db, today=date(2024, 3, 1))
    first = loader.load("PL", [2023])
    second = loader.load("PL", [2023])
    assert first.inserted > 0 and second.inserted == 0
    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(Match)) == 2
        assert s.scalar(select(func.count()).select_from(SeasonTeam)) == 2
        assert s.get(Team, 57).venue == "Emirates Stadium"
        assert s.get(Area, 2072).name == "England"


def test_refresh_only_requested_for_incomplete_season(db, fake_client):
    HistoricalLoader(FootballDataOrgProvider(fake_client), db, today=date(2024, 3, 1)).load("PL", [2023], True)
    season_calls = [refresh for _, params, refresh in fake_client.calls if params]
    assert season_calls == [True, True]


def test_cached_client_serves_repeats_from_db(db, fake_client):
    cached = CachedJsonClient(fake_client, db)
    cached.get("competitions/PL")
    cached.get("competitions/PL")
    assert len(fake_client.calls) == 1
    cached.get("competitions/PL", refresh=True)
    assert len(fake_client.calls) == 2
    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(ApiResponse)) == 1


def test_rate_limiter_sleeps_when_window_full():
    now = [0.0]
    slept = []
    limiter = RateLimiter(2, 60, clock=lambda: now[0], sleep=lambda t: (slept.append(t), now.__setitem__(0, now[0] + t)))
    limiter.wait()
    limiter.wait()
    limiter.wait()
    assert slept == [60.0]
