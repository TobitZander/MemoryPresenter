import threading
import time
import urllib.error
import urllib.request
import webbrowser

import pystray
from PIL import Image, ImageDraw
from flask import (
    Flask,
    has_request_context,
    render_template,
    request,
    send_from_directory,
)
from flask_socketio import SocketIO

from config import CARD_BACK_IMAGE, IMAGE_ROOT, MEMORY_SETS
from countdown import timer_loop
from game_state import GameState

app = Flask(__name__)
socketio = SocketIO(app, async_mode="threading")
game = GameState()
SERVER_URL = "http://127.0.0.1:5000/moderator"
SHUTDOWN_URL = "http://127.0.0.1:5000/internal-shutdown"
_clients = set()
_clients_lock = threading.Lock()
last_client_disconnect = None
shutdown_requested = threading.Event()
tray_icon = None


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


@app.post("/internal-shutdown")
def internal_shutdown():
    request_shutdown()
    return "", 204


def broadcast():
    socketio.emit("state", game.to_dict())


def request_shutdown():
    first_request = not shutdown_requested.is_set()
    if first_request:
        shutdown_requested.set()
        socketio.emit("server_shutdown")
        if tray_icon is not None:
            tray_icon.stop()
    if has_request_context():
        socketio.stop()
        return
    try:
        urllib.request.urlopen(
            urllib.request.Request(SHUTDOWN_URL, method="POST"),
            timeout=2,
        ).close()
    except (ConnectionError, TimeoutError, urllib.error.URLError) as error:
        app.logger.warning("Could not request server shutdown: %s", error)


def monitor_client_disconnects():
    while not shutdown_requested.wait(1):
        with _clients_lock:
            disconnected_at = last_client_disconnect
            no_clients = not _clients
        if (
            no_clients
            and disconnected_at is not None
            and time.monotonic() - disconnected_at >= 30
        ):
            request_shutdown()
            return


def create_tray_image():
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((4, 4, 60, 60), radius=14, fill="#285d91")
    draw.ellipse((14, 17, 26, 31), fill="#ffffff")
    draw.ellipse((38, 17, 50, 31), fill="#ffffff")
    draw.arc((16, 20, 48, 49), 20, 160, fill="#ffffff", width=4)
    return image


def open_browser(_icon, _item):
    webbrowser.open_new(SERVER_URL)


def exit_from_tray(_icon, _item):
    request_shutdown()


def run_server():
    socketio.start_background_task(timer_loop, game, socketio)
    threading.Timer(1.0, lambda: webbrowser.open_new(SERVER_URL)).start()
    try:
        socketio.run(
            app,
            host="127.0.0.1",
            port=5000,
            debug=False,
            allow_unsafe_werkzeug=True,
        )
    finally:
        shutdown_requested.set()
        if tray_icon is not None:
            tray_icon.stop()


@socketio.on("connect")
def client_connected():
    global last_client_disconnect
    with _clients_lock:
        _clients.add(request.sid)
        last_client_disconnect = None


@socketio.on("disconnect")
def client_disconnected():
    global last_client_disconnect
    with _clients_lock:
        _clients.discard(request.sid)
        if not _clients:
            last_client_disconnect = time.monotonic()


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


@socketio.on("shutdown")
def shutdown():
    request_shutdown()


if __name__ == "__main__":
    tray_icon = pystray.Icon(
        "memory-presenter",
        create_tray_image(),
        "Memory Presenter",
        pystray.Menu(
            pystray.MenuItem("Browser öffnen", open_browser),
            pystray.MenuItem("Beenden", exit_from_tray),
        ),
    )
    monitor_thread = threading.Thread(
        target=monitor_client_disconnects,
        name="client-disconnect-monitor",
        daemon=True,
    )
    monitor_thread.start()
    server_thread = threading.Thread(target=run_server, name="web-server", daemon=True)
    server_thread.start()
    tray_icon.run()
    if not shutdown_requested.is_set():
        request_shutdown()
