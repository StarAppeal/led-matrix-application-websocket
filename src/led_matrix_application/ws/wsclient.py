import asyncio
import json
import ssl
from zoneinfo import ZoneInfo
import websockets
import logging

class WebsocketClient:
    def __init__(self, url, jwt, led_matrix_controller, on_stop, error_queue):

        self.url = url
        self.jwt = jwt
        self.led_matrix_controller = led_matrix_controller
        self.on_stop = on_stop
        self.error_queue = error_queue
        self.current_mode = None
        self.running = True
        self.reconnect_delay = 5  # Initial reconnect delay in seconds
        self.max_reconnect_delay = 60  # Maximum backoff time
        self.websocket = None
        self.logger = logging.getLogger(__name__)

    async def run(self):
        headers = [("Authorization", f"Bearer {self.jwt}")]
        while self.running:
            try:
                self.logger.info("Attempting to connect to WebSocket...")

                if (self.url.startswith("wss://")):
                    _ssl = self._create_ssl_context()
                else:
                    _ssl = None

                async with websockets.connect(
                        self.url,
                        ssl=_ssl,
                        additional_headers=headers,
                        ping_interval=45,
                        max_size=2**24,
                ) as websocket:
                    self.logger.info("WebSocket connection established.")
                    self.websocket = websocket
                    self.reconnect_delay = 5  # Reset reconnect delay on success

                    await asyncio.gather(
                        self.handle_messages(),
                        self.send_error_messages()
                    )
            except (websockets.ConnectionClosed, asyncio.TimeoutError) as e:
                self.logger.warning(f"WebSocket connection closed: {e}")
                await self._handle_reconnect(e)
            except Exception as e:
                self.logger.error(f"Unexpected WebSocket error: {e}", exc_info=True)
                await self._handle_reconnect(e)
            finally:
                self.websocket = None
        self.on_stop()

    async def handle_messages(self):
        try:
            async for message in self.websocket:
                await self.on_message(message)
        except websockets.ConnectionClosedError as e:
            self.logger.warning(f"Connection lost while receiving messages: {e}")
            raise

    async def send_error_messages(self):
        while self.running:
            try:
                if not self.websocket:  # Skip if not connected
                    await asyncio.sleep(1)
                    continue
                # Use async get with a timeout to avoid indefinite blocking
                if not self.error_queue.empty():
                    error = await self.error_queue.get()
                    self.logger.debug(f"Error message received: {error}")
                    await self.send_message(error)
                    self.logger.info("switching to idle mode")
                    await self.led_matrix_controller.switch_mode("idle")
                await asyncio.sleep(0.2)
            except asyncio.TimeoutError:
                pass  # No error in queue, continue loop
            except Exception as e:
                self.logger.error(f"Error while sending error message: {e}")
                await self.error_queue.put({"type": "ERROR", "message": str(e)})

    async def send_message(self, message):
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error while sending message: {e}")

    async def on_message(self, message):
        try:
            json_message = json.loads(message)

            self.logger.info("Received message:")
            self.logger.info(json_message)
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON: {e}")
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
        self.logger.debug("SPOTIFY_UPDATE")
        await self.led_matrix_controller.modes["music"].update_song_data(message["payload"])

    async def _handle_reconnect(self, error):
        """Reconnect logic with exponential backoff."""
        self.logger.warning(f"Error: {error}. Reconnecting in {self.reconnect_delay} seconds...")
        if self.error_queue.qsize() < 5:
            await self.error_queue.put({"type": "ERROR", "message": str(error)})
        await asyncio.sleep(self.reconnect_delay)
        self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)

    def _create_ssl_context(self):
        """Creates and configures SSL context."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
