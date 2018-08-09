# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging
from abc import ABC, abstractmethod


class SummaryCallback(ABC):

    def __init__(self, **conf):
        self.log = logging.getLogger(__name__)

    @abstractmethod
    def callback(self, exp_ids, num_episodes, scores, hparams,
                 max_scores, _time, max_score, max_score_ind, config={}):
        """
        Report an experiment metrics summary

        :param exp_ids: array with experiment ids
        :param num_episodes: number of episodes
        :param scores: scores
        :param hparams: hyper parameters
        :param max_scores: max value of score for each experiment
        :param _time: total time per experiment
        :param max_score: max score for the experiment group
        :param max_score_ind: max_score index
        :param config: metrics backend configuration
        """
        raise NotImplementedError(
            "Callback method not implemented yet.")
