"""Rules every calculator, model and league must follow, including new ones.

These tests loop over the registries, so a calculator, table or league
added later is checked automatically.
"""
from sqlalchemy import UniqueConstraint

from scorecaster.config import FeatureConfig
from scorecaster.db import Base
from scorecaster.features.builder import FeatureBuilder
from scorecaster.features.calculators import default_calculators
from scorecaster.features.schema import FeatureTableSchema
from scorecaster.features.source import MatchSource
from scorecaster.features.state import LeagueState, MatchContext
from scorecaster.ingest.fdcuk import CsvLoader
from tests.conftest import (
    PAST_SEASON_CURRENT,
    read_fixture,
    rows,
    scalar,
    season_file,
)

TARGET_COLUMNS = {"goals_for", "goals_against", "result_pts", "is_finished"}


def test_feature_names_are_unique_across_calculators():
    names = [
        name
        for calculator in default_calculators(FeatureConfig())
        for name in calculator.columns()
    ]
    assert len(names) == len(set(names))
    context_columns = set(FeatureTableSchema([]).all_columns)
    assert not context_columns & set(names)


def test_every_calculator_returns_its_columns_for_a_first_match(loaded_db):
    source = MatchSource(loaded_db)
    state = LeagueState(FeatureConfig(), source.seasons(), source.market())
    first_match = source.matches()[0]
    state.start_day([first_match])
    context = MatchContext.for_side(first_match, True, state)
    for calculator in default_calculators(FeatureConfig()):
        features = calculator.compute(context)
        assert set(features) == set(calculator.columns()), calculator


def test_features_never_see_their_own_match_result(loaded_db):
    """Changing a result changes later features, never that match's own."""
    FeatureBuilder(loaded_db, FeatureConfig()).rebuild()
    before = feature_rows(loaded_db)
    changed_id = scalar(
        loaded_db,
        "SELECT id FROM matches WHERE match_date = '2024-08-24' "
        "ORDER BY id LIMIT 1",
    )
    with loaded_db.engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE matches SET ft_home = 0, ft_away = 5, ft_result = 'A' "
            f"WHERE id = {changed_id}"
        )
    FeatureBuilder(loaded_db, FeatureConfig()).rebuild()
    after = feature_rows(loaded_db)

    for key, values in before.items():
        match_id, _, match_date = key
        if match_date <= "2024-08-24":
            unchanged = {
                k: v for k, v in values.items() if k not in TARGET_COLUMNS
            }
            assert unchanged == {
                k: v for k, v in after[key].items()
                if k not in TARGET_COLUMNS
            }, key
    later = [key for key in before if key[2] > "2024-08-24"]
    assert any(before[key] != after[key] for key in later)


def test_every_model_table_has_a_natural_unique_key():
    for table in Base.metadata.sorted_tables:
        has_unique = any(
            isinstance(constraint, UniqueConstraint)
            for constraint in table.constraints
        )
        has_unique_column = any(column.unique for column in table.columns)
        composite_key = len(table.primary_key.columns) > 1
        assert has_unique or has_unique_column or composite_key, table.name


def test_loading_the_same_file_twice_adds_nothing(loaded_db):
    counts = table_counts(loaded_db)
    CsvLoader(loaded_db, PAST_SEASON_CURRENT).load(
        season_file("E0", 2024), read_fixture("mini_E0.csv")
    )
    assert table_counts(loaded_db) == counts


def feature_rows(db) -> dict:
    """Return feature rows keyed by (match id, team id, match date)."""
    with db.engine.connect() as connection:
        result = connection.exec_driver_sql(
            "SELECT * FROM team_match_features"
        )
        names = list(result.keys())
        return {
            (row[0], row[1], str(row[names.index("match_date")])): dict(
                zip(names, row)
            )
            for row in result
        }


def table_counts(db) -> dict:
    """Return the row count of every model table."""
    return {
        table.name: rows(db, f"SELECT COUNT(*) FROM {table.name}")[0][0]
        for table in Base.metadata.sorted_tables
    }
