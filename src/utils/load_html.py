from pathlib import Path
from loguru import logger


def load_html_string(path: Path):
    """Load and parse a html object from the given path.

    If the file does not exist this logs an error and returns an empty dict.
    ?????????????????????If the file exists but contains invalid JSON, the JSONDecodeError is
    propagated.

    Args:
        path: Path to the html object

    Returns:
        A html string containing the parsed html object, or an empty dict if the file
        does not exist.

    Raises:
        ???????????????json.JSONDecodeError: If the file exists but contains invalid JSON.
    """
    if not path.exists():
        logger.error(
            "html object not found in {path}",
        )
        return {}
    return path.read_text(encoding="utf-8")
