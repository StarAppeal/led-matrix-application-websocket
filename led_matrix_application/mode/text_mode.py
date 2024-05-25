import time

from mode.abstract_mode import AbstractMode
from utils import get_rgb_matrix

graphics = get_rgb_matrix().get("graphics")


class TextMode(AbstractMode):
    def __init__(self, matrix):
        super().__init__(matrix)
        self.font = graphics.Font()
        self.size = None
        self.offscreen_canvas = matrix.CreateFrameCanvas()
        self.frame = 0
        self.line_list = []
        self.total_height = 0
        self.last_frame_time = time.time()

    def start(self):
        pass

    def stop(self):
        pass

    def update_settings(self, settings):
        self.settings = settings
        if self.size != self.settings["size"]:
            self.font.LoadFont(f"fonts/tamzen/{self.settings['size']}.bdf")
            self.size = self.settings["size"]
        self.calculate_text()

    def calculate_text(self):
        one_char_width = self.font.CharacterWidth(0x0020)
        split_text = self.settings["text"].split(" ")

        self.line_list = []
        text_line = ""
        max_length = 64 // one_char_width

        for text in split_text:
            while len(text) > max_length:
                if text_line:
                    self.line_list.append(
                        (text_line, self.calculate_offset(text_line, one_char_width))
                    )
                    text_line = ""

                first_half = text[:max_length]
                text = text[max_length:]
                text_line += first_half + " "

            if one_char_width * len(text_line + text) < 64:
                text_line += text + " "
            else:
                self.line_list.append(
                    (text_line, self.calculate_offset(text_line, one_char_width))
                )
                text_line = text + " "

        self.line_list.append(
            (text_line, self.calculate_offset(text_line, one_char_width))
        )

        self.total_height = len(self.line_list) * self.font.height

        if self.total_height < 64:
            self.frame = 0

    def calculate_offset(self, line, one_char_width):
        offset_left = 0
        if self.settings["align"] == "center":
            width = one_char_width * (len(line) - 1)
            offset_left = (64 - width) // 2
        return offset_left

    def update_display(self):
        self.offscreen_canvas.Clear()

        current_time = time.time()
        time_delta = current_time - self.last_frame_time
        self.last_frame_time = current_time

        speed = self.settings["speed"] * self.settings["speed"]

        if self.total_height > 64:
            self.frame = (self.frame + speed * time_delta) % (
                self.total_height + self.font.height
            )

        offset_top = max((64 - self.total_height) // 2, 0) - self.frame - self.size

        for i, (line, offset_left) in enumerate(self.line_list):
            trimmed_line = line[:-1]

            y1 = offset_top + ((i + 1) * self.font.height)
            y2 = offset_top + ((i + 2) * self.font.height) + self.total_height

            if 0 <= y1 < 64 + self.font.height:
                graphics.DrawText(
                    self.offscreen_canvas,
                    self.font,
                    offset_left,
                    y1,
                    graphics.Color(*self.settings["color"]),
                    trimmed_line,
                )

            if self.total_height > 64 and 0 <= y2 < 64 + self.font.height:
                graphics.DrawText(
                    self.offscreen_canvas,
                    self.font,
                    offset_left,
                    y2,
                    graphics.Color(*self.settings["color"]),
                    trimmed_line,
                )

        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
