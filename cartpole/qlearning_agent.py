from collections import deque
import numpy as np
import random
import abc

from .client.seldon.client import SeldonClient


class QLearningAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size

        # hyperparameters
        self.gamma = 0.95  # discount rate on future rewards
        self.epsilon = 1.0  # exploration rate
        self.epsilon_decay = 0.995  # the decay of epsilon after each training batch
        self.epsilon_min = 0.1  # the minimum exploration rate permissible
        self.batch_size = 32  # maximum size of the batches sampled from memory

        # agent state
        self.model = self.build_model()
        self.memory = deque(maxlen=2000)
        self.seldon_client = None
        self.host = None

    @abc.abstractmethod
    def build_model(self):
        return None

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
