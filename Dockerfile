FROM python:3.8-alpine

#ENV PYTHONUNBUFFERED 1
#ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /app
WORKDIR /app
ADD ./requirements.txt requirements.txt

RUN \
 apk add --no-cache postgresql-libs libmemcached && \
 apk add --no-cache --virtual .build-deps g++ musl-dev postgresql-dev libmemcached-dev zlib-dev && \
 python3 -m pip install -r requirements.txt --no-cache-dir && \
 python3 -m pip install pylibmc --no-cache-dir && \
 apk --purge del .build-deps

COPY . /app
EXPOSE 5000
