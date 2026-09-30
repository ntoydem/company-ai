# Company AI V0 — all commands run inside docker compose; the host needs only Docker, make, curl.
SHELL := /bin/bash
.DEFAULT_GOAL := help

ENV_FILE ?= .env
COMPOSE  := docker compose --project-directory . -f infra/docker-compose.yml --env-file $(ENV_FILE)
DATA_ROOT := $(shell grep -E '^DATA_ROOT=' $(ENV_FILE) 2>/dev/null | cut -d= -f2- | tr -d '"')
DATA_ROOT := $(or $(DATA_ROOT),./data)
BACKEND_PORT := $(shell grep -E '^BACKEND_PORT=' $(ENV_FILE) 2>/dev/null | cut -d= -f2-)
BACKEND_PORT := $(or $(BACKEND_PORT),8000)
CADDY_PORT := $(shell grep -E '^CADDY_PORT=' $(ENV_FILE) 2>/dev/null | cut -d= -f2-)
CADDY_PORT := $(or $(CADDY_PORT),8080)
SVC ?=
EVAL_ARGS ?=

.PHONY: help env-check dirs up up-full down ps logs build test test-llm lint format prompt-doc validate-ledger \
        migrate migration seed-admin seed-demo-users seed-demo-departments seed-demo-projects \
        prose validate-documents seed-demo-documents build-frontend dev-frontend excel validate-excel \
        psql shell seed reset-demo eval backup restore clean

help: ## Bu listeyi göster
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env-check:
	@test -f $(ENV_FILE) || { echo "$(ENV_FILE) yok. Önce: cp infra/.env.example .env"; exit 1; }

dirs: env-check
	@mkdir -p "$(DATA_ROOT)/postgres" "$(DATA_ROOT)/documents" "$(DATA_ROOT)/excel" \
	          "$(DATA_ROOT)/app-data" "$(DATA_ROOT)/backups"

up: dirs ## postgres + backend + ocr-worker + caddy'yi başlat (build dahil); arayüz http://<vm-ip>:$(CADDY_PORT)
	$(COMPOSE) up -d --build postgres backend ocr-worker caddy
	CADDY_PORT=$(CADDY_PORT) bash scripts/wait_for_services.sh 120

up-full: dirs ## full profil (embed dahil; 16 GB VM)
	$(COMPOSE) --profile full up -d --build
	CADDY_PORT=$(CADDY_PORT) bash scripts/wait_for_services.sh 120

down: env-check ## container'ları durdur (veri kalır)
	$(COMPOSE) --profile full --profile tools down

ps: env-check ## servis durumu
	$(COMPOSE) ps -a

logs: env-check ## logları izle (make logs SVC=backend)
	$(COMPOSE) logs -f --tail=200 $(SVC)

build: env-check ## image'ları build et
	$(COMPOSE) build

test: dirs ## pytest: backend, sonra şema doğrulaması, sonra ocr-worker. make test ARGS="-k health"
	$(COMPOSE) run --rm -T backend \
		sh -c 'export DATABASE_URL="$$TEST_DATABASE_URL"; python -m app.cli wait-for-db --timeout 60 && pytest -q $(ARGS)'
	$(COMPOSE) run --rm -T backend \
		sh -c 'export DATABASE_URL="$$TEST_DATABASE_URL"; python -m app.cli assert-pipeline-schema'
	$(COMPOSE) run --rm -T ocr-worker \
		sh -c 'export DATABASE_URL="$$TEST_DATABASE_URL"; pytest -q $(ARGS)'

test-llm: dirs ## canlı LLM testleri (gerçek Gemini; LLM_API_KEY gerekir). make test-llm MODEL=gemini-3.5-flash
	$(COMPOSE) run --rm -T -e LLM_LIVE_TESTS=1 $(if $(MODEL),-e LLM_MODEL_ANSWER=$(MODEL)) backend \
		sh -c 'export DATABASE_URL="$$TEST_DATABASE_URL"; python -m app.cli wait-for-db --timeout 60 && pytest -q -s -m live_llm tests/live $(ARGS)'

build-frontend: env-check ## React bundle'ı içeren caddy imajını yeniden derle (make up zaten yapar)
	$(COMPOSE) build caddy

dev-frontend: env-check ## Vite dev server (HMR) http://<vm-ip>:5173 — /api backend'e proxy'lenir; make up çalışıyor olmalı
	$(COMPOSE) --profile tools run --rm --service-ports frontend npm run dev -- --host

lint: env-check ## ruff + mypy (backend), ruff (ocr-worker), eslint + tsc (frontend), prompt dokümanı güncel mi
	$(COMPOSE) run --rm -T --no-deps backend sh -c 'ruff check . && ruff format --check . && mypy'
	$(COMPOSE) run --rm -T --no-deps ocr-worker sh -c 'ruff check . && ruff format --check .'
	$(COMPOSE) --profile tools run --rm -T --no-deps frontend sh -c 'npm run lint && npm run typecheck'
	@$(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-answer-prompt 2>/dev/null \
		| diff -q - <(sed -n '/^```text$$/,/^```$$/{//!p}' docs/prompts/ANSWER_SYSTEM_PROMPT.md) >/dev/null \
		|| { echo "docs/prompts/ANSWER_SYSTEM_PROMPT.md güncel değil: make prompt-doc"; exit 1; }
	@$(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-excel-prompts 2>/dev/null \
		| diff -q - <(sed -n '/^```text$$/,/^```$$/{//!p}' docs/prompts/EXCEL_PROMPTS.md) >/dev/null \
		|| { echo "docs/prompts/EXCEL_PROMPTS.md güncel değil: make prompt-doc"; exit 1; }
	@$(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-router-prompts 2>/dev/null \
		| diff -q - <(sed -n '/^```text$$/,/^```$$/{//!p}' docs/prompts/ROUTER_PROMPTS.md) >/dev/null \
		|| { echo "docs/prompts/ROUTER_PROMPTS.md güncel değil: make prompt-doc"; exit 1; }
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_ledger
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_documents --prose-only
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_excel

validate-ledger: env-check ## truth ledger + questions.json doğrulaması (0 hata = exit 0)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_ledger --summary

prose: env-check ## demo belge prose'unu LLM ile üret (BİR KEZ; çıktı commit edilir, `make seed` LLM çağırmaz)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.generate_prose

excel: env-check ## 4 demo workbook'u ledger'dan üret + LibreOffice recalc (tools profili) + doğrula; çıktı commit edilir
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.generate_excel
	$(COMPOSE) --profile tools run --rm -T libreoffice
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_excel

validate-excel: env-check ## commit'li workbook'ları doğrula (cached değerler, named range'ler, ledger tutarlılığı)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_excel

validate-documents: env-check ## üretilen 15 demo belgenin içeriğini doğrula (banner/isim/izolasyon/facts)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_documents

prompt-doc: env-check ## /api/ask sistem promptunu docs/prompts/ANSWER_SYSTEM_PROMPT.md'ye yaz
	@{ printf '%s\n\n' '# Cevap sistem promptu (Phase 0.3)'; \
	   printf '%s\n\n' 'Kaynak: `backend/app/services/answer_prompt.py::SYSTEM_PROMPT`. Bu dosya yalnızca gözden geçirme kopyasıdır; `make lint` ikisinin aynı olduğunu doğrular. Değişiklik Python sabitinde yapılır, sonra `make prompt-doc` çalıştırılır.'; \
	   echo '```text'; $(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-answer-prompt 2>/dev/null; echo '```'; } \
	   > docs/prompts/ANSWER_SYSTEM_PROMPT.md && echo "yazıldı: docs/prompts/ANSWER_SYSTEM_PROMPT.md"
	@{ printf '%s\n\n' '# Excel plan + cevap promptları (Phase 4.2)'; \
	   printf '%s\n\n' 'Kaynak: `backend/app/services/excel_ask.py::PLAN_SYSTEM_PROMPT` ve `ANSWER_SYSTEM_PROMPT`. Gözden geçirme kopyası; `make lint` eşitliği denetler, değişiklik Python sabitinde yapılır.'; \
	   echo '```text'; $(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-excel-prompts 2>/dev/null; echo '```'; } \
	   > docs/prompts/EXCEL_PROMPTS.md && echo "yazıldı: docs/prompts/EXCEL_PROMPTS.md"
	@{ printf '%s\n\n' '# Router promptu (Phase 4.3)'; \
	   printf '%s\n\n' 'Kaynak: `backend/app/services/router.py::ROUTER_SYSTEM_PROMPT`. Gözden geçirme kopyası; `make lint` eşitliği denetler, değişiklik Python sabitinde yapılır. GENERAL promptu (`general_answer.py`) 30.09.2026'"'"'da GENERAL_QUERY ile birlikte kaldırıldı.'; \
	   echo '```text'; $(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-router-prompts 2>/dev/null; echo '```'; } \
	   > docs/prompts/ROUTER_PROMPTS.md && echo "yazıldı: docs/prompts/ROUTER_PROMPTS.md"

format: env-check ## ruff format + autofix (backend + ocr-worker)
	$(COMPOSE) run --rm -T --no-deps backend sh -c 'ruff format . && ruff check --fix .'
	$(COMPOSE) run --rm -T --no-deps ocr-worker sh -c 'ruff format . && ruff check --fix .'

migrate: dirs ## alembic upgrade head
	$(COMPOSE) run --rm -T backend alembic upgrade head

migration: dirs ## yeni migration üret: make migration NAME=add_documents
	@test -n "$(NAME)" || { echo "NAME=... gerekli"; exit 1; }
	$(COMPOSE) run --rm -T backend alembic revision --autogenerate -m "$(NAME)"

seed-admin: dirs ## admin kullanıcısını oluştur (yoksa)
	$(COMPOSE) run --rm -T backend python -m app.cli seed-admin

seed-demo-users: dirs ## demo kullanıcılarını oluştur (yoksa): yonetim, finans, hukuk, enerji
	$(COMPOSE) run --rm -T backend python -m app.cli seed-demo-users

seed-demo-departments: dirs ## demo departmanlarını + demo kullanıcı üyeliklerini oluştur (yoksa)
	$(COMPOSE) run --rm -T backend python -m app.cli seed-demo-departments

seed-demo-projects: dirs ## demo projelerini oluştur (yoksa): Ankara RES, İzmir RES
	$(COMPOSE) run --rm -T backend python -m app.cli seed-demo-projects

seed-demo-documents: dirs ## demo belgelerini yükle (yoksa; önce `make seed` içindeki generate/validate adımları)
	$(COMPOSE) run --rm -T backend python -m app.cli seed-demo-documents
	$(COMPOSE) run --rm -T backend python -m app.cli wait-for-documents --timeout 600

psql: env-check ## postgres'e psql ile bağlan
	$(COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"'

shell: env-check ## backend container'ında bash
	$(COMPOSE) run --rm backend bash

seed: dirs ## demo veri: ledger doğrula -> belge üret -> doğrula -> kullanıcı/departman/proje -> belge yükle -> ready bekle
	bash scripts/seed_demo.sh
reset-demo: dirs ## demo belgelerini sıfırla (yalnızca belgeler; kullanıcı/departman/proje korunur)
	bash scripts/reset_demo.sh
eval: dirs ## eval runner: questions.json -> /api/ask -> skor. make eval MODEL=gemini-3.5-flash
	$(if $(MODEL),LLM_MODEL_ANSWER=$(MODEL)) $(COMPOSE) up -d --wait --build backend
	@$(COMPOSE) run --rm -T backend python -m scripts.run_eval $(EVAL_ARGS); status=$$?; \
	echo "== backend .env'deki LLM_MODEL_ANSWER'a geri alınıyor =="; \
	$(COMPOSE) up -d --wait --build backend >/dev/null; \
	exit $$status
backup: dirs ## yedek al: postgres dump + documents/excel/app-data + .env (ayrı dosya). make backup ARGS="--sync-secondary"
	bash scripts/backup.sh $(ARGS)
restore: dirs ## yedekten geri yükle (YIKICI). make restore ARGS="2026-09-26" (veya ARGS="<yol> --yes")
	@test -n "$(ARGS)" || { echo "ARGS=<tarih|yol> gerekli, örn: make restore ARGS=2026-09-26"; exit 1; }
	bash scripts/restore.sh $(ARGS)

clean: env-check ## container + image sil; DATA_ROOT'a dokunmaz
	$(COMPOSE) --profile full --profile web down --rmi local --remove-orphans
