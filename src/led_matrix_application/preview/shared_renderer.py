import asyncio
import numpy as np
from PIL import Image
import io
import base64
import logging

logger = logging.getLogger("SharedRenderer")


class SharedRenderer:
    def __init__(self):
        self.sessions = {}
        self.running = True

    def register(self, session):
        self.sessions[session.user_id] = session
        logger.info(f"Session registered: user_id={session.user_id}")

    def unregister(self, user_id):
        self.sessions.pop(user_id, None)
        logger.info(f"Session unregistered: user_id={user_id}")

    async def start(self):
        logger.info("shared renderer started")

        while self.running:
            tasks = [
                self.render_session(session)
                for session in list(self.sessions.values())
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            # 10 FPS, change if needed
            await asyncio.sleep(0.1)

    async def render_session(self, session):
        controller = session.controller

        if not controller.mode_started:
            return

        try:
            frame_array = controller.matrix.get_frame()
        except Exception as exc:
            logger.error(f"frame error user_id={session.user_id}: {exc}")
            return

        if frame_array is None:
            return

        current_bytes = frame_array.tobytes()

        if current_bytes == session.last_frame_bytes:
            return

        session.last_frame_bytes = current_bytes

        loop = asyncio.get_running_loop()

        try:
            base64_str = await loop.run_in_executor(
                None,
                self.encode_frame,
                frame_array
            )

            await session.send_frame(base64_str)
        except Exception as exc:
            logger.error(f"error while sending user_id={session.user_id}: {exc}")

    def encode_frame(self, frame_array):
        img = Image.fromarray(np.uint8(frame_array), 'RGB')
        buffer = io.BytesIO()

        img.save(buffer, format="PNG", compress_level=1)

        return base64.b64encode(buffer.getvalue()).decode("utf-8")
