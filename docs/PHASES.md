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
| 3.2b | Retrieval/cevap düzeltmeleri (Phase 4.1 bulguları) | tamamlandı (eşikler kısmen, kalan boşluklar içerik — bkz. rapor §3.2) | phase-3-2b | [PHASE_3_2B_REPORT](reports/PHASE_3_2B_REPORT.md) |
| 3.2c | Prose yaması (3.2b'nin kalan soruları) | tamamlandı — **eval eşikleri geçildi** | phase-3-2c | [PHASE_3_2C_REPORT](reports/PHASE_3_2C_REPORT.md) |
| 3.3 | Frontend | tamamlandı | phase-3-3 | [PHASE_3_3_REPORT](reports/PHASE_3_3_REPORT.md) |
| 3.4 | Audit log + embedding (opsiyonel) | tamamlandı | phase-3-4 | [PHASE_3_4_REPORT](reports/PHASE_3_4_REPORT.md) |
| 4.1 | Eval runner (karne) | tamamlandı (skor eşiği altında, bkz. rapor §7) | phase-4-1 | [PHASE_4_1_REPORT](reports/PHASE_4_1_REPORT.md) |
| 4.2 | Excel motoru | tamamlandı | phase-4-2 | [PHASE_4_2_REPORT](reports/PHASE_4_2_REPORT.md) |
| 4.3 | Mixed query (router) | tamamlandı | phase-4-3 | [PHASE_4_3_REPORT](reports/PHASE_4_3_REPORT.md) |
| 5.1 | Tam dataset (~70) + consistency checks | tamamlandı (eval kısmen eşik altında kaldı, devamı Phase 5.1b'de — bkz. rapor) | phase-5-1 | [PHASE_5_1_REPORT](reports/PHASE_5_1_REPORT.md) |
| 5.1b | Eval eşik ihlalini kapatma (`RETRIEVAL_TOP_K` 40→80, `ANK-FIN-010` düzeltmesi) | tamamlandı (document/mixed/data eşiği geçti; **isolation %75, temporal %60 — bilinen sınırlama, kabul edildi (26.09.2026, Naci kararı)**, bkz. Phase 5.1 notu ve rapor §7/§8) | phase-5-1b | [PHASE_5_1B_REPORT](reports/PHASE_5_1B_REPORT.md) |
| 5.2 | Admin panel | tamamlandı | phase-5-2 | [PHASE_5_2_REPORT](reports/PHASE_5_2_REPORT.md) |
| 5.3 | Backup / restore | tamamlandı | phase-5-3 | [PHASE_5_3_REPORT](reports/PHASE_5_3_REPORT.md) |
| 5.4 | Temiz kurulum doğrulaması + README final | kısmen tamamlandı — README'nin 2 eksiği kapatıldı + `company-ai-test` VM'inde doğrulandı; Excel/DuckDB testi **denendi, günlük Gemini kotası tükendiği için başarısız oldu**; tarayıcı UI testi Naci elle yapacak; eval isolation/hallucination/temporal kategorileri Naci onayıyla atlandı; ilk DSCR ve Ankara/İzmir canlı ayrımı hâlâ eksik, bkz. rapor §0/§7 | phase-5-4 | [PHASE_5_4_REPORT](reports/PHASE_5_4_REPORT.md) |

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
**Not (02.10.2026, B-28):** Bu fazın **SORU 2 kararı (öneriyi yalnızca admin kabul eder = yayınlar) değiştirildi** — Tansu #5 iki aşamalı onay (NOT §5.2): yükleyen `submit`, hedef departmanın `department_manager`'ı `review`; `apply` admin'de kalır ama yayınlama eylemi değildir (ADR-024).
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
**Ön koşul (Phase 4.1 → 3.2b → 3.2c, 25.09.2026) — karşılandı:** Phase 3.2c sonrası eval: authorization/hallucination/isolation %100, document %87,0 (20/23), temporal %88,9 (8/9) — eşikler geçildi, `make eval` sıfır çıkış. Yol: 4.1 ölçtü (%50/%52/%33), 3.2b kod+prompt'u düzeltti (sözlük, deterministik sıralama, top_k=40, kural 2/5), 3.2c belge içeriğindeki boşlukları kapattı (7 cümle). Kalan 4: `IZM-DEV-005/006` negatif-olgu soruları (NO OPINION çelişkisi — Naci kararı bekliyor), `ANK-EPC-004`/`IZM-DEV-007` doğru cevap ama soru setinin ikinci atıf beklentisi. Güvenlik sınırı üç koşuda da sağlam (sıfır yasak kaynak). Ayrıntı: `docs/reports/PHASE_3_2C_REPORT.md`.
**Kapsam:** SPEC_04. Dört workbook ledger'dan (openpyxl) + build-time LibreOffice headless recalc (`seed_data/generator/recalc.sh`). Inspection (openpyxl), hesap DuckDB read-only; LLM yalnızca SELECT (whitelist) + predefined fonksiyonlar; timeout 10 s; kaynak dosya+sheet+range; `CalculationEngine` interface'i.
**Kabul kriterleri:** cached değerler dolu (`data_only` boş hücre yok); "Ankara RES 2026 Q2 DSCR kaç?" → DuckDB + `Covenant_Report.xlsx Q2_2026!D14` tarzı kaynak; `DROP/;/COPY/çoklu statement` reddedilir; `.xlsm` macro çalışmaz; audit'te excel kaynakları.
**Not (Phase 4.2):** Financial Model'in taban faiz / geri ödeme takvimi / çeyreklik CFADS girdileri ledger'a `AI_ASSUMPTION` olarak eklendi (`validate_ledger` F9-F11) — Naci gözden geçirip `USER_FACT`'e çevirebilir. Dört workbook `seed_data/excel/` altında commit'li (recalc LibreOffice `tools` container'ında, prod'da gerekmez). DATA giriş noktası `POST /api/excel/ask`; `/api/ask` DOCUMENT-only kaldı, birleştirme Phase 4.3'te.

## Phase 4.3 — Mixed query `S`
**Kapsam:** Router `DOCUMENT|DATA|MIXED|GENERAL`; MIXED = iki alt sorgu + birleştirme (yorum yok). Belirsiz "güncel DSCR kaç?" → covenant (belge) + gerçekleşen (Excel).
**Kabul kriterleri:** Q3 2024 bütçe sapması + "sebebi belgelerde var mı?" sorusu → Excel farkı (`Summary!D5`) + belge kaynağı + yalnızca belgedeki sebep (belgede sebep yoksa kural 6'nın sabit cümlesi — Phase 4.3 planı SORU 1, 25.09.2026: "EBITDA sorusu" ledger'da EBITDA ve sebep anlatan belge olmadığı için bu şekilde yeniden ifade edildi); belirsiz DSCR → iki değer iki kaynak türü; GENERAL sorularda şirket verisi kullanılmaz ve bu belirtilir.
**Naci karar noktası:** Gemini yeterli mi / yerel model gündemi (ölçüm: `docs/reports/PHASE_4_3_REPORT.md` §9).
**Not (Phase 4.3):** `questions.json` v2 = 48 soru (3 `data` + 2 `mixed`); `general` kategorisi ve "sebep belgede pozitif olarak yazıyor" örneği (Bakım Raporu Temmuz 2024 gibi bir belge gerektirir) Phase 5.1'e.
**GENERAL_QUERY kaldırıldı (30.09.2026, Naci + Tansu kararı, ayrı güvenlik/kapsam yaması — ayrı bir phase değil):** Router artık yalnızca `DOCUMENT|DATA|MIXED` döndürüyor; "DSCR ne demek?" gibi tanım soruları da dahil hiçbir soru modelin genel dünya bilgisinden cevaplanmıyor, hepsi belgelere bakıyor. `general_answer.py` silindi; `questions.json`'daki 3 `general` sorusu `document` kategorisine, `expect_no_answer: true` ile taşındı (korpus bu terimleri genel biçimde hiç tanımlamıyor). Canlı doğrulandı: 3 soru + `hallucination`/`authorization`'dan birer örnek, hepsi geçti. Detay: `docs/plans/GENERAL_QUERY_KALDIRMA_PLAN.md`, `docs/reports/GENERAL_QUERY_KALDIRMA_REPORT.md`.

---

# ADIM 5 — Ürün hali
Tanım: Gösterilebilir, yedeklenebilir, sıfırdan kurulabilir sistem.

## Phase 5.1 — Tam dataset + consistency checks `S`
**Kapsam:** ~70 belge (SPEC_05 §6 dağılımı), 8–10 görüntü PDF, `validate_dataset.py` (SPEC_05 §11), `questions.json` v2 (≥ 60).
**Kabul kriterleri:** validator 0 hata; görüntü PDF'ler `ready`; eval isolation/hallucination/authorization %100, diğerleri ≥ %80; belge ≤ 80.
**Kapandı (Phase 5.1, 25.09.2026):** Phase 4.3'ün ertelediği (a) `QuestionCategory` += `general` + 3 GENERAL sorusu (`eval_lib.py` artık `query_type`/kaynak-yokluğu üzerinden puanlıyor) ve (b) MIXED'in pozitif "sebep belgede yazıyor" dalı — yeni `DOC-ANK-OPS-005` (Bakım Raporu — Temmuz 2024) `incidents[0]`'ı `monthly_production[8]`'e bağlıyor, `ANK-MIX-002` artık pozitif; negatif örnek (Q1 2025, belgesiz kalan Ocak 2025 kesintisi) yeni `ANK-MIX-003`'e taşındı.
**Ertelenen (Phase 3.2c, 25.09.2026, Naci kararı — Phase 5.1/5.1b kapsamı dışında kaldı):** (1) `IZM-DEV-005/006` gibi negatif-olgu soruları ("lisans alındı mı?") NO OPINION kuralıyla çelişiyor — soru seti v2'de ya `expect_no_answer` beklenmeli ya da belgeler açıkça "henüz alınmamıştır" demeli (Phase 5.1b'de aynı desenin iki yeni örneği gözlemlendi: `IZM-DEV-003`/`IZM-DEV-004`, bkz. `docs/reports/PHASE_5_1B_REPORT.md` §8 — backlog artık 4 değil 6 örnek); (2) `ANK-EPC-004`/`IZM-DEV-007`: cevap doğru ama `required_sources` listesindeki ikinci belge gösterilmiyor — v2 şemasında "hepsi / en az biri" ayrımı (`required_sources_all`) tanımlanmalı ve eval runner'a yansıtılmalı; (3) elle düzenlenmiş prose dosyaları `hand_edited:` işaretli, `generate_prose.py` bunları `--force` ile bile ezmez — yeni belgeler üretilirken bu 6 dosya korunur (`docs/reports/PHASE_3_2C_REPORT.md`).
**Eval bulgusu (26.09.2026) — Phase 5.1b'de ele alındı:** ilk tam koşuda `document`/`mixed`/`temporal` eşik altındaydı (bkz. `docs/reports/PHASE_5_1_REPORT.md` §4/§8); Phase 5.1b bunu araştırıp kısmen kapattı (`document`/`mixed` artık geçiyor) — kalan `isolation`/`temporal` boşluğu ve tam kök neden analizi `docs/reports/PHASE_5_1B_REPORT.md`'de.
**Bilinen sınırlama, kabul edildi (26.09.2026, Naci kararı):** `isolation` (%75) ve `temporal` (%60) eşik altında kalmaya devam ediyor; üçüncü bir düzeltme turu açılmadı. Gerekçe: (1) hiçbir isolation başarısızlığı gerçek bir güvenlik ihlali değil — hepsi güvenli yöndeki aşırı temkin (belge erişilebilirken "bulamadım" demek), yasak kaynak sızıntısı yok; (2) Phase 4.1'den beri (4.1→3.2b→3.2c→5.1b) dört düzeltme turu geçirildi, azalan getiri gözlemlendi; (3) 25-26.09.2026'da Gemini'nin günlük ücretsiz kota kısıtı zaten yaşandı, ek deneme turlarının maliyeti şu an yüksek. Kök neden `answer_prompt.py`'nin model-cevaplama güvenilirliği (retrieval veya routing değil) — bilinçli olarak bu fazda dokunulmadı. Takip: bkz. Phase 5.4 notu ve olası ayrı bir gelecek "prompt tuning" fazı önerisi (aşağıda, ADIM 5 sonu).

## Phase 5.2 — Admin panel `S`
**Kapsam:** kullanıcı ekle/disable/rol, departman izinleri, proje CRUD, metadata düzenleme, "bu belgeyi kim görebilir", audit log (filtre).
**Kabul kriterleri:** admin her işlemi UI'dan; employee admin endpoint'lerinde 403; audit'te gizli veri yok.
**Kapandı (Phase 5.2, 26.09.2026):** Proje CRUD ve audit log backend'i zaten tamamdı (Phase 1.2/3.4) — yalnızca
admin UI'ları eklendi. Yeni: `/api/users` (kullanıcı ekle/liste/rol/aktiflik/departman üyeliği, admin kendi
rolünü düşüremez/hesabını kapatamaz — 409), `PATCH /api/documents/{id}` (öneri akışından bağımsız manuel
metadata düzenleme, versiyon zinciri alanları hariç), `GET /api/documents/{id}/visibility` ("kim görebilir",
`allowed_document_ids`'i `SingleDocumentIdsProvider` ile tersinden çalıştırır — ikinci bir yetki motoru yok).
Frontend: `/yonetim/kullanicilar`, `/yonetim/denetim-kaydi` (yalnızca admin nav'da görünür, `RequireAdmin`
guard'ı diğer rolleri sessizce anasayfaya yönlendirir), belge detayına "kim görebilir" kartı + manuel metadata
formu. "Departman izinleri" = yalnızca kullanıcı↔departman üyeliği ataması; departman ağacının kendisi hâlâ
seed-only (Phase 1.2 kararı yeniden açılmadı). Şifre sıfırlama kapsam dışı bırakıldı (SORU 2). Detay:
`docs/reports/PHASE_5_2_REPORT.md`.

## Phase 5.3 — Backup / restore `S`
**Kapsam:** `backup.sh` (Postgres dump, `documents/`, `excel/`, app-data, config) → `$DATA_ROOT/backups/` günlük, 14 gün; haftalık `BACKUP_SECONDARY_PATH` (spindown'dan önce); `restore.sh`; README prosedürü.
**Kabul kriterleri:** backup → `make down` → volume sil → restore → aynı belgeler/kullanıcılar; eval skoru aynı.
**Kapandı (Phase 5.3, 26.09.2026):** `scripts/backup.sh`/`scripts/restore.sh` (yeni), `make backup`/`make restore`
stub'ları gerçek script'lere bağlandı. Canlı dev VM'de gerçek bir yıkıcı döngü çalıştırıldı: `make backup` →
`make restore ARGS="<tarih> --yes"` (kendi içinde `compose down` + volume temizliği + geri yükleme + `compose
up` yapıyor) → `make test` (383/383 yeşil) + `make eval EVAL_ARGS="--retrieval-only"` (recall@80 36/36,
restore öncesiyle birebir aynı) + belge/kullanıcı/proje sayıları (74/5/3, birebir aynı) — hepsi doğrulandı
(SORU 4 kararına göre tam LLM eval'i çalıştırılmadı). Yol boyunca iki gerçek izin sorunu keşfedildi ve çözüldü:
(1) Postgres'in veri dizini container-içi bir kullanıcıya ait, host kullanıcısı doğrudan silemiyor/okuyamıyor —
hem `pg_dump`/`pg_restore` (stdin/stdout pipe) hem silme işlemleri kısa ömürlü bir `--user root` konteynerinden
yapılıyor; (2) `app-data/caddy` da aynı sebeple (Caddy container'ı root çalışıyor) host'tan okunamıyor — o da
aynı root-konteyner yöntemiyle arşivleniyor/geri yükleniyor (yalnızca `app-data/models`, 2,2 GB'lık yeniden
inebilir embedding önbelleği, hariç tutuluyor). Bu ikisi planda öngörülmemişti, uygulama sırasında ölçülerek
bulundu. Ayrıca Phase 5.2'den kalan, `make lint`'in daha önce hiç yakalamadığı gerçek bir mypy hatası
(`SingleDocumentIdsProvider`'da `str | None` daraltması eksikti) bu fazda bulunup düzeltildi. Detay:
`docs/reports/PHASE_5_3_REPORT.md`.

## Phase 5.4 — Temiz kurulum + README final `S` — prod klonunda
**Kapsam:** Proxmox'ta `company-ai-prod` (temiz klon veya sıfır VM). Yalnızca README izlenir; kod değişikliği beklenmez.
**Kabul kriterleri (V0 başarı):** `git clone` → `.env` (`DATA_ROOT=/srv/company-ai`) → `make up` → `make seed` → çalışır; Türkçe UI; `enerji` finansa ulaşamaz (UI+API+AI); güncel/ilk DSCR farklı ve doğru; Ankara/İzmir karışmaz; en az bir DuckDB analizi; kaynaksız soru uydurmaz; README'de kurulum, model değiştirme, backup/restore, bilinen sınırlar (embedding opsiyonel, HTTPS yok, consume yok, Word/e-posta yok, Gemini ücretsiz katman günlük kota, **eval isolation/temporal eşik altı — bkz. Phase 5.1/5.1b**).
**Kapandı (kısmen, Phase 5.4, 26.09.2026):** Bu oturum `company-ai-prod` yerine `company-ai-test` VM'inde
(önceden var olan repo kopyası, `git clone` yapılmadı) hiçbir bağlamı olmayan birinin README'yi birebir takip
edip edemeyeceğini test etti: `.env` → `make up` → `make seed` → login → gerçek bir DSCR sorusu → `enerji`↔finans
izolasyonu, sırayla. İki gerçek README eksiği bulundu ve düzeltildi: (1) Gemini API key alma talimatı yoktu,
eklendi (`aistudio.google.com/apikey`); (2) `.env` değiştikten sonra sıradan `docker compose restart`'ın
yetmediği, `--force-recreate` gerektiği (env_file compose'un değişiklik takibine dahil değil) belgelenmemişti,
yeni bir bölüm eklendi. Güncel DSCR (1,20x) + `enerji`↔finans izolasyonu (liste/indirme-403/`/api/ask`) canlı
LLM ile doğrulandı; `make test` 383+9 yeşil; `make eval --retrieval-only` recall@80 36/36 (Phase 5.3 ile aynı).
Naci ikinci turda resmi eval kategorilerini (kota riski, zaten `company-ai-dev`'de kanıtlandı) atlamayı
onayladı ve **tarayıcı UI testini kendisi elle yapacak** (bu oturumun kapsamında değil). Buna karşılık istenen
Excel/DuckDB testi ("Ankara RES 2026 Q2 DSCR kaç?", `/api/excel/ask`) denendi — 5 kez, 40 sn arayla — ama
`gemini-3.5-flash-lite`'ın günlük kotası (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, 500/gün)
gerçekten tükendiği için 5/5 başarısız oldu; bu, `company-ai-dev`/`company-ai-test`'in aynı `LLM_API_KEY`'i
paylaşmasının teorik değil **canlı, gerçekleşmiş bir riski** olduğunu kanıtladı (ayrı key önerilir).
**Planın geri kalanı karşılanmadı:** prod VM'de sıfırdan `git clone`, tarayıcı UI testi (Naci elle yapacak),
başarılı bir Excel/DuckDB analizi (denendi, kota nedeniyle engellendi), ilk DSCR (1,25x), Ankara/İzmir'in
canlı bir soruda karışmadığının kontrolü, resmi eval kategorilerinin (`isolation`/`hallucination`/`temporal`,
Naci onayıyla atlandı) canlı LLM ile koşulması — hiçbiri bu oturumda tamamlanamadı (Naci kararı bekleniyor:
ayrı bir faz mı, yoksa bu dar kapsam mı kabul edilecek). Detay: `docs/reports/PHASE_5_4_REPORT.md`.

**Olası gelecek faz önerisi (kapsam dışı, planlanmadı):** Phase 5.1b'nin kabul edilen bilinen sınırlaması (`isolation` %75, `temporal` %60) ileride ayrı, dar kapsamlı bir "prompt tuning" fazıyla ele alınabilir — `answer_prompt.py`'nin model-cevaplama güvenilirliğine odaklı, retrieval/routing'e dokunmayan bir faz. V0 kapsamında zorunlu değil; yalnızca unutulmasın diye not düşülüyor.

**Bağımsız güvenlik yaması (30.09.2026, `d588487`):** Yükleme yetki açığı kapatıldı, Tansu incelemesinden
(`docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §2 B-26/3, §7.1). Ayrı bir phase değil; plan
`docs/plans/GUVENLIK_YAMA_2026-09-30_PLAN.md`'de.

**GENERAL_QUERY kaldırıldı (30.09.2026, `0b891fb`):** Naci + Tansu kararı — bkz. Phase 4.3 notu (üstte).
Ayrı bir phase değil; plan `docs/plans/GENERAL_QUERY_KALDIRMA_PLAN.md`, rapor
`docs/reports/GENERAL_QUERY_KALDIRMA_REPORT.md`.

**Aşama A — "Balbal cevap döngüsü" (30.09.2026, `1199d88`):** AI-BalBal'ın `/api/ask` etrafında beklediği sözleşme
kapatıldı — `audit_log_id`, `product_level`, `warnings` (`missing_data`/`product_limit`; Tansu #1'in reddettiği
beğen/hatalı butonlarının yerine, `/api/ask/feedback` yazılmadı), `SourceCard` versiyon id'leri + `is_initial` (B-07),
`company_settings.enabled_products` + `/login`/`/me` alanı + `require_product("P2")` (`/api/excel/ask`) + P1'de
belgeye düşürme kuralı + `GET/PATCH /api/admin/settings` + `make set-products` (B-25, ADR-022), migration `0009`.
Ayrı bir phase değil; plan `docs/plans/ASAMA_A_BALBAL_DONGUSU_PLAN.md`, rapor
`docs/reports/ASAMA_A_BALBAL_DONGUSU_REPORT.md`. company-ai `frontend/` emekli, dokunulmadı.

**AI-BalBal Caddy'den sunuluyor (30.09.2026, `24ba438`):** `frontend-balbal/` git submodule'ü (`ftansu/AI-BalBal` @ `b219600`),
caddy imajı `FRONTEND_DIR` ile seçilen kaynaktan derlenir (`additional_contexts`), `FRONTEND_DIR=./frontend` + `make up`
tek değişkenle geri dönüş; `make update-frontend REF=…`; `make lint`'ten frontend adımı çıkarıldı. Caddyfile/backend
değişmedi. Ayrı bir phase değil; plan `docs/plans/AIBALBAL_DEPLOY_PLAN.md`, rapor `docs/reports/AIBALBAL_DEPLOY_REPORT.md`.
Tarayıcı adımları (A2/A3) Naci elle.

**Aşama B (30.09.2026, `9d83227`):** `file_kind` (B-13, `storage_path`'ten türetme, migration yok), indirme adı = başlık + uzantı
+ `?inline=1` (B-17; pdf/görüntü inline, açık `Content-Type` + `nosniff`), `AskRequest`/`ExcelAskRequest.project_id`
kaldırıldı (B-20/6; eski istemci 422 almaz, eval hiç göndermiyordu — NOT'taki isolation uyarısı geçersizdi). Ayrı bir
phase değil; plan `docs/plans/ASAMA_B_PLAN.md`, rapor `docs/reports/ASAMA_B_REPORT.md`.

**Aşama C (01.10.2026, `e6b9bc5`):** departman ağacı zihin haritasıyla birebir (B-20/1-5: 5 ad, 4 yeni satır, `finans`
kullanıcısı yalnızca Proje Finans; slug'lar sabit — belge/ledger/eval dokunulmadı), `users.primary_department_id` +
`primary_department_slug` (B-09, `department_slugs` ana departmanı başa alır), `users.title` + `GET /api/directory`
(B-05), migration `0010` (mevcut DB'yi düzeltir, boş DB'de no-op; seed aynı ağacı kurar). `manager_id` ve B-08 enum'u
yok. Ayrı bir phase değil; plan `docs/plans/ASAMA_C_PLAN.md`, rapor `docs/reports/ASAMA_C_REPORT.md`. Tarayıcı
kontrolü (C-09) Naci elle.

**Aşama D (01.10.2026, `d49af79`):** `GET /api/search?q=&limit=` (B-14: içerik + metadata belge hits, `ts_headline` düz metin
snippet + sayfa, projeler, kişiler; retrieval'la aynı FTS predicate'i, `retrieve()` değişmedi, `audit_log` yok) ve
`SourceCard.project_code/project_name` (B-20/6, `Document.project`). Migration yok. Ayrı bir phase değil; plan
`docs/plans/ASAMA_D_PLAN.md`, rapor `docs/reports/ASAMA_D_REPORT.md`. AI-BalBal henüz `/api/search`'ü çağırmıyor
(Tansu `SearchPanel`'i bağlar).

**Aşama E (01.10.2026, `c65293d`):** B-26 klasörler ve departman erişim yetkileri — `folders`/`folder_grants`/
`folder_grant_events` + `documents.folder_id` (migration `0011`: üst departman başına kök klasör, belgeler köke),
en yakın tanım mirası, `allowed_document_ids` tek kapı (yeni provider metodu, `employee` = üyelik ∪ grant, gizlilik
aşılmaz), `/api/admin/folders*` + `/api/folders` (`proposed.ts` §10 ile birebir), upload `folder_id` + write kontrolü,
ADR-023. Ayrı bir phase değil; plan `docs/plans/ASAMA_E_PLAN.md`, rapor `docs/reports/ASAMA_E_REPORT.md`. Tarayıcı
(E-15) Naci elle.

**Ürün 1 uyum turu (01.10.2026, `3350f3b`):** Balbal Anayasası v2.0 — Ü-3: `answer_prompt.py` kural 10 (projeler arası
karşılaştırma yok, sabit cümle + ayrı değerler, her pakette geçerli), `questions.json` v4 `comparison` kategorisi (3 soru,
%100 eşik, `required_phrases`/`forbidden_phrases`, iki ledger yollu `expected_answer`, `--repeat` ifade sayacı); Ç-7:
`warnings[].kind` `insufficient_data` (chunk var, model yetmez dedi) ↔ `missing_data` (sıfır chunk). Ayrı bir phase
değil; plan `docs/plans/URUN1_UYUM_PLAN.md`, rapor `docs/reports/URUN1_UYUM_REPORT.md`.

**B-08 departman yöneticisi rolü (02.10.2026, `6cfb3f0`):** `UserRole.department_manager` (migration `0012`, enum `ADD VALUE`;
downgrade tipi yeniden kurar, müdürleri `employee`'ye düşürür). Kural `allowed_document_ids`'in üyelik dalında tek satır:
müdür üye olduğu departmanların `normal` **ve** `restricted` belgelerini görür (üyelik ∪ klasör grant'i, aynı iki seviye),
`board` asla, başka departman asla; `management`/`admin`/`employee` değişmedi. Yeni uç/tablo/provider metodu yok;
rolü admin `PATCH /api/users/{id}` ile kişiye verir (kural sabit, tablo değil — Naci). Upload/klasör yazma kuralları müdürü
`employee` gibi ele alır (§5.2 ile tutarlı, testle kilitlendi). Demo `finans_mudur` (tek `restricted` demo belge `finans`'ta).
Ayrı bir phase değil; plan `docs/plans/B08_DEPARTMAN_MUDURU_PLAN.md`, rapor `docs/reports/B08_DEPARTMAN_MUDURU_REPORT.md`.
Rol/üyelik değişikliği kayıt defteri bu fazda yok (ayrı küçük iş, B-28/§5.2 öncesi).

**B-28 iki aşamalı belge onayı (02.10.2026, `db6a52d`, ADR-024):** `documents.review_status` (migration `0013`, DEFAULT
`approved` — 74 demo belge yayında kalır) **kapıya girdi**: yalnızca `approved` belge retrieval/arama/`/api/ask`/Excel
kataloğuna girer; `AuthorizationScope.include_pending` ile yükleyen kendi bekleyenini, müdür kuyruğunu, admin hepsini
görür (tek yeni provider metodu, imza sabit). Akış: hedef departmanın kendi `department_manager`'ı → anında `approved`;
diğer herkes (`management`/`admin` dahil) → `pending_metadata` → yükleyen `POST /submit` (%80 eşiği `confirmed_fields`,
`suggestion_pending`, `department_required`) → `pending_review` → müdür `POST /review` (`approve` | yorumlu
`request_changes` → `changes_requested` → yeniden `submit`). Onaycısı olmayan departmana yükleme 409
`approver_not_configured` (dosya yazılmaz; `department=None` admin kuyruğunda). Onaylı belgede metadata değişikliği
onayı düşürür (müdür hariç). Kayıt defteri `document_review_events` + `GET /api/admin/documents/{id}/review-events`
(admin). **Phase 3.2 SORU 2 kararı bu fazla değişti** (yukarıdaki Phase 3.2 notu). Ayrı bir phase değil; plan
`docs/plans/B28_ONAY_AKISI_PLAN.md`, rapor `docs/reports/B28_ONAY_AKISI_REPORT.md`. Demo: `hukuk`/`enerji_grubu`'na
personel yüklemesi müdür atanana kadar 409 alır (B-18'de `hukuk_mudur`/`enerji_mudur`). Kapsam dışı (B-28b):
`extra_fields`, `tag_catalog`, tür bazlı alan rehberi, klasör önerisi.

**AI-BalBal frontend senkronu — PR-1 (02.10.2026, `aa1c232`):** `ftansu/AI-BalBal` reposunda `feat/backend-sync-urun1`
dalı + **PR #2** (https://github.com/ftansu/AI-BalBal/pull/2; merge Tansu'da, main'e push yok — Anayasa T-14). İçerik:
`feat/urun1-arayuz` merge'i (Ürün 1 giriş ekranı, ekip sohbeti v8.0), backend tiplerinin eşitlenmesi (`enabled_products`,
`primary_department_slug`/`title`, `warnings`/`product_level`/`audit_log_id`, SourceCard versiyon id'leri + proje,
`file_kind`/`folder_id`/`review_status`, `department_manager`), `?inline=1` dosya linkleri, Ç-7 uyarı etiketleri,
`/api/search` · `/api/directory` · klasör uçları gerçek API'ye (`proposed.ts` §4/§10 kaldırıldı), belge listesinde dosya
türü + onay durumu rozeti (yalnızca gösterim). Backend'e dokunulmadı; company-ai'da yalnızca docs. `frontend-balbal`
submodule pini **merge sonrası** güncellenecek. Plan `docs/plans/AIBALBAL_FRONTEND_SYNC_PLAN.md` (rev. 2, iki PR), rapor
`docs/reports/AIBALBAL_SYNC_PR1_REPORT.md`. Sırada PR-2 `feat/onay-akisi-arayuz` (B-28 onay akışı arayüzü; PR-1'e bağımlı).

**AI-BalBal frontend senkronu — PR-2 (02.10.2026, `26e807d`):** `feat/onay-akisi-arayuz` + **PR #3**
(https://github.com/ftansu/AI-BalBal/pull/3; base PR #2, merge Tansu'da). B-28 onay akışı arayüzü: 1. aşama paneli
(yükleyen; %80 altı "Onaylıyorum", "Onaya gönder", 422 vurgusu), belge detayında onay durumu kartı + müdüre Onayla / Geri
gönder (yorum zorunlu), Belgeler'de onay durumu çipleri (yerel), yöneticiye kayıt defteri; `ApiError.code/fields`.
Backend ön koşulu `a8308b2` (`DocumentDetailResponse.uploaded_by_id`). Canlı akış Caddy üzerinden curl ile doğrulandı,
LLM 0. Plan `docs/plans/AIBALBAL_PR2_PLAN.md`, rapor `docs/reports/AIBALBAL_SYNC_PR2_REPORT.md`.

**AI-BalBal PR #2 + #3 merge ve submodule pini (02.10.2026, `df46b21`):** Tansu'nun sözlü onayı (Naci aktardı), merge
Naci'nin açık talimatıyla `gh pr merge --merge` ile yapıldı (dallar silinmedi; Tansu sonradan inceleyebilir/geri alabilir).
AI-BalBal `main` `bdefb29` → `b709f09`; company-ai `frontend-balbal` pini `b219600` → `b709f09` (`81178cb`). Dev Caddy
yeni sürümle kuruldu; canlı doğrulama Caddy üzerinden (LLM'siz): 4 hesapla giriş (`enabled_products`, `title`,
`primary_department_slug`), `/api/search` snippet + sayfa, klasörler (finans: Proje Finans write/15; admin 6 klasör),
rehber, `?inline=1` → `inline` / düz → `attachment`, SPA `/departman/finans` 200 (P2 açık → sekmeli; P1 ekranı
`make set-products PRODUCTS=P1` ile), onay akışı `finans` upload → `pending_metadata` (yönetim görmez) → submit →
`finans_mudur` kuyruğunda → approve → `yonetim` listede ve aramada görür; admin defteri `uploaded, submitted, approved`.
Rapor `docs/reports/AIBALBAL_MERGE_REPORT.md`.

**AI-BalBal PR #4 — iki küçük UX düzeltmesi (02.10.2026, `f3cba4b`):** `feat/ux-kucuk-duzeltmeler` @ `159b46c`
(https://github.com/ftansu/AI-BalBal/pull/4; main'e, merge edilmedi, T-12 tasarım onayı bekliyor). Tarayıcı testinden iki
gözlem: Ürün 1 giriş ekranından Belgeler'e görünür link yoktu → üst bara "Belgeler" linki (yalnızca o ekranda); onaylı
belgede "Durum: Taslak" yanıltıyordu → onay rozeti onaylıda da görünür ("Onaylı", yeşil). Backend'e dokunulmadı;
typecheck/lint/build yeşil. Rapor `docs/reports/AIBALBAL_UX_PR4_REPORT.md`.

**B-28b — ek alanlar, etiket kataloğu, tür rehberi (02.10.2026, `75234e6`, ADR-025):** `documents.extra_fields` JSONB
(`{key: {value, source: ai|user, confidence, added_by_id, added_at}}`, ≤20, snake_case, yalnızca metin), `tag_catalog`
(admin CRUD, katı doğrulama `unknown_tag`, AI önerisinde katalog dışı etiket `tags.dropped`), `document_type_guide` (10
aile; sınıflandırıcı promptu + yükleme ekranı için rehber, zorunlu form değil; `signals` ucu personelin sık eklediği
anahtarları sayar), `admin_events` (yapılandırma defteri), migration `0014` (veri adımı: 9 değişiklik etiketi + mevcut
11 etiket identity; seed aynı anlık görüntüyü verir). B-28 akışına entegre: `submit`/`apply`/`PATCH` `extra_fields` +
etiket doğrulaması, %80 kuralı `extra_fields.<key>` ile, `field_added` olayı. `/api/search` etiket + ek alan
(`matched_on`), `format_source` `Muhatap | Etiketler | Ek alanlar` satırı (sistem promptu değişmedi); retrieval
sıralaması değişmedi (Naci). Demo `parties` → `extra_fields.parties`. Ayrı bir phase değil; plan `docs/plans/B28B_PLAN.md`,
rapor `docs/reports/B28B_REPORT.md`. AI-BalBal tarafı PR-5 (ayrı).

**AI-BalBal PR #5 — B-28b arayüzü (02.10.2026, `3074598`):** `feat/b28b-arayuz` @ `1d4cca2` (https://github.com/ftansu/AI-BalBal/pull/5;
main'e, merge edilmedi, T-12 tasarım onayı bekliyor; PR #4'ten bağımsız, önerilen sıra #4 → #5). Etiketler katalogdan
çip seçiciyle (`TagPicker`; değişiklik etiketleri yalnızca `amendment` ailesinde açık), 1. aşama panelinde "Ek alanlar"
(Balbal önerisi güven çubuğu + %80 kuralı `extra_fields.<key>`, rehber satırları, "+ Alan ekle", kaynak rozeti
Balbal/Personel, ≤20), tür rehberi ipucu (Belge Yükle + panel aile rozeti), belge detayında ek alanlar herkese,
Yönetim › Etiketler ve Tür rehberi sayfaları (Sinyaller + "Rehbere ekle" yalnızca ön doldurma), arama `matched_on`
rozeti, admin'e `tags.dropped` notu. 3 CSS kuralı; typecheck/lint/build yeşil; dev Caddy'de geçici deploy → rotalar
200, pin `b709f09`'a geri. Backend'e dokunulmadı. Plan `docs/plans/AIBALBAL_PR5_PLAN.md`, rapor
`docs/reports/AIBALBAL_PR5_REPORT.md`.

**AI-BalBal PR #4 merge ve submodule pini (03.10.2026, `63efe16`):** Tansu PR #4 ve #5'i onayladığını söyledi;
`gh pr view` ile kontrol edildi — **PR #4 gerçekten `MERGED`** (merge commit `92bd778`); **PR #5 hâlâ `OPEN`**
(`mergedAt: null`, `reviews: []` — yorum olabilir, formal onay/merge yok). Naci'nin talimatıyla yalnızca PR #4
işlendi: `frontend-balbal` pini `b709f09` → `92bd778`; dev Caddy yeni sürümle kuruldu; canlı doğrulama PR #4
kapsamıyla sınırlı — SPA `/departman/finans` ve `/departman/finans/belgeler` 200, bundle'da "Belgeler"/"Onaylı"
string'leri, "Test Belgesi — Onay Akışı Denemesi" (`status=draft`, `review_status=approved`) PR #4'ün çözdüğü
senaryoyu canlı veride doğruladı. PR #5 (B-28b arayüzü) **pinlenmedi**, main'de yok. Rapor
`docs/reports/AIBALBAL_PR4_MERGE_REPORT.md`.

**AI-BalBal PR #5 merge ve submodule pini (03.10.2026, `9abcde0`):** `gh pr view 5` tekrar kontrol
edildi — `feat/b28b-arayuz` artık `MERGED` (merge commit `59421ed`). `frontend-balbal` pini `92bd778` →
`59421ed`; dev Caddy yeni sürümle kuruldu. Canlı doğrulama: Yönetim › Etiketler ve Tür rehberi sayfaları
200 + backend verisi (59 etiket, 10 aile); uçtan uca yükleme → gerçek LLM etiket/ek alan önerisi →
"Onaylıyorum" + "+ Alan ekle" ile submit (AI/kullanıcı kaynak ayrımı doğru, `extra_fields.source`) →
`finans_mudur` onayı; arama `matched_on` hem `content` hem `extra_field` için doğrulandı; Sinyaller ucu
elle eklenen anahtarı saydı. Test belgesi temizlendi (`documents` = 75). PR #4 ve #5'in ikisi de artık
main'de. Rapor `docs/reports/AIBALBAL_PR5_MERGE_REPORT.md`.

**Olası gelecek faz (kapsam dışı, planlanmadı): Ç-7.1 4 adımlı "veri yok" protokolü** — anlama kontrolü → durum etiketi
(`missing_data`/`insufficient_data` zaten ayrı) → "elimde şunlar var, göstereyim mi" (yalnızca `retrieved_document_ids`'ten
**kodla** üretilir, LLM'e yazdırılmaz — ADR-014) → açık uçlu kapanış. AI-BalBal `AnswerView` ile birlikte tasarlanmalı;
ayrı UX fazı, şimdi yapılmadı.

**Tarih/saat — demo takvimi vs gerçek takvim, tarih hesabının koda taşınması (05.10.2026, ADR-026):**
`app.services.temporal.today(settings)` tek giriş noktası (`demo_mode_enabled` bayrağı, varsayılan açık; kapatılınca
`company_timezone`'da gerçek gün — geri alma tek env değişkeni `DEMO_MODE=false`). `expiration_note()` saf fonksiyonu
kalan gün/süre dolmuş hesabını koda taşıdı (rule 3'ün tarihe uygulanması); `answer_prompt` rule 8 buna göre yeniden
yazıldı, model artık tarih farkını kendisi hesaplamıyor. `documents.expiration_date` ledger şemasına eklendi
(`Fact | None`, yeni doğrulama kuralı **C11**); 74 belgenin tamamına `expiration_date: null` yazıldı, **hiçbirine
gerçek tarih verilmedi**. Excel `outstanding_debt('today')` canlı hesaba çevrilmedi (V0 sadeliği) — bunun yerine
workbook'un kendi gömülü `Ledger_DemoToday`'i okunup sistemin bugünüyle karşılaştırılıyor, uyuşmazsa sessiz bayat
değer yerine açık "veri yok". "Bugünün tarihi nedir?" sorusu Ç-7'nin beş veri durumuna girmiyor (belge sorusu değil);
Naci kararı: yalnızca AI-BalBal'da küçük bir üst bar rozeti (`CurrentUser.today`/`demo_mode_enabled`, PR
`ftansu/AI-BalBal#8`, merge edilmedi) — backend'de kısa devre **yok**, Balbal bu soruya hâlâ "yeterli bilgi
bulamadım" diyor. **Aynı gün takip turu:** Naci üç adaydan **A**'yı (09.01.2025) onayladı; prose kaynağı
(`seed_data/generator/prose/DOC-ANK-OPS-009.yaml`) önce kontrol edildi — çelişkili bir süre/bitiş tarihi
içermediği doğrulandı, `make prose`/PDF yeniden üretimi yapılmadı. `DOC-ANK-OPS-009.expiration_date` ledger'a
yazıldı (`tag: AI_ASSUMPTION`, `note` alanında onay kaydı); `validate-ledger`/`lint` 0 hata; dev DB'deki tek satır
güncellendi (reseed gerekmedi, diğer 74 belge dokunulmadı); canlı doğrulama (`yonetim`, 2 LLM çağrısı): "Ankara
RES sigorta poliçesi bitmiş mi?" → "09.01.2025 tarihinde sona ermiştir" + doğru kaynaklar. Plan
`docs/plans/TARIH_SAAT_PLAN.md`, rapor `docs/reports/TARIH_SAAT_REPORT.md` (§9).

**Balbal davranış mantalitesi — Tansu Not 2 (05.10.2026, ADR-027, dal `feat/davranis-mantalitesi`, etiket
`pre-assist-mode`; `main`'e HENÜZ birleştirilmedi):** `ASSIST_MODE` bayrağı (varsayılan kapalı = bugünkü davranış
byte-identik; geri alma `.env` + `make restart-backend`). Açıkken cevap verilemeyen soruda sabit cümle `answer`'da
aynen kalır, yanına kodla üretilen `assist` bloğu gelir: eşleşmeyen terimler (yetkili belgelerde LIMIT-1 FTS sondası),
glossary'den yetkili belgelerde doğrulanmış aday terimler, "elimde şunlar var" (sıfır parçada metadata eşleşmesi,
yetersiz veride `retrieved_document_ids`'ten en iyi sayfa), tek netleştirme sorusu (sıfır parçada sabit şablon —
LLM yine çağrılmaz, ADR-021; yetersiz veride modelin `SORU:` satırı, rakam/tarih/para ve yetkisiz başlık denetiminden
geçmezse düşer). `AskWarning.kind` ve Ç-7 durumları değişmedi. Prompt'un bayraklı sürümü (`SYSTEM_PROMPT_ASSIST`):
rule 8 "Süre:" satırını kelimesi kelimesine kopyala, rule 11 tek soru; 1–7/9–10 aynı; örnek yok.
`audit_log.assist` (migration 0015). **Eval:** G1–G3 güvenlik değişmezleri (uydurma sayı/tarih yok — yazım
normalizasyonlu; kaynaksız cevap yok; yetkisiz/yanlış proje/yasak belge önerisi yok) her soruda %100 kapı;
`ambiguous`/`term_mismatch` kategorileri (≥%80) + `expect_assist`; `questions.json` v5 = 64 + 12 **TASLAK** soru
(5 belirsiz, 4 terim uyuşmazlığı, 1 rule 8, 2 negatif kontrol — Naci onayı bekliyor; LLM'siz kuru koşu yapıldı,
rapor §8). Aynı turda bulunan hata: `DEMO_MODE`/`ASSIST_MODE` env adları pydantic-settings tarafından okunmuyordu
(alan adı `*_ENABLED` bekleniyordu) — alias ile düzeltildi, test eklendi; `DEMO_MODE` kısmı `main`'e tek dosyalık
hotfix olarak alındı (`65c4ed9`). `partial` (kısmi cevap) Tansu Not 8 gelene kadar ertelendi; Not 7 kapsam dışı. Plan
`docs/plans/DAVRANIS_MANTALITESI_PLAN.md`, rapor `docs/reports/DAVRANIS_MANTALITESI_REPORT.md`.
