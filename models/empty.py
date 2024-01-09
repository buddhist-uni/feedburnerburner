#!/bin/python3

from .base import BaseModel, ModelStatus
from .feed import FeedEntry


class EmptyModel(BaseModel):
    NAME = "No Filter"
    DESCRIPTION = "Marks all posts as \"important\""
    MIN_DATA = "installing this program"

    def __init__(self, corpus):
        super().__init__(corpus)
        self.status = ModelStatus.Analyzed
        self.recall = 1.0

    @property
    def precision(self):
        return self.corpus.calculate_like_ratio()

    def score(self, post: FeedEntry):
        return 1

    def get_cutoff(self):
        return 1
