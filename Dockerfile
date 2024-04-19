FROM python:3.12-alpine3.19 as requirements

RUN pip install poetry-plugin-export

WORKDIR /loxsi

COPY pyproject.toml poetry.lock ./

RUN poetry export --without-hashes --format=requirements.txt > requirements.txt

FROM python:3.12-alpine3.19

WORKDIR /loxsi

COPY --from=requirements /loxsi/requirements.txt .

RUN pip install -r requirements.txt

COPY . .
