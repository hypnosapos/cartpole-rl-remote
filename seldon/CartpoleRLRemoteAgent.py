from keras.models import load_model
import numpy as np


class CartpoleRLRemoteAgent(object):

    def __init__(self):
        self.model = load_model('models/cartpole-rl-remote.h5')

    def predict(self, X, feature_names):
        # Send two element in order to avoid changing auto-generated module model_microservice.py
        return [[np.argmax(self.model.predict(X)[0])]]
