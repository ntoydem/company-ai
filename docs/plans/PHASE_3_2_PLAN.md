# Phase 3.2 — AI metadata önerisi + temporal/versiyon mantığı: Implementation Plan

## Bağlam ve tespitler

Phase 3.1 (`phase-3-1`) 15 gerçek demo belgeyi (ledger'dan, sayfa metniyle, gerçek versiyon zincirleriyle)
üretti ve yükledi. Adım 3'ün ikinci fazı Phase 3.2, PHASES.md'de iki başlık altında toplanıyor: **(A)** AI
metadata önerisi (yeni özellik) ve **(B)** "versiyon zinciri yönetimi + temporal 'güncel'/'ilk' ayrımı +
kural 6 ('neden?')". Kod tabanını okuyunca (B)'nin büyük kısmının **zaten Phase 0.3'te genel olarak inşa
edilmiş olduğunu** tespit ettim — bu plan hangi kısmın gerçekten yeni olduğunu netleştiriyor.

Okunanlar: `docs/PHASES.md` (Phase 3.2 + komşu fazlar), `docs/SPEC_02_dokuman_metadata_yetki_ux.md` (tamamı,
özellikle §1/§4/§9/§11), `docs/DOMAIN_MODEL.md` §3/§6/§9, `docs/ARCHITECTURE.md` ADR-004/006/009/012/014/021;
kod: `app/api/documents.py`, `app/api/ask.py`, `app/api/deps.py`, `app/services/{ask,answer_prompt,
version_chain,llm/*}.py`, `app/repositories/{document_repo,department_repo}.py`, `app/models/{document,
department}.py`, `app/schemas/document.py`, `app/core/config.py`, `backend/tests/test_documents.py`,
`seed_data/master/ankara_res.yaml`, `seed_data/evaluation/questions.json`.

### T1 — Temporal/versiyon mekanizması zaten genel, DSCR'a özel değil
`app/services/version_chain.py::evaluate_version_chains()` ve `app/services/ask.py::answer_question()`
Phase 0.3'ten beri **her** zincir için (yalnızca DSCR/Facility için değil) `is_current`/`is_initial` hesaplıyor
ve `answer_prompt.py`'nin sistem promptu (kural 5, "Zincir: GÜNCEL / İLK HALKA") zaten genel. Phase 3.1'in
gerçek Licence + Licence Amendment 01 zinciri (`DOC-ANK-DEV-001`→`002`, kapasite `initial`→`current`) ve
`seed_data/evaluation/questions.json`'daki `ANK-DEV-003`/`ANK-DEV-004` soruları bu mekanizmayı zaten
kullanılabilir halde buluyor — **yeni kod gerekmiyor**, yalnızca canlı doğrulama + kalıcı bir test.
`docs/reports/PHASE_3_1_REPORT.md`'de bu henüz canlı `/api/ask` ile İzmir/Ankara karışık test edilmedi (LLM
kotası nedeniyle bilinçli olarak sınırlı tutuldu) — bu fazda kapatılıyor.

### T2 — Kural 6 ("neden?") zaten sistem promptunda var
`answer_prompt.py`'nin kural 6'sı (`NO_REASON_TEXT = "belgelerde sebep belirtilmemiş"`) Phase 0.3'ten beri
kodda. Ledger'da (`seed_data/master/*.yaml`) hiçbir belgede nedensel bir açıklama (`reason`/`neden`/`sebep`
alanı) **hiç modellenmemiş** — yani PHASES.md'deki "EBITDA neden düştü?" örneği gerçek veri kümesinde birebir
karşılık bulmuyor (EBITDA hiç modellenmedi). Gerçek bir "neden?" sorusu (örn. "Ankara RES'in kapasitesi neden
artırıldı?") bu yüzden **her zaman** `NO_REASON_TEXT` dönmeli — yeni prompt kodu gerekmiyor, yalnızca canlı
doğrulama + kalıcı test (`test_ledger_live.py`'ye 4. kriter olarak eklenir).

### T3 — Gerçek yeni iş: AI metadata önerisi (SPEC_02 §4)
`document_metadata_suggestions` tablosu hiç yok; `LLM_MODEL_CLASSIFY` (config'te tanımlı, `gemini-3.5-flash-lite`)
hiçbir yerde kullanılmıyor; `Document.ai_suggestion_id` kolonu var ama FK'sız ("No FK yet: document_metadata_
suggestions arrives in Phase 3.2" — `app/models/document.py:111`). Bu fazın asıl işi bu.

### T4 — Gerçek yeni iş: upload formu department/subdepartment/project/confidentiality almıyor
`POST /api/documents/upload` şu an yalnızca `title/document_type/document_date/counterparty/status/
effective_date/version/supersedes_document_id` alıyor. `document_repo.create_with_job()` zaten
`department/subdepartment/project_id/confidentiality` kwarg'larını destekliyor (Phase 3.1 demo seed'i için
eklendi, docstring'i açıkça "later, Phase 3.2's metadata-suggestion acceptance flow" diyor) — yalnızca
endpoint'e bağlanmamış. PHASES.md'nin Phase 1.2 notu bunu bu fazın işi olarak işaretliyor: department alanı
`departments` tablosundaki bilinen slug'a karşı doğrulanmalı.

### T5 — Gerçek yeni iş: `mark_superseded` durum geçişi yapmıyor
`document_repo.py::mark_superseded()` docstring'i açık: "`older.status` is left untouched (Phase 0.3 decision;
status transitions belong to Phase 3.2)." Gerçek upload akışında (Phase 3.1 seed'i hariç — o ledger'daki
`status` değerini doğrudan yazıyor) bir belge başka birini `supersedes_document_id` ile değiştirdiğinde eski
belgenin `status`'u hâlâ değişmiyor. Bu fazda kapatılıyor: `mark_superseded` artık `older.status =
DocumentStatus.superseded` da yapacak (`draft`/`executed`/`amended`'dan `superseded`'a; zaten `superseded`
veya `active` ise dokunmaz — `active` iş/operasyon durumu, versiyon zincirinden bağımsız bir anlam taşıyabilir,
bkz. §5).

### T6 — LLM istemcisi yapılandırılmış yanıt (JSON) desteklemiyor
`app/services/llm/base.py::LLMRequest` yalnızca düz metin döndürüyor (`answer_prompt.py` `[K#]` etiketleriyle
kendi ayrıştırmasını yapıyor). Metadata önerisi 9 alan + her biri için confidence döndürmeli — düz metinle
regex ayrıştırmak kırılgan olur. `seed_data/generator/generate_prose.py` zaten Gemini'nin OpenAI-uyumlu
endpoint'inde `response_format={"type": "json_object"}`'ı doğrudan (kendi `openai.OpenAI` istemcisiyle, ADR-013
sınırı gereği `app.services.llm`'i kullanmadan) çalışır halde kanıtladı. Bu fazda `LLMRequest`/
`OpenAICompatibleClient` küçük bir opsiyonel `response_format` alanı kazanıyor (geriye dönük uyumlu, varsayılan
düz metin) — `/api/ask` hiç etkilenmiyor.

---

## 1. Migration + model — `document_metadata_suggestions`

```python
class SuggestionStatus(enum.StrEnum):
    pending = "pending"
    applied = "applied"
    rejected = "rejected"
    failed = "failed"

class DocumentMetadataSuggestion(TimestampMixin, Base):
    __tablename__ = "document_metadata_suggestions"
    id: UUID (pk)
    document_id: UUID (FK documents.id, ondelete=CASCADE, unique)  # belge başına tek satır
    model: str                        # örn. "gemini-3.5-flash-lite" (audit)
    status: SuggestionStatus = pending
    fields: JSONB                     # {"department": {"value": "finans", "confidence": 0.86}, ...}
    error: str | None                 # yalnızca status=failed
    applied_at: datetime | None
    applied_by_id: UUID | None (FK users.id, ondelete=SET NULL)
```
`fields` alanları: `department, subdepartment, project_code, document_type, counterparty, document_date,
status, confidentiality, tags` — her biri `{"value": ..., "confidence": 0.0-1.0}`. `project_code` (proje id
değil, `projects.code`) tutulur çünkü LLM proje UUID'sini bilemez; kabul sırasında `project_repo` ile
çözülür (T4'teki gibi).

`Document.ai_suggestion_id` bu tabloya gerçek FK kazanır (`ForeignKey("document_metadata_suggestions.id",
ondelete="SET NULL")`); docstring'i güncellenir. Migration `0005_document_metadata_suggestions`.

## 2. Öneri üretim servisi — `app/services/metadata_suggestion.py`

```python
def suggest_metadata(session, document, llm, settings) -> DocumentMetadataSuggestion:
    """`document.ingestion_status == ready` olmalı (çağıran garanti eder). İlk ~3 sayfanın
    metnini (document_pages, karakter tavanlı — kapak/özet genelde yeterli, tüm belgeyi
    göndermek maliyetli ve gereksiz) + bilinen departman slug'ları + proje kodları
    listesini LLM_MODEL_CLASSIFY'a JSON-mode ile gönderir. Başarısız olursa (LLMError)
    status=failed + error mesajı ile satırı yine de yazar — upload zaten bitmiş,
    hiçbir şeyi bozmaz (ADR-006)."""
```
Prompt: sistem promptu sabit (rules: yalnızca verilen metinden çıkar, bilinmeyen alan için `null` +
confidence 0, departman/proje **yalnızca verilen listeden** seçilir — halüsinasyon riskini yapısal olarak
kapatır, tıpkı prose üretiminde placeholder'ların kapatması gibi). Çıktı JSON şeması küçük bir Pydantic
modeliyle doğrulanır (`MetadataSuggestionPayload`); şema dışı/eksik alan → o alan `value=null,
confidence=0.0` sayılır, tüm cevap reddedilmez (kısmi güven kısmi işe yarar).

`fetch_pending_candidates(session, limit) -> list[Document]`: `ingestion_status == ready AND
ai_suggestion_id IS NULL`, en eski önce.

## 3. Tetikleme (SORU 1)

İki mekanizma birlikte, ikisi de aynı `suggest_metadata()` servisini çağırır:

- **Açık endpoint** `POST /api/documents/{id}/suggest-metadata` (admin) — `ingestion_status != ready` ise 409;
  zaten `pending`/`applied` bir öneri varsa var olanı döner (idempotent, yeniden üretmez — yeniden üretmek
  istenirse önce reddedilmeli). Testler ve elle "tekrar dene" (failed sonrası) bunu kullanır.
- **Arka plan taraması** (SORU 1'in asıl konusu): backend startup'ta (`lifespan`) başlayan, `asyncio.sleep`
  ile duraklayan bir döngü, her turda `fetch_pending_candidates` + `suggest_metadata`'ı bir batch limitiyle
  (örn. 5 belge/tur, 15 sn aralık) çalıştırır. Yeni bağımsız container/servis değil (ADR-001, "minimal
  moving parts") — tek `uvicorn` process'i içinde (ADR-002/003 T5 ile aynı "tek process yeter" mantığı).
  Kendi DB session'ını açar (request-scoped session'dan bağımsız). Testler bu döngüyü **hiç başlatmaz**
  (test app'i `lifespan` olmadan kurulur, mevcut `conftest.py` deseni); yalnızca `suggest_metadata`/
  `fetch_pending_candidates`'ı doğrudan çağırır.

  **Neden bu ikisi birden:** SPEC_02 §4 "Yükleme sonrası AI önerisi ... gösterilir" diyor — frontend henüz
  yok (Phase 3.3), o yüzden "otomatik" olması için bir arka plan mekanizması şart; ama tamamen arka plana
  güvenmek test edilebilirliği zorlaştırır (sleep tabanlı döngüler testte ya beklenir ya mock'lanır) — açık
  endpoint hem testi hem üretimde "tekrar dene" ihtiyacını basitçe çözer.

## 4. Kabul/düzenleme endpoint'i (SORU 2)

`POST /api/documents/{id}/metadata-suggestion/apply` — **admin-only** (`require_admin`, mevcut proje CRUD
deseniyle tutarlı; V0'da hiçbir "belge düzenle" yetkisi yok, en güvenli varsayılan). Body: yalnızca
**değiştirilmek istenen** alanların **açık değerleri** (öneriden aynen kopyalanmış ya da elle düzeltilmiş) —
`{"department": "finans", "project_code": "ANK_RES", "confidentiality": "normal", ...}`. Hiçbir alan
otomatik/sessizce uygulanmaz: yalnızca body'de **adı geçen** alanlar `documents` satırına yazılır (SPEC_02
§4 "kritik alan sessiz overwrite yok" — burada tüm alanlar aynı kurala tabi, ayrı bir "kritik" listesi
tutmuyoruz çünkü zaten hiçbir alan istek gövdesinde açıkça yer almadan değişmiyor; bkz. Kendi kararlarım).
`department`/`subdepartment` verilirse `departments` tablosundaki bilinen slug'a karşı doğrulanır (bilinmeyen
slug → 422); `project_code` verilirse `projects.code`'a karşı çözülür (bilinmeyen kod → 422). Öneri satırı
`status=applied`, `applied_at`, `applied_by_id` alır. `GET /api/documents/{id}/metadata-suggestion` (öneriyi
görüntüleme) ve `POST .../reject` (status=rejected, belgeye dokunmaz) da eklenir.

## 5. Upload formu genişlemesi (T4)

`POST /api/documents/upload`'a opsiyonel `department`, `subdepartment`, `project_id`, `confidentiality`
form alanları eklenir (SPEC_02 §1). `department` verilirse slug doğrulanır (422 mesajı: "Bilinmeyen
departman."). Hiçbiri zorunlu değil — boş bırakılırsa `NULL`/varsayılan kalır, AI önerisi + kabul akışı
sonradan doldurur. `status=active` bu fazda **eklenmiyor** LLM önerisi seçeneklerine (yaşam döngüsü
durumu — `draft/executed/amended/superseded` upload/amend akışından, `active` ayrı bir operasyonel anlam
taşıyor gibi görünüyor ama SPEC'te net ayrım yok; LLM'e yalnızca `draft/executed/amended` öneri seçeneği
olarak sunulur, `superseded`/`active` sistem tarafından yönetilir — küçük karar, raporda listelenir).

## 6. `mark_superseded` durum geçişi (T5)

```python
def mark_superseded(session, *, older, newer):
    older.superseded_by_document_id = newer.id
    if older.status in (DocumentStatus.draft, DocumentStatus.executed, DocumentStatus.amended):
        older.status = DocumentStatus.superseded
    session.flush()
```
Test: gerçek `/upload` ile bir belge yükle, `supersedes_document_id` ile ikincisini yükle → ilkinin
`status`'unun `superseded` olduğunu doğrula (mevcut `test_documents.py` upload testlerine ek).

## 7. LLM protokolüne JSON-mode (T6)

`LLMRequest`'e `response_format: Literal["text", "json_object"] = "text"` eklenir; `OpenAICompatibleClient.
complete()` bunu `response_format={"type": request.response_format}` olarak SDK çağrısına geçirir (yalnızca
`json_object` iken; `text` iken hiç göndermez — mevcut davranış birebir korunur). `/api/ask` etkilenmez
(hiç `response_format` set etmez, varsayılan `"text"`).

## 8. Temporal/kural-6 doğrulama (T1/T2 — yeni kod değil, doğrulama)

- `backend/tests/live/test_ledger_live.py`'ye 2 yeni canlı test: `test_current_capacity_vs_initial_licence_
  capacity_differ` (ANK-DEV-003/004 sorularının canlı `/api/ask` ile doğru ve **farklı** rakam döndürdüğünü
  doğrular, `ledger_value()` ile) ve `test_why_question_without_stated_reason_returns_fixed_text` (gerçek bir
  "neden?" sorusu → `answer_prompt.NO_REASON_TEXT` içerdiğini doğrular).
- Bunlar `make test-llm`'in parçası (gerçek Gemini çağrısı), `make test`'in değil — mevcut kural.

## 9. Kabul kriteri → kanıt

| Kriter | Kanıt |
|---|---|
| Facility Agreement upload → öneri Finans/Ankara/Facility Agreement + confidence | Gerçek bir Facility Agreement PDF'i (Phase 3.1'in ürettiği `DOC-ANK-FIN-004`'ün kopyası veya benzeri metin) ile `suggest_metadata()` birim testi; `fields["department"]["value"] == "finans"`, `fields["project_code"]["value"] == "ANK_RES"`, her alanda `confidence` mevcut |
| LLM hatası upload'ı bozmaz | Sahte hata fırlatan `LLMClient` ile `suggest_metadata()` → `status=failed` satırı yazılır, exception dışarı sızmaz; upload endpoint testi zaten öneri üretimini hiç çağırmıyor (tamamen ayrık) |
| "güncel kapasite" ↔ "ilk lisans kapasitesi" farklı ve doğru | `test_ledger_live.py::test_current_capacity_vs_initial_licence_capacity_differ` |
| "EBITDA neden düştü?" → yalnızca belgede yazan sebep veya "belirtilmemiş" | `test_ledger_live.py::test_why_question_without_stated_reason_returns_fixed_text` |

---

## SORU (Naci cevaplamalı)

1. **Otomatik tetikleme:** §3'teki "açık endpoint + arka plan taraması (asyncio, aynı process, 15 sn'de bir
   5 belge)" ikilisini onaylıyor musun? Alternatif: yalnızca açık endpoint (daha basit, arka plan döngüsü
   yok — "otomatik" davranış Phase 3.3'te frontend'in her ingestion-ready gördüğünde bu endpoint'i çağırmasıyla
   sağlanır). Ben ikiliyi öneriyorum çünkü frontend gelene kadar sistem hâlâ "otomatik" görünsün istiyorum,
   ama arka plan döngüsü bu depoda ilk kez kullanılan bir desen (`ADR-002`'nin "tek process" varsayımını
   asyncio ile paylaşıyor) — onayına ihtiyacım var.
2. **Kabul yetkisi:** öneri kabul/reddet/uygulama endpoint'i yalnızca `admin` mi (benim önerim, proje
   CRUD'daki gibi), yoksa belgeyi yükleyen kullanıcı (`uploaded_by_id`) da kendi belgesinin önerisini kabul
   edebilsin mi istersin?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- `document_metadata_suggestions` belge başına **tek satır** (upsert, geçmiş tutulmaz) — V0'da bir belgenin
  önerisi bir kez üretilir; tekrar denemek `reject` + yeni `suggest-metadata` çağrısı gerektirir.
  Confidence/geçmiş analizi Phase 4.1/5.x'in eval kapsamı, V0'ın değil.
- `fields` JSONB tek kolon (9 ayrı kolon yerine) — şema esnekliği, `document_metadata_suggestions`'ın kendisi
  hiçbir zaman retrieval/authorization'a girmiyor (yalnızca öneri görüntüleme), bu yüzden SQL sorgulanabilirlik
  gerekmiyor.
  `project_code` (id değil) tutulur, kabul sırasında çözülür — LLM proje UUID'si bilemez.
- Kabul endpoint'i "tüm alanlar aynı kural" — ayrı bir "kritik alan" listesi yok; SPEC'in "kritik alan sessiz
  overwrite yok" cümlesi, hiçbir alanın istek gövdesinde açıkça geçmeden değişmemesiyle zaten sağlanıyor.
- `status=active` LLM'in öneri seçeneklerinden çıkarılır (yaşam döngüsü değil operasyonel durum gibi
  görünüyor); `superseded` zaten sistem tarafından (`mark_superseded`) yönetiliyor, LLM'e seçenek olarak
  sunulmaz.
- `subdepartment` doğrulaması "yumuşak": verilirse ve seçilen `department`'ın bilinen bir alt departmanıysa
  kabul edilir, değilse serbest metin olarak (uyarı loglanır, hata verilmez) kabul edilir — `subdepartment`
  zaten yetki birimi değil (Phase 1.2 T7), salt görüntüleme/filtre alanı.
- LLM'e gönderilen belge metni ilk ~3 sayfa / ~4000 karakterle sınırlı (tüm belgeyi göndermek maliyetli ve
  gereksiz; kapak+özet sayfaları metadata için yeterli).
- Yeni golden-soru kategorisi (`questions.json`'a "neden"/rule-6 kategorisi) **eklenmiyor** — bu, kontrollü
  kategori/kota şemasını (Phase 2.1'in `validate_ledger.py` Q-kuralları) genişletmek olur, kapsamı Phase
  4.1/5.1'e ait; bu fazda kural 6 doğrulaması `test_ledger_live.py`'de kalıcı bir testle yapılır.

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: ADR-006'ya "Phase 3.2 concretization" notu (arka plan tarama mekanizması); ADR-009'a
  `response_format` notu; ADR-012'ye "Phase 3.2: full" satırının artık gerçekten kapandığını işaretleyen not;
  yeni bir ADR açılmıyor (mevcut ADR'ler zaten bu kararları kapsıyor, yalnızca somutlaşıyor).
- `docs/DOMAIN_MODEL.md`: `DocumentMetadataSuggestion` satırındaki "Phase 3.2" artık gerçek şemayla eşleşiyor;
  `document_status` enum notuna `superseded` geçişinin artık otomatik olduğu eklenir.
- `README.md`: yeni "AI metadata önerisi (Phase 3.2)" bölümü — curl örnekleriyle upload→suggest→apply akışı.
- `docs/reports/PHASE_3_2_REPORT.md`, `docs/PHASES.md` durum satırı, `git tag phase-3-2`.

## Uygulama sırası

1. Migration `0005_document_metadata_suggestions` + model + `Document.ai_suggestion_id` FK'si.
2. `LLMRequest.response_format` + `OpenAICompatibleClient` desteği + birim testi.
3. `app/services/metadata_suggestion.py` (`suggest_metadata`, `fetch_pending_candidates`) + birim testleri
   (sahte `LLMClient`).
4. `document_repo.py`'ye suggestion CRUD yardımcıları; `department_repo`/`project_repo` slug/kod çözümleme.
5. `app/api/documents.py`: upload'a department/subdepartment/project_id/confidentiality + slug doğrulama;
   `mark_superseded` durum geçişi; 3 yeni endpoint (`suggest-metadata`, `metadata-suggestion` GET, `apply`,
   `reject`).
6. Arka plan tarama döngüsü (`app/core/main.py` lifespan) — SORU 1 onayına bağlı.
7. `test_documents.py` genişlemesi (upload alanları, status geçişi, suggestion endpoint'leri, yetki testleri).
8. `test_ledger_live.py`'ye T1/T2 doğrulama testleri.
9. `.env.example` (yeni env değişkeni gerekirse — şu an öngörmüyorum, `LLM_MODEL_CLASSIFY` zaten var),
   README, ADR notları → `make test`/`make lint` yeşil → rapor → `docs/PHASES.md` → commit + tag `phase-3-2`
   + push.

## Kritik dosyalar

- `backend/alembic/versions/0005_document_metadata_suggestions.py`, `backend/app/models/document_metadata_
  suggestion.py`
- `backend/app/services/metadata_suggestion.py`, `backend/app/services/llm/{base,openai_compatible}.py`
- `backend/app/api/documents.py`, `backend/app/repositories/document_repo.py`
- `backend/tests/test_documents.py`, `backend/tests/live/test_ledger_live.py`
