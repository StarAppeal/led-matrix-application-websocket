import asyncio
from led_matrix_application.preview.preview_manager import PreviewServiceManager
from led_matrix_application.utils import setup_logging

async def run_server():
    setup_logging()
    manager = PreviewServiceManager()
    await manager.connect_to_rust()

if __name__ == "__main__":
    asyncio.run(run_server())