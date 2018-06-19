# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from collections import deque, OrderedDict
import numpy as np
import random
import logging

from .client.seldon.client import SeldonClient
from .model import get_model


HPARAMS_SCHEMA = {
    'gamma': {
        'dtype': float,
        'default': .095
    },
    'epsilon': {
        'dtype': float,
        'default': 1.
    },
    'epsilon_min': {
        'dtype': float,
        'default': .1
    },
    'epsilon_decay': {
        'dtype': float,
        'default': .0995
    },
    'batch_size': {
        'dtype': int,
        'default': 32
    }
}

DEFAULT_HPARAMS = {
    key: value.get('default', .0) for key, value in HPARAMS_SCHEMA.items()
}


class QLearningAgent(object):

    def __init__(self, state_size=4, action_size=2, hparams={}, model_config={}):

        self.model = get_model(**model_config)
        self.state_size = state_size
        self.action_size = action_size
        self.hparams = {**DEFAULT_HPARAMS}

        # hyperparameters
        if hparams:
            assert all(element in DEFAULT_HPARAMS.keys() for element in hparams.keys()),\
                "Invalid hyperparameters, choose one of: %s" % DEFAULT_HPARAMS.keys()
            self.hparams.update(hparams)

        [setattr(self, key, value) for key, value in self.hparams.items()]

        # agent state
        self.memory = deque(maxlen=2000)
        self.seldon_client = None
        self.host = None
        self.log = logging.getLogger(__name__)
        self.log.info('Hyperparams:: gamma: %(gamma)f epsilon: %(epsilon)f '
                      'epsilon_decay: %(epsilon_decay)f epsilon_min: %(epsilon_min)f batch_size: %(batch_size)i',
                      self.hparams)

    def select_action(self, state, host=None, train=None, grpc_client=False):
        random_exploit = np.random.rand()
        if train and random_exploit <= self.epsilon:
            return random.randrange(self.action_size), None, None
        elif train and random_exploit > self.epsilon:
            return np.argmax(self.model.predict(state)[0]), None, None
        else:
            value, request, response = self.request(host, state, call_type='grpc' if grpc_client else 'rest')

            return value, request, response

    def record(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return 0

        minibatch = random.sample(self.memory, self.batch_size)
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))
            target_f = self.model.predict(state)
            target_f[0][action] = target
            self.model.fit(state, target_f, epochs=1, verbose=0)

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def __check_seldon_client(self, host):
        if not self.seldon_client or host != self.host:
            self.seldon_client = SeldonClient(host)
            self.host = host

    def request(self, host, state, call_type='rest'):
        self.__check_seldon_client(host)
        __request_by_client_type = \
            self.seldon_client.grpc_request if call_type == 'grpc' else self.seldon_client.rest_request
        request, response = __request_by_client_type(state)
        if call_type == 'grpc':
            value = int(response.data.tensor.values[0])
        else:
            value = int(response.get('data').get('tensor').get('values')[0])

        return value, request, response

    def feedback(self, host, request, response, reward, done, call_type='rest'):
        self.__check_seldon_client(host)
        __feedback_by_client_type = \
            self.seldon_client.grpc_feedback if call_type == 'grpc' else self.seldon_client.rest_feedback
        response = __feedback_by_client_type(request, response, reward, done)
        return response
