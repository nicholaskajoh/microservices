FROM python:3.6-stretch
EXPOSE 8080

RUN mkdir /www
WORKDIR /www
COPY requirements.txt /www/
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED 1

COPY . /www/
CMD gunicorn --bind 0.0.0.0:8080 wsgi