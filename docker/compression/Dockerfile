FROM ubuntu
MAINTAINER Lucas Theis

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y git
RUN apt-get install -y libjpeg-dev libpng-dev
RUN apt-get install -y ffmpeg
RUN apt-get install -y python2.7 python-pip
RUN apt-get install -y python3.7 python3-pip python3.7-tk
RUN apt-get install -y libopenblas-base
RUN apt-get install -y libopencv-dev python-opencv python3-opencv

WORKDIR /tmp
COPY requirements.txt .

RUN pip2 install -r requirements.txt
RUN pip3 install -r requirements.txt
