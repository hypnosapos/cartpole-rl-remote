Cartpole RL Remote
==================
.. image:: https://circleci.com/gh/hypnosapos/cartpole-rl-remote/tree/master.svg?style=svg
   :target: https://circleci.com/gh/hypnosapos/cartpole-rl-remote/tree/master
   :alt: Build Status
.. image:: https://img.shields.io/pypi/v/modeldb-basic.svg?style=flat-square
   :target: https://pypi.org/project/modeldb-basic
   :alt: Version
.. image:: https://img.shields.io/pypi/pyversions/cartpole-rl-remote.svg?style=flat-square
   :target: https://pypi.org/project/cartpole-rl-remote
   :alt: Python versions
.. image:: https://codecov.io/gh/hypnosapos/cartpole-rl-remote/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/hypnosapos/cartpole-rl-remote
   :alt: Coverage

This project is intended to play with Cart Pole Game using Reinforcement Learning by a remote agent.

Install
=======

Install this python module to train or run the RL model under the wood.

Requirements:
- python >=3.5
- pip

You may launch all needed components using docker (or docker-compose) instead

Remotely
--------

The most widely known way to install a python package is by **pip** command.
The python package is available at [pypi repository](https://pypi.org/project/cartpole-rl-remote/) (legacy repo [here](https://pypi.python.org/pypi/cartpole-rl-remote)).

Just type this ``pip`` command to install it from pypi package repository::

 pip install cartpole-rl-remote


Alternatively it's possible to install it by using any of these URLs:

* ``pip install git+https://github.com/hypnosapos/cartpole-rl-remote[@<git_ref>]#egg=cartpole-rl-remote``
* ``pip install <release_file>``

Where [@<git_ref>] is an optional reference to a git reference (i.e: @master, v0.1.6) and
<release_file> is the URL of one release file at https://github.com/hypnosapos/cartpole-rl-remote/releases

Locally
-------

Previously downloaded in your host, somebody may install the package by typing::

 pip install -e .

or::

 python setup.py install



If the module was installed successfully, check out that "cartpole" command is available::

 cartpole --help



Training
========

Once we have the cartpole client installed as it was said above, just type this command to train a model::

  cartpole --log-level DEBUG -e 800 --metrics-engine visdom \
   --metrics-config '{"server": "http://localhost", "env": "train"}' train --gamma 0.097 0.099 0.001 --batch_size 32 33


The output of the training command is one or many h5 file/s (a trained model serialized as hdf5).

If you prefer launch the train with needed components just type::

   docker-compose up


* Adjust the command above for training

In order to view results take a look at: http://localhost:8097

Running
=======

In order to run the model, launch this command in your shell::

  cartpole -r --log-level DEBUG -e 5 --metrics-engine visdom \
   --metrics-config '{"server": "http://localhost", "env": "run"}' run --runners 5 --host "35.205.193.137"



If you prefer launch the train with needed components just type::

   docker-compose up


* Adjust the command above for running remote agent (default env name is 'main')

In order to view results take a look at: http://localhost:8097