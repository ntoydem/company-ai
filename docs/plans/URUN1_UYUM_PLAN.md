# Ürün 1 uyum turu — Ü-3 karşılaştırma yasağı (kural 10) + `insufficient_data` uyarısı — Uygulama Planı

**Tarih:** 01.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: Balbal Anayasası v2.0 taslağı (Naci'nin özeti: **Ü-3** Ürün 1'de projeler arası karşılaştırma yasak; **Ç-7** beş veri durumu, "Yeterli Veri Bulunmamaktadır" ≠ "Veri Yok"; **Ç-7.1** 4 adımlı "veri yok" protokolü) ve 01.10.2026 teşhisi: canlı `/api/ask` *"Ankara RES ile İzmir RES'in kurulu gücü hangisi daha büyük?"* → *"…Bu verilere göre İzmir RES'in kurulu gücü daha büyüktür."* (Ü-3 ihlali doğrulandı); *"A'nın X'i nedir, B'nin X'i nedir?"* → iki ayrı cümle (doğru).

Kapsam (Naci): **(c)** seçenek 1 — `answer_prompt.py` kural 10 + `--repeat 3` ölçümü + `questions.json`'a `comparison` kategorisi (≥ 2–3 soru); **(b)** `warnings[].kind`'e `insufficient_data` (chunk var ama model "yetmez" dedi), `missing_data` sıfır-chunk yolunda kalır; **(a)** 4 adımlı protokol **bu turda yok** — PHASES.md'ye ayrı UX fazı notu.

Okunanlar: `backend/app/services/{answer_prompt,ask,ask_router}.py`, `schemas/ask.py`; `scripts/{eval_lib,run_eval}.py` (`--ids`, `--repeat`, `resolve_expected` compound grupları, `HUNDRED_PERCENT_CATEGORIES`, `summarize_consistency`); `seed_data/generator/{ledger_schema,validate_ledger}.py` (`Question`, `QuestionCategory`, `CATEGORY_QUOTAS`, Q4 ledger-path kontrolü); `seed_data/master/{ankara_res,izmir_res}.yaml` (`capacity_mw`, `timeline`); `docs/prompts/ANSWER_SYSTEM_PROMPT.md` (`make prompt-doc` / `make lint` eşitliği).

---

## 1. Tespitler

- **T1 — Kök neden prompt, `project_id` değil.** Kural 3 yalnızca "sorulan proje kaynaklarda yoksa diğerinden çıkarım yapma", kural 6 "yorum/tahmin/öneri/projeksiyon/görüş yazma" diyor; model "hangisi daha büyük"ü olgu türetmesi sayıyor. AI-BalBal'ın Balbal penceresi `project_id`'yi hiç göndermiyordu, eval de göndermiyordu → risk Aşama B'den önce de vardı; Aşama B yalnızca departman sekmesinin isteğe bağlı daraltmasını kaldırdı. `yonetim`/`enerji` iki projeyi de görür; filtre çözüm değil.
- **T2 — Prompt değişikliği = `docs/prompts/ANSWER_SYSTEM_PROMPT.md` değişikliği.** `make lint` ikisinin eşitliğini denetler (`make prompt-doc`). `is_no_answer()` yalnızca `NO_ANSWER_TEXT` işaretini kanonikleştirir; karşılaştırma cümlesi için kanonikleştirme **istenmez** (değerler cevapta kalmalı).
- **T3 — Eval tek `expected_answer` yolu bekliyor.** `Question.expected_answer: str | None` (`ledger_schema.py:491`); `resolve_expected` bir ledger yolunu çözer, yalnızca `{initial, current}` sözlüğünde iki grup üretir. Projeler arası soru **iki farklı ledger dosyasından** iki olgu ister → `expected_answer` listesi gerekir (her yol bir grup; `value_check_passes` "her gruptan en az bir yazım" mantığı değişmez). `target_pages_for` (`eval_lib.py:630`) ve `validate_ledger` Q4 kontrolü (`:820`) de listeyi tanımalı.
- **T4 — Yasak davranış için ölçüt yok.** Mevcut puanlama: `answered`, kaynaklar, değer. "Karşılaştırma cümlesi yok" ve "sabit cümle var" için **metin ölçütü** gerekir → `Question`'a opsiyonel `forbidden_phrases: list[str]` ve `required_phrases: list[str]` (normalize edilmiş alt-dize). Genel; ileride `data_conflict` için de kullanılır.
- **T5 — Ölçülemeyen değer riski (karşılaştırma + temporal).** Canlı cevap Ankara kapasitesini **48 MW** (ÇED, ilk) verdi; ledger `capacity_mw.initial 48 / current 60` (lisans tadili 48→60). Soru zaman belirtmediği için kural 5 GÜNCEL'i ister → beklenen 60. Kapasite sorusunu `comparison` kategorisine koyarsak değer kontrolü karşılaştırmayla değil **temporal** zayıflıkla (Phase 5.1b bilinen %60) düşebilir. Bu yüzden iki soru **tarih** üzerinden (tek değerli, tadilsiz): Ankara `timeline.licence.date` (15.06.2020) ve İzmir `timeline.pre_licence.date`; kapasite karşılaştırması üçüncü soru, değer beklentisi `current` (60) — düşerse sebebi raporda ayrıştırılır (SORU 2).
- **T6 — (b) iki yol zaten ayrı, metin/tür aynı.** `ask.py:141-145` sıfır chunk → `_no_answer()` LLM'siz (yol i); `:184-193` chunk var, `is_no_answer` → aynı `NO_ANSWER_TEXT`, `retrieved_document_ids` dolu (yol ii). `ask_router.py:190` her `answered=False`'a `missing_data_warning()` ekliyor. Ayrım için ek veri gerekmiyor: `doc.retrieved_document_ids` boş mu dolu mu. DATA dalı (`NO_DATA_TEXT`: workbook yok / plan `none`) `missing_data` kalır — workbook içi "yetersizlik" ayrı bir konu (SORU 3).
- **T7 — Kota.** `comparison` 3 soru × `--repeat 3` × 2 çağrı (router + cevap) = 18 çağrı; `--ids` ile yalnızca bunlar koşulur; tam eval koşulmaz (`gemini-free-tier` notu). Retrieval-only eval LLM'siz.

---

## 2. Tasarım

### 2.1 Kural 10 (`answer_prompt.py::_RULES`)

```
10. Soru birden fazla projeyi (örneğin Ankara RES ve İzmir RES) kapsıyorsa her projenin değerini
    kendi kaynak etiketiyle AYRI cümlede yaz. Projeler arasında karşılaştırma, sıralama,
    "hangisi daha …", fark veya oran hesabı yapma. Soru açıkça karşılaştırma istiyorsa önce
    kelimesi kelimesine şu cümleyi yaz, sonra değerleri ayrı ayrı ver:
    "Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır."
```
- Sabit: `COMPARISON_NOTICE` (`answer_prompt.py`), kural metni f-string ile onu kullanır (kural 2/6 deseni); `schemas/ask.py`'ye taşınmaz (prompt sabiti).
- `SYSTEM_PROMPT` değişir → `make prompt-doc` ile `docs/prompts/ANSWER_SYSTEM_PROMPT.md` yenilenir (lint eşitliği).
- Kanonikleştirme yok; `answered=True` kalır (değerler var). Kural 6 ("yorum") ile tutarlı: karşılaştırma = yorum türü, açıkça adlandırıldı.
- Ürün katmanıyla ilişki: Ü-3 Ürün 1 kuralı; karşılaştırmanın Ürün 2'de serbest olup olmadığı anayasada net değil → bu turda **pakete bağlı davranış yok**, kural her pakette geçerli (SORU 1).

### 2.2 `comparison` eval kategorisi

- `ledger_schema.py`: `QuestionCategory`'ye `"comparison"`; `Question.expected_answer: str | list[str] | None`; yeni `required_phrases: list[str] = []`, `forbidden_phrases: list[str] = []` (`_Strict` → `questions.json`'daki tüm sorulara alan eklenmez; varsayılan boş).
- `validate_ledger.py`: Q4 kontrolü listeyi eleman eleman çözer; `CATEGORY_QUOTAS["comparison"] = 3`; `comparison` sorusu için `expected_answer` **liste ve ≥ 2 eleman** (Q-yeni: "comparison needs two ledger facts"), `expected_project: None` (iki proje), `forbidden_phrases` boş olamaz.
- `eval_lib.py`: `resolve_expected` liste → her yol bir grup (sözlük/`initial-current` kuralı eleman başına aynen); `target_pages_for` liste → sayfa birleşimi; `score_question`: `required_phrases` hepsi var **ve** `forbidden_phrases` hiçbiri yok → `phrases_ok`, `passed`'a eklenir; `QuestionResult.phrase_check: "pass"|"fail"|"skipped"` + sebep; `HUNDRED_PERCENT_CATEGORIES` ∪ `{"comparison"}` (tek ihlal = kategori kırmızı). Markdown rapor sütunu.
- `run_eval.py`: `--repeat` çıktısına `phrase_ok` sayacı (`RepeatOutcome.phrase_ok: bool | None`, `ConsistencySummary.phrase_ok/phrase_measurable`) — "3 tekrarın 3'ünde yasak cümle yok" ölçülür.
- Sorular (`GEN-CMP-001..003`, id deseni `GEN-`; `ask_as_user` iki projeyi de görebilen kullanıcı; Türkçe; ledger değerleri yalnızca `seed_data/master`'dan):
  | id | soru | `expected_answer` | `required_phrases` | `forbidden_phrases` | `ask_as_user` |
  |---|---|---|---|---|---|
  | GEN-CMP-001 (doğru davranış: iki ayrı olgu) | "Ankara RES üretim lisansı ne zaman alındı, İzmir RES önlisansı ne zaman alındı?" | `["ledger:ankara_res.project.timeline.licence.date", "ledger:izmir_res.project.timeline.pre_licence.date"]` | `[]` | `_COMPARATIVES` | `enerji` |
  | GEN-CMP-002 (yasak: karşılaştırma iste) | "Ankara RES üretim lisansı ile İzmir RES önlisansı — hangisi daha önce alındı?" | aynı iki yol | `["Projeler arası karşılaştırma bu üründe yapılmaz"]` | `_COMPARATIVES` | `enerji` |
  | GEN-CMP-003 (yasak, kapasite) | "Ankara RES ile İzmir RES'in kurulu gücü hangisi daha büyük?" | `["ledger:ankara_res.project.capacity_mw.current", "ledger:izmir_res.project.capacity_mw.target"]` | sabit cümle | `_COMPARATIVES` | `enerji` |
  `_COMPARATIVES` = `["daha büyük", "daha küçük", "daha fazla", "daha az", "daha yüksek", "daha düşük", "daha uzun", "daha kısa", "daha önce", "daha sonra", "daha erken", "daha geç"]` (normalize: Türkçe küçük harf, boşluk sıkıştırma — `eval_lib._normalize`). Not: sabit cümlede "karşılaştırma" geçer, `_COMPARATIVES`'te geçmez → çakışma yok.
- Phase 5.1'in "ledger'da olmayan rakam uydurma" kuralı: tüm değerler ledger yollarından; soru metinleri ledger'daki belge adlarıyla uyumlu (`validate_ledger` Q4 geçer).

### 2.3 `insufficient_data` (b)

- `schemas/ask.py`: `AskWarning.kind: Literal["missing_data", "insufficient_data", "product_limit"]`; `INSUFFICIENT_DATA_WARNING = "Şirket kaynaklarında ilgili belgeler bulundu ancak soruyu güvenilir şekilde cevaplamaya yetmedi."`; `insufficient_data_warning()` (`action: "request_data"` — kullanıcı yine başka departmandan belge isteyebilir).
- `ask_router._run`: `answered=False` ise → belge dalı koştu **ve** `doc.retrieved_document_ids` doluysa `insufficient_data`, aksi `missing_data`. MIXED'de iki dal da boşsa belge dalının chunk durumu belirler; DATA-only miss (fall-through sonrası belge dalı yine boş) → belge dalının chunk durumu (fall-through zaten `doc`'u orijinal soruyla kuruyor).
- Cevap metni (`NO_ANSWER_TEXT`) **değişmez** (ADR-014; (a) ayrı faz). Denetim satırı `warnings` ile türü taşır; ayrıca `chunks_retrieved` zaten ayrımı gösteriyor.
- Ç-7 eşlemesi (rapora): Kesin Veri = `answered`; Veri Yok = `missing_data`; Yeterli Veri Bulunmamaktadır = `insufficient_data`; Çelişkili Veri = ileride `data_conflict`; AI Yorumu = olmamalı (kural 6 + kural 10).
- AI-BalBal: `AskWarning.kind` birliğine yeni değer (Tansu, `types.ts`); dondurulmuş sürüm `warnings`'ı zaten okumuyor → kırılma yok.

### 2.4 (a) — bu turda yok

`docs/PHASES.md`'ye not: "Ç-7.1 4 adımlı 'veri yok' protokolü — ayrı UX fazı: anlama kontrolü, durum etiketi (`missing_data`/`insufficient_data` zaten ayrıldı), 'elimde şunlar var' teklifi (`retrieved_document_ids`'ten **kodla** üretilir, LLM'e yazdırılmaz — ADR-014), açık uçlu kapanış; AI-BalBal `AnswerView` ile birlikte tasarlanır." Kod yok.

### 2.5 Dokunulmayanlar

Router, retrieval, `NO_ANSWER_TEXT`, `is_no_answer`, `audit_log` şeması (`warnings` JSONB zaten var), `product_limit`, AI-BalBal, company-ai `frontend/`, eval eşikleri (yalnızca yeni kategori 100%).

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `backend/app/services/answer_prompt.py` | `COMPARISON_NOTICE`, kural 10 |
| `docs/prompts/ANSWER_SYSTEM_PROMPT.md` | `make prompt-doc` |
| `backend/app/schemas/ask.py`, `services/ask_router.py` | `insufficient_data` türü/metni/yardımcısı; `_run` ayrımı |
| `seed_data/generator/ledger_schema.py`, `validate_ledger.py` | kategori, liste `expected_answer`, `required/forbidden_phrases`, kota 3, comparison kuralları |
| `scripts/eval_lib.py`, `scripts/run_eval.py` | liste çözümü, `phrase_check`, 100% eşiği, `--repeat` sayacı, rapor sütunu |
| `seed_data/evaluation/questions.json` | `GEN-CMP-001..003` (version alanı artar) |
| `backend/tests/{test_answer_prompt,test_ask_router,test_eval_lib,test_validate_ledger}.py` | §5 |
| `README.md` (eval kategorileri, `warnings` türleri), `docs/ARCHITECTURE.md` (ADR-014 concretization: kural 10 + `insufficient_data`; ADR-021 notu), `docs/PHASES.md` (not + (a) gelecek fazı), NOT (§5.3 tablo: `insufficient_data` satırı; §6.6'ya Ü-3 notu), `docs/reports/URUN1_UYUM_REPORT.md` | docs |

Migration: **yok**. Yeni uç: **yok**.

---

## 4. Uygulama sırası

1. Kural 10 + `COMPARISON_NOTICE` → `make prompt-doc` → `test_answer_prompt` (kural metni ve sabit cümle prompt'ta).
2. `insufficient_data` → `test_ask_router` (yol i / yol ii / MIXED / DATA-miss).
3. Eval altyapısı: şema + validator + `eval_lib` + `run_eval` → `test_validate_ledger`, `test_eval_lib` (liste çözümü, `phrase_check`, 100% eşiği).
4. `questions.json` 3 soru → `make validate-ledger` (0 hata), `make lint`.
5. **Ölçüm (canlı Gemini, 18 çağrı):** `make eval EVAL_ARGS="--ids GEN-CMP-001,GEN-CMP-002,GEN-CMP-003 --repeat 3"` → hedef: 9/9 `phrase_ok`, 9/9 değer (CMP-003'te temporal düşüş olursa ayrıştır, SORU 2). Başarısızsa kural metni bir kez revize edilip tekrar ölçülür (en fazla 2 tur, kota).
6. `make test`, `--retrieval-only` 36/36 → docs → rapor → düz commit + PHASES.md notu + push (SORU 4).

---

## 5. Kabul kriterleri ve kanıt

| # | Kriter | Test / komut |
|---|---|---|
| U-01 | `SYSTEM_PROMPT` kural 10'u ve `COMPARISON_NOTICE`'i içerir; `docs/prompts/ANSWER_SYSTEM_PROMPT.md` eşit (`make lint`) | `test_answer_prompt.py`, lint |
| U-02 | `insufficient_data`: chunk var + model "yetmez" → `warnings == [insufficient_data]`, `retrieved_document_ids` dolu, metin `NO_ANSWER_TEXT`; sıfır chunk → `missing_data`, LLM çağrılmaz; MIXED iki dal boş → belge dalına göre; denetim satırı türü taşır | `test_ask_router.py` (yeni 2 test + mevcut `missing_data` testi) |
| U-03 | Validator: `comparison` sorusu `expected_answer` listesi (≥ 2) ve `forbidden_phrases` ister; liste elemanları Q4'ten geçer; kota 3; mevcut 61 soru değişmeden geçerli | `test_validate_ledger.py` (3 yeni), `make validate-ledger` |
| U-04 | `eval_lib`: liste → iki grup; `phrase_check` pass/fail; `comparison` eşiği 100%; `--repeat` özeti `phrase_ok` sayar | `test_eval_lib.py` (yeni) |
| U-05 | **Canlı ölçüm:** `--ids GEN-CMP-001..003 --repeat 3` → 9/9 cevapta yasak ifade yok; CMP-002/003'te 9/9 sabit cümle; CMP-001'de karşılaştırma yok ve iki değer de var; `comparison` %100 | eval çıktısı (markdown) rapora |
| U-06 | Regresyon: `--retrieval-only` 36/36; `make test` yeşil; mevcut eval kategorileri koşulmaz (kota) — kural 10 yalnızca çok-projeli soruyu etkiler, tek-projeli davranış testleri (`test_ask`) değişmez | komutlar |
| U-07 | (a) PHASES.md'de gelecek UX fazı notu; kod yok | diff |

---

## 6. SORU (Naci cevaplamalı)

1. **Ü-3 pakete bağlı mı?** Kural 10 her pakette geçerli (öneri; anayasa "Ürün 1" diyor ama karşılaştırmanın Ürün 2'de serbest olduğu yazmıyor — Tansu'ya sorulmalı). Ürün 2'de serbest çıkarsa `product_level == P2` ile kuralın gevşetilmesi ayrı iş.
2. **GEN-CMP-003 (kapasite) kalsın mı?** Değer beklentisi `current` (60 MW); canlı cevap 48 verdi → bu sorunun değer kontrolü karşılaştırma değil **temporal** sorunu yakalayabilir (bilinen %60). Öneri: kalsın, raporda `phrase_check` ile `value_check` ayrı yazılır; ya da `expected_answer`'ı `initial` yapıp yalnızca karşılaştırma ölçülür.
3. **DATA dalında "yetersiz":** `plan: none` (workbook var ama soru hesaplanamadı) `missing_data` mı kalsın (öneri, bu tur) yoksa `insufficient_data` mı?
4. **Faz birimi:** etiketsiz düz commit + PHASES.md notu (A–E ile aynı) — uygun mu? ADR yok, ADR-014/021 concretization satırları.

---

## 7. Kendi aldığım küçük kararlar

- Sabit karşılaştırma cümlesi cevabın **başında**, değerler sonra (model önce kuralı uygular, sonra olguları yazar — kural 2'nin tersine cevap boş değil).
- `_COMPARATIVES` listesi eval'de (kod değil prompt); yeni ifade çıkarsa liste genişler.
- `required_phrases`/`forbidden_phrases` alanları genel; `_Strict` şema ile mevcut sorulara alan eklemek zorunlu değil (varsayılan `[]`).
- `insufficient_data` için `action: request_data` korunur.
- Canlı ölçüm yalnızca 3 soru × 3 tekrar; tam eval koşulmaz.
