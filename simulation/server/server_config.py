"""Flower ServerConfig."""


from dataclasses import dataclass
from typing import Optional


@dataclass
class ServerConfig:
    """Flower server config.

    All attributes have default values which allows users to configure just the ones
    they care about.
    """

    num_rounds: int = 1
    round_timeout: Optional[float] = None

    def __repr__(self) -> str:
        """Return the string representation of the ServerConfig."""
        timeout_string = (
            "no round_timeout"
            if self.round_timeout is None
            else f"round_timeout={self.round_timeout}s"
        )
        return f"num_rounds={self.num_rounds}, {timeout_string}"