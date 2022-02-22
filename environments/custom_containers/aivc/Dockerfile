FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel

RUN apt-get update && \
    apt-get install ninja-build && \
    pip install tensorboard && \
    pip install colorama && \
    pip install matplotlib && \
    pip install graphviz && \
    pip install scipy && \
    pip install torchac