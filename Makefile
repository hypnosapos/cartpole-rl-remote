.PHONY: help clean test train train-dev train-docker build-docker train-docker-visdom push-docker seldon-build seldon-push seldon-deploy pre-release release
.DEFAULT_GOAL := help

# Shell to use with Make
SHELL := /bin/bash

DOCKER_ORG        ?= hypnosapos
DOCKER_IMAGE      ?= cartpole-rl-remote
DOCKER_USERNAME   ?= engapa
DOCKER_PASSWORD   ?= secretito
SELDON_IMAGE      ?= seldonio/core-python-wrapper
STORAGE_PROVIDER  ?= local
MODEL_FILE        ?= cartpole-rl-remote
PY_DEV_ENV        ?= .tox/py36/bin/activate
TRAIN_EPISODES    ?= 500
RUN_EPISODES	  ?= 10

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build files
	@rm -rf build dist .eggs *.egg-info *.egg.cache docs/build .helm

clean-pyc: ## remove Python build files
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test and coverage generated resources
	@rm -rf .tox .coverage htmlcov coverage-reports

clean-seldon: ## remove seldon resources
	@rm -rf seldon/build

clean-seldon-models: ## Remove seldon models
	@rm -rf seldon/models

test: ## run tests
	@tox

codecov: ## update coverage to codecov
	@tox -e codecov

build-py: ## build artifacts
	@tox -e build

build-docker:
	docker build -t $(DOCKER_ORG)/$(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)\
	 -t $(DOCKER_ORG)/$(DOCKER_IMAGE):latest .

install: ## install
	pip install .

visdom: ## Run a visdom server
	docker run -d -p 8097:8097 hypnosapos/visdom:latest

train: install clean-seldon-models ## train a model
	mkdir -p seldon/models
	cartpole -e $(EPISODES) train --gamma 0.095 0.099 0.001 -f seldon/models/$(MODEL_FILE)

train-dev: clean-seldon-models ## train a model in dev mode (requires a .tox/py35 venv)
	mkdir -p seldon/models
	source $(PY_DEV_ENV) &&\
	pip install -e . &&\
	cartpole -e $(TRAIN_EPISODES) -r --log-level DEBUG\
	 --metrics-engine visdom --metrics-config '{"server": "http://localhost", "env": "main"}'\
	 train --gamma 0.095 0.099 0.001 -f seldon/models/$(MODEL_FILE)

train-docker: clean-seldon-models ## train by docker container
	mkdir -p seldon/models
	docker run -it -v $(shell pwd)/seldon/models:/tmp/seldon/models $(DOCKER_ORG)/$(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)\
	  cartpole -e $(TRAIN_EPISODES) --log-level DEBUG train --gamma 0.094 0.099 0.001 -f /tmp/seldon/models/$(MODEL_FILE)

train-docker-visdom: clean-seldon-models ## train by docker compose using visdom server for monitoring
	mkdir -p seldon/models
	DOCKER_TAG=$(shell git rev-parse --short HEAD) docker-compose run cartpole-rl-remote cartpole --log-level DEBUG -e $(TRAIN_EPISODES)\
	 --metrics-engine visdom --metrics-config '{"server": "http://visdom", "env": "main"}'\
	  train --gamma 0.095 0.099 0.001 -f /tmp/seldon/models/$(MODEL_FILE)
	docker-compose down

publish-gcs: ## Upload experiments to google cloud storage
	gsutils rsync seldon/build/models gs://cartpole

push-docker: ## Publish docker image
	docker login -u=$(DOCKER_USERNAME) -p=$(DOCKER_PASSWORD)
	docker push $(DOCKER_ORG)/$(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)
	docker push $(DOCKER_ORG)/$(DOCKER_IMAGE):latest

doc: ## create documentation
	@tox -e doc

seldon-build: clean-seldon ## Generate seldon resources
	cp -a requirements.txt seldon/
	mkdir -p seldon/models
ifeq ($(STORAGE_PROVIDER), gcs)
	curl https://storage.googleapis.com/cartpole/$(MODEL_FILE) seldon/models/$(MODEL_FILE)
endif
	cd $(shell pwd)/seldon &&\
	docker run -v $(shell pwd)/seldon:/model $(SELDON_IMAGE) /model CartpoleRLRemoteAgent $(shell git rev-parse --short HEAD) $(DOCKER_ORG) --force
	cd $(shell pwd)/seldon/build && ./build_image.sh

seldon-push:  ## Push docker image for seldon deployment
	cd $(shell pwd)/seldon/build && ./push_image.sh

seldon-deploy: ## Deploy seldon resources on kubernetes
	kubectl apply -f test/cartpole_model.yaml -n seldon

pre-release: ## Pre-release tasks. Setup a version (SemV2) and generate changelog file (underlaying command generate a git tag)
	@tox -e pre-release

release: pre-release ## Release a version
	## Publish cartpole python package
	@tox -e publish
	## TODO: add the python asset to release site on github server
	## TODO: add the model (*-<version>.h5)asset to release site on github server
	## Helm chart
	@mkdir .helm && helm package helm/cartpole-rl-remote && mv cartpole-rl-remote*.tgz .helm/
    ## TODO: add the asset to release site on github server

