FROM nvidia/cuda:11.0.3-base-ubuntu18.04
MAINTAINER Lucas Theis

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y rsync
RUN apt-get install -y docker.io
RUN apt-get install -y python3.7 python3-pip
RUN apt-get install -y libssl-dev default-libmysqlclient-dev

WORKDIR /tmp
COPY requirements.txt .
RUN pip3 install -r requirements.txt

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
