import asyncio
import json
import logging
import websockets

from led_matrix_application.display import PreviewDisplay
from led_matrix_application.message_router import MessageRouter

logger = logging.getLogger("PreviewSession")


class PreviewSession:
    def __init__(self, websocket, user_id, is_admin):
        self.websocket = websocket
        self.user_id = user_id
        self.is_admin = is_admin

        self.controller = None
        self.last_frame_bytes = None
        self.last_sent = 0  # FPS throttling

    async def start(self):
        logger.info(f"Starting session {self.user_id}")
        from led_matrix_application.led_matrix_controller import LEDMatrixController

        error_queue = asyncio.Queue()
        display = PreviewDisplay(width=64, height=64, brightness=50)
        self.controller = LEDMatrixController(error_queue, display=display)
        self.message_router = MessageRouter(self.controller, logger)

        await self.controller.switch_mode("idle")
        asyncio.create_task(self.controller.run())

    async def stop(self):
        logger.info(f"Stopping session {self.user_id}")

    async def handle_command(self, data):
        try:
            message_type = data.get("type")
            if message_type == "STATE":
                mode_name = data.get("payload", {}).get("global", {}).get("mode", "unknown")
                logger.info(f"Got state with: user_id={self.user_id}: Change mode to: '{mode_name}'")

                await self.controller.update_state(data["payload"])
                return

            handled = await self.message_router.handle(data)
            if handled:
                logger.info(f"Preview update handled user_id={self.user_id}: {message_type}")

        except Exception as e:
            logger.error(f"Error in handle_command for {self.user_id}: {e}", exc_info=True)

    async def send_frame(self, base64_str):
        now = asyncio.get_event_loop().time()

        if now - self.last_sent < 0.1:
            return

        self.last_sent = now
        payload = json.dumps({
            "type": "PREVIEW_FRAME",
            "payload": f"data:image/png;base64,{base64_str}"
        })

        try:
            await self.websocket.send(payload)
        except websockets.ConnectionClosed as exc:
            logger.info(
                f"WebSocket disconnected: user_id={self.user_id} code={exc.code} reason={exc.reason}"
            )
        except Exception as e:
            logger.error(f"Send error {self.user_id}: {e}")