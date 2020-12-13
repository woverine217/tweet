FROM python:3.9.0-slim
COPY / /app
WORKDIR /app
RUN apt-get -y update
RUN apt-get -y upgrade
RUN apt-get install -y sqlite3 libsqlite3-dev
RUN pip install --upgrade pip
RUN pip install pipenv
RUN pipenv install
RUN pipenv install --system
RUN pipenv update
EXPOSE 5000
ENTRYPOINT ["python3"]
CMD ["twtr.py"]