FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update --fix-missing && apt-get install -y --fix-missing build-essential
RUN apt-get update && \
    apt-get install -y python3-dev && \
    apt-get install -y libgl1-mesa-glx && \
    apt-get install -y libglib2.0 && \
    pip install compressai==1.2.0b3