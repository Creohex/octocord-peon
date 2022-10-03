FROM python:3.9.14-alpine3.15

WORKDIR /app

RUN set -eux; \
    apk update; \
    apk add --no-cache bash git wget; \
    mkdir ./packages; \
    cd ./packages; \
    git clone https://github.com/smiley/steamapi;

COPY ./requirements.txt /app

RUN set -eux; \
    pip install --upgrade pip; \
    pip install --trusted-host pypi.python.org wheel; \
    pip install /app/packages/steamapi; \
    pip install --trusted-host pypi.python.org -r requirements.txt;

EXPOSE 80 443

COPY ./app/init /app/init
COPY ./app/assets /app/assets
COPY ./app/peon /usr/local/lib/python3.9/site-packages/peon

CMD ["/bin/bash", "./init/entrypoint.sh"]
