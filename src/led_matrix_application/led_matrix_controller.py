import asyncio
import logging
import traceback
import gc

from led_matrix_application.mode.clock_mode import ClockMode
from led_matrix_application.mode.idle_mode import IdleMode
from led_matrix_application.mode.image_mode import ImageMode
from led_matrix_application.mode.music_mode import MusicMode
from led_matrix_application.mode.text_mode import TextMode
from led_matrix_application.mode.game_of_life_mode import GameOfLifeMode
from led_matrix_application.display import HardwareDisplay


class LEDMatrixController:
    def __init__(self, error_queue, target_fps=60, display=None):
        self.error_queue = error_queue
        self.matrix = display or HardwareDisplay(rows=64, cols=64, brightness=50)

        self.current_mode_name = None
        self.current_mode = None

        self.mode_started = False
        self.target_fps = target_fps
        self.sleep_time = 1 / target_fps
        self.logger = logging.getLogger(__name__)

    async def switch_mode(self, mode_name):
        if self.current_mode_name == mode_name and self.current_mode is not None:
            return

        self.mode_started = False

        if self.current_mode is not None:
            await self.current_mode.stop()
            del self.current_mode
            self.current_mode = None
            gc.collect()

        self.current_mode_name = mode_name

        if mode_name == "idle":
            self.current_mode = IdleMode(self.matrix)
        elif mode_name == "clock":
            self.current_mode = ClockMode(self.matrix)
        elif mode_name == "text":
            self.current_mode = TextMode(self.matrix)
        elif mode_name == "music":
            self.current_mode = MusicMode(self.matrix)
        elif mode_name == "image":
            self.current_mode = ImageMode(self.matrix)
        elif mode_name == "game_of_life":
            self.current_mode = GameOfLifeMode(self.matrix)
        else:
            self.logger.error(f"Unknown mode: {mode_name}, fallback to idle")
            self.current_mode_name = "idle"
            self.current_mode = IdleMode(self.matrix)

        await self.current_mode.start()
        self.mode_started = True

    async def update_settings(self, settings):
        if self.current_mode:
            await self.current_mode.update_settings(settings)

    async def update_display(self):
        if not self.mode_started or not self.current_mode:
            return
        await self.current_mode.update_display()

    async def update_state(self, state):
        self.matrix.brightness = state["global"]["brightness"]
        mode_name = state["global"]["mode"]

        if self.current_mode_name != mode_name:
            await self.switch_mode(mode_name)

        if mode_name in state:
            await self.update_settings(state[mode_name])

    async def run(self):
        while True:
            try:
                await self.update_display()
            except Exception as e:
                error_message = {
                    "type": "ERROR",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
                await self.error_queue.put(error_message)
                self.logger.error(f"Error in LEDMatrixController: {e}")
            await asyncio.sleep(self.sleep_time)