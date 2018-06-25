Cartpole RL Remote
==================
.. image:: https://circleci.com/gh/hypnosapos/cartpole-rl-remote/tree/master.svg?style=svg
   :target: https://circleci.com/gh/hypnosapos/cartpole-rl-remote/tree/master
   :alt: Build Status
.. image:: https://img.shields.io/pypi/v/cartpole-rl-remote.svg?style=flat-square
   :target: https://pypi.org/project/cartpole-rl-remote
   :alt: Version
.. image:: https://img.shields.io/pypi/pyversions/cartpole-rl-remote.svg?style=flat-square
   :target: https://pypi.org/project/cartpole-rl-remote
   :alt: Python versions
.. image:: https://codecov.io/gh/hypnosapos/cartpole-rl-remote/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/hypnosapos/cartpole-rl-remote
   :alt: Coverage

This project is intended to play with `CartPole <https://gym.openai.com/envs/CartPole-v0/>`_ game using Reinforcement Learning.

The project is divided basically in three parts: Neural network model, QLearning algorithm and application runner.

We want to show you a journey from custom model trainer to a productive platform based on open source (training/inference).

Requirements
============

Basic scenario (Station #1):

- Make (gcc)
- Docker (17+)
- Docker compose (version 17.06.+, compose file format 3.3)

Advanced scenarios (Station #2 and #3):

- kubernetes (1.8+)

Station #1: Custom trainer and metrics collection
=================================================

As with any other software development, machine learning code must follow the same best practices.
It's very important to have on mind that our code should be run on any environment, on my laptop or on any cloud.

In the first attempt to train a CartPole model we have implemented a multiprocessor python module,
by default it tries to use one processor for each hyperparameter combination.

.. image:: assets/basic_scenario.png
   :alt: Basic Scenario

As result of the training we'll get out an **h5** file with the trained model and all metrics about the training process.

Collecting metrics with visdom
------------------------------

We trust in logs, so all details of model training should be outlined using builtins log libraries, and then the instrumentation
may come from tools that manage these log lines. We've used as first approach a log handler for Visdom server in order to send metrics to an external site.

Using python virtual env
^^^^^^^^^^^^^^^^^^^^^^^^

Requirements:

- Python (3.5+)

To create a local virtual env for python type::

   make venv

When this virtual env is activated, we can use the ``cartpole`` command client directly, type::

   cartpole --help

for more information about how to use it.

We have a couple of arguments to provide visdom configuration to send metrics: ``--metrics-engine`` and ``--metrics-config``.

The simplest way to train the model and collect metrics with visdom is next command::

   make train-dev


Change default values for hyperparameters in Makefile file if you wish another combination. Note that render mode is activated by default
so many windows, one per experiment, will show the CartPole game in action while is training.

Visdom server must be ready at: http://localhost:8097

Using docker compose
^^^^^^^^^^^^^^^^^^^^

If you prefer use docker containers for everything launch this command::

   make train-docker-visdom



Using docker log drivers, EFK in action
---------------------------------------

Ok, it's possible to implement our metrics collector, but as we are using containers, couldn't we use docker log drivers to extract metrics from log lines?
Yes, of course.

We've created a fluentd conf file to specify the regex pattern of searched lines in logs, and fluentd will send metrics to elasticsearch.

To run this stack type::

   make train-docker-efk


Kibana URL would be: http://localhost:5601. Set the text ``cartpole-*`` for the index pattern, in **efk/kibana** directory you can find
a kibana dashboard json file that you can import to view all graphics about cartpole model experiments.


Anybody could launch a docker compose with visdom and the EFK all-in-one by this command::

   make train-docker-visdom-efk


Station #2: Advanced training with Polyaxon
===========================================

Well, we have a simple model trainer with simple hyperparameter tuning implementation (something like a well known grid algorithm).
But we have too few hands on the code, and few weeks ago i discovered `polyaxon <http://polyaxon.com>`_.
It uses kubernetes as platform where all resources will be deployed.

The challenge now is try to create a polyaxon wrapper to take the CartPole model and train multiple experiments with several hyperparameter combinations.

Under the directory **polyaxon** you can find all resources related to it.

Follow this command sequence to get a kubernetes cluster with all polyaxon components (we'll use GKE service)::

   export GCP_CREDENTIALS=/tmp/gcp.json
   export GCP_ZONE=europe-west1-b
   export GCP_PROJECT_ID=my_project
   export GKE_CLUSTER_NAME=cartpole
   export GITHUB_TOKEN=githubtoken
   make gke-bastion gke-create-cluster gke-tiller-helm
   make -C polyaxon venv
   make -C polyaxon gke-polyaxon-nfs
   make -C polyaxon gke-polyaxon-nfs-grafana
   make -C polyaxon gke-polyaxon-preinstall gke-polyaxon-install

Let's deploy our experiments groups by this command::

   make gke-polyaxon-cartpole

Station #3: Model inference with Seldon
=======================================

The idea is to get trained models and deploy them within `Seldon <https://seldon.io>`_.
Install this python module to train or run the RL model under the wood.

Deploy Seldon
-------------

Deploy Seldon::

   export GKE_CLUSTER_NAME=seldon
   make gke-bastion gke-create-cluster gke-ui-login-skip gke-proxy
   make gke-tiller-helm gke-seldon-install


Deploy CartPole within Seldon
-----------------------------

Deploy seldon graphs with the cartpole model with different implements (choose one value of: [model, abtest, router] for SELDON_MODEL_TYPE variable)::

   SELDON_MODEL_TYPE=model make gke-seldon-cartpole

Run remote agent
----------------

You have to get external IP from svc/seldon-apiserver to set RUN_MODEL_IP variable.

In order to get model predictions launch this command in your shell::

  export RUN_MODEL_IP=35.205.148.146
  make run-dev


Model metrics in running mode will be collected on a `local visdom server <http://localhost:8059>`_.

//TODO imagen visdom switch route

Take a look at the grafana dashboard to view seldon metrics. Since *seldon-core-analytics* was installed with loadbalancer find out the public ip to get access.

//TODO imagen grafana

License
=======

This project is under MIT License

.. image:: https://app.fossa.io/api/projects/git%2Bgithub.com%2Fhypnosapos%2Fcartpole-rl-remote.svg?type=large
   :target: https://app.fossa.io/projects/git%2Bgithub.com%2Fhypnosapos%2Fcartpole-rl-remote?ref=badge_large
   :alt: License Check

Authors
=======

- David Suarez   - `davsuacar <http://github.com/davsuacar>`_
- Enrique Garcia - `engapa <http://github.com/engapa>`_
- Leticia Garcia - `laetitiae <http://github.com/laetitiae>`_
