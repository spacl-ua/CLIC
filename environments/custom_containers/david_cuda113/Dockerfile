FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel

RUN apt-get update \
    && apt-get install -y wget \
    && apt-get install -y unzip \
    && apt-get install build-essential \
    && pip install numpy \
        && pip install cupy-cuda113 \
        && pip install compressai==1.2.0b3 \
        && pip install opencv-python \
        && apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6
