import time

def timer_loop(game, socketio):
    while True:
        time.sleep(1)
        game.tick()
        socketio.emit("state", game.to_dict())
