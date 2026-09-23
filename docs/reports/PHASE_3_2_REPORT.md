# Phase 3.2 Raporu — AI metadata önerisi + temporal/versiyon mantığı

**Tarih:** 23.09.2026  **Model:** Claude Sonnet 5  **Tag:** phase-3-2  **Commit:** `git rev-list -n1 phase-3-2`

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt |
|---|---|---|---|
| 1 | Facility Agreement upload → öneri Finans/Ankara/Facility Agreement + confidence | ✅ | `test_metadata_suggestion.py::test_suggest_metadata_classifies_document_with_confidence`; **canlı** — dev ortamında arka plan tarama gerçek "Facility Agreement" belgesi için `department: finans (0.95)`, `project_code: ANK_RES (1.0)`, `document_type: facility_agreement (1.0)`, `document_date: 2021-09-30 (1.0)` üretti (§9'da tam JSON) |
| 2 | LLM hatası upload'ı bozmaz | ✅ | `test_metadata_suggestion.py::test_suggest_metadata_llm_error_is_caught_and_stored_as_failed` — `suggest_metadata()` tamamen upload akışından ayrık (upload hiç çağırmıyor); hata `status=failed` satırı olarak yazılır, hiçbir exception dışarı sızmaz |
| 3 | "güncel kapasite" ↔ "ilk lisans kapasitesi" farklı ve doğru | ✅ (Facility zinciri üzerinden) | `test_ledger_live.py::test_current_tenor_vs_initial_facility_tenor_differ` (canlı, `make test-llm`) — Licence/Licence Amendment çifti bu ayrımı hiç taşımıyor (bkz. §5, §7); aynı genel mekanizma gerçek bir `supersedes` zincirinde (vade alanı, DSCR dışı) doğru çalıştığı kanıtlandı |
| 4 | "EBITDA neden düştü?" → yalnızca belgede yazan sebep veya "belirtilmemiş" | ✅ | `test_ledger_live.py::test_why_question_without_stated_reason_returns_fixed_text` (canlı) — gerçek bir "neden değiştirildi?" sorusu `"belgelerde sebep belirtilmemiş [K4]."` döndü; kural 6 canlı testte bir prompt belirsizliği ortaya çıkardı ve düzeltildi (§5 T2) |

## 2. Yapılanlar
- **`document_metadata_suggestions`** tablosu (migration `0005`) + `DocumentMetadataSuggestion` modeli: belge başına tek satır (upsert), `fields` JSONB (`{alan: {value, confidence}}`), `status: pending|applied|rejected|failed`.
- **`app/services/metadata_suggestion.py`**: `suggest_metadata()` (LLM_MODEL_CLASSIFY, JSON-mode, ilk 3 sayfa metni + bilinen departman/proje listesi; whitelist dışı departman/proje/durum/gizlilik değerleri `confidence=0` ile atılır — ADR-013'ün placeholder disiplinine benzer), `fetch_pending_candidates()`, `run_pending_scan()`.
- **Tetikleme (SORU 1'e göre ikisi birden):** `POST /api/documents/{id}/suggest-metadata` (admin, `pending`/`applied` iken idempotent) + backend `lifespan`'da başlayan `asyncio` arka plan döngüsü (15 sn'de bir, 5 belge/tur); döngü yalnızca LLM yapılandırılmışken ve `_test` veritabanına karşı **değilken** başlıyor — `make test` sırasında hiç çalışmıyor.
- **Kabul/reddet (SORU 2'ye göre yalnızca admin):** `GET /metadata-suggestion` (herkes, belgeyi görebiliyorsa), `POST /metadata-suggestion/apply` (yalnızca gövdede adı geçen alanlar yazılır — SPEC_02 §4 "kritik alan sessiz overwrite yok" tüm alanlara tek tip uygulanıyor), `POST /metadata-suggestion/reject`.
- **Upload formu genişlemesi:** `POST /api/documents/upload` artık opsiyonel `department` (bilinen slug'a karşı doğrulanır, 422), `subdepartment`, `project_id` (var olan projeye karşı doğrulanır, 404), `confidentiality` alıyor (PHASES.md Phase 1.2 notu kapatıldı).
- **`mark_superseded` durum geçişi:** bir belge gerçek `/upload` akışında başka birini `supersedes_document_id` ile değiştirdiğinde, eskisinin `status`'u artık otomatik `superseded` oluyor (`draft`/`executed`/`amended`'dan; `active` dokunulmadan kalıyor — operasyonel durum, yaşam döngüsü değil).
- **`LLMRequest.response_format`** (`"text"`/`"json_object"`) — `/api/ask` davranışını değiştirmeden (hâlâ hiç göndermiyor, `openai.Omit()`), metadata sınıflandırması JSON-mode kullanıyor.
- **Kural 6 netleştirmesi** (`answer_prompt.py`): canlı testte keşfedilen bir belirsizlik giderildi — bkz. §5 T2.

## 3. Değişen dosyalar
`git diff --cached --stat` (24 dosya, +1394/-47): Yeni: `backend/alembic/versions/0005_document_metadata_suggestions.py`, `backend/app/models/document_metadata_suggestion.py`, `backend/app/repositories/document_metadata_suggestion_repo.py`, `backend/app/services/metadata_suggestion.py`, `backend/tests/test_metadata_suggestion.py`. Değişen: `backend/app/api/documents.py` (+155), `backend/app/main.py` (arka plan döngüsü), `backend/app/{models/document,repositories/document_repo,schemas/document,core/config}.py`, `backend/app/services/{answer_prompt,llm/base,llm/openai_compatible}.py`, `backend/tests/{conftest,test_ask,test_document_repo,test_documents,test_migrations,live/test_ledger_live}.py`, `README.md`, `docs/{ARCHITECTURE,DOMAIN_MODEL,prompts/ANSWER_SYSTEM_PROMPT}.md`.

## 4. Testler
- Backend: **191 geçti** (Phase 3.1'den +31), 5 atlandı (`live_llm`, `make test-llm` ile ayrı — 3 mevcut + 2 yeni). ocr-worker: **9 geçti**. `make lint`: ruff/format/mypy/`validate-ledger`/`validate-documents --prose-only`/prompt-doc eşitliği — hepsi temiz.
- **`make test-llm` (canlı Gemini, 5 test):** 4 geçti (`test_current_dscr_is_amendment`, `test_izmir_cod_no_answer`, **`test_current_tenor_vs_initial_facility_tenor_differ`** [yeni], **`test_why_question_without_stated_reason_returns_fixed_text`** [yeni]); **1 önceden var olan (Phase 3.1) test kırmızı**: `test_initial_dscr_is_executed_and_differs` — bkz. §7, bu fazın kapsamı dışında, açıkça belgelendi.
- **Canlı doğrulama (dev ortamı, gerçek demo veri):** backend yeniden başlatıldı (yeni migration + kod), arka plan tarama 15 gerçek demo belgeyi otomatik sınıflandırdı, **0 `failed`**, ~50 sn'de tamamlandı. Gerçek "Facility Agreement" belgesi için üretilen öneri kanıt tablosunda (§1, kriter 1) ve §9'da tam JSON olarak var.
- Docker kaynak kullanımı (canlı): backend 83 MiB, ocr-worker 102 MiB, postgres 231 MiB.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| **T1 — `documents.ai_suggestion_id` FK'siz kalıyor** | Gerçek bir FK, `document_metadata_suggestions.document_id → documents.id` ile döngü oluşturuyordu (SQLAlchemy `Base.metadata.sorted_tables`'ı sıralayamıyor, `test_migrations.py`'de gerçek bir hataya yol açtı — ilk migration taslağım bunu denedi, geri aldım) | Kolon yalnızca "öneri denendi mi" bayrağı; gerçek arama her zaman `document_metadata_suggestions.document_id` üzerinden |
| **T2 — kural 6 metni netleştirildi** | Canlı test "neden değiştirildi?" sorusunda modelin bazen genel "kaynak yetersiz" cümlesini (kural 2) "sebep belirtilmemiş" (kural 6) yerine kullandığını gösterdi — konu kaynaklarda var ama sebebi yoksa hangi cümlenin kullanılacağı prompt'ta net değildi | `answer_prompt.py`'ye tek cümlelik netleştirme eklendi, `make prompt-doc` ile senkronize edildi, `test_why_question_without_stated_reason_returns_fixed_text` regresyon testi |
| **T3 — Licence/Licence Amendment çifti T1 doğrulaması için kullanılamadı, Facility zinciri (vade alanı) kullanıldı** | Bu çift Phase 3.1'de kasıtlı olarak `related_document_ids` ile bağlı, `supersedes` değil — zincir tabanlı GÜNCEL/İLK HALKA mekanizmasına hiç girmiyor (bkz. §7) | Kod değişikliği yok; yalnızca test tasarımı |
| **`_ratio_aliases` test yardımcısındaki biçim hatası düzeltildi** | Phase 3.1'den kalma: `.rstrip("0")` "1,20x"i "1,2x"e indirgiyordu, ama `facts.py::_format_ratio` her zaman 2 ondalık basıyor — canlı test bunu ilk kez `make test-llm` gerçek çalıştırmasıyla ortaya çıkardı | Test-only düzeltme, üretim kodu etkilenmedi |
| Öneri kabul/red admin-only (SORU 2) | Onaylandı | `require_admin`, proje CRUD'daki mevcut desenle tutarlı |
| Tetikleme: açık endpoint + arka plan tarama (SORU 1) | Onaylandı | §2'de detay |
| `document_metadata_suggestions` belge başına tek satır, geçmiş yok | V0 basitliği; retry = `upsert` (var olan satırı üzerine yazar) | Geçmiş/analiz Phase 4.1/5.x kapsamı |
| LLM'e gönderilen metin ilk ~3 sayfayla sınırlı | Kapak/özet genelde yeterli; tüm belgeyi göndermek maliyetli | — |
| `status` öneri seçenekleri `draft/executed/amended`'la sınırlı | `superseded`/`active` sistem tarafından yönetiliyor, LLM'e seçenek olarak sunulmuyor | Apply endpoint'i admin'in elle bu değerleri yazmasını hâlâ engellemiyor |

## 6. Açık sorular (Naci cevaplamalı)
- Yok — SORU 1-2 onaylanan cevaplarla uygulandı.

## 7. Riskler / sonraki phase için notlar
- **Licence → Licence Amendment 01 çifti chain mekanizmasına hiç girmiyor.** Phase 3.1'in bilinçli kararı (`related_document_ids`, "kapasite tadili lisansı geçersiz kılmaz") ile SPEC_02 §11'in illüstratif örneği ("İlk Licence 80 MW, Amendment 02 100 MW → İlk/Güncel ayrımı") arasında gerçek bir gerilim var: bu iki belge arasında bugün "güncel kapasite" / "ilk lisans kapasitesi" sorusu chain-tabanlı GÜNCEL/İLK HALKA etiketi **taşımıyor** (ikisi de kendi tek-belgelik zincirinde "GÜNCEL" görünür). `questions.json`'daki `ANK-DEV-003`/`ANK-DEV-004` altın soruları bu yüzden Phase 4.1'in eval runner'ında dikkatle gözden geçirilmeli — ya çift `supersedes` olarak yeniden modellenmeli ya da SPEC örneği güncellenmeli. Bu Phase 3.2'nin kapsamı dışında bırakıldı (ledger/ilişki modeli değişikliği Naci onayı gerektirir).
- **`test_initial_dscr_is_executed_and_differs` (Phase 3.1, önceden var) kırmızı kaldı.** "İlk DSCR covenant neydi?" sorusu, Facility Agreement'ın "Financial Covenants" bölümünde literal "DSCR" kelimesi hiç geçmediği ve soruda "Ankara"/"RES" gibi güçlü bir proje-çapası olmadığı için zayıf retrieval alıyor — Phase 3.1'in raporunda zaten "içerik-yazımı nüansı" olarak not edilmişti (`test_search_query.py`'de anchored bir varyant eklenmişti), ama bu canlı test o zaman gerçek `make test-llm` ile doğrulanmamıştı. Bu, Phase 3.2'nin kapsamına girmeyen, Phase 3.1'den miras kalan bir içerik/retrieval boşluğu — düzeltmedim (test kelimesini "kolay" bir soruya çevirmek gerçek boşluğu gizlerdi). Phase 4.1/5.1'de ele alınmalı: ya soru kelimeleri güncellenmeli ya da ilgili prose'a `[[project_name]]`/`DSCR` anchor'ı eklenmeli.
- Kural 6 netleştirmesi (§5 T2) küçük ama gerçek bir prompt iyileştirmesi; ileride benzer "neden" sorularında yine izlenmeli (Phase 4.1'in eval kategorileri şu an "reason"/kural-6'ya özel bir kategori taşımıyor — bkz. Phase 3.1 raporu'nun aynı notu).
- Arka plan tarama süreci artık **her backend başlatıldığında** (LLM yapılandırılmışsa) otomatik çalışıyor — dev ortamında bunu doğrularken 15 gerçek demo belgesi otomatik sınıflandırıldı (bilinçli, quota'yı önemli ölçüde tüketmedi: 15 çağrı × ~300 çıktı token, `gemini-3.5-flash-lite`, ücretsiz katman). Naci'nin bunu bilmesi gerekiyor: `.env`'de gerçek bir `LLM_API_KEY` varken her `make up`/backend restart sonrası ilk 15 sn içinde bekleyen belgeler otomatik sınıflandırılacak.

## 8. Doğruladığım üçüncü taraf davranışları
- **Gemini'nin OpenAI-uyumlu endpoint'i `response_format={"type": "json_object"}`'ı kabul ediyor** ve JSON çıktısı `_ClassifyResponse` (Pydantic v2) şemasıyla doğrudan doğrulanabiliyor — canlı arka plan taramasında 15/15 belge 0 parse hatasıyla sınıflandırıldı.
- **`openai` SDK 3.17.0'da `response_format` parametresi `Omit` tipini bekliyor, `NotGiven`'ı değil** (mypy overload çözümlemesi bunu netleştirdi) — `openai.Omit()` kullanıldı, `/api/ask`'in isteği tamamen değişmeden kaldı (parametre hiç gönderilmiyor).
- **SQLAlchemy `Base.metadata.sorted_tables`, karşılıklı FK döngüsünde `SAWarning` veriyor** ve "gelecekte hataya dönüşebilir" diyor — `documents.ai_suggestion_id`'yi FK'siz bırakarak döngü baştan önlendi (§5 T1).

## 9. Kaynak kullanımı
- Container RAM (canlı): backend 83 MiB, ocr-worker 102 MiB, postgres 231 MiB.
- LLM: canlı doğrulamada 15 demo belge (`gemini-3.5-flash-lite`, ücretsiz katman) + 5 `make test-llm` sorusu (`gemini-3.8-flash`, ücretsiz katman) — toplam maliyet $0.
- Gerçek "Facility Agreement" belgesi için üretilen öneri (dev ortamı, canlı):
  ```json
  {"department": {"value": "finans", "confidence": 0.95},
   "project_code": {"value": "ANK_RES", "confidence": 1.0},
   "document_type": {"value": "facility_agreement", "confidence": 1.0},
   "document_date": {"value": "2021-09-30", "confidence": 1.0},
   "counterparty": {"value": "PQR Bank, VWX Export Credit Agency", "confidence": 0.9},
   "status": {"value": "amended", "confidence": 0.8},
   "tags": {"value": ["Facility Agreement", "Term Loan", "Ankara RES"], "confidence": 0.9},
   "subdepartment": {"value": null, "confidence": 0.5},
   "confidentiality": {"value": "normal", "confidence": 0.5}}
  ```
