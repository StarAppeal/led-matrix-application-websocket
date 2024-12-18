import os

from dotenv import load_dotenv


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
