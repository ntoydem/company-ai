# İş Emri 2026-10-11-D — Adım 2 Raporu (ayrı değerlendirme ortamı)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — canlıya dokunulmadı

## 1. Kurulum

- **Ayrı compose proje adı:** `company-ai-eval` (`docker compose -p company-ai-eval`,
  `COMPOSE_PROJECT_NAME` süreç ortam değişkeni ile — `seed_demo.sh` hiç değiştirilmedi).
- **Ayrı env dosyası:** `infra/.env.eval` (yeni dosya, `.env`'in bir kopyası; `.gitignore`
  `.env.*` deseniyle zaten kapsıyor, commit edilmedi/edilmeyecek). Canlı `.env` **hiç
  düzenlenmedi** — yalnız okunup kopyalandı.
- **Ayrı veri kökü:** `DATA_ROOT=./data-eval` (postgres/documents/excel/app-data/backups
  alt dizinleri) — canlının `./data`'sından tamamen ayrı, aynı host üzerinde farklı yol.
- **Ayrı DB adı:** `POSTGRES_DB=company_ai_eval` (ayrı container+volume olduğu için teknik
  olarak zorunlu değildi ama ek açıklık için).
- **Ayrı port:** `CADDY_PORT=8099` (dosyada tutuldu ama **Caddy hiç başlatılmadı** — eval
  yalnız `postgres`+`backend`+`ocr-worker` kullanıyor; `scripts.run_eval` backend'e
  compose-içi ağdan `http://backend:8000` ile bağlanıyor, host portu gerekmiyor).
- Gemini/Anthropic anahtarları (`LLM_API_KEY`, `PROSE_ANTHROPIC_API_KEY`) `.env`'den
  `infra/.env.eval`'e **değer yazdırılmadan** (`cp`/`sed`, hiç ekrana basılmadan) kopyalandı
  — Adım 4'ün C1'i gerçek Gemini'ye ihtiyaç duyuyor.

## 2. Tohumlama

`COMPOSE_PROJECT_NAME=company-ai-eval ENV_FILE=infra/.env.eval bash scripts/seed_demo.sh`
— script hiç değiştirilmedi (zaten `ENV_FILE` parametrik); proje adı yalnız ortam
değişkeniyle verildi. Sıra: ledger doğrula → 109 belge üret (102 PDF + `seed_data/excel/
manifest.json`'daki 7 workbook otomatik dahil, `ensure_demo_documents`'ın mevcut davranışı)
→ içerik doğrula → admin/demo kullanıcılar/departmanlar/klasörler/projeler → belgeleri
yükle → OCR bitene kadar bekle.

## 3. Sayı doğrulaması

```
wait-for-documents: all ready, count: 109
```

Doğrudan DB sorgusu: **toplam 109 = 102 PDF + 7 xlsx**, tamamı `ready`/`uploaded`.

## 4. Canlı sistem — dokunulmadı, doğrulandı

- Canlı `.env`: hiç yazılmadı (yalnız okunup `infra/.env.eval`'e kopyalandı).
- Canlı backend/postgres/caddy/ocr-worker (`company-ai` projesi): **hâlâ çalışıyor**,
  `/health` ✅. Ayrı proje (`company-ai-eval`) tamamen izole konteynerler/ağ/volume.
- Canlı DB'ye hiçbir yazma/okuma yapılmadı — tüm seed/eval işlemleri `company-ai-eval`
  projesinin kendi Postgres'ine (`company_ai_eval`) gitti.

Devam ediliyor: **Adım 3** (kriter dosyası, sonuçlardan önce).
