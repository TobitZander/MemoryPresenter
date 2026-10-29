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
DESCRIPTION_FILENAME = "descriptions.csv"
RANDOMIZE_ALL_MEMORIES = False

TEAM_NAMES = [f"Tisch {number}" for number in range(1, TEAM_COUNT + 1)]

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".svg", ".webp"}

# Images remain outside the executable. Override with WEDDING_MEMORY_IMAGES
# when the image folder is stored somewhere else.
if getattr(sys, "frozen", False):
    default_image_root = Path(sys.executable).resolve().parent / "images"
else:
    default_image_root = Path(__file__).resolve().parent / "images"

IMAGE_ROOT = Path(os.environ.get("WEDDING_MEMORY_IMAGES", default_image_root))


def discover_memory_sets():
    return sorted(
        path.name
        for path in IMAGE_ROOT.iterdir()
        if path.is_dir() and path.name.lower().startswith("memory")
    )


MEMORY_SETS = discover_memory_sets()
