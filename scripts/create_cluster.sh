#!/bin/bash

# create cluster
gcloud container clusters create clic-cluster \
	--zone us-west1-b \
	--num-nodes 2

# add service account information to kubernetes
if [ ! -f service-account.json ]; then
	# create service account key file
	read -p "Please enter a service account [clic2019@clic-215616.iam.gserviceaccount.com]: " SERVICE_ACCOUNT
	SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-clic2019@clic-215616.iam.gserviceaccount.com}
	gcloud iam service-accounts keys create --iam-account "${SERVICE_ACCOUNT}" service-account.json
fi
kubectl create secret generic clic-sa-key --from-file service-account.json

# add SQL account information to kubernetes
read -p "Please enter the SQL username [root]: " DB_USER
read -p "Please enter the SQL password: " DB_PASSWORD
DB_INSTANCE=$(gcloud sql instances describe clic | grep connectionName | cut -d ' ' -f 2)
DB_USER=${DB_USER:-root}
DB_NAME="clic2020"
kubectl create secret generic cloudsql \
	--from-literal user="$DB_USER" \
	--from-literal password="$DB_PASSWORD" \
	--from-literal instance="$DB_INSTANCE" \
	--from-literal name="$DB_NAME"
