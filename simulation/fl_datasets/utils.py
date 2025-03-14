"""Utils for FederatedDataset."""


import warnings
from typing import Optional, Union, cast

from .partitioner import Partitioner, IidPartitioner
from .preprocessor import Preprocessor, Merger


tested_datasets = [
    "mnist",
    "ylecun/mnist",
    "cifar10",
    "uoft-cs/cifar10",
    "fashion_mnist",
    "zalando-datasets/fashion_mnist",
    "sasha/dog-food",
    "zh-plus/tiny-imagenet",
    "scikit-learn/adult-census-income",
    "cifar100",
    "uoft-cs/cifar100",
    "svhn",
    "ufldl-stanford/svhn",
    "sentiment140",
    "stanfordnlp/sentiment140",
    "speech_commands",
    "LIUM/tedlium",
    "flwrlabs/femnist",
    "flwrlabs/ucf101",
    "flwrlabs/ambient-acoustic-context",
    "jlh/uci-mushrooms",
    "Mike0307/MNIST-M",
    "flwrlabs/usps",
    "scikit-learn/iris",
    "flwrlabs/pacs",
    "flwrlabs/cinic10",
    "flwrlabs/caltech101",
    "flwrlabs/office-home",
    "flwrlabs/fed-isic2019",
]


def _instantiate_partitioners(
    partitioners: dict[str, Union[Partitioner, int]]
) -> dict[str, Partitioner]:
    """Transform the partitioners from the initial format to instantiated objects.

    Parameters
    ----------
    partitioners : Dict[str, Union[Partitioner, int]]
        Dataset split to the Partitioner or a number of IID partitions.

    Returns
    -------
    partitioners : Dict[str, Partitioner]
        Partitioners specified as split to Partitioner object.
    """
    instantiated_partitioners: dict[str, Partitioner] = {}
    if isinstance(partitioners, dict):
        for split, partitioner in partitioners.items():
            if isinstance(partitioner, Partitioner):
                instantiated_partitioners[split] = partitioner
            elif isinstance(partitioner, int):
                instantiated_partitioners[split] = IidPartitioner(
                    num_partitions=partitioner
                )
            else:
                raise ValueError(
                    f"Incorrect type of the 'partitioners' value encountered. "
                    f"Expected Partitioner or int. Given {type(partitioner)}"
                )
    else:
        raise ValueError(
            f"Incorrect type of the 'partitioners' encountered. "
            f"Expected Dict[str, Union[int, Partitioner]]. "
            f"Given {type(partitioners)}."
        )
    return instantiated_partitioners


def _instantiate_merger_if_needed(
    merger: Optional[Union[Preprocessor, dict[str, tuple[str, ...]]]]
) -> Optional[Preprocessor]:
    """Instantiate `Merger` if preprocessor is merge_config."""
    if merger and isinstance(merger, dict):
        merger = Merger(merge_config=merger)
    return cast(Optional[Preprocessor], merger)


def _check_if_dataset_tested(dataset: str) -> None:
    """Check if the dataset is in the narrowed down list of the tested datasets."""
    if dataset not in tested_datasets:
        warnings.warn(
            f"The currently tested dataset are {tested_datasets}. Given: {dataset}.",
            stacklevel=1,
        )