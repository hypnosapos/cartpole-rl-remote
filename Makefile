.PHONY: help clean test train train-dev seldon-buil seldon-push seldon-deploy
.DEFAULT_GOAL := help

# Shell to use with Make
SHELL := /bin/bash

DOCKER_ORG        ?= hypnosapos
SELDON_IMAGE      ?= seldonio/core-python-wrapper
STORAGE_PROVIDER  ?= local
MODEL_FILE        ?= Cartpole-rl-remote.h5
PY_DEV_ENV        ?= .tox/py35/bin/activate
EPOCHS_TRAIN      ?= 2000
VERSION           ?= latest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build files
	@rm -rf build dist .eggs *.egg-info *.egg.cache docs/build

clean-pyc: ## remove Python build files
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage generated resources
	@rm -rf .tox .coverage htmlcov coverage-reports

clean-seldon: ## remove seldon resources
	@rm -rf seldon/build

test: ## run tests
	@tox

build: ## build artifacts
	@tox -e build

install: ## install
	pip install .

train: install ## train a model
	mkdir -p seldon/models
	cartpole -v train -e $(EPOCHS_TRAIN) -f seldon/models/$(MODEL_FILE)

train-dev: ## train a model in dev mode (requires a .tox/py36 venv)
	mkdir -p seldon/models
	source $(PY_DEV_ENV) &&\
	cartpole -v train -e $(EPOCHS_TRAIN) -f seldon/models/$(MODEL_FILE)

publish-gcs:
	gsutils rsync seldon/build/models gs://cartpole

release: ## upload release to pypi
	@tox -e release

codecov: ## update coverage to codecov
	@tox -e codecov

doc: ## create documentation
	@tox -e doc

seldon-build: clean-seldon ## Generate seldon resources
	cp -a requirements.txt seldon/
	mkdir -p seldon/models
ifeq ($(STORAGE_PROVIDER), gcs)
	curl https://storage.googleapis.com/cartpole/$(MODEL_FILE) seldon/models/$(MODEL_FILE)
endif
	cd $(shell pwd)/seldon && docker run -v $(shell pwd)/seldon:/model $(SELDON_IMAGE) /model CartpoleRLRemoteAgent $(VERSION) $(DOCKER_ORG) --force
	cd $(shell pwd)/seldon/build && ./build_image.sh

seldon-push:  ## Push docker image for seldon deployment
	cd $(shell pwd)/seldon/build && ./push_image.sh

seldon-deploy: ## Deploy seldon resources on kubernetes
	kubectl apply -f seldon/cartpole_seldon.json
