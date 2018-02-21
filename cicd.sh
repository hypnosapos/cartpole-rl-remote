#!/bin/bash -e

KUBE_VERSION=$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)
curl -LO https://storage.googleapis.com/kubernetes-release/release/${KUBE_VERSION}/bin/linux/amd64/kubectl
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

curl https://sdk.cloud.google.com -o gcloud_install.sh && bash ./gcloud_install.sh --disable-prompts
~/google-cloud-sdk/bin/gcloud -q components install beta
~/google-cloud-sdk/bin/gcloud config set disable_usage_reporting false
~/google-cloud-sdk/bin/gcloud version &&

cat << EOF > ~/.boto
[Credentials]
gs_access_key_id=$GCS_ACCESS_KEY_ID
gs_secret_access_key=$GCS_SECRET_ACCESS_KEY
EOF

gsutil cp gs://cartpole/ca.cert .

kubectl config set-cluster seldon-cluster --server=https://$KUBERNETES_CLUSTER_IP --certificate-authority=ca.cert
kubectl config set-credentials admin/seldon-cluster --username=$KUBERNETES_USER --password=$KUBERNETES_PASSWORD
kubectl config set-context seldon-cluster --namespace=default --user=admin/seldon-cluster --cluster=seldon-cluster
kubectl config use-context seldon-cluster
kubectl cluster-info
make seldon-deploy
