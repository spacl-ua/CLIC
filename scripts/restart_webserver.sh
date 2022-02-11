#!/bin/bash
set -uxe

# Build new docker image if needed.

# ./scripts/build_web_image.sh

# Split up to support deploying clic2022 into clic2021 deployment.
LABEL="clic2022"
DEPLOYMENT="clic2022"

# collect and upload static files
docker run --rm -ti \
	-w "$(pwd)/web" \
	-v "$(pwd)/web":"$(pwd)/web" \
	gcr.io/clic-215616/web-${LABEL} \
	python3 manage.py collectstatic --no-input && \
gsutil -m rsync -R web/static/ gs://${LABEL}_public/static/

# To be safe, lets not run thess unless  we have to.

# # allocate IP address if it does not already exist
# gcloud compute addresses create ${LABEL}-web --region us-west1 2> /dev/null && rc=$? || rc=$?                                         
# # https://stackoverflow.com/questions/9629710/what-is-the-proper-way-to-detect-shell-exit-code-when-errexit-option-is-set
# echo "exit code for ip allocation: $rc"

IP_ADDRESS=$(gcloud compute addresses describe ${DEPLOYMENT}-web --region us-west1 --format 'value(address)')
echo "IP_ADDRESS: $IP_ADDRESS"

# get sha256 of latest image
DIGEST=$(gcloud container images describe --format 'get(image_summary.digest)' gcr.io/clic-215616/web-${LABEL})

# start webserver
cat web/web.yaml | sed "s/{{ LABEL }}/${LABEL}/g" | sed "s/{{ DEPLOYMENT }}/${DEPLOYMENT}/g" | sed "s/{{ IP_ADDRESS }}/${IP_ADDRESS}/g" | sed "s/{{ DIGEST }}/${DIGEST}/g" | kubectl apply -f -
