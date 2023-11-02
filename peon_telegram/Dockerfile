FROM python:3.11.4-alpine3.18

WORKDIR /app

RUN set -eux; \
    apk update; \
    apk add --no-cache bash git wget openssh-client build-base linux-headers; \
    pip install --upgrade pip;

# installing project dependencies at a deeper layer to speed up container build process:
COPY ./dependencies/deps_common.txt ./dependencies/deps_telegram.txt dependencies/
RUN set -eux; \
    for file in ./dependencies/*.txt; do pip install --no-cache-dir -r "$file"; done;

# application setup:
COPY ./init ./peon_telegram/start.py init/
COPY ./peon_common ./peon_telegram packages/
RUN set -eux; \
    pip install --no-cache-dir -e ./packages;

EXPOSE 80 443

CMD ["/bin/bash", "/app/init/entrypoint.sh"]
