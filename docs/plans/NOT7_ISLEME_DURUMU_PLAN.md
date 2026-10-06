# Not 7 — Belge işleme durumu: "Son yüklenen belgeler" kartı + Balbal'ın "belge henüz işleniyor" cevabı — Uygulama Planı

**Tarih:** 06.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.** · **Kapsam:** yalnızca **Not 7** (belge: `docs/notes/Balbal_Not7_Not8_Gelistirici_Aciklama.docx`, Tansu v1.0 05.10.2026, §2–§3, §5 SORU 1, §6 T7-1…T7-6). **Not 8 plan dışı** (Anayasa Ü-3 sorusu Tansu'da). · **Bayrak:** `ASSIST_MODE` (Tansu SORU 1 cevabı: DAVRANIS planıyla aynı bayrak) · **Ürün:** Ürün 1 — Tanıma, her pakette · **Dal:** `feat/davranis-mantalitesi` üzerine (ADR-027 sözleşmesini genişletir) ya da ondan türeyen `feat/not7-isleme-durumu` — SORU 5

Kaynak: Tansu'nun belgesi (öncelik: Anayasa > Süreç Haritası > bu belge > backend notları; çelişkide Tansu'ya sorulur); CLAUDE.md kural 1 (SECURITY), 2, 4, 6; ADR-004 (tek kapı), ADR-006 (ingestion kuyruğu), ADR-014 (sabit metinler), ADR-021 (retrieval yalnızca hazır/onaylı/yetkili), ADR-024 (`review_status`), ADR-027 (assist bloğu, kod mülkiyeti); `docs/plans/DAVRANIS_MANTALITESI_PLAN.md` §2 (anahtar terim çıkarımı, `search_metadata`), T9 (çok turlu hafıza yok).

---

## 0. Tespitler (bugünkü kod)

- **T1 — Durum bilgisi var, ekrana ve cevaba yansımıyor.** `Document.ingestion_status` (`uploaded / ocr / ready / failed`), `ingestion_error`, `review_status` (`pending_metadata / pending_review / changes_requested / approved`), `created_at`, `uploaded_by_id`, `submitted_at`. `GET /api/documents` (`include_pending=True` kapısı) `ingestion_status`, `review_status`, `created_at`, `department`, `file_kind` döndürüyor; **`ingestion_error` yalnızca `GET /api/documents/{id}/status`'ta** ve ham metin. Arayüzde (AI-BalBal) yalnızca `UploadTab` o anki tek belgeyi 3 sn'de bir yokluyor (`useDocumentStatus`); Ürün 1 ana ekranında (`pages/urun1/Urun1Home.tsx`) durum bilgisi yok. Tansu'nun teşhisi doğru.
- **T2 — Hata nedeni bugün tek ve genel.** `ocr-worker/worker/pipeline.py`: her istisna geniş `except Exception` ile yakalanır, 3 denemeden sonra `ingestion_status=failed`, `ingestion_error=FAILURE_MESSAGE` = "Belge işlenirken bir hata oluştu." — **hata sınıfı saklanmıyor.** Tansu'nun eşleme tablosu (taranmış sayfada metin yok / parola / bozuk / desteklenmeyen) için worker'ın önce hatayı **sınıflandırması** gerekir. "Desteklenmeyen biçim" ise worker'a hiç ulaşmaz: yükleme zaten `415` ile reddediyor (PDF, PNG/JPG, xlsx/xlsm, csv beyaz listesi — **Word yok**). Tansu belgesindeki "PDF, Word veya Excel olarak yükleyin" ifadesi **yanlış**; doğru metin: "PDF, resim (PNG/JPG), Excel veya CSV".
- **T3 — Yetki kapısı hazır olmayan belgeyi zaten kapsıyor.** `SqlDocumentIdsProvider.list_document_ids` yalnızca `review_status`'a bakar (`include_pending` ile pending de girer), `ingestion_status`'a bakmaz → `uploaded/ocr/failed` belgeler, kullanıcı görmeye yetkiliyse `/api/documents` listesinde zaten var. Retrieval ise yalnızca `document_chunks` üzerinden çalışır ve hazır olmayan belgenin chunk'ı yoktur → Balbal'a hiç girmez (ADR-021, doğru). Yani Not 7 **yeni görünürlük açmaz**; kart ve cevap, `/api/documents`'ın gördüğü kümeyi gösterir.
- **T4 — Kuyruk sırası hesaplanabilir.** `ingestion_jobs(status, created_at)` indeksli; "Sırada N." = aynı anda `queued` olan, daha erken `created_at`'li iş sayısı + 1. Ucuz, LLM'siz.
- **T5 — Balbal cevabına ekleme noktası hazır.** ADR-027 ile `AskResult.assist` → `RoutedAnswer` → `AskResponse` hattı ve `ask_router._run`'daki "cevap yok → uyarı" dalı var; Not 7'nin `pending_documents` bloğu aynı yerde, aynı kod-mülkiyeti ilkesiyle eklenir. `AskWarning.kind` kapalı `Literal` (3 değer), AI-BalBal `AnswerView` `kind`→etiket eşlemesi (`strings.ts`: "Veri yok", "Yeterli veri bulunmamaktadır", "Paket sınırı").
- **T6 — Onay bekliyor kimde:** `pending_metadata` / `changes_requested` → yükleyen; `pending_review` → hedef departmanın `department_manager`'ı (`document_review.py`). Kart alt satırı buradan türetilir.
- **T7 — Bildirim altyapısı yok** (B-02 `useNotifications` `proposed.ts`'te) → Tansu'nun "bildirim seçeneği" satırı ve zil bildirimi **bu turda yok** (Naci madde 6); kart ve cevap bildirimsiz tasarlanır, alan boş kalır.

---

## 1. Ekran A — "Son yüklenen belgeler" kartı: liste/durum ucu

**Neden yeni uç (mevcut `/api/documents` yerine):** liste ucu `ingestion_error`'ı taşımıyor, "son 7 gün + çözülmemişler kalır" kuralı ve kuyruk sırası sunucuda hesaplanmalı (istemci tüm listeyi çekip süzmek zorunda kalmasın; `/api/documents` 75+ belge döner). Yetki kapısı **aynı**.

**`GET /api/documents/recent?department=<slug>&limit=5`** (varsayılan 5, en çok 20):

- Kapı: `allowed_document_ids(user, AuthorizationScope(department=…, include_pending=True), provider)` — `/api/documents` ile **birebir aynı çağrı**; yetkisiz belge adı asla dönmez (G3).
- Seçim: `department` eşleşen, `created_at >= now − 7 gün` belgeler; **artı** 7 günü geçmiş olsa da `ingestion_status ∈ {uploaded, ocr, failed}` olanlar (Tansu: "sorun çözülene kadar listede kalır"). Sıralama: yeniden eskiye; `failed` satırları üstte (Tansu önerisi, SORU 3). `limit` uygulanır.
- Satır şeması (`RecentDocumentItem`, additive, yeni):

```
{ document_id, title, document_type, file_kind, created_at, uploaded_by_id,
  ingestion_status, review_status,
  card_state: "queued" | "processing" | "pending_approval" | "ready" | "failed",
  queue_position: int | null,          # yalnızca queued
  approver: "uploader" | "department_manager" | null,   # yalnızca pending_approval
  reason: str | null }                 # yalnızca failed — sade Türkçe (bölüm 2), ASLA ham hata
```
- `card_state` türetimi (kod, tek yer `services/document_card.py`): `uploaded→queued`, `ocr→processing`, `failed→failed`, `ready` + `review_status≠approved→pending_approval`, `ready`+`approved→ready`. "Balbal kullanabilir" = `card_state == "ready"` (ADR-021/024 ile aynı koşul).
- "Tahmini: birkaç dk" **yazılmaz** (süre bilinmiyor; Tansu: uydurulmaz). Boş liste → `[]`; arayüz "Bu departmana son 7 günde belge yüklenmedi." yazar.
- Canlı güncelleme: arayüz, listede `queued/processing` varken 5 sn'de bir yeniler (mevcut `useDocumentStatus` deseni); sunucu tarafında ek bir şey yok.

**Bayrak:** bu uç salt okunur ve bugünkü görünürlük kümesini gösterir → **bayraksız** olması önerilir (kart Ürün 1 arayüz işi, davranış değişikliği değil) — SORU 1. Bayraklanacaksa `ASSIST_MODE=false` iken 404 değil **boş liste** döner (istemci kırılmaz).

## 2. `ingestion_error` → sade Türkçe eşleme

İki parça: (a) **worker sınıflandırır**, (b) **backend çevirir**. Kullanıcı hiçbir zaman ham metin görmez (Tansu "Önemli").

**(a) Worker (`ocr-worker/worker/pipeline.py`, `_handle_failure`):** geniş `except` korunur ama hata **koda** çevrilir ve `documents.ingestion_error`'a kod yazılır (metin yerine; ham `repr(exc)` yalnızca JSON log'da kalır — bugün de öyle). Yeni kolon **yok**: `ingestion_error` zaten serbest metin; değer artık şu kapalı kümeden biri olur:

| Kod (`ingestion_error`) | Worker'da nasıl tespit edilir | Kullanıcıya gösterilecek neden (backend eşlemesi) |
|---|---|---|
| `no_text` | OCR bitti, PyMuPDF sayfa metinlerinin tamamı boş/boşluk (`page_texts` toplam uzunluğu 0) — bugün bu durum "ready, 0 chunk" olarak **sessizce geçiyor olabilir**, kontrol edilecek (T7-2 için gerekli) | "Taranmış sayfalarda okunabilir metin bulunamadı. Daha net bir tarama yükleyin." |
| `encrypted` | `ocrmypdf` çıkış kodu / stderr'de `EncryptedPdfError` / "password" (ocrmypdf exit code 8 = `EncryptedPdfError` — resmi dokümandan doğrulanacak, **uydurulmayacak**) | "Belge parola korumalı olduğu için açılamadı. Parolasız halini yükleyin." |
| `corrupt` | `ocrmypdf` `InputFileError` (exit code 2) ya da PyMuPDF `open()` hatası | "Dosya bozuk görünüyor, açılamadı. Dosyayı kontrol edip tekrar yükleyin." |
| `unsupported` | **Worker'a ulaşmaz**: yükleme `415` verir; arayüz 415 mesajını gösterir. Eşleme tablosunda yine de bulunur (eski/elle değişmiş kayıtlar için) | "Bu dosya türü desteklenmiyor. PDF, resim (PNG/JPG), Excel veya CSV yükleyin." (**Word yok** — Tansu metni düzeltildi) |
| `unknown` (ve bugünkü eski "Belge işlenirken bir hata oluştu." satırları) | diğer her şey | "Belge okunamadı. Dosyayı kontrol edip tekrar yükleyin." |

`MAX_ATTEMPTS` (3) ve retry davranışı değişmez; `encrypted`/`corrupt`/`unsupported` **yeniden denenmez** (deterministik hatalar — SORU 4: 3 deneme boşuna; worker'da `NON_RETRYABLE` kümesi).

**(b) Backend (`app/services/ingestion_errors.py`, yeni, saf):** `reason_for(code: str | None) -> str | None`; eşleşmeyen her şey genel cümle. `DocumentStatusResponse`'a `reason` eklenir (`ingestion_error` ham alanı **admin dışına kapatılır** — SORU 2: ya alan listeden çıkar ya yalnızca admin görür). Kart ucu yalnızca `reason` taşır. `ocr-worker/tests/test_pipeline.py`'e kod sınıflandırma testleri, backend'e eşleme birim testi.

**Yükleme ekranı (`UploadTab`):** 415 metni zaten var; "Daha net bir tarama yükle" bağlantısı Belge Yükle sayfasına gider (arayüz işi, ayrı PR).

## 3. Davranış B — Balbal cevabı: Durum A/B/C/D, LLM'siz

**Yer:** `ask_router._run`, mevcut cevap üretildikten **sonra**, ek LLM çağrısı **yok**. Model bu belgelerden habersizdir (prompt'a girmez; Tansu "model … onlar hakkında hiçbir şey yazmaz").

**Aday küme:** `allowed_document_ids(user, AuthorizationScope(department=request.department, include_pending=True), provider)` — kart ve `/api/documents` ile **aynı kapı** (G3; retrieval kapısından farkı yalnızca `include_pending`: kullanıcının zaten listede gördüğü kendi bekleyen yüklemeleri). Bu kümeden `ingestion_status ∈ {uploaded, ocr, failed}` ve `created_at >= now − 7 gün` olanlar. Boşsa Not 7 **devreye girmez** (sorgu maliyeti: tek `SELECT`).

**Eşleştirme (yalnızca meta veri):** sorunun anahtar terimleri `question_terms()` ile; `GENERIC_TERMS` ve `project_words()` dışı, **≥ 4 karakter** terimler; her terim için `document_repo.search_metadata(session, pending_ids, term, limit=3)` (başlık / tür / muhatap / tag / ek alan ILIKE — ADR-027'deki aynı fonksiyon). Proje adı tek başına eşleştirmez ("Ankara" → her Ankara belgesi değil; Tansu: "her soruya liste basılmaz"). Eşleşen belgeler `created_at` desc, **en çok 3** (Tansu madde 2).

**Durum tablosu (kod, `services/pending_documents.py`):**

| Durum | Koşul | `answer` | `warnings` | Yeni alanlar |
|---|---|---|---|---|
| **A** | `answered=false` + eşleşen `uploaded/ocr` var | **SORU 6:** (i) sabit cümle `NO_ANSWER_TEXT` **kalır**, Not 7 cümlesi ayrı alanda; ya da (ii) `answer` Not 7 cümlesi olur | `missing_data/insufficient_data` yerine **`document_processing`** (message = "Hazır (işlenmiş) belgelerde bu soruya ait bilgi bulunmuyor." — Ç-7 durum notu, Tansu madde 4) | `pending_notice` = "Bu sorunun cevabı henüz işlenmekte olan bir belgede olabilir. Belge hazır olduğunda tekrar sorarsanız cevaplayabilirim." · `pending_documents[]` (≤ 3) |
| **B** | `answered=false` + eşleşen `failed` var (A ile çakışırsa A önce; B'nin belgeleri de listede) | aynı seçim | **`document_unreadable`** (message aynı Ç-7 notu) | `pending_notice` = "Bu soruyla ilgili olabilecek bir belge sistemde var ama okunamadığı için içeriğini kullanamıyorum." · `pending_documents[]` (`reason` dolu) |
| **C** | `answered=true` + eşleşen `uploaded/ocr` var | normal cevap, kaynaklar | değişmez | `pending_notice` = "Bu konuyla ilgili şu belge henüz işleniyor; işlendiğinde cevap değişebilir: <başlık>" (kod, başlık(lar) kodla doldurulur) · `pending_documents[]` |
| **D** | eşleşen belge yok | bugünkü davranış + ADR-027 assist | değişmez | `pending_documents: []`, `pending_notice: null` |

- **Tüm cümleler kod sabiti** (`services/pending_documents.py`), model hiçbir şey yazmaz; `pending_notice` içinde belge başlığı dışında hiçbir değişken yok.
- **Durum A/B'de ADR-027 assist bloğu da üretilir mi?** Üretilir ama **gösterim önceliği** Not 7'de (arayüz: `pending_notice` varken assist'in netleştirme sorusu ikinci sırada / gizli — SORU 7). Backend ikisini de döndürür; karar arayüzde değil, sözleşmede netleşsin.
- **Yetki (G3):** `pending_documents` yalnızca aday kümeden; `enerji` kullanıcısı finansın işlenmekte olan belgesini **hiçbir alanda** görmez (T7-4). `pending_notice` belge adı taşıdığından aynı kümeden gelir.
- **Audit (kural 4):** `audit_log.assist` JSON'una `pending_documents`/`pending_notice` de yazılır (ADR-027 kolonu yeniden kullanılır; migration yok) — kullanıcı ne gördüyse o. Ayrı kolon istenirse migration `0016` (SORU 8).
- **Zaman penceresi 7 gün** `created_at` ile; `failed` belgeler pencere dışında da listede kalır (kartla aynı kural).

## 4. Bayrak

- Davranış B (`pending_documents`, `pending_notice`, yeni `warnings.kind`) **`ASSIST_MODE` arkasında**: kapalıyken `pending_documents: []`, `pending_notice: null`, `warnings` bugünkü gibi — yanıt byte-identik (ADR-027 ile aynı sözleşme ve aynı geri alma: `.env` + `make restart-backend`).
- Kart ucu ve hata eşlemesi (bölüm 1–2): bayraksız önerilir (SORU 1). Worker'ın kod yazması da bayraksız (eski genel metin → `unknown` eşlemesiyle geriye uyumlu).

## 5. `AskWarning.kind` genişletmesinin etkisi

Tansu'nun önerisi: `document_processing` (A). Buna **`document_unreadable`** (B) eklenir; ikisi de "cevap yok" durumunun alt türüdür, Ç-7'de yeni durum **açılmaz** (Ç-7 notu `message`'da taşınır).

| Dokunulan yer | Etki |
|---|---|
| `schemas/ask.py` `AskWarning.kind` Literal | +2 değer; `action: "request_data"` **verilmez** (başka departmandan istemek değil, beklemek gerekir); `action` için yeni değer önerilmez (bildirim bu turda yok) |
| `ask_router._run` cevap-yok dalı | A/B'de `missing_data/insufficient_data` **yerine** yeni kind (Tansu: "Veri yok etiketi gösterilmez"); Ç-7 bilgisi `message` ile korunur |
| `audit_log.warnings` JSONB | yeni kind'lar olduğu gibi yazılır; şema değişikliği yok |
| AI-BalBal `AnswerView` kind→renk, `strings.ts` kind→etiket | "Belge işleniyor" (sarı) / "Belge okunamadı" (kırmızı); bilinmeyen kind için zaten `warn` varsayılanı var mı kontrol edilir (eski arayüz yeni kind alırsa kırılmamalı) |
| Eval (`scripts/eval_lib.py`) | G2 cevapsız yanıt tanımı `answered=false` + sabit cümle (SORU 6 (i) seçilirse değişmez); **G3 genişletilir**: `pending_documents[*].document_id ⊆ ask_as_user`'ın görebildiği küme, `expected_project` koşulu aynı; `forbidden_sources` `pending_documents` başlıklarına da uygulanır. `assist_check`'e benzer `expect_pending: "processing" \| "unreadable" \| "none"` alanı yalnızca T7 testleri için (eval sorularına eklenmez — demo korpusunda işlenmekte olan belge yok) |
| README `warnings[]` satırı, `docs/prompts` | README güncellenir; prompt **değişmez** (model bu belgeleri görmez) |

Tansu'nun yedek önerisi ("kind genişletilmezse yalnızca `pending_documents`") kabul görmezse: arayüz `pending_documents` doluyken "Veri yok" etiketini gizler — aynı sonuç, ama audit'te uyarı türü "veri yok" kalır; **önerim kind genişletmesi** (audit kullanıcı gördüğünü yansıtsın, kural 4).

## 6. Kabul testleri (T7-1…T7-6 → backend/worker/arayüz)

| Test | Senaryo (Tansu) | Backend/worker kanıtı (otomatik) | Arayüz (AI-BalBal PR, elle/T-12) |
|---|---|---|---|
| **T7-1** | Finans kullanıcısı PDF yükler, ana ekrana döner: Kuyrukta → İşleniyor → sayfa yenilemeden Hazır ✓ | `test_recent_documents.py`: upload → `/recent` `card_state=queued`, `queue_position=1`; job `ocr` → `processing`; worker `ready` + `approved` → `ready`; `pending_metadata` → `pending_approval`, `approver=uploader` | kart 5 sn yoklama, tik; yenileme olmadan geçiş |
| **T7-2** | Okunamayan taranmış PDF | ocr-worker `test_pipeline.py`: boş-metin PDF → `ingestion_error="no_text"`; parola korumalı PDF (ocrmypdf exit code doğrulanarak) → `encrypted`, **retry yok**; bozuk → `corrupt`. Backend: `/recent` ve `/status` `reason` = sade Türkçe, ham metin **hiçbir yanıtta yok** (`"exit code"`, `"Traceback"` substring testi) | kırmızı etiket + neden + "Daha net bir tarama yükle" bağlantısı |
| **T7-3** | Belge işlenirken adını içeren soru | `test_pending_documents.py` (fake LLM, `ASSIST_MODE=true`): "Facility Agreement Amendment 03 ne diyor?" + `ocr` durumunda başlığı eşleşen belge → `answered=false`, `warnings[0].kind=document_processing`, `pending_notice` A cümlesi, `pending_documents=[o belge]`; LLM çağrı sayısı değişmedi (sıfır parçada 0, aksi halde 1) | Görsel 3; "Veri yok" etiketi yok |
| **T7-4** | Enerji kullanıcısı finansın işlenmekte olan belgesini sorar | aynı test dosyası: `enerji` + finans belgesi `ocr` → `pending_documents=[]`, `pending_notice=null`, uyarı `missing_data` (Durum D); başlık yanıtın hiçbir alanında geçmez (JSON'a `title` substring testi) — **G3** | — |
| **T7-5** | Hazır belgeden cevap + aynı konuda işlenen yeni belge | `answered=true`, kaynaklar aynı, `pending_notice` C cümlesi + başlık, `warnings` değişmedi | not satırı |
| **T7-6** | İlgisiz belge işleniyor | başlığı soruyla eşleşmeyen `ocr` belge → `pending_documents=[]`, `pending_notice=null` (yalnızca "Ankara"/"RES"/proje adı ile eşleşen belge de **listelenmez**) | — |
| Ek | Bayrak kapalı | T7-3/5 senaryoları `ASSIST_MODE=false` → `pending_documents=[]`, `pending_notice=null`, `warnings` bugünkü; `make test` tam yeşil | — |
| Ek | Eşleme tablosu | `ingestion_errors.reason_for` 5 kod + bilinmeyen + eski genel metin → genel cümle | — |

Canlı doğrulama (dev VM, LLM ≤ 2): bir PDF yükleyip işlenirken aynı başlıkla soru (A), bir bozuk PDF (B: `failed` + `reason`), sonra hazır olunca aynı soru (normal cevap). Ölçüm (eval) **gerekmez**: demo korpusunda bekleyen belge yok; G1–G3 regresyonu için R1'in 14 sorusu ×1 yeterli (14 çağrı) — SORU 9.

## 7. Bu turda olmayanlar

- Bildirim satırı / zil (Naci madde 6; B-02 yok) — kart ve cevapta bildirim alanı **gösterilmez**.
- Not 8 (hazır toplam yoksa listele) — ayrı plan, Ü-3 kararından sonra.
- İşlenmemiş belgenin içeriği hakkında tahmin; yetki kapısı değişikliği; çok turlu hafıza (T9); prompt'a örnek.
- AI-BalBal arayüzü (kart bileşeni, Görsel 3/4 kutuları, `strings.ts` etiketleri) — backend sözleşmesi bittikten sonra ayrı PR, T-12 tasarım onayı.

## 8. Uygulama sırası (Tansu'nun önerisiyle aynı: önce kart, sonra davranış)

1. Worker hata sınıflandırması (`no_text` tespiti dahil) + backend `ingestion_errors.reason_for` + `DocumentStatusResponse.reason`; testler.
2. `GET /api/documents/recent` + `card_state`/`queue_position`/`approver`; testler (T7-1, T7-2 backend yarısı).
3. `services/pending_documents.py` + `ask_router` entegrasyonu + `AskWarning.kind` + `AskResponse.pending_notice/pending_documents` + audit; testler (T7-3…T7-6, bayrak kapalı).
4. Eval G3 genişletmesi (`pending_documents`), README/ADR (ADR-027'ye ek madde ya da **ADR-028**), PHASES notu, rapor; canlı doğrulama; commit/push; AI-BalBal PR'ları (kart; cevap kutuları) ayrı.

## Kritik dosyalar

`ocr-worker/worker/pipeline.py` (+ `ocr.py` exit code/stderr eşlemesi), `ocr-worker/tests/test_pipeline.py`, `backend/app/services/ingestion_errors.py` (yeni), `backend/app/services/document_card.py` (yeni), `backend/app/services/pending_documents.py` (yeni), `backend/app/api/documents.py` (`/recent`, `/status`), `backend/app/schemas/document.py`, `backend/app/schemas/ask.py`, `backend/app/services/ask_router.py`, `backend/app/services/audit_writer.py`, `backend/app/repositories/document_repo.py` (`list_recent`, `queue_position`), `scripts/eval_lib.py` (G3), AI-BalBal: `pages/urun1/Urun1Home.tsx`, `pages/Department.tsx`, `api/documents.ts`, `components/balbal/AnswerView.tsx`, `lib/strings.ts`.

---

## SORU (Naci cevaplamalı)

1. **Kart ucu bayraksız mı?** Önerim: `/recent` ve hata eşlemesi bayraksız (salt okunur, bugünkü görünürlük kümesi); yalnızca Balbal davranışı (Durum A/B/C) `ASSIST_MODE` arkasında.
2. **Ham `ingestion_error` alanı:** `DocumentStatusResponse`'tan tamamen çıkarılsın mı (yalnızca `reason`), yoksa admin'e kalsın mı? Önerim: herkese `reason`, ham kod yalnızca admin ucu/denetim kaydında.
3. **`failed` satırları üstte** (Tansu önerisi) — kabul mü?
4. **Deterministik hatalarda retry yok** (`encrypted`, `corrupt`): 3 deneme kaldırılsın mı? Önerim: evet, yalnızca `unknown` için 3 deneme kalsın.
5. **Dal:** `feat/davranis-mantalitesi` üzerine devam mı (sözleşme ortak, tek birleştirme), yoksa ondan türeyen ayrı dal mı?
6. **Durum A/B'de `answer` alanı:** (i) sabit cümle aynen kalır, Not 7 cümlesi `pending_notice`'ta (ADR-014/ADR-027 sözleşmesi ve eval G2 değişmez — **önerim**) ya da (ii) `answer` Not 7 cümlesi olur (Tansu'nun görseli bunu ima ediyor; ADR-014'ün sabit-cümle hükmü ve G2 tanımı değişir, Tansu'ya bilgi gerekir).
7. **A/B durumunda ADR-027 netleştirme sorusu** da gösterilsin mi, yoksa `pending_notice` varken gizlensin mi (arayüz kararı, backend ikisini de döndürür)?
8. **Audit:** `pending_*` bilgisi mevcut `audit_log.assist` JSON'una mı (migration yok), ayrı kolona mı?
9. **Ölçüm:** Not 7 için eval koşusu yok, yalnızca 14 soruluk G1–G3 regresyonu (bayrak açık, ×1) — yeterli mi?

## Kendi aldığım küçük kararlar

- Hata sınıfı için yeni kolon açılmaz; `ingestion_error` kapalı kod kümesi taşır, çeviri backend'de tek fonksiyonda.
- `queue_position` yalnızca `queued` için ve "+1" ile (1 = sıradaki); `ocr` durumunda yazılmaz.
- `pending_documents` ≤ 3, `created_at` desc; A ve B birlikte varsa uyarı türü A, liste ikisini de içerir (`status` alanından ayrışır).
- Eşleştirmede proje adı/generic kelime tek başına eşleşme sayılmaz (ADR-027'deki aynı listeler), Tansu'nun "ilgisiz belge listelenmez" kuralı için.
- Tansu belgesindeki "PDF, Word veya Excel" ifadesi plana **düzeltilmiş** haliyle girdi; Tansu'ya tek satır not düşülecek.
