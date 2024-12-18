import time

from mode.abstract_mode import AbstractMode


class IdleMode(AbstractMode):
    def start(self):
        self.matrix.Clear()

    def stop(self):
        pass

    def update_settings(self, _):
        pass

    def update_display(self):
        time.sleep(1)
