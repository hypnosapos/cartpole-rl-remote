# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from logging import Handler, Formatter
import numpy as np
import re
import collections

from cartpole.metrics import get_visdom_conn


class BaseVisdomHandler(Handler):
    """
    Base handler class which writes logging metrics to visdom server.
    More information about visdom at: https://github.com/facebookresearch/visdom
    """

    def __init__(self, opts={}):
        """
        Initializing visdom connection.
        """
        Handler.__init__(self)
        self.viz = get_visdom_conn(**opts)

    def emit(self, record):
        try:
            self._emit(record)
            self.flush()
        except Exception:
            self.handleError(record)

    def flush(self):
        self.acquire()
        try:
            if self.viz and hasattr(self.viz, "flush"):
                self.viz.flush()
        finally:
            self.release()

    def _emit(self, record):
        raise NotImplementedError(
            "emit not implemented for BaseVisdomHandler, which is an abstract class.")


class VisdomPlotHandler(BaseVisdomHandler):

    def __init__(self, name, plot_type, plot_opts={}, opts={}):
        """
        Plot your metrics
        :param name: name of window
        :param plot_type: Select one of: scatter, line or bar
        :param opts: Add particular options for each type of plot, for example,
        """
        super(VisdomPlotHandler, self).__init__(opts)
        self.name = name
        if plot_type not in ['scatter', 'line', 'bar']:
            raise ValueError('Select a valid type  of graph: scatter, line, bar')

        self.plot_type = plot_type
        self.plot_opts = plot_opts

        # Check the window does not exist yet
        if self.viz.win_exists(win=self.name, env=self.viz.env):
            raise ValueError('A window with name {} already exists in the env {}.'
                             .format(self.name, self.viz.env))

        self.win_fn = getattr(self.viz, plot_type)
        self.win = None

    def _emit(self, record):
        metric_entry = self.format(record)
        if metric_entry:
            x_y = (np.array(metric_entry.get('x')),
                   np.array(metric_entry.get('y')),)

            if self.plot_type == 'line':
                data = {'Y': x_y[1], 'X': x_y[0]}
            else:
                if x_y[1]:
                    data = {'X': x_y[0], 'Y': x_y[1]}
                else:
                    data = {'X': x_y[0]}
            if self.win and self.viz.win_exists(win=self.win, env=self.viz.env):
                self.win_fn(
                    **data,
                    win=self.win,
                    env=self.viz.env,
                    update='append'
                )
            else:
                self.win = self.win_fn(
                    **data,
                    env=self.viz.env,
                    opts=self.plot_opts)


class VisdomFormatter(Formatter):

    def __init__(self, metric_names, pattern=r"^(Metrics -)(.+)"):
        assert metric_names and type(metric_names) is dict, "It's required the metric name dict"
        assert pattern, "It's required a pattern to match entries to process."
        super(VisdomFormatter, self).__init__()
        self.metric_names = metric_names
        self.re = re.compile(pattern)
        self.re_metrics = [
            (metric_name_coor, re.compile(r"\s+%s:\s+(?P<%s>\d*\.?\d*)" % (metric_name, metric_name)),)
            for metric_name_coor, metric_name in metric_names.items()
        ]

    def format(self, record):
        s2match = super(VisdomFormatter, self).format(record)
        if s2match:
            metrics_match = self.re.match(s2match)
            if metrics_match and metrics_match.group(2):
                metric_values_dict = {}
                for metric_name_coor, metric_re in self.re_metrics:
                    re_metric_matches = metric_re.findall(metrics_match.group(2))
                    if re_metric_matches:
                        metric_values_dict[metric_name_coor] = float(re_metric_matches[0])
                if len(metric_values_dict.values()) == len(self.re_metrics):
                    # Skip entries if not all metrics are present
                    return {'x': [list(collections.OrderedDict(sorted(metric_values_dict.items(),
                                                                      key=lambda t: t[0])).values())]}

        return {}
