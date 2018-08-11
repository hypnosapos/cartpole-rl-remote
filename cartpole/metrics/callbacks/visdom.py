# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import numpy as np

from .callback import SummaryCallback

from cartpole.metrics import get_visdom_conn


class VisdomCallback(SummaryCallback):

    def __init__(self, **conf):
        super(VisdomCallback, self).__init__(**conf)
        self.vis = get_visdom_conn(**conf)

    def callback(self, exp_ids, num_episodes, scores, hparams,
                 max_scores, _time, max_score, max_score_ind, config={}):
        self.vis.boxplot(
            X=np.column_stack(scores),
            opts=dict(
                title='Experiment Scores',
                legend=exp_ids,
                width=2000,
                height=400,
                marginleft=60,
                marginright=60,
                marginbottom=80,
                margintop=60,
                fillarea=True,
                xlabel='Workers',
                boxpoints='all',
                ylabel='score'
            )
        )

        text = "".join(["<b>%s</b>:&nbsp;%s;&nbsp;Spent time:%s<br/>"
                        "" % (arg[0], arg[1], arg[2]) for arg in list(zip(exp_ids, hparams, _time))])
        text += ("<br/><br/>Best score: <b>%.3f</b>"
                 " was reached with worker <b>%s</b>" % (max_score, exp_ids[max_score_ind]))
        self.vis.text(
            text,
            opts=dict(
                title='Hyperparameters',
                width=2000,
                height=200
            )
        )
