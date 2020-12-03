FROM python:3.7-slim

RUN mkdir /app
WORKDIR /app

ENV FLASK_APP=liberaforms
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000
ENV FLASK_ENV=production

#ENV SECRET_KEY="super secret key"
#ENV ROOT_USERS=["me@example.com"]
#ENV MONGODB_HOST=127.0.0.1
#ENV MONGODB_PORT=2701
#ENV MONGODB_DB=liberaforms
#ENV MONGODB_USERNAME = 'db_user'
#ENV MONGODB_PASSWORD = 'pwd123'

COPY . /app
RUN pip3 install -r requirements.txt

EXPOSE 5000
#CMD ["flask", "run"]
ENTRYPOINT ["python", "/app/app.py"]
