# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import os

from .callback import SummaryCallback

from modeldb.basic.Structs import Model, ModelConfig, ModelMetrics, Dataset
from modeldb.basic.ModelDbSyncerBase import Syncer


class ModelDBCallback(SummaryCallback):

    def __init__(self, **conf):
        super(ModelDBCallback, self).__init__(**conf)
        opts_syncer_path = conf.get("syncer_conf")
        if opts_syncer_path:
            syncer_path = os.path.abspath(opts_syncer_path)
            self.log.debug("ModelDB callback - Loading config from file {}".format(syncer_path))
        else:
            syncer_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../../scaffold/modeldb/syncer.json'))
            self.log.debug("ModelDB callback - Loading default config from file {}".format(syncer_path))

        self.syncer = Syncer.create_syncer_from_config(syncer_path)

    def callback(self, exp_ids, num_episodes, scores, hparams,
                 max_scores, _time, max_score, max_score_ind, config={}):

        opts_syncer_path = config.get("syncer_conf")
        if opts_syncer_path:
            syncer_path = os.path.abspath(opts_syncer_path)
            self.log.debug("ModelDB callback - Loading config from file {}".format(syncer_path))
        else:
            syncer_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '../../../scaffold/modeldb/syncer.json'))
            self.log.debug("ModelDB callback - Loading default config from file {}".format(syncer_path))

        for _arg in list(zip(exp_ids, hparams, max_scores, _time)):
            model = Model("RL", 'CartPole-{}'.format(_arg[0]), "https://github.com/hypnosapos/cartpole-rl-remote")
            self.syncer.sync_datasets(
                dict(gym=Dataset("/path/to/gym", {"episodes": num_episodes[0]}))
            )

            model_config = ModelConfig("RL", _arg[1])
            self.syncer.sync_model("gym", model_config, model)

            model_metrics = ModelMetrics({'score': _arg[2]})
            self.syncer.sync_metrics("gym", model, model_metrics)

            self.syncer.sync()
