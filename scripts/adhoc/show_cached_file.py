"""Print the header and first rows of a file stored in the downloads table.

The database is opened read-only, so this never changes anything. The
name is matched against the end of the stored URL.

    python scripts/adhoc/show_cached_file.py fixtures.csv --rows 5
"""
import argparse
import sqlite3

import _bootstrap  # noqa: F401

from scorecaster.config import Settings
from scorecaster.ingest.fdcuk.reader import decode_csv


def main() -> None:
    """Print one stored file's columns, row count and first few lines."""
    args = parse_args()
    url, body = find_download(args.name)
    lines = decode_csv(body).splitlines()
    header = lines[0].split(",")
    print(f"{url}: {len(body)} bytes, {len(lines) - 1} rows")
    print(f"{len(header)} columns: {', '.join(header)}")
    for line in lines[1:args.rows + 1]:
        print(line)


def parse_args() -> argparse.Namespace:
    """Read the file name and how many rows to show."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", help="end of the URL, e.g. fixtures.csv")
    parser.add_argument("--rows", type=int, default=3, help="rows to show")
    return parser.parse_args()


def find_download(name: str) -> tuple[str, bytes]:
    """Return the URL and body of the one stored file ending in `name`."""
    db_uri = f"file:{Settings.from_env().db_path}?mode=ro"
    with sqlite3.connect(db_uri, uri=True) as connection:
        matches = connection.execute(
            "SELECT url, body FROM downloads WHERE url LIKE ?",
            (f"%/{name}",),
        ).fetchall()
    if len(matches) != 1:
        raise SystemExit(f"{len(matches)} stored files end in /{name}")
    return matches[0]


if __name__ == "__main__":
    main()
