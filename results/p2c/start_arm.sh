#!/usr/bin/env bash
# P2C: (re)start the EVAL backend with /app from one arm worktree; logs to results/p2c/<arm>/backend.log
set -euo pipefail
ARM=$1; SRC=$2   # e.g. base /home/naci/company-ai-arms/base
EC="docker compose -p company-ai-eval --project-directory . -f infra/docker-compose.yml --env-file infra/.env.eval"
docker rm -f company-ai-eval-backend-1 >/dev/null 2>&1 || true
$EC run -d --use-aliases --name company-ai-eval-backend-1 -v "$SRC/backend:/app" \
  -e LLM_PROVIDER=anthropic -e LLM_MODEL_CLASSIFY=claude-haiku-5-5 -e LLM_MODEL_ANSWER=claude-haiku-5-5 \
  -e LLM_MODEL_EXCEL_PLAN=claude-sonnet-5-5 -e ANTHROPIC_THINKING=false -e ANSWER_THINKING=true \
  -e ANSWER_THINKING_MAX_TOKENS=8192 -e EK_F_MODE=true -e ASSIST_MODE=false backend >/dev/null
mkdir -p "results/p2c/$ARM"
nohup docker logs -f company-ai-eval-backend-1 >> "results/p2c/$ARM/backend.log" 2>&1 &
for i in $(seq 1 60); do
  [ "$(docker inspect company-ai-eval-backend-1 --format '{{.State.Health.Status}}')" = healthy ] && break; sleep 2
done
docker inspect company-ai-eval-backend-1 --format '{{.State.Health.Status}} {{.State.StartedAt}}'
