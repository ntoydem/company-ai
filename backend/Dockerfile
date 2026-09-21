FROM python:3.12-slim

# uv for reproducible installs from uv.lock
COPY --from=ghcr.io/astral-sh/uv:0.12.17 /uv /uvx /bin/

ARG APP_UID=1000
ARG APP_GID=1000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH="/opt/venv/bin:${PATH}"

RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home --shell /bin/bash app \
    && mkdir -p /app /data/documents /data/excel /data/app-data \
    && chown -R app:app /app /data

WORKDIR /app

# Dependencies only (dev group included: pytest/ruff/mypy run inside the container).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project && chown -R app:app /opt/venv

# Source is bind-mounted at /app by compose; copy as fallback for standalone builds.
COPY --chown=app:app . /app
RUN chmod +x /app/entrypoint.sh

USER app
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
