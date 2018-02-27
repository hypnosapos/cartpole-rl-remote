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


This project is intended to play with Cart Pole Game using Reinforcement Learning.

Install
=======

Install this python module to train or run the RL model under the wood.

Requirements:
- pip

Remotely
--------

The most widely known way to install a python package is by **pip** command.
The python package is available at [pypi repository](https://pypi.org/project/cartpole-rl-remote/) (legacy repo [here](https://pypi.python.org/pypi/cartpole-rl-remote)).

Just type this ``pip`` command to install it from pypi package repository::

 pip install cartpole-rl-remote


Alternatively it's possible to install it by using any of these URLs:

* ``pip install git+https://github.com/davsuacar/cartpole-rl-remote[@<git_ref>]#egg=cartpole-rl-remote``
* ``pip install <release_file>``

Where [@<git_ref>] is an optional reference to a git reference (i.e: @master, v0.1.6) and
<release_file> is the URL of one release file at https://github.com/davsuacar/cartpole-rl-remote/releases

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

  cartpole train -e 5000


The output of the training command is an h5 file (a trained model serialized as hdf5).

Running
=======

In order to run the model, launch this command in your shell::

  cartpole run -e 100



Doc
===

See all doc at `here
 doc/model.rst`_.

