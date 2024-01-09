#!/bin/python3

from enum import Enum
from math import sqrt

from .feed import FeedEntry


class Corpus:
    def __init__(self):
        self.entries = set()
        self.liked = set()
        self.unseen = set()

    def add_entry(self, entry: FeedEntry):
        self.entries.add(entry)
        if entry.status == 'liked':
            self.liked.add(entry)
        if entry.status == 'unread':
            self.unseen.add(entry)

    @property
    def disliked(self):
        return self.entries - self.liked - self.unseen

    def calculate_like_ratio(self):
        return float(len(self.liked)) / \
            float(len(self.entries) - len(self.unseen))


ModelStatus = Enum('ModelStatus', ['Unanalyzed', 'Analyzed', 'Invalid'])


class BaseModel:
    NAME = "Base Model"
    DESCRIPTION = "Overwrite this in your subclass"

    def __init__(self, corpus: Corpus = None, **kwargs):
        self.corpus = corpus
        self.status = ModelStatus.Unanalyzed

    def analyze(self):
        raise NotImplementedError()

    def get_status_summary(self):
        match self.status:
            case ModelStatus.Unanalyzed:
                return "Unanalyzed"
            case ModelStatus.Invalid:
                return "Insufficient Data"
            case ModelStatus.Analyzed:
                return f"P={self.precision*100.0:.0f}% R={self.recall*100:.0f}% => {sqrt(self.precision*self.recall)*100:.0f}%"

    def get_parameters(self):
        return {}

    def is_refinable(self):
        return False

    def refine(self):
        raise NotImplementedError()

    def split_and_rank_posts(self, posts: list[FeedEntry]):
        cutoff = self.get_cutoff()
        highpri = []
        lowpri = []
        for post in posts:
            score = self.score(post)
            if score >= cutoff:
                highpri.append((-score, post))
            else:
                lowpri.append((-score, post))
        return ([obj for _, obj in sorted(highpri)],
                [obj for _, obj in sorted(lowpri)])
