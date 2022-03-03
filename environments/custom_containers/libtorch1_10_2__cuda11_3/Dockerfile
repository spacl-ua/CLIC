FROM pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel

RUN apt-get update \
    && apt-get install -y wget \
        && apt-get install -y unzip \
	    && pip install numpy \
	        && pip install imageio==1.5.0 \
		    && pip install opencv-python-headless \
		        && wget -P /usr/local https://download.pytorch.org/libtorch/cu113/libtorch-cxx11-abi-shared-with-deps-1.10.2%2Bcu113.zip \
			    && unzip /usr/local/libtorch-cxx11-abi-shared-with-deps-1.10.2+cu113.zip -d /usr/local \
			        && rm /usr/local/libtorch-cxx11-abi-shared-with-deps-1.10.2+cu113.zip

    