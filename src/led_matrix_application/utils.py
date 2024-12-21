import json
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


def setup_logging(max_length=100):
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            try:
                message = record.getMessage()

                if isinstance(record.msg, dict):
                    message = json.dumps(record.msg, ensure_ascii=False)

                data = json.loads(message)

                sanitized_data = sanitize_json(data, max_length=max_length)

                formatted_json = json.dumps(sanitized_data, indent=4, ensure_ascii=False)
                record.msg = f"\n{formatted_json}"
            except (json.JSONDecodeError, TypeError):
                pass
            return super().format(record)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))

    # Füge den Handler dem Root-Logger hinzu
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)


def sanitize_json(data, max_length=100):
    """Kürzt nur lange Strings oder große Datenstrukturen."""
    if isinstance(data, dict):
        return {key: sanitize_json(value, max_length) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_json(item, max_length) for item in data]
    elif isinstance(data, str):
        if len(data) > max_length:
            return f"{data[:max_length]}... [truncated]"
        return data
    elif isinstance(data, (int, float)):
        return data
    else:
        return "[unsupported type]"
