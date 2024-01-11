#!/bin/python3

from .empty import EmptyModel
from .metadata import TagModel
from .linear import LinearModel

ALL_MODELS = [
    EmptyModel,
    TagModel,
    LinearModel,
]

MODELS = {m.__name__: m for m in ALL_MODELS}
