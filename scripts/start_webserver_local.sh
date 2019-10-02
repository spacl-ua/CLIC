#!/bin/sh

if [ ! -f service-account.json ]; then
	# create service account key file
	read -p "Please enter a service account [clic2019@clic-215616.iam.gserviceaccount.com]: " SERVICE_ACCOUNT
	SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-clic2019@clic-215616.iam.gserviceaccount.com}
	gcloud iam service-accounts keys create --iam-account "${SERVICE_ACCOUNT}" service-account.json
fi

read -p "Please enter the SQL password: " DB_PASSWORD

DB_INSTANCE=$(gcloud sql instances describe clic --format 'value(connectionName)')
DB_HOST=$(gcloud sql instances describe clic --format 'value(ipAddresses.ipAddress)')

docker run \
	--rm \
	-ti \
	-v "$(pwd)/service-account.json":"/secret/service-account.json" \
	-e GOOGLE_APPLICATION_CREDENTIALS="/secret/service-account.json" \
	-e DB_INSTANCE="${DB_INSTANCE}" \
	-e DB_NAME=clic2020 \
	-e DB_USER=root \
	-e DB_PASSWORD="${DB_PASSWORD}" \
	-e DB_HOST="${DB_HOST}" \
	-e SUBMISSIONS_BUCKET="clic2020_submissions" \
	-w "$(pwd)/docker/web" \
	-v "$(pwd)/docker/web":"$(pwd)/docker/web" \
	-p 8000:8000 \
	gcr.io/clic-215616/web \
	/bin/bash
#	python3 manage.py runserver 0.0.0.0:8000
