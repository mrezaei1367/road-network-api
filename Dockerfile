FROM python:3.12-slim as base

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base as production
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base as test
COPY requirements-test.txt .
RUN pip install --no-cache-dir -r requirements-test.txt
COPY . .