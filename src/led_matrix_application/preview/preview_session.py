import asyncio
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
        self.run_task = None

    async def start(self):
        logger.info(f"Starting session {self.user_id}")
        from led_matrix_application.led_matrix_controller import LEDMatrixController

        error_queue = asyncio.Queue()
        display = PreviewDisplay(width=64, height=64, brightness=50)
        self.controller = LEDMatrixController(error_queue, display=display)
        self.message_router = MessageRouter(self.controller, logger)

        await self.controller.switch_mode("idle")
        self.run_task = asyncio.create_task(self.controller.run())

    async def stop(self):
        if self.controller:
            if self.controller.current_mode:
                await self.controller.current_mode.stop()

        if self.run_task:
            self.run_task.cancel()
            try:
                await self.run_task
            except asyncio.CancelledError:
                pass
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