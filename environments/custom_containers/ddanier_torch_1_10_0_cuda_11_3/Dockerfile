FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-runtime

# Python packages
RUN pip install --upgrade pip
RUN pip install --upgrade opencv-python
RUN pip install --upgrade numpy

RUN apt-get update && apt-get -y install unzip
