#!/bin/bash

# collect and upload static files
docker run --rm -ti \
	-w "$(pwd)/web" \
	-v "$(pwd)/web":"$(pwd)/web" \
	gcr.io/clic-215616/web \
	python3 manage.py collectstatic --no-input && \
gsutil -m rsync -R web/static/ gs://clic2020_public/static/

# allocate IP address if it does not already exist
gcloud compute addresses create clic2020-web --region us-west1 2> /dev/null
IP_ADDRESS=$(gcloud compute addresses describe clic2020-web --region us-west1 --format 'value(address)')

# start webserver
cat web/web.yaml | sed "s/{{ IP_ADDRESS }}/${IP_ADDRESS}/g" | kubectl apply -f -
