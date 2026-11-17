"""Standard console logging for the desktop process."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configure logging once, preserving any existing host handlers."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
