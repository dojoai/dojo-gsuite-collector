FROM python:3.8-slim-buster

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

RUN pip install Flask gunicorn google-api-python-client urllib3 google-cloud-bigquery google-cloud-storage python-dateutil gdown

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app
