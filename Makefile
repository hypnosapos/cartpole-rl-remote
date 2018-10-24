.DEFAULT_GOAL := help

# Shell to use with Make
SHELL ?= /bin/bash
ROOT_PATH := $(PWD)/$({0%/*})

DOCKER_ORG        ?= hypnosapos
DOCKER_IMAGE      ?= cartpole-rl-remote
DOCKER_TAG        ?= $(shell git rev-parse --short HEAD)
DOCKER_TAGS       ?= $(DOCKER_TAG) latest
DOCKER_USERNAME   ?= engapa
DOCKER_PASSWORD   ?= secretito

SELDON_IMAGE      ?= seldonio/core-python-wrapper
SELDON_MODEL_TYPE ?= model
SELDON_VERSION    ?= 0.2.3
STORAGE_PROVIDER  ?= local

MODEL_FILE        ?= cartpole-rl-remote
TRAIN_EPISODES    ?= 500
RUN_EPISODES      ?= 200
RUN_MODEL_IP      ?= localhost

PY_ENVS           ?= 3.5 3.6
DEFAULT_PY_ENV    ?= 3.5


UNAME := $(shell uname -s)
ifeq ($(UNAME),Linux)
OPEN := xdg-open
else
OPEN := open
endif

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: clean
clean: clean-build clean-py clean-test clean-docker clean-seldon clean-seldon-models ## remove all build, test, coverage and Python artifacts

.PHONY: clean-build
clean-build: ## Remove build files
	@cd $(ROOT_PATH) && rm -rf build dist .eggs .models *.egg-info *.egg.cache docs/build

.PHONY: clean-py
clean-py: ## Remove Python build files
	@rm -rf $(ROOT_PATH)/.venv
	@find $(ROOT_PATH) -name '*.pyc' -exec rm -f {} +
	@find $(ROOT_PATH) -name '*.pyo' -exec rm -f {} +
	@find $(ROOT_PATH) -name '*~' -exec rm -f {} +
	@find $(ROOT_PATH) -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-test
clean-test: ## Remove test and coverage generated resources
	@cd $(ROOT_PATH) && rm -rf .coverage htmlcov coverage-reports

.PHONY: clean-seldon-models
clean-seldon-models:
	@rm -rf $(ROOT_PATH)scaffold/seldon/models
	@mkdir -p $(ROOT_PATH).models

.PHONY: clean-seldon
clean-seldon: clean-seldon-models ## Remove seldon resources
	@rm -rf $(ROOT_PATH)/seldon/build

.PHONY: clean-docker
clean-docker: ## Remove docker containers and their images
	@$(foreach tag,\
	  $(DOCKER_TAGS),\
	  docker rm -f $$(docker ps -a -f "ancestor=$(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag)" --format '{{.Names}}') > /dev/null 2>&1 || true;\
	  docker rmi -f $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag) > /dev/null 2>&1 ] || true;)
	@$(foreach py_env,\
	  $(PY_ENVS),\
	  docker rm -f $$(docker ps -a -f "ancestor=$(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env)" --format '{{.Names}}') > /dev/null 2>&1 || true;\
	  docker rmi -f $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env) > /dev/null 2>&1 || true;)

.PHONY: docker-test-build
docker-test-build:
	@for i in $(PY_ENVS); do\
	  docker build --build-arg PY_VERSION=$${i} -t $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$${i} -f Dockerfile.test $(ROOT_PATH);\
	done

.PHONY: venv
venv: ## Create a local virtualenv with default python version (supported 3.5 and 3.6)
	@python -m venv .venv
	@. $(ROOT_PATH)/.venv/bin/activate && pip install -U pip && pip install $(ROOT_PATH)
	@echo -e "\033[32m[[ Type '. $(ROOT_PATH).venv/bin/activate' to activate virtualenv ]]\033[0m"

.PHONY: test
test: docker-test-build
	@$(foreach py_env,$(PY_ENVS),docker run -t $(DOCKER_ORG)/$(DOCKER_IMAGE)-test:py$(py_env) ./entry.sh test;)

.PHONY: docker-build
docker-build: ## Build docker images
	@$(foreach tag,\
	    $(DOCKER_TAGS),\
	    docker build -t $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag) $(ROOT_PATH);)

.PHONY: docker-push
docker-push: ## Push docker images
	@ $(foreach tag,\
	    $(DOCKER_TAGS),\
	    docker push $(DOCKER_ORG)/$(DOCKER_IMAGE):$(tag);)

.PHONY: docker-visdom
docker-visdom: ## Run a visdom server
	@docker rm -f $$(docker ps -a -f "name=local-visdom" --format "{{.Names}}") $^ 2>/dev/null ; true
	@docker run -d --name local-visdom -p 8097:8097 hypnosapos/visdom:latest
	@until curl --output /dev/null -f --silent http://localhost:8097; do \
	   echo "Trying connect to visdom server at http://localhost:8097 ..."; \
	   sleep 5; \
	 done

.PHONY: train
train: clean-seldon-models## Train model
	@cartpole -e $(EPISODES) \
	  train --gamma 0.095 0.099 0.001 -f $(ROOT_PATH).models/$(MODEL_FILE)

.PHONY: train-dev
train-dev: docker-visdom clean-seldon-models ## Train a model in dev mode with render option and visdom reports (requires venv)
	@. $(ROOT_PATH).venv/bin/activate && \
	 cartpole -e $(TRAIN_EPISODES) -r --log-level DEBUG \
	   --metrics-engine visdom --metrics-config '{"server": "http://127.0.0.1", "env": "main"}' \
	   train --gamma 0.095 0.099 0.001 -f $(ROOT_PATH).models/$(MODEL_FILE)

.PHONY: train-docker
train-docker: clean-seldon-models ## Train by docker container
	@docker run -it -v $(ROOT_PATH).models:/tmp/models $(DOCKER_ORG)/$(DOCKER_IMAGE):$(DOCKER_TAG)\
	 cartpole -e $(TRAIN_EPISODES) --log-level DEBUG \
	   train --gamma 0.095 0.099 0.001 -f /tmp/models/$(MODEL_FILE)

.PHONY: train-docker-modeldb
train-docker-modeldb: clean-seldon-models ## Train by docker compose using modeldb server for metrics
	## @docker-compose -f docker-compose-modeldb.yaml up --exit-code-from cartpole
	@docker-compose -f scaffold/docker-compose-modeldb.yaml up
	@docker-compose -f scaffold/docker-compose-modeldb.yaml down

.PHONY: train-docker-visdom
train-docker-visdom: clean-seldon-models ## Train by docker compose using visdom server for metrics
	@docker rm -f $$(docker ps -a -f "name=local-visdom" --format "{{.Names}}") $^ 2>/dev/null ; true
	## @docker-compose -f docker-compose-visdom.yaml up --exit-code-from cartpole
	@docker-compose -f scaffold/docker-compose-visdom.yaml up
	@docker-compose -f scaffold/docker-compose-visdom.yaml down

.PHONY: train-docker-efk
train-docker-efk: clean-seldon-models ## Train by docker compose using EFK for metrics and monitoring
	@docker-compose -f $(ROOT_PATH)/scaffold/docker-compose-efk.yaml up
	@docker-compose -f $(ROOT_PATH)/scaffold/docker-compose-efk.yaml down

.PHONY: seldon-build
seldon-build: clean-seldon ## Generate seldon resources
	@cp -a $(ROOT_PATH)requirements.txt $(ROOT_PATH)scaffold/seldon/
	@mkdir -p $(ROOT_PATH)scaffold/seldon/models
ifeq ($(STORAGE_PROVIDER), gcs)
	@curl https://storage.googleapis.com/cartpole/$(MODEL_FILE) $(ROOT_PATH)scaffold/seldon/models/$(MODEL_FILE)
else
	@mv $(ROOT_PATH).models/$(MODEL_FILE).h5 $(ROOT_PATH)scaffold/seldon/models/
endif
	@cd $(ROOT_PATH)scaffold/seldon && \
	 docker run -v $(ROOT_PATH)scaffold/seldon:/model $(SELDON_IMAGE) /model CartpoleRLRemoteAgent $(DOCKER_TAG) $(DOCKER_ORG) --force
	@cd $(ROOT_PATH)scaffold/seldon/build && ./build_image.sh

.PHONY: seldon-push
seldon-push:  ## Push docker image for seldon deployment
	@cd $(ROOT_PATH)scaffold/seldon/build && ./push_image.sh

.PHONY: run-dev
run-dev: docker-visdom ## Run a remote agent in dev mode with render option and visdom reports (requires venv)
	@. .venv/bin/activate && \
	 cartpole -e $(RUN_EPISODES) --log-level DEBUG \
	   --metrics-engine visdom --metrics-config '{"server": "http://127.0.0.1", "env": "main"}' \
	   run --host "$(RUN_MODEL_IP)" --runners 5

.PHONY: run-dev-router-agent
run-dev-router-agent: ## Run a router agent to change the default behaviour
	@. .venv/bin/activate && \
	 python $(ROOT_PATH)/test/e2e/test_router.py --visdom-config '{"server": "http://127.0.0.1", "env": "main"}' \
	 -pref-branch 1 -router-name eg-router -api-server $(RUN_MODEL_IP) --num-reqs 20000

.PHONY: gke-seldon-install
gke-seldon-install: ## Installing Seldon components
	@docker exec gke-bastion \
	  sh -c "helm repo add seldon https://storage.googleapis.com/seldon-charts \
	         && helm repo update \
	         && helm install seldon/seldon-core-crd --name seldon-core-crd --version $(SELDON_VERSION) \
	         && kubectl create namespace seldon \
	         && helm install seldon/seldon-core --name seldon-core \
	            --set apife_service_type=LoadBalancer \
	            --version $(SELDON_VERSION) --namespace seldon \
	         && helm install seldon/seldon-core-analytics --name seldon-core-analytics \
                --set grafana_prom_admin_password=password \
                --set persistence.enabled=false \
                --set grafana_prom_service_type=LoadBalancer \
                --version $(SELDON_VERSION) --namespace seldon"

.PHONY: gke-seldon-cartpole
gke-seldon-cartpole: ## Deploy cartpole model according to different seldon implementations (SELDON_MODEL_TYPE = [model|abtest|router])
	@docker cp scaffold/k8s/seldon/cartpole_$(SELDON_MODEL_TYPE).yaml gke-bastion:/seldon/cartpole_$(SELDON_MODEL_TYPE).yaml
	@docker exec gke-bastion \
	  sh -c "kubectl create -f /seldon/cartpole_$(SELDON_MODEL_TYPE).yaml -n seldon"

.PHONY: gke-seldon-cartpole-delete
gke-seldon-cartpole-delete: ## Delete cartpole model according to different seldon implementations (model, abtest, router)
	@docker exec gke-bastion \
	  sh -c "kubectl delete -f /seldon/cartpole_$(SELDON_MODEL_TYPE).yaml -n seldon"

.PHONY: gke-seldon-uninstall
gke-seldon-uninstall: ## Uninstalling Seldon components
	@docker exec gke-bastion \
	  sh -c "helm del --purge seldon-core \
	         && helm del --purge seldon-core-analytics \
	         && helm del --purge seldon-core-crd"
