"""Put the project root on sys.path and switch on INFO logging.

Imported first by every pipeline script so it runs without installing
the package.
"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
)
