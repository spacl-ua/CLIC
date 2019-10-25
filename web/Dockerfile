ARG PROJECT_ID=clic-215616

FROM gcr.io/$PROJECT_ID/decoding:latest
MAINTAINER Lucas Theis

RUN apt-get update
RUN apt-get upgrade -y

WORKDIR /tmp
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . /web
WORKDIR /web
