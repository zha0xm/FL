"""Flower ServerApp."""


from typing import Optional, Callable
from contextlib import contextmanager
from collections.abc import Iterator

from common import Context
from common.logger import (
    warn_preview_feature,
    warn_deprecated_feature_with_example,
)
from .client_manager import ClientManager
from .server import Server
from .server_config import ServerConfig
from server.strategy import Strategy
from .driver import Driver
from .typing import ServerFn, ServerAppCallable
from .compat import start_driver

SERVER_FN_USAGE_EXAMPLE = """

        def server_fn(context: Context):
            server_config = ServerConfig(num_rounds=3)
            strategy = FedAvg()
            return ServerAppComponents(
                strategy=strategy,
                server_config=server_config,
        )

        app = ServerApp(server_fn=server_fn)
"""


@contextmanager
def _empty_lifespan(_: Context) -> Iterator[None]:
    yield

    
class ServerApp:  # pylint: disable=too-many-instance-attributes
    """Flower ServerApp.

    Examples
    --------
    Use the `ServerApp` with an existing `Strategy`:

    >>> def server_fn(context: Context):
    >>>     server_config = ServerConfig(num_rounds=3)
    >>>     strategy = FedAvg()
    >>>     return ServerAppComponents(
    >>>         strategy=strategy,
    >>>         server_config=server_config,
    >>>     )
    >>>
    >>> app = ServerApp(server_fn=server_fn)

    Use the `ServerApp` with a custom main function:

    >>> app = ServerApp()
    >>>
    >>> @app.main()
    >>> def main(driver: Driver, context: Context) -> None:
    >>>    print("ServerApp running")
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        server: Optional[Server] = None,
        config: Optional[ServerConfig] = None,
        strategy: Optional[Strategy] = None,
        client_manager: Optional[ClientManager] = None,
        server_fn: Optional[ServerFn] = None,
    ) -> None:
        if any([server, config, strategy, client_manager]):
            warn_deprecated_feature_with_example(
                deprecation_message="Passing either `server`, `config`, `strategy` or "
                "`client_manager` directly to the ServerApp "
                "constructor is deprecated.",
                example_message="Pass `ServerApp` arguments wrapped "
                "in a `flwr.server.ServerAppComponents` object that gets "
                "returned by a function passed as the `server_fn` argument "
                "to the `ServerApp` constructor. For example: ",
                code_example=SERVER_FN_USAGE_EXAMPLE,
            )

            if server_fn:
                raise ValueError(
                    "Passing `server_fn` is incompatible with passing the "
                    "other arguments (now deprecated) to ServerApp. "
                    "Use `server_fn` exclusively."
                )

        self._server = server
        self._config = config
        self._strategy = strategy
        self._client_manager = client_manager
        self._server_fn = server_fn
        self._main: Optional[ServerAppCallable] = None
        self._lifespan = _empty_lifespan

    def __call__(self, driver: Driver, context: Context) -> None:
        """Execute `ServerApp`."""
        with self._lifespan(context):
            # Compatibility mode
            if not self._main:
                if self._server_fn:
                    # Execute server_fn()
                    components = self._server_fn(context)
                    self._server = components.server
                    self._config = components.config
                    self._strategy = components.strategy
                    self._client_manager = components.client_manager
                start_driver(
                    server=self._server,
                    config=self._config,
                    strategy=self._strategy,
                    client_manager=self._client_manager,
                    driver=driver,
                )
                return

            # New execution mode
            self._main(driver, context)

    def main(self) -> Callable[[ServerAppCallable], ServerAppCallable]:
        """Return a decorator that registers the main fn with the server app.

        Examples
        --------
        >>> app = ServerApp()
        >>>
        >>> @app.main()
        >>> def main(driver: Driver, context: Context) -> None:
        >>>    print("ServerApp running")
        """

        def main_decorator(main_fn: ServerAppCallable) -> ServerAppCallable:
            """Register the main fn with the ServerApp object."""
            if self._server or self._config or self._strategy or self._client_manager:
                raise ValueError(
                    """Use either a custom main function or a `Strategy`, but not both.

                    Use the `ServerApp` with an existing `Strategy`:

                    >>> server_config = ServerConfig(num_rounds=3)
                    >>> strategy = FedAvg()
                    >>>
                    >>> app = ServerApp(
                    >>>     server_config=server_config,
                    >>>     strategy=strategy,
                    >>> )

                    Use the `ServerApp` with a custom main function:

                    >>> app = ServerApp()
                    >>>
                    >>> @app.main()
                    >>> def main(driver: Driver, context: Context) -> None:
                    >>>    print("ServerApp running")
                    """,
                )

            warn_preview_feature("ServerApp-register-main-function")

            # Register provided function with the ServerApp object
            self._main = main_fn

            # Return provided function unmodified
            return main_fn

        return main_decorator

    def lifespan(
        self,
    ) -> Callable[
        [Callable[[Context], Iterator[None]]], Callable[[Context], Iterator[None]]
    ]:
        """Return a decorator that registers the lifespan fn with the server app.

        The decorated function should accept a `Context` object and use `yield`
        to define enter and exit behavior.

        Examples
        --------
        >>> app = ServerApp()
        >>>
        >>> @app.lifespan()
        >>> def lifespan(context: Context) -> None:
        >>>     # Perform initialization tasks before the app starts
        >>>     print("Initializing ServerApp")
        >>>
        >>>     yield  # ServerApp is running
        >>>
        >>>     # Perform cleanup tasks after the app stops
        >>>     print("Cleaning up ServerApp")
        """

        def lifespan_decorator(
            lifespan_fn: Callable[[Context], Iterator[None]]
        ) -> Callable[[Context], Iterator[None]]:
            """Register the lifespan fn with the ServerApp object."""
            warn_preview_feature("ServerApp-register-lifespan-function")

            @contextmanager
            def decorated_lifespan(context: Context) -> Iterator[None]:
                # Execute the code before `yield` in lifespan_fn
                try:
                    if not isinstance(it := lifespan_fn(context), Iterator):
                        raise StopIteration
                    next(it)
                except StopIteration:
                    raise RuntimeError(
                        "lifespan function should yield at least once."
                    ) from None

                try:
                    # Enter the context
                    yield
                finally:
                    try:
                        # Execute the code after `yield` in lifespan_fn
                        next(it)
                    except StopIteration:
                        pass
                    else:
                        raise RuntimeError("lifespan function should only yield once.")

            # Register provided function with the ServerApp object
            # Ignore mypy error because of different argument names (`_` vs `context`)
            self._lifespan = decorated_lifespan  # type: ignore

            # Return provided function unmodified
            return lifespan_fn

        return lifespan_decorator
