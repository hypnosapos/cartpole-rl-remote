# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

from tensorflow.keras import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import TensorBoard


def get_model(model_type='keras', model_spec={}):
    assert model_type == 'keras', "Only keras models are supported yet."
    return get_keras_model(model_spec=model_spec)


def get_keras_model(model_spec={}):
    # TODO: model tuning, pass layers and other config to get custom models
    model = Sequential()
    model.add(Dense(12, activation='relu', input_dim=4))
    model.add(Dense(12, activation='relu'))
    model.add(Dense(2))
    model.compile(Adam(lr=0.001), 'mse')
    return model


def get_tensorboard_callback(**kwargs):
    return TensorBoard(**kwargs)
