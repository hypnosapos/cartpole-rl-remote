# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
import threading
import numpy as np
from datetime import datetime

from gym.envs.registration import register

from .metrics.log.visdom import VisdomFormatter, VisdomPlotHandler

register(
    id='CartPoleExtra-v0',
    entry_point='gym.envs.classic_control:CartPoleEnv',
    max_episode_steps=7000,
    reward_threshold=195.0
)

import gym


class GymRunnerRemote:
    def __init__(self, name='gym_runner_remote',
                 gym_name='CartPoleExtra-v0',
                 max_timesteps=100000,
                 vis_config={}):
        self.name = name
        self.env = gym.make(gym_name)
        self.max_timesteps = max_timesteps
        self.seldon_client = None
        self.log = logging.getLogger(__name__)
        if vis_config and self.log.isEnabledFor(logging.DEBUG):
            vfmt = VisdomFormatter(['episode', 'score'])
            handler = VisdomPlotHandler(
                self.name, 'scatter',
                plot_opts=dict(
                    title=self.name,
                    xlabels='episodes',
                    ylabel='score',
                    markersize=5
                ),
                opts=vis_config
            )
            handler.setFormatter(vfmt)
            self.log.addHandler(handler)
        self.tstart = datetime.now()

    def train(self, agent, num_episodes, render=False, file_name='cartpole-rl-remote'):
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
                    action, request, response = agent.select_action(state, host=host, train=train,
                                                                    grpc_client=grpc_client)

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
                self.log.debug("Metrics - episode: %i/%i | score: %.3f | e: %s",
                               episode + 1, num_episodes, total_reward, agent.epsilon)
            else:
                self.log.debug("Metrics - episode: %i/%i | score: %.3f",
                               episode + 1, num_episodes, total_reward)

            scores.append(total_reward)
        if train:
            file_name = "{}-{}.h5".format(train['file_name'], self.name.split('-')[-1:][0])
            self.log.info("Saving model {} ...".format(file_name))
            agent.model.save(file_name)

        max_score = np.max(scores)
        _time = datetime.now() - self.tstart
        self.log.info('Episodes: %(episodes)i  MaxScore: %(max_score)f'
                      '  MinScore: %(min_score)f  AvgScore: %(avg_score)f'
                      ' SpentTime: %(time)s',
                      {'episodes': num_episodes,
                       'max_score': np.max(scores),
                       'min_score': np.min(scores),
                       'avg_score': np.average(scores),
                       'time': _time})
        if train:
            return self.name, scores, agent.hparams, max_score, _time, file_name
        else:
            return self.name, scores, agent.hparams, max_score, _time, None
