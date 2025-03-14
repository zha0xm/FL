"""Custom types for Flower servers."""


from typing import Callable

from common import Context

from .driver import Driver
from .serverapp_components import ServerAppComponents

ServerAppCallable = Callable[[Driver, Context], None]
Workflow = Callable[[Driver, Context], None]
ServerFn = Callable[[Context], ServerAppComponents]