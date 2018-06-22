import os
import unittest
import logging

# required for tensorflow logging control
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf
import pandas as pd
import numpy as np
import enso
from enso.download import generic_download
from sklearn.metrics import accuracy_score

from finetune import LanguageModelClassifier

SST_FILENAME = "SST-binary.csv"


class TestLanguageModelClassifier(unittest.TestCase):

    n_sample = 100
    n_hidden = 768

    @staticmethod
    def _download_sst(self):
        """
        Download Stanford Sentiment Treebank to enso `data` directory
        """
        generic_download(
            url="https://s3.amazonaws.com/enso-data/SST-binary.csv",
            text_column="Text",
            target_column="Target",
            filename=SST_FILENAME
        )

    @staticmethod
    def _dataset_path(filename):
        enso_project_dir = os.path.dirname(os.path.dirname(enso.__file__))
        return os.path.abspath(
            os.path.join(enso_project_dir, 'Data', 'Classify', filename)
        )

    def setUp(self):
        self.dataset = pd.read_csv(self._dataset_path(SST_FILENAME))
        tf.reset_default_graph()

    def test_fit_predict(self):
        """
        Ensure model training does not error out
        Ensure model returns predictions of the right type
        """
        model = LanguageModelClassifier(verbose=False)
        train_sample = self.dataset.sample(n=self.n_sample)
        valid_sample = self.dataset.sample(n=self.n_sample)
        model.fit(train_sample.Text, train_sample.Target)

        predictions = model.predict(valid_sample.Text)
        for prediction in predictions:
            self.assertIsInstance(prediction, (np.int, np.int64))

        probabilities = model.predict_proba(valid_sample.Text)
        for proba in probabilities:
            self.assertIsInstance(proba, dict)

    def test_save_load(self):
        """
        Ensure saving + loading does not cause errors
        Ensure saving + loading does not change predictions
        """
        model = LanguageModelClassifier(verbose=False)
        save_file = 'tests/saved-models/test-save-load'
        train_sample = self.dataset.sample(n=self.n_sample)
        valid_sample = self.dataset.sample(n=self.n_sample)
        model.fit(train_sample.Text, train_sample.Target)
        predictions = model.predict(valid_sample.Text)
        model.save(save_file)
        model = LanguageModelClassifier.load(save_file)
        new_predictions = model.predict(valid_sample.Text)
        for i, prediction in enumerate(predictions):
            self.assertEqual(prediction, new_predictions[i])

    def test_featurize(self):
        """
        Ensure featurization returns an array of the right shape
        Ensure featurization is still possible after fit
        """
        model = LanguageModelClassifier(verbose=False)
        train_sample = self.dataset.sample(n=self.n_sample)
        valid_sample = self.dataset.sample(n=self.n_sample)
        features = model.featurize(train_sample.Text)
        self.assertEqual(features.shape, (self.n_sample, self.n_hidden))
        model.fit(train_sample.Text, train_sample.Target)
        features = model.featurize(train_sample.Text)
        self.assertEqual(features.shape, (self.n_sample, self.n_hidden))