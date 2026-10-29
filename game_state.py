import random
import threading
import time
import colorsys

from memory_loader import load_memory
from config import (
    AUTO_CLOSE_DELAY,
    GRID_COLS,
    GRID_ROWS,
    MEMORY_SETS,
    RANDOMIZE_ALL_MEMORIES,
    ROUND_TIME_SECONDS,
    TEAM_COUNT,
    TEAM_NAMES,
)


class GameState:

    def __init__(self):

        if not MEMORY_SETS:
            raise ValueError("Keine Memory-Ordner im images-Ordner gefunden.")
        self.memory_order = MEMORY_SETS.copy()
        self.randomize_all_memories = RANDOMIZE_ALL_MEMORIES
        if self.randomize_all_memories:
            random.shuffle(self.memory_order)
        self.current_memory = self.memory_order[0]

        self.cards = []
        self.memory_boards = {}

        self.open_cards = []

        self.current_team = 0

        self.scores = [0] * TEAM_COUNT
        self.total_scores = [0] * TEAM_COUNT
        self.team_names = TEAM_NAMES.copy()
        self.grid_rows = GRID_ROWS
        self.grid_cols = GRID_COLS
        self.configured_grid_rows = GRID_ROWS
        self.configured_grid_cols = GRID_COLS
        self.round_time_seconds = ROUND_TIME_SECONDS
        self.auto_close_delay = AUTO_CLOSE_DELAY
        self.memory_index = 0
        self.tiebreaker = False
        self.tiebreaker_teams = []
        self.tiebreak_scores = [0] * TEAM_COUNT
        self.tiebreak_pending = False

        self.time_remaining = self.round_time_seconds

        self.pending_col = None
        self.pending_row = None

        self.selected_card = None

        self.rules_visible = False
        self.winner = None
        self.mismatch_until = None
        self.mismatch_paused_remaining = None
        self.match_status = None
        self.selected_column = None
        self.selected_row = None
        self.hovered_card = None
        self.last_opened_card = None
        self.description_card_indices = []
        self.zoom_card = None
        self.zoom_scale = 1.0
        self.zoom_offset_x = 0.0
        self.zoom_offset_y = 0.0
        self.theme = "light"
        self.paused = True
        self.lock = threading.RLock()

        self.load_memory(self.current_memory)

    def load_memory(self, memory_name, preserve_board=True):
        if memory_name not in MEMORY_SETS:
            raise ValueError(f"Unbekanntes Memory: {memory_name}")
        with self.lock:
            if preserve_board and not self.tiebreaker and self.cards and self.current_memory in MEMORY_SETS:
                self.memory_boards[self.current_memory] = (
                    self.grid_rows,
                    self.grid_cols,
                    self.cards,
                )
            self.current_memory = memory_name
            self.memory_index = self.memory_order.index(memory_name)
            saved_board = self.memory_boards.get(memory_name) if preserve_board else None
            if saved_board is not None:
                self.grid_rows, self.grid_cols, self.cards = saved_board
                slot_count = self.grid_rows * self.grid_cols
                self.cards = list(self.cards[:slot_count])
                self.cards.extend([None] * (slot_count - len(self.cards)))
            else:
                self.grid_rows = self.configured_grid_rows
                self.grid_cols = self.configured_grid_cols
                self.cards = load_memory(memory_name, self.grid_rows * self.grid_cols)
                self.cards.extend([None] * (self.grid_rows * self.grid_cols - len(self.cards)))
                if preserve_board:
                    self.memory_boards[memory_name] = (
                        self.grid_rows,
                        self.grid_cols,
                        self.cards,
                    )
                random.shuffle(self.cards)
            pair_ids = []
            for card in self.cards:
                if card is None:
                    continue
                if card.pair_id not in pair_ids:
                    pair_ids.append(card.pair_id)
            random.shuffle(pair_ids)
            pair_colors = {}
            for card in self.cards:
                if card is None:
                    continue
                pair_index = pair_ids.index(card.pair_id)
                if card.pair_id in pair_colors:
                    card.pair_color = pair_colors[card.pair_id]
                    continue
                hue = (pair_index / max(len(pair_ids), 1) + random.random() * 0.08) % 1
                red, green, blue = colorsys.hsv_to_rgb(hue, 0.52, 0.82)
                pair_colors[card.pair_id] = (
                    f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"
                )
                card.pair_color = pair_colors[card.pair_id]
            self.open_cards = [
                card for card in self.cards
                if card is not None and card.open and not card.matched
            ]
            self.mismatch_until = None
            self.mismatch_paused_remaining = None
            self.match_status = None
            self.winner = None
            self.selected_column = None
            self.selected_row = None
            self.hovered_card = None
            self.last_opened_card = None
            self.description_card_indices = []
            self.zoom_card = None
            self.zoom_scale = 1.0
            self.zoom_offset_x = 0.0
            self.zoom_offset_y = 0.0
            self.paused = True
            self.reset_timer()

    def reset_timer(self):

        self.time_remaining = self.round_time_seconds

    def next_team(self):
        with self.lock:
            eligible = self.tiebreaker_teams if self.tiebreaker else range(len(self.team_names))
            eligible = list(eligible)
            self.current_team = eligible[(eligible.index(self.current_team) + 1) % len(eligible)]
            self.reset_timer()

    def add_point(self):

        self.scores[self.current_team] += 1
        self.total_scores[self.current_team] += 1
        if self.tiebreaker:
            self.tiebreak_scores[self.current_team] += 1

    def calculate_index(self, col, row):

        return row * self.grid_cols + col

    def remove_presented_matches(self):
        if not any(card is not None and card.matched for card in self.cards):
            return
        self.cards = [
            None if card is not None and card.matched else card
            for card in self.cards
        ]
        self.match_status = None

    def open_card(self, card_index):
        with self.lock:
            if not 0 <= card_index < len(self.cards):
                return False
            if self.mismatch_until is not None:
                return False
            card = self.cards[card_index]
            if card is None:
                return False

            if card.open or card.matched or len(self.open_cards) >= 2:
                return False

            self.remove_presented_matches()
            if not self.open_cards:
                self.match_status = None
                self.description_card_indices = []
            card.open = True
            self.open_cards.append(card)
            self.last_opened_card = card_index
            self.description_card_indices.append(card_index)
            return True

    def check_match(self):
        with self.lock:
            if len(self.open_cards) != 2:
                return None

            a, b = self.open_cards

            if a.pair_id == b.pair_id:
                self.match_status = "match"
                a.matched = True
                b.matched = True
                self.add_point()
                eligible_teams = self.tiebreaker_teams if self.tiebreaker else list(range(len(self.team_names)))
                self.current_team = eligible_teams[
                    (eligible_teams.index(self.current_team) + 1) % len(eligible_teams)
                ]
                self.reset_timer()
                self.open_cards.clear()
                if all(card is None or card.matched for card in self.cards):
                    self.paused = True
                    if self.tiebreaker or self.memory_index >= len(self.memory_order) - 1:
                        eligible = self.tiebreaker_teams if self.tiebreaker else range(len(self.team_names))
                        eligible = list(eligible)
                        score_values = self.tiebreak_scores if self.tiebreaker else self.total_scores
                        highest_score = max(score_values[index] for index in eligible)
                        winners = [
                            index for index in eligible
                            if score_values[index] == highest_score
                        ]
                        self.winner = winners
                        self.tiebreak_pending = len(winners) > 1
                        self.tiebreaker = False
                        self.tiebreaker_teams = []
                return True

            self.match_status = "mismatch"
            self.mismatch_until = time.monotonic() + self.auto_close_delay
            if self.zoom_card is not None:
                self.mismatch_paused_remaining = self.auto_close_delay
                self.mismatch_until = None
            return False

    def set_selection(self, column=None, row=None):
        with self.lock:
            self.selected_column = column
            self.selected_row = row

    def set_hovered_card(self, card_index=None):
        with self.lock:
            self.hovered_card = card_index

    def set_zoom(self, card_index):
        with self.lock:
            if card_index is not None and (
                not 0 <= card_index < len(self.cards)
                or not (self.cards[card_index].open or self.cards[card_index].matched)
            ):
                return False
            self.zoom_card = card_index
            if card_index is None:
                if self.mismatch_paused_remaining is not None:
                    self.mismatch_until = time.monotonic() + self.mismatch_paused_remaining
                    self.mismatch_paused_remaining = None
                self.zoom_scale = 1.0
                self.zoom_offset_x = 0.0
                self.zoom_offset_y = 0.0
            elif self.mismatch_until is not None:
                self.mismatch_paused_remaining = max(
                    0.0, self.mismatch_until - time.monotonic()
                )
                self.mismatch_until = None
            return True

    def set_zoom_transform(self, scale, offset_x, offset_y):
        with self.lock:
            if self.zoom_card is None:
                return False
            self.zoom_scale = min(8.0, max(1.0, float(scale)))
            self.zoom_offset_x = float(offset_x)
            self.zoom_offset_y = float(offset_y)
            return True

    def close_non_matching(self):
        with self.lock:
            for card in self.cards:
                if card is not None and card.open and not card.matched:
                    card.open = False
            self.open_cards.clear()
            self.mismatch_until = None
            self.mismatch_paused_remaining = None
            self.last_opened_card = None
            self.match_status = None
            self.description_card_indices = []

    def tick(self):
        with self.lock:
            if self.paused or self.zoom_card is not None or self.rules_visible or self.match_status == "match":
                return
            if self.mismatch_until is not None and time.monotonic() >= self.mismatch_until:
                self.close_non_matching()
                self.next_team()
                self.reset_timer()
            if self.winner is not None:
                return
            self.time_remaining -= 1
            if self.time_remaining <= 0:
                self.close_non_matching()
                self.next_team()
                self.reset_timer()

    def reset_game(self):
        with self.lock:
            self.scores = [0] * len(self.team_names)
            self.total_scores = [0] * len(self.team_names)
            self.current_team = 0
            self.tiebreaker = False
            self.tiebreaker_teams = []
            self.tiebreak_scores = [0] * len(self.team_names)
            self.tiebreak_pending = False
            self.memory_boards.clear()
            self.cards = []
            self.memory_order = MEMORY_SETS.copy()
            if self.randomize_all_memories:
                random.shuffle(self.memory_order)
            self.load_memory(self.current_memory)

    def to_dict(self):
        with self.lock:
            return {
                "memory": self.current_memory,
                "cards": [card.to_dict() if card is not None else None for card in self.cards],
                "active_team": self.current_team,
                "team_names": self.team_names,
                "scores": self.total_scores,
                "total_scores": self.total_scores,
                "time": self.time_remaining,
                "mismatch_time": (
                    self.mismatch_paused_remaining
                    if self.mismatch_paused_remaining is not None
                    else max(0.0, self.mismatch_until - time.monotonic())
                    if self.mismatch_until is not None
                    else None
                ),
                "rules_visible": self.rules_visible,
                "winner": self.winner,
                "grid_rows": self.grid_rows,
                "grid_cols": self.grid_cols,
                "round_time_seconds": self.round_time_seconds,
                "auto_close_delay": self.auto_close_delay,
                "selected_column": self.selected_column,
                "selected_row": self.selected_row,
                "hovered_card": self.hovered_card,
                "last_opened_card": self.last_opened_card,
                "description_card_indices": self.description_card_indices,
                "match_status": self.match_status,
                "zoom_card": self.zoom_card,
                "zoom_scale": self.zoom_scale,
                "zoom_offset_x": self.zoom_offset_x,
                "zoom_offset_y": self.zoom_offset_y,
                "theme": self.theme,
                "paused": self.paused,
                "memory_index": self.memory_index,
                "memory_sets": MEMORY_SETS,
                "randomize_all_memories": self.randomize_all_memories,
                "tiebreaker": self.tiebreaker,
                "tiebreaker_teams": self.tiebreaker_teams,
                "tiebreak_scores": self.tiebreak_scores,
                "tiebreak_pending": self.tiebreak_pending,
                "visible_teams": (
                    self.tiebreaker_teams
                    if self.tiebreaker
                    else self.winner
                    if self.tiebreak_pending and self.winner
                    else list(range(len(self.team_names)))
                ),
            }

    def start_tiebreak(self):
        with self.lock:
            if not self.tiebreak_pending or not self.winner:
                return False
            self.tiebreaker = True
            self.tiebreaker_teams = self.winner.copy()
            self.tiebreak_scores = [0] * len(self.team_names)
            self.tiebreak_pending = False
            self.winner = None
            self.memory_order = [random.choice(MEMORY_SETS)]
            self.memory_index = -1
            self.current_team = self.tiebreaker_teams[0]
            self.load_memory(self.memory_order[0], preserve_board=False)
            return True

    def skip_memory(self):
        with self.lock:
            if self.tiebreaker or self.memory_index >= len(self.memory_order) - 1:
                return False
            self.load_memory(self.memory_order[self.memory_index + 1])
            return True

    def update_settings(self, settings):
        with self.lock:
            rows = int(settings["grid_rows"])
            cols = int(settings["grid_cols"])
            team_count = int(settings["team_count"])
            round_time = int(settings["round_time_seconds"])
            auto_close = float(settings["auto_close_delay"])
            randomize = settings.get("randomize_all_memories", self.randomize_all_memories)
            if isinstance(randomize, str):
                randomize = randomize.lower() == "true"
            if rows < 1 or cols < 1 or rows * cols % 2:
                raise ValueError("Das Spielfeld muss mindestens zwei und eine gerade Kartenanzahl haben.")
            if team_count < 1 or round_time < 1 or auto_close < 0:
                raise ValueError("Teams und Zeiten müssen positive Werte sein.")
            self.grid_rows = rows
            self.grid_cols = cols
            self.configured_grid_rows = rows
            self.configured_grid_cols = cols
            self.round_time_seconds = round_time
            self.auto_close_delay = auto_close
            self.randomize_all_memories = bool(randomize)
            self.memory_order = MEMORY_SETS.copy()
            if self.randomize_all_memories:
                random.shuffle(self.memory_order)
            old_scores = self.total_scores
            self.team_names = [f"Tisch {number}" for number in range(1, team_count + 1)]
            self.total_scores = (old_scores + [0] * team_count)[:team_count]
            self.scores = self.total_scores.copy()
            self.current_team %= team_count
            slot_count = rows * cols
            self.cards = list(self.cards[:slot_count])
            self.cards.extend([None] * (slot_count - len(self.cards)))
            self.grid_rows = rows
            self.grid_cols = cols
            self.configured_grid_rows = rows
            self.configured_grid_cols = cols
            self.open_cards = [
                card for card in self.cards
                if card is not None and card.open and not card.matched
            ]
            self.memory_boards[self.current_memory] = (
                self.grid_rows,
                self.grid_cols,
                self.cards,
            )
