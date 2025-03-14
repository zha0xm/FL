"""Flower driver app."""


from typing import Optional
from logging import INFO

from common.logger import log
from server.server import Server, init_defaults, run_fl
from server.server_config import ServerConfig
from server.strategy import Strategy
from server.history import History
from server.client_manager import ClientManager
from ..driver import Driver
from .app_utils import start_update_client_manager_thread


def start_driver(
    *,
    driver: Driver,
    server: Optional[Server] = None,
    config: Optional[ServerConfig] = None,
    strategy: Optional[Strategy] = None,
    client_manager: Optional[ClientManager] = None,
) -> History:
    """Start a Flower Driver API server.

    Parameters
    ----------
    driver : Driver
        The Driver object to use.
    server : Optional[flwr.server.Server] (default: None)
        A server implementation, either `flwr.server.Server` or a subclass
        thereof. If no instance is provided, then `start_driver` will create
        one.
    config : Optional[ServerConfig] (default: None)
        Currently supported values are `num_rounds` (int, default: 1) and
        `round_timeout` in seconds (float, default: None).
    strategy : Optional[flwr.server.Strategy] (default: None).
        An implementation of the abstract base class
        `flwr.server.strategy.Strategy`. If no strategy is provided, then
        `start_server` will use `flwr.server.strategy.FedAvg`.
    client_manager : Optional[flwr.server.ClientManager] (default: None)
        An implementation of the class `flwr.server.ClientManager`. If no
        implementation is provided, then `start_driver` will use
        `flwr.server.SimpleClientManager`.

    Returns
    -------
    hist : flwr.server.history.History
        Object containing training and evaluation metrics.
    """
    # Initialize the Driver API server and config
    initialized_server, initialized_config = init_defaults(
        server=server,
        config=config,
        strategy=strategy,
        client_manager=client_manager,
    )
    log(
        INFO,
        "Starting Flower ServerApp, config: %s",
        initialized_config,
    )
    log(INFO, "")

    # Start the thread updating nodes
    thread, f_stop, c_done = start_update_client_manager_thread(
        driver, initialized_server.client_manager()
    )

    # Wait until the node registration done
    c_done.wait()

    # Start training
    hist = run_fl(
        server=initialized_server,
        config=initialized_config,
    )

    # Terminate the thread
    f_stop.set()
    thread.join()

    return hist