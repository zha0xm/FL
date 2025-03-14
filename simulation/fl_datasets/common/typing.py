"""Flower Datasets type definitions."""


from typing import Any

import numpy as np
import numpy.typing as npt

NDArray = npt.NDArray[Any]
NDArrayInt = npt.NDArray[np.int_]
NDArrayFloat = npt.NDArray[np.float64]
NDArrays = list[NDArray]