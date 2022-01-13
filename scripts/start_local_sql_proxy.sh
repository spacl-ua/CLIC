#!/bin/sh
set -uxe

LABEL=${1-clic2022}

DB_INSTANCE=$(gcloud sql instances describe clic --format 'value(connectionName)')
DB_NAME=$(kubectl get secrets cloudsql-${LABEL} -o 'go-template={{index .data "DB_NAME"}}' 2> /dev/null | base64 -d -)
DB_PASSWORD=$(kubectl get secrets cloudsql-${LABEL} -o 'go-template={{index .data "DB_PASSWORD"}}' 2> /dev/null | base64 -d -)
 
cloud_sql_proxy -instances=${DB_INSTANCE}=tcp:0.0.0.0:1234 -credential_file service-account.json