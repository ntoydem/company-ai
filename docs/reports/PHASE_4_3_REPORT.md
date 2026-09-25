# Phase 4.3 Raporu — Mixed query (router)

**Tarih:** 25.09.2026  **Model:** Fable 5.1  **Tag:** phase-4-3  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den, SORU 1 ile yeniden ifade edilmiş hali) | Durum | Kanıt |
|---|---|---|---|
| 1 | Q3 2024 bütçe sapması + "sebebi belgelerde var mı?" → Excel farkı + belge kaynağı + yalnızca belgedeki sebep | ✅ | Canlı (gerçek Gemini, `assets/phase_4_3/live_test_llm.log`): router → `MIXED_QUERY`; Excel tarafı **"Ankara RES Q3 2024 bütçe sapması -894.000 TRY olmuştur."**, kaynak **`Budget_vs_Actual_2026.xlsx Summary!D5`** (motor: `budget_variance(Q3_2024)` = 25.106.000 − 26.000.000); belge tarafı hiçbir belge sebep anlatmadığı için sabit "yeterli bilgi bulamadım" — arıza/dişli/kesinti gibi uydurulmuş sebep yok (test bunu açıkça denetler). Sahte LLM'le deterministik: `test_ask_router.py::test_budget_variance_with_reason_only_from_documents` (belge tarafı kural 6 cümlesi `belgelerde sebep belirtilmemiş`, Excel tarafı şablon `Sonuç: -894.000 TRY …` — model rakamı bozunca ADR-011 şablonu kazanır). Canlı: `tests/live/test_router_live.py::test_budget_variance_with_no_reason_in_documents` |
| 2 | belirsiz DSCR → iki değer iki kaynak türü | ✅ | Canlı: "Güncel DSCR kaç?" → `MIXED_QUERY`, alt sorular *"Kredi sözleşmesindeki güncel minimum DSCR covenant'ı nedir?"* / *"En son dönemdeki gerçekleşen DSCR değeri kaç?"*; cevap **"Belgelere göre: … 1,20x [K1] … / Excel verisine göre: … 1,37x"**; `sources[0]` = Facility Agreement Amendment 01 s.4 (GÜNCEL), `excel_sources[0]` = `Covenant_Report.xlsx Q2_2026!D14`. Sahte: `test_ask_router.py::test_ambiguous_dscr_returns_covenant_and_actual_with_both_source_kinds` (iki kart türü, belge parçası önce, 3 LLM çağrısı — üçüncü "birleştirme" çağrısı yok, **tek** audit satırı `kind: document|excel`). Canlı: `test_router_live.py::test_ambiguous_dscr_returns_covenant_and_realised_values` |
| 3 | GENERAL sorularda şirket verisi kullanılmaz ve bu belirtilir | ✅ | Canlı: "DSCR ne demek?" → `GENERAL_QUERY`, cevap **"Bu cevap genel bilgidir; şirket belgeleri veya verileri kullanılmamıştır."** ile başlar, `sources=[]`, `excel_sources=[]`, `retrieved_document_ids=[]`, 790 token (belge+workbook yüklü olduğu hâlde). Sahte: `test_ask_router.py::test_general_question_uses_no_company_data_and_says_so` — `allowed_document_ids` üç modülde de `AssertionError` atacak şekilde yamalı ve **çağrılmıyor**; tek LLM isteği = çıplak soru, belge metni (`SECRET`) prompt'ta yok; audit satırı boş kaynaklarla `GENERAL_QUERY`. Sızıntı ağı: `::test_general_reply_naming_a_project_is_dropped`, `test_general_answer.py` |
| Router (ADR-010) | `DOCUMENT/DATA/MIXED/GENERAL` sınıflandırması | ✅ | Canlı, SPEC_04 §7 örnekleri 5/5 doğru (`test_router_classifies_spec_examples`): "Kredi sözleşmesindeki DSCR covenant nedir?"→DOCUMENT, "Ankara RES 2026 Q2 DSCR kaç?"→DATA, "Güncel DSCR kaç?"→MIXED, "DSCR ne demek?"→GENERAL, "İzmir RES'in COD tarihi nedir?"→DOCUMENT. Birim: `test_router.py` (7) — bozuk JSON / bilinmeyen tip / LLM hatası → DOCUMENT. Kablolama: `test_ask_router.py::test_real_router_wiring_falls_back_to_document_on_bad_json` |
| Audit tek satır (SORU 2) | | ✅ | `test_ask_router.py`: her dal için `len(rows)==1`; MIXED satırında iki kart türü, `excel_files_used`, `chunks_retrieved`, token toplamı; LLM hatasında `error` dolu tek satır + 503 |
| Eval v2 (SORU 3) | 3 `data` + 2 `mixed` | ✅ | §4 |
| Frontend | tip rozeti + Excel kartı + GENERAL notu | ✅ | `make lint` (eslint+tsc); ekran görüntüleri `assets/phase_4_3/0{1..4}_*.png` (§4) |

## 2. Yapılanlar
- **Router** `app/services/router.py`: `Router` Protocol + `LLMRouter` (tek `LLM_MODEL_CLASSIFY` çağrısı, `json_object`,
  ≤300 çıktı token'ı, SPEC_04 §7 örnekleri few-shot + "sözleşme/gerçekleşen belirsizliği → MIXED" kuralı). DOCUMENT/DATA
  **orijinal** soruyu koşar (retrieval/planlama router'dan etkilenmez), yalnızca MIXED alt soruları kullanır. Her hata →
  `DOCUMENT_QUERY` (güvenli yön).
- **Orkestrasyon** `app/services/ask_router.py::answer_routed_question`: `ask.answer_question` ve
  `excel_ask.answer_data_question` **değişmeden** (`write_audit=False` ile) çağrılır; MIXED = iki parça, sabit başlıklar
  (`Belgelere göre:` / `Excel verisine göre:`), üçüncü LLM çağrısı yok, iki dal her zaman koşar (boş dal sabit metnini
  korur). `api/ask.py` yalnızca bu fonksiyonu çağırır; `get_router` dependency (`FakeRouter` ile test).
- **GENERAL** `app/services/general_answer.py`: retrieval/Excel/yetki yok; sabit `GENERAL_NOTICE` kodla başa eklenir;
  sızıntı ağı (`projects` tablosundaki proje adları, Türkçe küçük harf; para tutarı kalıbı) → sabit metin, `answered=false`.
- **Audit** `app/services/audit_writer.py`: tek yazma yolu; `sources` kartlarına `kind`; MIXED'de `documents_retrieved` =
  belge + workbook id'leri; `excel_files_used` kart dosyalarından; token toplamına router dahil.
- **API/şema:** `AskResponse += query_type, excel_sources`, tipe göre `notice` (`MIXED_NOTICE`, `GENERAL_NOTICE`);
  `sources` anlamı değişmedi. `/api/excel/ask` router'sız kaldı (SORU 5).
- **Frontend:** `types.ts` (`QueryType`, `ExcelSourceCard`), `ExcelSourceCardList`, cevap başlığında tip rozeti
  (GENERAL sarı), GENERAL'de tekrar eden not gizli, DATA'da belge kartı bölümü / DOCUMENT'ta Excel bölümü gösterilmez;
  örnek sorulara "Ankara RES 2026 Q2 DSCR kaç?" ve "Güncel DSCR kaç?" eklendi.
- **Eval:** `questions.json` v2 (48): `ANK-DAT-001..003`, `ANK-MIX-001..002`; `eval_lib` kataloğu `seed_data/excel/manifest.json`'ı
  da okur (`file_to_title`), `AskOutcome.cited_files/query_type`, `run_eval` `excel_sources` + `query_type`; varsayılan
  istek aralığı 13→26 sn (soru başına ≥2 LLM isteği). Canlı test aralığı da 26 sn.
- **Prompt dokümanı:** `docs/prompts/ROUTER_PROMPTS.md` (`app.cli print-router-prompts`, `make prompt-doc`/`make lint`).
- **Dokümanlar:** ADR-010/016/021 somutlaştırma, DOMAIN_MODEL `query_type`, README "Soru yönlendirme" bölümü, PHASES 4.3 kriteri
  (SORU 1) + 5.1 ertelemeleri.

## 3. Değişen dosyalar
`git diff --stat phase-4-2..phase-4-3` (özet): 23 değişen + 8 yeni dosya, ~+600/−135. Yeni: `backend/app/services/{router,ask_router,general_answer,audit_writer}.py`,
`backend/tests/{test_router,test_general_answer,test_ask_router}.py`, `backend/tests/live/test_router_live.py`,
`docs/prompts/ROUTER_PROMPTS.md`, `docs/plans/PHASE_4_3_PLAN.md`, bu rapor + `assets/phase_4_3/`. Migration yok (şema değişmedi:
`audit_log.query_type` zaten vardı, `sources` JSONB'ye yalnızca `kind` anahtarı eklendi).

## 4. Canlı doğrulama, eval ve arayüz
- **`make test-llm`** (gerçek Gemini `gemini-3.5-flash-lite`, 7 dk 55 sn): **15 geçti** — Phase 3.1/4.2'nin 7 canlı ledger
  testi router üzerinden değişmeden geçti (regresyon yok) + 5 sınıflandırma + 3 uçtan uca (§1). Tam çıktı:
  `assets/phase_4_3/live_test_llm.log`.
- **`make eval`** (48 soru, 26 sn aralık, `gemini-3.5-flash-lite`) — üç koşu, hepsi `assets/phase_4_3/`:
  - **Koşu 1** (`eval_run1_before_fallback.md`): isolation/hallucination/authorization **%100**, mixed **2/2**, temporal %88,9;
    ama **document %69,6 (16/23)** ve data 1/3. Teşhis: router, sözleşmede *yazan* tutarları ("yerli banka kredisi ne kadar?",
    "ECA kredisi ne kadar?", "kalan borcu nedir?", "son covenant testi sonucu nedir?") DATA saydı; Excel'de bulamayınca
    "Erişebildiğiniz Excel dosyalarında … bulamadım" çıkmazında kaldı (4 belge sorusu). Ayrıca MWh biçimi (`13538` vs `13.538`)
    değer kontrolünü düşürdü. → Düzeltmeler (§6): DATA boş → belge hattına düşüş; router promptuna "belgede yazan rakam =
    DOCUMENT" kuralı + örnek; eval MWh alias; `normalize_month` TR tarih.
  - **Koşu 2** (`eval_run2_full.md`, düzeltmelerden sonra, tam 48 soru): authorization/hallucination/isolation **%100**,
    **document %82,6 (19/23)** — kalan 4 başarısızlık Phase 3.2c'de 5.1'e ertelenen `IZM-DEV-005/006/007` + `ANK-EPC-004`'ün
    aynısı (router öncesi düzeyle eşit), temporal %88,9, **mixed %100 (2/2)**, data **2/3**. Yönlendirme dağılımı: 43 DOCUMENT,
    3 MIXED, 2 DATA; `ANK-FIN-010` ("son covenant testi sonucu nedir?") MIXED'e yönlendi ve belge alt sorusu covenant eşiğine
    kaydı — 48'de 1 router hatası (bilinen sınır, §8). `ANK-DAT-003` ("bugün itibarıyla kalan kredi borcu?") Excel'de bulunamadı
    → belge hattına düştü → **Covenant Compliance Report'tan doğru 44.100.000 EUR** cevabı; ama soru `required_sources:
    Financial Model 2026` istiyordu. Kök neden **soru seti hatası**: Financial Model `restricted`, `ask_as_user: finans`
    (employee) onu göremez (ADR-004 doğru çalıştı — `/api/excel/ask` ile birebir yeniden üretildi: "no workbook exposes
    Outstanding_DemoToday"). Soru `yonetim` ile sorulacak şekilde düzeltildi (notu `questions.json`'da).
  - **Koşu 3** (`eval_run3_dat003.md`, yalnızca `--ids ANK-DAT-003`, düzeltilmiş soru): ✅ `DATA_QUERY`, cevap
    "Ankara RES'in bugün itibarıyla kalan kredi borcu 44.100.000 EUR'dur.", kaynak `Financial Model 2026` — data **3/3**
    (koşu 2 + koşu 3). **Sonuç:** koşu 2'nin tam seti + koşu 3 ile bütün kategoriler eşikte/üstünde; Phase 3.2c'nin
    ertelenmiş 4 belge sorusu dışında başarısızlık yok. Tek bir tam koşuda %100'ün altında kalan yalnızca `data` idi ve
    nedeni soru setiydi; yine de dürüst not: koşu 2 tek başına `make eval` için "❌" döndü.
  - Toplam token (koşu 2): 362.358 giriş / 4.828 çıkış; ~1,4 dk/soru ile 48 soru ≈ 25 dk (aralık kotadan, hesaptan değil).
- **Arayüz** (`assets/phase_4_3/0{1..4}_*.png`, admin, 1280×900, Phase 3.3 deseniyle tek seferlik Playwright script'i — repoya
  girmedi): `01_document` "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → rozet **Belge**, `[K#]` kartları;
  `02_data` "Ankara RES 2026 Q2 DSCR kaç?" → rozet **Excel**, yalnızca "Excel kaynakları" kartı (`Covenant_Report.xlsx —
  Sayfa (sheet) Q2_2026 — Aralık: D14 — Dosyayı indir`); `03_mixed` "Güncel DSCR kaç?" → rozet **Belge + Excel**, MIXED notu,
  "Belgelere göre: … 1,20x [K18] … / Excel verisine göre: … 1,37x", altında hem Kaynaklar (Amendment 01 s.4, Facility s.7)
  hem Excel kaynakları; `04_general` "DSCR ne demek?" → sarı rozet **Genel bilgi**, cevap "Bu cevap genel bilgidir; şirket
  belgeleri veya verileri kullanılmamıştır." ile başlıyor, kaynak bölümü yok (881/119 token).

## 5. Testler
- Backend: **360 geçti**, 15 atlandı (canlı LLM), 0 kırmızı (3 dk 11 sn); yeni: `test_router.py` (7), `test_general_answer.py` (4),
  `test_ask_router.py` (11), `test_eval_lib.py` (+2, 48 soru/v2), `test_periods.py` (+TR tarih). Mevcut `/api/ask` testleri **değişmeden** geçti — `fake_llm`
  fixture'ı DOCUMENT-only `FakeRouter` kurduğu için eski testler tam olarak eski LLM çağrılarını görüyor; tek düzenleme
  `test_audit_log_write_failure_never_breaks_the_response` (yama noktası `audit_writer`'a taşındı). ocr-worker 9.
- `make lint`: ruff+mypy, eslint+tsc, ledger F1-F11 (48 soru, Q1-Q5), prose, `validate_excel` W1-W5, **üç** prompt dokümanı eşitliği — temiz.
- `make test-llm`: 15 geçti (§4).

## 6. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Kabul kriteri "EBITDA sorusu" → "Q3 2024 bütçe sapması + sebep belgede var mı?" (SORU 1, onaylı) | ledger'da EBITDA yok; hiçbir belge arıza sebebini anlatmıyor | Kural 6'nın negatif dalı kanıtlandı; pozitif dal 5.1'e (PHASES.md notu) |
| Router hatası → DOCUMENT, asla GENERAL | kaynaksız cevap en riskli hata | Bozuk JSON'da davranış Phase 4.2 öncesiyle aynı |
| **DATA boş dönerse belge hattına düşer** (`query_type=DOCUMENT_QUERY` olarak) — ilk eval koşusundan sonra eklendi (§4) | router "yerli banka kredisi ne kadar?" gibi sözleşmede *yazan* tutarları DATA saydı, Excel'de yoktu → "Excel'de bulamadım" çıkmazı; düşüş, yanlış yönlendirilen soruyu router öncesi davranışa döndürür | Yanlış DATA sorusu +1 çağrı; `test_ask_router.py::test_data_miss_falls_back_to_the_document_pipeline` |
| Router promptuna "sözleşme/rapor'da yazan rakam = DOCUMENT" kuralı + 1 örnek | aynı bulgu; prompt tek doğruluk kaynağı (`docs/prompts/ROUTER_PROMPTS.md`) | ikinci eval koşusu §4 |
| `normalize_month` TR tarih (`15.09.2026`) → `2026-09` | planner `as_of` alanına TR tarih yazabiliyor; eskiden yalnızca yıl eşleşip yıl sonu bakiyesi (42,5M) dönüyordu | `test_periods.py` |
| Eval MWh alias (`13538 MWh` ↔ `13.538 MWh`) | belgeler gruplamasız, Excel motoru TR gruplamalı basıyor | `test_eval_lib.py::test_resolve_expected_accepts_grouped_and_ungrouped_mwh` |
| DOCUMENT/DATA'da orijinal soru, MIXED'de alt sorular | retrieval/plan davranışı router'dan bağımsız kalsın, eval karşılaştırılabilir kalsın | `test_router.py::test_document_type_always_runs_the_original_question` |
| MIXED birleştirme deterministik (başlık + iki parça), `answered = doc or data` | "yorum yok", ek maliyet yok | Bir dal boşsa sabit metni görünür kalır (`test_mixed_with_nothing_on_either_side…`) |
| `notice` tipe göre değişir; plandaki ayrı `data_notice` alanı eklenmedi | tek alan yeterli, frontend zaten `notice` gösteriyor | GENERAL'de cevap zaten notice ile başladığı için UI notu gizliyor (tekrar yok) |
| GENERAL sızıntı ağı proje adlarını `projects` tablosundan okur | isimleri sabit kodlamak demo'ya bağlardı | Bu okuma cevabı üretmez, yalnızca filtreler; `allowed_document_ids`/retrieval yine çağrılmaz |
| `AskResult.chunks` alanı | router'ın tek audit satırına `chunks_retrieved` yazabilmesi için | Serileştirilmez, yalnızca servis içi |
| `/api/excel/ask` audit satırı `documents_retrieved` = kart id'leri (tekilleştirilmiş) | ortak yazıcıya geçiş | Davranış aynı, sıra korunur |
| Eval istek aralığı 26 sn (13 değil) | her `/api/ask` ≥ 2 LLM isteği | 48 soru ≈ 25-30 dk |
| `ANK-MIX-002.expected_answer` bir dict'e işaret eder → değer kontrolü atlanır | variance ledger'da leaf değil (türetilmiş) | Kaynak + `answered` ile puanlanır, raporda "atlandı" listesinde |

## 7. Açık sorular (Naci cevaplamalı)
- `SORU:` **Gemini yeterli mi?** (PHASES.md karar noktası) — bu fazın ölçümü §9'da. Öneri: V0 için `gemini-3.5-flash-lite`
  router olarak yeterli (5/5 spec örneği, MIXED alt soruları anlamlı); asıl kısıt doğruluk değil **ücretsiz katman
  hızı** (5 istek/dk → MIXED soru ~50 sn). Yerel model gündemi V0 dışı; ücretli katman veya ikinci bir anahtar
  (`LLM_MODEL_CLASSIFY` için ayrı model → ayrı kota kovası) daha ucuz bir hızlandırma.

## 8. Riskler / sonraki phase için notlar
- Router LLM sınıflandırmasıdır: yanlış tip mümkündür (özellikle DOCUMENT↔MIXED sınırı). Eval `query_type`'ı JSON'a
  yazıyor; 5.1'de v2 soru setiyle tip doğruluğu ayrıca puanlanabilir (`expected_query_type` alanı önerisi).
- `.env`'de classify ve answer aynı model → aynı kota kovası. Farklı model seçilirse kota ikiye bölünür.
- MIXED'de belge dalının alt sorusu router'ın yeniden yazımıdır; retrieval için çoğunlukla daha iyi (sözleşme/covenant
  kelimeleri), ama nadiren orijinaldeki bir anahtar kelimeyi düşürebilir — canlı testte gözlenmedi.
- GENERAL sızıntı ağı kaba (proje adı + tutar). "Ankara" tek başına yakalanmaz; sistem promptu şirket atıflarını zaten yasaklıyor.
- Phase 5.1: `general` kategorisi, "sebep belgede pozitif" örneği (Bakım Raporu), `required_sources_all`.
- Phase 5.2 (admin panel, audit log ekranı): `sources[].kind` ile iki kart türü ayrı çizilmeli.

## 9. Doğruladığım üçüncü taraf davranışları
- Gemini OpenAI-uyumlu uç, `response_format={"type":"json_object"}` ile `gemini-3.5-flash-lite`: 5/5 sınıflandırmada
  geçerli JSON döndü; `reason` alanı serbest metin olarak dolduruldu (loglanıyor, karar için kullanılmıyor).
- Playwright docker imajı (`mcr.microsoft.com/playwright:v1.47.0-jammy`, compose ağında `http://caddy:80`) yalnızca rapor
  ekran görüntüsü için (Phase 3.3 deseni), repoya girmedi.

## 10. Kaynak kullanımı
- **LLM çağrısı / token (canlı ölçüm, `gemini-3.5-flash-lite`):** DOCUMENT 2 çağrı; DATA 3; MIXED 4 — "Güncel DSCR kaç?"
  toplam **5.887 giriş / 172 çıkış** token (router ~350 + belge prompt'u ~3.500 + Excel plan kataloğu ~1.700 + aktarım);
  Q3 2024 MIXED 3.753/174; GENERAL 2 çağrı, **790/127**. Router çağrısı tek başına ~300-400 giriş token. Tam demo veri
  setinde (19 belge, `RETRIEVAL_TOP_K=40`) aynı MIXED soru arayüzde **12.178/182** — fark belge prompt'unun boyutu, router değil.
  Koşu 2'de 48 soru toplam 362.358 giriş token (soru başına ort. ~7.500).
- Bu fazda harcanan LLM çağrısı: canlı test ≈ 40, eval 3 koşu ≈ 220, teşhis + ekran görüntüleri ≈ 20; birim testler sahte LLM.
- **Gemini yeterli mi (karar noktası):** sınıflandırma kalitesi 48 soruda 47 doğru yönlendirme (1 DOCUMENT→MIXED kayması);
  asıl darboğaz ücretsiz katman hızı (5 istek/dk) — tam eval ~25 dk, MIXED soru ~50 sn. Öneri §7.
- Container RAM değişmedi (yeni bağımlılık yok).
