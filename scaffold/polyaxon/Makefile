.DEFAULT_GOAL := help

# Shell to use with Make
SHELL ?= /bin/bash

GCP_ZONE            ?= my_zone
GCP_PROJECT_ID      ?= my_project
PLX_VERSION         ?= 0.1.6

UNAME := $(shell uname -s)
ifeq ($(UNAME),Linux)
OPEN := xdg-open
else
OPEN := open
endif

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: venv
venv: ## Create a local virtualenv with polyaxon packages installed
	@python -m venv .pvenv
	@. .pvenv/bin/activate && pip install -U pip && pip install polyaxon-cli
	@echo -e "\033[32m[[ Type '. .pvenv/bin/activate' to activate virtualenv ]]\033[0m"

.PHONY: gke-polyaxon-nfs
gke-polyaxon-nfs: ## Create a NFS server by ZFS single Node
	@echo "Visit https://console.cloud.google.com/launcher/details/click-to-deploy-images/singlefs?q=zfs"
	@echo "VM name must be: polyaxon-nfs-vm"
	@docker exec gke-bastion \
	   sh -c "gcloud config set project $(GCP_PROJECT_ID) \
	           && gcloud --project $(GCP_PROJECT_ID) compute ssh --zone=$(GCP_ZONE) polyaxon-nfs-vm \
	         --command 'for dir_name in data outputs logs repos upload;do mkdir -m 777 /data/$$dir_name;done'"

.PHONY: gke-polyaxon-nfs-grafana
gke-polyaxon-nfs-grafana: ## Create a machine to serve NFS storage
	@docker exec gke-bastion \
	   sh -c "gcloud --project $(GCP_PROJECT_ID) compute ssh --ssh-flag=-L3000:localhost:3000 --zone=$(GCP_ZONE) polyaxon-nfs-vm"


.PHONY: gke-polyaxon-preinstall
gke-polyaxon-preinstall: ## Get a docker image list of all nodes
	@docker exec gke-bastion \
	   sh -c 'gcloud config set project $(GCP_PROJECT_ID) \
	          && kubectl create namespace polyaxon \
	          && export IP="$$(gcloud compute instances describe polyaxon-nfs-vm \
	            --zone=$(GCP_ZONE) --format="'"value(networkInterfaces[0].networkIP)"'")" \
	          && find /cartpole-rl-remote/scaffold/k8s/polyaxon -name "'"*-pvc.yml"'" \
	              -exec sed -i s/NFS_HOST/$$IP/g {} \;\
	          && for file in data logs outputs repos upload; \
	          do kubectl apply -f /cartpole-rl-remote/scaffold/k8s/polyaxon/$$file-pvc.yml; done'

.PHONY: gke-polyaxon-install
gke-polyaxon-install: ## Install polyaxon
	@docker exec gke-bastion \
	   sh -c "helm repo add polyaxon https://charts.polyaxon.com \
	          && helm repo update \
	          && helm install polyaxon/polyaxon \
	           --name=polyaxon \
	           --namespace=polyaxon \
	           --version $(PLX_VERSION) \
	           -f /cartpole-rl-remote/scaffold/k8s/polyaxon/polyaxon-config.yml"

.PHONY: gke-polyaxon-uninstall
gke-polyaxon-uninstall: ## Uninstall polyaxon
	@docker exec gke-bastion \
	   sh -c 'helm del --purge polyaxon \
	         && for file in data logs outputs repos upload; \
	         do kubectl delete -f /cartpole-rl-remote/scaffold/k8s/polyaxon/$$file-pvc.yml; done \
	         && kubectl delete ns polyaxon'

.PHONY: gke-polyaxon-cartpole-init ## Initialize cartpole experiment group
gke-polyaxon-cartpole-init:
	docker exec gke-bastion \
	   sh -c 'apk --update add py-pip python-dev build-base && pip install polyaxon-cli \
	          && export POLYAXON_IP="$$(kubectl get svc --namespace polyaxon polyaxon-polyaxon-api -o jsonpath="'"{.status.loadBalancer.ingress[0].ip}"'")" \
	          && export POLYAXON_HTTP_PORT=80 \
	          && export POLYAXON_WS_PORT=80 \
	          && echo http://$$POLYAXON_IP:$$POLYAXON_HTTP_PORT \
	          && cd /cartpole-rl-remote/scaffold/polyaxon \
	          && polyaxon config set --host=$$POLYAXON_IP --http_port=$$POLYAXON_HTTP_PORT  --ws_port=$$POLYAXON_WS_PORT \
	          && polyaxon login --username root --password $$(kubectl get secret --namespace polyaxon polyaxon-polyaxon-secret -o jsonpath="'"{.data.user-password}"'" | base64 -d) \
	          && polyaxon project create --name cartpole --description "Cartpole RL Remote Agent" \
	          && polyaxon init cartpole'

.PHONY: gke-polyaxon-cartpole ## Upload and run cartpole experiment group
gke-polyaxon-cartpole:
	@docker exec gke-bastion sh -c "cd /cartpole-rl-remote/scaffold/polyaxon && polyaxon run -u"