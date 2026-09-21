#!/usr/bin/env bash
# Waits until the backend answers /health with 200 (default 90 s), then prints the body.
set -euo pipefail

PORT="${BACKEND_PORT:-8000}"
TIMEOUT="${1:-90}"
URL="http://localhost:${PORT}/health"

for ((i = 0; i < TIMEOUT; i++)); do
    if body="$(curl -fsS "$URL" 2>/dev/null)"; then
        echo "backend hazır: $URL -> $body"
        exit 0
    fi
    sleep 1
done

echo "backend ${TIMEOUT} saniye içinde hazır olmadı: $URL" >&2
echo "Loglar için: make logs SVC=backend" >&2
exit 1
