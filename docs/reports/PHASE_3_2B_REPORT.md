# Phase 3.2b Raporu — Retrieval/cevap düzeltmeleri (Phase 4.1 bulguları)

**Tarih:** 25.09.2026  **Model:** Fable 5.1  **Tag:** phase-3-2b  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
Bu faz için ayrı kabul kriteri yok; hedef PHASES.md'nin Phase 4.1 eşiklerini geçmek (plan §6).

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| 1 | Tutarlılık ölçümü (14 soru × 3, düzeltme öncesi/sonrası), retrieval ve model ayrı | ✅ | `assets/phase_3_2b/consistency_{before,after}.md` — §3 |
| 2 | Retrieval sayfa recall'ı LLM'siz ölçüldü, sözlük+eşitlik bozucu sonrası %100 | ✅ | `assets/phase_3_2b/recall_{before_top20,after_top20,after_top40}.md`: 18/20 → 20/20 |
| 3 | isolation/hallucination/authorization %100 | ❌ (hallucination %100, authorization %100, **isolation %75** — `ANK-ISO-003`, içerik boşluğu) | §4 kabul eval'i |
| 4 | document/temporal ≥ %80 | ❌ (document %69,6, temporal %66,7 — 4.1'deki %52,2 / %33,3'ten; kalan 11 başarısızlığın 9'u içerik/veri seti, §3.2) | §4 kabul eval'i |
| 5 | İki model karşılaştırması | ✅ (ikinci model yine kotaya takılıp yarıda kesildi — 4.2) | §4.2 |

## 2. Yapılanlar
- **Ölçüm araçları** (`scripts/run_eval.py --retrieval-only`, `--repeat N --ids …`; `scripts/eval_lib.py`
  `build_target_index`/`target_pages`/`summarize_consistency`): hedef (belge, sayfa) çiftleri `manifest.json`
  `key_facts_used` literal'inin sayfa metninde aranmasıyla LLM'siz türetiliyor; tutarlılık ölçümü her tekrarı
  kendi `audit_log` satırıyla eşleyip "hedef prompt'taydı ama model reddetti"yi "retrieval kaçırdı"dan ayırıyor.
- **`audit_log.chunks_retrieved`** (migration `0007`, SORU 1): prompt'a giren her chunk'ın (belge, sayfa, skor)'u.
- **FTS düzeltmeleri:** `app/services/search_glossary.py` alan sözlüğü (Türkçe kök → İngilizce belge terimi ve
  tersi, `build_search_query` OR'una eklenir; SORU 3), `search_fts`/`search_vector`'e deterministik eşitlik bozucu
  `(rank DESC, document_id, chunk_index)`, `retrieval_top_k` 20 → 40 (SORU 2), `retrieve()`'e per-leg zaman ve
  sıralama "explain" logu.
- **Prompt (SORU 4'ün koşulu tetiklendi — model kararlılığı %0):** kural 5'e "tadil yalnızca kendi yazdığı
  maddeleri değiştirir; sorulan değer GÜNCEL belgede geçmiyorsa zincirde önceki belgedeki değer geçerlidir" eki,
  kural 2'ye "değer kaynakların herhangi birinde açıkça yazıyorsa kaynaklar yeterlidir" eki. `make prompt-doc`.
  Canlı regresyon testi: `tests/live/test_ledger_live.py::test_value_stated_only_in_a_superseded_chain_member_is_still_answered`.
- **`ANK-ISO-002`** yol düzeltmesi (`project.timeline.licence.date` → `project.name`) + `eval_lib`'de `.name` yolu
  literal kuralı; `make validate-ledger` 0 hata.

## 3. Ölçüm: ne bulundu, ne düzeldi

### 3.1 Planın T1 varsayımı yanlıştı — retrieval değil, prompt kuralı
Plan, "aynı soru bazen cevap bazen red" bulgusunu Postgres eşitlik sıralamasına bağlamıştı. **Baseline tutarlılık
ölçümü bunu çürüttü:** 14 soru × 3 tekrarda retrieval kararlılığı **8/8 (%100)**, hedef sayfa 18 tekrarın 18'inde
prompt'taydı — ve model **18'inde de** reddetti (model kararlılığı **0/18**). Eşitlik bozucu yine de doğru (aynı
plan/heap'te sıra sabit görünse de garanti değildi) ama kök neden o değildi.

Kök neden, `chunks_retrieved` + belge metni karşılaştırmasıyla bulundu: **Facility Agreement Amendment 02 (GÜNCEL,
executed) hiçbir rakamı yeniden yazmıyor** — toplam kredi, DSCR, vade, marj hepsi *superseded* halkalarda
(Facility Agreement s.4/s.7, Amendment 01 s.4). Kural 5 "soruda zaman belirtilmemişse GÜNCEL belgeyi esas al"
dediği için model güncel belgede değeri bulamayıp reddediyordu — tutarlı biçimde, her seferinde. Bu, TEMPORAL
TRUTH kuralının prompt'ta eksik kalan yarısı: tadil yalnızca yazdığını değiştirir, değiştirmediği madde önceki
belgede geçerli kalır.

### 3.2 Düzeltme sonrası tutarlılık (aynı 14 soru × 3)
| Ölçü | Önce | Sonra |
|---|---|---|
| Retrieval kararlılığı | 8/8 | 8/8 |
| Model kararlılığı (hedef prompt'tayken cevap) | **0/18 (%0)** | **15/24 (%62,5)** |
| Uçtan uca (beklenen değer cevapta) | 0/27 | 15/27 (%55,6) |

Sonrasında **3/3 doğru** olanlar: `ANK-DEV-004` (ilk kapasite — sözlük+top_k ile hedef sayfa artık prompt'ta),
`ANK-FIN-002` (toplam kredi), `ANK-FIN-005` (marj), `ANK-FIN-006` (güncel DSCR), `ANK-FIN-013` (vade ilk/şimdi),
`ANK-FIN-009` (amendment sayısı). Hâlâ 3/3 reddedilenler ve **neden** (her biri belge metniyle doğrulandı — kod
değil, içerik):

| Soru | Reddetme nedeni (belge metni) | Sınıf |
|---|---|---|
| `ANK-FIN-003/004` yerli banka / ECA kredisi | Facility Agreement s.4: "specific allocations for 30,000,000 EUR and 20,400,000 EUR" — **hangisinin yerli, hangisinin ECA olduğu yazmıyor**; model doğru olarak reddediyor | Prose içerik boşluğu (Phase 3.1) |
| `ANK-FIN-007` ilk DSCR | s.7: "financial ratios that satisfy the minimum threshold set for 1.25x"; Draft s.4: "financial ratio known as 1.25x" — **"DSCR"/"debt service coverage" hiç geçmiyor** (Amendment 01'de geçiyor, o yüzden güncel DSCR cevaplanıyor) | Prose içerik boşluğu |
| `ANK-FIN-001`, `ANK-ISO-003` financial close tarihi | Hiçbir belgede basılı değil (`15.11.2021`/`November 15, 2021` 86 chunk'ın hiçbirinde yok) | Soru↔içerik uyumsuzluğu |
| `ANK-EPC-004` COD erteleme sebebi | "grid connection"/"deferral" hiçbir belgede yok | Prose içerik boşluğu |
| `ANK-FIN-012` DSCR ne zaman/hangi belgeyle değişti | Amendment 01 s.4 değişikliği yazıyor, tarih yalnızca kaynak **başlığında** (`Tarih: 15.03.2025`); model başlık alanını olgu saymıyor | Prompt (küçük, sonraki faz — §7) |
| `IZM-DEV-005/006` lisans alındı mı / inşaata başlandı mı | Negatif olgu; belgeler "henüz yok" demiyor, çıkarım gerekiyor (kural 1 yasaklıyor); 1/3 tekrarda ÇED yazısından "bekleyen adımlar" diye cevapladı | Veri seti beklentisi ↔ NO OPINION kuralı |

### 3.3 Retrieval recall (LLM'siz, `--retrieval-only`)
20/43 soru için hedef sayfa türetilebildi (diğerleri liste/`DOC-*`/negatif olgu ya da basılmayan değer).
Mevcut kod, top_k=20: **18/20** (kaçanlar: `ANK-DEV-004` ilk kapasite, `ANK-FIN-007` ilk DSCR). Sözlük + eşitlik
bozucu, top_k=20: **20/20**. top_k=40: **20/20**. Üç ardışık koşuda sonuç birebir aynı (eşitlik bozucu öncesi de
aynıydı — bkz. 3.1).

## 4. Kabul eval'i ve model karşılaştırması
### 4.1 Kabul eval'i — `make eval` (gemini-3.5-flash-lite, `EMBEDDINGS_ENABLED=false`, top_k=40, yeni prompt)
`assets/phase_3_2b/eval_after.{md,json}` (canlı koşu 07:11–07:21; `ANK-FIN-013` için kaynak-adı kuralı düzeltmesi —
"Facility Agreement" hem bir belgenin adı hem tip — sonradan `audit_log` kayıtlarından LLM'siz yeniden puanlandı, tek
değişen o soru).

| Kategori | Phase 4.1 | Phase 3.2b | Eşik |
|---|---|---|---|
| authorization | %100 (3/3) | **%100 (3/3)** | %100 ✅ |
| hallucination | %100 (4/4) | **%100 (4/4)** | %100 ✅ |
| isolation | %50 (2/4) | **%75 (3/4)** | %100 ❌ |
| document | %52,2 (12/23) | **%69,6 (16/23)** | %80 ❌ |
| temporal | %33,3 (3/9) | **%66,7 (6/9)** | %80 ❌ |

Yasak kaynak/proje karışması: **0/43** (Phase 4.1'de de 0). Kalan 11 başarısızlık: `ANK-FIN-001/003/004/007`,
`ANK-EPC-004`, `ANK-ISO-003` (belge içeriğinde yok/etiketsiz — §3.2), `ANK-FIN-012` (başlık tarihi — §3.2),
`IZM-DEV-005/006` (negatif olgu ↔ NO OPINION — §3.2), `IZM-DEV-007` (doğru cevap, ikinci kaynağı göstermedi),
`ANK-DEV-001` (development başlangıç tarihi hiçbir belgede yok; model lisans tarihini yazdı — 4.1'de de aynı).
**Projeksiyon:** §8'deki 5 cümlelik prose yaması sonrası içerik-boşluğu soruları geçerse document 22/23 (%95,7),
temporal 8/9 (%88,9), isolation 4/4 — eşiklerin hepsi geçilir. Bu yüzden karar Naci'ye bırakıldı (PHASES.md notu).

### 4.2 Model karşılaştırması
`make eval MODEL=gemini-3.5-flash` (`assets/phase_3_2b/eval_after_gemini-3.5-flash_partial.md`): 16 soru denendi,
11 puanlandı, 5 istek hatası (503 "high demand" + 429 kota, `audit_log.error`); 5 ardışık hatada güvenli durdurma
`ANK-EPC-002`'de tetiklendi — Phase 4.1'deki davranışın aynısı, bu hesapta `gemini-3.5-flash` kotası bir eval'e
yetmiyor. Puanlananlar flash-lite ile **aynı** desen: `ANK-FIN-002/005/006` geçti (prompt düzeltmesinin modelden
bağımsız işlediğini gösterir), `ANK-FIN-001/003/004` aynı içerik boşluklarıyla reddedildi; temporal 3/3, document 4/8.
Tek fark `ANK-DEV-001`: flash "bilgi bulamadım" dedi (doğru — o tarih hiçbir belgede yok), flash-lite lisans tarihini
yazdı. Sonuç: `.env` varsayılanı (`gemini-3.5-flash-lite`) kalıyor; karşılaştırma tamamlanmış bir koşu değil, not
olarak kaydedildi (plan §6 adım 4 — "429'a takılırsa kısmi rapor").

## 5. Embedding teşhisi (plan §4)
`make up-full` → `embed` 45 sn'de sağlıklı; tek soru embed gecikmesi **54 ms** (probe boyunca 40–190 ms, hiç
fallback yok) — Phase 4.1 probe'undaki 19–28 sn'lik istekler embed değil **LLM** süresiymiş (hipotez 1 elendi).
15 soru `--retrieval-only` (embedding açık, top_k=40): recall **8/8** ölçülebilir soruda; `retrieval explain` logu her
soruda vektör legini 38–40, FTS legini 16–34 chunk'la gösterdi ve fused listeye 6–22 **yalnızca-vektör** chunk girdi.
Yani bu korpusta (86 chunk) top_k=40 ile listeler doymuyor, RRF eleme sorunu (plan T6) fiilen oluşmuyor — ama Phase 4.1'in
top_k=20'sinde FTS listesi 20'ye doluyken **oluşuyordu** (hipotez 2 matematiksel olarak doğrulandı: `1/61 < 2/80`).
Düzeltme: `retrieve()` her legi `2×top_k` derinlikte çekip füzyondan sonra kesiyor (korpus büyüyünce, Phase 5.1,
aynı tuzağa düşmemek için). Sonuç: hibrit, sözlüklü FTS'e göre bu soru setinde **ölçülebilir ek kazanç sağlamıyor**
(ikisi de 20/20); referans konfigürasyon `EMBEDDINGS_ENABLED=false` kalıyor (ADR-007 notu). `embed` kapatıldı, `.env`
geri alındı, backend yeniden oluşturuldu.

## 6. Testler
- Backend: 275 geçti, 6 atlandı (canlı LLM), 0 kırmızı; ocr-worker 9. Yeni: `test_search_glossary.py` (6),
  `test_eval_lib.py` (+4: hedef sayfa indeksi, expected-text fallback, `.name` literal, tutarlılık özeti),
  `test_retrieval.py` (+1: eşit skorlarda deterministik sıra), `test_migrations.py` (`0007`, `chunks_retrieved`).
- `make lint` temiz (ruff+mypy, eslint+tsc, ledger/document validator, prompt dokümanı eşitliği).
- `make test-llm`: 6 canlı test — ilk koşuda 5 geçti, 1 kaldı (`test_why_question_without_stated_reason_returns_fixed_text`:
  model sabit cümleyi "sebebi belgelerde belirtilmemiş" diye kelime sırası değişmiş yazdı); kural 6'ya "kelimesi
  kelimesine" eklenince tekrar koşuda geçti (`belgelerde sebep belirtilmemiş [K1].`). Yeni test
  `test_value_stated_only_in_a_superseded_chain_member_is_still_answered` ilk koşuda geçti (`50.400.000 EUR [K7]`).

## 7. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Kural 5 de değiştirildi (plan yalnızca kural 2'yi öngörmüştü) | Ölçüm kök nedeni kural 5'te gösterdi (3.1); kural 2 tek başına "GÜNCEL belgeyi esas al" emrini kaldırmıyordu | Tadil zincirinde değişmeyen maddeler artık önceki halkadan, kaynak gösterilerek cevaplanıyor |
| Hedef sayfa türetimine ikinci kaynak: beklenen değerin yazımı `required_sources` belgelerinde aranıyor | `key_facts` dışında basılan değerler için (kapsama artmadı — basılmayan değerler zaten yok — ama mekanizma doğru) | 20/43 ölçülebilir kaldı; nedenleri 3.2'de |
| Prose içerik boşlukları **bu fazda düzeltilmedi** | Plan kapsamı: kod/prompt; prose değişikliği `make prose` (LLM) + yeniden üretim + reseed + ledger onay disiplini ister | §8'de Phase 5.1 için liste |
| Kural 6'ya "kelimesi kelimesine" eklendi — kabul eval'i (§4.1) bu ekten **önce** koşuldu | Canlı test, sabit cümlenin kelime sırası değişmiş halini yakaladı; ek yalnızca "neden?" sorularının sabit cümlesini etkiler, golden setteki tek sebep sorusu (`ANK-EPC-004`) içerik boşluğundan zaten geçmiyor | Eval yeniden koşulmadı (bütçe); etkisi canlı testle sınırlı doğrulandı |
| Sözlükte önek eşleşme, Türkçe morfoloji kütüphanesi yok | Küçük, öngörülebilir; "finansmanında"→"finansman" yeterli | `cod`→"code" gibi yanlış pozitifler mümkün ama yalnızca fazladan OR terimi ekler, zarar vermez |

## 8. Riskler / sonraki phase için notlar
- **Phase 5.1 (tam dataset) için prose düzeltme listesi:** Facility Agreement s.4'te yerli/ECA etiketleri; s.7 ve
  Draft s.4'te "DSCR (debt service coverage ratio)" ibaresi; financial close tarihi bir belgede (örn. Board
  Resolution veya Amendment 01 giriş) basılmalı; COD erteleme sebebi Provisional Acceptance/EPC change order'da
  yazmalı. Bunlar düzelince `ANK-FIN-001/003/004/007`, `ANK-EPC-004`, `ANK-ISO-003` otomatik geçer.
- `ANK-FIN-012` için küçük prompt eki (başlıktaki Belge/Tarih/Yürürlük alanları da olgudur) — bu fazda kabul
  eval'ini bozmamak için eklenmedi; `make test-llm` ile ayrı doğrulanmalı.
- `IZM-DEV-005/006` gibi "henüz olmadı mı?" soruları NO OPINION kuralıyla çelişiyor; ya soru seti "bilgi yok"
  beklemeli ya da belgeler açıkça "lisans henüz alınmamıştır" demeli — Naci kararı.
- Sözlük (`search_glossary.py`) alan sözlüğüdür; yeni belge türleri geldikçe (Phase 5.1) gerçek belge terimlerine
  göre genişletilmeli, soru setine göre değil.

## 9. Doğruladığım üçüncü taraf davranışları
- Postgres `ORDER BY … LIMIT` eşit skorlarda sıra garantisi vermez (SQL standardı); aynı plan/heap'te üç ardışık koşuda
  aynı sırayı verdi ama `(document_id, chunk_index)` eşitlik bozucu eklenmeden tekrarlanabilirlik varsayılamaz.
- `websearch_to_tsquery`: tırnaklı çok kelimeli terim (`"provisional acceptance"`) OR listesinde phrase olarak
  çalışıyor; `simple` config İngilizce kelimeleri kök almadan eşliyor, bu yüzden sözlükte `financing/financial/
  finance` gibi biçimler ayrı ayrı yazıldı.

## 10. Kaynak kullanımı
- LLM çağrısı: tutarlılık 42 + 42, kabul eval'i 43, model karşılaştırması 16 (+ retry'lar), canlı testler 6 — flash-lite toplamı ~135, bütçe (~170) içinde; 429 kotasına yalnızca `gemini-3.5-flash` takıldı (flash-lite'ta sıfır 429/503).
- `embed` servisi yalnızca §5 teşhisi için açıldı ve kapatıldı; referans konfigürasyon `EMBEDDINGS_ENABLED=false`.
