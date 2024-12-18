import asyncio
from mode.abstract_mode import AbstractMode

class IdleMode(AbstractMode):
    async def start(self):
        self.matrix.Clear()

    async def stop(self):
        pass

    async def update_settings(self, _):
        pass

    async def update_display(self):
        await asyncio.sleep(1)
