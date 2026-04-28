from __future__ import annotations

import logging
from zoneinfo import ZoneInfo


class MessageRouter:
    def __init__(self, led_matrix_controller, logger: logging.Logger | None = None):
        self.led_matrix_controller = led_matrix_controller
        self.logger = logger or logging.getLogger(__name__)

    async def handle(self, json_message: dict, current_mode: str | None = None) -> bool:
        message_type = json_message.get("type")
        payload = json_message.get("payload", {})

        if message_type == "SETTINGS":
            timezone = payload.get("timezone")
            if timezone:
                self.led_matrix_controller.modes["clock"].timezone = ZoneInfo(timezone)
                self.logger.info(f"Settings timezone={timezone}")
            return True

        if message_type == "WEATHER_UPDATE":
            if current_mode and current_mode != "clock":
                return False
            await self.led_matrix_controller.modes["clock"].update_weather_data(payload)
            return True

        if message_type == "SPOTIFY_UPDATE":
            if current_mode and current_mode != "music":
                return False
            await self.led_matrix_controller.modes["music"].update_song_data(payload)
            return True

        return False

