#!/bin/bash
set -uxe

LABEL=clic2022

# request some information
read -p "Please enter the SQL username [root]: " DB_USER
read -p "Please enter the SQL password: " DB_PASSWORD
DB_INSTANCE=$(gcloud sql instances describe clic --format 'value(connectionName)')
DB_USER=${DB_USER:-root}
DB_NAME="${LABEL}"

# https://humberto.io/blog/tldr-generate-django-secret-key/
SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(50))')"
read -p "Please enter the Sentry DSN (optional): " SENTRY_DSN

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