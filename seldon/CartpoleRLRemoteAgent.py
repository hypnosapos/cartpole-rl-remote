from keras.models import load_model
import numpy as np


class CartpoleRLRemoteAgent(object):

    def __init__(self):
        self.model = load_model('models/Cartpole-rl-remote.h5')

    def predict(self, X, feature_names):
        element = np.argmax(self.model.predict(X)[0])
        # Send two element ion order to avoid change auto-generated module model_microservice.py
        return [element, element]
