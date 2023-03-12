FROM python:3.9.14-alpine3.15

WORKDIR /app

RUN set -eux; \
    apk update; \
    apk add --no-cache bash git wget openssh-client build-base linux-headers; \
    pip install --upgrade pip;

COPY ./peon_common /packages/peon_common
COPY ./peon_telegram /packages/peon_telegram

RUN set -eux; \
    pip install /packages/peon_common; \
    pip install /packages/peon_telegram;

RUN set -eux; \
    cp /packages/peon_telegram/start.py /app/

EXPOSE 80 443

CMD ["/bin/bash", "/packages/peon_common/init/entrypoint.sh"]
