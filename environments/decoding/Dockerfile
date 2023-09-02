FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
MAINTAINER Lucas Theis

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y rsync
RUN apt-get install -y docker.io
RUN apt-get install -y python3.11 python3-pip python3.11-dev
RUN apt-get install -y libssl-dev default-libmysqlclient-dev build-essential
RUN apt-get install -y pkg-config
# https://stackoverflow.com/questions/44043906/the-headers-or-library-files-could-not-be-found-for-jpeg-installing-pillow-on
RUN apt-get install -y libjpeg-dev
RUN apt-get install -y ffmpeg

# use Python 3.11 by default
RUN \
	rm /usr/bin/python3 && \
	ln -s $(which python3.11) /usr/bin/python3

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

# install Google Cloud CLI
RUN \
	apt-get install -y apt-transport-https ca-certificates gnupg curl
RUN \
	echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
	curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
	apt-get update && \
	apt-get install google-cloud-cli

# add proxy for connecting to SQL server
RUN \
	mkdir /cloudsql && \
	cd /cloudsql && \
	curl https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -o cloud_sql_proxy && \
	chmod +x cloud_sql_proxy
