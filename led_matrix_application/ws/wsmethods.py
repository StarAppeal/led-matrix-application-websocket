import json
import threading
from datetime import datetime


class WebsocketMethods:
    def __init__(self, led_matrix_controller):
        self.led_matrix_controller = led_matrix_controller

    def on_open(self, ws):
        print("Connection opened")
       # ws.send("GET_STATE")

    def on_message(self, ws, message):
        print("Message received")
        print(message)

        #threading.Thread(target=self.led_matrix_controller.update_state, args=(json.loads(message),)).start()
        self.led_matrix_controller.update_state(json.loads(message))

    def on_error(self, ws, error):
        print("Error: ", error)

    def on_close(self, ws):
        print("Connection closed")

    def on_ping(self, ws, ping_status):
        print(datetime.now())
        print("Ping received: " + str(ping_status))

