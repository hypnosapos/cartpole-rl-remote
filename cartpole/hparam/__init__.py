# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

import numpy as np


def hparam_steps(hparam_values, hparam_type=float):
    if type(hparam_values) is list or type(hparam_values) is tuple:
        if len(hparam_values) >= 3:
            return np.arange(*[hparam_type(hparam_value) for hparam_value in hparam_values], dtype=hparam_type)
        else:
            return hparam_values
    else:
        raise ValueError('Value (or range of values)'
                         ' of hyperparameter {} is required'
                         ' (e.g [<min_val>, <max_value>, <step>])'.format(hparam_values))
