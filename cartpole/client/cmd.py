#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import argparse
import os
import sys
from ..cartpole_agent import Agent
from ..runner_remote import GymRunnerRemote

cli = argparse.ArgumentParser(prog='cartpole')


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


def main():
    cli.add_argument('-v', '--verbose', action='store_true',
                     help='Activate verbose mode')

    cli.add_argument('-m', '--mode', choices=('train', 'run',), required=True,
                     help='Execution mode: Train or Running')

    cli.add_argument('-e', '--episodes', type=int, default=50,
                     help='Number of episodes')

    cmd_args = cli.parse_args()

    gym = GymRunnerRemote('CartPole-v0')
    agent = Agent()

    if cmd_args.mode == 'train':

        print("Training...")
        gym.train(agent, cmd_args.episodes)
    else:

        print("Running...")
        gym.run(agent, cmd_args.episodes)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("... cartpole command was interrupted", file=sys.stderr)
        sys.exit.exit(2)
    except Exception as ex:
        print('Unexpected error: %s' % ex)
        sys.exit(1)
    sys.exit(0)
