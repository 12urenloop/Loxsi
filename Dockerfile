FROM pypy:slim-bullseye

RUN pip install -U poetry
RUN poetry config virtualenvs.create false

WORKDIR /loxsi

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main

COPY . .

CMD [ "pypy3", "-m", "uvicorn", "--host", "0.0.0.0", "--port", "80", "main:app" ]
