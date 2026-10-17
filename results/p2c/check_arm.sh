#!/usr/bin/env bash
# P2C: what the eval backend runs — /app mount source, fingerprints, settings; and the live fingerprint
docker inspect company-ai-eval-backend-1 --format '{{range .Mounts}}{{if eq .Destination "/app"}}/app <- {{.Source}}{{end}}{{end}}'
docker exec company-ai-eval-backend-1 sh -c '
  printf "router repayment-schedule-row: %s\n" $(grep -c "repayment schedule row" app/services/router.py)
  printf "plan use-a-superseded-one:     %s\n" $(grep -c "use a superseded one" app/services/excel_ask.py)
  printf "def _workbook_line:            %s\n" $(grep -c "def _workbook_line" app/services/excel_ask.py)
  printf "def split_footer:              %s\n" $(grep -c "def split_footer" app/excel/calc.py)
  printf "P2C plan log patch:            %s\n" $(grep -c "P2C measure only" app/services/excel_ask.py)'
docker exec -i company-ai-eval-backend-1 python - <<'PY'
from app.core.config import get_settings
s = get_settings()
print("settings:", s.llm_provider, s.llm_model_classify, s.llm_model_answer, s.llm_model_excel_plan,
      "anth_think", s.anthropic_thinking, "ans_think", s.answer_thinking, s.answer_thinking_max_tokens,
      "ek_f", s.ek_f_enabled, "assist", s.assist_mode_enabled, "demo_today", s.demo_today,
      "db", s.database_url.rsplit("/", 1)[-1])
PY
echo "live backend StartedAt: $(docker inspect company-ai-backend-1 --format '{{.State.StartedAt}}')"
echo "live HEAD: $(git rev-parse --short HEAD)"
