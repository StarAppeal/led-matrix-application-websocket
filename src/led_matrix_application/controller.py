import queue

from led_matrix_controller import LEDMatrixController

error_queue = queue.Queue()

led_matrix_controller = LEDMatrixController(error_queue)
