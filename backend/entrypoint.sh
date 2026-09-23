#!/usr/bin/env bash
# Backend container entrypoint.
#   no arguments  -> wait for DB -> migrate -> seed admin -> seed demo users/departments/projects -> serve (compose `up`)
#   with arguments -> run them (compose `run backend pytest`, `alembic ...`, `bash`)
set -euo pipefail
cd /app

if [ "$#" -gt 0 ]; then
    exec "$@"
fi

python -m app.cli wait-for-db --timeout 60
alembic upgrade head
python -m app.cli seed-admin
python -m app.cli seed-demo-users
python -m app.cli seed-demo-departments
python -m app.cli seed-demo-projects

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log --log-level warning
