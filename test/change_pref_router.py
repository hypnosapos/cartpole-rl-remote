#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
import numpy as np
from cartpole.client.seldon.client import SeldonClient


sclient = SeldonClient("35.195.234.39")

sclient.force_branch_router(
    np.array([[0, 0, 1, 1]]),
    pref_branch=2,
    iters=10000,
    routing_name='eg-router',
    # Plot route/feedback on visdom server
    vis_config=dict(
        server='http://localhost'
    )
)
