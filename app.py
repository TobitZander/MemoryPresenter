import threading
import time
import webbrowser

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO

from config import CARD_BACK_IMAGE, IMAGE_ROOT, MEMORY_SETS
from countdown import timer_loop
from game_state import GameState

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")
game = GameState()


@app.route("/")
def moderator():
    return render_template("moderator.html")


@app.route("/moderator")
def moderator_alias():
    return moderator()


@app.route("/display")
def display():
    return render_template("display.html")


@app.route("/images/<memory_name>/<path:filename>")
def image(memory_name, filename):
    return send_from_directory(IMAGE_ROOT / memory_name, filename)


@app.route("/card-back")
def card_back():
    return send_from_directory(IMAGE_ROOT, CARD_BACK_IMAGE)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(IMAGE_ROOT, "favicon.ico")


def broadcast():
    socketio.emit("state", game.to_dict())


@socketio.on("request_state")
@socketio.on("get_state")
def request_state():
    broadcast()


@socketio.on("open_card")
def open_card(data):
    try:
        card_index = int(data["card"])
    except (KeyError, TypeError, ValueError):
        return
    if game.open_card(card_index):
        game.paused = False
        game.check_match()
    broadcast()


@socketio.on("selection")
def selection(data):
    column = data.get("column") if isinstance(data, dict) else None
    row = data.get("row") if isinstance(data, dict) else None
    if not isinstance(column, int) or not 0 <= column < game.to_dict()["grid_cols"]:
        column = None
    if not isinstance(row, int) or not 0 <= row < game.to_dict()["grid_rows"]:
        row = None
    game.set_selection(column, row)
    if column is not None or row is not None:
        game.paused = False
    broadcast()


@socketio.on("hover_card")
def hover_card(data):
    card_index = data.get("card") if isinstance(data, dict) else None
    if not isinstance(card_index, int) or not 0 <= card_index < len(game.cards):
        card_index = None
    elif game.cards[card_index] is None:
        card_index = None
    if card_index is not None:
        game.paused = False
        if game.match_status == "match":
            game.match_status = None
    game.set_hovered_card(card_index)
    broadcast()


@socketio.on("zoom")
def zoom(data):
    card_index = data.get("card") if isinstance(data, dict) else None
    if card_index is not None:
        try:
            card_index = int(card_index)
        except (TypeError, ValueError):
            return
    if game.set_zoom(card_index):
        broadcast()


@socketio.on("zoom_transform")
def zoom_transform(data):
    if not isinstance(data, dict):
        return
    try:
        scale = float(data["scale"])
        offset_x = float(data["offset_x"])
        offset_y = float(data["offset_y"])
    except (KeyError, TypeError, ValueError):
        return
    if game.set_zoom_transform(scale, offset_x, offset_y):
        broadcast()


@socketio.on("next_team")
def next_team():
    game.next_team()
    broadcast()


@socketio.on("prev_team")
def previous_team():
    eligible = game.tiebreaker_teams if game.tiebreaker else list(range(len(game.team_names)))
    position = eligible.index(game.current_team)
    game.current_team = eligible[(position - 1) % len(eligible)]
    game.reset_timer()
    broadcast()


@socketio.on("reset_time")
def reset_time():
    game.reset_timer()
    broadcast()


@socketio.on("reset_game")
def reset_game():
    game.reset_game()
    broadcast()


@socketio.on("toggle_rules")
def toggle_rules():
    game.rules_visible = not game.rules_visible
    broadcast()


@socketio.on("toggle_theme")
def toggle_theme():
    game.theme = "light" if game.theme == "dark" else "dark"
    broadcast()


@socketio.on("toggle_pause")
def toggle_pause():
    if game.match_status == "match":
        game.match_status = None
        broadcast()
        return
    game.paused = not game.paused
    broadcast()


@socketio.on("switch_memory")
def switch_memory(data):
    memory_name = data.get("memory") if isinstance(data, dict) else None
    if memory_name not in MEMORY_SETS:
        return
    try:
        game.load_memory(memory_name)
    except (FileNotFoundError, ValueError) as error:
        socketio.emit("error_message", {"message": str(error)})
        return
    broadcast()


@socketio.on("skip_memory")
def skip_memory():
    if game.skip_memory():
        broadcast()


@socketio.on("start_tiebreak")
def start_tiebreak():
    if game.start_tiebreak():
        broadcast()


@socketio.on("update_settings")
def update_settings(data):
    try:
        game.update_settings(data)
    except (KeyError, TypeError, ValueError) as error:
        socketio.emit("error_message", {"message": str(error)})
        return
    broadcast()


if __name__ == "__main__":
    socketio.start_background_task(timer_loop, game, socketio)
    threading.Timer(
        1.0,
        lambda: webbrowser.open_new("http://127.0.0.1:5000/moderator"),
    ).start()
    socketio.run(
        app,
        host="127.0.0.1",
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True,
    )
