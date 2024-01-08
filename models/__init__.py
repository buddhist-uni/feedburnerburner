#!/bin/python3

from .empty import EmptyModel
from .metadata import TagModel

ALL_MODELS = [
    EmptyModel,
    TagModel,
]

MODELS = {m.NAME: m for m in ALL_MODELS}
