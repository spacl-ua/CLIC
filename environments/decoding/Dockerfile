FROM nvidia/cuda:10.0-base-ubuntu18.04
MAINTAINER Lucas Theis

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y rsync
RUN apt-get install -y docker.io
RUN apt-get install -y python3.7 python3-pip

# install gcsfuse for mounting cloud storage
RUN apt-get install -y lsb-release curl gnupg2
ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE true
RUN \
	export GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s) && \
	echo "deb http://packages.cloud.google.com/apt $GCSFUSE_REPO main" | tee /etc/apt/sources.list.d/gcsfuse.list && \
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
	apt-get update && \
	apt-get install -y gcsfuse

RUN \
	export CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)" && \
	echo "deb http://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
	apt-get update && \
	apt-get install -y google-cloud-sdk
