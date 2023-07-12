#!/bin/bash
set -uxe

PROJECT_ID=$(gcloud config get-value project)

gcloud iam service-accounts create clic-sa --description="clic-service-account"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:clic-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:clic-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/container.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:clic-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/logging.admin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:clic-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/logging.admin"
