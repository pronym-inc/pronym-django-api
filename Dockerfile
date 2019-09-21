FROM python:3.6

ADD . /app

RUN pip3 install pytest
RUN pip3 install /app/
