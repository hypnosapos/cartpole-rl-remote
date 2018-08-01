# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from .visdom import VisdomCallback
from .modeldb import ModelDBCallback

__all__ = [
    'create_callback',
]

CALLBACKS = {
    'visdom': VisdomCallback,
    'modeldb': ModelDBCallback
}


def create_callback(callback_id, **conf):
    if callback_id not in CALLBACKS.keys():
        raise NotImplemented("Not implemented callback for id {}."
                             " Choose one of: {}".format(callback_id, CALLBACKS.keys()))
    else:
        return CALLBACKS[callback_id](**conf)
