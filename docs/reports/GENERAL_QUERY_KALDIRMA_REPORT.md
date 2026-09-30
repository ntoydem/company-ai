# GENERAL_QUERY'nin kaldırılması — Rapor

**Tarih:** 30.09.2026  **Model:** Sonnet 5  **Tag:** (yok — bağımsız düzeltme, `GUVENLIK_YAMA_2026-09-30` ile aynı desende)  **Commit:** (bu rapor commit'iyle aynı)

Plan: `docs/plans/GENERAL_QUERY_KALDIRMA_PLAN.md`. Naci, Tansu ile netleşti: sistem artık hiçbir zaman
modelin kendi genel dünya bilgisinden cevap vermeyecek; "DSCR ne demek?" gibi tanım soruları da dahil her
soru şirket belgelerine bakacak.

## 1. Kabul kriterleri
| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| 1 | `QueryType`'ta `GENERAL_QUERY` yok, `general_answer.py` yok | ✅ | `grep -rn "GENERAL_QUERY\|GENERAL_NOTICE\|general_answer" backend/app` → 0 sonuç |
| 2 | Router "DSCR ne demek?"'i `DOCUMENT_QUERY`'e yönlendiriyor | ✅ | `tests/live/test_router_live.py::test_router_classifies_spec_examples` (canlı, güncellendi) + `tests/test_router.py` (sahte LLM, malformed/GENERAL_QUERY dahil her bilinmeyen tip `DOCUMENT_QUERY`'e düşüyor) |
| 3 | Kaynaksız tanım sorusu sabit "bilgi bulamadım" metnini döner, uydurma cevap vermez | ✅ | **Canlı doğrulandı** (bkz. §4) — 3 taşınan soru gerçek Gemini ile test edildi, üçü de tam `NO_ANSWER_TEXT` döndü |
| 4 | Yeni kural 9 prompt'ta var ve dokümanla birebir aynı | ✅ | `make lint`'in prompt-doc eşitlik kontrolü yeşil; `docs/prompts/ANSWER_SYSTEM_PROMPT.md` satır 9 |
| 5 | `make test` tam yeşil | ✅ | 381 backend (389'dan -8, silinen testler) + 9 ocr-worker |
| 6 | `make lint` tam yeşil | ✅ | ruff/mypy/eslint/tsc + prompt-doc + ledger/document/excel validasyonları |
| 7 | `questions.json` 0 hatayla doğrulanıyor, `general` kategorisi hiç geçmiyor | ✅ | `make validate-ledger --summary` → 0 hata; `grep '"category": "general"' questions.json` → 0 |
| 8 | Eval'de `general` kategorisi raporlanmıyor, `document` eşiğin altına düşmüyor | ✅ | `--retrieval-only` recall@80 36/36 (%100, Phase 5.3/5.4 ile aynı); canlı spot-check'te `document` kategorisi 3/3 (%100) |
| 9 | ADR-010 ve `docs/PHASES.md` güncel | ✅ | bu rapor + ilgili commit'teki diff |

**Genel sonuç:** Tüm kriterler karşılandı. Kod tabanında `GENERAL_QUERY`'nin hiçbir izi kalmadı; kaldırma
canlı LLM ile doğrulandı (yalnızca sahte-LLM birim testleriyle değil).

## 2. Yapılanlar
- **Tam kaldırma (SORU 1, opsiyon a):** `schemas/ask.py::QueryType`'tan `"GENERAL_QUERY"` çıkarıldı, `GENERAL_NOTICE` silindi. `services/general_answer.py` (tüm dosya) silindi. `services/router.py::ROUTER_SYSTEM_PROMPT` 3 tipe indirildi; "DSCR ne demek?" örneği artık `DOCUMENT_QUERY` döndürüyor, gerekçe metni "documents are always checked first, no general-knowledge fallback". `_normalize()`'ın artık erişilemez son dalı kaldırıldı (mypy `warn_unreachable=true` ile temiz). `services/ask_router.py`'nin GENERAL dalı, ilgili import'ları (`GENERAL_NOTICE`, `answer_general`, yalnızca bu dal için kullanılan `project_repo`) silindi. `app/cli.py::cmd_print_router_prompts` artık yalnızca router promptunu yazdırıyor.
- **`answer_prompt.py`'ye yeni kural 9** (SORU 3'ün önceki turunda tespit edilen boşluk — "farklı tanımları hepsiyle göster"): "Kaynaklardan birden fazlası aynı terim/kavram için farklı bir tanım veriyorsa (5. kuraldaki zincir ilişkisi geçerli değilse), hepsini kendi etiketiyle yaz, birini tercih etme." `make prompt-doc` ile `docs/prompts/ANSWER_SYSTEM_PROMPT.md`/`ROUTER_PROMPTS.md`'ye yansıtıldı.
- **`questions.json` (SORU 2 — onaylandı):** GEN-GEN-001/002/003 → `category: "document"`, `expect_no_answer: true`; `notes` alanları güncellendi. `seed_data/generator/ledger_schema.py`'nin `QuestionCategory` literalinden `"general"` çıkarıldı; `validate_ledger.py`'nin `CATEGORY_QUOTAS`'ından `"general": 3` ve artık gereksiz `q.category != "general"` istisnası kaldırıldı.
- **Testler:** `tests/test_general_answer.py` (49 satır) ve `tests/test_router.py::test_general_has_no_sub_questions` silindi; `test_router.py`'nin fallback testine `GENERAL_QUERY`'nin de artık "bilinmeyen tip" gibi `DOCUMENT_QUERY`'e düştüğü eklendi. `test_ask_router.py`'deki iki GENERAL testi (`test_general_question_uses_no_company_data_and_says_so`, `test_general_reply_naming_a_project_is_dropped`) ve onlara özel importlar (`ProjectStage`, `project_repo`, `GENERAL_*`, kullanılmayan kalan `ask_module`/`retrieval_module`/`pytest`) silindi. `tests/live/test_router_live.py`: parametrized listede `GENERAL_QUERY` → `DOCUMENT_QUERY`; `test_general_question_states_no_company_data` yerine `test_definition_question_without_a_document_definition_returns_no_answer` (yeni: `DOCUMENT_QUERY` + tam `NO_ANSWER_TEXT` bekliyor). `tests/test_eval_lib.py::test_score_question_general_passes_only_with_no_company_sources` silindi; `scripts/eval_lib.py`'nin `general` özel puanlama bloğu (33 satır) kaldırıldı — artık genel `document`/`expect_no_answer` akışından geçiyor.

## 3. Değişen dosyalar
`backend/app/schemas/ask.py`, `router.py`, `ask_router.py`, `cli.py`, `answer_prompt.py`; `backend/app/services/general_answer.py` (silindi); `backend/tests/test_general_answer.py` (silindi), `test_router.py`, `test_ask_router.py`, `tests/live/test_router_live.py`, `test_eval_lib.py`; `scripts/eval_lib.py`; `seed_data/generator/ledger_schema.py`, `validate_ledger.py`, `seed_data/evaluation/questions.json`; `docs/prompts/ANSWER_SYSTEM_PROMPT.md`, `ROUTER_PROMPTS.md`; `Makefile` (`prompt-doc` hedefinin router başlığı); `docs/ARCHITECTURE.md` (ADR-010), `docs/PHASES.md`. Migration yok.

## 4. Doğrulama (SORU 3'ün onaylanan kapsamı: tam eval değil, `--retrieval-only` + birkaç canlı doğrulama)
- `make eval EVAL_ARGS="--retrieval-only"`: recall@80 **36/36 (%100)** — Phase 5.3/5.4 baseline'ıyla birebir aynı, bu değişikliğin retrieval'a hiç dokunmadığının kanıtı.
- `make eval EVAL_ARGS="--ids GEN-GEN-001,GEN-GEN-002,GEN-GEN-003,GEN-HAL-001,ANK-AUT-001"` (canlı Gemini, 5 soru):
  - **GEN-GEN-001/002/003** (DSCR/ÇED/covenant test tanımları): üçü de `query_type: DOCUMENT_QUERY`, `answered: false`, cevap **birebir** `NO_ANSWER_TEXT` ("Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.") — model kaynaklarda gerçekten tanım olmadığını doğru tespit etti, uydurma bir tanım üretmedi.
  - **GEN-HAL-001** (hallucination): `DOCUMENT_QUERY`, sabit metin, geçti.
  - **ANK-AUT-001** (authorization): `MIXED_QUERY`, her iki dal da sabit "bulamadım" metni, geçti.
  - Kategori özeti: `document` 3/3 (%100), `hallucination` 1/1 (%100), `authorization` 1/1 (%100) — hepsi eşiği geçti.
- Tam `make eval` (61 soru, gerçek kota maliyeti) bu fazda **bilinçli olarak çalıştırılmadı** — SORU 3'ün onaylanan kararı, Gemini'nin günlük kota geçmişi (Phase 5.1/5.4) göz önüne alınarak.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Tam kaldırma (savunma amaçlı bir "GENERAL gelirse DOCUMENT gibi davran" kod yolu değil) | CLAUDE.md kod kalitesi kuralı ("ileride lazım olur" soyutlaması yasak); router'ın mevcut Pydantic doğrulaması zaten `GENERAL_QUERY`'i geçersiz bir `QueryType` literal'i olarak reddedip `DOCUMENT_QUERY`'e düşürüyor — ayrı bir savunma dalı gereksiz | Kod tabanında GENERAL'in hiçbir izi kalmadı |
| GEN-GEN-001/002/003 `document`/`expect_no_answer: true` (yeni belge içeriği eklenmedi) | Korpus taraması (grep) DSCR/ÇED/covenant test için hiçbir genel tanım cümlesi olmadığını gösterdi; gerçekçi olanı kabul etmek, sonradan yanlış çıkacak bir "gerçek kaynaklı cevap" beklentisi kurmaktan daha dürüst | Canlı testle doğrulandı (§4) — tahmin değil, ölçülmüş sonuç |
| Yeni kural 9 sentetik bir fixture ile test edilmedi | Mevcut 8 kuralın hiçbiri de ayrı bir sentetik fixture'la kanıtlanmıyor, yalnızca prompt disiplinine güveniliyor; ayrı bir fixture prematüre soyutlama olurdu | Kural yalnızca prompt metninde var, gerçek "çelişen tanım" senaryosu korpusta yok |
| company-ai'ın kendi `frontend/`'indeki ölü `GENERAL_QUERY` kodu **dokunulmadı** | Naci'nin kararı (kapsam dışı) | §6'da ayrıntı |

## 6. Bilinen, dokunulmayan nokta
`company-ai`'ın kendi `frontend/`'i (`ftansu/AI-BalBal`'dan bağımsız, ayrı bir kopya) hâlâ ölü `GENERAL_QUERY`
kodu taşıyor: `frontend/src/lib/strings.ts:49` (`GENERAL_QUERY: "Genel bilgi"`), `api/types.ts:235` (`QueryType`
union'ında hâlâ 4. değer), `components/AskPanel.tsx:73,77-78,86` (rozet/notice/kaynak-gizleme dalları),
`pages/admin/AdminAuditLogPage.tsx:15` (filtre listesi). Backend artık bu değeri hiç üretmediği için bu kod
yolları **zararsız ölü kod** olarak kalıyor — hata vermez, yalnızca hiç tetiklenmez. Naci'nin açık kararıyla
bu fazın kapsamı dışında bırakıldı; `ftansu/AI-BalBal`'a (aynı dosyaların bayt bayt kopyasını taşıyor)
zaten dokunulmuyor.

## 7. Riskler / sonraki adım için notlar
- Yukarıdaki §6'daki ölü kod, company-ai'ın kendi frontend'i gerçekten kullanılmaya devam ederse küçük bir
  temizlik borcu olarak kalıyor — riski yok, yalnızca gereksiz.
- Yeni kural 9, gerçek bir "iki belge aynı terimi farklı tanımlıyor" senaryosuyla hiç uçtan uca kanıtlanmadı
  (korpus taraması bunu gösterdi); ileride demo veri zenginleştirmesi sırasında böyle bir çift eklenirse bu
  kuralın gerçekten çalıştığı da doğrulanabilir.
- Tam `make eval` çalıştırılmadığı için `general` kategorisinin kaldırılmasının **diğer** kategorilerin
  (`temporal`, `mixed`, `data`) eşiklerini etkilemediği yalnızca `--retrieval-only` (retrieval'a hiç dokunulmadı)
  ve 2 spot-check sorusuyla (hallucination/authorization) dolaylı olarak gösterildi, tam kategori bazlı LLM
  sonucuyla değil — Naci isterse ayrıca tam bir `make eval` istenebilir.

## 8. Doğruladığım üçüncü taraf davranışları
- **Pydantic'in `Literal` alan doğrulaması, `QueryType`'tan çıkarılan `"GENERAL_QUERY"`'i otomatik olarak
  geçersiz kılıyor:** `_RouterResponse.query_type: QueryType` alanına LLM'in (varsayımsal olarak) hâlâ
  `"GENERAL_QUERY"` döndürdüğü bir senaryo `ValidationError` fırlatıyor, bu da `route()`'un mevcut
  `except (LLMError, json.JSONDecodeError, ValidationError)` bloğunda yakalanıp `DOCUMENT_QUERY`'e
  düşüyor — yeni kod yazmadan, tip sisteminin kendisinden gelen bir güvenlik ağı (`test_router.py`'de
  birim testle doğrulandı).
- **mypy `warn_unreachable=true`, `_normalize()`'ın üç `if`'le tam kapsanan bir `Literal`'den sonraki
  son `return` satırını gerçekten "unreachable" olarak işaretliyor** — ilk denemede bu satırı olduğu gibi
  bıraktığımda `make lint` hata vermedi çünkü henüz silmemiştim; satırı `elif`/örtük-`else` mantığıyla
  kaldırınca mypy hâlâ temiz kaldı, doğrulanmış bir tip daraltması.

## 9. Kaynak kullanımı
- Canlı LLM: 5 soru × (1 router + 1 cevap) ≈ 10 çağrı (`gemini-3.5-flash-lite`), günlük kotanın önemsiz bir kısmı.
- `--retrieval-only`: 0 LLM çağrısı.
- Disk: yeni dosya yok (yalnızca değişiklikler); `general_answer.py` (89 satır) ve `test_general_answer.py`
  (49 satır) silindi.
