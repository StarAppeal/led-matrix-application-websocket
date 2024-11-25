import queue
import ssl
from datetime import datetime
from zoneinfo import ZoneInfo

import websocket
import threading
import json


class WebsocketClient:
    def __init__(self, url, jwt, led_matrix_controller, on_stop):
        self.ws = websocket.WebSocketApp(
            url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
            on_ping=self.on_ping,
            header={"authorization": "Bearer " + jwt},
        )
        self.led_matrix_controller = led_matrix_controller
        self.on_stop = on_stop
        self.error_queue = led_matrix_controller.error_queue
        self.error_queue_running = True
        self.current_mode = None

    def send_error_messages(self):
        while self.error_queue_running:
            try:
                error = self.error_queue.get(timeout=1)
                if error:
                    self.ws.send(json.dumps(error))
                    self.led_matrix_controller.switch_mode("idle")
            except queue.Empty:
                pass  # no errors, skipping
            except Exception as e:
                print(f"Error while sending error message: {e}")

    def run(self):
        threading.Thread(target=self.send_error_messages, daemon=True).start()
        try:
            self.ws.run_forever(
                reconnect=5,
                ping_interval=45,
                sslopt={"cert_reqs": ssl.CERT_NONE},
            )
        except Exception as e:
            print(f"Critical WebSocket error: {e}")
            self.error_queue.put({"type": "ERROR", "message": str(e)})
        finally:
            self.error_queue_running = False
            self.on_stop()

    def on_open(self, ws):
        print("Connection opened")
        self.send_message(ws, {"type": "GET_SETTINGS"})
        self.send_message(ws, {"type": "GET_STATE"})

    def on_message(self, ws, message):
        print("Message received")
        json_message = json.loads(message)
        print("current mode: " + str(self.current_mode))

        if "type" not in json_message:
            # Broadcasted message from server
            self.handle_state_update(ws, json_message)
        elif json_message["type"] == "SETTINGS":
            settings = json_message["payload"]
            timezone = settings["timezone"]
            self.led_matrix_controller.modes["clock"].timezone = ZoneInfo(timezone)
        elif json_message["type"] == "SPOTIFY_UPDATE" and self.current_mode == "music":
            self.handle_spotify_update(json_message)
        elif json_message["type"] == "WEATHER_UPDATE" and self.current_mode == "clock":
            print("WEATHER_UPDATE")
            self.led_matrix_controller.modes["clock"].update_weather_data(json_message["payload"])
        elif json_message["type"] == "STATE":
            self.handle_state_update(ws, json_message["payload"])

    def on_error(self, ws, error):
        print("Error: ", error)

    def on_close(self, ws, close_status_code, close_msg):
        print("Connection closed")

    def on_ping(self, ws, ping_status):
        print(datetime.now())
        print("Ping received: " + str(ping_status))

    def send_message(self, ws, message):
        ws.send(json.dumps(message))

    def handle_state_update(self, ws, state):
        self.led_matrix_controller.update_state(state)
        new_mode = state["global"]["mode"]
        if self.current_mode != "music" and new_mode == "music":
            self.send_message(ws, {"type": "GET_SPOTIFY_UPDATES"})
        elif self.current_mode == "music" and new_mode != "music":
            self.send_message(ws, {"type": "STOP_SPOTIFY_UPDATES"})

        if self.current_mode != "clock" and new_mode == "clock":
            self.send_message(ws, {"type": "GET_WEATHER_UPDATES"})
        elif self.current_mode == "clock" and new_mode != "clock":
            self.send_message(ws, {"type": "STOP_WEATHER_UPDATES"})
        self.current_mode = new_mode

    def handle_spotify_update(self, message):
        print("SPOTIFY_UPDATE")
        self.led_matrix_controller.modes["music"].update_song_data(message["payload"])
