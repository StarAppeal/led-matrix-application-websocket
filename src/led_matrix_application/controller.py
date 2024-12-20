import asyncio
import queue

from led_matrix_controller import LEDMatrixController

error_queue = asyncio.Queue()

led_matrix_controller = LEDMatrixController(error_queue)
