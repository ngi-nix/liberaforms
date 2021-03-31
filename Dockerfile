FROM python:3.8-slim

#ENV PYTHONUNBUFFERED 1
#ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /app
WORKDIR /app

ADD ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /app
EXPOSE 5000
