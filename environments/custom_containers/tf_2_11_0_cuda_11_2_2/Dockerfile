FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04

# Install python
RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt install software-properties-common -y 
RUN add-apt-repository ppa:deadsnakes/ppa -y 
RUN apt install python3.9 -y
RUN apt install python3-pip -y
RUN apt-get install libgl1 -y

WORKDIR /tmp
COPY requirements.txt /tmp

# Install pip packages
RUN python3.9 -m pip install -r requirements.txt
