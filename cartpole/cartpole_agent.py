# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

from cartpole.qlearning_agent import QLearningAgent


class Agent(QLearningAgent):
    def __init__(self):
        super().__init__(4, 2)

    def build_model(self):
        model = Sequential()
        model.add(Dense(12, activation='relu', input_dim=4))
        model.add(Dense(12, activation='relu'))
        model.add(Dense(2))
        model.compile(Adam(lr=0.001), 'mse')

        # load the weights of the model if reusing previous training session
        # model.load_weights("Cartpole-rl-remote.h5")

        return model

    def save_model(self):
        self.model.save("Cartpole-rl-remote.h5")
