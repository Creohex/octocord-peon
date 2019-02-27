FROM python:3.6-slim

WORKDIR /app
COPY ./requirements.txt /app
RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 80 443

COPY ./app /app

CMD ["python", "app.py"]

