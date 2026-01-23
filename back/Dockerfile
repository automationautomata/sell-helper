FROM python:3.12-slim as base

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
    
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgl1 \
        libzbar0 \
	libpq-dev && \
    rm -rf /var/lib/apt/lists/*

FROM base AS builder

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN python -m pip install --no-cache-dir poetry==2.0.0 &&  \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root --no-interaction --no-ansi

FROM base as runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY app ./app
COPY config/config.yaml ./config/config.yaml
