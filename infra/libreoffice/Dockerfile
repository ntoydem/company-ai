# LibreOffice Calc, headless, for `seed_data/generator/recalc.sh` (Phase 4.2). Build-time
# tooling only (compose profile "tools"); the backend never runs this image.
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-calc-nogui \
        fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=C.UTF-8 HOME=/tmp
