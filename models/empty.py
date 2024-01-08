#!/bin/python3

from .base import BaseModel, ModelStatus

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
