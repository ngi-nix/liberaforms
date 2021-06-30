FROM python:3.8-buster

#ENV PYTHONUNBUFFERED 1
#ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$PATH:$VIRTUAL_ENV/bin"

RUN apt-get install libmemcached-dev -y

RUN mkdir /app
WORKDIR /app
ADD ./requirements.txt requirements.txt

RUN pip install -r requirements.txt --no-cache-dir
RUN pip install pylibmc --no-cache-dir

COPY . /app
EXPOSE 5000
