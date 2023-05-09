FROM bitnami/python:latest

WORKDIR /application

COPY . /application

RUN python3 -m pip install --upgrade pip wheel setuptools
RUN python3 -m pip install -r requirements.txt
