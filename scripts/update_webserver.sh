#!/bin/bash

IP_ADDRESS=$(gcloud compute addresses describe clic2020-web --region us-west1 --format 'value(address)')
cat web/web.yaml | sed "s/{{ IP_ADDRESS }}/${IP_ADDRESS}/g" | kubectl apply -f -
