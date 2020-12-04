FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
EXPOSE 5000

ENV FLASK_APP=liberaforms
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_ENV=production
ENV SESSION_TYPE=memcached

#ENV SECRET_KEY="super secret key"
#ENV ROOT_USERS=["me@example.com"]
#ENV MONGODB_HOST=127.0.0.1
#ENV MONGODB_PORT=2701
#ENV MONGODB_DB=liberaforms
#ENV MONGODB_USERNAME = 'db_user'
#ENV MONGODB_PASSWORD = 'pwd123'

#ENTRYPOINT ["python", "/app/app.py"]
