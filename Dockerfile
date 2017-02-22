FROM alpine
MAINTAINER Roy Xiang <developer@royxiang.me>

ENV LANG C.UTF-8

RUN apk add --update --no-cache ca-certificates

RUN set -ex \
        && apk add --no-cache --virtual .run-deps \
                ffmpeg \
                freetype \
                lcms2 \
                libjpeg-turbo \
                libmagic \
                openblas \
                openjpeg \
                python3 \
                py3-certifi \
                py3-requests \
                tiff \
                libwebp \
                zlib \
        && ln -sf "$(python3 -c 'import requests; print(requests.__path__[0])')/cacert.pem" \
                  "$(python3 -c 'import certifi; print(certifi.__path__[0])')/cacert.pem" \
        && mkdir -p /opt/ehForwarderBot/storage

COPY . /opt/ehForwarderBot

RUN set -ex \
        && apk add --no-cache --virtual .build-deps \
                freetype-dev \
                lcms2-dev \
                libjpeg-turbo-dev \
                musl-dev \
                openblas-dev \
                openjpeg-dev \
                python3-dev \
                tiff-dev \
                libwebp-dev \
                zlib-dev \
        && ln -s /usr/include/locale.h /usr/include/xlocale.h \
        && pip3 install -r /opt/ehForwarderBot/requirements.txt \
        && rm /usr/include/xlocale.h \
        && rm -rf /root/.cache \
        && apk del .build-deps

WORKDIR /opt/ehForwarderBot

CMD ["python3", "main.py"]