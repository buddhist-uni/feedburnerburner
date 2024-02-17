#!/bin/python3

import time
import numpy as np
import joblib
from math import log10
from random import gauss
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
from .feed import FeedEntry

from settings import db_dir

stemmer = SnowballStemmer('english')
tokenizer = NLTKWordTokenizer()
def stemmed_nltk_tokenizer(s):
    tokens = tokenizer.tokenize(s)
    tokens = [t[:-1] if t.endswith('.') else t for t in tokens]
    return [stemmer.stem(token) for token in tokens]

class LinearModel(BaseModel):
    NAME = "Linear Regressor"
    DESCRIPTION = "A Ridge classifier over normalized Tf-Idf Vectors"
    MIN_DATA = "25 likes and dislikes"
    MIN_DOCS_WITH_TERM = 2
    MIN_CHI2 = 0.02

    def __init__(self, corpus: Corpus = None, **kwargs):
        super().__init__(corpus=corpus, **kwargs)
        if corpus:
            if len(corpus.liked) < 25 or len(corpus.disliked) < 25:
                self.status = ModelStatus.Invalid
        self.cutoff = kwargs.get('cutoff')
        if kwargs.get('model_file'):
            self.model = joblib.load(db_dir.joinpath(kwargs['model_file']))
            self.vectorizer = joblib.load(db_dir.joinpath(kwargs['vectorizer_file']))
            self.rmse = kwargs.get('rmse', 0)

    def get_cutoff(self):
        return self.cutoff

    def analyze(self):
        corpus = [entry for entry in self.corpus.entries - self.corpus.unseen]
        Y = [1.0 if entry.status == "liked" else 0.0 for entry in corpus]
        with yaspin(text="Compiling dictionary..."):
            dictionary = self.create_dictionary(corpus, Y)
        self.vectorizer = TfidfVectorizer(
            tokenizer=stemmed_nltk_tokenizer,
            lowercase=False,
            token_pattern=None,
            vocabulary=dictionary,
        )
        print(f"Compiled a dictionary with {len(dictionary)} terms")
        with yaspin(text="Extracting features..."):
            X = self.vectorizer.fit_transform((
                entry.get_text_for_training() for entry in corpus
            ))
        started_at = time.time()
        self.model = RidgeClassifierCV(
            store_cv_values=True,
            scoring="balanced_accuracy",
            alphas=(0.00001, 0.0001, 0.001, 0.01, 0.1, 1),
        )
        with yaspin(text="Fitting a model..."):
            self.model.fit(X, Y)
        alpha = round(log10(self.model.alpha_)) + 5
        print(f"Done fitting in {time.time() - started_at:.3f} seconds.\nSelected smoothing level {alpha} (α={self.model.alpha_})")
        # Use the model's provided Cross Validation data to select the optimal cutoff
        # and to accurately estimate the model's accuracy because the default
        # cutoff of 0 is not always ideal and because model.best_score_ is overfit
        Y_p = self.model.cv_values_
        true_positives = [(Y_p[i][0][alpha], Y[i]) for i in range(len(Y))]
        true_positives.sort()
        true_positives = np.array(true_positives)
        positive_cumsum = np.cumsum(true_positives[:, 1])
        # roll the cumsum forward by one because the cutoff will include that item
        positive_cumsum = np.roll(positive_cumsum, 1)
        positive_cumsum[0] = 0
        recall = 1.0 - (positive_cumsum / len(self.corpus.liked))
        precision = (len(self.corpus.liked) - positive_cumsum) / np.arange(len(Y), 0, -1)
        accuracy = np.sqrt(recall * precision)
        max_accuracy_i = np.argmax(accuracy)
        self.cutoff = float(round(0.5*(true_positives[max_accuracy_i][0]+true_positives[max_accuracy_i-1][0]), 5))
        self.accuracy = accuracy[max_accuracy_i]
        self.precision = precision[max_accuracy_i]
        self.recall = recall[max_accuracy_i]
        final_errors = [
            (Y_p[i,0,alpha] - self.cutoff)
            if (Y[i]==0.0 and Y_p[i,0,alpha]>self.cutoff) or (Y[i]==1.0 and Y_p[i,0,alpha]<self.cutoff)
            else 0
            for i in range(len(Y))
        ]
        self.rmse = round(float(np.sqrt(np.mean(np.square(final_errors)))), 5)
        print(f"Cross-validation predicts an accuracy of P={self.precision*100:.0f}% × R={self.recall*100:.0f}% = {self.accuracy*100:.1f}% at cutoff={self.cutoff}±{self.rmse}\n")
        self.status = ModelStatus.Analyzed

    def score(self, post: FeedEntry):
        x = self.vectorizer.transform([post.get_text_for_training(), ])
        y_p = self.model.decision_function(x)
        if not self.rmse:
            return float(y_p[0])
        return float(y_p[0]) + gauss(sigma=self.rmse)

    def get_parameters(self):
        ret = super().get_parameters()
        ret['cutoff'] = self.cutoff
        VECTORIZER_FNAME = 'linear-vectorizer.pkl'
        MODEL_FNAME = 'linear-model.pkl'
        joblib.dump(self.vectorizer, db_dir.joinpath(VECTORIZER_FNAME), compress=True)
        joblib.dump(self.model, db_dir.joinpath(MODEL_FNAME), compress=True)
        ret['model_file'] = MODEL_FNAME
        ret['vectorizer_file'] = VECTORIZER_FNAME
        ret['rmse'] = self.rmse
        return ret

    def create_dictionary(self, corpus: list, Y: list):
        word_counter = CountVectorizer(tokenizer=stemmed_nltk_tokenizer, lowercase=False, token_pattern=None)
        word_counts = word_counter.fit_transform((
            entry.get_text_for_training() for entry in corpus
        ))
        _, docs_with_term, _ = destructure(word_counts)
        has_min_docs = np.bincount(docs_with_term) >= self.MIN_DOCS_WITH_TERM
        trans = TfidfTransformer()
        X = trans.fit_transform(word_counts)
        cs, _ = chi2(X, Y)
        reasonable_chi2 = cs > self.MIN_CHI2
        return word_counter.get_feature_names_out()[has_min_docs & reasonable_chi2]

