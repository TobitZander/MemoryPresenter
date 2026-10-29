import csv
import random
from pathlib import Path

from card import Card
from config import DESCRIPTION_FILENAME, GRID_COLS, GRID_ROWS, IMAGE_ROOT, SUPPORTED_IMAGE_EXTENSIONS


def _read_descriptions(image_dir):
    descriptions = {}
    description_file = image_dir / DESCRIPTION_FILENAME
    if not description_file.exists():
        return descriptions
    with description_file.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            filename = (row.get("filename") or "").strip()
            if filename:
                descriptions[filename] = (row.get("description") or "").strip()
    return descriptions


def load_memory(memory_name, required_cards=None):
    image_dir = IMAGE_ROOT / memory_name
    if not image_dir.exists():
        raise FileNotFoundError(f"Memory-Ordner nicht gefunden: {image_dir}")

    descriptions = _read_descriptions(image_dir)
    grouped = {}
    for file in sorted(image_dir.rglob("*")):
        if not file.is_file() or file.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
            continue
        pair_id = file.stem.split("_")[0].split()[0]
        grouped.setdefault(pair_id, []).append(file)

    required_cards = required_cards or GRID_ROWS * GRID_COLS
    pairs = [files for files in grouped.values() if len(files) >= 2]
    random.shuffle(pairs)
    selected = pairs[: required_cards // 2]
    cards = []
    selected_pairs = [
        (pair_id, files)
        for pair_id, files in grouped.items()
        if files in selected
    ]
    for pair_number, (pair_id, files) in enumerate(selected_pairs, start=1):
        chosen_files = random.sample(files, 2)
        for file in chosen_files:
            relative_path = file.relative_to(IMAGE_ROOT).as_posix()
            cards.append(Card(
                id=len(cards),
                pair_id=str(pair_number),
                image_path=f"/images/{relative_path}",
                description=descriptions.get(file.name, ""),
                display_pair_id=str(pair_number),
            ))
    if len(cards) < required_cards:
        required_cards = len(cards)
    random.shuffle(cards)
    for index, card in enumerate(cards):
        card.id = index
    return cards