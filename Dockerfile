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
                py3-numpy \
                py3-openssl \
                py3-pillow

COPY . /root/ehForwarderBot

RUN set -ex \
        && apk add --no-cache --virtual .build-deps git \
        && pip3 install --upgrade setuptools pip \
        && pip3 install pypng pyqrcode requests[security] \
        && pip3 install -r /root/ehForwarderBot/requirements.txt \
        && ln -sf "$(python3 -c 'import requests; print(requests.__path__[0])')/cacert.pem" \
                  "$(python3 -c 'import certifi; print(certifi.__path__[0])')/cacert.pem" \
        && rm -rf /root/.cache \
        && apk del .build-deps

WORKDIR /root/ehForwarderBot

CMD ["python3", "main.py"]
