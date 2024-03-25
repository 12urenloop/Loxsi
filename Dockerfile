FROM python:3.12

RUN pip install -U poetry
RUN poetry config virtualenvs.create false

WORKDIR /loxsi

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main

COPY . .

# CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "main:app"]
