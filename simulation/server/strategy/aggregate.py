"""Aggregation functions for strategy implementations."""


from functools import reduce, partial
from typing import Union

import numpy as np

from common import NDArray, NDArrays, FitRes, parameters_to_ndarrays
from server.client_proxy import ClientProxy


def aggregate(results: list[tuple[NDArrays, int]]) -> NDArrays:
    """Compute weighted average."""
    # Calculate the total number of examples used during training
    num_examples_total = sum(num_examples for (_, num_examples) in results)

    # Create a list of weights, each multiplied by the related number of examples
    weighted_weights = [
        [layer * num_examples for layer in weights] for weights, num_examples in results
    ]

    # Compute average weights of each layer
    weights_prime: NDArrays = [
        reduce(np.add, layer_updates) / num_examples_total
        for layer_updates in zip(*weighted_weights)
    ]
    return weights_prime


def aggregate_inplace(results: list[tuple[ClientProxy, FitRes]]) -> NDArrays:
    """Compute in-place weighted average."""
    # Count total examples
    num_examples_total = sum(fit_res.num_examples for (_, fit_res) in results)

    # Compute scaling factors for each result
    scaling_factors = np.asarray(
        [fit_res.num_examples / num_examples_total for _, fit_res in results]
    )

    def _try_inplace(
        x: NDArray, y: Union[NDArray, np.float64], np_binary_op: np.ufunc
    ) -> NDArray:
        return (  # type: ignore[no-any-return]
            np_binary_op(x, y, out=x)
            if np.can_cast(y, x.dtype, casting="same_kind")
            else np_binary_op(x, np.array(y, x.dtype), out=x)
        )

    # Let's do in-place aggregation
    # Get first result, then add up each other
    params = [
        _try_inplace(x, scaling_factors[0], np_binary_op=np.multiply)
        for x in parameters_to_ndarrays(results[0][1].parameters)
    ]

    for i, (_, fit_res) in enumerate(results[1:], start=1):
        res = (
            _try_inplace(x, scaling_factors[i], np_binary_op=np.multiply)
            for x in parameters_to_ndarrays(fit_res.parameters)
        )
        params = [
            reduce(partial(_try_inplace, np_binary_op=np.add), layer_updates)
            for layer_updates in zip(params, res)
        ]

    return params


def weighted_loss_avg(results: list[tuple[int, float]]) -> float:
    """Aggregate evaluation results obtained from multiple clients."""
    num_total_evaluation_examples = sum(num_examples for (num_examples, _) in results)
    weighted_losses = [num_examples * loss for num_examples, loss in results]
    return sum(weighted_losses) / num_total_evaluation_examples