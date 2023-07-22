#!/bin/bash
set -uxe

# Build new docker image if needed.
# ./scripts/build_web_image.sh

# Split up to support deploying clic202x into clic202y deployment.
LABEL="clic2023"
DEPLOYMENT="clic2023"

PROJECT_ID=$(gcloud config get-value project)

# make sure we're using the latest image
docker pull gcr.io/${PROJECT_ID}/web-${LABEL}

# collect and upload static files
docker run --rm -ti \
	-w "$(pwd)/web" \
	-v "$(pwd)/web":"$(pwd)/web" \
	gcr.io/${PROJECT_ID}/web-${LABEL} \
	python3 manage.py collectstatic --no-input && \
gsutil -m rsync -R web/static/ gs://${LABEL}_public/static/

# allocate IP address if it does not already exist
# https://stackoverflow.com/questions/9629710/what-is-the-proper-way-to-detect-shell-exit-code-when-errexit-option-is-set
gcloud compute addresses create ${LABEL}-web --region us-west1 2> /dev/null && rc=$? || rc=$?
echo "exit code for ip allocation: $rc"

IP_ADDRESS=$(gcloud compute addresses describe ${DEPLOYMENT}-web --region us-west1 --format 'value(address)')
echo "IP_ADDRESS: $IP_ADDRESS"

# get sha256 of latest image
DIGEST=$(gcloud container images describe --format 'get(image_summary.digest)' gcr.io/${PROJECT_ID}/web-${LABEL})

# start webserver
cat web/web.yaml | sed "s/{{ LABEL }}/${LABEL}/g" | sed "s/{{ DEPLOYMENT }}/${DEPLOYMENT}/g" | sed "s/{{ IP_ADDRESS }}/${IP_ADDRESS}/g" | sed "s/{{ DIGEST }}/${DIGEST}/g" | kubectl apply -f -
