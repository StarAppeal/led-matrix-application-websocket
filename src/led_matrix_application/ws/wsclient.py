import asyncio
import json
import ssl
from datetime import datetime
from zoneinfo import ZoneInfo
import websockets
import traceback


class WebsocketClient:
    def __init__(self, url, jwt, led_matrix_controller, on_stop, error_queue):
        self.url = url
        self.jwt = jwt
        self.led_matrix_controller = led_matrix_controller
        self.on_stop = on_stop
        self.error_queue = error_queue  # Pass the shared asyncio.Queue
        self.current_mode = None
        self.running = True
        # Create SSL context in the constructor
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.websocket = None

    async def send_error_messages(self):
        while self.running:
            try:
                # Use async get with a timeout to avoid indefinite blocking
                if not self.error_queue.empty():
                    error = self.error_queue.get()
                    print(f"Error message received: {error}")
                    await self.send_message(error)
                    print("switching to idle mode")
                    await self.led_matrix_controller.switch_mode("idle")
                await asyncio.sleep(0.2)
            except asyncio.TimeoutError:
                pass  # No error in queue, continue loop
            except Exception as e:
                print(f"Error while sending error message: {e}")

    async def run(self):
        headers = [
            ("Authorization", f"Bearer {self.jwt}")
        ]

        while self.running:
            try:
                print("Attempting to connect to WebSocket...")
                async with websockets.connect(self.url, ssl=self.ssl_context, additional_headers=headers,
                                              ping_interval=45) as websocket:
                    print("Connection opened")
                    self.websocket = websocket
                    await asyncio.gather(
                        self.handle_messages(),
                        self.send_error_messages()
                    )

            except Exception as e:
                print(f"WebSocket error: {e}")
                if self.error_queue.qsize() < 5:  # Avoid spamming too many errors
                    await self.error_queue.put({"type": "ERROR", "message": str(e)})
                await asyncio.sleep(5)  # Backoff before retrying
            finally:
                self.websocket = None
                self.running = False
                self.on_stop()

    async def handle_messages(self):
        try:
            async for message in self.websocket:
                await self.on_message(message)
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed with error: {e}")

    async def on_message(self, message):
        try:
            json_message = json.loads(message)
            print(f"Received message: {json_message}")
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return

        if "type" not in json_message:
            await self.handle_state_update(json_message)
        elif json_message["type"] == "SETTINGS":
            settings = json_message["payload"]
            timezone = settings["timezone"]
            self.led_matrix_controller.modes["clock"].timezone = ZoneInfo(timezone)
        elif json_message["type"] == "SPOTIFY_UPDATE" and self.current_mode == "music":
            await self.handle_spotify_update(json_message)
        elif json_message["type"] == "WEATHER_UPDATE" and self.current_mode == "clock":
            await self.led_matrix_controller.modes["clock"].update_weather_data(json_message["payload"])
        elif json_message["type"] == "STATE":
            await self.handle_state_update(json_message["payload"])

    async def handle_state_update(self, state):
        await self.led_matrix_controller.update_state(state)
        new_mode = state["global"]["mode"]

        if self.current_mode != "music" and new_mode == "music":
            await self.send_message({"type": "GET_SPOTIFY_UPDATES"})
        elif self.current_mode == "music" and new_mode != "music":
            await self.send_message({"type": "STOP_SPOTIFY_UPDATES"})

        if self.current_mode != "clock" and new_mode == "clock":
            await self.send_message({"type": "GET_WEATHER_UPDATES"})
        elif self.current_mode == "clock" and new_mode != "clock":
            await self.send_message({"type": "STOP_WEATHER_UPDATES"})

        self.current_mode = new_mode

    async def handle_spotify_update(self, message):
        print("SPOTIFY_UPDATE")
        await self.led_matrix_controller.modes["music"].update_song_data(message["payload"])

    async def send_message(self, message):
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Error while sending message: {e}")
