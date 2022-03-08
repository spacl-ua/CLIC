FROM pytorch/pytorch:1.8.1-cuda10.2-cudnn7-runtime

RUN apt-get update \
    && apt-get install -y wget \ 
    && apt-get install -y unzip \
    && pip install numpy \
    && pip install imageio==1.5.0 \
    && pip install opencv-python-headless \
    && wget -P /usr/local https://download.pytorch.org/libtorch/lts/1.8/cu102/libtorch-cxx11-abi-shared-with-deps-1.8.2%2Bcu102.zip \
    && unzip /usr/local/libtorch-cxx11-abi-shared-with-deps-1.8.2+cu102.zip -d /usr/local \ 
    && rm /usr/local/libtorch-cxx11-abi-shared-with-deps-1.8.2+cu102.zip
