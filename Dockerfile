FROM ubuntu:xenial
MAINTAINER Roy Xiang <developer@royxiang.me>

RUN apt-get update -y \
    && apt-get install -y python3 python3-pip ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/ehForwarderBot/storage

COPY . /opt/ehForwarderBot

RUN pip3 install --upgrade setuptools pip \
    && pip3 install -r /opt/ehForwarderBot/requirements.txt \
    && rm -rf /root/.cache/*

WORKDIR /opt/ehForwarderBot

CMD ["python3", "main.py"]
