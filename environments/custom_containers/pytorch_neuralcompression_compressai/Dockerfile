FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime

RUN apt-get update && apt-get install -y g++ gcc

RUN \
    pip install pip --upgrade && \
    pip install compressai==1.2.4 && \
    pip install einops && \
    pip install timm==0.9.7 && \
    pip install omegaconf && \
    pip install scikit-learn &&\
    pip install lightning==2.0.4 && \
    pip install pytorch-lightning==2.0.4 && \
    pip install pytorch-msssim && \
    pip install tabulate && \
    pip install neuralcompression==0.3.1 && \
    pip install torchmetrics==1.1.2 && \
    pip install torch-fidelity==0.3.0 && \
    pip install hydra-core==1.3.2
