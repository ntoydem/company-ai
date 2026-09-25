# Phase 3.2b — Retrieval/cevap düzeltmeleri (Phase 4.1 bulguları): Implementation Plan

## Bağlam ve tespitler

Phase 4.1 (`phase-4-1`) eval'i eşiğin altında kapattı (document %52,2, temporal %33,3, isolation %50);
PHASES.md'nin kuralı gereği Phase 4.2 öncesi buraya dönülüyor. Bu faz **dar kapsamlı**: yeni özellik yok, yalnızca
raporun §3/§7/§8'indeki iki kök nedeni ölçüp düzeltmek ve eval'i eşiğin üstüne çıkarmak.

Okunanlar: `docs/reports/PHASE_4_1_REPORT.md` §3/§7/§8, `backend/app/services/{answer_prompt,retrieval,
search_query,ask}.py`, `backend/app/repositories/document_chunk_repo.py` (`search_fts`/`search_vector`), ADR-007/020/021,
`seed_data/documents/manifest.json` (`page_map`, `key_facts_used`). Ayrıca canlı DB'de (`audit_log`, `document_chunks`)
raporun bulgularını yeniden sorguladım — aşağıdaki tespitler o sorgulardan.

### T1 — "Model tutarsız" bulgusunun büyük kısmı aslında **Postgres eşitlik (tie) sıralaması**
Raporun kök neden 2'si ("aynı soru/bağlam, bazen cevap bazen red") için varsayım LLM'di. Canlı SQL bunu çürütüyor:
`"Ankara RES'in toplam finansman (kredi) tutarı nedir?"` için FTS skor dağılımı — 0.6 ×1, 0.4 ×3, 0.3 ×2, **0.2 ×28**,
0.1 ×8. Hedef sayfa (Facility Agreement s.4, "50,400,000 EUR" burada) **0.2 katmanında, 27 başka chunk'la berabere**.
`search_fts` `ORDER BY rank DESC LIMIT 20` yapıyor, **eşitlik bozucu yok** → 6 üst chunk'tan sonra kalan 14 slota 28
beraberenin hangisinin gireceğini Postgres rastgele seçiyor (heap sırası/plan). Aynı sorunun 3 dk arayla bir kez
reddedilip bir kez doğru cevaplanması (06:01:42 red, 06:05:16 doğru, ikisi de ~1 sn) tam bunu gösteriyor: **prompt'a
giden chunk kümesi koşudan koşuya değişiyor**, model aynı prompt'a farklı davranmıyor. LLM varyansı sıfır demek değil
— §1'deki ölçüm ikisini ayırıyor — ama önce ölçülmeden prompt'a dokunulmayacak.

### T2 — top_k=20 korpusun dörtte biri; prompt bütçesi bunun 3-4 katını rahat kaldırıyor
86 chunk (sayfa), ortalama ~450 karakter (~150-200 token). 20 chunk ≈ 3-5k `tokens_in` (eval'de 4-5,7k ölçüldü).
Gemini flash-lite'ın bağlam sınırı bunun yüzlerce katı. `retrieval_top_k` zaten bir ayar (`config.py`, varsayılan 20)
— 40'a çıkarmak yukarıdaki sorguda eşleşen 42 chunk'ın **tamamını** prompt'a sokar, hedef sayfa kesin girer. Phase 5.1
(~70 belge, ~400-500 chunk) ölçeğinde de 40-60 chunk ≈ 10-15k token, hâlâ ucuz. Ama tek başına yeterli değil: eşitlik
bozucu olmadan sonuç yine tekrarlanamaz (ADR-021 "deterministic"). İkisi birlikte gerekli.

### T3 — Retrieval **sayfa** seviyesinde hiçbir yere kaydedilmiyor; "retrieval mi, model mi" sonradan ayırt edilemiyor
`audit_log.documents_retrieved` belge id'leri; `AskResponse.retrieved_document_ids` de öyle. Phase 4.1 raporundaki "14
soruda retrieval doğruydu" ifadesi belge seviyesindeydi — sayfa seviyesinde **yanlıştı** (T1). §1'deki ölçüm için
her `/api/ask` çağrısının prompt'a hangi (belge, sayfa) çiftlerini soktuğu bilinmeli. Seçenekler §1'de, karar SORU 1.

### T4 — 429 ≠ 503, ama API ikisini de 503 yapıyor
`audit_log.error` gerçek kodu saklıyor: `gemini-3.5-flash` koşusunda 20:09-20:12 arası `503 "high demand"`, 20:13'ten
itibaren **`429 "You exceeded your current quota"`** — yani "yarıda kesilme" gerçekten günlük kotaydı, `run_eval.py`'nin
güvenli-durdurma tahmini doğruydu. Bu fazda değişiklik yok; ölçüm bütçesini (§1/§6) buna göre planlıyorum.

### T5 — Sayfa seviyesi "doğru cevap" LLM'siz, kotasız türetilebilir
`manifest.json` her belge için `key_facts_used` (`{"total_debt": "50,400,000 EUR", ...}` — belgeye **basılan** literal
metin) ve `page_map` taşıyor. Bir sorunun `expected_answer` ledger yolu → hangi belgelerin `key_facts`'ında aynı yol
var → o belgelerin `key_facts_used` literal'i → `document_chunks.text`'te hangi sayfada geçiyor. Bu, her soru için
**hedef (belge, sayfa) kümesi**dir; retrieval'ın onu top-k'ya sokup sokmadığı saf SQL ile, saniyeler içinde, 43 soru
için ölçülür. Bu fazın asıl geliştirme döngüsü budur (§3/§4) — LLM yalnızca son doğrulamada (§6).

### T6 — RRF k=60, 20+20'lik listelerde tek-listeli sonucu **yapısal olarak** eliyor
Yalnızca vektör listesinde 1. sıradaki chunk: `1/(60+1) = 0.0164`. İki listede de olan bir chunk, en kötü konumda bile
(20, 20): `2/80 = 0.025 > 0.0164`. İki liste ≥20 ortak chunk içeriyorsa (Facility belgelerinin sayfaları ikisinde de
üstte — çok olası) **hiçbir vektör-tek sonuç fused top-20'ye giremez**, `[:top_k]` kesiminde düşer. Embedding'in 15
soruda "işe yaramamış" görünmesinin en olası nedeni bu: FTS'in kaçırdığı sayfayı vektör bulsa bile birleştirme onu
atıyor. Embed kalitesiyle ilgisi yok. Kesin teşhis §4'te (sıralama logları).

### T7 — Eşanlam listesi soru setinden değil alan sözlüğünden türetilmeli
43 sorudaki 97 farklı arama terimi içinde İngilizce belgede karşılığı olmayan Türkçe finans/enerji terimi ~25
(`finansman, kredi, tutar, faiz, marj, vade/tenor, kapasite, lisans, sözleşme, bedel, kapanış, kalan/ödenmemiş,
yerli banka, tadil, geçici kabul, ticari işletme, yüklenici, taahhüt…`). Golden sorulara göre yazılan bir liste
Phase 5.1'in 60+ sorusunda yine delik verir; liste **alan sözlüğü** olarak (enerji projesi finansmanı terminolojisi)
yazılır, golden set yalnızca kapsama testidir.

### T8 — `ANK-ISO-002`: yol yanlış, doğru yol ledger'da zaten var
Soru "Hangi projenin üretim lisansı var?" → beklenen cevap proje **adı**; `ankara_res.yaml` `project.name: Ankara RES`
(etiketsiz kimlik anahtarı, `resolve_path` çözüyor). `eval_lib._classify_and_format` bu string için `_FIELD_KIND`
eşleşmesi bulamayıp "atla" der — `.name` ile biten yol için literal kabul kuralı gerekir (tek satır).

---

## 1. Tutarlılık ölçümü — 14 soru × 3 tekrar, retrieval ve model ayrı ayrı

**Ne ölçülüyor:** Phase 4.1'de "reddedildi" olan 14 soru (`ANK-DEV-004`, `ANK-FIN-001..007`, `ANK-FIN-009`,
`ANK-FIN-012`, `ANK-FIN-013`, `ANK-EPC-004`, `IZM-DEV-005`, `IZM-DEV-006`), her biri 3 kez, **düzeltmelerden önce**
(baseline: mevcut `phase-4-1` kodu, `EMBEDDINGS_ENABLED=false`, `gemini-3.5-flash-lite`). Her tekrar için üç alan:
1. `target_in_prompt`: hedef (belge, sayfa) çiftlerinden (T5) en az biri prompt'a girdi mi?
2. `answered`: model cevapladı mı (`AskResponse.answered`)?
3. `value_ok`: cevap beklenen değeri içeriyor mu (`eval_lib.value_check_passes`, mevcut kod)?

**Çıktı tablosu (rapora):** soru × {tekrar1,2,3} matrisi + üç özet oran: *retrieval kararlılığı* (3 tekrarda
`target_in_prompt` aynı mı), *model kararlılığı* (`target_in_prompt=True` olan tekrarlarda `answered` oranı — **asıl
"model reddediyor mu" sayısı bu**), *uçtan uca* (`value_ok` oranı). Beklenti (T1): retrieval kararlılığı düşük,
model kararlılığı yüksek. Beklenti tutmazsa §2 devreye girer.

**Araç:** `scripts/run_eval.py`'ye `--repeat N` ve `--ids ANK-FIN-001,...` argümanları (yeni script değil — aynı
login/hız-sınırı/retry altyapısı; `eval_lib`'e `consistency_report()` ve `render_consistency_markdown()`). Hedef sayfa
türetimi `eval_lib.target_pages(question, manifest, chunks_by_doc)` (T5) — LLM'siz, birim testli.

**`target_in_prompt` nereden okunacak (SORU 1):** önerim `audit_log`'a `chunks_retrieved: JSONB`
(`[{"document_id", "page_number", "rank"}]`, migration `0007`) — `_write_audit_log` zaten `chunks`'a sahip; SPEC_06 §1
"hangi kaynaklar kullanıldı"nın sayfa seviyesi hali, AUDITABILITY kuralının doğal uzantısı; script `request_id`
üzerinden (`X-Request-Id` yanıt başlığı, ADR-017) satırı çeker. Alternatif: `AskResponse`'a `retrieved_pages` alanı
(API yüzeyi büyür, frontend kullanmaz) ya da yalnızca structured log (script'in `docker compose logs` parse etmesi
gerekir — kırılgan). Bütçe: 42 çağrı, ~10 dk, kotanın küçük bir kısmı.

## 2. "Yetersiz bilgi" eşiği — ölçüme koşullu prompt değişikliği

Rule 2 bugün: *"Kaynaklar soruyu güvenilir şekilde cevaplamaya yetmiyorsa…"* — "güvenilir" tanımsız; rule 1 ("kaynakta
olmayanı yazma") ile birleşince model, değer **kaynakta varken** bile bağlam gürültülüyse (20 chunk'ın 19'u alakasız)
reddetmeye eğilimli olabilir. **Karar kuralı:** §1'de model kararlılığı ≥ %90 ise rule 2'ye **dokunulmaz** (T1
doğrulanmış olur, sorun retrieval'dır). < %90 ise rule 2 şu netleştirmeyle değiştirilir (tek cümle ekleme, mevcut
sabit cümle değişmez):

> 2. … yetmiyorsa … yeterli bilgi bulamadım. **Sorulan değer/tarih/olay kaynakların herhangi birinde açıkça yazıyorsa
> kaynaklar yeterlidir — diğer kaynakların ilgisiz olması cevabı engellemez; o değeri, kaynağını etiketleyerek yaz.**

Değişiklik `SYSTEM_PROMPT`'ta → `make prompt-doc` → `docs/prompts/ANSWER_SYSTEM_PROMPT.md` (lint bunu zorluyor) →
`tests/live/test_ledger_live.py`'ye "gürültülü bağlamda cevap verir" canlı testi (`make test-llm`). Rule 6/ADR-014
("belgelerde sebep belirtilmemiş") ve rule 3 (proje karışması) etkilenmez; `isolation`/`hallucination` regresyonu §6'da
eval ile kontrol edilir — **bu değişiklik hallucination'ı artırırsa geri alınır** (kabul kriteri %100 kırmızı çizgi).

## 3. FTS eşanlam/çapa sözlüğü — embedding'e ucuz alternatif

**Tasarım:** `app/services/search_glossary.py` — `GLOSSARY: dict[str, tuple[str, ...]]`, anahtar Türkçe **kök/gövde**
(`turkish_lower` sonrası, örn. `"finansman"`, `"kredi"`, `"faiz"`, `"marj"`, `"vade"`, `"tenor"`, `"kapasite"`,
`"lisans"`, `"sözleşme"`, `"bedel"`, `"kapanış"`, `"kalan"`, `"ödenmemiş"`, `"tadil"`, `"taahhüt"`, `"yüklenici"`,
`"geçici kabul"`, `"ticari işletme"`, `"dscr"`), değer İngilizce belge terimleri (`("financing", "facility", "loan")`,
`("interest",)`, `("margin",)`, `("tenor", "maturity")`, `("capacity", "MW")`, `("licence", "license")`,
`("agreement", "contract")`, `("price", "consideration")`, `("close", "closing")`, `("outstanding",)`,
`("amendment",)`, `("covenant",)`, `("contractor", "EPC")`, `("provisional acceptance",)`, `("commercial operation",
"COD")`, `("debt service coverage", "DSCR")`). Ters yön de (İngilizce soru → Türkçe mevzuat belgesi: `"licence"→"lisans"`,
`"EIA"→"ÇED"`) aynı tabloda. **Çok kelimeli** değerler tırnaklı `websearch_to_tsquery` ifadesi olarak eklenir
(`"provisional acceptance"` → phrase). Kelime kökü eşleştirme: soru token'ı `turkish` stemmer'dan geçmeden önce
sözlük anahtarıyla **önek** eşleşmesi (`"finansmanında"` → `"finansman"`; `"kredisinin"` → `"kredi"`) — küçük ve
öngörülebilir, Türkçe morfoloji kütüphanesi **eklenmez**.

**Entegrasyon:** `build_search_query()` → her token için sözlük genişletmesi OR'a eklenir; `ts_rank_cd` zaten çok
terim eşleşen chunk'ı yukarı taşır — hedef sayfa (T1 örneği: "total financial accommodation", "50,400,000") artık
`financing`/`facility` ile de eşleşip 0.2 katmanından çıkar. Sözlük **yalnızca FTS legini** etkiler (ADR-020 kapsamı);
`raw_question` embedding'e dokunulmadan gider. ADR-020'ye "Phase 3.2b concretization" notu.

**Doğrulama LLM'siz (T5):** `scripts/run_eval.py --retrieval-only` — 43 soru için `retrieve()` doğrudan (container
içi, `finans`/`enerji` kullanıcısıyla, gerçek `allowed_document_ids`), hedef sayfa top-k'da mı? Çıktı: *sayfa recall@k*
(hedef sayfası olan sorularda). Eşik: sözlük + T2 (top_k=40) + eşitlik bozucu ile **recall@40 = %100** (43 soruda),
sözlüksüz mevcut kodda ölçülen değerle karşılaştırmalı (rapora). Sözlüğün kapsama testi: `tests/test_search_glossary.py`
(her golden sorunun terimlerinden en az biri genişliyor mu — değil, **hedef sayfanın kelimelerinden** en az biri
sorgunun genişletilmiş halinde var mı; ikincisi anlamlı olan).

**Küçük ama gerekli eşlik eden düzeltmeler (aynı PR):** `search_fts`'e deterministik eşitlik bozucu
(`ORDER BY rank DESC, document_id, chunk_index`) — T1'in kökü; `retrieval_top_k` varsayılanı 20→40 (SORU 2);
`search_vector`'e de aynı eşitlik bozucu.

## 4. Embedding'in 15 soruda işe yaramama teşhisi

**Yöntem (kod: yalnızca loglama):** `retrieve()`'e tek bir structured `log.info("retrieval explain", extra={...})`:
`fts_ms`, `embed_ms`, `vector_ms`, `fts_top` ve `vector_top` (ilk 20 `(document_id, page, rank)`), `fused_top`,
`fallback` (embed hatası oldu mu). `EMBEDDINGS_ENABLED=true` + `--retrieval-only` (LLM yok) ile 15 soru koşulur;
üç hipotez sırayla elenir:
1. **Zaman aşımı/fallback** — Phase 4.1 probe'unda 15 isteğin 4'ü 19-28 sn sürdü (`audit_log.execution_ms`); 30 sn
   `EMBED_TIMEOUT_S`'in altında ama şüpheli. Log `fallback=true` gösteriyorsa: TEI CPU ısınması/eşzamanlılık; çözüm
   backfill/ask için ayrı timeout değil, `embed` healthcheck + `wait_for_services` (Phase 3.4'te embed'e healthcheck
   **yazılmamıştı** — T-not: `docker ps` health göstermiyor).
2. **RRF yapısal eleme (T6)** — `vector_top` hedef sayfayı içeriyor ama `fused_top` içermiyorsa doğrulanmıştır.
   Düzeltme: her legi `2×top_k` çekip fused listeyi `top_k`'da kesmek (tek-listeli chunk'a yer açar) **ve/veya**
   k'yı 60'tan 10'a indirmek (kısa listelerde standart; Cormack'ın 60'ı 1000'lik listeler için). Hangisi: `--retrieval-
   only` recall@40 ile ikisi de ölçülür, iyi olan kalır.
3. **Vektör de bulamıyor** — `vector_top` hedefi içermiyorsa bge-m3 TR soru ↔ EN sayfa eşleşmesi zayıf demektir;
   bu fazda **düzeltilmez**, Phase 3.4'e (ADR-007) not düşülür ("hibrit, FTS sözlüğüne göre ek kazanç sağlamadı").

**Karar kuralı:** 1 veya 2 doğrulanırsa düzeltme bu fazda (küçük, ölçülebilir); 3 ise not. Her durumda referans
konfigürasyon `EMBEDDINGS_ENABLED=false` kalır (ADR-007) — §6'daki kabul eval'i **embedding kapalı** koşulur; embedding
açık koşu ek bilgi olarak rapora girer.

## 5. `ANK-ISO-002` yol düzeltmesi

`questions.json`: `"expected_answer": "ledger:ankara_res.project.timeline.licence.date"` →
`"ledger:ankara_res.project.name"`. `make validate-ledger` yolu çözüyor (etiketsiz kimlik anahtarı, `resolve_path`
düz string döner). `eval_lib._classify_and_format`: yol `.name` ile bitiyorsa `(value,)` literal (T8) + testi.
Aynı taramada diğer 42 sorunun yol↔soru uyumu bir kez daha gözle kontrol edilir; **başka değişiklik bulunursa
listelenir, yapılmaz** (ledger onay disiplini, ADR-013).

## 6. Kanıt: eşikler nasıl geçilecek

| Adım | Komut | Beklenen |
|---|---|---|
| 0. Baseline tutarlılık (düzeltme öncesi) | `make eval EVAL_ARGS="--ids <14 id> --repeat 3"` | §1 tablosu; retrieval kararlılığı düşük |
| 1. Retrieval recall (LLM'siz), önce/sonra | `make eval EVAL_ARGS="--retrieval-only"` | sözlük+top_k+tie-break sonrası recall@40 = 43/43 hedefli soruda %100 |
| 2. Tutarlılık (düzeltme sonrası) | adım 0 tekrar | 14 soruda `target_in_prompt` 42/42, `answered` ≥ 40/42 |
| 3. **Kabul eval'i** | `make eval` (`gemini-3.5-flash-lite`, embedding kapalı) | isolation/hallucination/authorization **%100**; document/temporal **≥ %80** (`ANK-ISO-002` düzeltmesiyle isolation 4/4 mümkün) |
| 4. Model karşılaştırması (bütçe izin verirse) | `make eval MODEL=gemini-3.5-flash` | 429'a takılırsa T4 notuyla kısmi rapor |
| 5. Regresyon | `make test`, `make lint`, `make test-llm` | yeşil; prompt değiştiyse yeni canlı test dahil |

Kota bütçesi (T4): adım 0+2 = 84, adım 3 = 43, adım 4 ≤ 43 → ~170 çağrı, 13 sn aralıkla ~40 dk; günlük kotaya
sığmazsa adım 4 atlanır (raporda "atlandı, neden" ile), adım 3 asla atlanmaz. Kabul: adım 3'ün `results.md`'si
rapora, `results.json` `docs/reports/assets/phase_3_2b/`'ye kopyalanır (results klasörü git-ignored, kanıt kalıcı olsun).

---

## SORU (Naci cevaplamalı)

1. **Sayfa seviyesi retrieval kaydı nereye?** Önerim `audit_log.chunks_retrieved` (JSONB, migration `0007`) — SPEC_06
   §1'in doğal uzantısı, kalıcı fayda (admin panel Phase 5.2'de "bu cevap için hangi sayfalar okundu" gösterebilir).
   Alternatifler: `AskResponse`'a alan (API büyür) / yalnızca log. Onaylıyor musun?
2. **`retrieval_top_k` 20 → 40** (T2): prompt ~2× büyür (5k→10k token), Gemini için önemsiz, ama `.env.example`/README'de
   belgelenen bir varsayılan değişiyor. 40 mı, yoksa "eşleşen tüm chunk'lar, en fazla 60" mı? Önerim 40.
3. **Sözlük konumu:** `app/services/search_glossary.py` (kod, tüm kurulumlar için ürün davranışı) mı, yoksa
   `seed_data/`/`$DATA_ROOT` altında düzenlenebilir YAML mı (müşteriye göre terminoloji)? Önerim kod — V0'da tek
   alan (enerji proje finansmanı), YAML "ileride lazım olur" soyutlaması olur. Ama ürün kararı.
4. **Prompt değişikliği koşullu (§2):** "model kararlılığı ≥ %90 ise dokunma" eşiğini onaylıyor musun, yoksa ölçüm ne
   çıkarsa çıksın netleştirmeyi ekleyelim mi? Önerim koşullu — ölçülmemiş bir sorunu düzeltmek başka bir şeyi bozar
   (Phase 3.2'de rule 6 deneyimi).

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- Yeni script yok: tutarlılık ve retrieval-only modları `run_eval.py`'ye argüman (`--repeat`, `--ids`,
  `--retrieval-only`); mantık `eval_lib`'de, birim testli.
- Hedef sayfa türetimi `manifest.json key_facts_used` literal'inin chunk metninde aranmasıyla (T5); questions.json'a
  sayfa numarası **eklenmiyor** (belge yeniden üretilince kayar).
- `search_fts`/`search_vector` eşitlik bozucu `(rank DESC, document_id, chunk_index)` — davranış değişikliği değil,
  tekrarlanabilirlik.
- Sözlük anahtarları önek eşleşmeli (`finansman*`), Türkçe morfoloji kütüphanesi yok; çok kelimeli değerler phrase.
- RRF düzeltmesi yalnızca §4'te hipotez 2 doğrulanırsa; k ve liste uzunluğu recall ölçümüyle seçilir, "hissiyatla" değil.
- Prompt sabit cümleleri (`NO_ANSWER_TEXT`, `NO_REASON_TEXT`) değişmez; `is_no_answer()` bozulmaz.
- Faz adı/etiketi `3.2b` / `phase-3-2b`; PHASES.md durum tablosuna 3.2'nin altına satır, Phase 4.2'nin ön koşul notu
  sonuçla güncellenir.

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: ADR-020'ye "Phase 3.2b concretization" (sözlük, eşitlik bozucu, top_k); ADR-007'ye §4'ün
  sonucu (RRF düzeltmesi veya "hibrit ek kazanç sağlamadı" notu); ADR-016'ya `chunks_retrieved` (SORU 1 evetse).
- `docs/prompts/ANSWER_SYSTEM_PROMPT.md` (yalnızca §2 tetiklenirse, `make prompt-doc`).
- `infra/.env.example`, README ("Soru sorma" bölümüne top_k/sözlük notu; "Eval" bölümüne `--repeat`/`--retrieval-only`;
  "Bilinen sınırlar"daki eval maddesi sonuçla güncellenir).
- `docs/reports/PHASE_3_2B_REPORT.md` (+ `assets/phase_3_2b/results.json`), `docs/PHASES.md`, `git tag phase-3-2b`.

## Uygulama sırası

1. `eval_lib.target_pages()` + testleri; `run_eval.py --retrieval-only`; **mevcut kodla** recall@20 ölçümü (baseline).
2. SORU 1'e göre `chunks_retrieved` (migration 0007 + `_write_audit_log`) ; `--repeat/--ids`; **baseline tutarlılık**
   koşusu (§1, 42 çağrı) → rapora.
3. `search_fts`/`search_vector` eşitlik bozucu + `retrieval_top_k` (SORU 2) → recall tekrar.
4. `search_glossary.py` + `build_search_query` entegrasyonu + testler → recall@40 %100 hedefi.
5. §4 teşhisi (`make up-full`, explain logu, 15 soru retrieval-only) → düzeltme ya da not; `embed` kapatılır.
6. §2 karar kuralı: model kararlılığı < %90 ise rule 2 netleştirmesi + canlı test + `make prompt-doc`.
7. `ANK-ISO-002` düzeltmesi + `eval_lib` `.name` kuralı + `make validate-ledger`.
8. §6 tablosu: tutarlılık (sonrası), kabul eval'i, model karşılaştırması; `make test`/`make lint`/`make test-llm`.
9. Dokümanlar → rapor → PHASES.md → commit + tag `phase-3-2b` + push.

## Kritik dosyalar

- `backend/app/services/search_query.py`, `backend/app/services/search_glossary.py` (yeni)
- `backend/app/repositories/document_chunk_repo.py` (`search_fts`/`search_vector` sıralama), `backend/app/services/retrieval.py`
- `backend/app/services/answer_prompt.py` (koşullu), `backend/app/services/ask.py` + `alembic/versions/0007_*` (SORU 1)
- `scripts/eval_lib.py`, `scripts/run_eval.py`, `backend/tests/test_eval_lib.py`, `backend/tests/test_search_glossary.py` (yeni)
- `seed_data/evaluation/questions.json` (yalnızca `ANK-ISO-002`)
