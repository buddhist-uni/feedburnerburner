#!/bin/python3

from .empty import EmptyModel
from .metadata import TagModel

ALL_MODELS = [
    EmptyModel,
    TagModel,
]

MODELS = {m.__class__.__name__: m for m in ALL_MODELS}
