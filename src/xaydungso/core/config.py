"""Foundation defaults; no persistent user settings are needed yet."""

import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    """Application metadata, initial window size, and logging level."""

    app_name: str = "xaydungso"
    window_title: str = "Xây Dựng Số"
    window_width: int = 1180
    window_height: int = 740
    log_level: int = logging.INFO
