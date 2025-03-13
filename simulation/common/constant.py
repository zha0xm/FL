"""Flower constants."""


from __future__ import annotations


# Message TTL
MESSAGE_TTL_TOLERANCE = 1e-1


class MessageType:
    """Message type."""

    TRAIN = "train"
    EVALUATE = "evaluate"
    QUERY = "query"

    def __new__(cls) -> MessageType:
        """Prevent instantiation."""
        raise TypeError(f"{cls.__name__} cannot be instantiated.")
    

class MessageTypeLegacy:
    """Legacy message type."""

    GET_PROPERTIES = "get_properties"
    GET_PARAMETERS = "get_parameters"

    def __new__(cls) -> MessageTypeLegacy:
        """Prevent instantiation."""
        raise TypeError(f"{cls.__name__} cannot be instantiated.")
    
    
class SType:
    """Serialisation type."""

    NUMPY = "numpy.ndarray"

    def __new__(cls) -> SType:
        """Prevent instantiation."""
        raise TypeError(f"{cls.__name__} cannot be instantiated.")