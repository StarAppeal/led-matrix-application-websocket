import asyncio
import sys
from mode.text_mode import TextMode
from utils import get_rgb_matrix


SETUP_SETTINGS = {
    "text": "SETUP MODE Connect to 'LED-Matrix-Setup' WiFi on your phone and enter your credentials.",
    "size": 1,
    "color": [255, 255, 0],
    "align": "center",
    "speed": 3.0,
}

async def main():
    try:
        matrix_data = get_rgb_matrix()
        RGBMatrix = matrix_data.get("RGBMatrix")
        RGBMatrixOptions = matrix_data.get("RGBMatrixOptions")

        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64

        matrix = RGBMatrix(options=options)

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