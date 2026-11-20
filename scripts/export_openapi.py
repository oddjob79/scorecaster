"""Write the API's OpenAPI schema to web/openapi.json.

Usage: python scripts/export_openapi.py

Builds the app in memory and saves its schema, so the front end can
generate its typed client from a file. No server is started and no
database is read: producing the schema never queries the database.
"""
import json

import _bootstrap  # noqa: F401

from scorecaster.api.main import create_app
from scorecaster.config import PROJECT_ROOT
from scorecaster.db import Database

SCHEMA_PATH = PROJECT_ROOT / "web" / "openapi.json"


def main() -> None:
    """Write the schema, indented, and print where it went."""
    app = create_app(Database("sqlite://"))
    SCHEMA_PATH.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"wrote {SCHEMA_PATH}")


if __name__ == "__main__":
    main()
