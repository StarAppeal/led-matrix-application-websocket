import threading
import time

from mode.abstract_mode import AbstractMode
from PIL import Image, ImageSequence
import re
from io import BytesIO
import base64


class ImageMode(AbstractMode):
    def __init__(self, matrix):
        super().__init__(matrix)
        self.offscreen_canvas = matrix.CreateFrameCanvas()
        self.image_frames = []
        self.frame_durations = []
        self.current_frame = 0
        self.offset = (0, 0)
        self.lock = threading.Lock()

    def start(self):
        self.matrix.Clear()

    def stop(self):
        pass

    def update_settings(self, settings):
        with self.lock:
            self.matrix.Clear()
            self.offscreen_canvas.Clear()

            image_data = re.sub('^data:image/.+;base64,', '', settings['image'])
            decoded_image = BytesIO(base64.b64decode(image_data))

            img = Image.open(decoded_image)
            self.current_frame = 0
            self.frame_durations = []
            if img.format == "GIF":
                self.image_frames = []
                for frame in ImageSequence.Iterator(img):
                    self.image_frames.append(self.process_frame(frame.copy()))
                    self.frame_durations.append(frame.info.get("duration", 100))
            else:
                self.image_frames = [self.process_frame(img)]

            first_frame = self.image_frames[0]
            self.offset = (64 - first_frame.size[0]) // 2, (
                64 - first_frame.size[1]
            ) // 2

            self.offscreen_canvas.SetImage(
                first_frame, self.offset[0], self.offset[1], False
            )
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    def update_display(self):
        with self.lock:
            if not self.image_frames or not self.frame_durations:
                return
            start_time = time.time()
            img = self.image_frames[self.current_frame]
            self.offscreen_canvas.Clear()
            self.offscreen_canvas.SetImage(img, self.offset[0], self.offset[1], False)
            self.current_frame = (self.current_frame + 1) % len(self.image_frames)
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
            end_time = time.time()
            calculation_time = end_time - start_time
            sleep_time = max(
                self.frame_durations[self.current_frame] / 1000 - calculation_time, 0
            )
            time.sleep(sleep_time)

    def process_frame(self, frame):
        frame.thumbnail((64, 64))
        return frame.convert("RGB")
