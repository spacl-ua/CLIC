#!/bin/sh

LABEL=clic2021

if [ ! -f service-account.json ]; then
	# create service account key file
	if ( kubectl get secret clic-sa-key 2>&1 > /dev/null ); then
		kubectl get secrets clic-sa-key -o 'go-template={{index .data "service-account.json"}}' | base64 -D - > service-account.json;
	else
		read -p "Please enter a service account [clic2019@clic-215616.iam.gserviceaccount.com]: " SERVICE_ACCOUNT
		SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-clic2019@clic-215616.iam.gserviceaccount.com}
		gcloud iam service-accounts keys create --iam-account "${SERVICE_ACCOUNT}" service-account.json
	fi
fi

DB_INSTANCE=$(gcloud sql instances describe clic --format 'value(connectionName)')
DB_NAME=$(kubectl get secrets cloudsql-${LABEL} -o 'go-template={{index .data "DB_NAME"}}' 2> /dev/null | base64 -D -)
DB_PASSWORD=$(kubectl get secrets cloudsql-${LABEL} -o 'go-template={{index .data "DB_PASSWORD"}}' 2> /dev/null | base64 -D -)
SECRET_KEY=$(kubectl get secrets django-${LABEL} -o 'go-template={{index .data "secret_key"}}' 2> /dev/null | base64 -D -)
SENTRY_DSN=$(kubectl get secrets sentry-${LABEL} -o 'go-template={{index .data "dsn"}}' 2> /dev/null | base64 -D -)

if [ -z "$DB_PASSWORD" ]; then
	read -p "Please enter the SQL password: " DB_PASSWORD
fi

if [ -z "$DB_NAME" ]; then
	DB_NAME=${LABEL}
	read -p "Please enter the SQL database [${LABEL}]: " DB_NAME
fi

if [ -z "$SECRET_KEY" ]; then
	read -p "Please enter a secret key for Django (optional): " SECRET_KEY
fi

if [ -z "$SENTRY_DSN" ]; then
	read -p "Please enter the Sentry DSN (optional): " SENTRY_DSN
fi

docker run \
	--rm \
	--name cloudsql \
	-d \
	-w "/cloudsql" \
	-v "$(pwd)/service-account.json":"/secret/service-account.json" \
	-e GOOGLE_APPLICATION_CREDENTIALS="/secret/service-account.json" \
	-p 5432:5432 \
	gcr.io/cloudsql-docker/gce-proxy:1.16 \
	/cloud_sql_proxy \
		-dir=/cloudsql \
		-instances=${DB_INSTANCE}=tcp:0.0.0.0:5432

docker run \
	--rm \
	-ti \
	-v "$(pwd)/service-account.json":"/secret/service-account.json" \
	-e GOOGLE_APPLICATION_CREDENTIALS="/secret/service-account.json" \
	-e DB_NAME="${DB_NAME}" \
	-e DB_USER=root \
	-e DB_PASSWORD="${DB_PASSWORD}" \
	-e DB_HOST="host.docker.internal" \
	-e DB_PORT="5432" \
	-e BUCKET_SUBMISSIONS="${LABEL}_submissions" \
	-e BUCKET_PUBLIC="${LABEL}_public" \
	-e SENTRY_DSN="${SENTRY_DSN}" \
	-e SECRET_KEY="${SECRET_KEY}" \
	-e DEBUG=1 \
	-w "$(pwd)/web" \
	-v "$(pwd)/web":"$(pwd)/web" \
	-p 8000:8000 \
	gcr.io/clic-215616/web \
	gunicorn \
		--bind :8000 \
		--worker-class gevent \
		--workers 2 \
		--timeout 600 \
		--reload \
		--log-level DEBUG \
		clic.wsgi

docker stop cloudsql
