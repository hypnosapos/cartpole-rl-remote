# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import visdom
import time


def get_visdom_conn(**opts):
    try:
        vis = visdom.Visdom(**opts)
        startup_sec = 15
        while not vis.check_connection() and startup_sec > 0:
            time.sleep(1)
            startup_sec -= 1
        assert vis.check_connection(), 'No connection could be formed quickly'

    except Exception as e:
        if vis:
            vis.close()
        raise ConnectionError(
            "Unexpected error was raised {} \n"
            "Trying to establish connection with"
            " visdom server with parameters: {}".format(e, opts))

    return vis
