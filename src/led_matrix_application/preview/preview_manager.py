import asyncio
import json
import logging
from led_matrix_application.preview.preview_session import PreviewSession
from led_matrix_application.preview.shared_renderer import SharedRenderer
import gc

from led_matrix_application.utils import RUST_HOST, RUST_COMMAND_SOCKET_PORT

logger = logging.getLogger("PreviewManager")

class PreviewServiceManager:
    def __init__(self):
        self.active_sessions = {}
        self.renderer = SharedRenderer()
        asyncio.create_task(self.renderer.start())

    async def connect_to_rust(self):
        logger.info(f"connect command-socket to rust (Port {RUST_COMMAND_SOCKET_PORT})...")
        while True:
            try:
                reader, _ = await asyncio.open_connection(RUST_HOST, RUST_COMMAND_SOCKET_PORT, limit=1024 * 1024 * 10)
                logger.info("connected with command-socket in rust!")

                async for line in reader:
                    await self.handle_rust_command(line)

            except Exception as e:
                logger.error(f"connection lost, retrying in 2s... {e}")
                await asyncio.sleep(2)

    async def handle_rust_command(self, line):
        try:
            data = json.loads(line.decode('utf-8'))
            event = data.get("event")
            user_id = data.get("user_id")

            if event == "connect":
                logger.info(f"new user: {user_id}")
                session = PreviewSession(None, user_id, False)
                self.active_sessions[user_id] = session
                await session.start()
                self.renderer.register(session)

            elif event == "message":
                if user_id in self.active_sessions:
                    await self.active_sessions[user_id].handle_command(data.get("data"))

            elif event == "disconnect":
                logger.info(f"user disconnected: {user_id}")
                if user_id in self.active_sessions:
                    session = self.active_sessions[user_id]
                    await session.stop()

                    if session.controller:
                        del session.controller

                    self.renderer.unregister(user_id)
                    del self.active_sessions[user_id]

                    gc.collect()

        except Exception as e:
            logger.error(f"error while parsing rust command: {e}")