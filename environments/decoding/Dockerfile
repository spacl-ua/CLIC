FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
MAINTAINER Lucas Theis

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y rsync
RUN apt-get install -y docker.io
RUN apt-get install -y python3.11 python3-pip python3.11-dev
RUN apt-get install -y libssl-dev default-libmysqlclient-dev
# https://stackoverflow.com/questions/44043906/the-headers-or-library-files-could-not-be-found-for-jpeg-installing-pillow-on
RUN apt-get install -y libjpeg-dev
RUN apt-get install -y ffmpeg

WORKDIR /tmp
COPY requirements.txt .
RUN python3.7 -m pip install -r requirements.txt

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

# connects to SQL server
RUN \
	mkdir /cloudsql && \
	cd /cloudsql && \
	curl https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -o cloud_sql_proxy && \
	chmod +x cloud_sql_proxy
