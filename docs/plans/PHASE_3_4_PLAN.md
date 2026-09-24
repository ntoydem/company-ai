# Phase 3.4 — Audit log + embedding (opsiyonel): Implementation Plan

## Bağlam ve tespitler

Phase 3.3 (`phase-3-3`) frontend'i kapattı; Adım 3'ün son fazı Phase 3.4 iki bağımsız parçadan oluşuyor:
**(A) audit log** (zorunlu, her `/api/ask` çağrısı) ve **(B) embedding** (opsiyonel, `EMBEDDINGS_ENABLED` bayrağı,
16 GB VM gerektirir). Bu ikisi kod olarak neredeyse hiç kesişmiyor — ayrı ayrı planlandı.

Okunanlar: `docs/PHASES.md` (Phase 3.4), `docs/SPEC_06_operasyon_guvenlik_kalite.md` (tamamı, özellikle §1/§6/§7/§8),
`docs/SPEC_01_urun_kapsam_altyapi.md` §4-6, `docs/ARCHITECTURE.md` ADR-001/002/004/006/007/017; kod:
`backend/app/api/ask.py`, `backend/app/services/{ask,retrieval,search_query}.py`,
`backend/app/repositories/document_chunk_repo.py`, `backend/app/models/document_chunk.py` (embedding kolonu
**zaten var**), `backend/app/main.py` (Phase 3.2'nin arka plan döngüsü — bu fazda iki kez daha kullanılan desen),
`backend/app/core/{request_id,logging}.py`, `infra/docker-compose.yml` (`embed` servisi zaten tanımlı).
Ayrıca TEI'nin (`ghcr.io/huggingface/text-embeddings-inference`) OpenAI-uyumlu `/v1/embeddings` ucu ve bge-m3'ün
(560M parametre, 1024 boyut, ~1,1 GB fp16 ağırlık) gerçek boyutları resmi kaynaklardan doğrulandı (§4).

### T1 — `document_chunks.embedding` kolonu zaten var, migration'sız
`0002_documents_pipeline.py` zaten `embedding Vector(1024)` (nullable) yazmış; `EMBEDDING_DIM = 1024` sabiti
`document_chunk.py`'de "verify against the embed service when it lands" notuyla duruyor. Bu fazda **yeni kolon
migration'ı gerekmiyor** — yalnızca `audit_log` tablosu için (0006).

### T2 — Arka plan döngüsü deseni zaten iki kez kanıtlanmış (Phase 3.2)
`app/main.py`'nin `lifespan`'ı, `_is_test_database()` ile korunan bir `asyncio` döngüsü zaten çalıştırıyor
(metadata-suggestion tarama, 15 sn). Bu fazın **iki** yeni arka plan işi (audit log temizliği, embedding
backfill) **aynı deseni** tekrar kullanıyor — yeni bir zamanlayıcı kütüphanesi (APScheduler vb.) veya cron
container'ı **gerekmiyor** (ADR-001, "minimal moving parts").

### T3 — `retrieve()`'in imzası embedding için yetersiz
`app/services/ask.py:86-87`: `query = build_search_query(request.question); retrieve(session, user, query, filters)`
— `retrieve()`'e yalnızca OR-token'lanmış FTS sorgusu gidiyor, **orijinal doğal dil sorusu gitmiyor**. Embedding
anlamsal olduğu için ham soruyu (stopword'leri temizlenmemiş) embed etmek gerekiyor — imza değişmeli (§5).
Etkilenen çağrı yerleri: `ask.py` (1), `tests/test_retrieval.py` (2), `tests/test_search_query.py` (2).

### T4 — `ocr-worker` dokunulmuyor
`ocr-worker` "kendi pyproject/tests'i, backend/app'i import etmez" ilkesiyle inşa edildi ve embed servisini hiç
bilmiyor. Embedding hesaplama backend tarafında, ayrı bir arka plan döngüsüyle yapılacak (§5) — ocr-worker'a yeni
bir dış servis bağımlılığı eklenmiyor.

### T5 — Router (Phase 4.3) henüz yok, `query_type` şimdilik sabit
`DOMAIN_MODEL.md`'nin `query_type` enum'u (`DOCUMENT_QUERY|DATA_QUERY|MIXED_QUERY|GENERAL_QUERY`) ADR-010'un
router'ına ait; router Phase 4.3'te geliyor. `/api/ask` bugün yalnızca DOCUMENT_QUERY yapıyor — audit_log'un
`query_type` kolonu bu fazda **her zaman `"DOCUMENT_QUERY"`** yazılır, ileriye dönük hazır kolon.

---

## 1. `audit_log` tablosu (migration `0006`)

SPEC_06 §1'deki alanlar birebir:

```python
class AuditLog(Base):  # TimestampMixin YOK — satır değişmez, kendi `timestamp` alanı var
    __tablename__ = "audit_log"
    id: UUID (pk)
    user_id: UUID | None (FK users.id, ondelete=SET NULL — kullanıcı silinse de log kalır)
    timestamp: datetime (timestamptz, server_default=now())
    question: str (Text)
    query_type: str  # şimdilik hep "DOCUMENT_QUERY" (T5)
    scope_department: str | None
    scope_project: UUID | None  # FK yok (documents.department gibi — projeler silinebilir, log kalır)
    documents_retrieved: list[UUID]  # ARRAY(Uuid), FK yok (tags/related_document_ids deseniyle aynı)
    excel_files_used: list[str]  # ARRAY(String) — Phase 4.2'ye kadar hep []
    answer: str (Text)
    sources: list[dict]  # JSONB — SourceCard'ların ham hali
    model: str | None
    tokens_in: int
    tokens_out: int
    cost_estimate: Decimal | None  # Numeric(10,6), USD — §5 kararı
    execution_ms: int
    request_id: str | None
    error: str | None  # yalnızca LLM/sistem hatası; "kaynak yok" iş sonucu değil (T6)
```
İndeks: `(timestamp)` (90 gün temizliği + tarih filtresi), `(user_id, timestamp)` (admin filtresi).
`password/api_key/token` içeren hiçbir alan yok (SPEC_06 §1) — `question`/`answer` kullanıcı girdisi/LLM çıktısı,
sızma riski `answer_prompt.py`'nin zaten "yalnızca kaynaktan" kuralına bağlı, audit ek bir maskeleme gerektirmiyor.

## 2. Yazma noktası — `app/services/ask.py::answer_question()` içinde

**T6 — Kendi kararım:** audit satırı `ask.py`'nin **API katmanında değil, servis katmanında** yazılır — aynı yerde
zaten hesaplanan (`retrieved_ids`, `sources`, `model`, `tokens_*`, `duration_ms`) veriyi ikinci kez hesaplamamak
için (`log.info("ask completed", …)` çağrısının hemen yanına). İki dal:
- **Başarı/"bilgi yok" dalı:** mevcut akışın sonunda `audit_log_repo.create(...)` çağrılır — `error=None`.
- **LLM hata dalı:** `llm.complete(...)` çağrısı bugün hiç `try/except` içinde değil, `LLMError` doğrudan
  `app/core/errors.py::llm_exception_handler`'a düşüyor (503). Bu fazda `llm.complete(...)` bir `try/except
  LLMError as exc` ile sarılır: audit satırı `error=str(exc)` ile yazılır, **sonra `raise`** — kullanıcıya giden
  503 yanıtı birebir aynı kalır, yalnızca audit'e bir satır eklenir.
- **Audit yazımı asla `/api/ask`'i bozmaz:** `audit_log_repo.create(...)` çağrısı kendi `try/except Exception`
  içinde — DB yazımı başarısız olursa `log.error(...)` yazılır, kullanıcıya giden cevap etkilenmez (ADR-006'nın
  "öneri hatası upload'ı bozmaz" ilkesiyle aynı desen).
`request_id` için `app.core.request_id.get_request_id()` doğrudan çağrılır (mevcut contextvar, ADR-017 —
middleware zaten her istekte dolduruyor).

## 3. 90 gün saklama + günlük temizlik (SORU'ya gerek yok — T2 emsali)

**Nasıl tetiklenecek:** iki mekanizma birden (Phase 3.2'nin "açık uç + arka plan" deseninin emsali):
- `app/main.py` lifespan'a üçüncü bir `asyncio` döngüsü: `_audit_log_cleanup_loop`, her
  `audit_log_cleanup_interval_s` (varsayılan 6 saat — "günlük" hedefini rahatça karşılar, DELETE sorgusu ucuz ve
  idempotent olduğu için sık çalışması zararsız) `DELETE FROM audit_log WHERE timestamp < now() - 90 days`
  çalıştırır. `_is_test_database()` koruması altında (Phase 3.2 ile aynı) — `make test` bunu hiç çalıştırmaz.
- `python -m app.cli cleanup-audit-log` — elle/host cron'undan tetiklenebilir alternatif, testlerin doğrudan
  çağırdığı fonksiyonun ince bir sarmalayıcısı (`app/repositories/audit_log_repo.py::delete_older_than`).

## 4. `embed` servisi — bge-m3, RAM tahmini, izolasyon garantisi

**RAM tahmini (kaynaklı):** bge-m3 560M parametre, fp16 ağırlık ~1,1 GB; CPU'da (fp32/int8 karışık, TEI'nin
Rust motoru) çalışma zamanı ağırlıklar + batch tamponları + runtime overhead ile gerçekçi toplam **3-4 GB
container RSS** (HuggingFace model-memory tartışma sayfası + TEI CPU imaj notları, §"Doğruladığım üçüncü taraf
davranışları"). Bu oturumda ölçülen mevcut servisler (postgres ~250 MB, backend ~85 MB, ocr-worker ~60-100 MB,
caddy ~10 MB) ile toplam **~4-5 GB** — 16 GB VM'de rahat, `make up-full` sırasında eşzamanlı `make test` için de
yer kalır. Gerçek sayı implementasyonda `docker stats` ile ölçülüp rapora yazılır (tahmin değil).

**Kapalıyken sıfır etki garantisi (iki katman):**
1. **Compose:** `embed` servisi `profiles: ["full"]` altında kalır (zaten öyle) — `make up` onu hiç başlatmaz;
   container yoksa hiçbir şey ona bağlanamaz.
2. **Kod:** `EMBEDDINGS_ENABLED=false` iken (a) hibrit retrieval adımı hiç çalışmaz (§5, düz `if` ile atlanır,
   embedding istemcisi hiç kurulmaz), (b) embedding backfill döngüsü hiç başlamaz (Phase 3.2'nin LLM-yapılandırılmamışsa-
   döngü-başlamaz desenirinin aynısı). `EmbeddingClient` **tembel** kurulur (`get_llm_client()`'ın
   `LLMNotConfiguredError` deseni gibi) — import zamanında hiçbir bağlantı denenmez. `make test`, `EMBEDDINGS_
   ENABLED` ortam değişkenini hiç set etmediği için (varsayılan `false`) embed servisiyle hiç konuşmaz; test
   DB'sinde `embedding` kolonu hep `NULL` kalır, mevcut FTS testleri değişmeden geçer.

**Yeni ayarlar (`config.py`/`.env.example`):** `EMBED_BASE_URL=http://embed:8080` (compose ağı içi, servis adı
zaten `embed`), `EMBED_TIMEOUT_S=30`, `EMBEDDING_BACKFILL_INTERVAL_S=15`, `EMBEDDING_BACKFILL_BATCH_SIZE=20`.

**İstemci:** `app/services/embedding_client.py` — `EmbeddingClient` Protocol + `TEIEmbeddingClient` (openai SDK,
`base_url=f"{EMBED_BASE_URL}/v1"`, TEI'nin OpenAI-uyumlu `/v1/embeddings` ucu — resmi TEI dokümanında doğrulandı;
API key alanı TEI'de kullanılmıyor, SDK'nın zorunlu tuttuğu bir placeholder string geçilir, gerçek davranış
implementasyonda TEI'nin quick-tour dokümanına karşı bir kez doğrulanır — CLAUDE.md: "olmayan API/parametre
üretme"). `app/services/llm/`'deki çok-sağlayıcılı (`OpenAICompatibleClient`/`AnthropicClient`) yapı burada
**taklit edilmiyor** — tek sağlayıcı (bge-m3/TEI) var, `llm/` tarzı bir paket premature abstraction olur.

## 5. Hibrit retrieval — `EMBEDDINGS_ENABLED=true` iken `retrieve()` nasıl değişir

1. **İmza:** `retrieve(session, user, query, filters, *, raw_question: str | None = None)` — `raw_question`
   verilmezse `query` ile aynı kabul edilir (mevcut 4 test çağrı yeri **değişmeden** derlenmeye devam eder);
   `ask.py` artık `retrieve(session, user, query, filters, raw_question=request.question)` çağırır (T3).
2. **Embedding araması:** `EMBEDDINGS_ENABLED` açıksa, `raw_question`'ı `EmbeddingClient.embed([raw_question])`
   ile vektöre çevirir, `document_chunks.embedding <=> :vector` (pgvector cosine distance) ile `allowed_ids`
   kısıtlı, `top_k` sıralı ikinci bir liste çeker (FTS ile **aynı** yetki kapısından geçmiş — ADR-004 sırası
   bozulmaz: önce `allowed_document_ids`, sonra hem FTS hem vektör arama bu kümeyle sınırlı).
3. **Birleştirme — Reciprocal Rank Fusion (RRF), kendi kararım:** `ts_rank_cd` (FTS) ve cosine-distance (vektör)
   ham skorları karşılaştırılamaz ölçeklerde; RRF yalnızca **sıra** kullanır: `score(chunk) = Σ 1/(k + rank)`
   (k=60, IR literatüründeki standart varsayılan), yalnızca bir listede olan chunk'lar da tek terimle skor alır.
   Birleşik liste `top_k`'ya kesilir. Bu, ağırlık kalibrasyonu gerektirmeyen, kanıtlanmış bir teknik — SORU değil.
4. **Zarif bozulma (kendi kararım, SPEC_06 §8'in "geri kalan çalışır" ilkesinden):** embed servisine çağrı
   zaman aşımına uğrar/bağlantı hatası verirse, `retrieve()` bunu yakalar, uyarı loglar ve **yalnızca FTS
   sonuçlarıyla** devam eder — `/api/ask` asla bu yüzden 503 vermez. (LLM cevap adımı farklı: oradaki hata hâlâ
   503'e düşer, çünkü cevabı üretecek başka bir yol yok — yalnızca retrieval'ın FTS yedeği var.)
5. **Embedding backfill (yeni arka plan döngüsü, T2 emsali):** `app/services/embedding_backfill.py` —
   `fetch_pending_chunks()` (`document_chunks WHERE embedding IS NULL`, `EMBEDDING_BACKFILL_BATCH_SIZE` limit),
   `run_pending_scan()` — toplu `embed()` çağrısı + `UPDATE`. `app/main.py`'de dördüncü koşullu döngü: yalnızca
   `EMBEDDINGS_ENABLED=true` **ve** `_is_test_database()` değilken başlar.
6. **pgvector indeksi eklenmiyor (kendi kararım):** V0 demo ölçeğinde (15-70 belge, birkaç yüz chunk) sıralı
   tarama (`<=>` + `LIMIT`) indekssiz de milisaniyeler sürer; `ivfflat`/`hnsw` eklemek bu ölçekte premature
   optimization olur. Chunk sayısı ciddi büyürse (Phase 5.1 sonrası) ayrı bir migration'la eklenebilir — not
   olarak `docs/ARCHITECTURE.md`'ye düşülür.

## 6. Admin-only audit log görüntüleme API'si (yalnızca API, UI Phase 5.2)

Phase 3.3'ün `DocumentListItem`/`DocumentDetailResponse` ikilisiyle aynı desen:
- `GET /api/audit-log?user_id=&department=&project_id=&query_type=&from=&to=&has_error=&limit=&offset=` —
  `require_admin`; hafif liste (`id, timestamp, user_id, question, query_type, scope_department, scope_project,
  model, tokens_in, tokens_out, execution_ms, error != null`) — `answer`/`sources`/tam `question` **yok** (ağır).
- `GET /api/audit-log/{id}` — `require_admin`; tam kayıt (`answer`, `sources`, `documents_retrieved`, hepsi).
- Admin dışı rol → 403 (mevcut `require_admin` deseni, `test_projects.py`'deki gibi).
- Ayrı bir `/api/admin/*` önek yok — mevcut kod hiçbir yerde böyle bir ad alanı kullanmıyor (proje CRUD'u da
  düz `/api/projects` altında, `require_admin` ile korunuyor); tutarlılık için aynı desen.

## 7. Kabul kriteri → kanıt

| Kriter (PHASES.md) | Kanıt |
|---|---|
| her `/api/ask` audit'te (kaynaklar, model, token) | `test_ask.py`'ye eklenen testler: başarılı cevap → `audit_log`'da 1 satır, `sources`/`model`/`tokens_in`/`tokens_out`/`execution_ms` dolu; "bilgi yok" dalı → satır var, `error=None`; sahte `LLMRateLimitError` → satır var, `error` dolu, **response hâlâ 503** (davranış değişmedi) |
| şifre/key yok | `audit_log_repo` birim testi: `question`/`answer` içine sokulan bir sentinel string log'a girsin ama tablo şemasında `password`/`api_key`/`token` kolonu **hiç yok** — statik garanti; ayrıca `caplog` ile `create()` çağrısının olağan JSON log satırına sızıntı yapmadığı (`test_login_failure_does_not_log_password_or_hash` deseniyle aynı) |
| `EMBEDDINGS_ENABLED=false` ile tüm testler geçer | `make test` zaten bunu varsayılan olarak yapıyor (env hiç set edilmiyor); yeni test: `retrieve()` çağrısı `raw_question` verilse bile bayrak kapalıyken embedding istemcisine hiç dokunmadığını sahte/instrumented bir `EmbeddingClient` ile doğrular (`assert calls == []`) |
| `true` ile embed servisi çalışır (RAM yoksa atlandı diye raporlanır) | Canlı: `make up-full`, `docker stats` ile gerçek RAM ölçümü rapora yazılır; VM'de yeterli boş RAM varsa `curl embed:8080/health` + gerçek bir belge için backfill'in `embedding`'i doldurduğu SQL ile doğrulanır + hibrit bir sorgunun FTS-only'den farklı/en az eşit kalitede sonuç verdiği gösterilir. **Bu VM'de gerçekten denenip denenmeyeceği SORU 1** |

---

## SORU (Naci cevaplamalı)

1. **Canlı embedding doğrulamasının kapsamı.** `make up-full` gerçek bge-m3 modelini indirip (~2 GB disk) ayağa
   kaldırmak birkaç dakika + ~3-4 GB RAM gerektiriyor. Bunu bu VM'de **gerçekten çalıştırıp** hibrit retrieval'ı
   canlı doğrulayayım mı (rapor gerçek `docker stats` + gerçek bir sorgu örneğiyle biter), yoksa testler sahte/
   küçük-boyutlu bir `EmbeddingClient` ile yeterli sayılsın ve canlı doğrulama yalnızca "RAM yeterliyse Naci'nin
   kendi ortamında `make up-full` ile deneyebileceği bir adım" olarak README'de mi kalsın? Önerim: dev VM'in
   mevcut boş RAM'ini önce `free -h` ile kontrol edip yeterliyse gerçekten deneyeyim, değilse sahte istemciyle
   yetinip raporda açıkça "gerçek modelle denenmedi, RAM sınırı" diye not düşeyim.
2. **`cost_estimate` fiyat tablosu.** Sütun şemada var (SPEC_06 §1) ama gerçek $/1K-token fiyatları Gemini'nin
   güncel resmi fiyatlandırma sayfasından implementasyon sırasında doğrulanacak (şu an tahmin/uydurma rakam
   yazmıyorum). Model listede yoksa `cost_estimate = NULL` (asla 0 ya da tahmini bir sayı). Onaylıyor musun, yoksa
   V0'da bu alan hep `NULL` kalsın, fiyat tablosu hiç eklenmesin mi (basitlik, Phase 4.1/5.x'e ertelenir)?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- Audit satırı servis katmanında (`answer_question()`), API katmanında değil — hesaplanmış veriyi tekrar
  üretmemek için (§2).
- Audit yazımı kendi `try/except` içinde; asla `/api/ask` yanıtını bozmaz (ADR-006 emsali).
- Temizlik: arka plan döngüsü (6 saatte bir, "günlük" hedefini fazlasıyla karşılar) + `cleanup-audit-log` CLI
  komutu, ikisi birden (§3, Phase 3.2 SORU 1 emsali — burada ayrıca sormaya gerek görmedim).
- `EmbeddingClient` tek dosya (`embedding_client.py`), `app/services/llm/` tarzı çok-sağlayıcılı paket değil —
  tek sağlayıcı var, soyutlama gereksiz.
- Hibrit birleştirme: Reciprocal Rank Fusion, k=60 (standart IR sabiti) — ağırlık kalibrasyonu gerekmiyor.
- Embed servisi geçici olarak ulaşılamazsa retrieval FTS'e düşer, `/api/ask` 503 vermez (yalnızca LLM adımı 503
  verir) — SPEC_06 §8'in "geri kalan çalışır" ilkesi.
- pgvector ANN indeksi (ivfflat/hnsw) bu fazda eklenmiyor — V0 ölçeğinde gereksiz, not olarak bırakılıyor.
- `query_type` şimdilik her zaman `"DOCUMENT_QUERY"` (router Phase 4.3'te geliyor).
- Admin audit endpoint'i liste/detay ayrımı (Phase 3.3'ün belge deseniyle aynı); ayrı `/api/admin/*` önek yok.
- `scope_project`/`documents_retrieved` FK'siz (mevcut `tags`/`related_document_ids` deseniyle tutarlı) —
  silinen bir proje/belge audit geçmişini bozmasın.

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: yeni **ADR-016 devamı** değil, ADR-016 zaten "audit log ≠ hafıza" kararını taşıyor —
  ona "Phase 3.4 concretization" notu (yazma noktası, temizlik mekanizması, admin API). ADR-007'ye "Phase 3.4
  concretization" notu (RRF, zarif bozulma, backfill döngüsü, ANN indeksi ertelemesi). RAM ölçümü + ivfflat notu.
- `docs/DOMAIN_MODEL.md`: `AuditLog` satırındaki "Phase 3.4" artık gerçek şemayla eşleşiyor; `query_type` notuna
  "şu an hep DOCUMENT_QUERY" eklenir.
- `README.md`: "Audit log (Phase 3.4)" bölümü (admin API örnek `curl`), "Embedding (Phase 3.4, opsiyonel)"
  bölümü (`make up-full`, RAM notu, `EMBEDDINGS_ENABLED` açma/kapama).
- `docs/reports/PHASE_3_4_REPORT.md`, `docs/PHASES.md` durum satırı, `git tag phase-3-4`.

## Uygulama sırası

1. Migration `0006_audit_log` + `AuditLog` modeli + `audit_log_repo.py` (`create`, `list_filtered`, `get`,
   `delete_older_than`) + birim testleri.
2. `ask.py`'ye audit yazımı (başarı + hata dalı) + testleri (`test_ask.py` genişlemesi).
3. `cleanup-audit-log` CLI komutu + `app/main.py`'de temizlik döngüsü + testi.
4. `GET /api/audit-log` + `/{id}` (admin-only) + şemalar + testleri.
5. `embedding_client.py` (`EmbeddingClient`, `TEIEmbeddingClient`, tembel kurulum) + `.env.example`/`config.py`
   yeni ayarlar.
6. `retrieve()` imza değişikliği (`raw_question`) + RRF birleştirme + zarif bozulma + 4 çağrı yerinin güncellenmesi.
7. `embedding_backfill.py` + `app/main.py`'de dördüncü döngü + `backfill-embeddings` CLI komutu + testleri (sahte
   `EmbeddingClient`).
8. SORU 1'in cevabına göre: `make up-full` canlı deneme + `docker stats` + hibrit sorgu kanıtı, ya da not.
9. README/ADR notları → `make test`/`make lint` yeşil → rapor → `docs/PHASES.md` → commit + tag `phase-3-4` + push.

## Kritik dosyalar

- `backend/alembic/versions/0006_audit_log.py`, `backend/app/models/audit_log.py`,
  `backend/app/repositories/audit_log_repo.py`, `backend/app/api/audit_log.py`
- `backend/app/services/ask.py` (audit yazımı), `backend/app/services/retrieval.py` (hibrit)
- `backend/app/services/embedding_client.py`, `backend/app/services/embedding_backfill.py`
- `backend/app/main.py` (iki yeni döngü), `backend/app/core/config.py`, `infra/.env.example`
