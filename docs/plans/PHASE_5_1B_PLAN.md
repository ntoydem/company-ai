# Phase 5.1b — Eval eşik ihlalini kapatma: Implementation Plan

## Bağlam

`docs/reports/PHASE_5_1_REPORT.md` §4/§8: 26.09.2026'da koşan tam `make eval` (61 soru, 0 istek hatası)
`document` (%74,2), `mixed` (%66,7), `temporal` (%60,0) eşiklerini geçemedi. 13 başarısız sorudan **4'ü**
Naci'nin Phase 3.2c'de açıkça Phase 5.1 kapsamı dışına ertelediği kalıntılar (`ANK-EPC-004`, `IZM-DEV-005`,
`IZM-DEV-006`, `IZM-DEV-007`) — **bu plan onlara dokunmuyor**. Geri kalan **9** yeni başarısız soru bu planın konusu:
`ANK-DEV-004`, `ANK-FIN-005`, `ANK-FIN-010`, `ANK-OPS-001`, `IZM-DEV-004`, `IZM-DEV-008`, `ANK-MIX-001`,
`ANK-EPC-005`, `IZM-DEV-011`.

PHASES.md kuralı ("Kırmızı test varken ilerleme") gereği Phase 5.2'ye geçmeden önce bu ele alınmalı; sıra
Naci'nin verdiği önceliğe göre: (1) en ucuz seçenek (`RETRIEVAL_TOP_K`) → (2) ölç (`--repeat 3`, 3.2b'nin T1
dersi: önce ölç, sonra düzelt) → (3) yetersizse router vakalarını (`ANK-FIN-010`) ayrı incele.

### Tespitler (T)

- **T1 — Haystack 3,6× büyüdü, `top_k` sabit kaldı.** `retrieval_top_k=40` Phase 3.2b'de 86 chunk'lık bir
  korpus için ayarlandı (ADR: "40 chunk ≈ 10k token"). Şu an `document_chunks` **310** satır (Phase 5.1: 15→70
  belge). `build_user_prompt()` retrieve()'in döndürdüğü **her** chunk'ı tam sayfa metni olarak prompt'a
  ekliyor — başka bir filtre/kırpma yok (`answer_prompt.py::format_source`). `EMBEDDINGS_ENABLED=false`
  olduğundan (`retrieval.py`) `leg_k = top_k` — yani `top_k`'yi artırmak doğrudan FTS'in kaç satır döndürdüğünü
  belirliyor, ek bir "derinlik" katsayısı yok.
- **T2 — `top_k` artırmak günlük istek kotasını ETKİLEMİYOR.** Kesinti (§9, PHASE_5_1_REPORT) `GenerateRequestsPerDayPerProjectPerModel-FreeTier` — istek SAYISI bazlı, token hacmi bazlı değil. `top_k` artışı yalnızca istek başına prompt token'ını büyütür, günlük 500 istek hakkını değil — yani bu fazın ölçüm/deneme bütçesi bugünkü kesintiden bağımsız.
- **T3 — Gerçek token verisi elimizde.** 26.09.2026'nın tam koşusundan (`results.json`): `tokens_in` ortalama
  **10.638**, `document` kategorisinde ortalama **11.629**, maksimum **13.250** (top_k=40'ta). Doğrusal
  ölçeklenirse (40→60, ×1,5) ortalama ~**16.000-17.400**, maksimum ~**19.900** — Gemini flash-lite'ın bağlam
  penceresinin (milyon token mertebesi) çok altında, önemsiz.
- **T4 — 9 sorunun 2'si retrieval değil, model/router aşamasında başarısız.** `--retrieval-only` (LLM'siz,
  25.09.2026) bu 9 sorudan **7'sinin** hedef sayfasını zaten buluyordu (yalnızca `ANK-OPS-001` retrieval-only'de
  de kaçırıyordu). Tam eval'de `ANK-EPC-005`/`IZM-DEV-011` (retrieval-only'de ✅) modelin "bulamadım" demesiyle
  başarısız oldu — **retrieval sorunu değil, cevaplama adımı**. `top_k` artışı bu ikisini muhtemelen düzeltmez
  (kaynak zaten prompt'taydı); bunlar `--repeat`in asıl hedefi (gerçek bir model-güvenilirliği sorunu mu, yoksa
  tek-koşu değişkenliği mi).
- **T5 — `ANK-FIN-010` retrieval değil, router sınıflandırma sorunu.** Soru: *"Ankara RES'in son covenant testi
  sonucu nedir?"* — router bunu `DATA_QUERY`'e yönlendirdi, Excel motoru `Covenant_Report.xlsx`'ten "pass"
  hesapladı (doğru rakam, **yanlış kaynak türü** — golden set PDF `Covenant Compliance Report Q2 2026`
  bekliyor). Phase 4.3'ün "DATA miss → belge hattına düş" güvenlik ağı (`ask_router.py:134`) burada **devreye
  girmiyor** çünkü DATA dalı başarıyla cevap verdi (`data.answered=True`) — bu, "DATA yanlışlıkla ama güvenle
  cevapladı" durumu için hiç tasarlanmamış farklı bir vaka. `ANK-DAT-001`/`ANK-MIX-001` de aynı "covenant/DSCR
  hem belgede hem Excel'de var" belirsizliğine değiyor — `ANK-FIN-010`'un tekil bir bug'ı değil, router
  promptunun "DOCUMENT vs DATA" sınırının bu soru ailesinde zaten gevşek olduğunun bir işareti (Phase 4.3'ten
  miras, Phase 5.1 yeni covenant-adjacent içerikle (`DOC-ANK-FIN-015/016`) yoğunluğu artırmış olabilir).
- **T6 — Araçlar zaten var, kod değişikliği gerekmeyebilir.** `make eval EVAL_ARGS="--retrieval-only"` (T4/T1
  için), `make eval EVAL_ARGS="--repeat 3 --ids <id,id,...>"` (T4 için, `RepeatOutcome`/`ConsistencySummary`
  retrieval-tutarlılığı ile model-tutarlılığını ayrı raporluyor — tam olarak 3.2b'nin T1 dersi: "Postgres tie
  ordering" hipotezi yanlış çıkmıştı, gerçek neden prompt kuralıydı; burada da önce ölç, sonra düzelt).
  `RETRIEVAL_TOP_K` `.env`'e eklenip `make eval` çalıştırılarak kalıcı bir kod değişikliği yapılmadan denenebilir.

## Uygulama sırası (Naci'nin verdiği sıra)

### Adım 1 — `RETRIEVAL_TOP_K` 40→60 dene (en ucuz)
1. `.env`'e `RETRIEVAL_TOP_K=60` ekle (geçici deneme; `infra/.env.example`/`config.py`'nin varsayılanı **henüz**
   değiştirilmiyor — yalnızca deneme sonrası kalıcı yapılacak, SORU 1'e bağlı).
   `docker compose up -d --wait --build backend` (env değişikliğini backend'e yansıt).
2. `make eval EVAL_ARGS="--retrieval-only"` — **LLM çağırmadan**, top_k=60'ta recall'ı ölç; özellikle 9 sorudan
   `ANK-DEV-004`, `ANK-FIN-005`, `IZM-DEV-004`, `IZM-DEV-008` (T4'te "retrieval-only'de zaten ✅" demediğim
   4 soru + ANK-OPS-001) hedef sayfayı buluyor mu.
3. Sonuç net iyileşme gösteriyorsa (özellikle `ANK-OPS-001` gibi retrieval-only'de de kaçıran sorularda) →
   Adım 2'ye top_k=60 ile geç. İyileşme yoksa top_k=80 ile bir kez daha dene (T3'ün token tahminini güncelleyerek);
   yine yoksa top_k'yi kalıcı artırmaktan vazgeç, doğrudan Adım 3'e geç (T4/T5 zaten retrieval-dışı sorunlar
   olduğunu gösteriyor).

### Adım 2 — `--repeat 3` ile 9 soruyu ölç (gerçek gerileme mi, değişkenlik mi)
1. `make eval EVAL_ARGS="--repeat 3 --ids ANK-DEV-004,ANK-FIN-005,ANK-FIN-010,ANK-OPS-001,IZM-DEV-004,IZM-DEV-008,ANK-MIX-001,ANK-EPC-005,IZM-DEV-011"`
   (Adım 1'de karar verilen `RETRIEVAL_TOP_K` değeriyle) — retrieval-tutarlılık ve model-tutarlılık ayrı ayrı.
2. Yorumlama: `retrieval_stable` düşükse (aynı soru farklı koşularda farklı sayfa getiriyor) → gerçek bir top_k/
   sıralama sorunu, top_k'yi biraz daha artırmak ya da `search_glossary.py`'ye yeni terim eklemek gerekebilir
   (3.2b'nin izlediği yol). `retrieval_stable` yüksek ama `model_answered`/`value_ok` düşükse → **model
   cevaplama davranışı** sorunu (T4'ün `ANK-EPC-005`/`IZM-DEV-011` gözlemiyle uyumlu) — bu, `answer_prompt.py`
   kural 2'nin (kaynak yeterliliği eşiği) yeniden ince ayarını gerektirebilir, ama bu ince ayar riskli (Phase
   3.2/3.2b'de zaten birkaç kez değiştirildi, her değişiklik başka soruları bozma riski taşıyor) — **bu fazda
   yalnızca ölçülüyor, prompt'a dokunulmuyor** (SORU 2).
3. Tek koşuda "başarısız" görünen bir soru 3 tekrarın ≥2'sinde geçerse, bu "tek-koşu değişkenliği" sayılır (eval
   kategori eşiğinin doğası gereği zaten olası — 3.2b'nin `docs/reports/assets/phase_3_2b/consistency_after.md`
   emsali) ve ayrı bir düzeltme gerektirmez; raporda "gözlemlenen ama düzeltilmesi gerekmeyen değişkenlik"
   olarak not edilir.

### Adım 3 — Yetersizse: router vakalarını ayrı incele (`ANK-FIN-010` ailesi)
1. Adım 1-2 `ANK-FIN-010`'u düzeltmezse (T5 zaten bunun retrieval değil router sorunu olduğunu gösteriyor,
   büyük ihtimalle düzeltmeyecek): `services/router.py::ROUTER_SYSTEM_PROMPT`'a "covenant testi SONUCU
   (pass/fail) sözleşme/rapor DİLİYLE soruluyorsa DOCUMENT, DSCR SAYISI hesaplanıyor/karşılaştırılıyorsa DATA"
   ayrımını netleştiren bir kural + örnek eklemeyi değerlendir (Phase 4.3'ün "belgede yazan rakam = DOCUMENT"
   kuralına benzer, ama bu kez "sonuç" (pass/fail) ile "değer" (1,37x) arasındaki fark için).
2. Alternatif (daha az riskli): `ANK-FIN-010`'u `questions.json`'da MIXED'e taşımak — zaten aynı belirsizliği
   taşıyan `ANK-DAT-001`/`ANK-MIX-001` ile tutarlı olur, router promptuna dokunmadan golden set'i gerçekçi
   duruma getirir (SORU 3).
3. Her iki seçenek de küçük, izole bir değişiklik; `test_router.py`/`test_ask_router.py`'ye ilgili birim testi
   eklenir; canlı doğrulama `make test-llm` + hedefli `make eval EVAL_ARGS="--ids ANK-FIN-010,ANK-DAT-001,ANK-MIX-001"`.

## Kabul kriterleri → kanıt

| Kriter | Kanıt |
|---|---|
| `document`/`mixed`/`temporal` ≥%80 (4 bilinen kalıntı hariç tutularak hesaplanmış) | Adım 1-3 sonrası tam `make eval`; kategori tablosu + hangi adımın hangi soruyu düzelttiğinin dökümü |
| Değişiklikler ölçüme dayalı, spekülatif değil | Her adımın kendi `--retrieval-only`/`--repeat` kanıtı raporda |
| 4 bilinen kalıntıya dokunulmadı | `questions.json`'da `ANK-EPC-004`/`IZM-DEV-005/006/007` değişmedi (diff'te görünmemeli) |
| Token/maliyet öngörülebilir | T3'ün tahmini, gerçek Adım 1 sonrası ölçümle karşılaştırılır |

## SORU (Naci cevaplamalı)

1. **`RETRIEVAL_TOP_K` kalıcı olarak 40'tan (60'a veya bulunan değere) mı değişsin** (`config.py`/`.env.example`/
   gerçek `.env`), yoksa bu yalnızca Phase 5.1b'nin tanı aracı olarak mı kalsın (deneme sonrası eski değere
   dönülsün, ayrı bir SORU/karar olarak mı bıraksın)? Önerim: Adım 1 net bir iyileşme gösterirse **kalıcı**
   yap (korpus büyümeye devam edecek — Phase 5.4'e kadar başka içerik eklenmeyecek olsa da mevcut 70 belge için
   bile 40 artık düşük); göstermezse geri al.
2. **Adım 2'de model-cevaplama değişkenliği (`ANK-EPC-005`/`IZM-DEV-011` gibi) çıkarsa `answer_prompt.py` kural
   2'ye dokunulsun mu, yoksa bu fazda yalnızca ölçülüp ayrı bir karar noktası olarak mı bırakılsın?** Önerim:
   **bu fazda dokunma** — kural 2 hassas, önceki fazlarda birkaç kez ince ayar gördü, riskli bir değişikliği dar
   kapsamlı bir fazda yapmak istemiyorum; ölç, raporla, ayrı bir küçük faz öner.
3. **`ANK-FIN-010` için Adım 3'ün iki seçeneği** (router promptuna kural ekle / soruyu MIXED'e taşı) — hangisini
   tercih edersin, yoksa ikisi de değil, soru olduğu gibi (bilinen bir sınır olarak) mı kalsın?

## Kritik dosyalar

- `.env`, `infra/.env.example`, `backend/app/core/config.py` (SORU 1'e bağlı)
- `scripts/run_eval.py`, `scripts/eval_lib.py` (değişiklik beklenmiyor, yalnızca kullanılıyor)
- `backend/app/services/router.py`, `seed_data/evaluation/questions.json` (yalnızca Adım 3 gerekirse, SORU 3'e bağlı)
