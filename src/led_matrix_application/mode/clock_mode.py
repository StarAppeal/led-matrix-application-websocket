import asyncio
import logging
from datetime import date, datetime

from mode.abstract_mode import AbstractMode
from PIL import Image
from utils import get_rgb_matrix

graphics = get_rgb_matrix().get("graphics")

class ClockMode(AbstractMode):
    def __init__(self, matrix):
        super().__init__(matrix)
        self.offscreen_canvas = None
        self.icon = None
        self.temperature = ""
        self.font = graphics.Font()
        self.font.LoadFont("fonts/clock.bdf")
        self.offscreen_canvas = matrix.CreateFrameCanvas()
        self.timezone = None
        self.has_loaded = False
        self.logger = logging.getLogger(__name__)
        self.settings = None

    async def start(self):
        self.offscreen_canvas.Clear()
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    async def stop(self):
        self.has_loaded = False

    async def update_settings(self, _settings):
        self.settings = _settings

    async def update_display(self):
        if not self.has_loaded:
            return
        self.offscreen_canvas.Clear()
        display_color = graphics.Color(*self.settings["color"])
        aware_time = datetime.now(self.timezone)
        time_hours = aware_time.strftime("%H")
        time_minutes = aware_time.strftime("%M")

        graphics.DrawText(
            self.offscreen_canvas, self.font, 10, 16, display_color, time_hours
        )
        if aware_time.second % 2 == 0:
            graphics.DrawText(
                self.offscreen_canvas, self.font, 27, 15, display_color, ":"
            )
        graphics.DrawText(
            self.offscreen_canvas, self.font, 36, 16, display_color, time_minutes
        )

        display_date = date.today().strftime("%d %b")
        graphics.DrawText(
            self.offscreen_canvas, self.font, 5, 58, display_color, display_date
        )

        self.draw_icon(4, 24)
        graphics.DrawText(
            self.offscreen_canvas, self.font, 24, 37, display_color, self.temperature
        )

        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
        await asyncio.sleep(0.1)

    async def update_weather_data(self, data):
        self.logger.info("Refreshing weather data: ")
        self.logger.info(data)
        try:
            path = f"icons/clock/{data['weather']['icon']['raw']}.png"
            with Image.open(path) as img:
                self.icon = img.copy()
            self.temperature = f"{int(round(data['weather']['temp']['cur']))}°C"
        except Exception as e:
            self.logger.error(f"Error in refresh_weather_data: {e}")
        self.has_loaded = True

    def draw_icon(self, x, y):
        if self.icon is None:
            return
        width = self.icon.size[0]
        color = tuple(self.settings["color"])
        for index, pixel in enumerate(self.icon.getdata()):
            if pixel[0] == 255:
                self.offscreen_canvas.SetPixel(
                    x + (index % width), y + index // width, *color
                )
