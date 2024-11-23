import ssl
import websocket


class WebsocketClient:
    def __init__(self, url, jwt, on_message, on_error, on_close, on_open, on_ping, on_stop):
        self.ws = websocket.WebSocketApp(url,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close,
                                         on_open=on_open,
                                         on_ping=on_ping,
                                         header={
                                             "authorization": "Bearer " + jwt})
        self.on_stop = on_stop

    def run(self):
        self.ws.run_forever(
                            reconnect=5,
                            ping_interval=45,
                            sslopt={
                                "cert_reqs": ssl.CERT_NONE})  # Set dispatcher to automatic reconnection, 5 second reconnect delay if connection closed unexpectedly
        self.on_stop()
