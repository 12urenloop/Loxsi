FROM python:3.12

WORKDIR /loxsi

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "--host", "0.0.0.0", "--port", "80", "main:app"]