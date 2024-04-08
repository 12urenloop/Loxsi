FROM python:3.12-alpine3.19

RUN pip install -U poetry
RUN poetry config virtualenvs.create false

WORKDIR /loxsi

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main

COPY . .
