.DEFAULT_GOAL := help

# Shell to use with Make
SHELL := /bin/bash

DOCKER_ORG        ?= hypnosapos
DOCKER_IMAGE      ?= cartpole-rl-remote
DOCKER_TAG        ?= $(shell git rev-parse --short HEAD)
DOCKER_TAGS       ?= $(DOCKER_TAG) latest
DOCKER_USERNAME   ?= engapa
DOCKER_PASSWORD   ?= secretito
SELDON_IMAGE      ?= seldonio/core-python-wrapper
STORAGE_PROVIDER  ?= local
MODEL_FILE        ?= cartpole-rl-remote
PY_DEV_ENV        ?= .tox/py36/bin/activate
TRAIN_EPISODES    ?= 500
RUN_EPISODES      ?= 10
PY_ENVS           ?= 3.5 3.6
DEFAULT_PY_ENV    ?= 3.5


define search_container
	$(shell docker ps -a | grep cartpole-$(1)-test | grep wc -l)
endef

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: clean-build clean-py clean-test clean-docker clean-seldon clean-seldon-models## remove all build, test, coverage and Python artifacts

.PHONY: clean-build
clean-build: ## Remove build files
	@rm -rf build dist .eggs *.egg-info *.egg.cache docs/build

.PHONY: clean-py
clean-py: ## Remove Python build files
	@rm -rf .venv
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test: ## Remove test and coverage generated resources
	@rm -rf .coverage htmlcov coverage-reports

.PHONY: clean-seldon-models
clean-seldon-models:
	@rm -rf seldon/models
	@mkdir -p seldon/models

.PHONY: clean-seldon
clean-seldon: clean-seldon-models ## Remove seldon resources
	@rm -rf seldon/build

.PHONY: clean-docker
clean-docker: ## Remove docker containers and their images
	@$(foreach tag,\
	  $(DOCKER_TAGS),\
	  @docker rm -f $$(docker ps -a -f "ancestor=$(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag)" --format '{{.Names}}') > /dev/null 2>&1 || echo "No docker containers for ancestor $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag)";\
	  @docker rmi -f $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag) > /dev/null 2>&1 || echo "Not found image $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag)";)
	@$(foreach py_env,\
	  $(PY_ENVS),\
	  @docker rm -f $$(docker ps -a -f "ancestor=$(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env)" --format '{{.Names}}') > /dev/null 2>&1 || echo "No docker containers for ancestor $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env)";\
	  @docker rmi -f $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env) > /dev/null 2>&1 || echo "Not found image $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env)";)

.PHONY: docker-test-build
docker-test-build:
	@for i in $(PY_ENVS); do\
	  docker build --build-arg PY_VERSION=$${i} -t $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$${i} -f Dockerfile.test .;\
	done

.PHONY: venv
venv: ## Create a local virtualenv with default python version (supported 3.5 and 3.6)
	@python -m venv .venv
	@. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt -r requirements-dev.txt
	@echo -e "\033[32m[[ Type '. .venv/bin/activate' to activate virtualenv ]]\033[0m"

.PHONY: test
test: docker-test-build
	@$(foreach py_env,$(PY_ENVS),docker run -t $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env) ./entry.sh test;)

.PHONY: docker-build
docker-build: ## Build docker images
	@$(foreach tag,\
	    $(DOCKER_TAGS),\
	    docker build -t $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag) .;)

.PHONY: docker-push
docker-push: ## Push docker images
	@ $(foreach tag,\
	    $(DOCKER_TAGS),\
	    docker push $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag);)

.PHONY: visdom
docker-visdom: ## Run a visdom server
	@docker run -d --name local-visdom -p 8097:8097 hypnosapos/visdom:latest

train: clean-seldon-models## Train model
	@cartpole -e $(EPISODES) \
	  train --gamma 0.095 0.099 0.001 -f seldon/models/$(MODEL_FILE)

train-dev: docker-visdom clean-seldon-models ## Train a model in dev mode with render option and visdom reports (requires a .tox/py35 venv)
	@. .venv/bin/activate && \
	 pip install -e . && \
	 cartpole -e $(TRAIN_EPISODES) -r --log-level DEBUG \
	   --metrics-engine visdom --metrics-config '{"server": "http://localhost", "env": "main"}' \
	   train --gamma 0.095 0.099 0.001 -f seldon/models/$(MODEL_FILE)
	@docker rm -f local-visdom

train-docker: clean-seldon-models ## train by docker container
	@docker run -it -v $(shell pwd)/seldon/models:/tmp/seldon/models $(DOCKER_ORG)/$(DOCKER_IMAGE):$(shell git rev-parse --short HEAD)\
	 cartpole -e $(TRAIN_EPISODES) --log-level DEBUG \
	   train --gamma 0.094 0.099 0.001 -f /tmp/seldon/models/$(MODEL_FILE)

train-docker-visdom: clean-seldon-models ## train by docker compose using visdom server for monitoring
	@docker-compose -f docker-compose-visdom.yaml up --exit-code-from train-cartpole
	@docker-compose -f docker-compose-visdom.yaml down

train-docker-visdom: clean-seldon-models ## train by docker compose using EFK for monitoring
	@docker-compose -f docker-compose-efk.yaml up
	@docker-compose -f docker-compose-efk.yaml down

seldon-build: clean-seldon clean-seldon-models ## Generate seldon resources
	@ cp -a requirements.txt seldon/
ifeq ($(STORAGE_PROVIDER), gcs)
	@curl https://storage.googleapis.com/cartpole/$(MODEL_FILE) seldon/models/$(MODEL_FILE)
endif
	@cd $(shell pwd)/seldon &&\
	@docker run -v $(shell pwd)/seldon:/model $(SELDON_IMAGE) /model CartpoleRLRemoteAgent $(shell git rev-parse --short HEAD) $(DOCKER_ORG) --force
	@cd $(shell pwd)/seldon/build && ./build_image.sh

seldon-push:  ## Push docker image for seldon deployment
	@cd $(shell pwd)/seldon/build && ./push_image.sh

seldon-deploy: ## Deploy seldon resources on kubernetes
	@kubectl apply -f test/cartpole_model.yaml -n seldon


