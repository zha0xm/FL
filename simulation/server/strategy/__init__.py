"""Contains the strategy abstraction and different implementations."""


from .fedavg import FedAvg as FedAvg
from .stategy import Strategy as Strategy

__all__ = [
    "FedAvg",
    "Strategy",
]