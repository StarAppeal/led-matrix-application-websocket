import asyncio
import logging
import websockets
from led_matrix_application.preview.preview_manager import PreviewServiceManager
from led_matrix_application.utils import setup_logging

logger = logging.getLogger("Main")


async def run_server():
    setup_logging()
    manager = PreviewServiceManager()

    logger.info("Staring preview Server on port 8765...")

    async with websockets.serve(manager.handle_client, "0.0.0.0", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nPreview-Server beendet.")
