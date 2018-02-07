from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

from runner_remote import GymRunnerRemote
from qlearning_agent import QLearningAgent


class Agent(QLearningAgent):
    def __init__(self):
        super().__init__(4, 2)

    def build_model(self):
        model = Sequential()
        model.add(Dense(12, activation='relu', input_dim=4))
        model.add(Dense(12, activation='relu'))
        model.add(Dense(2))
        model.compile(Adam(lr=0.001), 'mse')

        return model

    def save_model(self):
        self.model.save("Cartpole-rl-remote.h5")


if __name__ == '__main__':
    gym = GymRunnerRemote('CartPole-v0')
    agent = Agent()

    gym.train(agent, 100)
    gym.run(agent, 50)
