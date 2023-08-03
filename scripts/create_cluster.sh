#!/bin/bash

# create cluster and CPU nodes
gcloud container clusters create clic-cluster \
	--zone us-west1-b \
	--machine-type n1-standard-4 \
	--enable-autoscaling \
	--min-nodes 1 \
	--max-nodes 4 \
	--num-nodes 1 \
	--verbosity error

# add GPU nodes
gcloud container node-pools create gpu-pool \
	--cluster clic-cluster \
	--zone us-west1-b \
	--machine-type g2-standard-8 \
	--accelerator type=nvidia-l4-vws,count=1 \
	--enable-autoscaling \
	--min-nodes 0 \
	--max-nodes 4 \
	--num-nodes 0 \
	--disk-size 200GB \
	--verbosity error

# install nvidia drivers on GPU nodes
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
