import queue
import ssl
import websocket
import threading
import json


class WebsocketClient:
    def __init__(self, url, jwt, on_message, on_error, on_close, on_open, on_ping, on_stop, error_queue):
        self.ws = websocket.WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open,
            on_ping=on_ping,
            header={"authorization": "Bearer " + jwt},
        )
        self.on_stop = on_stop
        self.error_queue = error_queue
        self.running = True

    def send_error_messages(self):
        while self.running:
            try:
                error = self.error_queue.get(timeout=1)
                if error:
                    self.ws.send(json.dumps(error))
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
            self.running = False
            self.on_stop()
