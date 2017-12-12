from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

from runner import GymRunner
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

        # load the weights of the model if reusing previous training session
        # model.load_weights("models/cartpole-v0.h5")

        return model


if __name__ == '__main__':
    gym = GymRunner('CartPole-v0')
    agent = Agent()

    gym.train(agent, 100000)
    gym.run(agent, 5000)
