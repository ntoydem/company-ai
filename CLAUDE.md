# Company AI V0 — Claude Code Çalışma Kuralları

Bu dosya her oturumda otomatik yüklenir. Kısa tutulmuştur; detaylar `docs/` altındadır.

## Proje
Proxmox üzerinde tek bir Linux VM'de Docker Compose ile çalışan kurumsal doküman + Excel + AI bilgi platformu (V0/MVP).
Hedef: kurumsal bilginin **kaynağını, erişim yetkisini, tarihini, versiyonunu ve ilişkilerini** koruyarak AI tarafından güvenilir kullanılmasını sağlayan bir şirket hafızası. Basit bir chatbot DEĞİLDİR.

Okuma sırası: `docs/PHASES.md` (6 adım / phase planı + kabul kriterleri) → ilgili `docs/SPEC_0x_*.md` → `docs/ARCHITECTURE.md` (ADR'ler) → `docs/DOMAIN_MODEL.md`.

## Dil
- Son kullanıcı arayüzü, hata mesajları, README: **Türkçe** (locale tr-TR, tarih DD.MM.YYYY).
- Kod, yorumlar, commit mesajları, ADR'ler, API, DB şeması: **İngilizce**.
- AI cevapları varsayılan Türkçe; kullanıcı başka dilde sorarsa o dilde.

## Stack — KARAR VERİLMİŞTİR, değiştirme, alternatif önerme
- Backend: Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, pytest
- DB: PostgreSQL 16 + pgvector (tek container, database `company_ai`; pgvector extension)
- Doküman depolama: dosyalar diskte (`$DATA_ROOT/documents/<uuid>/original.pdf`, `ocr.pdf`), metadata Postgres'te. Paperless YOK.
- OCR/metin: ayrı `ocr-worker` container'ı — `ocrmypdf` (`--language tur+eng --skip-text --rotate-pages --deskew`) → metin katmanlı PDF; sayfa bazlı metin `PyMuPDF` ile. Kuyruk: Postgres tablosu (`ingestion_jobs`), worker polling; Redis/Valkey YOK.
- Arka plan işleri: FastAPI BackgroundTasks + `ingestion_jobs` tablosu.
- Frontend: Vite + React 18 + TypeScript + react-router + TanStack Query. Next.js YOK.
- Reverse proxy: Caddy. V0'da LAN üzerinde düz HTTP.
- Excel: openpyxl (inspection), DuckDB (hesap), Polars (dönüşüm). LLM matematik yapmaz.
- LLM: tek OpenAI-uyumlu istemci (`openai` SDK + `base_url`); varsayılan Gemini. Opsiyonel Anthropic istemcisi. İki ayrı model değişkeni: `LLM_MODEL_CLASSIFY`, `LLM_MODEL_ANSWER`.
- Embedding: bge-m3, ayrı `embed` servisi, `EMBEDDINGS_ENABLED=false/true` bayrağı. Bayrak kapalıyken sistem yalnızca full-text + metadata ile çalışır ve ÇALIŞMALIDIR.
- Sayfa bazlı kaynak V0'da VAR: `document_chunks.page_number` dolu; kaynak kartı sayfa gösterir.
- Demo belge üretimi: Markdown/HTML şablon + WeasyPrint → PDF. Excel üretimi: openpyxl + tek seferlik LibreOffice headless recalc (build adımı, runtime servisi değil).
- Auth: JWT (httpOnly cookie, 8 saat), Argon2 (argon2-cffi). Refresh token yok.
- Paperless, Tika, Gotenberg, Valkey/Redis, Qdrant, Kubernetes, LangChain/LlamaIndex: YOK.

## V0 kapsamı dışında (implement ETME, sorma)
E-mail / Microsoft Graph / Gmail, SharePoint/OneDrive, SAP/ERP, Kubernetes, Qdrant, lokal LLM, GPU, autonomous agent/agent swarm, native mobil, BI, SSO/Entra ID (yalnızca `auth_provider`/`external_id` alanları hazır durur), HTTPS/Tailscale (V0 sonrası), consume klasörü / klasör izleme, Word/e-posta ingest, LLM'in yazdığı Python'ı çalıştırma, Playwright/UI testleri, Grafana/Prometheus.

## Beş değişmez kural
1. **SECURITY** — Yetkisiz belge içeriği LLM promptuna dahi girmez. Sıra: AUTHORIZATION → allowed documents → retrieval → LLM.
2. **SOURCE GROUNDING** — Şirket bilgisi kaynak olmadan üretilmez. Kaynak yoksa: "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım."
3. **CALCULATION** — Excel matematiğini LLM değil DuckDB/Python yapar. LLM ne hesaplanacağını belirler ve sonucu yorumlar.
4. **AUDITABILITY** — Her cevabın kaynağı (belge/sayfa/tarih/versiyon/proje veya dosya/sheet/range) kullanıcıya gösterilir ve audit log'a yazılır.
5. **TEMPORAL TRUTH** — Eski değer ≠ yanlış değer. Tarih, versiyon, effective_date ve supersedes ilişkisi kullanılır; "güncel" ile "ilk/tarihsel" ayrılır.
6. **NO OPINION (V0)** — Sistem bulur, okur, aktarır; yorum/görüş/projeksiyon üretmez. "Neden?" sorularına yalnızca belgede yazan sebep aktarılır; yoksa "belgelerde sebep belirtilmemiş" denir.

## Yetkinin yeri (Adım 0'dan itibaren)
`app/services/authorization.py` içinde tek fonksiyon: `allowed_document_ids(user, scope) -> set[UUID]`. Retrieval, belge listesi, belge indirme ve `/api/ask` bu fonksiyondan geçmeden hiçbir belgeye dokunmaz. Adım 0'da fonksiyon "tüm belgeler" döndürür (tek admin kullanıcı); Adım 1'de doldurulur. Fonksiyonu atlayan bir kod yolu yazmak yasaktır. `documents` tablosunda `department`, `project_id`, `confidentiality` alanları Adım 0'dan itibaren vardır (Adım 0'da varsayılan değerlerle).

## Audit log ≠ kurumsal hafıza
Audit log = kim, ne zaman, ne sordu, hangi kaynaklar kullanıldı; yalnızca admin görür; 90 gün. Kurumsal hafıza = belgeler ve bilinçli eklenen notlar. Soru-cevaplar bilgi tabanına GİRMEZ; kullanıcının sorusu başka bir kullanıcının cevabını etkilemez.

## Çalışma biçimi
1. Oturum başında `docs/PHASES.md`'yi oku, hangi adım/phase'de olduğumuzu `## Durum` tablosundan gör. **Bir oturumda bir phase.** Adımlar (0–5) Naci'nin takip birimi, phase'ler (0.1, 0.2 …) senin çalışma birimin.
2. Kod yazmadan önce plan yaz (plan modu): dosyalar, tablolar, endpoint'ler, alınacak kararlar. Naci onaylamadan implementasyona geçme.
3. Spec'te olmayan **ürün/mimari** kararını tahmin etme: `SORU:` ile sor ve bekle. Küçük teknik detayları (isimlendirme, dosya bölme) kendin karar ver, raporda listele.
4. Üçüncü taraf davranışından emin değilsen (ocrmypdf CLI, PyMuPDF, Gemini OpenAI-uyumlu endpoint, pgvector, DuckDB, WeasyPrint) resmi dokümana bak. **Olmayan API/parametre üretme.**
5. Phase sonunda sırayla: tüm testler yeşil → README ve ilgili docs güncel → migration oluşturulmuş → `docs/reports/PHASE_NN_REPORT.md` yazılmış (şablon `docs/reports/TEMPLATE.md`) → `docs/PHASES.md` durum tablosu güncellenmiş → `git commit` + `git tag phase-A-B` (örn. `phase-0-2`).
6. Kırmızı test varken ilerleme; bozuk temel üstüne feature ekleme.
7. Kabul kriterlerini kelimesi kelimesine test et. "Çalışıyor gibi görünüyor" kabul değildir.
8. `docs/ARCHITECTURE.md` bir ADR listesidir (kısa kararlar + gerekçe), tasarım romanı değil. Yeni mimari karar aldığında ADR ekle.

## Kod kalitesi
İstenen: clean architecture (api / services / repositories / models), type hints, Pydantic v2 şemaları, structured JSON logging, küçük modüller, testable services, Alembic migrations, her endpoint için en az bir test.
İstenmeyen: 400+ satırlık dosyalar, kopyala-yapıştır, framework soup, premature abstraction, "ileride lazım olur" diye eklenen soyutlamalar.

## Güvenlik kısayolları YASAK
- Yetki kontrolü yalnızca frontend'de → yasak; her endpoint server-side authorize eder.
- Secrets `.env`'den gelir; koda, loga, test fixture'a gerçek key yazılmaz. Password/API key loglanmaz.
- `.xlsm` macro çalıştırılmaz. LLM'in ürettiği Python çalıştırılmaz; yalnızca predefined fonksiyonlar + read-only DuckDB SQL.
- Upload'da MIME/type doğrulaması yapılır. Kullanıcı stack trace görmez.

## Geliştirme ortamı (KARAR)
- Geliştirme: Proxmox üzerindeki `company-ai-dev` VM'inde (Ubuntu 24.04, Docker + Compose plugin). Naci PC'den SSH ile bağlanır; Claude Code bu VM'de çalışır. Repo `~/company-ai`.
- Prod: aynı VM'in Phase 16'da alınan temiz klonu (`company-ai-prod`); orada yalnızca `git clone` + `.env` + `make up`.
- Bu yüzden: veri kökü `DATA_ROOT` env değişkeni (dev: `./data`, prod: `/srv/company-ai`); compose'da sabit `/srv/...` yolu yazma. Tüm script'ler `bash`, LF satır sonu. Host'a özel ayar yok; dev'de çalışan prod'da da çalışmalı.
- RAM: dev VM 16 GB. Temel servisler (postgres, backend, ocr-worker, caddy) 6 GB'a sığar. `embed` servisi `--profile full` altında; Adım 0 boyunca açılmaz, Phase 3.4'te `make up-full`.
- Tüm host portları `.env`'den (`CADDY_PORT=8080`).

## Repo düzeni
```
backend/      FastAPI (app/api, app/services, app/repositories, app/models, app/schemas, app/core, app/excel), tests/, alembic/
ocr-worker/   ocrmypdf + PyMuPDF worker (ingestion_jobs tablosunu poll eder)
frontend/     Vite + React + TS
infra/        docker-compose.yml, Caddyfile, .env.example, ocr-worker/Dockerfile
seed_data/    master/ (YAML truth ledger), generator/, documents/, excel/, evaluation/
scripts/      seed_demo.sh, reset_demo.sh, backup.sh, restore.sh, run_eval.py, wait_for_services.sh
docs/         SPEC_0x_*.md, PHASES.md, ARCHITECTURE.md, DOMAIN_MODEL.md, reports/, prompts/
Makefile      up, down, logs, test, eval, seed, reset-demo, backup, restore, lint
```

## Demo sabitleri
- İki demo proje: **Ankara RES** (işletmede, 2026'da 3. işletme yılı) ve **İzmir RES** (development, ÇED tamamlanmamış). İkisi ASLA karıştırılmaz.
- `DEMO_TODAY=15.09.2026` — "güncel", "şu anda", "kaçıncı yıl" hesapları bu tarihe göre, gerçek takvime göre değil.
- Rakamlar (kapasite, capex, kredi tutarları, tarihler) yalnızca `seed_data/master/*.yaml` truth ledger'dan gelir. Ledger'da olmayan rakamı UYDURMA; `SORU:` ile sor.
