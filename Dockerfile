FROM alpine:3.7
MAINTAINER Roy Xiang <developer@royxiang.me>

ENV LANG C.UTF-8

RUN apk add --update --no-cache ca-certificates

RUN set -ex \
        && apk add --no-cache --virtual .run-deps \
                ffmpeg \
                libmagic \
                mailcap \
                python3 \
                py3-numpy \
                py3-pillow

ENV FFMPEG_BINARY /usr/bin/ffmpeg

COPY . /opt/ehForwarderBot

RUN set -ex \
        && apk add --no-cache --virtual .build-deps git \
        && pip3 install -U setuptools pip \
        && pip3 install -r /opt/ehForwarderBot/requirements-pre.txt \
        && pip3 install -r /opt/ehForwarderBot/requirements.txt \
        && rm -rf /root/.cache \
        && apk del .build-deps \
        && mkdir /data \
        && ln -sf /data/config.py /opt/ehForwarderBot/config.py \
        && ln -sf /data/tgdata.db /opt/ehForwarderBot/plugins/eh_telegram_master/tgdata.db \
        && chown -R 32767:32767 /opt/ehForwarderBot/storage

EXPOSE 5000

USER 32767:32767

WORKDIR /opt/ehForwarderBot

CMD ["python3", "main.py"]
