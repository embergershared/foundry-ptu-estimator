FROM python:3.13-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /uvx /usr/local/bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim AS runtime

LABEL org.opencontainers.image.title="foundry-tpu-est-data" \
      org.opencontainers.image.description="Azure AI Foundry traffic generator for PTU sizing" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/embergershared/foundry-tpu-est-data"

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LOG_LEVEL=INFO

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src/tpu_est /app/src/tpu_est

RUN useradd --uid 10001 --create-home --shell /bin/bash app \
    && chown -R app:app /app

USER app

ENTRYPOINT ["python", "-m", "tpu_est", "run-once"]
