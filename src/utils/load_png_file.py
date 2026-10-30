from pathlib import Path
from loguru import logger
from PIL import Image, UnidentifiedImageError
import io
import base64


def load_png_as_data_url(path: Path) -> str:
    """
    Load a PNG file and return it as a base64 data URL string.

    Args:
        path: Path to the PNG file.

    Returns:
        A string like "data:image/png;base64,<base64-encoded-png>".

    Raises:
        FileNotFoundError: if path does not exist.
        PIL.UnidentifiedImageError: if the file exists but is not a valid image.
        OSError: other I/O errors from Pillow or I/O operations.
    """
    if not path.exists():
        logger.error("png file not found in {path}", path=path)
        raise FileNotFoundError(f"PNG not found: {path}")

    try:
        # Use context manager so file handles are closed promptly
        with Image.open(path) as img:
            # Force loading the image into memory (avoid deferred reads)
            img.load()

            # Save to an in-memory bytes buffer in PNG format and base64-encode
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()
            b64 = base64.b64encode(png_bytes).decode("ascii")
            data_url = "data:image/png;base64," + b64
            return data_url

    except UnidentifiedImageError:
        logger.exception("Failed to identify image file at {path}", path=path)
        raise
    except Exception:
        logger.exception("Error reading or encoding PNG file at {path}", path=path)
        raise
