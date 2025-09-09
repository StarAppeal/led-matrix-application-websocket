import asyncio
import logging
from urllib.request import urlopen
from mode.abstract_mode import AbstractMode
from PIL import Image
from utils import get_rgb_matrix

from pathlib import Path


graphics = get_rgb_matrix().get("graphics")

IMAGE_SIZE = 50, 50
IMAGE_SIZE_FULLSCREEN = 64, 64
COLOR_WHITE = graphics.Color(255, 255, 255)
TEXT_SPEED = 20


class MusicMode(AbstractMode):
    def __init__(self, matrix):
        super().__init__(matrix)
        logo_path = Path(__file__).parent.parent / "icons" / "spotify.png"
        self.logo = Image.open(logo_path).convert("RGB")

        self.font = graphics.Font()
        font_path = Path(__file__).parent.parent / "fonts" / "tamzen" / "1.bdf"
        self.font.LoadFont(str(font_path))

        self.offscreen_canvas = matrix.CreateFrameCanvas()

        self.song_data = None
        self.text = None
        self.image = None
        self.image_fullscreen = None
        self.last_frame_time = asyncio.get_event_loop().time()
        self.frame = 0
        self.one_char_width = self.font.CharacterWidth(0x0020)
        self.text_width = 0
        self.space_width = self.one_char_width * 4
        self.total_width = 0
        self.offset_left = 0
        self.is_mode_active = False
        self.logger = logging.getLogger(__name__)

    async def start(self):
        self.offscreen_canvas.Clear()
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
        self.is_mode_active = True

    async def stop(self):
        self.is_mode_active = False

    async def update_settings(self, settings):
        if self.song_data is None:
            self.settings = settings
            return

        if self.song_data["currently_playing_type"] == "track":
            image_url = self.song_data["item"]["album"]["images"][2]["url"]
        else:
            image_url = self.song_data["item"]["images"][2]["url"]
        if settings["fullscreen"]:
            self.settings = settings
            if self.image_fullscreen is None:
                self.image_fullscreen = self.process_image(
                    image_url, IMAGE_SIZE_FULLSCREEN
                )
            await self.display_fullscreen_image()
        else:
            if self.image is None:
                self.image = self.process_image(image_url, IMAGE_SIZE)
            self.last_frame_time = asyncio.get_event_loop().time()
            self.settings = settings

    async def update_display(self):
        if self.song_data is None or (
                self.image is None and self.image_fullscreen is None
        ):
            self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
            return

        if self.settings["fullscreen"]:
            return

        self.offscreen_canvas.Clear()

        graphics.DrawText(
            self.offscreen_canvas,
            self.font,
            self.offset_left,
            61,
            COLOR_WHITE,
            self.text,
        )

        if self.text_width > self.offscreen_canvas.width:
            graphics.DrawText(
                self.offscreen_canvas,
                self.font,
                self.offset_left + self.total_width,
                61,
                COLOR_WHITE,
                self.text,
            )

        self.offscreen_canvas.SetImage(self.image, 7, 2, False)

        current_time = asyncio.get_event_loop().time()
        time_delta = current_time - self.last_frame_time
        self.last_frame_time = current_time

        if self.text_width > self.offscreen_canvas.width:
            self.frame = (self.frame + TEXT_SPEED * time_delta) % self.total_width
            self.offset_left = round(
                max((self.offscreen_canvas.width - self.text_width) // 2, 0)
                - self.frame
            )

        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    async def update_song_data(self, new_song_data):
        if new_song_data["currently_playing_type"] == "ad":
            # just ignore ads
            return
        if new_song_data is not None and (
                self.song_data is None
                or new_song_data["item"]["id"] != self.song_data["item"]["id"]
        ):
            self.song_data = new_song_data
            if self.song_data["currently_playing_type"] == "track":
                artist = self.song_data["item"]["artists"][0]["name"]
                song = self.song_data["item"]["name"]
                image_url = self.song_data["item"]["album"]["images"][2]["url"]
            else:
                artist = self.song_data["item"]["show"]["publisher"]
                song = f"{self.song_data['item']['show']['name']} - {self.song_data['item']['name']}"
                image_url = self.song_data["item"]["images"][2]["url"]

            self.text = f"{artist} - {song}"

            self.frame = 0
            self.text_width = self.one_char_width * len(self.text)
            self.total_width = self.text_width + self.space_width
            self.offset_left = round(max((self.matrix.width - self.text_width) // 2, 0))

            if self.settings and self.settings["fullscreen"]:
                self.image_fullscreen = self.process_image(
                    image_url, IMAGE_SIZE_FULLSCREEN
                )
                self.image = None
                await self.display_fullscreen_image()
            else:
                self.image = self.process_image(image_url, IMAGE_SIZE)
                self.image_fullscreen = None

    def process_image(self, url, size):
        try:
            return Image.open(urlopen(url)).resize(size).convert("RGB")
        except Exception as e:
            self.logger.error(f"Error in process_image: {e}")

    async def display_fullscreen_image(self):
        self.offscreen_canvas.SetImage(self.image_fullscreen, 0, 0, False)
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)
