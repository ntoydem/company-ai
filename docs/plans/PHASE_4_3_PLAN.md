# Phase 4.3 — Mixed query (router): Implementation Plan

## Bağlam ve tespitler

Phase 4.2 (`phase-4-2`) DATA yolunu ayrı bir uçta (`POST /api/excel/ask`) bıraktı; `/api/ask` DOCUMENT-only. Bu faz
ADR-010'un router'ını getiriyor: `/api/ask` tek giriş noktası olur, soru `DOCUMENT | DATA | MIXED | GENERAL` olarak
sınıflanır, MIXED iki alt sorgu + yorumsuz birleştirme, GENERAL şirket verisi kullanmaz ve bunu söyler.

Okunanlar: `docs/PHASES.md` (4.3), `docs/SPEC_04` §7-8, ADR-010/011/014/021, `docs/reports/PHASE_4_2_REPORT.md` §8,
kod: `services/ask.py::answer_question`, `services/excel_ask.py::answer_data_question`, `schemas/{ask,excel}.py`,
`api/ask.py`, `services/metadata_suggestion.py` (json_object classify deseni), `frontend/src/{api/types.ts,
components/{AskPanel,SourceCardList}.tsx}`, `scripts/eval_lib.py`, `ledger_schema.QuestionCategory`,
`seed_data/master/ankara_res.yaml` (`incidents`, `budget_vs_actual`), `prose/DOC-ANK-OPS-001.yaml`.

### T1 — Kabul kriterindeki "EBITDA sorusu" mevcut veriyle **cevaplanamaz**
Ledger'da EBITDA yok (CFADS çeyreklik var, bütçe/gerçekleşen çeyreklik TRY var); belgelerde EBITDA kelimesi yok.
SPEC_04 §8'in "üretim düşüşünün finansal etkisi + teknik nedeni" senaryosu için ledger'da `incidents` (2024-07-08
"Türbin dişli kutusu arızası (T-07), 11 gün duruş", 2025-01-22 şebeke kesintisi) var ama **hiçbir belge bunları
anlatmıyor** — Production Report Ağustos 2026 genel bir metin, Maintenance Report yok (Phase 5.1 envanteri). Yani
"sebep belgede yazıyor mu?" dalının **pozitif** örneği bugün üretilemez, yalnızca "belgelerde sebep belirtilmemiş"
(kural 6) dalı test edilebilir. Karar **SORU 1**.

### T2 — İki alt servis zaten "bir soru → cevap + kartlar" sözleşmesinde; router onları çağırır, kopyalamaz
`answer_question(session, user, AskRequest, llm, settings) -> AskResult` ve `answer_data_question(session, user,
ExcelAskRequest, llm, settings, engine) -> ExcelAskResult` imzaları birbirine paralel. Router her ikisini
**aynen** çağırır (4.2 raporu §8). Tek engel: ikisi de kendi `audit_log` satırını yazıyor — MIXED'de iki (hatta
router için üç) satır olur; SPEC_06 "her `/api/ask` çağrısı bir satır" der. Çözüm §2, karar **SORU 2**.

### T3 — Frontend Excel kartını bilmiyor
`AskResponse`/`SourceCard` yalnızca belge; `SourceCardList` sayfa/versiyon gösteriyor. 4.2 raporu §8: "Sor ekranı
Excel kaynak kartını öğrenmeli". Bu fazda küçük bir frontend değişikliği kaçınılmaz (§3) — Phase 3.3 deseniyle
(elle doğrulama + ekran görüntüsü, Playwright yok).

### T4 — Eval soru setinde `data`/`mixed` kategorisi tanımlı ama **sıfır soru** var
`QuestionCategory` `data`/`mixed`'i içeriyor, `questions.json` v1'de yok; `eval_lib` Excel kaynak kartını
(`file`/`sheet`/`range`) tanımıyor. Kabul kriterlerini eval ile de kanıtlamak için birkaç soru + `eval_lib` eki
gerekir (**SORU 3**).

### T5 — Sınıflandırma için ek bir LLM çağrısı kaçınılmaz, ama ucuz
Kural tabanlı sınıflandırma ("kaç"/"toplam" → DATA) "güncel DSCR kaç?" gibi belirsiz soruları yanlış keser —
spec bunları MIXED istiyor. `LLM_MODEL_CLASSIFY` + `json_object` (Phase 3.2/4.2 deseni), ~300-400 token, few-shot
SPEC_04 §7'nin dört örneği. Çağrı sayısı soru başına: DOCUMENT 1+1, DATA 1+2, MIXED 1+1+2 = 4, GENERAL 1+1. Ücretsiz
katmanda (5 istek/dk) eval süresi uzar — `run_eval` aralığı zaten 13 sn, MIXED sorular için ~50 sn/soru.

### T6 — GENERAL'de "şirket verisi kullanılmadı" ölçülebilir olmalı
`allowed_document_ids`/`retrieve`/`answer_data_question` hiç çağrılmaz; `audit_log.documents_retrieved=[]`,
`excel_files_used=[]`, `sources=[]`, `query_type=GENERAL_QUERY`; cevap sabit cümleyle başlar. Testte sahte
`allowed_document_ids` ile "hiç çağrılmadı" doğrulanır (monkeypatch deseni, `test_ask.py`).

---

## 1. Router tasarımı — `app/services/router.py`

```python
QueryType = Literal["DOCUMENT_QUERY", "DATA_QUERY", "MIXED_QUERY", "GENERAL_QUERY"]

@dataclass(frozen=True)
class RoutedQuestion:
    query_type: QueryType
    document_question: str | None   # DOCUMENT/MIXED: belge alt sorusu (MIXED'de LLM yeniden yazar)
    data_question: str | None       # DATA/MIXED: Excel alt sorusu
    reason: str                     # log-only

def classify(question: str, llm: LLMClient, settings: Settings) -> RoutedQuestion
```
- **Ayrı, tek LLM çağrısı** (T5): `LLM_MODEL_CLASSIFY`, `response_format="json_object"`, `max_output_tokens=300`,
  sistem promptu (İngilizce, kısa) dört tipin tanımı + SPEC_04 §7'nin dört örneği + "belirsiz 'güncel DSCR kaç?' →
  MIXED, belge sorusu 'güncel minimum DSCR covenant nedir?', veri sorusu 'en son çeyreğin gerçekleşen DSCR'i kaç?'"
  kuralı. Çıktı `{"query_type": ..., "document_question": ..., "data_question": ...}`; Pydantic ile doğrulanır.
- **Hata/parse hatası → `DOCUMENT_QUERY`** (mevcut davranış; asla soru kaybolmaz). GENERAL'e düşürme yalnızca
  LLM açıkça söylerse — şirket verisi kullanmayan bir cevaba yanlışlıkla düşmek en riskli hata (kaynaksız cevap).
- Mevcut `/api/ask` akışına **entegre**: `api/ask.py` → `services/ask_router.py::answer(...)` → `classify` →
  dal. `answer_question` ve `answer_data_question` **değişmeden** çağrılır (T2); yalnızca `write_audit=False`
  parametresi eklenir (§2). `/api/excel/ask` kalır (doğrudan DATA, router'sız; testler ve ileride araçlar için —
  **SORU 5**).
- Router bir servis, sabit arayüz (ADR-010): `RouterService.route(question) -> RoutedQuestion`; V0'da tek
  implementasyon `LLMRouter`; testlerde `FakeRouter` (sabit tip döndürür) — `/api/ask` dallarını LLM'siz test etmek
  için `get_router` dependency'si (`get_llm_client` deseni).

## 2. MIXED — iki alt sorgu, yorumsuz birleştirme

`ask_router.answer()`:
```python
routed = classify(...)
doc = answer_question(session, user, AskRequest(question=routed.document_question, ...), llm, settings,
                      write_audit=False)            if routed.query_type in (DOCUMENT, MIXED)
data = answer_data_question(session, user, ExcelAskRequest(question=routed.data_question, ...), llm, settings,
                            engine, write_audit=False) if routed.query_type in (DATA, MIXED)
```
- **Birleştirme deterministik, üçüncü LLM çağrısı yok** (spec: "yorum yok"): `answer = doc.answer + "\n\n" +
  data.answer` — her parça kendi etiketlerini korur (`[K1]` / `(Covenant_Report.xlsx Q2_2026!D14)`); MIXED'de
  parçaların başına sabit Türkçe başlık: "Belgelere göre: …" / "Excel verisine göre: …". Biri `answered=False`
  ise o parça sabit metniyle kalır (örn. Excel yoksa "Erişebildiğiniz Excel dosyalarında … bulamadım."), cevap
  `answered = doc.answered or data.answered`.
- **Audit (SORU 2):** iki alt servise `write_audit: bool = True` parametresi; router çağırırken `False` verir ve
  **tek satır** yazar: `query_type` gerçek tip (artık `DOCUMENT_QUERY` sabiti değil), `documents_retrieved` +
  `chunks_retrieved` belge dalından, `excel_files_used` + Excel kartları veri dalından, `sources` = iki kart
  listesinin birleşimi (JSON'da `kind: "document" | "excel"` alanı), `tokens_*` toplamı (router çağrısı dahil),
  `model` = cevap modeli. `_write_audit_log` `services/audit_writer.py`'ye taşınır (ask.py + excel_ask.py + router
  ortak; kopya yok).
- Kod tekrarı: `ask.py`'nin `AskResult` ve `excel_ask.py`'nin `ExcelAskResult`'ı olduğu gibi kalır; router yalnızca
  `MergedAnswer(answer, answered, query_type, sources, excel_sources, retrieved_document_ids, model, tokens)`
  üretir ve `AskResponse`'a eşler.

## 3. İki kaynak türü tek cevapta

- `AskResponse` **geriye uyumlu genişler**: `query_type: QueryType`, `excel_sources: list[ExcelSourceCard] = []`,
  `data_notice: str | None` (GENERAL'de sabit cümle). `sources` belge kartları olarak kalır (frontend/eval/audit
  bozulmaz).
- Frontend (T3, küçük): `types.ts`'e `ExcelSourceCard` + `query_type`; `SourceCardList` altında ikinci liste
  `ExcelSourceCardList` (dosya, sheet!range, indir linki — `document_id` ile `downloadUrl`); cevap başında tip
  rozeti (`Belge` / `Excel` / `Belge + Excel` / `Genel bilgi`); GENERAL'de `data_notice` sarı bilgi kutusu.
  `strings.ts`'e 6-8 Türkçe metin. `make lint` (eslint+tsc) + tarayıcıda elle doğrulama + 4 ekran görüntüsü
  (`docs/reports/assets/phase_4_3/`), Phase 3.3 deseni.
- Audit `sources` JSONB: belge kartları `{"kind":"document", ...SourceCard}`, Excel kartları `{"kind":"excel",
  ...ExcelSourceCard}` — admin API/5.2 paneli ayırt edebilsin.

## 4. Belirsiz "güncel DSCR kaç?" → iki değer, iki kaynak türü

Tetikleme router promptunda **açık kural + örnek**: "Bir soru hem sözleşme/covenant/limit hem gerçekleşen/ölçülen
değeri kastedebiliyorsa (belirsiz 'güncel DSCR', 'DSCR kaç', 'vade ne kadar' vb.) MIXED: `document_question` =
sözleşmedeki güncel değeri soran cümle, `data_question` = en son dönem gerçekleşen değeri soran cümle."
Beklenen uçtan uca: belge dalı → "…güncel minimum DSCR covenant'ı 1,20x'tir [K1]" (Amendment 01); veri dalı →
`dscr(Q2_2026)` → "…2026 Q2 DSCR 1,37x" (`Covenant_Report.xlsx Q2_2026!D14`). Birleşik cevapta iki değer, iki
kart türü; test hem sahte router/LLM ile (deterministik) hem canlı (`make test-llm`) koşar.
Belirsizlik çözümü **modelden değil** kuraldan gelir: router "MIXED" dedi mi, iki dal **her zaman** koşar;
biri boş dönerse boşluğu sabit metin doldurur, model "birini seçmez".

## 5. GENERAL — şirket verisi kullanılmadığının belirtilmesi

- Router `GENERAL_QUERY` derse: retrieval **yok**, Excel **yok**, yetki sorgusu **yok** (T6). Tek LLM çağrısı
  (`LLM_MODEL_ANSWER`, `services/general_answer.py`), sistem promptu: "Genel bilgi sorusu. Kısa, Türkçe, tanım/
  açıklama; şirkete, projeye, rakama, belgeye atıf yapma; yorum/tavsiye yok." Cevabın **başına** sabit cümle kod
  ile eklenir (modelden beklenmez): `GENERAL_NOTICE = "Bu cevap genel bilgidir; şirket belgeleri veya verileri
  kullanılmamıştır."` — `AskResponse.data_notice` alanında da döner, frontend bilgi kutusunda gösterir.
- Güvenlik ağı: model cevabında proje adı ("Ankara RES"/"İzmir RES"), demo SPV/taraf adları veya ledger'daki
  rakam kalıpları (3+ haneli sayı + para birimi) geçerse cevap **şablona** düşer ("Bu soru genel bir bilgi
  sorusudur; şirket verisi kullanılmadan kısa bir tanım için soruyu yeniden sorun." değil — daha basit: notice +
  modelin cevabı yerine "Şirket verisi kullanılmadan cevaplanır: <ilk cümle>"). **SORU 4** (GENERAL'de model
  bilgisiyle cevap verilsin mi, yoksa yalnızca "bu genel bir soru, şirket verisi yok" denip bırakılsın mı).
- Audit: `query_type=GENERAL_QUERY`, boş kaynaklar; test bunu ve `allowed_document_ids`'in hiç çağrılmadığını
  doğrular.

## 6. Kabul kriteri → kanıt

| Kriter (PHASES.md) | Kanıt |
|---|---|
| EBITDA sorusu → Excel farkı + belge kaynağı + yalnızca belgedeki sebep | **SORU 1'e bağlı.** Önerilen örnek: "Ankara RES Q3 2024 bütçe sapması neydi ve sebebi belgelerde yazıyor mu?" → router MIXED → veri dalı `budget_variance(Q3_2024)` = −894.000 TRY (`Budget_vs_Actual_2026.xlsx Summary!D5`) + belge dalı kural 6 → "belgelerde sebep belirtilmemiş" (sebep hiçbir belgede yok — dürüst sonuç). `tests/test_ask_router.py::test_mixed_budget_question…` (sahte router+LLM) + canlı |
| belirsiz DSCR → iki değer iki kaynak türü | `test_ask_router.py::test_ambiguous_dscr_returns_covenant_and_actual` (sahte router MIXED, sahte LLM iki cevap; assert 1,20x + 1,37x, `sources[0].title="Facility Agreement Amendment 01"`, `excel_sources[0].label="Covenant_Report.xlsx Q2_2026!D14"`); canlı `tests/live/…::test_ambiguous_dscr_is_routed_mixed` (gerçek router + gerçek LLM, `make test-llm`) |
| GENERAL sorularda şirket verisi kullanılmaz ve bu belirtilir | `test_ask_router.py::test_general_question_uses_no_company_data` (monkeypatch `allowed_document_ids` → çağrılırsa `AssertionError`; `sources==[]`, `excel_sources==[]`, cevap `GENERAL_NOTICE` ile başlar, audit satırı `documents_retrieved==[]`); canlı "DSCR ne demek?" |
| Router tipleri (ADR-010) | `test_router.py`: dört tip için sahte LLM JSON → `RoutedQuestion`; bozuk JSON → DOCUMENT; `test_ask_router.py` her dal için `/api/ask` 200 + `query_type` |
| Audit tek satır (SORU 2) | `test_ask_router.py::test_mixed_writes_one_audit_row_with_both_source_kinds` |
| Eval (SORU 3) | `questions.json` v1.1: 3 `data` + 2 `mixed` + (`general` kategorisi yok → `hallucination`/`document` dışı; SORU 3) — `make eval` mevcut eşikler + yeni kategoriler ≥%80 |
| Frontend | `make lint` + ekran görüntüleri (DOCUMENT, DATA, MIXED, GENERAL) |
| Naci karar noktası (Gemini yeterli mi) | Raporda soru tipine göre çağrı/token/süre tablosu (canlı ölçüm) |

---

## SORU (Naci cevaplamalı)

1. **"EBITDA sorusu" kriteri (T1).** EBITDA de, arıza/sebep anlatan belge de yok. Seçenekler: (a) kriteri mevcut
   veriyle **yeniden ifade et**: "Q3 2024 bütçe sapması + sebebi belgelerde var mı?" → Excel farkı + "belgelerde
   sebep belirtilmemiş" (kural 6'nın negatif dalı kanıtlanır; pozitif dal Phase 5.1'de Maintenance Report gelince
   eklenir); (b) bu fazda küçük bir içerik eklemesi: Production Report Ağustos 2026 prose'una `incidents`'tan
   token'lı bir cümle ("… [[incident_date]] tarihli [[incident_type]] nedeniyle üretim kaybı yaşanmıştır")
   — ama 2026 raporuna 2024 arızası yazmak anakronik; yeni bir "Bakım Raporu Temmuz 2024" belgesi (prose + ledger
   envanteri + reseed) 3.2c ölçeğinde bir içerik işi. Önerim **(a)** — 4.3 router fazı, içerik fazı değil;
   pozitif örnek 5.1'e not.
2. **Audit: MIXED tek satır mı?** Önerim tek satır (`query_type=MIXED_QUERY`, iki kart türü `kind` alanıyla, token
   toplamı) — alt servislere `write_audit=False`; `/api/excel/ask` doğrudan çağrıldığında kendi satırını yazmaya
   devam eder. Alternatif: alt satırlar + router satırı (3 satır) — daha izlenebilir ama SPEC_06'nın "çağrı başına
   bir satır"ıyla çelişir.
3. **Eval soru seti v1.1 şimdi mi?** Önerim: `questions.json`'a 3 `data` ("Ankara RES 2026 Q2 DSCR kaç?", "2026
   toplam üretim kaç MWh?", "Q2 2026 bütçe sapması?"), 2 `mixed` ("güncel DSCR kaç?", SORU 1'in sorusu) ve
   `eval_lib`'e Excel kartı eşleme (`required_sources`'ta dosya adı `Covenant_Report.xlsx` → `excel_sources[].file`)
   eklensin; şema `expected_answer` yolu ledger'a zaten var (`covenant_tests[-1].dscr`, `budget_vs_actual[...]`).
   GENERAL için kategori yok — `QuestionCategory`'ye `general` eklemek şema değişikliği; önerim bu fazda test ile
   yetinmek, `general` kategorisini 5.1 v2'ye bırakmak. Yoksa hepsini 5.1'e mi bırakalım (4.3 yalnızca pytest+canlı)?
4. **GENERAL cevabı modelin genel bilgisinden gelsin mi?** SPEC "genel bilgi; şirket verisi kullanılmaz, cevapta
   bu belirtilir" diyor — yani cevap veriliyor. Önerim: evet, kısa tanım + sabit notice, §5'teki sızıntı ağıyla.
   Alternatif (daha muhafazakâr): yalnızca "Bu genel bir bilgi sorusu; sistem şirket belgelerine dayalı cevap verir"
   deyip tanım vermemek.
5. **`/api/excel/ask` kalsın mı?** Önerim kalsın (router'sız DATA; 4.2 testleri, ileride Excel-özel ekran).
   Frontend Sor ekranı yalnızca `/api/ask` kullanır.

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- Router LLM çıktısı Pydantic ile doğrulanır; her hata → `DOCUMENT_QUERY` (mevcut davranış korunur).
- MIXED birleştirme deterministik (başlık + iki parça), üçüncü LLM çağrısı yok; parça sırası belge → Excel.
- `AskResponse` geriye uyumlu genişler (`query_type`, `excel_sources`, `data_notice`); `sources` anlamı değişmez.
- `_write_audit_log` ortak `services/audit_writer.py`'ye taşınır; JSON kartlara `kind` alanı.
- `get_router` dependency + `FakeRouter` test ikilisi (`get_llm_client`/`FakeLLMClient` deseni).
- GENERAL notice kodla eklenir, modele bırakılmaz; sızıntı ağı (proje/taraf adı, rakam+para birimi) şablona düşürür.
- Frontend: yalnızca kart listesi + rozet + bilgi kutusu; yeni sayfa/route yok.
- `docs/prompts/ROUTER_PROMPT.md` + `GENERAL_PROMPT` `make prompt-doc`/lint eşitliğine girer (mevcut desen).

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: ADR-010'a "Phase 4.3 concretization" (LLM router, JSON şeması, DOCUMENT fallback, MIXED
  deterministik birleştirme, GENERAL notice + sızıntı ağı, tek audit satırı); ADR-016 (`query_type` artık gerçek,
  `sources.kind`); ADR-021 (`/api/ask` artık router'dan geçer).
- `docs/DOMAIN_MODEL.md` `query_type` notu ("router 4.3'te geldi").
- README "Soru sorma": dört tip, örnek `curl`'ler (`query_type`, `excel_sources`), GENERAL notice; "Excel analizi":
  `/api/ask` artık DATA'yı da yönlendirir.
- `docs/prompts/ROUTER_PROMPT.md`, `docs/reports/PHASE_4_3_REPORT.md` (+ `assets/phase_4_3/` ekran görüntüleri,
  çağrı/token tablosu Naci'nin Gemini kararı için), `docs/PHASES.md`, `git tag phase-4-3`.

## Uygulama sırası

1. `services/audit_writer.py` (ortak), `ask.py`/`excel_ask.py` `write_audit` parametresi (davranış değişmez) + testler.
2. `services/router.py` (`classify`, `RoutedQuestion`, prompt) + `test_router.py`; `get_router` dependency + `FakeRouter`.
3. `services/general_answer.py` + sızıntı ağı + testler.
4. `services/ask_router.py::answer()` (dört dal, MIXED birleştirme, tek audit) + `AskResponse` genişlemesi +
   `api/ask.py` bağlantısı + `test_ask_router.py` (kabul kriterleri tablosu).
5. Frontend: tipler, `ExcelSourceCardList`, rozet, notice; `make lint`; elle doğrulama + ekran görüntüleri.
6. SORU 3'e göre `questions.json` v1.1 + `eval_lib` Excel kartı eşleme + `make eval`.
7. Canlı: `make test-llm` (belirsiz DSCR, GENERAL, SORU 1 sorusu); çağrı/token/süre ölçümü.
8. Dokümanlar → rapor → PHASES.md → commit + tag `phase-4-3` + push.

## Kritik dosyalar

- `backend/app/services/{router,ask_router,general_answer,audit_writer}.py` (yeni), `ask.py`, `excel_ask.py`
- `backend/app/api/{ask,deps}.py`, `backend/app/schemas/ask.py`
- `frontend/src/api/types.ts`, `frontend/src/components/{AskPanel,SourceCardList}.tsx`, `frontend/src/lib/strings.ts`
- `scripts/eval_lib.py`, `seed_data/evaluation/questions.json` (SORU 3)
