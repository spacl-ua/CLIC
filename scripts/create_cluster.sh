#!/bin/bash

LABEL=clic2021

# request some information
read -p "Please enter the SQL username [root]: " DB_USER
read -p "Please enter the SQL password: " DB_PASSWORD
DB_INSTANCE=$(gcloud sql instances describe clic --format 'value(connectionName)')
DB_USER=${DB_USER:-root}
DB_NAME="${LABEL}"

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
	--machine-type n1-standard-8 \
	--enable-autoscaling \
	--min-nodes 1 \
	--max-nodes 8 \
	--num-nodes 2 \
	--verbosity error

# add GPU nodes
gcloud container node-pools create gpu-pool \
	--zone us-west1-b \
	--machine-type n1-standard-4 \
	--accelerator type=nvidia-tesla-p100,count=1 \
	--cluster clic-cluster \
	--enable-autoscaling \
	--min-nodes 0 \
	--max-nodes 8 \
	--num-nodes 0 \
	--verbosity error

# install nvidia drivers on GPU nodes
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/daemonset.yaml

# add service account information to kubernetes
kubectl create secret generic clic-sa-key --from-file service-account.json

# add SQL account information to kubernetes
kubectl create secret generic cloudsql-${LABEL} \
	--from-literal DB_USER="$DB_USER" \
	--from-literal DB_PASSWORD="$DB_PASSWORD" \
	--from-literal DB_INSTANCE="$DB_INSTANCE" \
	--from-literal DB_NAME="$DB_NAME"

# add bucket names
kubectl create secret generic buckets-${LABEL} \
	--from-literal BUCKET_SUBMISSIONS="${LABEL}_submissions" \
	--from-literal BUCKET_TARGETS="${LABEL}_targets" \
	--from-literal BUCKET_ENVIRONMENTS="${LABEL}_environments" \
	--from-literal BUCKET_PUBLIC="${LABEL}_public"

# add other secret information used by webserver
kubectl create secret generic django-${LABEL} --from-literal secret_key="$SECRET_KEY"
kubectl create secret generic sentry-${LABEL} --from-literal dsn="$SENTRY_DSN"

# add evaluation code to kubernetes
kubectl create configmap code-${LABEL} --from-file code/
