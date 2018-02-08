from keras.models import load_model
import numpy as np


class CartpoleRlRemoteAgent(object):

    def __init__(self):
        self.model = load_model('Cartpole-rl-remote.h5')

    def predict(self, X, feature_names):
        print("Esto en un POST")
        print(X)
        print(np.array(X).shape)
        return [np.argmax(self.model.predict(X)[0])]
