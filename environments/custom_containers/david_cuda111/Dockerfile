FROM pytorch/pytorch:1.8.1-cuda11.1-cudnn8-runtime

RUN apt-get update \
    && apt-get install -y wget \
    && apt-get install -y unzip \
    && apt-get install -y build-essential \
    && pip install numpy \
	&& pip install cupy-cuda111 \
	&& pip install compressai==1.2.0b3 \
	&& pip install opencv-python \
	&& apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6
