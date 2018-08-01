#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import multiprocessing
from shutil import copy2
import argparse
import os
import sys
import uuid
import logging
import json
import time
from itertools import product
import numpy as np
from datetime import datetime

import cartpole.metrics.callbacks as callbacks

import cartpole.hparam as hp
from cartpole.runner_remote import GymRunnerRemote
from cartpole.qlearning_agent import (
    QLearningAgent as Agent,
    HPARAMS_SCHEMA
)


STR_NOW = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
EXPERIMENT_GROUP = uuid.uuid1()

LOG_FORMAT = '%(asctime)s %(name)-12s [' + str(EXPERIMENT_GROUP) \
             + '] %(processName)-12s %(threadName)-12s %(levelname)-8s %(message)s'
logging.basicConfig(
    format=LOG_FORMAT,
    datefmt='%Y-%m-%d %H:%M:%S',
)

LOG = logging.getLogger('cartpole')
LOG.setLevel(logging.NOTSET)

RESULTS = []


def train(episodes, render=False, hparams={}, model_config={}, file_name='cartpole-rl-remote',
          metrics_engine=None, metrics_config={}):
    LOG.info("Training ...")
    gym = GymRunnerRemote(name=multiprocessing.current_process().name,
                          metrics_engine=metrics_engine, metrics_config=metrics_config)
    agent = Agent(hparams=hparams, model_config=model_config)
    return gym.train(agent, episodes, render=render, file_name=file_name)


def run(episodes, render=False, host='localhost', grpc_client=False,
        metrics_engine=None, metrics_config={}):
    LOG.info("Running ...")
    gym = GymRunnerRemote(name=multiprocessing.current_process().name,
                          metrics_engine=metrics_engine, metrics_config=metrics_config)
    agent = Agent(metrics_engine=metrics_engine, metrics_config=metrics_config)
    return gym.run(agent, episodes, render=render, host=host, grpc_client=grpc_client)


def process_callback(callback_args, callback_metrics):

    LOG.debug("Processing callbacks ...")
    exp_ids, num_episodes, scores, hparams, max_scores, _time, file_name = list(zip(*callback_args))
    max_score = np.max(max_scores)
    max_score_ind = np.argmax(max_scores)

    result = dict(
        model=file_name[max_score_ind],
        score=max_score,
        hparams=hparams[max_score_ind]
    )

    callback_metrics.callback(
        exp_ids, num_episodes, scores, hparams, max_scores, _time, max_score, max_score_ind)

    model_dir = os.path.dirname(file_name[max_score_ind])
    _, file_extension = os.path.splitext(file_name[max_score_ind])
    model_file = 'cartpole-rl-remote{}'.format(file_extension)
    model_path = os.path.join(model_dir, model_file if model_dir else model_file)
    copy2(file_name[max_score_ind], model_path)

    print(json.dumps(result))

    RESULTS.append(result)


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
                        choices=(None, 'visdom', 'modeldb'),  # TODO: Add tensorboard callbacks
                        help='Type of metrics visualizer engine.')

    parser.add_argument('--metrics-config', type=json.loads,
                        default={},
                        help='Metrics configuration. Contents are different according to "metrics-engine" arg.'
                             ' Visdom example: {"server": "http://localhost"}.'
                             ' ModelDB example: {}.')  # TODO: ' Tensorboard example: {"log_dir": "/tmp/logs/"}.'

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

    metrics_engine = args.metrics_engine
    metrics_config = args.metrics_config
    callback_metrics = callbacks.create_callback(metrics_engine, **metrics_config)

    if args.func == train:

        hparams = {
            hparam_name: hp.hparam_steps(
                getattr(args, hparam_name),
                HPARAMS_SCHEMA.get(hparam_name).get('dtype')
            ) for hparam_name in HPARAMS_SCHEMA if hasattr(args, hparam_name)
        }

        # TODO: auto-modeling by custom config (get_model(**config)), defaults to {}
        _args = [(args.episodes, args.render, dict(zip(hparams.keys(), hparam_values)),
                  {}, args.file_name, metrics_engine, metrics_config)
                 for hparam_values in list(product(*hparams.values()))]
        with multiprocessing.Pool(len(_args)) as process_pool:
            results = process_pool.starmap_async(
                args.func,
                _args,
                callback=lambda callback_args: process_callback(callback_args, callback_metrics)
            )
            results.get()

    else:
        _args = [(args.episodes, args.render, args.host,
                  args.grpc_client, metrics_engine, metrics_config)
                 for _ in range(args.runners)]
        with multiprocessing.Pool(args.runners) as process_pool:
            results = process_pool.starmap_async(
                args.func,
                _args
            )
            results.get()


if __name__ == "__main__":

    try:
        import cartpole.metrics.callbacks as callbacks
        main(sys.argv[1:])
    except KeyboardInterrupt:
        LOG.warning("... cartpole command was interrupted")
        sys.exit(2)
    except Exception as ex:
        LOG.error('Unexpected error: %s' % ex)
        sys.exit(1)
    sys.exit(0)
