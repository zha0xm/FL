"""ServerAppComponents for the ServerApp."""


from dataclasses import dataclass
from typing import Optional


from .server_config import ServerConfig
from .server import Server
from .strategy import Strategy
from .client_manager import ClientManager


@dataclass
class ServerAppComponents:  # pylint: disable=too-many-instance-attributes
    """Components to construct a ServerApp.

    Parameters
    ----------
    server : Optional[Server] (default: None)
        A server implementation, either `flwr.server.Server` or a subclass
        thereof. If no instance is provided, one will be created internally.
    config : Optional[ServerConfig] (default: None)
        Currently supported values are `num_rounds` (int, default: 1) and
        `round_timeout` in seconds (float, default: None).
    strategy : Optional[Strategy] (default: None)
        An implementation of the abstract base class
        `flwr.server.strategy.Strategy`. If no strategy is provided, then
        `flwr.server.strategy.FedAvg` will be used.
    client_manager : Optional[ClientManager] (default: None)
        An implementation of the class `flwr.server.ClientManager`. If no
        implementation is provided, then `flwr.server.SimpleClientManager`
        will be used.
    """

    server: Optional[Server] = None
    config: Optional[ServerConfig] = None
    strategy: Optional[Strategy] = None
    client_manager: Optional[ClientManager] = None