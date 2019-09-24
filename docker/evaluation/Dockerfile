ARG PROJECT_ID=clic-215616

FROM gcr.io/$PROJECT_ID/decoding:latest
MAINTAINER Lucas Theis

RUN apt-get update
RUN apt-get upgrade -y

RUN apt-get install -y python3-pip

WORKDIR /tmp
COPY requirements.txt .
RUN pip3 install -r requirements.txt

#COPY evaluate.py .
#ENTRYPOINT ["python3", "evaluate.py"]
