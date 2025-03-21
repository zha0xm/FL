"""Flower ClientApp."""


import inspect
from typing import Optional, Callable
from collections.abc import Iterator
from contextlib import contextmanager

from common import Message, Context, MessageType
from common.logger import warn_deprecated_feature, warn_preview_feature
from client.message_handler.message_handler import handle_legacy_message_from_msgtype
from client.mod.utils import make_ffn

from .typing import ClientFnExt, Mod, ClientAppCallable


def _alert_erroneous_client_fn() -> None:
    raise ValueError(
        "A `ClientApp` cannot make use of a `client_fn` that does "
        "not have a signature in the form: `def client_fn(context: "
        "Context)`. You can import the `Context` like this: "
        "`from flwr.common import Context`"
    )


def _inspect_maybe_adapt_client_fn_signature(client_fn: ClientFnExt) -> ClientFnExt:
    client_fn_args = inspect.signature(client_fn).parameters

    if len(client_fn_args) != 1:
        _alert_erroneous_client_fn()

    first_arg = list(client_fn_args.keys())[0]
    first_arg_type = client_fn_args[first_arg].annotation

    if first_arg_type is str or first_arg == "cid":
        # Warn previous signature for `client_fn` seems to be used
        warn_deprecated_feature(
            "`client_fn` now expects a signature `def client_fn(context: Context)`."
            "The provided `client_fn` has signature: "
            f"{dict(client_fn_args.items())}. You can import the `Context` like this:"
            " `from flwr.common import Context`"
        )


@contextmanager
def _empty_lifespan(_: Context) -> Iterator[None]:
    yield


class ClientAppException(Exception):
    """Exception raised when an exception is raised while executing a ClientApp."""

    def __init__(self, message: str):
        ex_name = self.__class__.__name__
        self.message = f"\nException {ex_name} occurred. Message: " + message
        super().__init__(self.message)


class ClientApp:
    """Flower ClientApp.

    Examples
    --------
    Assuming a typical `Client` implementation named `FlowerClient`, you can wrap it in
    a `ClientApp` as follows:

    >>> class FlowerClient(NumPyClient):
    >>>     # ...
    >>>
    >>> def client_fn(context: Context):
    >>>    return FlowerClient().to_client()
    >>>
    >>> app = ClientApp(client_fn)
    """

    def __init__(
        self,
        client_fn: Optional[ClientFnExt] = None,  # Only for backward compatibility
        mods: Optional[list[Mod]] = None,
    ) -> None:
        self._mods: list[Mod] = mods if mods is not None else []

        # Create wrapper function for `handle`
        self._call: Optional[ClientAppCallable] = None
        if client_fn is not None:

            client_fn = _inspect_maybe_adapt_client_fn_signature(client_fn)

            def ffn(
                message: Message,
                context: Context,
            ) -> Message:  # pylint: disable=invalid-name
                out_message = handle_legacy_message_from_msgtype(
                    client_fn=client_fn, message=message, context=context
                )
                return out_message

            # Wrap mods around the wrapped handle function
            self._call = make_ffn(ffn, mods if mods is not None else [])

        # Step functions
        self._train: Optional[ClientAppCallable] = None
        self._evaluate: Optional[ClientAppCallable] = None
        self._query: Optional[ClientAppCallable] = None
        self._lifespan = _empty_lifespan

    def __call__(self, message: Message, context: Context) -> Message:
        """Execute `ClientApp`."""
        with self._lifespan(context):
            # Execute message using `client_fn`
            if self._call:
                return self._call(message, context)

            # Execute message using a new
            if message.metadata.message_type == MessageType.TRAIN:
                if self._train:
                    return self._train(message, context)
                raise ValueError("No `train` function registered")
            if message.metadata.message_type == MessageType.EVALUATE:
                if self._evaluate:
                    return self._evaluate(message, context)
                raise ValueError("No `evaluate` function registered")
            if message.metadata.message_type == MessageType.QUERY:
                if self._query:
                    return self._query(message, context)
                raise ValueError("No `query` function registered")

            # Message type did not match one of the known message types abvoe
            raise ValueError(f"Unknown message_type: {message.metadata.message_type}")

    def train(
        self, mods: Optional[list[Mod]] = None
    ) -> Callable[[ClientAppCallable], ClientAppCallable]:
        """Return a decorator that registers the train fn with the client app.

        Examples
        --------
        Registering a train function:

        >>> app = ClientApp()
        >>>
        >>> @app.train()
        >>> def train(message: Message, context: Context) -> Message:
        >>>    print("ClientApp training running")
        >>>    # Create and return an echo reply message
        >>>    return message.create_reply(content=message.content())

        Registering a train function with a function-specific modifier:

        >>> from flwr.client.mod import message_size_mod
        >>>
        >>> app = ClientApp()
        >>>
        >>> @app.train(mods=[message_size_mod])
        >>> def train(message: Message, context: Context) -> Message:
        >>>    print("ClientApp training running with message size mod")
        >>>    return message.create_reply(content=message.content())
        """

        def train_decorator(train_fn: ClientAppCallable) -> ClientAppCallable:
            """Register the train fn with the ServerApp object."""
            if self._call:
                raise _registration_error(MessageType.TRAIN)

            warn_preview_feature("ClientApp-register-train-function")

            # Register provided function with the ClientApp object
            # Wrap mods around the wrapped step function
            self._train = make_ffn(train_fn, self._mods + (mods or []))

            # Return provided function unmodified
            return train_fn

        return train_decorator

    def evaluate(
        self, mods: Optional[list[Mod]] = None
    ) -> Callable[[ClientAppCallable], ClientAppCallable]:
        """Return a decorator that registers the evaluate fn with the client app.

        Examples
        --------
        Registering an evaluate function:

        >>> app = ClientApp()
        >>>
        >>> @app.evaluate()
        >>> def evaluate(message: Message, context: Context) -> Message:
        >>>    print("ClientApp evaluation running")
        >>>    # Create and return an echo reply message
        >>>    return message.create_reply(content=message.content())

        Registering an evaluate function with a function-specific modifier:

        >>> from flwr.client.mod import message_size_mod
        >>>
        >>> app = ClientApp()
        >>>
        >>> @app.evaluate(mods=[message_size_mod])
        >>> def evaluate(message: Message, context: Context) -> Message:
        >>>    print("ClientApp evaluation running with message size mod")
        >>>    # Create and return an echo reply message
        >>>    return message.create_reply(content=message.content())
        """

        def evaluate_decorator(evaluate_fn: ClientAppCallable) -> ClientAppCallable:
            """Register the evaluate fn with the ServerApp object."""
            if self._call:
                raise _registration_error(MessageType.EVALUATE)

            warn_preview_feature("ClientApp-register-evaluate-function")

            # Register provided function with the ClientApp object
            # Wrap mods around the wrapped step function
            self._evaluate = make_ffn(evaluate_fn, self._mods + (mods or []))

            # Return provided function unmodified
            return evaluate_fn

        return evaluate_decorator

    def query(
        self, mods: Optional[list[Mod]] = None
    ) -> Callable[[ClientAppCallable], ClientAppCallable]:
        """Return a decorator that registers the query fn with the client app.

        Examples
        --------
        Registering a query function:

        >>> app = ClientApp()
        >>>
        >>> @app.query()
        >>> def query(message: Message, context: Context) -> Message:
        >>>    print("ClientApp query running")
        >>>    # Create and return an echo reply message
        >>>    return message.create_reply(content=message.content())

        Registering a query function with a function-specific modifier:

        >>> from flwr.client.mod import message_size_mod
        >>>
        >>> app = ClientApp()
        >>>
        >>> @app.query(mods=[message_size_mod])
        >>> def query(message: Message, context: Context) -> Message:
        >>>    print("ClientApp query running with message size mod")
        >>>    # Create and return an echo reply message
        >>>    return message.create_reply(content=message.content())
        """

        def query_decorator(query_fn: ClientAppCallable) -> ClientAppCallable:
            """Register the query fn with the ServerApp object."""
            if self._call:
                raise _registration_error(MessageType.QUERY)

            warn_preview_feature("ClientApp-register-query-function")

            # Register provided function with the ClientApp object
            # Wrap mods around the wrapped step function
            self._query = make_ffn(query_fn, self._mods + (mods or []))

            # Return provided function unmodified
            return query_fn

        return query_decorator

    def lifespan(
        self,
    ) -> Callable[
        [Callable[[Context], Iterator[None]]], Callable[[Context], Iterator[None]]
    ]:
        """Return a decorator that registers the lifespan fn with the client app.

        The decorated function should accept a `Context` object and use `yield`
        to define enter and exit behavior.

        Examples
        --------
        >>> app = ClientApp()
        >>>
        >>> @app.lifespan()
        >>> def lifespan(context: Context) -> None:
        >>>     # Perform initialization tasks before the app starts
        >>>     print("Initializing ClientApp")
        >>>
        >>>     yield  # ClientApp is running
        >>>
        >>>     # Perform cleanup tasks after the app stops
        >>>     print("Cleaning up ClientApp")
        """

        def lifespan_decorator(
            lifespan_fn: Callable[[Context], Iterator[None]]
        ) -> Callable[[Context], Iterator[None]]:
            """Register the lifespan fn with the ServerApp object."""
            warn_preview_feature("ClientApp-register-lifespan-function")

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

            # Register provided function with the ClientApp object
            # Ignore mypy error because of different argument names (`_` vs `context`)
            self._lifespan = decorated_lifespan  # type: ignore

            # Return provided function unmodified
            return lifespan_fn

        return lifespan_decorator
    

def _registration_error(fn_name: str) -> ValueError:
    return ValueError(
        f"""Use either `@app.{fn_name}()` or `client_fn`, but not both.

        Use the `ClientApp` with an existing `client_fn`:

        >>> class FlowerClient(NumPyClient):
        >>>     # ...
        >>>
        >>> def client_fn(context: Context):
        >>>     return FlowerClient().to_client()
        >>>
        >>> app = ClientApp(
        >>>     client_fn=client_fn,
        >>> )

        Use the `ClientApp` with a custom {fn_name} function:

        >>> app = ClientApp()
        >>>
        >>> @app.{fn_name}()
        >>> def {fn_name}(message: Message, context: Context) -> Message:
        >>>    print("ClientApp {fn_name} running")
        >>>    # Create and return an echo reply message
        >>>    return message.create_reply(
        >>>        content=message.content()
        >>>    )
        """,
    )