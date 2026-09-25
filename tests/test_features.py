from datetime import date

import pytest
from sqlalchemy import select, text

from percy.analysis.dataset import DatasetLoader
from percy.config import FeatureConfig
from percy.features.builder import FeatureBuilder
from percy.features.state import LeagueTable, PositionBands

CFG = FeatureConfig(form_windows=(2,), goal_windows=(2,), venue_windows=(1,),
                    position_bands=((1, 2), (3, 4)), relegation_places=1, min_games_for_strength=1)


def rows(db, builder):
    t = builder.schema.table
    with db.engine.connect() as conn:
        return {(r.match_id, r.team_id): r for r in conn.execute(select(t))}


@pytest.fixture
def small_league(league):
    """Four teams; two rounds on separate days plus a same-day pair and an upcoming fixture."""
    league.season(10, 2022, [1, 2, 3, 4])
    ids = {
        "a": league.match(10, "2022-08-01 15:00", 1, 2, (2, 0)),
        "b": league.match(10, "2022-08-01 17:30", 3, 4, (1, 1)),
        "c": league.match(10, "2022-08-08 15:00", 2, 1, (0, 3)),
        "d": league.match(10, "2022-08-08 15:00", 4, 3, (2, 1)),
        "e": league.match(10, "2022-08-15 15:00", 1, 3, None),
    }
    return league, ids


def test_first_match_has_no_history(db, small_league):
    _, ids = small_league
    builder = FeatureBuilder(db, CFG)
    builder.build()
    r = rows(db, builder)[(ids["a"], 1)]
    assert r.matches_played_total == 0 and r.form_2_pts is None and r.rest_days is None
    assert r.league_position is None and r.goals_for == 2 and r.result_pts == 3


def test_same_day_results_do_not_leak(db, small_league):
    _, ids = small_league
    builder = FeatureBuilder(db, CFG)
    builder.build()
    r = rows(db, builder)[(ids["b"], 3)]
    assert r.matches_played_total == 0 and r.league_position is None


def test_form_table_and_h2h(db, small_league):
    _, ids = small_league
    builder = FeatureBuilder(db, CFG)
    builder.build()
    r = rows(db, builder)
    upcoming = r[(ids["e"], 1)]
    assert upcoming.form_2_pts == 6 and upcoming.form_2_wins == 2
    assert upcoming.goals_2_gf == 5 and upcoming.goals_2_clean_sheets == 2
    assert upcoming.home_form_1_pts == 3 and upcoming.away_form_1_pts == 3
    assert upcoming.league_position == 1 and upcoming.position_band == 1
    assert upcoming.streak_wins == 2 and upcoming.rest_days == 7
    assert upcoming.goals_for is None and not upcoming.is_finished
    rematch = r[(ids["c"], 1)]
    assert rematch.h2h_played == 1 and rematch.h2h_pts == 3 and rematch.h2h_gf == 2
    assert rematch.h2h_venue_played == 0


def test_similar_opponent_uses_band_at_time(db, small_league):
    _, ids = small_league
    builder = FeatureBuilder(db, CFG)
    builder.build()
    r = rows(db, builder)[(ids["e"], 1)]
    # Team 3 is 3rd (band 2); team 1 beat team 2 on day 2 when team 2 was 4th (band 2).
    assert r.opponent_band == 2 and r.vs_band_played == 1 and r.vs_band_ppg == 3


def test_incremental_build_refreshes_only_pre_result_rows(db, small_league):
    league, ids = small_league
    builder = FeatureBuilder(db, CFG)
    first = builder.build()
    assert first.inserted == 5
    league.finish(ids["e"], (1, 0))
    second = builder.build()
    assert (second.inserted, second.replaced, second.unchanged) == (0, 1, 4)
    assert rows(db, builder)[(ids["e"], 1)].result_pts == 3


def test_changed_columns_require_rebuild(db, small_league):
    FeatureBuilder(db, CFG).build()
    wider = FeatureConfig(form_windows=(2, 3), goal_windows=(2,), venue_windows=(1,), position_bands=CFG.position_bands)
    with pytest.raises(RuntimeError):
        FeatureBuilder(db, wider).build()
    assert FeatureBuilder(db, wider).build(rebuild=True).inserted == 5


def test_match_view_pivots_to_one_row_per_match(db, small_league):
    _, ids = small_league
    FeatureBuilder(db, CFG).build()
    frame = DatasetLoader(db).matches()
    assert len(frame) == 4
    first = frame.set_index("match_id").loc[ids["a"]]
    assert first.result == "H" and first.total_goals == 2 and first.home_team_id == 1
    assert "away_form_2_pts" in frame.columns and "home_elo" in frame.columns
    assert len(DatasetLoader(db).matches(finished=False)) == 1
    with db.engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM v_team_match_features")).scalar() == 10


def test_second_season_carries_form_and_prior_band(db, league):
    league.season(10, 2022, [1, 2])
    league.season(11, 2023, [1, 3])
    league.match(10, "2022-08-01", 1, 2, (1, 0))
    league.match(10, "2022-08-08", 2, 1, (0, 1))
    mid = league.match(11, "2023-08-01", 3, 1, None)
    builder = FeatureBuilder(db, CFG)
    builder.build()
    r = rows(db, builder)
    team1, promoted = r[(mid, 1)], r[(mid, 3)]
    assert team1.form_2_pts == 6 and team1.matches_played_season == 0
    assert team1.prev_season_position == 1 and team1.position_band == 1
    assert promoted.prev_season_position is None and promoted.position_band == 2
    assert promoted.elo < team1.elo


def test_league_table_tiebreaks_and_bands():
    table = LeagueTable([1, 2, 3])
    table.apply(1, 2, 1, 0)
    table.apply(3, 2, 3, 0)
    assert [r.team_id for r in table.standings()] == [3, 1, 2]
    assert table.points_at(1) == 3 and table.goals_per_team_game() == pytest.approx(4 / 4)
    bands = PositionBands(((1, 4), (5, 8)))
    assert bands.band_of(6) == 2 and bands.band_of(None) is None
