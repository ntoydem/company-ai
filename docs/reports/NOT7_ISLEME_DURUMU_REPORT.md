# Not 7 Raporu — Belge işleme durumu: "Son yüklenen belgeler" kartı + Balbal'ın "belge henüz işleniyor" cevabı

**Tarih:** 06.10.2026  **Model:** Fable 5.1  **Plan:** `docs/plans/NOT7_ISLEME_DURUMU_PLAN.md`  **Kaynak:** `docs/notes/Balbal_Not7_Not8_Gelistirici_Aciklama.docx` (Tansu v1.0, 05.10.2026) — yalnızca Not 7; Not 8 plan dışı.
**Dallar (Naci SORU 5):** dal 1 `feat/not7-isleme-durumu` (main'den; bayraksız: worker sınıflandırma, Türkçe neden eşlemesi, `/api/documents/recent`) → `ff97e7e`; dal 2 `feat/not7-balbal-davranisi` (`feat/davranis-mantalitesi`'nden türedi, dal 1 **merge** edildi; Durum A/B/C `ASSIST_MODE` arkasında) → bu dalın HEAD'i (`git log -1 feat/not7-balbal-davranisi`). Hiçbiri `main`'e birleştirilmedi. ADR-028.

## 0. Canlı backend hangi koddan çalışıyordu (Naci SORU 5, başlamadan önce)
- `backend` ve `ocr-worker` servisleri **bind-mount** çalışır (`./backend:/app`, `./ocr-worker:/worker`): canlı kod = o anki checkout; imaj yalnızca bağımlılıkları taşır; `uvicorn` reload'suz → kod değişikliği ancak **restart** ile canlıya geçer.
- Başlangıçta: backend konteyneri 17:34 UTC'de başlatılmış, checkout `feat/davranis-mantalitesi` @ `8baba16` (ADR-027 kodu, `.env` `ASSIST_MODE=false`, `DEMO_MODE=true`); worker konteyneri 26.09'dan beri çalışıyordu, imaj 25.09 (`8b5664b` sonrası, son worker commit'i) — Not 7 öncesi worker kodu.
- Bu turda: worker imajı dal 1 kodundan yeniden kuruldu (18:17 UTC); backend dal 2 kodundan yeniden başlatıldı (18:38 UTC, canlı doğrulama için `ASSIST_MODE=true`, sonra tekrar `false`). Canlı DB `alembic` 0015'te kaldı (dal 2'nin başı; dal 1 testleri için test DB geçici olarak 0014'e indirilip geri alındı).

## 1. Kabul kriterleri (Tansu §6, T7-1…T7-6)
| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| T7-1 | Finans kullanıcısı PDF yükler; ana ekranda Kuyrukta → İşleniyor → sayfa yenilemeden Hazır ✓ | ✅ backend yarısı (`card_state` geçişleri + kuyruk sırası + onaylayıcı) · ⏭ arayüz (AI-BalBal kartı ayrı PR, T-12) | `test_documents_recent.py::test_recent_card_states_follow_ingestion_job_and_review`, `…window_keeps_unresolved…`, `…limit…`; canlı: `/recent?department=finans` → `queued 1` (worker durdurulmuşken), `pending_approval/uploader`, `ready`, `failed` + neden |
| T7-2 | Okunamayan taranmış PDF → kırmızı etiket + sade Türkçe neden, teknik metin yok | ✅ | worker: `test_pipeline.py::test_blank_scanned_pdf_fails_with_code_no_text…`, `…encrypted…`, `…corrupt_pdf…`, `…corrupt_image…`; backend: `test_status_returns_turkish_reason_and_never_the_raw_code` (`exit code`/`Traceback`/kod substring'i yanıtta yok); canlı: parolalı PDF → `reason: "Belge parola korumalı olduğu için açılamadı…"`, boş tarama → "Taranmış sayfalarda okunabilir metin bulunamadı…" |
| T7-3 | İşlenmekte olan belgenin adını içeren soru → Görsel 3 (sabit cümle + sarı kutu + durum notu, "Veri yok" yok) | ✅ | `test_pending_documents.py::test_question_naming_a_processing_document_gets_state_a_without_an_llm_call` (LLM çağrısı 0, `warnings[0].kind=document_processing`, audit); canlı A: finans "Teminat mektubu tutarı nedir?" → `pending_notice` A cümlesi, kuyruktaki belge listede |
| T7-4 | Enerji kullanıcısı finansın işlenmekte olan belgesini sorar → belge adı hiçbir yerde geçmez, Durum D (G3) | ✅ | `…::test_other_departments_processing_document_is_never_mentioned` (JSON'da başlık substring testi); canlı D: enerji aynı soru → `pending_documents=[]`, `insufficient_data`, "Not7" yanıtta yok |
| T7-5 | Hazır belgeden cevap + aynı konuda işlenen yeni belge → Durum C notu | ✅ | `…::test_answered_question_with_a_processing_document_on_the_same_topic_gets_a_note`, `…::test_own_pending_upload_is_listed_but_its_text_never_reaches_the_prompt` (C + include_pending sızıntı testi) |
| T7-6 | İlgisiz belge işleniyor → anılmaz | ✅ | `…::test_unrelated_processing_document_is_not_mentioned` (proje adı/"RES" tek başına eşleşmez), `…old_processing_document_outside_the_window…`, `…at_most_three…` |
| Ek | Bayrak kapalı → yanıt bugünkü gibi | ✅ | `…::test_flag_off_carries_nothing_even_with_a_matching_processing_document` (audit `assist` NULL) + `test_assist.py::test_flag_off_keeps_todays_contract` |
| Ek | `include_pending` kapsamı retrieval'a sızmaz (Naci SORU 9) | ✅ | `…::test_own_pending_upload_is_listed_but_its_text_never_reaches_the_prompt`: onay bekleyen, chunk'lı belge listede **var**, prompt'ta ve `retrieved_document_ids`'te **yok** |
| Ek | Eşleme tablosu | ✅ | `test_reason_for_maps_known_codes…`, `test_unsupported_reason_names_the_real_formats_not_word` |
| Ek | 14 soruluk G1–G3 regresyonu (bayrak açık ×1) | G1–G3 **14/14 ✅** (`seed_data/evaluation/results/gemini-3.5-flash-lite_2026-10-06/`); hiçbir soruda `pending_documents` oluşmadı (demo korpusunda bekleyen belge yok). Kategori skorları: authorization 3/3, hallucination 4/4, comparison 2/3, isolation 3/4 — iki kayıp Not 7 dışı model/retrieval değişkenliği: ANK-ISO-002 cevabında yasak kaynak 'ÇED Süreci Durum Yazısı' alıntılandı (G3 assist/pending bloklarını ölçer, cevap alıntısı kategori puanı), GEN-CMP-003'te beklenen 'Licence Amendment 01' kaynağı gelmedi; prompt ve retrieval bu turda değişmedi, R1'de aynı 14 soru 42/42'ydi — tekrar koşulmadı (politika: tek koşu, G1–G3 temiz) | §4 |

## 2. Yapılanlar
**Dal 1 (bayraksız):**
- `ocr-worker/worker/errors.py` — kapalı kod kümesi `encrypted` / `corrupt` / `no_text` / `unknown`; `classify(exc)`; `NON_RETRYABLE`. `pipeline.py`: PDF için OCR öncesi `pymupdf.open` ön kontrolü (açılamıyorsa `corrupt`, kesin), OCR sonrası tüm sayfalar boşsa `no_text` (**önceden sessizce `ready` + 0 chunk oluyordu** — koddan doğrulandı, canlı dev verisinde böyle bir belge yoktu: 71 PDF'nin hepsi chunk'lı), `_handle_failure` artık metin değil **kod** yazar; kesin kodlar ilk denemede `failed`, `unknown` 3 deneme.
- `backend/app/services/ingestion_errors.py` — kod → sade Türkçe (`reason_for`); bilinmeyen/eski metin → genel cümle; "unsupported" metni PDF, resim (PNG/JPG), Excel, CSV (**Word yok**).
- `GET /api/documents/{id}/status`: `reason` (+ aynı metni taşıyan eski alan `ingestion_error`, deprecated — dağıtık AI-BalBal yükleme sekmesi bu alanı basıyor, bozulmasın diye); `DocumentDetailResponse`: `ingestion_reason` herkese, ham `ingestion_error` yalnızca admin (SORU 2).
- `GET /api/documents/recent?department=&limit=` — `/api/documents` ile aynı kapı (`include_pending`); son 7 gün + çözülmemişler; `failed` üstte (SORU 3); `card_state`, `queue_position` (worker'ın kuyruk sırası), `approver`, `reason`. `app/services/document_card.py`, `document_repo.list_recent/latest_jobs/queued_job_ids`.
- README, ocr-worker README, ADR-028.

**Dal 2 (`ASSIST_MODE` arkasında):**
- `backend/app/services/pending_documents.py` — cevaptan **sonra**, LLM'siz: aday küme `allowed_document_ids(user, AuthorizationScope(department, include_pending=True))` (liste/kart ile aynı), yalnızca `uploaded/ocr` (7 gün) ve `failed` (süresiz), retrieval'ın okuduğu belgeler hariç; eşleştirme `question_terms` (≥4 karakter, `GENERIC_TERMS` ve proje kelimeleri hariç) × `search_metadata` (başlık/tür/muhatap/etiket/ek alan); en yeni 3. `resolve` → A/B/C/D; cümleler kod sabiti.
- Sözleşme (additive): `AskResponse.pending_notice`, `pending_documents[]` (`PendingDocumentCard`: id, başlık, durum, yüklenme zamanı, departman, `reason`); `AskWarning.kind` + `document_processing` / `document_unreadable` (`message` = Ç-7 notu "Hazır (işlenmiş) belgelerde bu soruya ait bilgi bulunmuyor.", `action` yok). `answer` sabit cümle **aynen** (SORU 6-i); ADR-027 assist bloğu A/B'de de döner (SORU 7). Audit: `audit_log.assist` JSON'una `pending_state/notice/documents` (migration yok, SORU 8).
- Eval: `AskOutcome.pending_documents`; G3 bekleyen belgelere de uygulanır (görünür küme + `forbidden_sources`); `run_eval` alanı kaydeder; `test_eval_lib.py::test_safety_g3_covers_not7_pending_documents`.
- Prompt **değişmedi** (model bu belgeleri görmez).

## 3. Değişen dosyalar
Dal 1 (`main..ff97e7e`): 14 dosya, +883/−43 — `ocr-worker/worker/{errors,pipeline}.py`, `ocr-worker/tests/{test_errors,test_pipeline}.py`, `backend/app/services/{document_card,ingestion_errors}.py`, `backend/app/api/documents.py`, `backend/app/repositories/document_repo.py`, `backend/app/schemas/document.py`, `backend/tests/test_documents_recent.py`, README'ler, ADR-028.
Dal 2 (dal 1 + davranis üzerine): 12 dosya, ~+330 — `backend/app/services/pending_documents.py` (yeni), `backend/tests/test_pending_documents.py` (yeni), `backend/app/{api/ask,schemas/ask,services/ask_router,services/audit_writer,repositories/document_repo}.py`, `scripts/{eval_lib,run_eval}.py`, `backend/tests/test_eval_lib.py`, README, ADR-028 (part 2), PHASES, bu rapor.

## 4. Testler ve ölçüm
- Dal 1 `make test`: backend **517 passed** (15 deselected live_llm), şema doğrulaması OK, ocr-worker **18 passed** (6 yeni: şifreli/bozuk PDF/bozuk PNG/boş tarama gerçek fixture'larla, `unknown` 3 deneme monkeypatch ile, saf sınıflandırma). `make lint` (ruff + mypy strict + worker ruff) temiz.
- Dal 2 `make test`: backend **547 passed** (15 deselected live_llm; +30: `test_pending_documents.py` 12, `test_eval_lib.py` +1, dal 1'in 17'si), şema doğrulaması OK, ocr-worker **18 passed**; 11 dk 23 sn. `make lint` temiz.
- **Canlı worker doğrulaması** (dal 1 imajı, gerçek yükleme `finans` ile, 18:18 UTC): dijital PDF → `ready` (1 chunk); parolalı PDF → `failed` / `encrypted` / 1 deneme (ocrmypdf exit 8); boş tarama → `failed` / `no_text` / 1 deneme. Worker logu: `code`, `final`, `error=repr(exc)` (yalnızca log).
- **Canlı Durum A/B/D** (dal 2, `ASSIST_MODE=true`, 18:38–18:41 UTC, 3 LLM çağrısı): worker durdurulup "Not7 Teminat Mektubu Taslağı" yüklendi (kuyrukta kaldı) → finans "Teminat mektubu tutarı nedir?" → **A** (`document_processing`, A cümlesi, kuyruktaki belge); finans "canlı encrypted belgesinde ne yazıyor?" → **B** (`document_unreadable`, iki okunamayan belge + nedenleri; ham kod yok); enerji aynı teminat sorusu → **D** (`insufficient_data`, `pending_documents=[]`, finans belgesinin adı yanıtta yok). Sonra 4 geçici belge + dosyaları + 3 test audit satırı silindi (orphan job/chunk 0), worker yeniden başlatıldı.
- **G1–G3 regresyonu** (R1'in 14 sorusu × 1, bayrak açık, flash-lite): G1–G3 **14/14 ✅** (`seed_data/evaluation/results/gemini-3.5-flash-lite_2026-10-06/`); hiçbir soruda `pending_documents` oluşmadı (demo korpusunda bekleyen belge yok). Kategori skorları: authorization 3/3, hallucination 4/4, comparison 2/3, isolation 3/4 — iki kayıp Not 7 dışı model/retrieval değişkenliği: ANK-ISO-002 cevabında yasak kaynak 'ÇED Süreci Durum Yazısı' alıntılandı (G3 assist/pending bloklarını ölçer, cevap alıntısı kategori puanı), GEN-CMP-003'te beklenen 'Licence Amendment 01' kaynağı gelmedi; prompt ve retrieval bu turda değişmedi, R1'de aynı 14 soru 42/42'ydi — tekrar koşulmadı (politika: tek koşu, G1–G3 temiz).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `corrupt` yalnızca PyMuPDF `FileDataError/EmptyFileError` (PDF ön kontrol) ya da `FzErrorFormat` (resim dönüşümü); ocrmypdf exit 2 → `unknown` | exit 2 (`input_file`) DPI/font/imza hatalarını da kapsıyor — "kesin değilse unknown" (SORU 4) | bozuk JPEG'ler (`FzErrorLibrary`) 3 deneme sonra `unknown` + genel cümle |
| `encrypted` tek kaynak: ocrmypdf exit 8 | kurulu 17.12.1'de `ExitCode.encrypted_pdf == 8` doğrulandı; PyMuPDF `needs_pass` ikinci bir yol olurdu ama gerek yok | — |
| Hata kodu için yeni kolon yok; `ingestion_error` kodu taşır | plan | eski satırlardaki cümle genel cümleye eşlenir |
| `/status.ingestion_error` korunup `reason` ile aynı metni taşıyor (deprecated) | dağıtık AI-BalBal `UploadTab` bu alanı gösteriyor; kaldırılsa hata satırı boş kalırdı | AI-BalBal PR'ında `reason`'a geçilince kaldırılabilir; `DocumentDetailPanel` admin olmayanlar için artık boş → `ingestion_reason`'a geçmeli |
| `card_state` için iş satırı (`queued`/`running`) kullanılıyor | `ingestion_status=uploaded` OCR sırasında da aynı kalıyor; "Kuyrukta" ile "İşleniyor" ayrımı ancak `ingestion_jobs.status` ile mümkün | — |
| Retrieval'ın okuduğu belgeler bekleyen listesinden hariç | test yardımcısı `uploaded` durumlu chunk'lı belge yaratınca "okunan belge işleniyor" çelişkisi çıktı; prod'da olmaz ama savunma ucuz | — |
| Kesin olmayan eşleşmede proje kontrolü yok (bekleyen belgede proje meta verisi henüz boş olabilir); proje adı tek başına eşleşmez | G3 eval'de `pending_documents` için proje testi yapılmıyor, görünürlük + yasak kaynak yapılıyor | — |
| Dal 2, dal 1'i merge ederek içeriyor | Durum B'nin `reason` alanı dal 1'in eşlemesine bağlı | `main`'e sıra: önce dal 1, sonra davranis, sonra dal 2 (ya da dal 2 tek seferde) |
| Rapor ve PHASES notu yalnızca dal 2'de | dal 2 ikisini de kapsıyor | dal 1 tek başına birleşirse PHASES notu ayrıca taşınmalı |

## 6. Açık sorular (Naci)
- Birleştirme sırası ve `assist-mode-1` etiketi (ADR-027 ile birlikte).
- AI-BalBal PR'ı: kart bileşeni (`/recent`, 5 sn yoklama), `UploadTab`/`DocumentDetailPanel` → `reason`/`ingestion_reason`, cevap kutuları (sarı/kırmızı, Durum C notu), A/B'de ADR-027 netleştirme sorusunu gizleme kararı (SORU 7 — arayüz).
- Tansu'ya not: belgedeki "PDF, Word veya Excel olarak yükleyin" ifadesi düzeltildi — Word hiç desteklenmiyor (415); doğru metin "PDF, resim (PNG/JPG), Excel veya CSV".

## 7. Riskler / sonraki adım notları
- `no_text` artık bir hata: tamamen boş çıkan taramalar `failed` olur; gerçek sahada düşük kaliteli taramalar "kısmen boş" çıkarsa yine `ready` olur (yalnızca **tüm** sayfalar boşsa hata).
- `queue_position` tek worker varsayımıyla (`created_at` sırası); birden fazla worker'da yaklaşık.
- Bildirim satırı (B-02) bu turda yok; Not 8 ayrı plan.

## 8. Doğruladığım üçüncü taraf davranışları
- ocrmypdf 17.12.1 (konteynerde): `ocrmypdf.exceptions.ExitCode` — `encrypted_pdf=8`, `input_file=2` (DpiError, NonEmbeddedFontsError, DigitalSignatureError, UnsupportedImageFormatError de 2 döndürür), `already_done_ocr=6`; parolalı PDF gerçekten 8 ile çıktı; `%PDF-1.4\ngarbage` 2 ile çıktı.
- PyMuPDF 1.28.2: bozuk PDF `pymupdf.FileDataError`; bozuk PNG `open` başarılı, `convert_to_pdf` → `pymupdf.mupdf.FzErrorFormat` ("premature end of data in png image"); bozuk JPEG → `FzErrorLibrary` (bu yüzden `unknown`); `doc.save(encryption=PDF_ENCRYPT_AES_256, user_pw=…)` ile şifreli fixture.

## 9. Kaynak kullanımı
- RAM (docker stats): backend 31 MiB, ocr-worker 76 MiB, caddy 11 MiB, postgres ~1 GiB.
- LLM: canlı doğrulama 3 çağrı + regresyon 14 çağrı (flash-lite); worker doğrulaması LLM'siz.

## 10. Birleştirme öncesi kontrol ve birleştirme (Naci, 06.10.2026 — ikinci tur)

**1. İki kayıp sorunun ×3 tekrarı, bayrak kapalı / açık (dal 2 checkout'u, flash-lite, 12 çağrı):**

| Soru | Ölçüt | Bayrak KAPALI (×3) | Bayrak AÇIK (×3) |
|---|---|---|---|
| ANK-ISO-002 "Hangi projenin üretim lisansı var?" | yasak kaynak `ÇED Süreci Durum Yazısı` alıntılandı | **2/3** (18:55:44, 18:56:36) | **1/3** (18:59:06) |
| GEN-CMP-003 "…kurulu gücü hangisi daha büyük?" | beklenen `Licence Amendment 01 (Kapasite Tadili)` kaynağı gelmedi | **2/3** (yalnızca 18:57:54'te geldi) | **3/3** |
| Her ikisi | G1–G3 | 6/6 ✅ | 6/6 ✅ |

Kaynak: `audit_log.sources` (kapalı: `consistency_185756`, açık: `consistency_190053`; tutarlılık modu kaynak kuralını puanlamadığından alıntılar denetim kaydından okundu). Kapalıyken de aynı düşme var → **model/retrieval değişkenliği**, assist/Not 7 ile ilgisi yok; birleştirmeye engel yok. Yan gözlem (ADR-027'den beri, bu turda değişmedi): `audit_log.assist` boşken SQL `NULL` değil JSON `null` yazılıyor (`jsonb_typeof = 'null'`, 97 satır; 0015 öncesi 783 satır SQL NULL) — ORM her ikisini `None` okur, davranış etkilenmez; istenirse `JSONB(none_as_null=True)` ile tek satırlık düzeltme.

**2.** Tansu'nun docx'i commit edildi (`7e5c4ca`, dal 2 → main).

**3. Birleştirme sırası ve sonuçlar (hepsi bayrak kapalı):**

| Adım | Birleştirme | Commit | `make test` | `make lint` |
|---|---|---|---|---|
| 1 | `feat/not7-isleme-durumu` → `main` (fast-forward) | `ff97e7e` | backend 517 ✅, worker 18 ✅ (test DB geçici 0014) | ✅ |
| 2 | `feat/davranis-mantalitesi` → `main` (`docs/ARCHITECTURE.md` çakışması: ADR-027 önce, ADR-028 sonra) | `eec10bf` | backend 535 ✅, worker 18 ✅ (test DB 0015'e alındı) | ✅ |
| 3 | `feat/not7-balbal-davranisi` → `main` | `bbf67fe` (`docs/ARCHITECTURE.md` çakışması: dal 2 sürümü alındı; `git diff feat/not7-balbal-davranisi main` boş) | backend 547 ✅, worker 18 ✅ | ✅ |

Etiket: `assist-mode-1` → `bbf67fe`, `origin/main` ve etiket push edildi.

**4. VM `main`'de:** checkout `main` @ `bbf67fe`; `make restart-backend` (19:36 UTC) → `get_settings()`: `assist_mode_enabled=False`, `demo_mode_enabled=True`. Bayrak kapalı `/api/ask` örneği (enerji, GEN-TRM-002 "İzmir RES türbin tedarikçisi kim?") R0'daki (eski `main` kodu, 06.10 sabahı) kayıtla karşılaştırıldı: `answered=false`, `answer` sabit cümle, `cited_titles=[]`, `query_type=DOCUMENT_QUERY`, `assist=null` — **ortak alanlar birebir aynı**; yalnızca ek anahtarlar `pending_notice=null`, `pending_documents=[]` (additive). (İlk deneme ANK-AUT-001'de router bu kez `MIXED_QUERY` dedi — router değişkenliği, bayrakla ilgisiz; o yüzden ikinci soru gösterildi.) Worker: `up -d --build ocr-worker` (imaj 19:37 UTC); konteynerdeki `worker/errors.py` ve `worker/pipeline.py` md5'leri `main` ile aynı; `errors` modülü yüklü. Not: canlı worker **bind-mount** olduğundan imaj yalnızca bağımlılık taşır, kod checkout'tan gelir.

**5. LLM'siz tarama (canlı DB, `ingestion_status=ready`, Excel/CSV hariç):** 76 `ready` belge (72 PDF/resim + 4 Excel). Chunk'sız: **0**; sayfasız: **0**; tüm sayfaları boş: **0** → Not 7'nin `no_text` kapsamına girecek belge **yok**. En az bir boş sayfası olan: **1** — `fatura` (external_ref yok, elle yüklenmiş test belgesi; 2 sayfa, 2. sayfa boş, 1 chunk) → kapsam dışı (yalnızca tüm sayfalar boşsa hata). `failed`/`uploaded`/`ocr`: 0. Düzeltme yapılmadı.
