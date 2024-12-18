import traceback

from mode.clock_mode import ClockMode
from mode.idle_mode import IdleMode
from mode.image_mode import ImageMode
from mode.music_mode import MusicMode
from mode.text_mode import TextMode
from utils import get_rgb_matrix

RGBMatrix = get_rgb_matrix().get("RGBMatrix")
RGBMatrixOptions = get_rgb_matrix().get("RGBMatrixOptions")


class LEDMatrixController:
    def __init__(self, error_queue):
        self.error_queue = error_queue
        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        options.brightness = 50
        self.matrix = RGBMatrix(options=options)
        self.modes = {
            "idle": IdleMode(self.matrix),
            "clock": ClockMode(self.matrix),
            "text": TextMode(self.matrix),
            "music": MusicMode(self.matrix),
            "image": ImageMode(self.matrix),
        }
        self.current_mode = None
        self.mode_started = False

    def switch_mode(self, mode_name):
        self.mode_started = False
        if self.current_mode is not None:
            self.current_mode.stop()
        self.current_mode = self.modes[mode_name]
        self.current_mode.start()
        self.mode_started = True

    def update_settings(self, settings):
        self.current_mode.update_settings(settings)

    def update_display(self):
        if not self.mode_started:
            return
        self.current_mode.update_display()

    def update_state(self, state):
        self.matrix.brightness = state["global"]["brightness"]
        mode_name = state["global"]["mode"]
        if self.current_mode != self.modes[mode_name]:
            self.switch_mode(mode_name)
        if mode_name in state:
            self.update_settings(state[mode_name])

    def run(self):
        while True:
            try:
                self.update_display()
            except Exception as e:
                error_message = {
                    "type": "ERROR",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                }
                self.error_queue.put(error_message)
                print(f"Error in LEDMatrixController: {e}")
