#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import numpy as np
import json
import argparse
import sys

from cartpole.client.seldon.client import SeldonClient


def main():

    parser = argparse.ArgumentParser(description='Test visdom server.')
    parser.add_argument('--visdom-config', type=json.loads,
                        default=None,
                        help='The visdom server configuration to send metrics'
                             '. Example \'{"server": "http://localhost", "env": "run"}\''
                             '. By default there is not a visualizer.')
    parser.add_argument('-api-server',
                        help='The seldon api server.')
    parser.add_argument('-router-name',
                        help='Name of router.')
    parser.add_argument('-pref-branch',
                        type=int,
                        help='The branch all traffic will be redirected to.')
    parser.add_argument('--num-reqs', type=int,
                        default=100,
                        help='Number of requests.')

    args = parser.parse_args()

    sclient = SeldonClient(args.api_server)

    sclient.force_branch_router(
        np.array([[0, 0, 1, 1]]),
        pref_branch=args.pref_branch,
        iters=args.num_reqs,
        router_name=args.router_name,
        vis_config=args.visdom_config
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        print('Unexpected error: %s' % ex)
        sys.exit(1)
    sys.exit(0)
