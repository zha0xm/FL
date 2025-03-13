"""Flower Logger."""


import logging
from logging import WARN


# Create logger
LOGGER_NAME = "flwr"
FLOWER_LOGGER = logging.getLogger(LOGGER_NAME)
FLOWER_LOGGER.setLevel(logging.DEBUG)
log = FLOWER_LOGGER.log

LOG_COLORS = {
    "DEBUG": "\033[94m",  # Blue
    "INFO": "\033[92m",  # Green
    "WARNING": "\033[93m",  # Yellow
    "ERROR": "\033[91m",  # Red
    "CRITICAL": "\033[95m",  # Magenta
    "RESET": "\033[0m",  # Reset to default
}


def warn_preview_feature(name: str) -> None:
    """Warn the user when they use a preview feature."""
    log(
        WARN,
        """PREVIEW FEATURE: %s

            This is a preview feature. It could change significantly or be removed
            entirely in future versions of Flower.
        """,
        name,
    )
    

def warn_deprecated_feature(name: str) -> None:
    """Warn the user when they use a deprecated feature."""
    log(
        WARN,
        """DEPRECATED FEATURE: %s

            This is a deprecated feature. It will be removed
            entirely in future versions of Flower.
        """,
        name,
    )