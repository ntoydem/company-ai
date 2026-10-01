# Ürün 1 uyum turu Raporu — Ü-3 kural 10 (karşılaştırma yasağı) + `insufficient_data` + `comparison` eval kategorisi

**Tarih:** 01.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `3350f3b`
**Plan:** `docs/plans/URUN1_UYUM_PLAN.md` · **ADR:** ADR-014 concretization; yeni ADR yok · **Migration:** yok

Naci'nin SORU cevapları: (1) kural 10 her pakette geçerli; "karşılaştırma Ürün 2'de serbest mi?" Tansu'ya ayrı soru (NOT §7.2 #9); (2) GEN-CMP-003 kaldı, `phrase_check`/`value_check` ayrı raporlanıyor; (3) DATA dalında "yetersiz" → `missing_data` kaldı; (4) etiketsiz düz commit. **Canlı ölçüm hedefi (9/9) ilk turda tutuldu — revizyon turu gerekmedi.** (a) Ç-7.1 4 adımlı protokol bu turda yapılmadı, PHASES.md'ye ayrı UX fazı notu düşüldü.

## 1. Kabul kriterleri (plan §5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| U-01 | `SYSTEM_PROMPT` kural 10'u ve `COMPARISON_NOTICE`'i içerir; `docs/prompts/ANSWER_SYSTEM_PROMPT.md` eşit | ✅ | `test_answer_prompt.py::test_rule_10_forbids_cross_project_comparison_with_the_fixed_notice`; `make prompt-doc` + `make lint` eşitlik kontrolü yeşil |
| U-02 | `insufficient_data`: chunk var + model "yetmez" → `warnings == [insufficient_data]`, `retrieved_document_ids` dolu, metin `NO_ANSWER_TEXT`, denetim satırı türü taşır; sıfır chunk → `missing_data`; MIXED iki dal boş → belge dalına göre `insufficient_data` | ✅ | `test_ask_router.py::test_insufficient_data_when_documents_were_retrieved_but_the_model_declined`, `test_mixed_with_retrieved_documents_but_no_answer_is_insufficient_data`; mevcut `missing_data` testi değişmeden yeşil |
| U-03 | Validator: `comparison` sorusu liste `expected_answer` (≥ 2) + `expected_project: null` + `forbidden_phrases` ister (Q6); liste elemanları Q4'ten geçer; kota 3; 61 eski soru değişmeden geçerli; `make validate-ledger` 0 hata | ✅ | `test_validate_ledger.py::test_comparison_questions_need_two_facts_no_project_and_forbidden_phrases`, `test_list_expected_answer_paths_are_each_checked`; `validate_ledger` 0 error(s) |
| U-04 | `eval_lib`: liste → iki değer grubu; `phrase_check_passes` zorunlu/yasak ifade; `comparison` eşiği %100; `--repeat` özeti `phrase_ok` sayar | ✅ | `test_eval_lib.py::test_resolve_expected_accepts_a_list_of_ledger_facts_one_group_each`, `test_phrase_check_requires_the_notice_and_rejects_comparatives` |
| **U-05** | **Canlı ölçüm** `--ids GEN-CMP-001,002,003 --repeat 3` (gerçek Gemini, 18 çağrı) | ✅ **9/9** | Retrieval kararlılığı 3/3; model kararlılığı 9/9; **uçtan uca (değer) 9/9**; **ifade kuralı 9/9** (`seed_data/evaluation/results/consistency_2026-10-01/consistency_211029.*`, git dışı). Tüm 9 cevap §4'te |
| U-06 | Regresyon: `--retrieval-only` **39/39** (36 + 3 yeni ölçülebilir soru); `make test` **456 geçti** (449 + 7 yeni), 15 deselected; `make lint` yeşil; tek-projeli davranış testleri (`test_ask`) değişmedi | ✅ | komut çıktıları |
| U-07 | (a) PHASES.md'de gelecek UX fazı notu; kod yok | ✅ | `docs/PHASES.md` "Olası gelecek faz: Ç-7.1 4 adımlı protokol" |

## 2. Yapılanlar

- **`answer_prompt.py`:** `COMPARISON_NOTICE` sabiti; kural 10 (birden fazla proje → her projenin değeri kendi kaynak etiketiyle ayrı cümlede; karşılaştırma/sıralama/"hangisi daha …"/fark/oran yok; karşılaştırma istenirse önce sabit cümle, sonra ayrı değerler). `docs/prompts/ANSWER_SYSTEM_PROMPT.md` `make prompt-doc` ile yenilendi. Kanonikleştirme yok; `answered=True` kalır.
- **`schemas/ask.py` / `ask_router.py`:** `AskWarning.kind` ∋ `insufficient_data`; `INSUFFICIENT_DATA_WARNING` ("Şirket kaynaklarında ilgili belgeler bulundu ancak soruyu güvenilir şekilde cevaplamaya yetmedi."), `action: request_data`; `_run` cevapsızsa belge dalının `retrieved_document_ids` doluluğuna göre türü seçer; Excel-only miss `missing_data` (SORU 3).
- **Eval altyapısı:** `ledger_schema.py` — `QuestionCategory` ∋ `comparison`, `expected_answer: str | list[str] | None`, `required_phrases`/`forbidden_phrases` (varsayılan boş; `_Strict` korunur); `validate_ledger.py` — Q4 listeyi eleman eleman çözer, Q6 comparison kuralları, `CATEGORY_QUOTAS["comparison"] = 3`; `eval_lib.py` — `resolve_expected` liste (grup/yol), `target_pages_for` birleşim, `phrase_check_passes`, `QuestionResult.phrase_check(_reason)`, `passed` koşuluna eklendi, `HUNDRED_PERCENT_CATEGORIES` ∋ `comparison`, JSON/markdown raporu, `RepeatOutcome.phrase_ok` + `ConsistencySummary.phrase_*` + tablo sütunu; `run_eval.py` — `--repeat` döngüsünde `phrase_ok`.
- **`questions.json` v4 (64 soru):** `GEN-CMP-001` (iki ayrı olgu, lisans/önlisans tarihleri), `GEN-CMP-002` ("hangisi daha önce", yasak), `GEN-CMP-003` ("kurulu gücü hangisi daha büyük", yasak; değer beklentisi Ankara **güncel** 60 MW + İzmir hedef 80 MW); `forbidden_phrases` 12 karşılaştırma ifadesi; tüm değerler ledger yollarından.
- **Docs:** README (`warnings` türleri, eval v4/`comparison`), ADR-014 concretization, PHASES.md notu + Ç-7.1 gelecek fazı, NOT (§5.3 `insufficient_data` satırı, §6.6 #4 Ü-3 notu, §7.2 **#9 yeni açık madde: karşılaştırma Ürün 2'de serbest mi?** — Tansu'ya).
- **Dokunulmayanlar:** router, retrieval, `NO_ANSWER_TEXT`/`is_no_answer`, `audit_log` şeması, `product_limit`, diğer eval kategorileri/eşikleri, AI-BalBal, company-ai `frontend/`.

## 3. Değişen dosyalar

17 dosya. Kod: `backend/app/services/{answer_prompt,ask_router}.py`, `backend/app/schemas/ask.py`, `scripts/{eval_lib,run_eval}.py`, `seed_data/generator/{ledger_schema,validate_ledger}.py`, `seed_data/evaluation/questions.json`, `docs/prompts/ANSWER_SYSTEM_PROMPT.md`; testler: `backend/tests/{test_answer_prompt,test_ask_router,test_eval_lib,test_validate_ledger}.py`; docs: `README.md`, `docs/{ARCHITECTURE,PHASES}.md`, `docs/notes/TANSU_…md`, bu rapor.

## 4. Testler ve canlı ölçüm

- Backend: **456 geçti** (7 yeni: 1 prompt, 2 router, 2 eval_lib, 2 validator), 15 deselected, 7 dk 46 sn. Geçici kırmızılar (test tarafı): `test_load_questions` 61/v3 → 64/v4 güncellendi; kendi testimde İzmir önlisans tarihini yanlış yazmıştım (18.01.2024 — ledger'dan düzeltildi); iki E501.
- `make lint` yeşil; `make validate-ledger` 0 hata; `--retrieval-only` 39/39.
- **Canlı ölçüm (21:06–21:10, `enerji`, `--repeat 3`), 9 cevap (denetim kaydından):**
  - GEN-CMP-001 ×3: *"Ankara RES üretim lisansı 15.06.2020 tarihinde onaylanmıştır [K3]. İzmir RES önlisansı 18.01.2024 tarihinde düzenlenmiştir [K7]."* — 3. tekrarda model sabit cümleyi **istenmeden** başa koydu (karşılaştırma sorulmamıştı); kural yine sağlanıyor (yasak ifade yok, iki değer var), fakat aşırı temkinli — §5.
  - GEN-CMP-002 ×3: *"Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır. Ankara RES üretim lisansı 15.06.2020 … [K3]. İzmir RES önlisansı 18.01.2024 … [K8]."* — "daha önce" yargısı yok, 3/3.
  - GEN-CMP-003 ×3: sabit cümle + *"Ankara RES … 48 MW [K2] ve 60 MW [K58] … İzmir RES … 80 MW [K3]"* (tekrarlarda "48 MW (veya 60 MW)" varyantları) — karşılaştırma yok 3/3, değer kontrolü 3/3 (60 MW cevapta); **ama** kural 5 uygulanmadı: iki Ankara değeri yan yana, "60 MW, Licence Amendment 01 ile 48'den değiştirildi" biçimi yok — bilinen temporal zayıflık (Phase 5.1b %60), bu turun kapsamı dışı, kaydedildi.
- Kota: 18 cevap çağrısı + 18 router çağrısı; revizyon turu gerekmedi.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| Sabit karşılaştırma cümlesi cevabın başında, değerler sonra | Model önce kuralı uygular; kural 2'nin aksine cevap boş değil | GEN-CMP-001/3'te istenmeden de görünebiliyor — zararsız, ölçüldü |
| `expected_answer` liste → her yol bir grup, biri çözülemezse tüm kontrol `skip` | Mevcut `initial/current` grup mantığıyla aynı yarı-yol | — |
| `required_phrases`/`forbidden_phrases` genel alanlar, varsayılan `[]` | `_Strict` şema, 61 eski soruya alan eklenmedi | `data_conflict` için de kullanılabilir |
| Q6 doğrulaması yalnızca `comparison` için | Diğer kategorilerin sözleşmesi değişmedi | — |
| `insufficient_data` yalnızca belge dalı; Excel miss `missing_data` | SORU 3 | Workbook içi "yetersizlik" ayrı konu |
| GEN-CMP-003 değer beklentisi `capacity_mw.current.value` (60) | SORU 2; canlıda geçti (60 cevapta) ama rule 5 biçimi yok (§4) | Temporal faz için somut örnek |

## 6. Açık sorular (Naci cevaplamalı)

- Yok (backend). **Tansu'ya:** NOT §7.2 #9 — "projeler arası karşılaştırma Ürün 2'de serbest mi?" Cevaba göre `product_level == P2`'de kural 10 gevşetilir ya da aynen kalır.

## 7. Riskler / sonraki adım için notlar

- Kural 10'un aşırı uygulanması (karşılaştırma istenmeden sabit cümle) 9 cevabın 1'inde görüldü; UX açısından küçük, kural ihlali değil. İzlenir; sıklaşırsa kural metnine "yalnızca karşılaştırma istendiğinde" vurgusu.
- GEN-CMP-003 temporal bulgusu (48 ve 60 yan yana): Phase 5.1b'nin bilinen sınırlaması; gelecekteki "prompt tuning" fazı için somut, tekrar üretilebilir örnek.
- Ç-7.1 4 adımlı protokol: PHASES.md notu; AI-BalBal `AnswerView` ile birlikte tasarlanacak ayrı UX fazı.
- AI-BalBal `types.ts`'teki `AskWarning.kind` birliğine `insufficient_data` eklenmeli (Tansu); dondurulmuş sürüm `warnings`'ı okumadığı için kırılma yok.

## 8. Doğruladığım üçüncü taraf davranışları

- Gemini (`gemini-3.8-flash`, `low` thinking): kural 10'u 9/9 uyguladı; sabit cümleyi harfiyen yazdı (`phrase_check` normalize edilmiş alt-dize ile geçti).
- Pydantic v2 `_Strict` (`extra="forbid"`) modelde varsayılanlı yeni alan eklemek eski JSON'u kırmaz; `str | list[str] | None` birlik tipi liste/dize ayrımını korur.

## 9. Kaynak kullanımı

- LLM: 36 çağrı (18 router + 18 cevap) ölçüm için; testler/eval retrieval-only LLM'siz. Backend/Caddy RAM değişmedi.
