FROM ubuntu:xenial
MAINTAINER Roy Xiang <developer@royxiang.me>

RUN apt-get update -y && apt-get install -y python3 ffmpeg \
        libtiff5 libjpeg8 zlib1g libfreetype6 liblcms2-2 libwebp5 \
        libtcl8.6 libtk8.6 python3-magic python3-tk \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/ehForwarderBot/storage

COPY . /opt/ehForwarderBot

RUN apt-get update -y && apt-get install -y python3-pip \
        libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
        liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev \
    && pip3 install --upgrade setuptools pip \
    && pip3 install -r /opt/ehForwarderBot/requirements.txt \
    && rm -rf /root/.cache/* \
    && apt-get purge -y python3-pip \
        libtiff5-dev libjpeg8-dev zlib1g-dev libfreetype6-dev \
        liblcms2-dev libwebp-dev tcl8.6-dev tk8.6-dev \
    && apt-get autoremove --purge -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/ehForwarderBot

CMD ["python3", "main.py"]
