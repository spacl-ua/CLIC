FROM pytorch/pytorch:1.9.0-cuda10.2-cudnn7-runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    apt-get install -y libglib2.0 && \
    pip install mmcv-full==1.4.5 -f https://download.openmmlab.com/mmcv/dist/cu102/torch1.9.0/index.html && \
    pip install compressai==1.2.0b3
