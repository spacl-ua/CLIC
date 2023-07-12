FROM ubuntu
MAINTAINER Lucas Theis

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y git curl
RUN apt-get install -y libjpeg-dev libpng-dev
RUN apt-get install -y ffmpeg
RUN apt-get install -y python3.11 python3-pip python3-tk
RUN apt-get install -y libopenblas-base
RUN apt-get install -y libopencv-dev python3-opencv
RUN apt-get install -y libfreetype-dev
RUN apt-get install -y libhdf5-dev
RUN apt-get install -y cython3

WORKDIR /tmp
COPY requirements.txt .
COPY requirements2.txt .

RUN pip3 install -r requirements.txt
