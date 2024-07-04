FROM python:3.12.4-slim-bullseye

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONBUFFERED 1


RUN apt-get update \
    && apt-get -y install g++ libpq-dev gcc unixodbc unixodbc-dev
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

COPY . /usr/src/app

ENTRYPOINT [ "/usr/src/app/entrypoint.sh" ]
