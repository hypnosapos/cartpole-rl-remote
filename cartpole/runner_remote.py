# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
import numpy as np

from gym.envs.registration import register
from .client.seldon.client import SeldonClient

register(
    id='CartPoleExtra-v0',
    entry_point='gym.envs.classic_control:CartPoleEnv',
    max_episode_steps=7000,
    reward_threshold=195.0
)

import gym


class GymRunnerRemote:
    def __init__(self, gym_name='CartPoleExtra-v0', max_timesteps=100000):

        self.env = gym.make(gym_name)
        self.max_timesteps = max_timesteps
        self.seldon_client = None
        self.log = logging.getLogger('cartpole')

    def train(self, agent, num_episodes, render=False, file_name='Cartpole-rl-remote.h5'):
        return self.run(agent, num_episodes, train={'file_name': file_name}, render=render)

    def run(self, agent, num_episodes, train=None, render=False, host='localhost', grpc_client=False):
        scores = []
        for episode in range(num_episodes):
            state = self.env.reset().reshape(1, self.env.observation_space.shape[0])
            total_reward = 0

            for t in range(self.max_timesteps):

                if render:
                    self.env.render()
                try:
                    action, request, response = agent.select_action(state, host=host, train=train, grpc_client=grpc_client)

                    # execute the selected action
                    next_state, reward, done, _ = self.env.step(action)

                    if not train and (request and response):
                            agent.feedback(host, request, response, reward, done,
                                           call_type='grpc' if grpc_client else 'rest')

                    next_state = next_state.reshape(1, self.env.observation_space.shape[0])

                    # record the results of the step
                    if train:
                        agent.record(state, action, reward, next_state, done)

                    total_reward += reward
                    state = next_state

                except Exception as e:
                    self.log.error('Unexpected error: %s', e)
                    done = True
                    break
                finally:
                    if done:
                        break

            # train the agent based on a sample of past experiences
            if train:
                agent.replay()

            self.log.info("episode: %s/%s | score: %s | e: %s",
                          episode + 1, num_episodes, total_reward, agent.epsilon)
            scores.append(total_reward)
        if train:
            self.log.info("Saving model...")
            agent.save_model(train['file_name'])

        self.log.info('Episodes: %(episodes)i  MaxScore: %(max_score)f'
                      '  MinScore: %(min_score)f  AvgScore: %(avg_score)f',
                      {'episodes': num_episodes,
                       'max_score': np.max(scores),
                       'min_score': np.min(scores),
                       'avg_score': np.average(scores)})
