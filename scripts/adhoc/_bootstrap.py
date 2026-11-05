"""Put the project root on sys.path and switch on INFO logging.

Imported first by every adhoc script so it runs without installing the
package, from any working directory.
"""
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
)
