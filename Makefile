# Company AI V0 — all commands run inside docker compose; the host needs only Docker, make, curl.
SHELL := /bin/bash
.DEFAULT_GOAL := help

ENV_FILE ?= .env
COMPOSE  := docker compose --project-directory . -f infra/docker-compose.yml --env-file $(ENV_FILE)
DATA_ROOT := $(shell grep -E '^DATA_ROOT=' $(ENV_FILE) 2>/dev/null | cut -d= -f2- | tr -d '"')
DATA_ROOT := $(or $(DATA_ROOT),./data)
BACKEND_PORT := $(shell grep -E '^BACKEND_PORT=' $(ENV_FILE) 2>/dev/null | cut -d= -f2-)
BACKEND_PORT := $(or $(BACKEND_PORT),8000)
SVC ?=

.PHONY: help env-check dirs up up-full down ps logs build test test-llm lint format prompt-doc validate-ledger \
        migrate migration seed-admin seed-demo-users seed-demo-departments seed-demo-projects \
        prose validate-documents seed-demo-documents \
        psql shell seed reset-demo eval backup restore clean

help: ## Bu listeyi göster
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

env-check:
	@test -f $(ENV_FILE) || { echo "$(ENV_FILE) yok. Önce: cp infra/.env.example .env"; exit 1; }

dirs: env-check
	@mkdir -p "$(DATA_ROOT)/postgres" "$(DATA_ROOT)/documents" "$(DATA_ROOT)/excel" \
	          "$(DATA_ROOT)/app-data" "$(DATA_ROOT)/backups"

up: dirs ## postgres + backend + ocr-worker'ı başlat (build dahil) ve /health bekle
	$(COMPOSE) up -d --build postgres backend ocr-worker
	BACKEND_PORT=$(BACKEND_PORT) bash scripts/wait_for_services.sh 120

up-full: dirs ## full profil (embed dahil; 16 GB VM)
	$(COMPOSE) --profile full up -d --build
	BACKEND_PORT=$(BACKEND_PORT) bash scripts/wait_for_services.sh 120

down: env-check ## container'ları durdur (veri kalır)
	$(COMPOSE) --profile full --profile web down

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

lint: env-check ## ruff + mypy (backend), ruff (ocr-worker), prompt dokümanı güncel mi
	$(COMPOSE) run --rm -T --no-deps backend sh -c 'ruff check . && ruff format --check . && mypy'
	$(COMPOSE) run --rm -T --no-deps ocr-worker sh -c 'ruff check . && ruff format --check .'
	@$(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-answer-prompt 2>/dev/null \
		| diff -q - <(sed -n '/^```text$$/,/^```$$/{//!p}' docs/prompts/ANSWER_SYSTEM_PROMPT.md) >/dev/null \
		|| { echo "docs/prompts/ANSWER_SYSTEM_PROMPT.md güncel değil: make prompt-doc"; exit 1; }
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_ledger
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_documents --prose-only

validate-ledger: env-check ## truth ledger + questions.json doğrulaması (0 hata = exit 0)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_ledger --summary

prose: env-check ## demo belge prose'unu LLM ile üret (BİR KEZ; çıktı commit edilir, `make seed` LLM çağırmaz)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.generate_prose

validate-documents: env-check ## üretilen 15 demo belgenin içeriğini doğrula (banner/isim/izolasyon/facts)
	$(COMPOSE) run --rm -T --no-deps backend python -m seed_data.generator.validate_documents

prompt-doc: env-check ## /api/ask sistem promptunu docs/prompts/ANSWER_SYSTEM_PROMPT.md'ye yaz
	@{ printf '%s\n\n' '# Cevap sistem promptu (Phase 0.3)'; \
	   printf '%s\n\n' 'Kaynak: `backend/app/services/answer_prompt.py::SYSTEM_PROMPT`. Bu dosya yalnızca gözden geçirme kopyasıdır; `make lint` ikisinin aynı olduğunu doğrular. Değişiklik Python sabitinde yapılır, sonra `make prompt-doc` çalıştırılır.'; \
	   echo '```text'; $(COMPOSE) run --rm -T --no-deps backend python -m app.cli print-answer-prompt 2>/dev/null; echo '```'; } \
	   > docs/prompts/ANSWER_SYSTEM_PROMPT.md && echo "yazıldı: docs/prompts/ANSWER_SYSTEM_PROMPT.md"

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
eval: ## eval runner (Phase 4.1)
	@echo "Henüz uygulanmadı (Phase 4.1)."; exit 1
backup: ## yedek (Phase 5.3)
	@echo "Henüz uygulanmadı (Phase 5.3)."; exit 1
restore: ## geri yükleme (Phase 5.3)
	@echo "Henüz uygulanmadı (Phase 5.3)."; exit 1

clean: env-check ## container + image sil; DATA_ROOT'a dokunmaz
	$(COMPOSE) --profile full --profile web down --rmi local --remove-orphans
