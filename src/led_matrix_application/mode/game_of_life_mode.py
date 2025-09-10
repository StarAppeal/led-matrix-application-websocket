import asyncio
import random
from mode.abstract_mode import AbstractMode
from utils import get_rgb_matrix

graphics = get_rgb_matrix().get("graphics")


class GameOfLifeMode(AbstractMode):
    def __init__(self, matrix):
        super().__init__(matrix)
        self.offscreen_canvas = matrix.CreateFrameCanvas()

        self.settings = {
            "cell_size": 2,
            "speed": 10,
            "color": [0, 255, 0]
        }

        self.grid_width = self.matrix.width // self.settings["cell_size"]
        self.grid_height = self.matrix.height // self.settings["cell_size"]
        self.grid = []
        self.last_update_time = asyncio.get_event_loop().time()

    def _initialize_grid(self):
        """Erstellt ein neues Gitter und füllt es zufällig mit lebenden Zellen."""
        self.grid_width = self.matrix.width // self.settings["cell_size"]
        self.grid_height = self.matrix.height // self.settings["cell_size"]

        density = 0.2

        self.grid = [
            [1 if random.random() < density else 0 for _ in range(self.grid_width)]
            for _ in range(self.grid_height)
        ]


    async def start(self):
        self._initialize_grid()
        self.last_update_time = asyncio.get_event_loop().time()

    async def stop(self):
        self.grid = []

    async def update_settings(self, settings):
        cell_size_changed = self.settings["cell_size"] != settings.get("cell_size", self.settings["cell_size"])
        self.settings.update(settings)

        if cell_size_changed:
            self._initialize_grid()

    async def _update_grid(self):
        """Berechnet die nächste Generation des Spiels basierend auf den Regeln."""
        new_grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                live_neighbors = 0
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        if i == 0 and j == 0:
                            continue

                        neighbor_x = (x + j + self.grid_width) % self.grid_width
                        neighbor_y = (y + i + self.grid_height) % self.grid_height

                        live_neighbors += self.grid[neighbor_y][neighbor_x]

                cell_state = self.grid[y][x]
                if cell_state == 1 and (live_neighbors < 2 or live_neighbors > 3):
                    new_grid[y][x] = 0
                elif cell_state == 0 and live_neighbors == 3:
                    new_grid[y][x] = 1
                else:
                    new_grid[y][x] = cell_state

        self.grid = new_grid

    def _draw_grid(self):
        """Zeichnet das aktuelle Gitter auf den Canvas."""
        self.offscreen_canvas.Clear()
        cell_color = graphics.Color(*self.settings["color"])
        cell_size = self.settings["cell_size"]

        for y, row in enumerate(self.grid):
            for x, cell_state in enumerate(row):
                if cell_state == 1:
                    px = x * cell_size
                    py = y * cell_size
                    for i in range(cell_size):
                        graphics.DrawLine(self.offscreen_canvas, px, py + i, px + cell_size - 1, py + i, cell_color)

    async def update_display(self):
        if not self.grid:
            return

        current_time = asyncio.get_event_loop().time()
        time_delta = current_time - self.last_update_time
        update_interval = 1 / self.settings["speed"]

        if time_delta >= update_interval:
            self.last_update_time = current_time
            await self._update_grid()

        self._draw_grid()
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

        await asyncio.sleep(0.01)