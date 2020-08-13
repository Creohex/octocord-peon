FROM python:3.7.4-slim

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 80 443

COPY ./app/init /app/init
COPY ./app/assets /app/assets
COPY ./app/peon /usr/local/lib/python3.7/site-packages/peon

CMD ["/bin/bash", "./init/entrypoint.sh"]
