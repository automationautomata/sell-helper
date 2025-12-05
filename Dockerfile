FROM python:3.12-slim AS builder

WORKDIR /app

COPY pyproject.toml .
RUN python -m pip install --no-cache-dir poetry==1.4.2 &&  \
    poetry config virtualenvs.in-project true && \
    poetry install --without test --no-interaction --no-ansi



FROM python:3.12-slim AS base


RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /app /app
COPY app ./

EXPOSE 8000

CMD ["./.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
