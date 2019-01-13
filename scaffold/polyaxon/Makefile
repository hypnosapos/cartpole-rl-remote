.DEFAULT_GOAL := help

# Shell to use with Make
SHELL ?= /bin/bash

GCP_ZONE            ?= my_zone
GCP_PROJECT_ID      ?= my_project

PLX_VERSION         ?= 0.3.7

ZFS_VM              ?= polyaxon-nfs-vm

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
	@echo "VM name must be: $(ZFS_VM)"
	@docker exec gke-bastion \
	   sh -c "gcloud config set project $(GCP_PROJECT_ID) \
	           && gcloud --project $(GCP_PROJECT_ID) compute ssh --zone=$(GCP_ZONE) $(ZFS_VM) \
	         --command 'for dir_name in data outputs logs repos upload;do mkdir -m 777 /data/$$dir_name;done'"

.PHONY: gke-polyaxon-nfs-grafana
gke-polyaxon-nfs-grafana: ## Create a machine to serve NFS storage
	@docker exec gke-bastion \
	   sh -c "gcloud --project $(GCP_PROJECT_ID) compute ssh --ssh-flag=-L3000:localhost:3000 --zone=$(GCP_ZONE) $(ZFS_VM)"


.PHONY: gke-polyaxon-preinstall
gke-polyaxon-preinstall: ## Get a docker image list of all nodes
	@docker cp ../k8s/polyaxon gke-bastion:/polyaxon-k8s
	@docker exec gke-bastion \
	   sh -c 'kubectl create namespace polyaxon \
	          && export IP="$$(gcloud compute instances describe $(ZFS_VM) \
	            --zone=$(GCP_ZONE) --project $(GCP_PROJECT_ID) --format="'"value(networkInterfaces[0].networkIP)"'")" \
	          && find /polyaxon-k8s -name "'"*-pvc.yml"'" \
	              -exec sed -i s/NFS_HOST/$$IP/g {} \;\
	          && for file in data logs outputs repos upload; \
	          do kubectl apply -f //polyaxon-k8s/$$file-pvc.yml; done'

.PHONY: gke-polyaxon-install
gke-polyaxon-install: ## Install polyaxon
	@docker exec gke-bastion \
	   sh -c "helm repo add polyaxon https://charts.polyaxon.com \
	          && helm repo update \
	          && helm install polyaxon/polyaxon \
	           --name=polyaxon \
	           --namespace=polyaxon \
	           --version $(PLX_VERSION) \
	           -f /polyaxon-k8s/polyaxon-config.yml"

.PHONY: gke-polyaxon-uninstall
gke-polyaxon-uninstall: ## Uninstall polyaxon
	@docker exec gke-bastion \
	   sh -c 'helm del --purge polyaxon \
	         && for file in data logs outputs repos upload; \
	         do kubectl delete -f /polyaxon-k8s/$$file-pvc.yml; done \
	         && kubectl delete ns polyaxon'

.PHONY: gke-polyaxon-cartpole-init ## Initialize cartpole experiment group
gke-polyaxon-cartpole-init:
	@docker exec gke-bastion \
	   sh -c 'apk --upgrade add py-pip python-dev build-base linux-headers musl-dev && pip install -U pip && pip install -U polyaxon-cli \
	          && export POLYAXON_IP="$$(kubectl get svc --namespace polyaxon polyaxon-polyaxon-api -o jsonpath="'"{.status.loadBalancer.ingress[0].ip}"'")" \
	          && export POLYAXON_HTTP_PORT=80 \
	          && export POLYAXON_WS_PORT=1337 \
	          && echo http://$$POLYAXON_IP:$$POLYAXON_HTTP_PORT \
	          && mkdir -p /polyaxon && cd /polyaxon \
	          && polyaxon config set --host=$$POLYAXON_IP --http_port=$$POLYAXON_HTTP_PORT  --ws_port=$$POLYAXON_WS_PORT \
	          && polyaxon login --username root --password $$(kubectl get secret --namespace polyaxon polyaxon-polyaxon-secret -o jsonpath="'"{.data.POLYAXON_ADMIN_PASSWORD}"'" | base64 -d) \
	          && polyaxon project create --name cartpole --description "Cartpole RL Remote Agent" --init'

.PHONY: gke-polyaxon-cartpole ## Upload and run cartpole experiment group
gke-polyaxon-cartpole:
	@docker cp polyaxonfile_grp.yml gke-bastion:/polyaxon/
	@docker cp model.py gke-bastion:/polyaxon/
	@docker exec gke-bastion sh -c "cd /polyaxon && polyaxon run -f polyaxonfile_grp.yml -u --name 'cartpole' --description 'CartPole game by RL'"

.PHONY: gke-polyaxon-notebook ## Launch jupyter
gke-polyaxon-notebook:
	@docker cp polyaxonfile_notebook.yml gke-bastion:/polyaxon/
	@docker exec gke-bastion sh -c "cd /polyaxon && polyaxon notebook start -f polyaxonfile_notebook.yml"

.PHONY: gke-polyaxon-tensorboard ## Launch tensorboard
gke-polyaxon-tensorboard:
	@docker cp polyaxonfile_tensorboard.yml gke-bastion:/polyaxon/
	@docker exec gke-bastion sh -c "cd /polyaxon && polyaxon tensorboard start -f polyaxonfile_tensorboard.yml"