import os
import sys
from pathlib import Path

GRID_ROWS = 3
GRID_COLS = 4

TEAM_COUNT = 10

ROUND_TIME_SECONDS = 45

# Seconds that two non-matching cards remain visible.
AUTO_CLOSE_DELAY = 8.0

CARD_BACK_IMAGE = "card-back.svg"
TITLE_PAGE_FILENAME = "title_page.txt"
DESCRIPTION_FILENAME = "descriptions.csv"
RANDOMIZE_ALL_MEMORIES = False

TEAM_NAMES = [f"Tisch {number}" for number in range(1, TEAM_COUNT + 1)]

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".svg", ".webp"}

# Resources remain outside the executable. Override with WEDDING_MEMORY_RESOURCES
# when the image folder is stored somewhere else.
if getattr(sys, "frozen", False):
    default_resource_root = Path(sys.executable).resolve().parent / "resources"
else:
    default_resource_root = Path(__file__).resolve().parent / "resources"

RESOURCE_ROOT = Path(os.environ.get("WEDDING_MEMORY_RESOURCES", default_resource_root))
TITLE_PAGE_PATH = RESOURCE_ROOT / TITLE_PAGE_FILENAME
RULES_PATH = RESOURCE_ROOT / "rules.txt"


def discover_memory_sets():
    return sorted(
        path.name
        for path in RESOURCE_ROOT.iterdir()
        if path.is_dir() and path.name.lower().startswith("memory")
    )


MEMORY_SETS = discover_memory_sets()
