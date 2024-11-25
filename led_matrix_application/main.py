import threading

from controller import led_matrix_controller
import os

from ws.wsclient import WebsocketClient


wsclient = WebsocketClient(
    url=os.getenv("WEBSOCKET_URL"),
    jwt=os.getenv("JWT_TOKEN"),
    led_matrix_controller=led_matrix_controller,
    on_stop=lambda: print("Stopped"),
)

threading.Thread(target=wsclient.run).start()
threading.Thread(target=led_matrix_controller.run).start()
