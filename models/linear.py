#!/bin/python3

import numpy as np
from math import log10
from scipy.sparse import find as destructure
from nltk.tokenize import NLTKWordTokenizer
from nltk.stem.snowball import SnowballStemmer
from sklearn.feature_extraction.text import (
    TfidfVectorizer,
    TfidfTransformer,
    CountVectorizer,
)
from sklearn.feature_selection import chi2
from sklearn.linear_model import RidgeClassifierCV
from yaspin import yaspin

from .base import BaseModel, Corpus, ModelStatus

stemmer = SnowballStemmer('english')
def stemmed_nltk_tokenizer(s):
    tokens = NLTKWordTokenizer().tokenize(s)
    tokens = [t[:-1] if t.endswith('.') else t for t in tokens]
    return [stemmer.stem(token) for token in tokens]

class LinearModel(BaseModel):
    NAME = "Linear Regressor"
    DESCRIPTION = "A Ridge classifier over normalized Tf-Idf Vectors"
    MIN_DATA = "25 likes and dislikes"
    MIN_DOCS_WITH_TERM = 1
    MIN_CHI2 = 0.02

    def __init__(self, corpus: Corpus = None, **kwargs):
        super().__init__(corpus=corpus, **kwargs)
        if corpus:
            if len(corpus.liked) < 25 or len(corpus.disliked) < 25:
                self.status = ModelStatus.Invalid

    def analyze(self):
        corpus = [entry for entry in self.corpus.entries - self.corpus.unseen]
        Y = [1.0 if entry.status == "liked" else 0.0 for entry in corpus]
        with yaspin(text="Compiling dictionary"):
            dictionary = self.create_dictionary(corpus, Y)
        self.vectorizer = TfidfVectorizer(
            tokenizer=stemmed_nltk_tokenizer,
            lowercase=False,
            token_pattern=None,
            vocabulary=dictionary,
        )
        with yaspin(text="Extracting features"):
            X = self.vectorizer.fit_transform((
                entry.get_text_for_training() for entry in corpus
            ))
        self.model = RidgeClassifierCV(
            store_cv_values=True,
            scoring="balanced_accuracy",
            alphas=(0.00001, 0.0001, 0.001, 0.01, 0.1, 1),
        )
        with yaspin(text="Fitting a model"):
            self.model.fit(X, Y)
        alpha = round(log10(self.model.alpha_)) + 5
        print(f"Done fitting.\nSelected smoothing level {alpha} (α={self.model.alpha_})")
        Y_p = self.model.cv_values_
        true_positives = [(Y_p[i][0][alpha], Y[i]) for i in range(len(Y))]
        true_positives.sort()
        true_positives = np.array(true_positives)
        positive_cumsum = np.cumsum(true_positives[:, 1])
        positive_cumsum = np.roll(positive_cumsum, 1)
        positive_cumsum[0] = 0
        recall = 1.0 - (positive_cumsum / len(self.corpus.liked))
        precision = (len(self.corpus.liked) - positive_cumsum) / np.arange(len(Y), 0, -1)
        accuracy = np.sqrt(recall * precision)
        max_accuracy_i = np.argmax(accuracy)
        self.cutoff = round(0.5*(true_positives[max_accuracy_i][0]+true_positives[max_accuracy_i-1][0]), 5)
        self.accuracy = accuracy[max_accuracy_i]
        self.precision = precision[max_accuracy_i]
        self.recall = recall[max_accuracy_i]
        print(f"Cross-validation predicts a max accuracy of {self.accuracy*100:.1f}% at cutoff={self.cutoff}")
        self.status = ModelStatus.Analyzed

    def create_dictionary(self, corpus: list, Y: list):
        word_counter = CountVectorizer(tokenizer=stemmed_nltk_tokenizer, lowercase=False, token_pattern=None)
        word_counts = word_counter.fit_transform((
            entry.get_text_for_training() for entry in corpus
        ))
        _, docs_with_term, _ = destructure(word_counts)
        has_min_docs = np.bincount(docs_with_term) > self.MIN_DOCS_WITH_TERM
        trans = TfidfTransformer()
        X = trans.fit_transform(word_counts)
        cs, _ = chi2(X, Y)
        reasonable_chi2 = cs > self.MIN_CHI2
        return word_counter.get_feature_names_out()[has_min_docs & reasonable_chi2]

