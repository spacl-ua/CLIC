#!/bin/sh

read -p "Please enter the SQL password: " DB_PASSWORD

DB_INSTANCE=$(gcloud sql instances describe clic | grep connectionName | cut -d ' ' -f 2)
DB_HOST=$(gcloud sql instances describe clic | grep -i ipAddress: | cut -d ' ' -f 3)

cd docker/web;

docker run \
	--rm \
	-ti \
	-e DB_INSTANCE="${DB_INSTANCE}" \
	-e DB_NAME=clic2020 \
	-e DB_USER=root \
	-e DB_PASSWORD="${DB_PASSWORD}" \
	-e DB_HOST="${DB_HOST}" \
	-w "$(pwd)" \
	-v "$(pwd)":"$(pwd)" \
	-p 8000:8000 \
	gcr.io/clic-215616/web \
	/bin/bash
#	python3 manage.py runserver 0.0.0.0:8000
