import os

from dotenv import load_dotenv

import logging


def get_rgb_matrix():
    load_dotenv()

    if os.getenv("USE_EMULATOR") == "True":
        from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions, graphics
    else:
        from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

    return {
        "RGBMatrix": RGBMatrix,
        "RGBMatrixOptions": RGBMatrixOptions,
        "graphics": graphics,
    }


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ],
    )
