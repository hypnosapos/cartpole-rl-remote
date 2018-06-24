.DEFAULT_GOAL := help

# Shell to use with Make
SHELL := /bin/bash

GCP_ZONE            ?= my_zone
GCP_PROJECT_ID      ?= my_project

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv: ## Create a local virtualenv with polyaxon packages installed
	@python -m venv .venv
	@. .venv/bin/activate && pip install -U pip && pip install polyaxon-cli
	@echo -e "\033[32m[[ Type '. .venv/bin/activate' to activate virtualenv ]]\033[0m"

.PHONY: gke-polyaxon-nfs
gke-polyaxon-nfs: ## Create a NFS server by ZFS single Node
	@echo "Visit https://console.cloud.google.com/launcher/details/click-to-deploy-images/singlefs?q=zfs"

.PHONY: gke-polyaxon-nfs-grafana
gke-polyaxon-nfs-grafana: ## Create a machine to serve NFS storage
	@docker exec gke-bastion \
	   sh -c "gcloud --project $(GCP_PROJECT_ID) compute ssh --ssh-flag=-L3000:localhost:3000 --zone=$(GCP_ZONE) polyaxon-nfs-vm"
	@docker exec gke-bastion \
	   sh -c ""

.PHONY: gke-polyaxon-preinstall
gke-polyaxon-preinstall: ## Get a docker image list of all nodes
	@docker cp scaffold gke-bastion:/tmp/
	@docker exec gke-bastion \
	   sh -c "IP=$$(gcloud compute instances describe polyaxon-nfs-vm \
	          --zone=$(GCP_ZONE) \
	          --format='value(networkInterfaces[0].networkIP)') \
	          && sed -e s/NFS_HOST/$${IP}/g /tmp/scaffold/*-pvc.yml"
	@docker exec gke-bastion \
	   sh -c 'kubectl create namespace polyaxon \
	          && for file in data logs outputs repos upload; \
	          do kubectl apply -f /tmp/scaffold/$$file-pvc.yml; done'

.PHONY: gke-polyaxon-install
gke-polyaxon-install: ## Install polyaxon
	@docker exec gke-bastion \
	   sh -c "helm repo add polyaxon https://charts.polyaxon.com \
	          && helm repo update \
	          && helm install polyaxon/polyaxon \
	           --name=polyaxon \
	           --namespace=polyaxon \
	           -f /tmp/scaffold/polyaxon-config.yml"

.PHONY: polyaxon-cartpole
polyaxon-cartpole:
	@. .venv/bin/activate && \
	 polyaxon create project --name "cartpole" --description "Cartpole RL Remote Agent" && \
	 polyaxon init cartpole && \
	 polyaxon run -u
