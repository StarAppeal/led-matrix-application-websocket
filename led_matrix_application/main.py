import threading

from controller import led_matrix_controller
import os

from ws.wsclient import WebsocketClient
from ws.wsmethods import WebsocketMethods

ws_methods = WebsocketMethods(led_matrix_controller)

wsclient = WebsocketClient(
    url=os.getenv("WEBSOCKET_URL"),
    jwt=os.getenv("JWT_TOKEN"),
    on_message=ws_methods.on_message,
    on_open=ws_methods.on_open,
    on_error=ws_methods.on_error,
    on_close=ws_methods.on_close,
    on_ping=ws_methods.on_ping,
    on_stop=lambda: print("Stopped"),
    error_queue=led_matrix_controller.error_queue
)

threading.Thread(target=wsclient.run).start()
threading.Thread(target=led_matrix_controller.run).start()
