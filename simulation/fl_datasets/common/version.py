"""Flower Datasets package version helper.

The code is an exact copy from flwr.
"""


import importlib.metadata as importlib_metadata


def _check_package(name: str) -> tuple[str, str]:
    version: str = importlib_metadata.version(name)
    return name, version


def _version() -> tuple[str, str]:
    """Read and return Flower Dataset package name and version.

    Returns
    -------
    package_name, package_version : Tuple[str, str]
    """
    for name in ["flwr-datasets", "flwr-datasets-nightly"]:
        try:
            return _check_package(name)
        except importlib_metadata.PackageNotFoundError:
            pass

    return ("unknown", "unknown")


package_name, package_version = _version()