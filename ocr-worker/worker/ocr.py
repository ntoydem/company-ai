"""ocrmypdf subprocess wrapper (ADR-006's exact flags)."""

from __future__ import annotations

import subprocess
from pathlib import Path


class OcrError(Exception):
    """ocrmypdf exited non-zero. `stderr` carries the tool's own diagnostic (log-only,
    never shown to an end user — see `pipeline.handle_failure`)."""

    def __init__(self, returncode: int, stderr: str) -> None:
        super().__init__(f"ocrmypdf exited with code {returncode}: {stderr}")
        self.returncode = returncode
        self.stderr = stderr


def run_ocr(input_pdf: Path, output_pdf: Path) -> None:
    result = subprocess.run(
        [
            "ocrmypdf",
            "--language",
            "tur+eng",
            "--skip-text",
            "--rotate-pages",
            "--deskew",
            str(input_pdf),
            str(output_pdf),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise OcrError(result.returncode, result.stderr)
