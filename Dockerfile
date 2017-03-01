FROM alpine:edge
MAINTAINER Roy Xiang <developer@royxiang.me>

ENV LANG C.UTF-8

RUN apk add --update --no-cache ca-certificates

RUN set -ex \
        && apk add --no-cache --virtual .run-deps \
                ffmpeg \
                libmagic \
                mailcap \
                python3 \
                py3-certifi \
                py3-numpy \
                py3-pillow \
                py3-requests \
        && ln -sf "$(python3 -c 'import requests; print(requests.__path__[0])')/cacert.pem" \
                  "$(python3 -c 'import certifi; print(certifi.__path__[0])')/cacert.pem" \
        && mkdir -p /opt/ehForwarderBot/storage

COPY . /opt/ehForwarderBot

RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
                git \
        && pip3 install pypng pyqrcode \
        && pip3 install -r /opt/ehForwarderBot/requirements.txt \
        && rm -rf /root/.cache \
        && apk del .build-deps

WORKDIR /opt/ehForwarderBot

CMD ["python3", "main.py"]
