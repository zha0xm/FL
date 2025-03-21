"""Flower type definitions."""


from dataclasses import dataclass
from typing import Any, Union, Callable, Optional
from enum import Enum

import numpy.typing as npt


NDArray = npt.NDArray[Any]
NDArrays = list[NDArray]

# The following union type contains Python types corresponding to ProtoBuf types that
# ProtoBuf considers to be "Scalar Value Types", even though some of them arguably do
# not conform to other definitions of what a scalar is. Source:
# https://developers.google.com/protocol-buffers/docs/overview#scalar
Scalar = Union[bool, bytes, float, int, str]

# Value types for common.MetricsRecord
MetricsScalar = Union[int, float]
MetricsScalarList = Union[list[int], list[float]]
MetricsRecordValues = Union[MetricsScalar, MetricsScalarList]
# Value types for common.ConfigsRecord
ConfigsScalar = Union[MetricsScalar, str, bytes, bool]
ConfigsScalarList = Union[MetricsScalarList, list[str], list[bytes], list[bool]]
ConfigsRecordValues = Union[ConfigsScalar, ConfigsScalarList]

Metrics = dict[str, Scalar]
MetricsAggregationFn = Callable[[list[tuple[int, Metrics]]], Metrics]

Config = dict[str, Scalar]
Properties = dict[str, Scalar]

# Value type for user configs
UserConfigValue = Union[bool, float, int, str]
UserConfig = dict[str, UserConfigValue]


class Code(Enum):
    """Client status codes."""

    OK = 0
    GET_PROPERTIES_NOT_IMPLEMENTED = 1
    GET_PARAMETERS_NOT_IMPLEMENTED = 2
    FIT_NOT_IMPLEMENTED = 3
    EVALUATE_NOT_IMPLEMENTED = 4


@dataclass
class Status:
    """Client status."""

    code: Code
    message: str


@dataclass
class Parameters:
    """Model parameters."""

    tensors: list[bytes]
    tensor_type: str


@dataclass
class GetParametersIns:
    """Parameters request for a client."""

    config: Config


@dataclass
class GetParametersRes:
    """Response when asked to return parameters."""

    status: Status
    parameters: Parameters


@dataclass
class FitIns:
    """Fit instructions for a client."""

    parameters: Parameters
    config: dict[str, Scalar]


@dataclass
class FitRes:
    """Fit response from a client."""

    status: Status
    parameters: Parameters
    num_examples: int
    metrics: dict[str, Scalar]


@dataclass
class EvaluateIns:
    """Evaluate instructions for a client."""

    parameters: Parameters
    config: dict[str, Scalar]


@dataclass
class EvaluateRes:
    """Evaluate response from a client."""

    status: Status
    loss: float
    num_examples: int
    metrics: dict[str, Scalar]


@dataclass
class GetPropertiesIns:
    """Properties request for a client."""

    config: Config


@dataclass
class GetPropertiesRes:
    """Properties response from a client."""

    status: Status
    properties: Properties


@dataclass
class ReconnectIns:
    """ReconnectIns message from server to client."""

    seconds: Optional[int]


@dataclass
class DisconnectRes:
    """DisconnectRes message from client to server."""

    reason: str


@dataclass
class RunStatus:
    """Run status information."""

    status: str
    sub_status: str
    details: str


@dataclass
class Run:
    """Run details."""

    run_id: int
    fab_id: str
    fab_version: str
    fab_hash: str
    override_config: UserConfig
    pending_at: str
    starting_at: str
    running_at: str
    finished_at: str
    status: RunStatus

    @classmethod
    def create_empty(cls, run_id: int) -> "Run":
        """Return an empty Run instance."""
        return cls(
            run_id=run_id,
            fab_id="",
            fab_version="",
            fab_hash="",
            override_config={},
            pending_at="",
            starting_at="",
            running_at="",
            finished_at="",
            status=RunStatus(status="", sub_status="", details=""),
        )
    

class RunNotRunningException(BaseException):
    """Raised when a run is not running."""