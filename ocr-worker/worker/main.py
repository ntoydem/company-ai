"""Poll loop entrypoint: `python -m worker.main`."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from worker.config import load_config
from worker.db import Tables, make_engine
from worker.logging_config import setup_logging
from worker.pipeline import process_one_job, requeue_stale_jobs

log = logging.getLogger("worker.main")
HEARTBEAT_PATH = Path("/tmp/worker-heartbeat")  # noqa: S108 - container-local, not shared state


def _touch_heartbeat() -> None:
    HEARTBEAT_PATH.write_text("", encoding="utf-8")


def run() -> None:
    setup_logging()
    config = load_config()
    engine = make_engine(config.database_url)
    tables = Tables(engine)
    log.info("ocr-worker started", extra={"poll_interval_s": config.poll_interval_s})

    while True:
        _touch_heartbeat()
        requeue_stale_jobs(engine, tables, config.stale_job_minutes)
        processed = process_one_job(engine, tables, config)
        if not processed:
            time.sleep(config.poll_interval_s)


if __name__ == "__main__":
    run()
