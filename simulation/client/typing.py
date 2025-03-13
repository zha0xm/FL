"""Custom types for Flower clients."""


from typing import Callable

from common import Context, Message

from .client import Client as Client

# Compatibility
ClientFn = Callable[[str], Client]
ClientFnExt = Callable[[Context], Client]

ClientAppCallable = Callable[[Message, Context], Message]
Mod = Callable[[Message, Context, ClientAppCallable], Message]