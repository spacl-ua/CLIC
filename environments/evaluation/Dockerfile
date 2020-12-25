ARG PROJECT_ID=clic-215616

FROM gcr.io/$PROJECT_ID/decoding:latest
MAINTAINER Lucas Theis

RUN apt-get update
RUN apt-get upgrade -y

WORKDIR /tmp
COPY requirements1.txt .
COPY requirements2.txt .
RUN pip3 install -r requirements1.txt
RUN pip3 install -r requirements2.txt
