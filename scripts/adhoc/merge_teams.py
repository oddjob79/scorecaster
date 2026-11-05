"""Merge teams stored under two spellings into one.

Each pair is VARIANT:CANONICAL team ids. For each pair, the variant's
matches are moved to the canonical team, the variant's name becomes a
team alias (so future loads map it straight to the canonical team), and
the variant's teams row is deleted.

Without --apply the changes are only printed. With --apply they are made
in one transaction. Rebuild the features afterwards, since the feature
table still holds the old team ids.

    python scripts/adhoc/merge_teams.py 752:785 963:965
    python scripts/adhoc/merge_teams.py 752:785 963:965 --apply
"""
import argparse
from dataclasses import dataclass

from sqlalchemy import text

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.db import Database

COUNT_MATCHES = text("""
    SELECT COUNT(*) FROM matches
    WHERE home_team_id = :variant OR away_team_id = :variant
""")
# Matches that would collide with an existing match once remapped.
COLLISIONS = text("""
    SELECT COUNT(*) FROM matches moved
    JOIN matches kept
      ON kept.competition_id = moved.competition_id
     AND kept.match_date = moved.match_date
     AND kept.home_team_id = CASE WHEN moved.home_team_id = :variant
                                  THEN :canonical
                                  ELSE moved.home_team_id END
     AND kept.away_team_id = CASE WHEN moved.away_team_id = :variant
                                  THEN :canonical
                                  ELSE moved.away_team_id END
    WHERE (moved.home_team_id = :variant OR moved.away_team_id = :variant)
      AND kept.id != moved.id
""")
MOVE_HOME = text(
    "UPDATE matches SET home_team_id = :canonical "
    "WHERE home_team_id = :variant"
)
MOVE_AWAY = text(
    "UPDATE matches SET away_team_id = :canonical "
    "WHERE away_team_id = :variant"
)
MOVE_ALIASES = text(
    "UPDATE team_aliases SET team_id = :canonical "
    "WHERE team_id = :variant"
)
EXISTING_ALIAS = text(
    "SELECT team_id FROM team_aliases "
    "WHERE country = :country AND alias = :alias"
)
# OR IGNORE only skips the row when it already maps to the canonical team;
# plan_merge refuses any alias that maps elsewhere.
ADD_ALIAS = text(
    "INSERT OR IGNORE INTO team_aliases (country, alias, team_id) "
    "VALUES (:country, :alias, :canonical)"
)
DELETE_TEAM = text("DELETE FROM teams WHERE id = :variant")


@dataclass(frozen=True)
class Merge:
    """One variant team to fold into its canonical team."""

    variant_id: int
    canonical_id: int
    country: str
    variant_name: str
    canonical_name: str
    matches: int

    @property
    def params(self) -> dict:
        """Return the SQL parameters for this merge."""
        return {
            "variant": self.variant_id,
            "canonical": self.canonical_id,
            "country": self.country,
            "alias": self.variant_name,
        }


def main() -> None:
    """Check every pair, print the plan, and apply it if asked."""
    args = parse_args()
    db = Database.for_path(Settings.from_env().db_path)
    with db.session() as session:
        merges = [plan_merge(session, pair) for pair in args.pairs]
    for merge in merges:
        print(
            f"{merge.country}: {merge.variant_name} ({merge.variant_id}) "
            f"-> {merge.canonical_name} ({merge.canonical_id}), "
            f"{merge.matches} matches moved, alias added"
        )
    if not args.apply:
        print("\npreview only; add --apply to make these changes")
        return
    with db.session() as session:
        for merge in merges:
            apply_merge(session, merge)
    print(f"\nmerged {len(merges)} teams; now run "
          "scripts/build_features.py --rebuild")


def parse_args() -> argparse.Namespace:
    """Read the VARIANT:CANONICAL pairs and --apply."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pairs", nargs="+", help="VARIANT:CANONICAL team ids, e.g. 752:785"
    )
    parser.add_argument(
        "--apply", action="store_true", help="make the changes"
    )
    return parser.parse_args()


def plan_merge(session, pair: str) -> Merge:
    """Look up both teams and refuse any merge that isn't safe.

    Both teams must exist, be different, share a country; no moved match
    may collide with one the canonical team already has; and the variant
    name must not already be an alias of a different team.
    """
    variant_id, canonical_id = (int(part) for part in pair.split(":"))
    if variant_id == canonical_id:
        raise SystemExit(f"{pair}: the two ids are the same")
    variant = _team(session, variant_id)
    canonical = _team(session, canonical_id)
    if variant.country != canonical.country:
        raise SystemExit(
            f"{pair}: {variant.name} ({variant.country}) and "
            f"{canonical.name} ({canonical.country}) are in different "
            "countries"
        )
    params = {"variant": variant_id, "canonical": canonical_id}
    if session.execute(COLLISIONS, params).scalar():
        raise SystemExit(f"{pair}: some matches would be duplicated")
    aliased_to = session.execute(
        EXISTING_ALIAS, {"country": variant.country, "alias": variant.name}
    ).scalar()
    if aliased_to is not None and aliased_to != canonical_id:
        raise SystemExit(
            f"{pair}: '{variant.name}' is already an alias of team "
            f"{aliased_to}; remove that alias first"
        )
    return Merge(
        variant_id=variant_id,
        canonical_id=canonical_id,
        country=variant.country,
        variant_name=variant.name,
        canonical_name=canonical.name,
        matches=session.execute(COUNT_MATCHES, params).scalar(),
    )


def apply_merge(session, merge: Merge) -> None:
    """Move the variant's matches and aliases, record it, delete it."""
    for statement in (
        MOVE_HOME, MOVE_AWAY, MOVE_ALIASES, ADD_ALIAS, DELETE_TEAM
    ):
        session.execute(statement, merge.params)


def _team(session, team_id: int):
    """Return a team's id, country and name, or stop if it doesn't exist."""
    row = session.execute(
        text("SELECT id, country, name FROM teams WHERE id = :id"),
        {"id": team_id},
    ).first()
    if row is None:
        raise SystemExit(f"no team with id {team_id}")
    return row


if __name__ == "__main__":
    main()
