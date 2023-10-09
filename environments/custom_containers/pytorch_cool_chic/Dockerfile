FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

RUN apt-get update && \
    pip install torchvision==0.15.2 && \
    pip install constriction==0.3.0 && \
    pip install einops==0.6.0 && \
    pip install fvcore==0.1.5.post20221221
