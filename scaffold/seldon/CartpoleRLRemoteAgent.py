from tensorflow.keras.models import load_model
import numpy as np


class CartpoleRLRemoteAgent(object):

    def __init__(self):
        # The model under GCS bucket is the best one based on it highest score.
        # Get public info at: https://www.googleapis.com/storage/v1/b/cartpole-rl-models/o/cartpole-rl-remote.h5
        # Public URL: https://storage.googleapis.com/cartpole-rl-models/cartpole-rl-remote.h5
        self.model = load_model('gs://cartpole-rl-models/cartpole-rl-remote.h5')

    def predict(self, X, feature_names):
        # Send two element in order to avoid changing auto-generated module model_microservice.py
        return [[np.argmax(self.model.predict(X)[0])]]
