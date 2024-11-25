import json
from datetime import datetime


class WebsocketMethods:
    def __init__(self, led_matrix_controller):
        self.led_matrix_controller = led_matrix_controller
        self.latest_mode = None

    def on_open(self, ws):
        print("Connection opened")
        self.send_message(ws, {"type": "GET_STATE"})

    def on_message(self, ws, message):
        print("Message received")
        json_message = json.loads(message)
        print(self.latest_mode)
        print("Current Time is: ", datetime.now())

        if "type" not in json_message:
            # Broadcasted message from server
            self.handle_state_update(ws, json_message)
        elif json_message["type"] == "SPOTIFY_UPDATE" and self.latest_mode == "music":
            self.handle_spotify_update(json_message)
        elif json_message["type"] == "STATE":
            self.handle_state_update(ws, json_message["payload"])

    def on_error(self, ws, error):
        print("Error: ", error)

    def on_close(self, ws):
        print("Connection closed")

    def on_ping(self, ws, ping_status):
        print(datetime.now())
        print("Ping received: " + str(ping_status))

    def send_message(self, ws, message):
        ws.send(json.dumps(message))

    def handle_state_update(self, ws, state):
        self.led_matrix_controller.update_state(state)
        new_mode = state["global"]["mode"]
        if self.latest_mode != "music" and new_mode == "music":
            self.send_message(ws, {"type": "GET_SPOTIFY_UPDATES"})
        elif self.latest_mode == "music" and new_mode != "music":
            self.send_message(ws, {"type": "STOP_SPOTIFY_UPDATES"})
        self.latest_mode = new_mode

    def handle_spotify_update(self, message):
        print("SPOTIFY_UPDATE")
        self.led_matrix_controller.modes["music"].update_song_data(message["payload"])
