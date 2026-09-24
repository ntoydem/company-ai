# PHASES — Company AI V0

Altı **adım** (Naci'nin takip birimi) ve altlarında **phase**'ler (Claude Code'un çalışma birimi: bir oturum = bir phase). Sıra değiştirilmez; bir phase'in kabul kriterleri (Abnahmekriterien) sağlanmadan sonraki phase'e geçilmez.
Model: `O` = Opus, `S` = Sonnet. RAM: aksi yazılmadıkça 16 GB VM yeter.
Adım 0 ve Adım 4 sonunda Naci "devam mı" kararı verir.

## Durum
| Phase | Ad | Durum | Tag | Rapor |
|---|---|---|---|---|
| 0.1 | İskelet + ADR'ler | tamamlandı | phase-0-1 | [PHASE_0_1_REPORT](reports/PHASE_0_1_REPORT.md) |
| 0.2 | Belge hattı (upload → OCR → sayfa → chunk → FTS) | tamamlandı | phase-0-2 | [PHASE_0_2_REPORT](reports/PHASE_0_2_REPORT.md) |
| 0.3 | LLM + soru-cevap + sayfa kaynaklı cevap (T0) | tamamlandı | phase-0-3 | [PHASE_0_3_REPORT](reports/PHASE_0_3_REPORT.md) |
| 1.1 | Auth + kullanıcılar | tamamlandı | phase-1-1 | [PHASE_1_1_REPORT](reports/PHASE_1_1_REPORT.md) |
| 1.2 | Departman, rol, proje, yetki | tamamlandı | phase-1-2 | [PHASE_1_2_REPORT](reports/PHASE_1_2_REPORT.md) |
| 2.1 | Truth ledger + validator + golden questions v1 | tamamlandı (ledger onaylandı 23.09.2026) | phase-2-1 | [PHASE_2_1_REPORT](reports/PHASE_2_1_REPORT.md) |
| 3.1 | 15 demo belge + seed/reset | tamamlandı | phase-3-1 | [PHASE_3_1_REPORT](reports/PHASE_3_1_REPORT.md) |
| 3.2 | AI metadata önerisi + temporal/versiyon mantığı | tamamlandı | phase-3-2 | [PHASE_3_2_REPORT](reports/PHASE_3_2_REPORT.md) |
| 3.3 | Frontend | tamamlandı | phase-3-3 | [PHASE_3_3_REPORT](reports/PHASE_3_3_REPORT.md) |
| 3.4 | Audit log + embedding (opsiyonel) | bekliyor | – | – |
| 4.1 | Eval runner (karne) | bekliyor | – | – |
| 4.2 | Excel motoru | bekliyor | – | – |
| 4.3 | Mixed query | bekliyor | – | – |
| 5.1 | Tam dataset (~70) + consistency checks | bekliyor | – | – |
| 5.2 | Admin panel | bekliyor | – | – |
| 5.3 | Backup / restore | bekliyor | – | – |
| 5.4 | Temiz kurulum doğrulaması + README final | bekliyor | – | – |

Durum değerleri: bekliyor / planlandı / devam / tamamlandı.

---

# ADIM 0 — T0: Çekirdek testi
Tanım: Şirket belgelerinden kaynak göstererek doğru cevap alınabildiğinin en küçük ölçekte kanıtı. Tek admin kullanıcı; yetki fonksiyonu var ama "hepsine izinli".

## Phase 0.1 — İskelet + ADR'ler `O`
**Kapsam:** Repo düzeni, `.gitignore`, `.gitattributes` (LF), `Makefile`, `infra/.env.example`, `docker-compose.yml` (postgres + backend aktif; ocr-worker, caddy, embed yer tutucu/profil). Backend: FastAPI, `/health`, pydantic-settings, structured logging, Alembic init, pytest. Tek admin kullanıcı seed (`admin`, şifre `.env`). `docs/ARCHITECTURE.md` ADR listesi (≥ 10, her biri ≤ 15 satır): topoloji, auth, yetki modeli ve `allowed_document_ids` sözleşmesi, depolama (`DocumentStore`), ingestion hattı ve `ingestion_jobs` kuyruğu, retrieval (FTS + metadata, embedding bayraklı), sayfa bazlı kaynak, router, Excel sınırları, temporal model, synthetic truth modeli, "yorum yok" kuralı, güvenlik sınırları. `docs/DOMAIN_MODEL.md` iskeleti (rakamsız).
**Kabul kriterleri:**
1. `make up` → postgres + backend; `curl localhost:8000/health` → 200.
2. `make test` ≥ 1 test geçer; `make lint` yeşil; `alembic upgrade head` boş DB'de hatasız.
3. ARCHITECTURE.md ≥ 10 ADR; secret yok; `DATA_ROOT=./data` ile çalışır.

## Phase 0.2 — Belge hattı `S`
**Kapsam:** `documents`, `document_pages`, `document_chunks`, `ingestion_jobs` tabloları (SPEC_02 alanları; department/project/confidentiality varsayılan değerle). `POST /api/documents/upload` (pdf/png/jpg, MIME doğrulama). `ocr-worker` container'ı: ocrmypdf + PyMuPDF, job polling, retry 3, hata kaydı. Chunking (~800 token, 100 overlap, sayfa sınırı korunur), Postgres FTS (`turkish` + `simple`). `GET /api/documents`, `GET /api/documents/{id}/status`. `allowed_document_ids()` stub'ı: tüm belgeler. Retrieval servisi: `retrieve(user, question, filters)` → önce `allowed_document_ids`, sonra FTS. Test için `seed_data/t0/` altında 2 belge: Facility Agreement EXECUTED (DSCR 1,25x, tenor 12 yıl) ve Amendment 01 (DSCR 1,20x, tenor 14 yıl) — WeasyPrint ile üretilir, 6–10 sayfa, geçici rakamlar, "DEMO" ibaresi; ayrıca birinin görüntü PDF kopyası.
**Kabul kriterleri:**
1. Dijital PDF upload → `ready`; `document_pages` sayfa sayısı = PDF sayfa sayısı.
2. Görüntü PDF upload → ocrmypdf çalışır → `ready`; metin okunabilir ("DSCR" bulunur).
3. Bozuk dosya → `failed` + `ingestion_error` dolu; `.exe` → 415.
4. FTS: "DSCR covenant" → iki belgeden chunk döner, her chunk'ta `page_number` dolu.
5. Retrieval `allowed_document_ids()` üzerinden geçer (test: fonksiyon boş küme döndürünce sonuç boş).

## Phase 0.3 — LLM + soru-cevap (T0) `O`
**Kapsam:** `app/services/llm/`: `LLMClient` protokolü, `OpenAICompatibleClient` (Gemini), opsiyonel `AnthropicClient`; token sayımı. `POST /api/ask`: authorize → retrieve → versiyon/tarih değerlendirme (`supersedes`, `effective_date`, `DEMO_TODAY`) → prompt (yalnızca izinli chunk'lar, kural 2 ve 6) → cevap + kaynaklar (belge, **sayfa**, tarih, versiyon). Kaynak yoksa standart "bilgi bulamadım". Minimal tek sayfalık HTML (Caddy olmadan, backend'den servis) veya `curl` ile kullanım; tam frontend Adım 3.
**Kabul kriterleri (T0):**
1. "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → 1,20x + Amendment 01 + sayfa numarası.
2. "İlk DSCR covenant neydi?" → 1,25x + EXECUTED + sayfa; iki cevap farklı.
3. "İzmir RES'in COD tarihi nedir?" → "bilgi bulamadım".
4. Prompt'a giden chunk'lar test ile yakalanır; `allowed_document_ids` dışı hiçbir chunk yok.
5. Cevaplar Türkçe, kaynak İngilizce olsa da; token sayıları loglanmış.
**Naci karar noktası:** devam / dur.

---

# ADIM 1 — Kapı: kullanıcılar ve yetkiler
Tanım: Kimin hangi belgeyi görebileceğini belirleyen yapı. Adım 0'daki stub doldurulur.

## Phase 1.1 — Auth + kullanıcılar `O`
**Kapsam:** `users` (`username, password_hash, display_name, role, is_active, auth_provider, external_id`), Argon2, `/api/auth/login|logout|me`, JWT httpOnly cookie 8 saat, login rate limit. Seed: `admin, yonetim, finans, hukuk, enerji`.
**Kabul kriterleri:** doğru login 200 + cookie; yanlış şifre / disable 401; cookie'siz `me` 401; loglarda şifre/hash yok (test).

## Phase 1.2 — Departman, rol, proje, yetki `O`
**Kapsam:** `departments` (ağaç), `user_departments`, `projects` (admin CRUD, aktif/pasif, çoklu departman), roller `admin|management|employee`, `confidentiality normal|restricted|board`. `allowed_document_ids()` gerçek mantıkla dolar (SPEC_02 §5). Belge listesi, indirme, `/api/ask` — hepsi bu fonksiyondan.
**Kabul kriterleri:**
1. `enerji` → finans belgesi listede yok, indirme 403, `/api/ask` ile "bilgi bulamadım". Audit'te
   `retrieved_document_ids`: yetkisiz sorguda yalnızca kullanıcının erişebildiği (ama alakasız) belgeleri
   içerebilir; yasak departmanın belgesi asla listede olmaz — `forbidden_sources` kontrolü budur, boş liste değil
   (bkz. `docs/reports/PHASE_3_1_REPORT.md §7`).
2. `finans` → legal 403, kendi 200; `yonetim` → hepsi 200; `restricted`/`board` kuralları test edilmiş.
3. Admin proje CRUD; employee 403.
4. Yetki servisi birim testleri + endpoint entegrasyon testleri.

---

# ADIM 2 — Doğruluk defteri
Tanım: İki demo projenin tüm rakam ve tarihleri tek onaylı kaynakta. **Naci onayı olmadan Adım 3'e geçilmez.**

## Phase 2.1 — Truth ledger + validator + golden questions v1 `S`
**Kapsam:** `seed_data/master/company.yaml, ankara_res.yaml, izmir_res.yaml, fx_rates.yaml` (SPEC_05 §3 şeması), her değer `USER_FACT|AI_ASSUMPTION`. `validate_ledger.py`: kaba kronoloji, finans tutarlılığı, İzmir'de lisans sonrası alanlar boş, para birimleri, isim whitelist. `evaluation/questions.json` v1 (≥ 30 soru, SPEC_05 §9 şeması).
**Süreç:** Claude Code taslak üretir (hepsi `AI_ASSUMPTION`) → Naci + enerji finansı ekip arkadaşı gözden geçirir → onaylananlar `USER_FACT`.
**Kabul kriterleri:** validator 0 hata; Ankara zinciri (DRAFT→V01→V02→EXECUTED→AMD01→AMD02) ledger'da; Ankara 3. işletme yılı `DEMO_TODAY`'e göre; İzmir COD/lisans/finansman `null`; her tutarda para birimi; ≥ 30 soru (İzmir ≥ 9, Ankara ≥ 20, hallucination ≥ 3, isolation ≥ 3, authorization ≥ 3).

---

# ADIM 3 — Ürün 1a: Belge sistemi
Tanım: Tanıma aşaması — bulur, okur, kaynak göstererek aktarır; yorum katmaz.

## Phase 3.1 — 15 demo belge + seed/reset `S`
**Kapsam:** `seed_data/generator/` şablonlar + WeasyPrint; 15 belge (Ankara: Facility zinciri 4, Licence + Amendment 2, EPC, COD belgesi, Covenant Report, Production Report; İzmir: ÇED durum yazısı, arazi edinim, teknik rapor, önlisans/başvuru; company: Board Resolution). Dil karışık (finans EN, mevzuat TR). Rakam/tarih/isim yalnızca ledger'dan; prose LLM ile batch, `AI_ASSUMPTION`. `scripts/seed_demo.sh` (kullanıcılar + projeler + belgeler + metadata), `scripts/reset_demo.sh`. Adım 0'daki geçici 2 belge kaldırılır.
**Kabul kriterleri:** `make seed` → 15 belge `ready`, metadata doğru, zincir bağlı, "güncel" belge tek; belgeler gerçekçi görünür; gerçek isim yok (validator); `make reset-demo` + `make seed` tekrar çalışır.

## Phase 3.2 — AI metadata önerisi + temporal mantık `S`
**Kapsam:** Upload sonrası `LLM_MODEL_CLASSIFY` ile öneri (`document_metadata_suggestions`), kullanıcı kabul/düzenleme endpoint'i; kritik alan sessiz overwrite yok. Versiyon zinciri (`supersedes/superseded_by`) yönetimi ve `/api/ask`'te "güncel"/"ilk" ayrımının tam hali; "neden?" sorularında kural 6.
**Kabul kriterleri:** Facility Agreement upload → öneri Finans/Ankara/Facility Agreement + confidence; LLM hatası upload'ı bozmaz; "güncel kapasite" ↔ "ilk lisans kapasitesi" farklı ve doğru; "EBITDA neden düştü?" → yalnızca belgede yazan sebep veya "belirtilmemiş".
**Not (Phase 1.2):** `documents.department` FK almıyor, serbest slug string olarak kalıyor (bkz. `docs/plans/PHASE_1_2_PLAN.md` T2) — bu fazda upload formu/öneri akışı, kullanıcının veya LLM önerisinin yazdığı `department` değerini `departments` tablosundaki bilinen slug listesine karşı doğrulamalı; yanlış yazılmış/bilinmeyen bir slug şu an güvenli yönde başarısız oluyor (belge admin dışında kimseye görünmüyor) ama sessizce, hatasız geçiyor.

## Phase 3.3 — Frontend `S`
**Kapsam:** Vite+React+TS, Caddy compose'a; ekranlar: Giriş, Ana sayfa (departman kartları + Genel Sor), Departman (Sor / Belgeler / Yükle / Projeler), Yükle (form + AI önerisi), Belgeler, Sor (cevap + kaynak kartları: belge, sayfa, tarih, versiyon, proje). Türkçe, sade, responsive.
**Kabul kriterleri:** `http://<vm-ip>:8080` uçtan uca; `enerji` ile Finans kartı görünmez VE API 403; yükleme akışı çalışır; hata mesajları Türkçe, stack trace yok.

## Phase 3.4 — Audit log + embedding (opsiyonel) `S` — embedding için VM 16 GB
**Kapsam:** `audit_log` (SPEC_06 §1), 90 gün temizlik; audit ≠ hafıza. `embed` servisi (bge-m3, profile full), `EMBEDDINGS_ENABLED`; hibrit retrieval.
**Kabul kriterleri:** her `/api/ask` audit'te (kaynaklar, model, token); şifre/key yok; `EMBEDDINGS_ENABLED=false` ile tüm testler geçer; `true` ile embed servisi çalışır (RAM yoksa atlandı diye raporlanır).

---

# ADIM 4 — Karne ve Excel
Tanım: Doğruluğun ölçülmesi; kesin veriyle aritmetik yapan Excel motoru; projeksiyon yok.

## Phase 4.1 — Eval runner `S`
**Kapsam:** `scripts/run_eval.py`: `questions.json` → `/api/ask` (soruyu `ask_as_user` ile) → skor (normalize karşılaştırma `1.20x/1,20x/1.2`, required/forbidden sources, expected_project, expect_no_answer). Çıktı markdown + JSON, `results/<model>_<date>`. Gemini ücretsiz katman istek sınırına uyum (bekleme).
**Kabul kriterleri:** `make eval MODEL=…` çalışır; isolation/hallucination/authorization %100; document/temporal ≥ %80 (değilse Phase 3.2'ye dönülür); iki model karşılaştırma dosyası.
**Ön koşul (Phase 3.2):** Eval koşmadan önce FTS'in İngilizce çoğul/kısaltma eşleşme zayıflığı (`test_initial_dscr_is_executed_and_differs`, "covenant" vs "covenants", "DSCR" literal geçmiyor) golden questions/prose seviyesinde çözülmeli veya bilinen sınırlama olarak eval sonuçlarına not düşülmeli — aksi halde document kategorisi skoru retrieval hatasını model hatası gibi gösterir (bkz. `docs/reports/PHASE_3_2_REPORT.md` §7).
**Not (Phase 0.3):** `isolation` kategorisi, alakasız projenin chunk'ları retrieval'a girdiğinde (OR-FTS, ADR-020: "İzmir RES" sorusu Ankara chunk'larını getirir) LLM'in çıkarım yapmayıp "bilgi bulamadım" demesini de kapsamalı; T0'da kriter 3 tam olarak bu yola dayanıyor. Runner Gemini ücretsiz katmanı (5 istek/dk, 503 "high demand") için bekleme/retry ve `MODEL=` override'ı içermeli.

## Phase 4.2 — Excel motoru `O`
**Kapsam:** SPEC_04. Dört workbook ledger'dan (openpyxl) + build-time LibreOffice headless recalc (`seed_data/generator/recalc.sh`). Inspection (openpyxl), hesap DuckDB read-only; LLM yalnızca SELECT (whitelist) + predefined fonksiyonlar; timeout 10 s; kaynak dosya+sheet+range; `CalculationEngine` interface'i.
**Kabul kriterleri:** cached değerler dolu (`data_only` boş hücre yok); "Ankara RES 2026 Q2 DSCR kaç?" → DuckDB + `Covenant_Report.xlsx Q2_2026!D14` tarzı kaynak; `DROP/;/COPY/çoklu statement` reddedilir; `.xlsm` macro çalışmaz; audit'te excel kaynakları.

## Phase 4.3 — Mixed query `S`
**Kapsam:** Router `DOCUMENT|DATA|MIXED|GENERAL`; MIXED = iki alt sorgu + birleştirme (yorum yok). Belirsiz "güncel DSCR kaç?" → covenant (belge) + gerçekleşen (Excel).
**Kabul kriterleri:** EBITDA sorusu → Excel farkı + belge kaynağı + yalnızca belgedeki sebep; belirsiz DSCR → iki değer iki kaynak türü; GENERAL sorularda şirket verisi kullanılmaz ve bu belirtilir.
**Naci karar noktası:** Gemini yeterli mi / yerel model gündemi.

---

# ADIM 5 — Ürün hali
Tanım: Gösterilebilir, yedeklenebilir, sıfırdan kurulabilir sistem.

## Phase 5.1 — Tam dataset + consistency checks `S`
**Kapsam:** ~70 belge (SPEC_05 §6 dağılımı), 8–10 görüntü PDF, `validate_dataset.py` (SPEC_05 §11), `questions.json` v2 (≥ 60).
**Kabul kriterleri:** validator 0 hata; görüntü PDF'ler `ready`; eval isolation/hallucination/authorization %100, diğerleri ≥ %80; belge ≤ 80.

## Phase 5.2 — Admin panel `S`
**Kapsam:** kullanıcı ekle/disable/rol, departman izinleri, proje CRUD, metadata düzenleme, "bu belgeyi kim görebilir", audit log (filtre).
**Kabul kriterleri:** admin her işlemi UI'dan; employee admin endpoint'lerinde 403; audit'te gizli veri yok.

## Phase 5.3 — Backup / restore `S`
**Kapsam:** `backup.sh` (Postgres dump, `documents/`, `excel/`, app-data, config) → `$DATA_ROOT/backups/` günlük, 14 gün; haftalık `BACKUP_SECONDARY_PATH` (spindown'dan önce); `restore.sh`; README prosedürü.
**Kabul kriterleri:** backup → `make down` → volume sil → restore → aynı belgeler/kullanıcılar; eval skoru aynı.

## Phase 5.4 — Temiz kurulum + README final `S` — prod klonunda
**Kapsam:** Proxmox'ta `company-ai-prod` (temiz klon veya sıfır VM). Yalnızca README izlenir; kod değişikliği beklenmez.
**Kabul kriterleri (V0 başarı):** `git clone` → `.env` (`DATA_ROOT=/srv/company-ai`) → `make up` → `make seed` → çalışır; Türkçe UI; `enerji` finansa ulaşamaz (UI+API+AI); güncel/ilk DSCR farklı ve doğru; Ankara/İzmir karışmaz; en az bir DuckDB analizi; kaynaksız soru uydurmaz; README'de kurulum, model değiştirme, backup/restore, bilinen sınırlar (embedding opsiyonel, HTTPS yok, consume yok, Word/e-posta yok).
