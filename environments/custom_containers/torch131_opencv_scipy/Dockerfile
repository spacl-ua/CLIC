FROM pytorch/pytorch:1.3-cuda10.1-cudnn7-devel

RUN \
    pip install pip --upgrade -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install opencv-python-headless -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install scipy -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip list &&  \
    gcc --version && \
    echo done
