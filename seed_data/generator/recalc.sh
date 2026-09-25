#!/usr/bin/env bash
# Phase 4.2: recalculate every generated workbook with LibreOffice headless so each formula
# cell carries a cached value (openpyxl writes formulas only; SPEC_04 §6). Runs inside the
# `libreoffice` tools container (infra/libreoffice/Dockerfile): make excel -> compose run.
# Usage: recalc.sh [file.xlsx ...]   (default: every seed_data/excel/*.xlsx)
set -euo pipefail

EXCEL_DIR="$(cd "$(dirname "$0")/../excel" && pwd)"
PROFILE="file:///tmp/lo_profile"
files=("$@")
if [ ${#files[@]} -eq 0 ]; then
  files=("$EXCEL_DIR"/*.xlsx)
fi

for f in "${files[@]}"; do
  out="$(mktemp -d)"
  # --convert-to xlsx re-saves through Calc: formulas without a cached value are computed on
  # load and written back with their results. Profile in /tmp: headless first-run safe.
  timeout 180 soffice "-env:UserInstallation=$PROFILE" --headless --norestore --nologo \
    --convert-to xlsx --outdir "$out" "$f" >/dev/null
  if [ ! -s "$out/$(basename "$f")" ]; then
    echo "recalc failed: $f" >&2
    exit 1
  fi
  mv "$out/$(basename "$f")" "$f"
  rm -rf "$out"
  echo "recalculated: $(basename "$f")"
done
