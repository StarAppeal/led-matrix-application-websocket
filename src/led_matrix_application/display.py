from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

from led_matrix_application.utils import get_rgb_matrix

ColorTuple = Tuple[int, int, int]


class MatrixDisplay(ABC):
    def __init__(self, width: int, height: int, brightness: int = 50):
        self._width = width
        self._height = height
        self._brightness = brightness
        self.graphics = None

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def brightness(self) -> int:
        return self._brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._brightness = int(max(0, min(100, value)))

    @abstractmethod
    def create_frame_canvas(self):
        raise NotImplementedError

    @abstractmethod
    def swap_on_vsync(self, canvas):
        raise NotImplementedError

    def CreateFrameCanvas(self):
        return self.create_frame_canvas()

    def SwapOnVSync(self, canvas):
        return self.swap_on_vsync(canvas)

    def get_frame(self) -> Optional[np.ndarray]:
        return None


class HardwareDisplay(MatrixDisplay):
    def __init__(self, rows: int = 64, cols: int = 64, brightness: int = 50):
        matrix_data = get_rgb_matrix()
        RGBMatrix = matrix_data.get("RGBMatrix")
        RGBMatrixOptions = matrix_data.get("RGBMatrixOptions")
        self.graphics = matrix_data.get("graphics")

        options = RGBMatrixOptions()
        options.rows = rows
        options.cols = cols
        options.brightness = brightness

        self._matrix = RGBMatrix(options=options)
        super().__init__(self._matrix.width, self._matrix.height, brightness)

    @property
    def brightness(self) -> int:
        return self._matrix.brightness

    @brightness.setter
    def brightness(self, value: int) -> None:
        self._matrix.brightness = int(max(0, min(100, value)))

    def create_frame_canvas(self):
        return self._matrix.CreateFrameCanvas()

    def swap_on_vsync(self, canvas):
        return self._matrix.SwapOnVSync(canvas)


class PreviewDisplay(MatrixDisplay):
    def __init__(self, width: int = 64, height: int = 64, brightness: int = 50):
        super().__init__(width, height, brightness)
        self.graphics = PreviewGraphics()
        self._front_buffer = np.zeros((height, width, 3), dtype=np.uint8)

    def create_frame_canvas(self):
        return PreviewCanvas(self.width, self.height)

    def swap_on_vsync(self, canvas: "PreviewCanvas"):
        self._front_buffer = canvas.buffer.copy()
        return PreviewCanvas(self.width, self.height)

    def get_frame(self) -> Optional[np.ndarray]:
        if self._front_buffer is None:
            return None
        if self._brightness < 100:
            scale = self._brightness / 100.0
            return np.clip(self._front_buffer * scale, 0, 255).astype(np.uint8)
        return self._front_buffer.copy()


class PreviewCanvas:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.buffer = np.zeros((height, width, 3), dtype=np.uint8)

    def Clear(self) -> None:
        self.buffer.fill(0)

    def SetPixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = (r, g, b)

    def SetImage(self, image, x: int, y: int, _unsafe: bool = True) -> None:
        if image is None:
            return
        if isinstance(image, np.ndarray):
            img_array = image
        else:
            img_array = np.array(image.convert("RGB"))
        img_h, img_w = img_array.shape[:2]

        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + img_w)
        y1 = min(self.height, y + img_h)

        if x1 <= x0 or y1 <= y0:
            return

        src_x0 = x0 - x
        src_y0 = y0 - y
        self.buffer[y0:y1, x0:x1] = img_array[
            src_y0:src_y0 + (y1 - y0),
            src_x0:src_x0 + (x1 - x0),
        ]


@dataclass
class _BdfGlyph:
    width: int
    height: int
    xoff: int
    yoff: int
    dwidth: int
    bitmap: List[List[int]]


class PreviewFont:
    def __init__(self):
        self.height = 0
        self.ascent = 0
        self.descent = 0
        self._default_width = 6
        self._glyphs: Dict[int, _BdfGlyph] = {}

    def LoadFont(self, path: str) -> None:
        self._glyphs = {}
        self.ascent = 0
        self.descent = 0
        self.height = 0
        self._default_width = 6

        current_glyph = None
        bitmap_rows: List[str] = []

        with open(path, "r", encoding="utf-8", errors="ignore") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if line.startswith("FONT_ASCENT"):
                    self.ascent = int(line.split()[1])
                elif line.startswith("FONT_DESCENT"):
                    self.descent = int(line.split()[1])
                elif line.startswith("FONTBOUNDINGBOX"):
                    parts = line.split()
                    if len(parts) >= 3:
                        self._default_width = int(parts[1])
                        self.height = int(parts[2])
                elif line.startswith("STARTCHAR"):
                    current_glyph = {
                        "encoding": None,
                        "dwidth": self._default_width,
                        "bbx": None,
                    }
                    bitmap_rows = []
                elif line.startswith("ENCODING") and current_glyph is not None:
                    current_glyph["encoding"] = int(line.split()[1])
                elif line.startswith("DWIDTH") and current_glyph is not None:
                    current_glyph["dwidth"] = int(line.split()[1])
                elif line.startswith("BBX") and current_glyph is not None:
                    parts = line.split()
                    current_glyph["bbx"] = tuple(int(p) for p in parts[1:5])
                elif line == "BITMAP" and current_glyph is not None:
                    bitmap_rows = []
                elif line == "ENDCHAR" and current_glyph is not None:
                    glyph = self._build_glyph(current_glyph, bitmap_rows)
                    if glyph and current_glyph.get("encoding") is not None:
                        self._glyphs[current_glyph["encoding"]] = glyph
                    current_glyph = None
                elif current_glyph is not None:
                    if all(c in "0123456789ABCDEF" for c in line) and line:
                        bitmap_rows.append(line)

        if self.height == 0:
            self.height = self.ascent + self.descent

    def _build_glyph(self, data, bitmap_rows: List[str]) -> Optional[_BdfGlyph]:
        if data.get("bbx") is None:
            return None
        width, height, xoff, yoff = data["bbx"]
        bitmap = []
        for row in bitmap_rows:
            row_bits = len(row) * 4
            value = int(row, 16)
            row_pixels = [
                1 if value & (1 << (row_bits - 1 - idx)) else 0
                for idx in range(width)
            ]
            bitmap.append(row_pixels)
        return _BdfGlyph(
            width=width,
            height=height,
            xoff=xoff,
            yoff=yoff,
            dwidth=data.get("dwidth", self._default_width),
            bitmap=bitmap,
        )

    def CharacterWidth(self, _codepoint: int) -> int:
        return self._default_width

    def get_glyph(self, codepoint: int) -> Optional[_BdfGlyph]:
        return self._glyphs.get(codepoint)


class PreviewGraphics:
    Font = PreviewFont

    @staticmethod
    def Color(r: int, g: int, b: int) -> ColorTuple:
        return int(r), int(g), int(b)

    @staticmethod
    def DrawText(canvas: PreviewCanvas, font: PreviewFont, x: int, y: int, color: ColorTuple, text: str) -> int:
        cursor_x = x
        for ch in text:
            glyph = font.get_glyph(ord(ch))
            if glyph is None:
                cursor_x += font.CharacterWidth(ord(" "))
                continue

            for row_index, row in enumerate(glyph.bitmap):
                y_up = (glyph.height - 1 - row_index) + glyph.yoff
                y_pos = y - y_up
                if y_pos < 0 or y_pos >= canvas.height:
                    continue
                for col_index, value in enumerate(row):
                    if value:
                        canvas.SetPixel(cursor_x + glyph.xoff + col_index, y_pos, *color)
            cursor_x += glyph.dwidth
        return cursor_x

    @staticmethod
    def DrawLine(canvas: PreviewCanvas, x0: int, y0: int, x1: int, y1: int, color: ColorTuple) -> None:
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            canvas.SetPixel(x0, y0, *color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

