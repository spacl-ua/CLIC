#!/bin/bash

cd "$(dirname "$(realpath $0)")/.."

[ -z "$1" ] && echo "missing image name"
[ -z "$1" ] && exit 1


mkdir -p environments/custom_containers/$1
echo Write your dockerfile now and press ctrl+D
cat > environments/custom_containers/$1/Dockerfile

cp cloudbuild_custom_dockers.yaml /tmp/add_image_yamltmp

(
cat << EOF
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/\$PROJECT_ID/custom_containers/$1:latest', 'environments/custom_containers/$1']
EOF
tail -n +2 /tmp/add_image_yamltmp
echo "  - 'gcr.io/\$PROJECT_ID/custom_containers/$1:latest'"
) > cloudbuild_custom_dockers.yaml

git add environments/custom_containers/$1
git commit -a -m "Add $1 Docker container"
