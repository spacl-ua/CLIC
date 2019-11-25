#!/bin/bash

IP_ADDRESS=$(gcloud compute addresses describe clic2020-web --region us-west1 --format 'value(address)')
DIGEST=$(gcloud container images describe --format 'get(image_summary.digest)' gcr.io/clic-215616/web)
cat web/web.yaml | sed "s/{{ IP_ADDRESS }}/${IP_ADDRESS}/g" | sed "s/{{ DIGEST }}/${DIGEST}/g" | kubectl apply -f -
