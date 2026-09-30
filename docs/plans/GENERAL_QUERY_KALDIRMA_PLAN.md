# GENERAL_QUERY'nin kaldırılması: Implementation Plan

## Bağlam

Naci, Tansu ile netleşti: sistem artık hiçbir zaman modelin kendi genel dünya bilgisinden cevap vermeyecek.
"DSCR ne demek?" gibi tanım soruları da dahil, her soru şirket belgelerine bakacak. Birden fazla belgede
farklı tanım varsa hepsi kaynağıyla gösterilecek; hiçbir belgede yoksa mevcut "bilgi bulamadım" sabit metni
(`NO_ANSWER_TEXT`, ADR-014) döner.

Okunanlar: `docs/PHASES.md` Phase 4.3 bölümü, `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §6 (ürün katmanı
eşlemesi, `GENERAL_QUERY`'nin `product_level` kararı henüz verilmemişti); kod: `backend/app/services/router.py`,
`general_answer.py`, `ask_router.py`, `answer_prompt.py`, `schemas/ask.py`; testler:
`backend/tests/test_general_answer.py`, `test_router.py`, `test_ask_router.py` (GENERAL bölümü),
`tests/live/test_router_live.py`, `tests/test_eval_lib.py`; `scripts/eval_lib.py`, `seed_data/generator/
ledger_schema.py`, `seed_data/generator/validate_ledger.py`, `seed_data/evaluation/questions.json`
(GEN-GEN-001/002/003), `docs/prompts/ROUTER_PROMPTS.md`, `docs/ARCHITECTURE.md` ADR-010; frontend:
`company-ai/frontend/src/{lib/strings.ts,api/types.ts,components/AskPanel.tsx,pages/admin/
AdminAuditLogPage.tsx}`.

## Tespitler

- **T1 — `GENERAL_QUERY`'nin kod ayak izi tam olarak şurada:** `schemas/ask.py` (`QueryType` literal,
  `GENERAL_NOTICE`), `services/router.py` (`ROUTER_SYSTEM_PROMPT`'ta 4. tip + örnek, `_normalize`'ın son
  `return None, None` dalı), `services/general_answer.py` (tüm dosya — yalnızca GENERAL_QUERY için var),
  `services/ask_router.py` (`NOTICE_BY_TYPE["GENERAL_QUERY"]`, `_run`'daki `if query_type == "GENERAL_QUERY"`
  bloğu), `app/cli.py::cmd_print_router_prompts` (`GENERAL_SYSTEM_PROMPT` içe aktarımı ve yazdırması). Bunların
  dışında hiçbir yerde GENERAL'e özgü iş mantığı yok — `audit_log.query_type` düz `String(32)` (migration
  gerekmez, geçmiş satırlar etkilenmez), `AskResponse.query_type` da düz `Literal` (DB constraint değil).
- **T2 — Soru 1 (tam kaldırma mı, DOCUMENT'a yönlendirme mi): tam kaldırma önerilir, daha az kod değil ama
  daha temiz.** İki seçenek:
  (a) `QueryType`'tan `"GENERAL_QUERY"`'i sil, `general_answer.py`'yi sil, router prompt'unu 3 tipe indir,
  `ask_router.py`'deki GENERAL dalını sil.
  (b) `QueryType`'ı olduğu gibi bırak, router prompt'unda GENERAL seçeneğini kaldır (model artık hiç
  üretmeyecek) ama `_run`'da "GENERAL_QUERY gelirse DOCUMENT_QUERY gibi davran" savunma kodu bırak.
  (b) **daha az satır değiştirir** ama CLAUDE.md'nin "kod kalitesi" kuralına ("İstenmeyen: … 'ileride lazım
  olur' diye eklenen soyutlamalar") aykırı bir ölü kod yolu bırakır — LLM artık asla üretmeyeceği bir değeri
  savunma amaçlı işlemeye devam eder, `general_answer.py` kullanılmadan repoda kalır. **Öneri: (a).** Naci'nin
  "kaldırılıyor" ifadesiyle de birebir örtüşüyor. Router'ın kendi güvenli-yön ilkesi zaten korunuyor: bir
  sınıflandırma hatası (bozuk JSON, bilinmeyen tip, LLM hatası) hâlâ `DOCUMENT_QUERY`'e düşüyor (`router.py:117-120
  fallback()`), bu davranış değişmiyor — yalnızca modelin **kasıtlı olarak GENERAL seçme ihtimali** ortadan
  kalkıyor.
- **T3 — Soru 2 (general_answer.py'nin akıbeti): silinsin.** `answer_general`, `leaks_company_data`,
  `GENERAL_SYSTEM_PROMPT`, `GENERAL_LEAK_TEXT`, `_MONEY` regex'i — hiçbiri başka bir yerden çağrılmıyor
  (`grep` ile doğrulandı, tek çağıran `ask_router.py::_run`'ın silinecek GENERAL dalı). Dosya tamamen silinir;
  `tests/test_general_answer.py` da (49 satır, yalnızca bu dosyayı test ediyor) silinir.
- **T4 — Soru 3 ("farklı tanımları hepsiyle göster" davranışı): mevcut akışta yok, yeni bir kural gerekiyor.**
  `answer_prompt.py`'nin 8 kuralı (`_RULES`) şunu içermiyor: birden fazla **ilgisiz** (zincir/versiyon ilişkisi
  olmayan) kaynak aynı kavram için farklı bir şey söylüyorsa ne yapılacağı. Kural 5 (`describe_chain`/GÜNCEL-
  İLK HALKA) yalnızca **aynı belgenin `supersedes` zincirindeki** temporal farkı çözüyor (ADR-012) — bağımsız
  iki belgenin aynı terimi farklı tanımlaması ayrı bir durum. Kural 1/4 ("yalnızca kaynaklardan yaz, her
  cümleyi etiketle") örtük olarak birden fazla kaynağı aktarmaya izin veriyor ama **"hepsini göster, birini
  seçme"** açıkça yazmıyor — model tek bir kaynağı seçip diğerini görmezden gelebilir. **Yeni kural 9** eklenir
  (taslak): *"Kaynaklardan birden fazlası aynı terim/kavram için farklı bir tanım veya açıklama veriyorsa
  (zincir ilişkisi yoksa, kural 5 geçerli değilse), hepsini kendi kaynak etiketiyle ayrı ayrı yaz; birini
  diğerine tercih etme veya hangisinin doğru olduğuna karar verme."* Bu, `answer_prompt.py::_RULES` listesine
  eklenir ve `docs/prompts/ANSWER_SYSTEM_PROMPT.md`'ye `make prompt-doc` ile yansıtılır (`make lint` eşitliği
  zaten denetliyor).
  - **Test edilebilirlik sınırı (dürüstçe not düşülmeli):** `seed_data/generator/prose/*.yaml` içinde "DSCR",
    "borç servisi", "Debt Service Coverage" için **hiçbir genel tanım cümlesi yok** (grep ile doğrulandı, sıfır
    eşleşme); ne ÇED ne "covenant test" için de var. Demo korpusunda bugün **gerçek bir "farklı tanım"
    senaryosu yok** — bu kural yalnızca prompt metninde bir talimat olarak eklenebilir, gerçek çok-tanımlı bir
    belge çiftiyle uçtan uca kanıtlanamaz (uydurma bir sentetik senaryo kurmak SORU 2'de soruluyor).
- **T5 — Soru 4 (mevcut testler): silinecekler ve değişecekler listesi.**
  | Dosya | Ne olacak |
  |---|---|
  | `tests/test_general_answer.py` | **silinir** (T3) |
  | `tests/test_router.py::test_general_has_no_sub_questions` | **silinir**; `ROUTER_SYSTEM_PROMPT`'a karşı asserte eden diğer testler (`_route` içindeki `assert request.system == ROUTER_SYSTEM_PROMPT`) değişmeden geçer, prompt metni değiştiği için **içerik** değil **referans** karşılaştırması olduğundan kırılmaz |
  | `tests/test_router.py::test_malformed_json_unknown_type_and_llm_error_fall_back_to_document` | değişmez — `"EMAIL_QUERY"` zaten bilinmeyen bir tip örneği, `"GENERAL_QUERY"` değil |
  | `tests/test_ask_router.py::test_general_question_uses_no_company_data_and_says_so` | **silinir** |
  | `tests/test_ask_router.py::test_general_reply_naming_a_project_is_dropped` | **silinir** |
  | `tests/live/test_router_live.py::test_router_classifies_spec_examples` | `("DSCR ne demek?", "GENERAL_QUERY")` satırı `("DSCR ne demek?", "DOCUMENT_QUERY")` olur |
  | `tests/live/test_router_live.py::test_general_question_states_no_company_data` | **silinir**; yerine (SORU 3) yeni bir canlı test önerilir: "DSCR ne demek?" artık `DOCUMENT_QUERY`'e düşüyor ve ya (a) gerçek bir kaynaktan alıntı ya da (b) `NO_ANSWER_TEXT` döndüğünü doğrular — hangisi olacağı T4'teki korpus boşluğuna bağlı |
  | `tests/test_eval_lib.py::test_score_question_general_passes_only_with_no_company_sources` | **silinir** (T6) |
  | `scripts/eval_lib.py` satır 322-354 (`if question.category == "general": …`) | **silinir**; genel `score_question` akışı (document kategorisiyle aynı yol) devreye girer |
- **T6 — Soru 5 (questions.json'daki "general" kategorisi): `document`'a taşınmalı, `expect_no_answer=true`
  ile — SORU'ya bağlı.** GEN-GEN-001/002/003 (`"DSCR (Debt Service Coverage Ratio) ne demek?"`, `"ÇED
  (Çevresel Etki Değerlendirmesi) süreci nedir?"`, `"Bir kredi sözleşmesinde covenant testi ne işe yarar?"`)
  bugün `expected_answer: null`, `expect_no_answer: false` ve `category: "general"` (yalnızca bu kategori
  `expected_answer=None`'a izin veriyor, `validate_ledger.py:830`). T4'teki korpus taramasına göre bu üç
  terimin hiçbiri hiçbir belgede genel biçimde tanımlanmıyor — yani `DOCUMENT_QUERY`'e yönlendirilince
  gerçekçi sonuç `NO_ANSWER_TEXT` olacaktır, uydurma bir kaynak değil. Bu, tam da Naci'nin "hiçbir belgede
  yoksa bilgi bulamadım" ifadesinin öngördüğü durum. Öneri: üçü de `category: "document"`,
  `expect_no_answer: true` olarak taşınır; bu hem gerçekçi (mevcut içerikle tutarlı) hem de tam olarak
  korunması gereken regresyonu test eder — "tanım sorusuna genel dünya bilgisinden uydurma cevap verme."
  Bunun karşı alternatifi (ledger'a/bir sözleşme şablonuna gerçek bir tanım cümlesi eklemek ki soru gerçekten
  cevaplanabilsin) SORU 2'de soruluyor; CLAUDE.md'nin "rakamı uydurma" kuralı doğrudan rakamlarla ilgili olsa
  da, kapsam dışı yeni belge içeriği eklemek bu fazın (yalnızca router/prompt davranışı) sınırlarını aşar.
  - `seed_data/generator/ledger_schema.py:29` `QuestionCategory` literal'inden `"general"` çıkarılır.
  - `seed_data/generator/validate_ledger.py:56` `CATEGORY_QUOTAS`'tan `"general": 3` satırı silinir.
  - `seed_data/generator/validate_ledger.py:830` `and q.category != "general"` istisnası artık gereksiz
    (hiçbir soru bu kategoride olmayacağı için), ama kod sağlığı için silinir.
  - Toplam soru sayısı değişmez (61, `MIN_QUESTIONS=60` hâlâ sağlanır), yalnızca 3 sorunun kategorisi/
    `expect_no_answer` alanı değişir.
- **T7 — Soru 6 (kural 2/6, ADR notu): çelişki yok, güçlendiriyor; yeni ADR numarası değil, ADR-010'a
  concretization.** Kural 2 (SOURCE GROUNDING: "kaynak yoksa sabit cümle") ve kural 6 (NO OPINION: "sistem
  bulur, okur, aktarır") zaten bunu istiyordu; GENERAL_QUERY, Phase 4.3'te bu ikisine **kasıtlı bir istisna**
  olarak eklenmişti ("genel dünya bilgisi, şirket verisi değil" diye ayrı bir kategori). Bu istisnayı
  kaldırmak, kuralları **orijinal haline** döndürüyor — çelişki değil, düzeltme. `docs/ARCHITECTURE.md`
  ADR-010'a (Question router) yeni bir "Phase X concretization" satırı: GENERAL_QUERY kaldırıldı, üç tip
  kaldı, gerekçe (kural 2/6, Naci+Tansu kararı, tarih). Yeni ADR numarası açılmaz — bu depoda kararların
  evrilmesi hep mevcut ADR'ye concretization eklenerek yapılıyor (bkz. ADR-004/010/016'nın kendi geçmişi).
- **T8 — Frontend (company-ai'ın kendi `frontend/`'i) etkileniyor, ama bu fazın kapsamı dışında bırakılmalı
  mı diye SORU 4'te soruluyor.** `frontend/src/lib/strings.ts:49` (`GENERAL_QUERY: "Genel bilgi"`),
  `api/types.ts:235` (`QueryType` union), `components/AskPanel.tsx:73,77-78,86` (`GENERAL_QUERY`'e özel
  rozet/notice/kaynak-gizleme dalları), `pages/admin/AdminAuditLogPage.tsx:15` (filtre listesi) — hiçbiri
  backend değişmeden **kırılmaz** (`GENERAL_QUERY` artık hiç üretilmeyeceği için bu dallar yalnızca ölü kod
  olur, hata vermez). Temizlemek isteğe bağlı bir küçük iş; `ftansu/AI-BalBal` de aynı dosyaların **bayt bayt
  aynı** kopyalarını taşıyor (`docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md`'de tespit edildi) — o depoya
  **dokunulmaz** (backend frontend'e dokunmaz kuralı). company-ai'ın kendi frontend'inin temizliği bu planın
  kapsamına dahil edilebilir (küçük, riski yok) ya da ayrı bırakılabilir — SORU 4.

## Kapsam (uygulama aşamasında, şimdi yazılmayacak)

1. `backend/app/schemas/ask.py`: `QueryType` literalinden `"GENERAL_QUERY"` çıkar, `GENERAL_NOTICE` sabitini sil.
2. `backend/app/services/router.py`: `ROUTER_SYSTEM_PROMPT`'u 3 tipe indir (GENERAL_QUERY tanımı ve "Q: DSCR
   ne demek?" örneği çıkar; örneği "Q: DSCR ne demek? -> DOCUMENT_QUERY" ile değiştir, gerekçe: "terim şirket
   belgelerinde tanımlanıyor olabilir, dünya bilgisinden cevap verme" — modelin artık bu soruyu belgelerde
   aramaya çalışmasını teşvik eden bir örnek). "Rules: 1. If in doubt between DOCUMENT_QUERY and GENERAL_QUERY…"
   satırı kaldırılır (artık anlamsız). `_normalize`'ın son `return None, None` dalı kaldırılabilir (artık
   ulaşılamaz) ya da savunma amaçlı kalabilir — küçük bir uygulama detayı.
3. `backend/app/services/general_answer.py`: **dosya silinir.**
4. `backend/app/services/ask_router.py`: `GENERAL_NOTICE` içe aktarımı, `NOTICE_BY_TYPE["GENERAL_QUERY"]`,
   `answer_general` içe aktarımı, `_run`'daki `if query_type == "GENERAL_QUERY": …` bloğu, `project_repo`
   içe aktarımı (yalnızca GENERAL'in `forbidden_terms`i için kullanılıyordu — başka bir çağıran yoksa o da
   silinir) kaldırılır.
5. `backend/app/cli.py::cmd_print_router_prompts`: `GENERAL_SYSTEM_PROMPT` içe aktarımı ve `"=== GENERAL …"`
   yazdırma satırları kaldırılır.
6. `backend/app/services/answer_prompt.py`: yeni kural 9 (T4) `_RULES` listesine eklenir.
7. `docs/prompts/ROUTER_PROMPTS.md` ve `docs/prompts/ANSWER_SYSTEM_PROMPT.md`: `make prompt-doc` ile yeniden
   üretilir (elle düzenlenmez, `make lint` eşitliği zaten bunu denetliyor).
8. Testler: T5 tablosundaki silme/değişiklikler.
9. `seed_data/evaluation/questions.json`: GEN-GEN-001/002/003 → `category: "document"`,
   `expect_no_answer: true`, `notes` güncellenir (T6, SORU 1'in cevabına göre).
10. `seed_data/generator/ledger_schema.py`, `validate_ledger.py`: T6'daki üç değişiklik.
11. `docs/ARCHITECTURE.md` ADR-010: concretization notu (T7).
12. `docs/PHASES.md`: Phase 4.3'ün "Kapsam"/"Kabul kriterleri" satırlarına bu değişikliğe işaret eden bir not
    (Phase 4.3'ün kendisi yeniden açılmaz, yalnızca "GENERAL_QUERY sonradan kaldırıldı, bkz. [tarih]" çapraz
    referansı) — Adım 5 altına, önceki güvenlik yaması notuyla aynı desende.
13. (SORU 4'ün cevabına göre) `frontend/src/{lib/strings.ts,api/types.ts,components/AskPanel.tsx,pages/admin/
    AdminAuditLogPage.tsx}`'den `GENERAL_QUERY` referanslarının temizlenmesi.

## Kabul kriterleri

| # | Kriter | Kanıt |
|---|---|---|
| 1 | `QueryType`'ta `GENERAL_QUERY` yok, kod tabanında `general_answer.py` yok | `grep -rn "GENERAL_QUERY\|GENERAL_NOTICE\|general_answer" backend/app` → 0 sonuç |
| 2 | Router artık `DSCR ne demek?`'i `DOCUMENT_QUERY`'e yönlendiriyor | `tests/test_router.py`'de sahte-LLM testi (yeni, `_RouterResponse` `DOCUMENT_QUERY` döndürünce normalize doğru çalışıyor — zaten var olan mekanizma, yeni bir dal değil) + canlı test (T5, `make test-llm`, isteğe bağlı/kota riskli) |
| 3 | Kaynaksız tanım sorusu sabit "bilgi bulamadım" metnini döner, uydurma cevap vermez | `tests/test_ask.py` deseninde yeni bir birim test: boş/ilgisiz korpusla `DOCUMENT_QUERY` olarak "DSCR ne demek?" sorulduğunda `NO_ANSWER_TEXT` dönüyor (retrieval zaten sıfır chunk döndürüyor, ADR-021'in mevcut "chunk yoksa LLM çağrılmadan sabit metin" yolu — yeni kod değil, mevcut yolun bu soru için de çalıştığının kanıtı) |
| 4 | Yeni kural 9 prompt'ta var ve dokümanla birebir aynı | `make lint` (prompt-doc eşitliği kontrolü) yeşil |
| 5 | `make test` tam yeşil (silinen/değişen testler dahil) | `make test` çıktısı |
| 6 | `make lint` tam yeşil (ruff/mypy/eslint/tsc + prompt-doc + ledger/document/excel validasyonları) | `make lint` çıktısı |
| 7 | `questions.json` yine 0 hatayla doğrulanıyor, `general` kategorisi hiç geçmiyor | `make validate-ledger --summary` |
| 8 | Eval'de `general` kategorisi artık raporlanmıyor, `document` kategorisi eşiğin altına düşmüyor | `make eval EVAL_ARGS="--retrieval-only"` (LLM'siz, kota riski yok) + zaman/kota uygunsa tam `make eval` (SORU 5) |
| 9 | ADR-010 ve `docs/PHASES.md` güncel | diff incelemesi |

## SORU (Naci cevaplamalı)

1. **GEN-GEN-001/002/003'ün yeni kategorisi/`expect_no_answer`'ı T6'daki öneri (`document`, `expect_no_answer:
   true`) gibi mi olsun?** Alternatif: bu üç terimden biri için (ör. DSCR) bir sözleşme şablonuna gerçek bir
   tanım cümlesi eklensin ki soru **gerçekten** kaynaklı cevaplanabilsin (ledger + prose + belge üretimi
   gerektirir, bu fazın kapsamını genişletir). Önerim: T6 — şimdilik gerçekçi olanı (`expect_no_answer:
   true`) kabul et, belge içeriği eklemeyi ayrı bir "demo veri zenginleştirme" işine bırak.
2. **T4'teki yeni kural 9'u kanıtlayacak sentetik bir test fixture'ı (iki sahte belge, aynı terimi farklı
   tanımlayan) eklensin mi, yoksa kural yalnızca prompt metninde kalıp mevcut kuralların (1-8) hiçbirinin
   sentetik fixture'ı olmadığı gibi test edilmeden mi bırakılsın?** Önerim: eklenmesin — mevcut 8 kural da
   yalnızca prompt disipliniyle güveniliyor, ayrı bir fixture prematüre bir soyutlama olur (CLAUDE.md).
3. **`tests/live/test_router_live.py::test_general_question_states_no_company_data`'nın yerine geçecek yeni
   canlı test hangi sonucu bekleyecek — `NO_ANSWER_TEXT` mi, yoksa modelin retrieval'da bulduğu ilgisiz bir
   parçadan zorlama bir "cevap" üretip üretmediğini mi kontrol edecek?** Önerim: `NO_ANSWER_TEXT` bekle (T6'nın
   gerekçesiyle tutarlı) ve ayrıca cevapta hiçbir uydurma rakam/tanım olmadığını (`"CFADS"`, `"borç servisi"`
   gibi kelimelerin **yalnızca** gerçek bir kaynak etiketiyle birlikte geçtiğini, aksi halde hiç geçmediğini)
   doğrula.
4. **company-ai'ın kendi `frontend/`'indeki `GENERAL_QUERY` referansları (T8) bu fazda temizlensin mi, yoksa
   ayrı bir küçük işe mi bırakılsın?** Önerim: bu fazda temizlensin — küçük, riski yok, ölü kod bırakmama
   ilkesiyle tutarlı; `ftansu/AI-BalBal`'a dokunulmaz.
5. **Tam `make eval` (LLM'li) bu faz kapsamında çalıştırılsın mı, yoksa yalnızca `--retrieval-only` +
   `make test` mi yeterli?** Gemini günlük kota geçmişi (Phase 5.1/5.4) göz önüne alınarak önerim:
   `--retrieval-only` + `make test` yeterli; tam eval'in `general` kategorisiz halini görmek istersen ayrıca
   iste, kota müsaitse çalıştırırım.

## Uygulama sırası (onaydan sonra)

1. `schemas/ask.py`, `router.py`, `general_answer.py` (sil), `ask_router.py`, `cli.py` — kod değişiklikleri.
2. `answer_prompt.py` yeni kural 9.
3. `make prompt-doc` → `docs/prompts/ROUTER_PROMPTS.md`/`ANSWER_SYSTEM_PROMPT.md` yeniden üretilir.
4. Testler: T5 tablosundaki silme/güncellemeler + kabul kriteri 2/3'ün yeni testleri.
5. `seed_data/evaluation/questions.json`, `ledger_schema.py`, `validate_ledger.py` (T6, SORU 1'e göre).
6. `make test` + `make lint` + `make validate-ledger --summary`.
7. (SORU 5) `make eval EVAL_ARGS="--retrieval-only"`, isteğe bağlı tam `make eval`.
8. `docs/ARCHITECTURE.md` ADR-010, `docs/PHASES.md` Phase 4.3 çapraz referansı.
9. (SORU 4) frontend temizliği.
10. Commit + push (Naci'nin talimatına göre phase etiketi ya da düz commit).

## Kritik dosyalar

- `backend/app/schemas/ask.py`, `backend/app/services/router.py`, `backend/app/services/general_answer.py`
  (silinecek), `backend/app/services/ask_router.py`, `backend/app/services/answer_prompt.py`,
  `backend/app/cli.py`
- `backend/tests/test_general_answer.py` (silinecek), `test_router.py`, `test_ask_router.py`,
  `tests/live/test_router_live.py`, `tests/test_eval_lib.py`
- `scripts/eval_lib.py`
- `seed_data/generator/ledger_schema.py`, `seed_data/generator/validate_ledger.py`,
  `seed_data/evaluation/questions.json`
- `docs/prompts/ROUTER_PROMPTS.md`, `docs/prompts/ANSWER_SYSTEM_PROMPT.md`
- `docs/ARCHITECTURE.md` (ADR-010), `docs/PHASES.md`
