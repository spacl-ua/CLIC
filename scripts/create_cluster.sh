#!/bin/bash

gcloud container clusters create clic-cluster \
	--zone us-west1-b \
	--num-nodes 2

# add service account to kubernetes
gcloud iam service-accounts keys create --iam-account "clic2019@clic-215616.iam.gserviceaccount.com" service-account.json
kubectl create secret generic clic-sa-key --from-file service-account.json
rm service-account.json
