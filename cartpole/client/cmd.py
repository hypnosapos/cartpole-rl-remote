#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import argparse
import os
import sys
import logging

from cartpole.cartpole_agent import Agent
from cartpole.runner_remote import GymRunnerRemote


logging.basicConfig(
    format=format or '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
)

LOG = logging.getLogger('cartpole')


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
    gym.train(agent, args.episodes, args.render, args.file_name)


def run(gym, agent, args):
    LOG.info("Running...")
    gym.run(agent, args.episodes, args.render)


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

    train_subcommand.add_argument('-e', '--episodes', type=int, default=250,
                                  help='Number of episodes')

    run_subcommand.add_argument('-e', '--episodes', type=int, default=50,
                                help='Number of episodes')

    train_subcommand.add_argument('-f', '--file-name',
                                  default='Cartpole-rl-remote.h5',
                                  help='The name of the h5 file. Defaults to "Cartpole-rl-remote.h5"')

    args = parser.parse_args(argv)
    if args.verbose:
        LOG.setLevel(logging.DEBUG)

    gym = GymRunnerRemote('CartPole-v0')
    agent = Agent()

    args.func(gym, agent, args)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print("... cartpole command was interrupted", file=sys.stderr)
        sys.exit.exit(2)
    except Exception as ex:
        print('Unexpected error: %s' % ex)
        sys.exit(1)
    sys.exit(0)
