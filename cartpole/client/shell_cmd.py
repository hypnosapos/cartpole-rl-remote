#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import multiprocessing
from shutil import copy2
import argparse
import os
import sys
import logging
import json
from itertools import product
import numpy as np
from datetime import datetime

from cartpole.runner_remote import GymRunnerRemote
from cartpole.qlearning_agent import (
    QLearningAgent as Agent,
    HPARAMS_SCHEMA
)
from cartpole.metrics import get_visdom_conn
import cartpole.hparam as hp


LOG_FORMAT = '%(asctime)s %(name)-12s %(processName)-12s %(threadName)-12s %(levelname)-8s %(message)s'
logging.basicConfig(
    format=LOG_FORMAT,
    datefmt='%Y-%m-%d %H:%M:%S',
)

LOG = logging.getLogger('cartpole')
LOG.setLevel(logging.NOTSET)


STR_NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def train(episodes, render=False, hparams={}, model_config={}, file_name='cartpole-rl-remote', vis_config={}):
    LOG.info("Training...")
    gym = GymRunnerRemote(name=multiprocessing.current_process().name, vis_config=vis_config)
    agent = Agent(hparams=hparams, model_config=model_config)
    return gym.train(agent, episodes, render=render, file_name=file_name)


def run(episodes, render=False, host='localhost', grpc_client=False, vis_config={}):
    LOG.info("Running...")
    gym = GymRunnerRemote(name=multiprocessing.current_process().name, vis_config=vis_config)
    agent = Agent()
    return gym.run(agent, episodes, render=render, host=host, grpc_client=grpc_client)


def process_callback(callback_args, metrics_config={}):

    LOG.debug("Processing callbacks ...")
    exp_ids, scores, hparams, max_scores, _time, file_name = list(zip(*callback_args))
    max_score = np.max(max_scores)
    max_score_ind = np.argmax(max_scores)

    metrics_engine = metrics_config.get('engine')
    if metrics_engine:
        getattr(sys.modules[__name__],
                ('process_callback_%s' % metrics_engine))(
                    exp_ids, scores, hparams, max_scores, _time, max_score,
                    max_score_ind, metrics_config.get('config', {}))

    model_dir = os.path.dirname(file_name[max_score_ind])
    _, file_extension = os.path.splitext(file_name[max_score_ind])
    model_file = 'cartpole-rl-remote{}'.format(file_extension)
    model_path = os.path.join(model_dir, model_file if model_dir else model_file)
    copy2(file_name[max_score_ind], model_path)

    print(
        json.dumps(
            dict(
                model=file_name[max_score_ind],
                score=max_score,
                hparams=hparams[max_score_ind]
            )
        )
    )


def process_callback_visdom(exp_ids, scores, hparams, max_scores, _time, max_score, max_score_ind, config={}):

    vis = get_visdom_conn(**config)

    vis.boxplot(
        X=np.column_stack(scores),
        opts=dict(
            title='Experiment Scores',
            legend=exp_ids,
            width=1200,
            height=500,
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
    vis.text(
        text,
        opts=dict(
            title='Hyperparameters',
            width=1200,
            height=200
        )
    )


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(prog='cartpole')
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='required subcommands',
                                       help='Subcommands')
    train_subcommand = subparsers.add_parser('train')
    train_subcommand.set_defaults(func=train)

    run_subcommand = subparsers.add_parser('run')
    run_subcommand.set_defaults(func=run)

    parser.add_argument('-r', '--render', action='store_true',
                        help='Activate view')

    parser.add_argument('-e', '--episodes', type=int, default=50,
                        help='Number of episodes')

    parser.add_argument('--log-file',
                        help='Path of file where write logs to.')

    parser.add_argument('--log-level',
                        default='INFO',
                        choices=logging._levelToName.values(),
                        help='Log level (name). Defaults to INFO')

    parser.add_argument('--conf-file', type=json.load,
                        help='Pass all parameters from json config file')

    parser.add_argument('--metrics-engine',
                        default=None,
                        choices=(None, 'visdom', 'kibana', 'sphinx',),
                        help='Type of metrics visualizer engine.')

    parser.add_argument('--metrics-config', type=json.loads,
                        default={},
                        help='Metrics configuration. Contents are different accordign to "metrics-engine" arg'
                             'Example {"server": "http://localhost"}.')

    train_subcommand.add_argument('-f', '--file-name',
                                  default='cartpole-rl-remote',
                                  help='The name of the h5 file. Defaults to "cartpole-rl-remote"')

    run_subcommand.add_argument('--host', required=True,
                                help='Host IP')

    run_subcommand.add_argument('--grpc-client', action='store_true',
                                help='If present then GRCP client will be use instead of REST')

    run_subcommand.add_argument('--runners', type=int, default=1,
                                help='Number of runners, defaults to 1')

    for hparam_name, hparam in HPARAMS_SCHEMA.items():
        train_subcommand.add_argument('--{}'.format(hparam_name), type=hparam.get('dtype'), nargs='*',
                                      required=False,
                                      default=[hparam.get('default')],
                                      help='Hyperparameter {}'.format(hparam_name))

    args = parser.parse_args(argv)

    logging.basicConfig(level=getattr(logging, args.log_level))

    LOG.setLevel(level=args.log_level)

    if args.log_file:
        fh = logging.FileHandler(args.log_file)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        LOG.addHandler(fh)

    metrics_config = dict(
        engine=args.metrics_engine,
        config=dict()
    )

    if args.metrics_engine == 'visdom':
        metrics_config['config'].update(dict(server='http://localhost'))
    metrics_config['config'].update(args.metrics_config)

    if args.func == train:

        hparams = {
            hparam_name: hp.hparam_steps(
                getattr(args, hparam_name),
                HPARAMS_SCHEMA.get(hparam_name).get('dtype')
            ) for hparam_name in HPARAMS_SCHEMA if hasattr(args, hparam_name)
        }

        # TODO: auto-modeling by custom config (get_model(**config)), defaults to {}
        _args = [(args.episodes, args.render, dict(zip(hparams.keys(), hparam_values)),
                  {}, args.file_name, metrics_config['config']) for hparam_values in list(product(*hparams.values()))]

        with multiprocessing.Pool(len(_args)) as process_pool:
            results = process_pool.starmap_async(
                args.func,
                _args,
                callback=lambda callback_args: process_callback(callback_args, metrics_config)
            )
            results.get()

    else:
        _args = [(args.episodes, args.render, args.host,
                  args.grpc_client, metrics_config['config']) for _ in range(args.runners)]
        with multiprocessing.Pool(args.runners) as process_pool:
            results = process_pool.starmap_async(
                args.func,
                _args
            )
            results.get()


if __name__ == "__main__":

    try:
        main(sys.argv[1:])

    except KeyboardInterrupt:
        LOG.warning("... cartpole command was interrupted")
        sys.exit(2)
    except Exception as ex:
        LOG.error('Unexpected error: %s' % ex)
        sys.exit(1)
    sys.exit(0)
