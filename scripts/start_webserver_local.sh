#!/bin/sh
set -uxe

LABEL="clic2023"
PROJECT_ID=$(gcloud config get-value project)

INTERACTIVE=false

for arg in "$@"; do
	case $arg in
		-i|--interactive)
			INTERACTIVE=true
	esac
done

if [ ! -f service-account.json ]; then
	# create service account key file
	if ( kubectl get secret clic-sa-key 2>&1 > /dev/null ); then
		kubectl get secrets clic-sa-key -o 'go-template={{index .data "service-account.json"}}' | base64 -d - > service-account.json;
	else
		read -p "Please enter a service account [clic-sa@${PROJECT_ID}.iam.gserviceaccount.com]: " SERVICE_ACCOUNT
		SERVICE_ACCOUNT=${SERVICE_ACCOUNT:-clic-sa@${PROJECT_ID}.iam.gserviceaccount.com}
		gcloud iam service-accounts keys create --iam-account "${SERVICE_ACCOUNT}" service-account.json
	fi
fi

DB_INSTANCE=$(gcloud sql instances describe clic --format 'value(connectionName)')
DB_NAME=$(kubectl get secrets cloudsql-${LABEL} -o 'go-template={{index .data "DB_NAME"}}' 2> /dev/null | base64 -d -i -)
DB_PASSWORD=$(kubectl get secrets cloudsql-${LABEL} -o 'go-template={{index .data "DB_PASSWORD"}}' 2> /dev/null | base64 -d -i -)
SECRET_KEY=$(kubectl get secrets django-${LABEL} -o 'go-template={{index .data "secret_key"}}' 2> /dev/null | base64 -d -i -)
SENTRY_DSN=$(kubectl get secrets sentry-${LABEL} -o 'go-template={{index .data "dsn"}}' 2> /dev/null | base64 -d -i -)

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

if $INTERACTIVE; then
	COMMAND="/bin/bash"
else
	COMMAND="gunicorn \
		--bind :8000 \
		--worker-class gevent \
		--workers 2 \
		--timeout 600 \
		--reload \
		--log-level DEBUG \
		clic.wsgi"
fi

# open connection to MySQL server
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
		-instances=${DB_INSTANCE}=tcp:0.0.0.0:5432 \
		 || echo "Failed starting proxy"

# start webserver

# Note --add-host due to
# https://stackoverflow.com/questions/48546124/what-is-linux-equivalent-of-host-docker-internal/61001152

docker run \
	--rm \
	-ti \
	-v "$(pwd)/service-account.json":"/secret/service-account.json" \
	-e GOOGLE_APPLICATION_CREDENTIALS="/secret/service-account.json" \
	-e DB_NAME="${DB_NAME}" \
	-e DB_USER=root \
	-e DB_PASSWORD="${DB_PASSWORD}" \
	--add-host=host.docker.internal:host-gateway \
	-e DB_HOST="host.docker.internal" \
	-e DB_PORT="5432" \
	-e BUCKET_SUBMISSIONS="${LABEL}_submissions" \
	-e BUCKET_PUBLIC="${LABEL}_public" \
	-e SENTRY_DSN="${SENTRY_DSN}" \
	-e SECRET_KEY="${SECRET_KEY}" \
	-e SECURE_SSL_REDIRECT=0 \
	-e DEBUG=1 \
	-w "$(pwd)/web" \
	-v "$(pwd)/web":"$(pwd)/web" \
	-p 8000:8000 \
	"gcr.io/${PROJECT_ID}/web-${LABEL}" \
	/bin/bash \
	-c "${COMMAND}"


# close connection to MySQL server
docker stop cloudsql
