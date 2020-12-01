FROM python:3.7-slim
RUN mkdir /app
WORKDIR /app

#ENV SECRET_KEY="super secret key"
#ENV ROOT_USERS=["me@example.com"]
#ENV MONGODB_HOST=127.0.0.1
#ENV MONGODB_PORT=2701
#ENV MONGODB_DB=liberaforms
ENV FLASK_ENV=production


ADD requirements.txt /app
ADD app.py /app
RUN pip3 install -r requirements.txt
ADD . /app
EXPOSE 5000
ENTRYPOINT ["python", "/app/app.py"]
