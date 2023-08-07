FROM python:3.9-alpine

RUN mkdir code
WORKDIR code

ADD . /code/

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_NAME=DISTRIBUTION
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD gunicorn distribution.wsgi:application -b 0.0.0.0:8000