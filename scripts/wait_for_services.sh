#!/usr/bin/env bash
# Waits until /health answers 200 through Caddy (default 90 s), then prints the body.
# Since Phase 3.3 the backend has no host port (ADR-018); Caddy proxies /health.
set -euo pipefail

PORT="${CADDY_PORT:-8080}"
TIMEOUT="${1:-90}"
URL="http://localhost:${PORT}/health"

for ((i = 0; i < TIMEOUT; i++)); do
    if body="$(curl -fsS "$URL" 2>/dev/null)"; then
        echo "hazır: $URL -> $body"
        echo "arayüz: http://<vm-ip>:${PORT}"
        exit 0
    fi
    sleep 1
done

echo "servisler ${TIMEOUT} saniye içinde hazır olmadı: $URL" >&2
echo "Loglar için: make logs SVC=backend  /  make logs SVC=caddy" >&2
exit 1
