# Adım 2 — Ek-F metin ve biçim (F-2, F-3, F-5, F-8) + Ç-2, Ç-3, Ç-10 — uygulama planı

**Tarih:** 09.10.2026 · **Durum:** plan, Naci onayı bekliyor; **kod değişikliği ve canlı çağrı yok** · **Dayanak:** `URUN1_KARARLAR_VE_SIRA.md` §3.2 adım 2 (Naci onayı 09.10), Ek-F Karakter Tanımı (AI-BalBal PR #16, ADT-2, iki Proje Yetkilisi onayı 09.10), `NACI_CEVAP_2026-10-08.md` §4 (Ç-2 A, Ç-3 A, Ç-10 A), `ADIM1_SORU15_REPORT.md` §4 (007 liste kotası, 001/011 biçim gözlemi) · **Dal:** `feat/adim2-ekf` (`feat/adim1-soru15` üzerinden; `main`'e birleştirme yok) · **Kapsam dışı:** F-4 gerçek belirsizlik tespiti (plan adım 4), cevap eşiği/kural 2 metni (Ç-1 A), sözlük tablosu (adım 8), kütüphane.

## 0. Bayrak

`EK_F_MODE` (env; `Settings.ek_f_enabled`, varsayılan **False**, `AliasChoices("EK_F_MODE", "EK_F_ENABLED")`, `infra/.env.example`'a satır). Kapalıyken bugünkü davranış bayt-bayt aynı (mevcut test paketi bunu zaten sabitler). Açıkken §1–§4. **ASSIST_MODE ile ilişki:** F-5 listeyi ADR-027 assist hesaplarından alır; `EK_F_MODE=true` bu hesapları **kendisi açar** (`assist_mode_enabled or ek_f_enabled` tek yerde, `Settings.assist_computations` özelliği). `ASSIST_MODE` eski ara sunum olarak kalır (kör test turu 1 sonrası kaldırma kararı, plan §3.2 adım 3). → **SORU 1.**

## 1. F-8 biçim — kodla, LLM'e bırakılmaz

Kaynak teşhisi: DSC-001'deki "Capex 72000000 EUR … 2021-11-15 00:00:00" Excel hattının **tablo yolundan** geliyor: `excel_ask._sql_value` 1×1 olmayan sonucu `str(v)` ile ham aktarıyor (float, `datetime`), model de aynen yazıyor. 1×1 yol zaten `format_value` ile TR biçiminde. DSC-011'deki para birimsiz "1.000.000": 1×1 yol, `unit=""` (SQL yolu birim bilmiyor).

| # | Değişiklik | Dosya / fonksiyon | Not |
|---|---|---|---|
| 1.1 | Yeni modül `app/services/tr_format.py`: `format_date(date\|datetime) → "GG.AA.YYYY"` (saat 00:00:00 düşer; saat ≠ 00:00 ise de yalnızca tarih — Ek-F'de saat yok), `format_number(x, decimals=None)` → `1.234.567,89` (tam sayı → ondalıksız), `format_amount(x, currency)` → `"1.234.567,89 USD"` (kod sonda, `TL/USD/EUR`; `TRY`→`TL`, `€/$/₺` → kod), `format_percent(x)` → `%2,90` (2 ondalık), `format_multiple(x)` → `1,20x`, `format_cell(value, column_label)` → sütun etiketinden birim çıkarır | yeni dosya | `excel_ask.format_value` bu modüle **taşınır** (tek yer); mevcut `%38,2` (1 ondalık) → `%38,2` korunur: yüzde ondalığı değer kaynaklıysa aynen, F-8 örneği 2 ondalık (`%2,90`) → kural: en az 1, en çok 2 ondalık, sondaki sıfır yalnızca 2. basamakta korunur (SORU 2) |
| 1.2 | Birim çıkarımı tablo yolunda: sütun etiketi `"Capex (EUR)"`, `"Cash to equity (EUR)"`, `"DSCR"` (x), `"… (%)"`, `"… (MWh)"`, `_meta` sayfası; etiket parantezindeki birim → `format_cell`. Birim bulunamazsa sayı TR biçiminde, birim **eklenmez** (uydurma yok, Ç-6). `datetime`/`date` hücre → `format_date` | `excel_ask._sql_value` → `_sql_table_text(result)` biçimli tablo; `_sql_value` 1×1 dönüşünde birim: tek sütunun etiketinden (`"Debt (EUR)"` → `EUR`) | DSC-011'in "1.000.000" → "1.000.000 EUR" (sütun etiketi birim taşıyorsa) |
| 1.3 | Modelin ham hücreyi yazmasını engellemek: `result_block`'a yalnızca **biçimli** tablo gider; `ANSWER_SYSTEM_PROMPT` (Excel) kural 1 "AYNEN verilen biçimde" zaten var → prompt değişmez. Çıktı denetimi (`_value_variants`) biçimli değerle çalışır (bugünkü gibi) | `excel_ask.answer_data_question` | Excel hattı prompt'u değişmez → Excel R1 soruları yine koşar (ANK-AUT, GEN-CMP içinde DATA/MIXED varsa) |
| 1.4 | Belge hattı son biçim geçidi `tr_format.polish_answer(text)` — **yalnızca güvenli dönüşümler:** (a) ISO tarih `YYYY-MM-DD( 00:00:00)?` → `GG.AA.YYYY`; (b) `GG.AA.YYYY 00:00:00` → saat düşer; (c) `1,234,567.89` İngiliz biçimi → TR (yalnızca binlik virgül + ondalık nokta kalıbı). **Dokunmaz:** `[K12]` etiketleri, belge/sözleşme numaraları (`S-26-001`, `ENR2026001121`), yıllar, boşluksuz 4+ haneli sayılar (uydurma gruplama riski) | `ask.py` answered dalında, `polish_answer` sonra `parse_citations` öncesi değil **sonrası** (etiketler korunur) | Belge kaynakları zaten TR biçimli (generator); geçit kaynağa sadık kalır, sayı eklemez. Ölçüm için `format_check` (§5) |
| 1.5 | Kaynak kartı tarihleri zaten `date`; arayüz biçimler (`ask.html fmtDate`). Değişiklik yok | — | — |

## 2. F-5 "Veri Yok" kalıbı — sabit cümle + yardım bloğu yerine (bayrak açık)

Model davranışı değişmez: kural 2 cümlesi modelin iç sinyali olarak kalır (`is_no_answer`). Kullanıcıya giden `answer` kodla **kurulur**:

```
[«{terim}» ifadesini {sözlük karşılığı} olarak anladım. ]      ← Ç-3, yalnızca soruda sözlük terimi varsa
Bu konuda kesin bilgi bulamadım.                               ← sabit karar cümlesi (ADR-014 yeni metin)
Elimde konuyla ilgili şunlar var:                              ← liste boş değilse
  Ankara RES: Facility Agreement (20.06.2022); …               ← F-3 proje başlıklı gruplar, ≤ 7 belge
  İzmir RES: ÇED Süreci Durum Yazısı (…)
İsterseniz açayım.
[Aradığınız bilgi genellikle {belge türü} belgesinde olur; yüklenirse cevaplayabilirim.]
                                                               ← yalnızca liste BOŞSA ve tür sözlükten biliniyorsa (F-5: yükleme ilk cümle olmaz, yalnızca kayıt yoksa)
{netleştirme sorusu}                                           ← her zaman son satır (F-5 "soru ya da seçenekle biter")
```

| # | Değişiklik | Dosya / fonksiyon |
|---|---|---|
| 2.1 | `answer_prompt.NO_DATA_VERDICT = "Bu konuda kesin bilgi bulamadım."`; `NO_ANSWER_TEXT` kalır (prompt kural 2, `is_no_answer`, bayrak kapalı çıktı) | `answer_prompt.py` |
| 2.2 | `assist.py` yeni `render_no_data(assist, *, understood: str \| None, typical_type: str \| None) -> str` — yukarıdaki kalıbı kurar; sayı/tarih yalnızca belge tarihleri (kaynak kartıyla aynı), başka rakam yok (G1) | `assist.py` |
| 2.3 | `ask.py`: `is_no_answer` dalında bayrak açıksa `answer = render_no_data(...)`, `answered=False` aynen; bayrak kapalı → `NO_ANSWER_TEXT` (bugünkü). Sıfır parça dalı aynı | `ask.py` (`answer_question`) |
| 2.4 | Ç-3 "anladım" cümlesi: `search_glossary.understood_terms(question_terms)` → soru terimlerinden `GLOSSARY`/`CONCEPT_GLOSSARY` anahtarına denk düşenler için `(terim, Türkçe karşılık)`; karşılık **kodda** (sözlük anahtarının TR etiketi; ör. `amendment → tadil`, `finansal model → finansal model (Financial Model)`). Yalnızca cevapsız dalda; cevaplı dalda eklenmez (gürültü) | `search_glossary.py` (+`TR_LABEL` eşlemesi), `assist.py` |
| 2.5 | "genellikle … belgesinde olur": `CONCEPT_GLOSSARY` genişletme yerine ayrı küçük `TYPICAL_DOCUMENT_TYPE` (kavram → belge türü adı, ör. "ödeme planı" → "Financial Model / kredi sözleşmesi geri ödeme maddesi"); eşleşme yoksa cümle **yazılmaz** | `search_glossary.py` |
| 2.6 | MIXED birleştirme: belge hattı cevapsız + Excel cevaplı → bayrak açıkken "Belgelere göre: {Veri Yok}" bölümü **gösterilmez**, yalnızca Excel cevabı + kaynak (DSC-011 bugünkü çift başlık). İkisi de cevapsızsa tek F-5 metni | `ask_router.merge_mixed_answer` (bayrak parametresi) — SORU 3 |
| 2.7 | ADR-014 güncelleme notu + **ADR-030** "Ek-F rendering layer: fixed verdict, code-built pattern, format gate" | `docs/ARCHITECTURE.md` |
| 2.8 | Eval: `eval_lib` G2 kontrolü cevapsız yanıtta `NO_ANSWER_TEXT` **veya** `NO_DATA_VERDICT` ile başlamayı kabul eder (anladım cümlesi öndeyse ikinci cümle); `answered` alanı zaten API'den. "sabit cümle tek başına" metriği: `answered=False ∧ available=[] ∧ question=None` tanımı aynı | `scripts/eval_lib.py`, `test_eval_lib.py` |

## 3. F-3 liste — ≤ 7, proje gruplu, metadata kotası (007)

| # | Değişiklik | Dosya / fonksiyon |
|---|---|---|
| 3.1 | `MAX_AVAILABLE = 7` (bayrak açık; kapalı 5 kalır → sabit iki değer, `assist_limits(settings)`) | `assist.py` |
| 3.2 | **Kota:** `build_insufficient_assist` — parça kaynaklı (chunk-vouched) en çok **4**, metadata/kavram kaynaklı için **≥ 3 yer ayrılır**; metadata eşleşmesi azsa kalan yerleri parça kaynaklılar doldurur. Metadata adayları varlık sorusu şartı olmadan da eklenir (bugün yalnız varlık sorusu ya da boş liste). Sıra: metadata eşleşmesi soru terimini **başlıkta** taşıyorsa (ör. "ÇED" ∈ "Ankara RES ÇED Olumlu Kararı") öne | `assist.py` |
| 3.3 | **Gruplama:** `Assist.available` korunur (eval/G3 aynı); yeni `Assist.groups: tuple[AvailableGroup, ...]` — `project_code`, `project_name` (Project tablosundan), `documents` (ilgili `available` alt kümesi, tarih sırası yeni→eski). Grup sırası: soruda adı geçen proje önce; yoksa belge sayısı çoğu önce; proje kodu olmayan belgeler "Şirket geneli" grubu. Tansu T-1 cevabı gelmediği için **projeye göre** gruplama — raporda belirtilecek | `assist.py` (`group_available`), `schemas/ask.py` (`AssistBlock.groups`) |
| 3.4 | F-5 metni grupları `Proje adı: başlık (GG.AA.YYYY); …` satırlarıyla yazar; 7'den fazla aday varsa "… ve N belge daha" **sayı** olarak (F-3) — sayı G1'de "kaynaklarda olmayan rakam" sayılmaz: eval `fact_tokens` için `_COUNT_PHRASE` istisnası (SORU 4) | `assist.py`, `eval_lib.py` |
| 3.5 | G3 değişmez: gruplar yalnızca `allowed` içinden (`available` ile aynı küme); yeni test "gizli belge grupta yok" | `test_assist*.py` |

## 4. F-2 dolgu yok · Ç-2 `previous_question` · Ç-10 chip'ler

| # | Değişiklik | Dosya / fonksiyon | Not |
|---|---|---|---|
| 4.1 | F-2: kural 7'ye tek cümle: "Selamlama, 'memnuniyetle', 'harika soru' gibi dolgu ifadeleri, ünlem ve emoji kullanma." (bayrak açık prompt'ta; `SYSTEM_PROMPT` kapalıyken bayt-aynı kalır → `system_prompt(settings)` üç varyant yerine **iki**: `assist` promptu Ek-F cümlesini alır, çünkü Ek-F assist hesaplarını açar) | `answer_prompt.py`, `docs/prompts/ANSWER_SYSTEM_PROMPT.md` (lint diff), `test_answer_prompt.py` | **Prompt değişir → R1 ×1 koşulur** |
| 4.2 | Ç-2: `AskRequest.previous_question: str \| None = None` (max 1000); bayrak açıkken `build_user_prompt`'a `ÖNCEKİ SORU (yalnızca bağlam): …` satırı (BUGÜN satırının altına); retrieval sorgusu değişmez **ama** mevcut soru proje kelimesi içermiyor ve önceki içeriyorsa önceki sorunun proje kelimeleri `raw_question` bağlamına eklenir (metadata/assist proje tespiti için; parça sorgusu aynı). Audit: `assist` JSON'a `context: {previous_question}` (migration yok) — SORU 5 | `schemas/ask.py`, `answer_prompt.build_user_prompt`, `ask.py`, `ask_router.py` (audit) |
| 4.3 | Ç-10: `backend/app/static/ask.html` örnek linkleri kaldırılır. AI-BalBal `BalbalChat.tsx` `example-list` + `strings.ts exampleQuestions/P2`: Tansu'nun reposu → ayrı dal `feat/ekf-chips-kaldir` + PR (bizim repoya değil); PR açılması için **ayrıca onay** (SORU 6). UI'nin F-5'i göstermesi: `answer` zaten tam metni taşır; `assist.groups` linkli liste olarak (ayrı UI işi, aynı PR'da notlanır) | `static/ask.html`, AI-BalBal PR |

## 5. Ölçüm — **31 çağrı**, bayrak `EK_F_MODE=true` (ASSIST_MODE kapalı kalır)

| Koşu | Sorular | Çağrı | Kriter (sonuca bakarak gevşetilmez) |
|---|---|---|---|
| R1 ×1 | 14 (`a2_ids.env R1`: ANK-AUT-001/002/003, ANK-ISO-002/003, GEN-CMP-001/002/003, GEN-HAL-001…004, IZM-ISO-001/004) | 14 | cevaplanma gerilemesi 0 (referans 6 cevaplanabilir), **≥ 12/14**, G1–G3 14/14 |
| Keşif ×1 | 13 resmi (GEN-DSC-001…013) | 13 | **≥ 10/13** (Adım 1 tabanı; 007 kota düzeltmesiyle 11 hedef), "kesin bilgi bulamadım" tek başına 0, G1–G3 13/13 |
| Negatif kontrol ×1 | ANK-NEG-003, ANK-NEG-004, CO-NEG-005, GEN-AMB-003-F | 4 | uydurma 0, cevaplanma referansla aynı (4/4 cevaplandı, 08.10), G1–G3 4/4 |
| **Toplam** | | **31** | ayrıca `format_check` 31/31 |

`format_check` (eval'e yeni, kodla): cevap metninde (a) ISO tarih/`00:00:00` yok, (b) `\d{7,}` gruplanmamış sayı yok, (c) `1,234.56` biçimi yok, (d) `%` ile yazılan oran `%\d+,\d+` biçiminde, (e) ≥ 4 haneli tutarın yanında para birimi var **yalnızca Excel hattında** (belge hattında kaynak biçimi esas; para birimi kaynakta yoksa eklenmez). `results.json`'a `format_check/format_reason`.

Sıra: `make test` + `make lint` yeşil → kuru koşu LLM'siz (`render_no_data` 13 keşif sorusu için `available` tahmini, 007'de ÇED Olumlu Kararı listede mi; 0 çağrı) → bayrak aç + `make restart-backend` → R1 → keşif → negatif → bayrak kapat + restart (kontrol: `ek_f_enabled = False`). **Durma:** herhangi G1–G3 ihlali → anında dur, bayrak kapat, raporla. R1 < 12/14 → geri al. Tek prompt revizyon hakkı (yalnızca F-2 cümlesi), revizyon sonrası R1 yeniden (+14 çağrı) → o durumda toplam 45; **önceden izin yoksa revizyon yapılmaz, raporlanır.** Kota kontrolü için ayrı çağrı yok (503 görülürse eval'in yeniden denemesi).

## 6. Testler (deterministik, `make test`)

- `test_tr_format.py`: tarih/datetime, tam/ondalık sayı, para birimi (TL/USD/EUR, sembol ve `TRY` eşlemesi), yüzde, çarpan, sütun etiketinden birim, `polish_answer` (dönüştürülenler ve **dokunulmayanlar**: `[K12]`, `S-26-001`, `ENR2026001121`, 2026).
- `test_excel_ask.py` ek: çok sütunlu SQL sonucu biçimli tablo (float → `72.000.000 EUR`, datetime → `15.11.2021`); 1×1 sütun etiketinden birim.
- `test_assist_ekf.py`: `render_no_data` 5 varyant (liste var/yok, anladım cümlesi, tipik tür, soru son satır, G1: metinde belge tarihleri dışında rakam yok); kota (5 parça + 2 metadata → metadata ikisi de listede, toplam ≤ 7); gruplama sırası (soruda adı geçen proje önce, "Şirket geneli"); gizli belge grupta yok (G3); 7+ aday → "ve N belge daha".
- `test_ask.py` ek: bayrak kapalı → `NO_ANSWER_TEXT` bayt-aynı; açık → `NO_DATA_VERDICT` ile başlar/anladım cümlesi; `previous_question` prompt'a girer, audit JSON'da; MIXED belge-cevapsız + Excel-cevaplı tek bölüm.
- `test_answer_prompt.py`: kapalı prompt bayt-aynı; açık promptta F-2 cümlesi; `docs/prompts/ANSWER_SYSTEM_PROMPT.md` lint diff'i (hangi varyantı yazdığımız — SORU 7).
- `test_eval_lib.py`: G2 iki karar cümlesini kabul eder; `format_check` olumlu/olumsuz; sayı istisnası.

## 7. Dokümanlar
ADR-030; ADR-014 notu; `.env.example` `EK_F_MODE=false`; `docs/prompts/ANSWER_SYSTEM_PROMPT.md`; README "Veri Yok kalıbı (Ek-F)" paragrafı; `docs/reports/ADIM2_EKF_REPORT.md` (+ assets ham sonuçlar); `docs/PHASES.md` not satırı; `URUN1_KARARLAR_VE_SIRA.md` §3.2 adım 2 durumu (ayrı dalda — rapor sonrası tek satır).

Büyüklük: M (≈ 2 gün kod + test, 1 ölçüm saati).

## SORU (Naci)

1. **Bayrak ilişkisi:** `EK_F_MODE=true` assist hesaplarını kendisi açsın (A, tek bayrakla ölçüm; ASSIST_MODE kapalı kalır) mı, ikisi birden açılması gereksin (B) mi? Önerim A.
2. **Yüzde ondalığı:** Excel'den gelen `%38,2` 2 ondalığa (`%38,20`) zorlansın (A) mı, değerin kendi ondalığı korunup en çok 2 (B) mi? Önerim B (yuvarlama/sıfır ekleme yok, Ç-6).
3. **MIXED'te belge hattı cevapsızsa** "Belgelere göre: Veri Yok" bölümü gizlensin, yalnız Excel cevabı (A) mı; iki bölüm kalsın, ilk bölüm F-5 (B) mi? Önerim A.
4. **"… ve N belge daha" sayısı** G1 için istisna olsun (A) mı, sayı yazılmasın, "devamını gösterebilirim" densin (B) mi? Önerim A (F-3 "toplam sayıyı söyler").
5. **`previous_question` audit'i:** `assist` JSON içinde `context` (A, migration yok) mı, `audit_log.previous_question` kolonu (B, migration 0016) mi? Önerim A şimdi; O-13/8 ölçüm kaydı adımında (plan adım 9) kolonlara taşınır.
6. **Ç-10 AI-BalBal PR'ı:** bu adımda Tansu'nun reposuna chip kaldırma + `groups` listesi PR'ı açılsın (A) mı, yalnızca `static/ask.html` yapılıp PR rapor sonrası ayrı onayla (B) mi? Önerim B.
7. **`docs/prompts/ANSWER_SYSTEM_PROMPT.md`** hangi varyantı tutsun: bayrak açık (Ek-F) prompt (A) mı, kapalı (B) mi? Bugün kapalı varyant yazılı ve lint onu diff'liyor. Önerim: A'ya geçiş **bayrak varsayılan açık olduğunda** (adım 3); şimdi B kalır, Ek-F cümlesi dosyaya not olarak eklenir.
8. **Belge hattı biçim geçidi** (1.4) yalnızca tarih + İngiliz sayı biçimiyle sınırlı kalsın (A) mı, 7+ haneli boşluksuz sayıları da gruplasın (B, belge numarası riski) mi? Önerim A.
