#!/usr/bin/env bash
# Upload the Phase 0.2 T0 fixtures with the version chain for Phase 0.3's T0 questions:
#   Facility Agreement (EXECUTED, 01.06.2023, DSCR 1,25x) → Amendment 01 (15.03.2025, DSCR 1,20x)
# Usage (from the repo root, after `make up`):  bash seed_data/t0/upload.sh
# Requires only curl (host) — the PDFs are generated inside the backend container if missing.
set -euo pipefail

cd "$(dirname "$0")/../.."
ENV_FILE="${ENV_FILE:-.env}"
BACKEND_PORT="$(grep -E '^BACKEND_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- || true)"
API="http://localhost:${BACKEND_PORT:-8000}"
T0="seed_data/t0"

if [[ ! -f "$T0/facility_agreement.pdf" || ! -f "$T0/amendment_01.pdf" ]]; then
  echo "T0 PDF'leri üretiliyor..."
  docker compose --project-directory . -f infra/docker-compose.yml --env-file "$ENV_FILE" \
    run --rm -T backend python seed_data/t0/generate.py
fi

json_field() { sed -n "s/.*\"$1\":\"\([^\"]*\)\".*/\1/p"; }

upload() { # file title document_date effective_date [supersedes_id]
  local extra=()
  [[ -n "${5:-}" ]] && extra=(-F "supersedes_document_id=$5")
  curl -sf -X POST "$API/api/documents/upload" \
    -F "file=@$1;type=application/pdf" -F "title=$2" -F "document_type=facility_agreement" \
    -F "document_date=$3" -F "effective_date=$4" -F "counterparty=PQR Bank A.Ş." \
    -F "status=executed" -F "version=1" "${extra[@]}" | json_field id
}

wait_ready() { # id
  for _ in $(seq 1 60); do
    status="$(curl -sf "$API/api/documents/$1/status" | json_field ingestion_status)"
    case "$status" in
      ready) return 0 ;;
      failed) echo "belge $1 failed" >&2; return 1 ;;
    esac
    sleep 2
  done
  echo "belge $1 zaman aşımı" >&2; return 1
}

FACILITY_ID="$(upload "$T0/facility_agreement.pdf" "Facility Agreement" 2023-06-01 2023-06-01)"
echo "Facility Agreement: $FACILITY_ID"
AMENDMENT_ID="$(upload "$T0/amendment_01.pdf" "Amendment 01" 2025-03-15 2025-03-15 "$FACILITY_ID")"
echo "Amendment 01:       $AMENDMENT_ID (supersedes $FACILITY_ID)"
wait_ready "$FACILITY_ID" && wait_ready "$AMENDMENT_ID"
echo "İki belge de ready. Deneyin: $API/ask"
