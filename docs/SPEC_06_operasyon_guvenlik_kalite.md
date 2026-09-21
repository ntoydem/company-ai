# SPEC 06 — Operasyon, deployment, güvenlik ve kalite

## 1. Audit log (`audit_log`)
Alanlar: `id, user_id, timestamp, question, query_type, scope_department, scope_project, documents_retrieved (ids), excel_files_used, answer, sources (json), model, tokens_in, tokens_out, cost_estimate, execution_ms, request_id, error`.
Audit log kurumsal hafıza DEĞİLDİR: soru-cevaplar bilgi tabanına girmez, retrieval'da kullanılmaz.
Password/API key/JWT asla loglanmaz. Saklama 90 gün; günlük temizlik job'ı. Admin UI'da filtreli görüntüleme (Phase 14).

## 2. Admin panel (Phase 14)
Kullanıcı ekle/disable/rol; departman izinleri; proje CRUD; metadata düzenleme; belge erişim görünümü ("bu belgeyi kim görebilir"); audit log.

## 3. Deployment
Geliştirme: Proxmox → `company-ai-dev` VM (Ubuntu 24.04, Docker + Compose plugin). Prod: aynı VM'in temiz klonu. Aynı compose, farklı `.env`. Repo kökünde `Makefile`, `README.md`; `infra/docker-compose.yml`, `infra/Caddyfile`, `infra/.env.example`. Başarı: `git clone` → `cp infra/.env.example .env` → `make up` → `make seed`.

## 4. Persistent storage
`DATA_ROOT` env ile: dev `./data`, prod `/srv/company-ai`.
```
$DATA_ROOT/
  postgres/  documents/  excel/  app-data/  backups/
```
Bind mount; container silinmesi veri kaybı yaratmaz. Hepsi NVMe'de; 8 TB HDD yalnızca ikincil backup hedefi.

## 5. Backup
Kapsam: Postgres dump, `documents/`, `excel/`, app-data, `.env` (şifrelenmiş veya ayrı, README'de belirtilir). `scripts/backup.sh` günlük → `/srv/company-ai/backups/YYYY-MM-DD/`, 14 gün rotasyon. Haftalık `BACKUP_SECONDARY_PATH` (8 TB) kopyası; cron saati HDD spindown'dan önce. `scripts/restore.sh` + README'de adım adım restore. Restore testi Phase 15 kabul kriteri.

## 6. Ağ
V0 internete açık değildir. Erişim LAN (ileride Tailscale/WireGuard). Caddy `:8080` HTTP; Postgres, ocr-worker, embed portları host'a açılmaz (yalnızca compose network). Public WAN exposure yok.

## 7. Güvenlik
Argon2; secrets `.env`; `.env` commit edilmez; upload MIME doğrulama; macro çalıştırılmaz; authorization server-side; LLM'e yalnızca izinli içerik; LLM Python çalıştırılmaz; SQL whitelist; rate limit login'de; CORS yalnızca Caddy origin; request id her logda.

## 8. Hata yönetimi
Kullanıcıya Türkçe, teknik detaysız mesaj; backend structured JSON log (level, request_id, user_id, path, error, stack). LLM/ocr-worker/embed servisi düşerse sistem ilgili özelliği "geçici olarak kullanılamıyor" diye bildirir, geri kalan çalışır.

## 9. Kod kalitesi
CLAUDE.md'deki liste. Ek: `ruff` + `mypy` (backend), `eslint` + `tsc` (frontend); `make lint` yeşil olmadan phase kapanmaz. Her servis için birim test; her endpoint için entegrasyon test; test DB ayrı (`company_ai_test`).

## 10. Her phase sonunda
Sistemi çalıştır → testleri çalıştır → hataları düzelt → README/docs güncelle → migration → rapor → PHASES.md durum → commit + tag. Bozuk temel üstüne feature yok.

## 11. Nihai hedef
"ChatGPT'ye şirket PDF'lerini yüklemek" değil: **kurumsal bilginin kaynağını, erişim yetkisini, tarihini, versiyonunu ve ilişkilerini koruyarak AI tarafından güvenilir şekilde kullanılmasını sağlayan bir şirket hafızası.** Her teknik karar bu prensibe göre alınır.
