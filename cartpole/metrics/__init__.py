# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import visdom
import time
import logging

LOG = logging.getLogger(__name__)


def get_visdom_conn(**opts):
    vis = visdom.Visdom(**opts)
    startup_sec = 15
    LOG.debug("Checking visdom connectivity ...")
    while not vis.check_connection() and startup_sec > 0:
        time.sleep(1)
        startup_sec -= 1
    assert vis.check_connection(), 'No connection could be formed quickly'

    return vis
