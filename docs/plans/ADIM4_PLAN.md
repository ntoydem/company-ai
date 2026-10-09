# Adım 4 — Proje ekseni belirsizlik tespiti + projesiz soruda proje çıkarımı (uygulama planı)

**Tarih:** 09.10.2026 · **Durum:** plan **onaylı** (Naci 09.10.2026, SORU 1–5 cevaplandı, §5); uygulama bu dalda · **Dayanak:** `URUN1_KARARLAR_VE_SIRA.md` §3.2 Adım 4, §4 ("gerçek belirsizlik tespiti — dürüst yaklaşım"); `PROJESIZ_SORU_PLAN.md` §3 Seçenek B + §4 SORU 1–2 cevapları (09.10.2026) · **Dal:** `feat/adim4-proje-ekseni` (`feat/adim2-ekf` üzerinden) · **Bağımlılık:** Adım 2 (Ek-F, kod `feat/adim2-ekf`'te) · **Kapsam dışı:** sürüm ekseni (ikinci tur), belge ekseni ("hangi belge?" — F-4 (2) linkli liste yolu zaten var), Seçenek A (G3 tanımı — Tansu T-1 bekliyor), Seçenek C (model karar eşiği — ayrı round, Adım 3'ün önkoşulu) · **Ölçüm:** retrieval-only, 0 LLM çağrısı; canlı Gemini çağrısı yok.

## 1. Mekanizma — tek sinyal (proje dağılımı), iki eşik, üç çıkış

Hem V3'ün orijinal tasarımı (disambiguate) hem Seçenek B'nin genişlemesi (dominant) **aynı girdiden** çalışır: adayların (zero-chunk → metadata eşleşmeleri; parça varsa → `specific_matched_terms` ile vouch edilen parçalar) proje koduna göre dağılımı.

```
project_distribution(adaylar) → {ANK_RES: 6, IZM_RES: 1, None: 0}  (örnek: ANK-NEG-004 şekli)
```

| Durum | Koşul | Çıkış | Örnek |
|---|---|---|---|
| **Adlandırılmış** | soru metni **bir** projeyi adlandırıyor (`named_project_codes`, zaten kod — ADR-030) | mevcut davranış: o projeye daralt, "varsayıldı" cümlesi **yok** (kullanıcı zaten söyledi) | GEN-HAL-001 |
| **Disambiguate** | adlandırılmamış ∧ dağılım **yakın eşit** (ikinci grubun payı ≥ `DISAMBIG_SPREAD` × birincinin) ∧ sohbet bağlamında (`previous_question`) proje kelimesi yok | **LLM çağrılmadan** (ADR-021 tarzı, chunks olsa da): `assist.kind="disambiguate"`, `assist.axis="project"`, soru = "Hangi projeyi kastediyorsunuz: {A} mi, {B} mi?" (proje adları kapıdan, `allowed` içinden), **liste yok** | DSC-007 şekli — ama DSC-007 bugün Ü-3'ün "listele" yolunda kalıyor; disambiguate yalnız **dağılım gerçekten yakınsa** tetiklenir (bkz. §1.2) |
| **Dominant** | adlandırılmamış ∧ dağılım **net** bir projede toplanmış (o projenin payı ≥ `DOMINANT_SHARE`) | O projeye daralt (Ek-F F-3/F-5 listesi); **sessiz tahmin yasak** (Naci 09.10, SORU 1) — cevapsız kalırsa F-5 metnine "**{Proje}** projesine ait olduğu varsayıldı." cümlesi eklenir (rakam/tarih yok → G1'i bozmaz) | ANK-NEG-004 (6 Ankara / 1 İzmir) |
| **Yok** | ne adlandırılmış ne disambiguate ne dominant | **bugünkü Adım 2 davranışı** — iki proje de gösterilir, proje başlıklı | GEN-DSC-007 (İzmir 4 + Ankara 3, hiçbiri net çoğunluk değil) |

İki eşik de `Settings` üzerinden env ile ayarlanır, **ölçümde sabit tutulur**, değerleri rapora yazılır (Naci SORU 2):

| Parametre | Env | Başlangıç önerisi | Anlamı |
|---|---|---|---|
| `DISAMBIG_SPREAD` | `PROJECT_AXIS_DISAMBIG_SPREAD` | `0.5` (V3'ün eski değeri, §4'te zaten kullanılmıştı) | ikinci grubun payı ≥ bu × birincinin payı → yakın eşit |
| `DOMINANT_SHARE` | `PROJECT_AXIS_DOMINANT_SHARE` | `0.75` | bir projenin payı ≥ bu → net çoğunluk (ANK-NEG-004: 6/7 ≈ 0,857 ≥ 0,75 ✓) |

**Disambiguate ile Dominant arasındaki boşluk** (ör. ikinci grup payı %30–%50 arası) bilerek **"Yok"** sonucuna düşer — ne tahmin ne soru; bugünkü davranış. Bu, §2.3'teki aralık boşluğunu açıkça kapatıyor (ikisi arasında sessizce bir karar verilmiyor).

### 1.1 Disambiguate'in LLM'den önce çalışması

Adlandırılmış/dominant durumlar LLM çağrısına **dokunmaz** (model normal çalışır; yalnız cevapsız kalırsa listeleme değişir). **Disambiguate** farklı: tetiklenirse **LLM hiç çağrılmaz** — `ask.py::answer_question`, parçalar çekildikten **hemen sonra, prompt kurulmadan önce** kontrol edilir (zero-chunk yolunda zaten LLM çağrılmıyordu — ADR-021; bu, chunks varken de aynı garantiyi getiriyor, V3'ün orijinal tasarımıyla aynı).

### 1.2 Yanlış alarm riski — §2.3'teki boşluktan ayrı bir risk

V3'ün eski ölçümünde (`BELIRSIZLIK_REPORT.md`) disambiguate'in kaçırdığı sorular (AMB-02/03/05) **düşük skorlu ama** dağılımca iki projeye yakın yayılmıştı; eski eşik "ikinci ≥ 0,5×birinci **skor**" idi (skor, pay değil) — bu yüzden kaçırıyordu. Bu planda ölçüt **sayı/pay**, skor değil (zaten §4'te kararlaştırıldı) — bu riski kapatması beklenir ama ölçümle doğrulanacak (§3).

## 2. Dosya / fonksiyon değişiklikleri

| # | Değişiklik | Dosya |
|---|---|---|
| 2.1 | `project_distribution(session, allowed, terms, chunks) -> dict[str \| None, int]` — zero-chunk'ta `available_from_metadata`'nın tüm adayları (limit yüksek), parça varsa `specific_matched_terms` ile vouch edilen belgelerin projeleri. Aynı veri, Ek-F'nin zaten hesapladığı kümeler — yeniden retrieval yok. | `services/assist.py` |
| 2.2 | `ProjectAxisDecision` (dataclass: `kind: Literal["named","disambiguate","dominant","none"]`, `project_code: str \| None`); `classify_project_axis(distribution, named, *, disambig_spread, dominant_share) -> ProjectAxisDecision` — saf fonksiyon, DB'siz, birim test edilebilir. | `services/assist.py` |
| 2.3 | `Settings.project_axis_disambig_spread`, `Settings.project_axis_dominant_share` (env, varsayılan §1'deki değerler) | `core/config.py`, `infra/.env.example` |
| 2.4 | `ask.py::answer_question`: parçalar çekildikten sonra (chunks boş ya da dolu, ikisinde de) `classify_project_axis` çağrılır; `disambiguate` ise LLM atlanır, sabit `Assist(kind="disambiguate", axis="project", question=template, available=())` döner. `dominant` ise sonucu `build_zero_chunk_assist`/`build_insufficient_assist`'e `inferred_project=` olarak geçer (adlandırılmış projeyle **aynı** daraltma mekanizmasını kullanır — `named_project` parametresi genişler: `named_project: str \| None` artık "adlandırılmış **veya** çıkarılmış" anlamına gelir, ama **hangisi olduğu** `Assist`'te ayrı tutulur ki F-5 doğru cümleyi yazsın) | `services/ask.py`, `services/assist.py` |
| 2.5 | `render_no_data`: `assist.inferred` (bool) alanı `True` ise listeden önce "**{Proje}** projesine ait olduğu varsayıldı." satırı eklenir; adlandırılmışsa (zaten kullanıcı söylediği için) eklenmez. `disambiguate` kalıbı ayrı, sabit: yalnız soru satırı, liste yok, "İsterseniz açayım" yok. | `services/assist.py` |
| 2.6 | `AssistBlock.kind` Literal'i `"disambiguate"` değeriyle genişler; yeni `AssistBlock.axis: Literal["project"] \| None` alanı (bayrak kapalıyken `None`) | `schemas/ask.py` |
| 2.7 | Eval: `ledger_schema.Question.expect_assist` Literal'i `"disambiguate"` değerini kabul eder; `assist_check` bu türü tanır; G1 kontrolü disambiguate sorusunda da rakam/tarih/para yok şartını aynen uygular (zaten genel kural) | `seed_data/generator/ledger_schema.py`, `scripts/eval_lib.py` |

## 3. Ölçüm — **retrieval-only, 0 LLM çağrısı**

Adım 4'ün ölçütü, modelin ne yapacağını değil, **tespit + daraltma kodunun** doğru çalıştığını ölçer — "model cevaplar mı" sorusu bilerek Seçenek C'ye bırakılmıştır (Naci SORU 4, 09.10.2026). Bu yüzden ölçüm canlı `/api/ask` çağırmaz: `scripts/dry_run_project_axis.py` (yeni, Ek-F'nin kuru koşu script'iyle aynı desen) her soru için gerçek retrieval'ı in-process çalıştırır (0 LLM), `classify_project_axis`'i çağırır ve `dominant`/`none` durumunda **model cevapsız kaldığını varsayarak** (`build_insufficient_assist`'i zorla çağırır) F-5 metnini üretir — canlı modelin o soruyu gerçekten cevaplayıp cevaplamayacağına bakılmaz.

| Küme | Sorular | Beklenen | Hedef |
|---|---|---|---|
| **Dev AMB (5)** | GEN-AMB-001…005 (hepsi projesiz, belge-sınıfı kelimesi, proje kelimesi yok) | `disambiguate` | **≥ 4/5** |
| **Dev NEG (9)** | ANK-NEG-001/002 (proje **adlandırılmış** → `named`, tetiklenmemeli), ANK-NEG-003/004, CO-NEG-005 (projesiz, tek-proje-beklenen → `dominant`, doğru proje), GEN-AMB-003-F (projesiz, tek zincir → `none`, hiç tetiklenmemeli), GEN-CMP-001/002/003 (iki proje **adlandırılmış** → `named`/Ü-3 çoklu-proje yolu, `disambiguate` **olmamalı**) | yanlış alarm (gereksiz `disambiguate`) **0/9** | **0/9** |
| **Held-out (10, yeni)** | Naci/danışman yazar; 5 AMB + 5 NEG; geliştirici AI ölçüm gününe kadar görmez (05.10 kuralı, `URUN1_KARARLAR_VE_SIRA.md` §2) | AMB ≥ 3/5, NEG yanlış alarm ≤ 1/5 | §4.5 eski hedefle aynı |

**ANK-NEG-004 özel kontrolü:** dry run'da `dominant` + `project_code="ANK_RES"` çıkmalı, liste yalnız Ankara belgeleri + "varsayıldı" cümlesi, İzmir'in belgesi hiç görünmemeli (G3). Bu, bu planın **somut kapanış kriteri**dir (`PROJESIZ_SORU_PLAN.md`'nin bıraktığı açık nokta).

**Durma kuralı (değişmez, eski kural):** NEG yanlış alarmı > 0 (dev) ya da held-out'ta > 1 → eşik **oynatılmaz**, tanım/sınıf-listesi gözden geçirilir, rapor yazılır, durulur.

**09.10.2026 güncellemesi (ilk ölçüm sonrası, Naci kararı):** dev AMB'nin ilk 5 sorusu (GEN-AMB-001…005) ilk ölçümde 3/5 çıktı (ADIM4_REPORT.md §3.1); GEN-AMB-001/002'nin bu korpusta **belge varlığı** bakımından gerçekten belirsiz olmadığı kanıtlandı (§4.2) — ama **dev settten çıkarılmadı**, sayım ve kriter değişmedi. Belge-varlığı kriteriyle (iki projede de aynı belge türünden ≥ 2'şer belge) **tek** yeni soru eklendi: `GEN-AMB-006`. Sonuç iki ayrı sayı olarak raporlanır (orijinal 5 ve yeni soru), hedef karşılandı iddiası yapılmaz.

**Held-out ve eşik kilidi — ertelendi (09.10.2026, Naci kararı):** held-out ölçümü ve nihai eşik kilidi **Adım 5'ten (veri kütüphanesi) sonrasına** ertelendi. Gerekçe: korpus Adım 5'te kökten değişecek (Ç-9 B yeniden adlandırma + yeni belgeler); şimdiki `0.5`/`0.75` eşikleri **yeni korpusta yeniden doğrulanacak** — bugünkü dev ölçümü (3/5 + 1 yeni soru) bir **ara doğrulama**dır, nihai kilit değildir. §3.2'deki sıra: Adım 4 (bu adım, kod + dev ölçüm) → Adım 5 (kütüphane) → Adım 4′ (yeniden ölçüm, yeni korpus, held-out burada istenir) → eşik kilidi.

## 4. Testler (deterministik, `make test`)

- `test_project_axis.py` (yeni): `classify_project_axis` dört çıkış (named önceliği, disambiguate — eşit/yakın dağılım, dominant — net çoğunluk, none — aradaki boşluk); eşik env'den okunuyor (settings monkeypatch); `project_distribution` zero-chunk ve chunk'lı yoldan aynı sözlüğü üretiyor.
- `test_assist_ekf.py` ek: ANK-NEG-004 şekli (6 Ankara + 1 İzmir aday, zorla cevapsız) → `dominant`, liste yalnız Ankara, "varsayıldı" cümlesi var, İzmir hiç yok (G3); GEN-AMB-00x şekli (yakın dağılım) → `disambiguate`, `fake_llm.requests == []` (LLM hiç çağrılmadı), liste boş; GEN-CMP şekli (iki proje adlandırılmış) → `disambiguate` **değil**, mevcut çoklu-proje yolu çalışıyor; aradaki boşluk (%30–50) → `none`, bugünkü iki-projeli liste.
- `test_eval_lib.py` ek: `expect_assist="disambiguate"` eşleşmesi; G1 disambiguate sorusunda rakam yok.

## 5. SORU (Naci) — cevaplar 09.10.2026

| # | Karar | Ayrıntı |
|---|---|---|
| 1 | **Aynı bayrak (`EK_F_MODE`)** | Yeni bayrak yok. |
| 2 | `DOMINANT_SHARE=0.75`, `DISAMBIG_SPREAD=0.5` | Eşikler **yalnız dev setinde** ayarlanabilir, sonra **kilitlenir**, değerler rapora yazılır; held-out sonucuna göre eşik **oynatılmaz**. |
| 3 | Held-out **kod bittikten sonra** istenir | Naci/danışman seti ölçüm gününe kadar geliştirici AI'a vermez; geliştirici AI yazmaz. |
| 4 | "Model cevapsız sayarak" retrieval-only kuru koşu **onaylı** | Canlı LLM çağrısı yok. |
| 5 | Yeni dal **`feat/adim4-proje-ekseni`** (`feat/adim2-ekf` üzerinden) | — |

**Ek kurallar (uygulama sırasında geçerli):** proje ekseni **yalnız kodla** tespit edilir; netleştirme sorusunda içerik sıralaması/belge listesi **yok**; sessiz tahmin yok — dominant ise cevap varsayılan projeyi açıkça yazar; aradaki boşluk bugünkü davranışa düşer. Ü-3 ve Ç-6 korunur.
