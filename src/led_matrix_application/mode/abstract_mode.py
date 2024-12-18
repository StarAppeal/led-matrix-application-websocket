from abc import ABC, abstractmethod


class AbstractMode(ABC):
    def __init__(self, matrix):
        self.matrix = matrix
        self.settings = None

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def update_settings(self, settings):
        pass

    @abstractmethod
    def update_display(self):
        pass
