from abc import ABC, abstractmethod

class AbstractMode(ABC):
    def __init__(self, matrix):
        self.matrix = matrix
        self.settings = None

    @abstractmethod
    async def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def update_settings(self, settings):
        pass

    @abstractmethod
    async def update_display(self):
        pass