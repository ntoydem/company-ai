# ocrmypdf + tesseract (tur+eng) + PyMuPDF ingestion worker (ADR-006, Phase 0.2).
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

# ocrmypdf's own system dependencies: tesseract + Turkish/English language data,
# ghostscript (PDF/A conversion) and qpdf (repair/linearization). `--rotate-pages` and
# `--deskew` are covered by ocrmypdf's Python package itself; `unpaper` (only needed for
# `--clean`, not used here) is deliberately omitted.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-tur \
        tesseract-ocr-eng \
        ghostscript \
        qpdf \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home --shell /bin/bash app \
    && mkdir -p /worker /data/documents \
    && chown -R app:app /worker /data

WORKDIR /worker

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project && chown -R app:app /opt/venv

COPY --chown=app:app . /worker

USER app

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD find /tmp/worker-heartbeat -mmin -1 || exit 1

CMD ["python", "-m", "worker.main"]
