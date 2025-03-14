"""Preprocessor."""


from typing import Callable

from datasets import DatasetDict

Preprocessor = Callable[[DatasetDict], DatasetDict]