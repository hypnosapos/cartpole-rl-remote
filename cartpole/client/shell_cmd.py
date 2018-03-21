#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from multiprocessing import Process
import argparse
import os
import sys
import logging

from cartpole.cartpole_agent import Agent
from cartpole.runner_remote import GymRunnerRemote

logging.basicConfig(
    format='%(asctime)s %(name)-12s %(processName)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
LOG = logging.getLogger('cartpole')

PROCESSES = []


def env(*_vars, **kwargs):
    """Search for the first defined of possibly many env vars.

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.

    """
    for var in _vars:
        value = os.getenv(var, None)
        if value:
            return value
    return kwargs.get('default', '')


def train(gym, agent, args):
    LOG.info("Training...")
    gym.train(agent, args.episodes, render=args.render, file_name=args.file_name)


def run(gym, agent, args):
    LOG.info("Running...")
    gym.run(agent, args.episodes, render=args.render, host=args.host, grpc_client=args.grpc_client)


def main(argv=sys.argv[1:]):

    parser = argparse.ArgumentParser(prog='cartpole')
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='required subcommands',
                                       help='Subcommands')
    train_subcommand = subparsers.add_parser('train')
    train_subcommand.set_defaults(func=train)

    run_subcommand = subparsers.add_parser('run')
    run_subcommand.set_defaults(func=run)

    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Activate verbose mode')

    parser.add_argument('-r', '--render', action='store_true',
                        help='Activate view')

    parser.add_argument('-e', '--episodes', type=int, default=50,
                        help='Number of episodes')

    run_subcommand.add_argument('--host', required=True,
                                help='Host IP')

    run_subcommand.add_argument('--grpc-client', action='store_true',
                                help='If present then GRCP client will be use instead of REST')

    run_subcommand.add_argument('--runners', type=int, default=1,
                                help='Number of processes, defaults to 1')

    train_subcommand.add_argument('-f', '--file-name',
                                  default='Cartpole-rl-remote.h5',
                                  help='The name of the h5 file. Defaults to "Cartpole-rl-remote.h5"')
    train_subcommand.add_argument('--gamma', type=float,
                                  default='.095',
                                  help='Gamma value')
    train_subcommand.add_argument('--epsilon', type=float,
                                  default='1.0',
                                  help='Epsilon value')
    train_subcommand.add_argument('--epsilon-decay', type=float,
                                  default='0.995',
                                  help='Epsilon decay value')
    train_subcommand.add_argument('--epsilon-min', type=float,
                                  default='0.1',
                                  help='Min value of epsilon')
    train_subcommand.add_argument('--batch-size', type=int,
                                  default='32',
                                  help='Batch size')
    train_subcommand.add_argument('--runners', type=int, default=1,
                                  help='Number of processes, defaults to 1')

    args = parser.parse_args(argv)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        LOG.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
        LOG.setLevel(logging.INFO)

    for m in range(0, args.runners):
        gym = GymRunnerRemote()
        agent = Agent()
        LOG.info("Runner %s/%s", m+1, args.runners)
        p = Process(target=args.func, args=(gym, agent, args), name='runner-{}'.format(m+1))
        PROCESSES.append(p)
        p.start()

    for p in PROCESSES:
        p.join()


if __name__ == "__main__":

    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        LOG.warning("... cartpole command was interrupted")
        sys.exit(2)
    except Exception as ex:
        LOG.error('Unexpected error: %s' % ex)
        sys.exit(1)
    finally:
        for p in PROCESSES:
            p.terminate()
    sys.exit(0)
