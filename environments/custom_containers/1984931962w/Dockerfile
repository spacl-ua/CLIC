ARG PYTORCH_VERSION=2.0.1-cuda11.7-cudnn8-devel

FROM pytorch/pytorch:$PYTORCH_VERSION

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt