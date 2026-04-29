import asyncio
import logging

logger = logging.getLogger("SharedRenderer")

TARGET_FPS = 30
class SharedRenderer:
    def __init__(self):
        self.sessions = {}
        self.running = True
        self.frame_writer = None

    async def _connect_frame_socket(self):
        while self.running:
            try:
                _, writer = await asyncio.open_connection('rust-preview', 5001)
                self.frame_writer = writer
                logger.info("connected to Frame-Socket (5001) on rust!")
                return
            except Exception:
                await asyncio.sleep(1)

    def register(self, session):
        self.sessions[session.user_id] = session

    def unregister(self, user_id):
        self.sessions.pop(user_id, None)

    async def start(self):
        await self._connect_frame_socket()

        while self.running:
            if not self.frame_writer:
                # check if this needs to be the same as TARGET_FP
                await asyncio.sleep(0.1)
                continue

            for user_id, session in list(self.sessions.items()):
                self.send_frame_to_buffer(session)

            try:
                await self.frame_writer.drain()
            except Exception as e:
                logger.error(f"lost connection to rust socket: {e}")
                self.frame_writer = None
                asyncio.create_task(self._connect_frame_socket())

            await asyncio.sleep(1 / TARGET_FPS)

    def send_frame_to_buffer(self, session):
        if not session.controller.mode_started: return

        frame_array = session.controller.matrix.get_frame()
        if frame_array is None: return

        current_bytes = frame_array.tobytes()
        if current_bytes == session.last_frame_bytes: return
        session.last_frame_bytes = current_bytes

        user_id_bytes = session.user_id.encode('utf-8')
        header = bytes([len(user_id_bytes)]) + user_id_bytes
        packet = header + current_bytes

        try:
            self.frame_writer.write(packet)
        except:
            pass