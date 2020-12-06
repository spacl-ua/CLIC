#!/bin/bash

# collect and upload static files
docker run --rm -ti \
	-w "$(pwd)/web" \
	-v "$(pwd)/web":"$(pwd)/web" \
	gcr.io/clic-215616/web-${LABEL} \
	python3 manage.py collectstatic --no-input && \
gsutil -m rsync -R web/static/ gs://clic2021_public/static/

# allocate IP address if it does not already exist
gcloud compute addresses create clic2021-web --region us-west1 2> /dev/null
IP_ADDRESS=$(gcloud compute addresses describe ${LABEL}-web --region us-west1 --format 'value(address)')

# get sha256 of latest image
DIGEST=$(gcloud container images describe --format 'get(image_summary.digest)' gcr.io/clic-215616/web-${LABEL})

# start webserver
cat web/web.yaml | sed "s/{{ IP_ADDRESS }}/${IP_ADDRESS}/g" | sed "s/{{ DIGEST }}/${DIGEST}/g" | kubectl apply -f -
