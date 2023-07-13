ARG PROJECT_ID=clic-392518

FROM gcr.io/$PROJECT_ID/decoding:latest
MAINTAINER Lucas Theis

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y postgresql
RUN apt-get install -y default-libmysqlclient-dev build-essential
RUN apt-get install -y pkg-config
RUN apt-get install -y libpq-dev

WORKDIR /tmp
COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV PYTHONWARNINGS "ignore:Unverified HTTPS request"

COPY . /web
WORKDIR /web
