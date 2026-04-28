import asyncio
import json
import logging
import aiohttp
import websockets
import os

from led_matrix_application.preview.preview_session import PreviewSession
from led_matrix_application.preview.shared_renderer import SharedRenderer

logger = logging.getLogger("PreviewManager")
BACKEND_URL = os.getenv("BACKEND_INTERNAL_URL", "http://ledmatrix-backend:3000")


class PreviewServiceManager:
    def __init__(self):
        self.active_sessions = {}
        self.renderer = SharedRenderer()

        asyncio.create_task(self.renderer.start())

    async def verify_token_via_backend(self, token):
        url = f"{BACKEND_URL}/api/user/me"
        headers = {"Authorization": f"Bearer {token}"}

        logger.info(f"Verifying token with backend: {url}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()

                        logger.info(f"Backend response {data}")

                        return data["data"]["_id"], data["data"]["config"]["isAdmin"]
        except Exception as e:
            logger.error(f"Auth Error: {e}")

        return None, None

    async def handle_client(self, websocket):
        session = None
        user_id = None

        try:
            logger.info("New preview client connected")
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)

            user_id, is_admin = await self.verify_token_via_backend(auth_data.get("token"))

            if not user_id:
                await websocket.send(json.dumps({"type": "ERROR"}))
                logger.warning("Authentication failed")
                return

            await websocket.send(json.dumps({"type": "AUTH_SUCCESS"}))
            logger.info(f"Preview-Auth OK: user_id={user_id}")

            session = PreviewSession(websocket, user_id, is_admin)
            self.active_sessions[user_id] = session

            await session.start()
            self.renderer.register(session)

            async for message in websocket:
                data = json.loads(message)
                await session.handle_command(data)

        except websockets.ConnectionClosed as exc:
            logger.info(f"Preview-Client disconnected: code={exc.code} reason={exc.reason}")
        except Exception as exc:
            logger.error(f"Preview-Client error: {exc}")

        finally:
            if session:
                await session.stop()
                self.renderer.unregister(user_id)

            if user_id in self.active_sessions:
                del self.active_sessions[user_id]
