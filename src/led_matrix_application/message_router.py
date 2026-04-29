from __future__ import annotations
import logging
from zoneinfo import ZoneInfo


class MessageRouter:
    def __init__(self, led_matrix_controller, logger: logging.Logger | None = None):
        self.led_matrix_controller = led_matrix_controller
        self.logger = logger or logging.getLogger(__name__)

    async def handle(self, json_message: dict) -> bool:
        message_type = json_message.get("type")
        payload = json_message.get("payload", {})

        actual_mode = self.led_matrix_controller.current_mode_name

        if message_type == "SETTINGS":
            timezone = payload.get("timezone")
            if timezone and actual_mode == "clock":
                self.led_matrix_controller.current_mode.timezone = ZoneInfo(timezone)
                self.logger.info(f"Settings timezone={timezone}")
            return True

        if message_type == "WEATHER_UPDATE":
            if actual_mode != "clock":
                return False
            await self.led_matrix_controller.current_mode.update_weather_data(payload)
            return True

        if message_type == "SPOTIFY_UPDATE":
            if actual_mode != "music":
                return False
            await self.led_matrix_controller.current_mode.update_song_data(payload)
            return True

        return False