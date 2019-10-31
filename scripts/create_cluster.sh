#!/bin/bash

# request some information
read -p "Please enter the SQL username [root]: " DB_USER
read -p "Please enter the SQL password: " DB_PASSWORD
DB_INSTANCE=$(gcloud sql instances describe clic | grep connectionName | cut -d ' ' -f 2)
DB_USER=${DB_USER:-root}
DB_NAME="clic2020"

if [ ! -f service-account.json ]; then
	# create service account key file
	read -p "Please enter a service account [clic2019@clic-215616.iam.gserviceaccount.com]: " SERVICE_ACCOUNT
	SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-clic2019@clic-215616.iam.gserviceaccount.com}
	gcloud iam service-accounts keys create --iam-account "${SERVICE_ACCOUNT}" service-account.json
fi

read -p "Please enter a secret key for Django (optional): " SECRET_KEY
read -p "Please enter the Sentry DSN (optional): " SENTRY_DSN

# create cluster and CPU nodes
gcloud container clusters create clic-cluster \
	--zone us-west1-b \
	--machine-type n1-standard-1 \
	--num-nodes 2 \
	--verbosity error

# add GPU nodes
gcloud container node-pools create gpu-pool \
	--zone us-west1-b \
	--accelerator type=nvidia-tesla-k80,count=1 \
	--machine-type n1-standard-2 \
	--cluster clic-cluster \
	--num-nodes 1 \
	--verbosity error

# install nvidia drivers on GPU nodes
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/daemonset.yaml

# add service account information to kubernetes
kubectl create secret generic clic-sa-key --from-file service-account.json

# add SQL account information to kubernetes
kubectl create secret generic cloudsql \
	--from-literal DB_USER="$DB_USER" \
	--from-literal DB_PASSWORD="$DB_PASSWORD" \
	--from-literal DB_INSTANCE="$DB_INSTANCE" \
	--from-literal DB_NAME="$DB_NAME"

# add bucket names
kubectl create secret generic buckets \
	--from-literal BUCKET_SUBMISSIONS="clic2020_submissions" \
	--from-literal BUCKET_TARGETS="clic2020_targets" \
	--from-literal BUCKET_ENVIRONMENTS="clic2020_environments"

# add other secret information used by webserver
kubectl create secret generic django --from-literal secret_key="$SECRET_KEY"
kubectl create secret generic sentry --from-literal dsn="$SENTRY_DSN"

# add evaluation code to kubernetes
kubectl create configmap code --from-file code/
