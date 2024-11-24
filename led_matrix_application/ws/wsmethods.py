import json
from datetime import datetime


class WebsocketMethods:
    def __init__(self, led_matrix_controller):
        self.led_matrix_controller = led_matrix_controller
        self.latest_mode = None

    def on_open(self, ws):
        print("Connection opened")
        ws.send("GET_STATE")

    def on_message(self, ws, message):
        print("Message received")

        json_message = json.loads(message)

        #todo: refactoring needed
        print(json_message)
        print(self.latest_mode)
        if "type" not in json_message:
            # broadcasted message from server
            self.led_matrix_controller.update_state(json_message)
            if self.latest_mode != "music" and json_message["global"]["mode"] == "music":
                ws.send("GET_SPOTIFY_UPDATES")
            if self.latest_mode == "music" and json_message["global"]["mode"] != "music":
                ws.send("STOP_SPOTIFY_UPDATES")
            self.latest_mode = json_message["global"]["mode"]
            return
        if json_message["type"] == "SPOTIFY_UPDATE" and self.latest_mode == "music":
            print("SPOTIFY_UPDATE")
            self.led_matrix_controller.modes["music"].update_song_data(json_message["payload"])
        elif json_message["type"] == "STATE":
            self.led_matrix_controller.update_state(json_message["payload"])
            if self.latest_mode != "music" and json_message["payload"]["global"]["mode"] == "music":
                ws.send("GET_SPOTIFY_UPDATES")
            if self.latest_mode == "music" and json_message["payload"]["global"]["mode"] != "music":
                ws.send("STOP_SPOTIFY_UPDATES")
            self.latest_mode = json_message["payload"]["global"]["mode"]

    def on_error(self, ws, error):
        print("Error: ", error)

    def on_close(self, ws):
        print("Connection closed")

    def on_ping(self, ws, ping_status):
        print(datetime.now())
        print("Ping received: " + str(ping_status))
