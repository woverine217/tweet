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
RUN pip3 install git+https://github.com/dimitrismistriotis/profanity-check.git
EXPOSE 5000
RUN chmod a+x main.sh
CMD ["./main.sh"]
