import asyncio
import sys
from led_matrix_application.mode.text_mode import TextMode
from led_matrix_application.display import HardwareDisplay


SETUP_SETTINGS = {
    "text": "SETUP MODE Connect to 'LED-Matrix-Setup' WiFi on your phone and enter your credentials.",
    "size": 1,
    "color": [255, 255, 0],
    "align": "center",
    "speed": 3.0,
}

async def main():
    try:
        matrix = HardwareDisplay(rows=64, cols=64, brightness=50)

        setup_mode = TextMode(matrix)

        await setup_mode.update_settings(SETUP_SETTINGS)

        while True:
            await setup_mode.update_display()
            await asyncio.sleep(0.02)

    except Exception as e:
        print(f"FATAL: Fehler im Setup-Modus aufgetreten: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSetup-Modus manuell beendet.")