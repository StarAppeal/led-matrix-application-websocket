import asyncio
from mode.abstract_mode import AbstractMode

class IdleMode(AbstractMode):

    def __init__(self, matrix):
        super().__init__(matrix)
        self.offscreen_canvas = matrix.CreateFrameCanvas()

    async def start(self):
        self.offscreen_canvas.Clear()
        self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)

    async def stop(self):
        pass

    async def update_settings(self, _):
        pass

    async def update_display(self):
        await asyncio.sleep(0.1)
