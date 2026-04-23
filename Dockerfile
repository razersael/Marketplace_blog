FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system -e .

COPY src/ ./src/
COPY alembic.ini ./
COPY migrations/ ./migrations/

CMD ["sh", "-c", "alembic upgrade head && uvicorn src.marketplace_blog.main:app --host 0.0.0.0 --port 8000"]CMD ["sh", "-c", "alembic upgrade head && uvicorn src.marketplace_blog.main:app --host 0.0.0.0 --port 8000"]
