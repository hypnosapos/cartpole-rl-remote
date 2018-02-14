
from gym.envs.registration import register
from client import send_feedback_rest

register(
            id='CartPoleExtra-v0',
            entry_point='gym.envs.classic_control:CartPoleEnv',
            max_episode_steps=7000,
            reward_threshold=195.0,
        )

import gym
class GymRunnerRemote:
    def __init__(self, env_id, max_timesteps=100000):

        self.env = gym.make('CartPoleExtra-v0')
        self.max_timesteps = max_timesteps

    def calc_reward(self, state, action, gym_reward, next_state, done):
        return gym_reward

    def train(self, agent, num_episodes):
        return self.run(agent, num_episodes, do_train=True)

    def run(self, agent, num_episodes, do_train=False):
        for episode in range(num_episodes):
            state = self.env.reset().reshape(1, self.env.observation_space.shape[0])
            total_reward = 0

            for t in range(self.max_timesteps):
                self.env.render()
                request, response, action = agent.select_action(state, do_train)

                # execute the selected action
                next_state, reward, done, _ = self.env.step(action)

                print(reward, done)

                send_feedback_rest(request, response, reward)

                next_state = next_state.reshape(1, self.env.observation_space.shape[0])
                reward = self.calc_reward(state, action, reward, next_state, done)

                # record the results of the step
                if do_train:
                    agent.record(state, action, reward, next_state, done)

                total_reward += reward
                state = next_state
                if done:
                    break

            # train the agent based on a sample of past experiences
            if do_train:
                agent.replay()

            print("episode: {}/{} | score: {} | e: {:.3f}".format(
                episode + 1, num_episodes, total_reward, agent.epsilon))

        if do_train:
            print("Saving model...")
            agent.save_model()




