import asyncio
import os
from controller import led_matrix_controller
from ws.wsclient import WebsocketClient

async def main():
    print("Starting LED Matrix Application")

    wsclient = WebsocketClient(
        url=os.getenv("WEBSOCKET_URL"),
        jwt=os.getenv("JWT_TOKEN"),
        led_matrix_controller=led_matrix_controller,
        on_stop=lambda: print("Stopped"),
        error_queue=led_matrix_controller.error_queue,
    )

    controller_task = asyncio.create_task(led_matrix_controller.run())
    websocket_task = asyncio.create_task(wsclient.run())

    await asyncio.gather(controller_task, websocket_task)

if __name__ == "__main__":
    asyncio.run(main())