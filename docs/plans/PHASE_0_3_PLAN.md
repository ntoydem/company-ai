# Phase 0.3 — LLM + soru-cevap (T0): Implementation Plan

## Bağlam ve tespitler

Phase 0.2 (`phase-0-2`) belge hattını ve yetki-filtreli `retrieve()`'i kurdu. Phase 0.3, `docs/PHASES.md`'deki T0 kabul kriterlerini (5 madde) kapatır: `POST /api/ask`, LLM istemcisi, versiyon/tarih değerlendirmesi, sayfa kaynaklı Türkçe cevap. Okunanlar: PHASES.md (0.3), SPEC_01 §5/§7, SPEC_02 §9–§11, SPEC_06 §1/§8, DOMAIN_MODEL §6, ADR-004/007/008/009/012/014/015/017, `retrieval.py`, `authorization.py`, `document_chunk_repo.py`, `document_repo.py`, `documents.py`, `deps.py`, `config.py`, `conftest.py`, `seed_data/t0/generate.py`.

Plan yazılmadan önce canlı stack'te doğrulanan **üç tespit** planı şekillendiriyor:

**T1 — Mevcut FTS, doğal dil sorularına 0 sonuç döndürüyor.** `websearch_to_tsquery` terimleri AND'liyor; "güncel", "nedir", "ilk", "neydi" gibi Türkçe soru kelimeleri İngilizce belgelerde yok. Canlı DB'de (22 chunk, 3 belge) ölçüm:

| Soru | AND (mevcut) | OR (önerilen) | OR ilk sonuç |
|---|---|---|---|
| "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" | 0 chunk | 11 chunk | Amendment 01 s.3 (rank 0,60), Facility s.6 (0,40) |
| "İlk DSCR covenant neydi?" | 0 chunk | 6 chunk | Facility s.6 / Amendment s.3 |
| "İzmir RES'in COD tarihi nedir?" | 0 chunk | 0 chunk (phrase `res <-> in` yüzünden; temizlenmiş terimlerle `res` Ankara chunk'larını döndürür) | — |

Sonuç: `/api/ask`, `retrieve()`'i olduğu gibi kullanamaz; sorgu kurma katmanı gerekir (§2.1). Phase 0.2'nin "DSCR covenant" testi OR ile de geçer.

**T2 — Versiyon zinciri hiçbir yerde kurulmuyor.** `documents` tablosunda `supersedes_document_id`, `superseded_by_document_id`, `effective_date`, `version` var ama `POST /api/documents/upload` bunları kabul etmiyor; canlı DB'de 3 belgenin hiçbirinde zincir/effective_date/project yok. Kriter 1 ("güncel → Amendment 01") zincir olmadan yalnızca LLM'in metin okumasına dayanır; bu ADR-012'ye aykırı. Zincir kurma yolu eklenmeli (§2.3, SORU 1).

**T3 — Üçüncü taraf doğrulamaları (resmi doküman, 22.09.2026):**
- Gemini OpenAI-uyumlu endpoint: `base_url = https://generativelanguage.googleapis.com/v1beta/openai/` (config'teki değerle aynı). `reasoning_effort` destekleniyor (`minimal|low|medium|high`, Gemini 3 ailesinde `thinking_level`'a eşlenir; "reasoning cannot be turned off for Gemini 3 models"). `extra_body={"google": {"thinking_config": {"thinking_level": ..., "include_thoughts": ...}}}` de var; **kullanmayacağız**, `reasoning_effort` standart parametre. `response_format` (structured output) destekleniyor; `usage` alan adları sayfada ayrıntılı değil → implementasyonda gerçek cevaptan doğrulanacak.
- Model listesi: `gemini-3.8-flash` ve `gemini-3.5-flash-lite` ikisi de **Stable** (config/.env.example değerleri geçerli).
- `openai` PyPI güncel sürüm **3.17.0** (`>=3.10`). Major 3 — `chat.completions.create` yüzeyi ve `OpenAI(base_url=, api_key=, timeout=, max_retries=, http_client=)` parametreleri implementasyonda kurulu sürüm üzerinden doğrulanacak; plan bu imzayı varsayar, farklıysa raporda yazılır.

---

## 1. LLM istemcisi — `app/services/llm/`

```
app/services/llm/
  __init__.py          # public: LLMClient, LLMRequest, LLMResponse, LLMError*, build_llm_client
  base.py              # Protocol + dataclass'lar + hata hiyerarşisi
  openai_compatible.py # OpenAICompatibleClient (openai SDK + base_url; Gemini varsayılan)
  factory.py           # build_llm_client(settings) -> LLMClient  (LLM_PROVIDER'a göre)
```

### 1.1 İstek / cevap şekli
```python
@dataclass(frozen=True)
class LLMRequest:
    system: str
    user: str                         # tek kullanıcı mesajı (V0'da sohbet geçmişi yok)
    model: str                        # settings.llm_model_answer / _classify — çağıran seçer
    max_output_tokens: int
    temperature: float = 0.0
    reasoning_effort: Literal["minimal", "low", "medium", "high"] = "low"

@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    tokens_in: int                    # usage.prompt_tokens
    tokens_out: int                   # usage.completion_tokens (Gemini'de thinking dahil — SPEC_01 §5)
    tokens_reasoning: int | None      # usage.completion_tokens_details.reasoning_tokens, varsa
    finish_reason: str | None
    latency_ms: int

class LLMClient(Protocol):
    def complete(self, request: LLMRequest) -> LLMResponse: ...
```
Senkron (ADR-002: sync SQLAlchemy, endpoint threadpool'da). Streaming yok (V0). `messages = [{"role":"system",...},{"role":"user",...}]`, `max_completion_tokens=request.max_output_tokens` (`max_tokens` deprecated; SDK 3.x'te hangisinin geçtiği doğrulanacak), `temperature`, `reasoning_effort`.

### 1.2 Hata yönetimi
Tek kök `LLMError(Exception)`; alt sınıflar: `LLMNotConfiguredError` (API key yok), `LLMAuthError` (401/403), `LLMRateLimitError` (429), `LLMTimeoutError`, `LLMUnavailableError` (5xx / bağlantı), `LLMResponseError` (boş içerik, `finish_reason=content_filter/length` ile anlamsız cevap). SDK istisnaları `openai_compatible.py` içinde bu hiyerarşiye çevrilir; servis/API katmanı `openai` paketini import etmez. SDK'nın kendi retry'ı: `max_retries=1` (429/5xx için exponential backoff; Gemini ücretsiz katman sınırı — SPEC PHASES 4.1 notu). Timeout: `LLM_TIMEOUT_S`. API katmanı `LLMError` → **503** `"Yapay zeka servisi geçici olarak kullanılamıyor."` (`LLMNotConfiguredError` → 503 `"Yapay zeka servisi yapılandırılmamış."`), detay JSON log'a (SPEC_06 §8, ADR-017); API key hiçbir log/hata gövdesine girmez (`api_key` zaten maskeleniyor).

### 1.3 Token sayımı
- **Yetkili sayı API'nin `usage` alanıdır**; her çağrıda `app.services.llm` logger'ına `"llm call"` kaydı: `model, tokens_in, tokens_out, tokens_reasoning, latency_ms, finish_reason, prompt_chars`. Kriter 5'in "token sayıları loglanmış" kanıtı budur; Phase 3.4 aynı değerleri `audit_log`'a yazacak.
- Çağrı öncesi tokenizer **yok** (`tiktoken` 0.2'de de reddedilmişti: Gemini tokenizer'ıyla eşleşmez). Prompt boyutu `top_k × ~875 karakter ≈ 17 k karakter ≈ 5 k token` — Flash sınıfı için sorun değil; yalnızca `prompt_chars` loglanır.
- Yeni ayar: `LLM_REASONING_EFFORT=low` (`Settings.llm_reasoning_effort`, `.env.example`'a). SPEC_01 §5 "thinking bütçesi düşük tutulur" — sabit yerine env, çünkü maliyet/doğruluk denemesi Phase 4.1'de model karşılaştırmasıyla birlikte yapılacak. `temperature=0` sabit.

### 1.4 Factory ve DI
`build_llm_client(settings)`: `openai_compatible` → `OpenAICompatibleClient(base_url, api_key, timeout, max_retries)`; key boşsa `LLMNotConfiguredError` **çağrı anında** (uygulama import/startup'ta patlamaz — LLM yokken belge hattı çalışmalı, SPEC_06 §8). `anthropic` → bkz. SORU 3. `app/api/deps.py::get_llm_client` (`@lru_cache`'li factory sarmalayıcı); testler `app.dependency_overrides[get_llm_client]` ile `FakeLLMClient` verir — kriter 4'ün "prompt'a giden chunk'ları yakalama" mekanizması bu.

---

## 2. `POST /api/ask`

### 2.0 Akış (SPEC_02 §9 sırası, kod karşılığı)
```
AskRequest{question, department?, project_id?}
  → get_current_user (Step-0 stub: admin)
  → retrieve(session, user, search_query, filters)          # içinde allowed_document_ids → SQL filtre (değişmiyor)
      search_query = build_search_query(question)            # §2.1 (yeni)
  → chunk yoksa: NO_ANSWER, LLM çağrısı YOK, sources=[]      # kaynak yoksa standart cevap, sıfır token
  → documents = document_repo.get_many(ids) + load_chain()   # §2.3
  → chain = evaluate_version_chains(documents, DEMO_TODAY)   # deterministik, kodda (ADR-012)
  → prompt = build_answer_prompt(question, chunks, documents, chain)   # §2.4
  → llm.complete(...)                                        # yalnızca izinli chunk'lar (retrieve zaten garanti eder)
  → parse: NO_ANSWER tespiti + [K#] atıfları → sources       # §2.5
  → log "ask completed" → AskResponse
```
Dosyalar: `app/api/ask.py` (HTTP), `app/schemas/ask.py`, `app/services/ask.py` (orkestrasyon), `app/services/search_query.py`, `app/services/version_chain.py`, `app/services/answer_prompt.py` (prompt metni + kaynak formatı + atıf parse). Hiçbiri 400 satırı geçmez; `ask.py` ≈ 120 satır hedef.

### 2.1 Sorgu kurma — `build_search_query(question) -> str` (T1'in çözümü)
1. Kesme işareti ekleri atılır: `RES'in → RES`, `covenant'ı → covenant` (regex `'\S*`).
2. Noktalama temizlenir, kelimelere ayrılır, 2 karakterden kısa ve **Türkçe soru/bağlaç stoplist**'indeki kelimeler düşer (`ne, nedir, neydi, nedi̇r, hangi, kaç, kaçtır, mi, mı, mu, mü, ve, veya, ile, için, olan, olarak, bu, şu, o, bir, gibi, göre` — küçük sabit liste; Postgres `turkish` config'i bunları düşürmüyor: `nedir → 'ne'` olarak kalıyor).
3. Kalan terimler `" OR "` ile birleştirilir; `websearch_to_tsquery` OR sözdizimini doğal olarak anlıyor → `search_fts` **değişmez** (repo sorgu dilini bilmeye devam etmez, sadece string alır). Sıralama `ts_rank` (mevcut): OR'da daha çok terim eşleşen chunk üstte — canlı ölçümde Amendment s.3 > Facility s.6 (tablo T1).
4. Terim kalmazsa (soru yalnızca stopword) → boş sonuç → NO_ANSWER.

`retrieve()` imzası değişmez; `question` parametresine artık kurulmuş sorgu geçilir; `/api/documents`'ı ilgilendirmez. **ADR-020** olarak yazılır (ADR-007'yi supersede etmez, onu tamamlar: "FTS + metadata" kararı aynı, sorgu semantiği OR).

Not: OR semantiği İzmir sorusunda `res` üzerinden Ankara chunk'larını getirir. Bu **istenen** durum: kriter 3, "retrieval boş" gibi önemsiz bir yoldan değil, LLM'in kural-2 disiplininden (kaynaklar İzmir'i anlatmıyor → bilgi bulamadım) kanıtlanmış olur; retrieval boş yolu ayrıca birim testle kanıtlanır.

### 2.2 İstek / cevap şemaları — `app/schemas/ask.py`
```python
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    department: str | None = None          # → RetrievalFilters (Phase 1.2'de anlam kazanır)
    project_id: UUID | None = None

class SourceCard(BaseModel):
    ref: str                 # "K1" — cevaptaki atıf etiketi
    document_id: UUID
    title: str
    page_number: int         # ADR-008
    document_date: date
    effective_date: date | None
    version: int
    status: DocumentStatus
    is_current: bool         # zincir değerlendirmesinden (§2.3)
    supersedes_title: str | None
    superseded_by_title: str | None

class AskResponse(BaseModel):
    answer: str
    answered: bool           # False → answer == NO_ANSWER_TEXT
    sources: list[SourceCard]            # yalnızca cevapta atıf yapılanlar
    retrieved_document_ids: list[UUID]   # prompt'a giren belgeler (test/eval/audit için; zaten izinli)
    model: str | None
    tokens_in: int
    tokens_out: int
    notice: str = "Bu cevap yorum içermez; yalnızca şirket belgelerinde yazanı kaynak göstererek aktarır."  # ADR-014
```
Tarihler API'de ISO (kod İngilizce); DD.MM.YYYY biçimi prompt'ta ve HTML sayfada uygulanır.

### 2.3 Versiyon/tarih değerlendirmesi — `app/services/version_chain.py`
Girdi: retrieval'dan gelen belgeler + `supersedes/superseded_by` bağlantılarıyla yüklenen tam zincir (`document_repo.load_chain(session, document)` — iki yönde yürür, döngü koruması, yalnızca izinli id'ler; izinsiz zincir üyesi **yüklenmez**, sadece "başka bir belge tarafından değiştirilmiş" bilgisi kalır — ADR-004). Çıktı, belge başına:
```python
@dataclass(frozen=True)
class ChainPosition:
    position: int; chain_length: int
    in_force: bool          # (effective_date or document_date) <= DEMO_TODAY and (expiration_date is None or > DEMO_TODAY)
    is_current: bool        # zincirde in_force olan SON halka (ADR-012: "last link effective on DEMO_TODAY")
    is_initial: bool        # position == 1
    supersedes_title: str | None; superseded_by_title: str | None
```
`DEMO_TODAY` `settings.demo_today`'den (duvar saati asla). Zincirsiz tek belge: `position=1/1, is_current=in_force`. **LLM bu bayrakları hesaplamaz, sadece okur.** Chunk filtrelemesi yapılmaz: "güncel" sorusunda eski belge de prompt'ta kalır, çünkü SPEC_02 §9 örneği "Amendment 01 ile önceki 1,25x seviyesinden değiştirilmiştir" der — bu, eski değeri de görmeyi gerektirir.

**Zincirin kurulması (T2):** `POST /api/documents/upload`'a üç **opsiyonel** form alanı: `effective_date` (date), `version` (int ≥ 1, default 1), `supersedes_document_id` (UUID). Kurallar: hedef `allowed_document_ids` içinde değilse **404** (izinsiz belgeye bağ kurulamaz); hedefin `superseded_by_document_id`'si doluysa **409** `"Belge zaten başka bir belge tarafından güncellenmiş."` (DOMAIN_MODEL §6: tam olarak bir sonraki belge); aynı transaction'da hedefe `superseded_by_document_id` yazılır. Hedefin `status`'u **değiştirilmez** (SORU 1). Migration gerekmez — kolonlar 0002'de var; rapora "şema değişikliği yok" yazılır.

`seed_data/t0/upload.sh` (bash, curl + sed; jq yok): PDF'ler yoksa `generate.py`'yi çalıştırır; Facility Agreement'ı (executed, `document_date=effective_date=2023-06-01`, v1) sonra Amendment 01'i (`2025-03-15`, v1, `supersedes_document_id=<facility id>`) yükler, `status` `ready` olana kadar bekler. Taranmış kopya **yüklenmez** (T0 için gereksiz çift kaynak). README'ye girer.

### 2.4 Prompt tasarımı — `app/services/answer_prompt.py`
Sistem promptu Türkçe, sabit string (Python sabiti; `docs/prompts/ANSWER_SYSTEM_PROMPT.md`'ye kopyası — Naci'nin okuyup düzeltebilmesi için, kaynak koddur). Kural listesi (nihai metin implementasyonda):
1. **Yalnızca aşağıdaki kaynaklardan** cevap ver; kaynaklarda olmayan hiçbir rakam, tarih, isim, olay yazma; model bilgisiyle tamamlama (kural 2, SPEC_01 §7-A).
2. Cevap için yeterli bilgi yoksa **yalnızca** şu cümleyi yaz, başka hiçbir şey ekleme: `Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.`
3. Kaynaklar sorudaki **projeyi** (ör. İzmir RES) anlatmıyorsa, benzer başka projeden (Ankara RES) çıkarım **yapma** → kural 2 cümlesi (izolasyon).
4. Her bilgi cümlesinin sonuna kaynak etiketi: `[K1]`, `[K2]`. Etiketsiz olgu yazma.
5. Zaman: her kaynağın başlığında `Zincir:` satırı vardır. "güncel / şu anki / mevcut" → `GÜNCEL` işaretli belge; "ilk / orijinal / başlangıçta / önceden" → zincirin ilk halkası. Cevapta değişimi belirt: "Bu değer <belge> ile önceki <X> seviyesinden değiştirilmiştir." Eski değer yanlış değil, tarihsel değerdir (kural 5).
6. **Yorum, tahmin, öneri, projeksiyon yok.** "Neden?" sorusunda yalnızca belgede yazan sebep; yoksa `belgelerde sebep belirtilmemiş` (kural 6, ADR-014).
7. Dil: kaynak İngilizce olsa da **Türkçe** cevap; sayı biçimi kaynaktaki gibi (1,20x), tarih DD.MM.YYYY. Kısa ve düz; başlık/madde işareti gerekmedikçe yok.
8. Bugünün tarihi: `DEMO_TODAY` (DD.MM.YYYY) — "kaçıncı yıl / şu anda" için bu tarih.

Kullanıcı mesajı:
```
SORU: <question>

KAYNAKLAR:
[K1] Belge: Amendment 01 | Tarih: 15.03.2025 | Yürürlük: 15.03.2025 | Versiyon: 1 | Durum: executed | Sayfa: 3
     Zincir: GÜNCEL — "Facility Agreement" (01.06.2023) belgesini değiştirir
<chunk metni>

[K2] Belge: Facility Agreement | Tarih: 01.06.2023 | ... | Sayfa: 6
     Zincir: İLK HALKA — "Amendment 01" (15.03.2025) tarafından değiştirilmiş
<chunk metni>
```
Sıra: önce `is_current` belgelerin chunk'ları, sonra rank sırası (LLM'in "güncel"i baştan görmesi için; deterministik). Her `[K#]` tam olarak bir `(chunk_id)` → `(document, page)` eşlemesidir; kod tarafında `dict[str, RetrievedChunk]` tutulur. Prompt'a giren **tek** içerik `retrieve()` sonucudur; başka hiçbir yerden metin okunmaz (kriter 4'ün yapısal garantisi + test).

Çıktı biçimi: **düz metin + `[K#]` etiketleri** (JSON/structured output değil). Gerekçe: parse tek regex; JSON modunda model Türkçe metni kaçış karakterleriyle bozabiliyor ve `json_schema` desteği "beta" — kanıtlanmamış. Yedek: cevapta hiç `[K#]` yoksa ve NO_ANSWER değilse `sources=[]` + `warning` log (kaynaksız olgu cümlesi ihtimali) — Phase 4.1 eval'da "citations" kategorisi bunu yakalar.

### 2.5 Cevap işleme
- `NO_ANSWER` tespiti: normalize edilmiş cevap sabit cümleyi **içeriyorsa** (model ufak sapma yapabilir) `answered=false`, `answer` **kanonik** cümleyle değiştirilir, `sources=[]`.
- `[K(\d+)]` etiketleri → benzersiz, sıralı → `SourceCard` (aynı belge+sayfa tek kart). Bilinmeyen etiket (`[K9]` yokken) düşürülür + `warning` log.
- Log `"ask completed"` (`app.services.ask`): `user_id, question (ilk 200 karakter), retrieved_document_ids, cited_document_ids, answered, model, tokens_in, tokens_out, duration_ms`. Soru metninin kendisi bu fazda audit tablosuna değil, uygulama loguna gider; Phase 3.4 `audit_log`'a taşır (ADR-016). Şifre/anahtar bu kayda giremez (alan listesi sabit).

---

## 3. Minimal test arayüzü — öneri: **tek dosya HTML + curl, ikisi birden**

**Öneri:** `backend/app/static/ask.html` (tek dosya, framework yok, ~120 satır, inline CSS/JS, `fetch('/api/ask')`) → `GET /ask` ile `FileResponse`. Artı README'de curl örneği.

Gerekçe:
- T0'ın değeri, Naci'nin **aynı soruyu varyasyonlarıyla** (güncel / ilk / İzmir / "neden") arka arkaya sorup **kaynak kartlarını** (belge, sayfa, tarih, versiyon, GÜNCEL rozeti) görmesi. curl'de Türkçe karakter + JSON kaçışı + 20 satırlık cevap gövdesini okumak bu döngüyü yavaşlatır.
- Maliyet düşük: build yok, bağımlılık yok, Caddy yok, `docs/PHASES.md`'nin "backend'den servis" seçeneğiyle birebir. Playwright/UI testi yok (kapsam dışı); tek pytest: `GET /ask` → 200, `text/html`, "Sorunuzu yazın" içerir.
- Phase 3.3'te Caddy `/` ve `/api`'yi alınca bu sayfa dışarıdan görünmez olur; silinmez, geliştirici sayfası olarak backend'de kalır (karar Phase 3.3'e).
- curl yine de birincil **kanıt** aracıdır: rapora giren çıktılar curl'den alınır (kopyalanabilir, deterministik).

Sayfa: soru kutusu, "Sor" butonu, cevap metni, kaynak kartları (`SourceCard` alanları; `is_current` → "GÜNCEL" rozeti; tarih DD.MM.YYYY), üstte `notice`, altta `model / token in-out / request_id`. Türkçe UI metinleri (SPEC_01 §2: "Sorunuzu yazın", "AI'ya Sor", "Kaynaklar"). Hata → `detail` alanı gösterilir (stack trace yok — mevcut error handler).

---

## 4. Kabul kriteri → kanıt

İki katman: **offline** (`make test`, `FakeLLMClient`, ağ yok — CI'da/prod klonunda deterministik) ve **canlı** (`make test-llm`, gerçek Gemini; `LLM_LIVE_TESTS=1` + `LLM_API_KEY` yoksa atlanır; SORU 4). Kriter 1–3 ve 5a'nın nihai kanıtı canlı katman + raporda curl çıktısıdır; 4 ve 5b offline kanıtlanır.

| # | Kriter (PHASES.md) | Test / komut | Kanıt (assert) |
|---|---|---|---|
| 1 | "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → 1,20x + Amendment 01 + sayfa | `tests/live/test_t0_live.py::test_current_dscr_is_amendment` (T0 fixture: gerçek PDF sayfa metinleri PyMuPDF ile chunk'lanır, zincir kurulu) + raporda `curl -d '{"question": ...}' /api/ask` çıktısı | `answered`; `"1,20" in answer` (veya `1.20`/`1,2`); `sources[0].title == "Amendment 01"` ve `is_current`; `page_number == 3`; cevapta "Facility Agreement" / "1,25" değişim cümlesi |
| 2 | "İlk DSCR covenant neydi?" → 1,25x + EXECUTED + sayfa; iki cevap farklı | `::test_initial_dscr_is_executed_and_differs` | `"1,25" in answer`; kaynaklar arasında `title=="Facility Agreement"`, `status=="executed"`, `page_number==6`; `answer_q2 != answer_q1` ve `"1,20"` cevabın ana değeri değil (K-etiketli ilk cümle 1,25) |
| 3 | "İzmir RES'in COD tarihi nedir?" → "bilgi bulamadım" | `::test_izmir_cod_no_answer` (**OR retrieval Ankara chunk'larını verir**, LLM reddetmeli) + offline `tests/test_ask.py::test_no_chunks_means_no_llm_call` (retrieval boş → sıfır LLM çağrısı) | `answered is False`; `answer == NO_ANSWER_TEXT`; `sources == []`; offline testte `fake.calls == 0`, `tokens_in == 0` |
| 4 | Prompt'a giden chunk'lar test ile yakalanır; `allowed_document_ids` dışı hiçbir chunk yok | `tests/test_ask.py::test_prompt_contains_only_allowed_chunks` (3 belge: 2 finance, 1 legal `SENTINEL-GIZLI-…` metniyle; `department=finance` scope'u **gerçek** `SqlDocumentIdsProvider` üzerinden) + `::test_prompt_empty_when_gate_returns_empty` (pasif kullanıcı → LLM çağrısı yok) + `::test_prompt_respects_fake_gate_subset` (`allowed_document_ids` monkeypatch ile alt küme) | `FakeLLMClient.requests[0]` içindeki `system+user` metninde izinli chunk metinleri **var**, sentinel **yok**; `retrieved_document_ids ⊆ allowed`; her chunk `document_id`'si allowed kümesinde |
| 5a | Cevaplar Türkçe, kaynak İngilizce olsa da | canlı testler 1–2: cevapta Türkçe'ye özgü karakter (`çğıöşü`) ve `"covenant"` dışı İngilizce cümle yok (sezgisel: `" the "`, `" is "` geçmez) + rapora yapıştırılan cevaplar | assert'ler + rapor |
| 5b | Token sayıları loglanmış | `tests/test_ask.py::test_llm_call_logs_token_counts` (`caplog`, logger `app.services.llm`) + `tests/test_llm_client.py::test_usage_parsed` (httpx `MockTransport` ile sahte `usage`) | kayıtta `tokens_in`, `tokens_out` int; `"ask completed"` kaydında aynı alanlar |

Destekleyici testler: `test_search_query.py` (kesme eki, stoplist, OR birleştirme, "yalnızca stopword → boş"; T1 tablosundaki 3 soru için gerçek T0 sayfalarıyla **hit sayısı > 0 / == beklenen belge**), `test_version_chain.py` (tek belge; iki halka; gelecek tarihli halka → önceki güncel; `expiration_date` geçmiş; döngü koruması; izinsiz halka yüklenmez), `test_llm_client.py` (istek gövdesi: `model`, `reasoning_effort`, `max_completion_tokens`, `temperature`; 401→`LLMAuthError`; 429→`LLMRateLimitError`; timeout→`LLMTimeoutError`; boş choices→`LLMResponseError`; key yok→`LLMNotConfiguredError`), `test_ask.py` ek: 422 (boş soru), 503 (LLMError → Türkçe mesaj, gövdede istisna metni yok), `[K9]` bilinmeyen etiket düşer, NO_ANSWER içeren cevap kanonikleşir; `test_documents.py` ek: `supersedes_document_id` → hedefe `superseded_by` yazılır; izinsiz hedef 404; dolu hedef 409; `test_ask_page.py`.

T0 fixture (`tests/t0_fixtures.py`): `seed_data/t0/*.pdf` yoksa `generate.main()` çağrılır (WeasyPrint backend image'ında var); sayfa metinleri `pymupdf` ile okunup `document_pages` + `document_chunks` (sayfa başına 1 chunk — sayfalar 800 kelimenin altında, worker'ın çıktısıyla aynı) doğrudan yazılır; ocr-worker'a bağımlılık yok.

Canlı doğrulama komutu (rapora girer): `make up` → `bash seed_data/t0/upload.sh` → üç soru için `curl -s -X POST localhost:8000/api/ask -H 'content-type: application/json' -d @q.json`; `make logs SVC=backend | grep '"llm call"'` token kaydı.

---

## 5. SORU (Naci cevaplamalı)

1. **SORU: Zincir kurma yolu ve `status`.** Önerim: `upload`'a opsiyonel `effective_date`/`version`/`supersedes_document_id` (§2.3) + `seed_data/t0/upload.sh`. Alternatif: yalnızca seed script'in DB'ye doğrudan yazması (API'siz). Ayrıca: Amendment 01 yüklendiğinde Facility Agreement'ın `status`'u `executed` kalsın mı (önerim: **kalsın**, PHASES kriter 2 "1,25x + EXECUTED" diyor; `amended/superseded` geçişleri Phase 3.2'nin işi), yoksa otomatik `amended` olsun mu?
2. **SORU: Proje izolasyonu 0.3'te yalnızca içerik + prompt kuralıyla.** `projects` tablosu Phase 1.2'de; `project_id` boş kalıyor, `AskRequest.project_id` filtresi yapısal olarak var ama T0'da kullanılamıyor. İzmir kriteri LLM disiplinine (kural 3) dayanacak; yapısal proje filtresi 1.2'de gelince eval'a eklenir. Kabul mü?
3. **SORU: `AnthropicClient` bu fazda mı?** PHASES/ADR-009 "opsiyonel" diyor; talimatın 1. maddesinde yok. Önerim: **ertelenir** — factory `LLM_PROVIDER=anthropic` için açık `LLMNotConfiguredError("V0'da yapılandırılmadı")` verir; Phase 4.3 karar noktasında ("Gemini yeterli mi") gerekirse eklenir (~60 satır, `anthropic` SDK). Şimdi eklenirse canlı test edilemez (Anthropic anahtarı yok).
4. **SORU: Canlı LLM testleri `make test`'in dışında mı?** Önerim: ayrı `make test-llm` (`LLM_LIVE_TESTS=1`; anahtar/ağ yoksa `skip`), `make test` tamamen offline kalır (prod klonunda ve anahtarsız ortamda yeşil). Rapor canlı testin çıktısını içerir.
5. **SORU: Dev DB sıfırlama izni.** Canlı DB'de 0.2'den kalan 4 belge var (Facility, Amendment 01 — zincirsiz; taranmış kopya; Corrupt). T0 doğrulaması için dev verisini sıfırlamayı (`make down` → `data/postgres` + `data/documents` silme → `make up` → `upload.sh`) öneriyorum; alternatif, zinciri elle SQL ile kurmak. Hangisi?
6. **SORU: `LLM_REASONING_EFFORT` env değişkeni** (varsayılan `low`) eklensin mi, yoksa `low` sabit mi kalsın? (Önerim: env, §1.3 gerekçesiyle.)

---

## 6. Kendi aldığım küçük kararlar (raporda da listelenecek)
- OR sorgu semantiği + Türkçe soru-kelimesi stoplist'i (`search_query.py`); `search_fts` ve `retrieve` imzaları değişmez. → ADR-020.
- Cevap hattı: retrieval boşsa LLM çağrılmaz; zincir bayrakları kodda; kaynaklar `[K#]` atıflarından; LLM hatası 503 Türkçe. → ADR-021.
- Düz metin + `[K#]` (JSON mode değil), `temperature=0`, `max_retries=1`, tek sistem + tek kullanıcı mesajı, streaming yok.
- `sources` = yalnızca atıf yapılanlar; `retrieved_document_ids` ayrıca döner (eval/audit için).
- `retrieval_top_k=20` aynen; prompt ~17 k karakter.
- Prompt sabiti `docs/prompts/ANSWER_SYSTEM_PROMPT.md`'de de tutulur (kaynak = Python; test ikisinin aynı olduğunu doğrular).
- `GET /ask` sayfası Phase 3.3'te de silinmez (geliştirici sayfası).
- Migration yok (şema değişmedi); `pyproject`'e `openai>=3.17,<4`.

## 7. Doküman değişiklikleri
- `docs/ARCHITECTURE.md`: ADR-020 (sorgu kurma), ADR-021 (cevap hattı). ADR-009'a not: Anthropic ertelendi (SORU 3 cevabına göre).
- `README.md`: "Soru sorma (Phase 0.3)" bölümü (curl + `/ask`), LLM env açıklaması, `make test-llm`, bilinen sınırlar güncellemesi.
- `infra/.env.example`: `LLM_REASONING_EFFORT`, `LLM_LIVE_TESTS` (yorumlu).
- `Makefile`: `test-llm`.
- `docs/reports/PHASE_0_3_REPORT.md`, `docs/PHASES.md` durum satırı, `git tag phase-0-3`.

## 8. Uygulama sırası
1. `openai` bağımlılığı + `llm/` paketi + `test_llm_client.py` (MockTransport).
2. `search_query.py` + testleri (T0 sayfalarıyla hit doğrulaması).
3. Upload'a zincir alanları + `document_repo.load_chain/get_many/set_superseded_by` + testler.
4. `version_chain.py` + testleri.
5. `answer_prompt.py`, `ask.py`, `schemas/ask.py`, `api/ask.py`, `deps.get_llm_client`, `FakeLLMClient` + `test_ask.py` (kriter 3-offline, 4, 5b).
6. `ask.html` + `GET /ask` + test.
7. `seed_data/t0/upload.sh`; dev DB sıfırlama (SORU 5); canlı T0: 3 soru + log kanıtı; `tests/live/` + `make test-llm`.
8. `make test` + `make lint` yeşil → ADR-020/021, README, .env.example → rapor → PHASES.md → commit + tag + push.

## Kritik dosyalar
- `backend/app/services/llm/openai_compatible.py`, `backend/app/services/ask.py`, `backend/app/services/answer_prompt.py`
- `backend/app/services/search_query.py` (T1), `backend/app/services/version_chain.py` (T2)
- `backend/app/api/ask.py`, `backend/app/api/documents.py` (zincir alanları)
- `backend/tests/test_ask.py` (kriter 4), `backend/tests/live/test_t0_live.py` (kriter 1–3, 5a)
- `seed_data/t0/upload.sh`, `backend/app/static/ask.html`
