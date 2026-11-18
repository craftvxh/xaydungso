"""Application metadata and initial window defaults."""

import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class AppSettings:
    """Application metadata, initial window size, and logging level."""

    app_name: str = "xaydungso"
    window_title: str = "Xây Dựng Số"
    window_width: int = 1280
    window_height: int = 800
    log_level: int = logging.INFO
