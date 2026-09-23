# Phase 2.1 — Truth ledger + validator + golden questions v1: Implementation Plan

> Bu planda **hiçbir demo rakamı, tarihi veya tutarı yoktur** (CLAUDE.md "Demo sabitleri"; SPEC_03 satır 3). Şema, alan listesi, kurallar ve soru *kalıpları* vardır; değerler Naci + enerji finansı ekip arkadaşının onayına kalır (PHASES.md 2.1 "Süreç").

## Bağlam ve tespitler

ADIM 2'nin tek phase'i. Kapsam (`docs/PHASES.md` 2.1): `seed_data/master/{company,ankara_res,izmir_res,fx_rates}.yaml` (SPEC_05 §3), her değer `USER_FACT|AI_ASSUMPTION`; `validate_ledger.py` (kaba kronoloji, finans tutarlılığı, İzmir'de lisans sonrası alanlar boş, para birimleri, isim whitelist); `evaluation/questions.json` v1 (≥ 30 soru, SPEC_05 §9). Adım 3 (belge üretimi) bu ledger onaylanmadan başlamaz (SPEC_05 §2).

Okunanlar: `docs/PHASES.md` (2.1, 3.1, 4.1, 5.1), `docs/SPEC_03_domain_modeli.md` (tamamı), `docs/SPEC_05_synthetic_veri_ve_evaluation.md` (tamamı), `docs/DOMAIN_MODEL.md` §4/§6/§7/§8, `docs/ARCHITECTURE.md` ADR-013, `SPEC_01` satır 51, `SPEC_04` §9, `README_NASIL_KULLANILIR.md` "Ledger onayı için hazırlık", `CLAUDE.md`; kod: `seed_data/t0/{generate.py,upload.sh}`, `backend/tests/{t0_fixtures.py,live/test_t0_live.py}`, `backend/app/services/demo_{users,departments,projects}_seed.py`, `backend/app/core/config.py`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/Dockerfile`, `Makefile`, `.gitignore`.

Planı şekillendiren tespitler:

- **T1 — Şema yalnızca proje dosyası için var.** SPEC_05 §3 `ankara_res.yaml`/`izmir_res.yaml`'ın `meta / project / documents` iskeletini veriyor; `company.yaml` ve `fx_rates.yaml` için hiçbir şema yok (içerik SPEC_03 §9 ve §4'ten çıkarılıyor). Bu plan ikisini tanımlar (§1.3, §1.4).
- **T2 — Etiketin yeri şemada tutarsız.** Bazı alanlar alan-bazlı `tag` taşıyor (`capacity_mw.initial.tag`, timeline olayları), bazıları kayıt-bazlı (`turbines.tag`, `documents[].tag`), bazıları hiç taşımıyor (`tenor_years`, `dscr_covenant`, `spv`, `drawdowns`). Kural "her değer etiketli" olduğu için tek bir mekanizma tanımlanıyor (§2) ve validator bunu zorluyor.
- **T3 — Zorunlu soruların ihtiyaç duyduğu bazı alanlar şemada yok.** "EPC bedeli", "güncel EPC sözleşmesi", "capacity amendment tarihi", construction bitişi (validator kuralı için), debt/equity. Şemaya `construction:` bölümü ve eksik finans alanları ekleniyor (§1.1).
- **T4 — Departman değeri kodla uyuşmuyor.** SPEC_05 örneği `department: finance` / `expected_department: "finance"`; DB slug'ı `finans` (Phase 1.2, `demo_departments_seed.py`). Ledger ve questions.json **DB slug'larını** kullanır; validator slug'ı bilinen listeye karşı doğrular — Phase 3.2 notunun (PHASES.md) ilk yarısı böylece burada kapanır.
- **T5 — `questions.json` yolu çelişiyor.** SPEC_05 §9 ve PHASES `evaluation/questions.json`; SPEC_05 §1, CLAUDE.md ve `.gitignore` (`seed_data/evaluation/results/`) `seed_data/evaluation/`. Karar: `seed_data/evaluation/questions.json` (klasör zaten gitignore'da öngörülmüş).
- **T6 — Facility zinciri 6 halka, Phase 3.1 4 belge üretiyor.** 2.1 kabul kriteri "DRAFT→V01→V02→EXECUTED→AMD01→AMD02 ledger'da"; 3.1 kapsamı "Facility zinciri 4". Envanter 6 halkayı da taşır, her belge `generate_in_phase` alanıyla hangi fazda dosyaya dönüşeceğini söyler (SORU 5).
- **T7 — Kotalar örtüşüyor.** İzmir ≥ 9 + Ankara ≥ 20 + hallucination ≥ 3 + isolation ≥ 3 + authorization ≥ 3 = 38 > 30 → proje kotası `expected_project`'ten, kategori kotası `category`'den sayılır, bir soru ikisine de sayılır (§4.3).
- **T8 — PyYAML yalnızca geçişli bağımlılık.** `uv.lock`'ta uvicorn[standard] üzerinden var; açıkça deklare edilmeli (dev grubu — generator/validator runtime'a girmez, ADR-013). `jsonschema` yok; şema doğrulaması için zaten bağımlı olduğumuz **Pydantic v2** kullanılacak, yeni kütüphane eklenmiyor.
- **T9 — Validator backend container'ında çalışır.** `./seed_data` `/app/seed_data`'ya mount'lu; `docker compose run --rm --no-deps backend python seed_data/generator/validate_ledger.py`. `make lint`'te zaten kod-dışı bir tutarlılık kontrolü var (prompt-doc diff) — validator aynı yere eklenir. mypy `files=["app"]` olduğundan generator mypy'a girmez; ruff `.` taradığı için `seed_data/` ruff'a girer.
- **T10 — İşletme yılı hesabı tanımsız.** "3. işletme yılı `DEMO_TODAY`'e göre" — yıldönümü bazlı sayım seçiliyor (§3.2), takvim yılı değil.
- **T11 — Adım 0'ın geçici T0 değerleri ledger'ı bağlamaz.** `seed_data/t0/` ve `tests/live/test_t0_live.py`'deki değerler "geçici rakam" (PHASES 0.2/0.3); ledger onaylanınca T0 seti Phase 3.1'de kaldırılır. Bu fazda `tests/live/` değişmez.
- **T12 — Whitelist'in tek tanımı SPEC_05 §11'de.** "'A.Ş.' önündeki isimler whitelist'te mi". Aday isimler SPEC_05 §4'teki 7 kurgusal ad; kamu kurumları serbest. Whitelist `company.yaml`'da yaşar (§1.3), validator oradan okur.

---

## 1. `seed_data/master/` — dosya yapısı ve şema

Dört YAML dosyası; hepsi aynı `meta` bloğuyla başlar. Şema `seed_data/generator/ledger_schema.py`'de **Pydantic v2 modelleri** olarak tanımlanır (tek kaynak; validator ve ileride generator/Excel aynı modelleri kullanır; backend import etmez).

### 1.0 Ortak yapı taşları
```yaml
meta:
  schema_version: 1
  demo_today: "<DEMO_TODAY>"        # 4 dosyada da aynı; validator backend DEMO_TODAY ile eşitliğini denetler
  currency_note: "<serbest metin>"
```
| Yapı taşı | Şekil | Not |
|---|---|---|
| **Fact** (etiketli değer) | `{value: <scalar>, tag: USER_FACT\|AI_ASSUMPTION, source_doc: DOC-ID?, note: str?}` | Her "bilgi" bu şekilde yazılır (§2) |
| **Money** | `{value: <number>, currency: EUR\|USD\|TRY, tag:, source_doc?:}` | Para birimi **zorunlu**; kabul kriteri "her tutarda para birimi" |
| **Event** (tarihli olay) | `{date: <ISO date> \| null, doc: DOC-ID \| null, tag:, note?:}` | Timeline girdileri; İzmir'de `date: null` olabilir |
| **Ref** | `DOC-<PRJ>-<DEP>-<NNN>` | Belge kimliği; `<PRJ>` ∈ `ANK\|IZM\|CO`, `<DEP>` ∈ `DEV\|FIN\|EPC\|OPS\|LEG\|ADM` |

### 1.1 `ankara_res.yaml`
```yaml
meta: {...}
project:
  code: ANK_RES                     # DB projects.code ile aynı (Phase 1.2 seed)
  name: Ankara RES
  stage: operation
  spv: {name: Fact, shareholders: [{name: Fact, share_pct: Fact}]}
  capacity_mw: {initial: Fact, current: Fact}          # current.source_doc = lisans tadili belgesi
  turbines: {count: Fact, model_generic: Fact}
  timeline:                          # hepsi Event
    development_start:
    pre_licence:
    licence:
    licence_amendment:               # kapasite artışı (SORU 2: adlandırma)
    financing_signed:
    financial_close:
    epc_signed:
    construction_start:
    construction_end:
    commissioning:
    cod_expected_initial:
    cod_actual:
    operation_start:                 # = cod_actual olabilir; ayrı tutuluyor (validator: ≥ cod_actual)
  finance:
    capex: Money
    equity: Money                    # validator: capex − total_debt tutarlılığı (§3.3)
    total_debt: Money
    local_debt: Money                # validator: local + eca = total
    eca_debt: Money
    lenders: {local_bank: Fact, eca: Fact}             # company.yaml parties'e referans (isim)
    interest: {base: Fact, margin_pct: Fact}
    tenor_years: {initial: Fact, current: Fact, changed_by: DOC-ID}
    grace_months: Fact
    repayment_profile: Fact          # metin (ör. sculpted/annuity/equal — değer onaya tabi)
    dscr_covenant: {initial: Fact, current: Fact, changed_by: DOC-ID}
    drawdowns: [{date:, amount: Money, doc:, tag:}]
    outstanding_debt_as_of_demo_today: Money
    covenant_tests: [{period: "Qn_YYYY", dscr: <number>, result: pass|fail, doc:, tag:}]
    facility_chain: [DOC-ID, ...]     # sıralı: DRAFT, V01, V02, EXECUTED, AMD01, AMD02 (kabul kriteri)
  construction:                      # T3 — şemaya ekleniyor
    epc_contractor: Fact
    turbine_supplier: Fact
    epc_contract_price: Money
    epc_contract_current_doc: DOC-ID  # "güncel EPC sözleşmesi" sorusu
    change_orders: [{date:, subject: Fact, doc:, tag:}]
  operations:
    operating_year_on_demo_today: Fact     # validator hesaplar ve karşılaştırır (§3.2)
    monthly_production: [{month: "YYYY-MM", mwh:, availability_pct:, capacity_factor_pct:, tag:}]
    budget_vs_actual: [{period:, budget: Money, actual: Money, tag:}]
    incidents: [{date:, type: Fact, doc:, tag:}]
documents: [...]                     # §1.5
```

### 1.2 `izmir_res.yaml`
```yaml
meta: {...}
project:
  code: IZM_RES
  name: İzmir RES
  stage: development
  spv: {...}
  capacity_mw: {target: Fact}         # initial/current YOK — lisans yok
  turbines: null
  timeline:
    development_start: Event
    pre_licence_application: Event
    pre_licence: Event
    land_acquisition_start: Event
    ced_application: Event            # ÇED süreci başlangıcı
    # --- lisans sonrası alanların hepsi `null` (kabul kriteri) ---
    licence: null
    financing_signed: null
    financial_close: null
    epc_signed: null
    construction_start: null
    construction_end: null
    commissioning: null
    cod_expected_initial: null
    cod_actual: null
    operation_start: null
  finance: null
  construction: null
  operations: null
  development:                        # SPEC_05 §3 son satırı
    ced_status: Fact                  # ongoing
    permits_completed: [{step: <SPEC_03 §2 adım adı>, date:, doc:, tag:}]
    pending_steps: [{step:, expected: <serbest metin/null>, tag:}]
    latest_event: Event
documents: [...]
```
`step` değerleri SPEC_03 §2'deki sabit listeden (Önlisans, Süre Uzatımı Başvurusu, Arazi Edinimi, İmar Kesinleşme, Kat'i Proje Onayı, Bağlantı Anlaşması, Askeri Yasak Yazısı, TEA Yazısı, ÇED, Yapı Ruhsatı, Üretim Lisansı) seçilir; validator enum'a karşı doğrular. Hangi adımların "tamamlandı" sayılacağı onaya tabi (SORU 6).

### 1.3 `company.yaml` (T1 — bu planla tanımlanıyor)
```yaml
meta: {...}
holding: {name: Fact, role: "sponsor/parent"}
parties:                              # SPEC_03 §9 aktörleri; her biri {name: Fact, role:, kind:}
  - {name: Fact, role: sponsor|spv|local_bank|eca|epc_contractor|turbine_supplier|technical_advisor|insurer|legal_counsel, kind: company|bank|agency}
spvs: [{project_code: ANK_RES|IZM_RES, name: Fact, shareholders: [{name: Fact, share_pct: Fact}]}]
public_institutions: [EPDK, TEİAŞ, ÇŞB, ...]      # gerçek kurum adları — serbest liste (SPEC_03 §9)
name_whitelist: [<parties[].name.value'ların hepsi>]  # validator'ın "A.Ş./Ltd./Bank/Sigorta" taraması buna bakar (T12)
demo_banners: {all: "DEMO / FICTIONAL DOCUMENT FOR DEMONSTRATION PURPOSES ONLY", contracts: "NOT A REAL CONTRACT"}
documents: [...]                      # company-level envanter (Board Resolution vb.), §1.5 şeması, DOC-CO-*
```
`name_whitelist` ayrı tutuluyor (parties'ten türetmek yerine) çünkü belge metinlerinde kısaltılmış/varyant adlar da (ör. "PQR Bank" vs "PQR Bank A.Ş.") geçebilir; validator whitelist'in `parties` adlarını kapsadığını da denetler.

### 1.4 `fx_rates.yaml` (T1 — bu planla tanımlanıyor; SORU 3)
```yaml
meta: {...}
base_note: "<serbest metin: kurlar kurgusal, SPEC_03 §4>"
rates:
  - {pair: EUR/TRY, period: "YYYY" | "YYYY-Qn" | "YYYY-MM-DD", rate:, tag:}
  - {pair: USD/TRY, ...}
  - {pair: EUR/USD, ...}
```
Öneri: her çift için yıl bazında ortalama (Phase 4.2'nin `Financial_Model_<year>.xlsx` ve `Budget_vs_Actual_<year>.xlsx`'i için) + `demo_today` spot. Validator: `pair` üç sabit değerden biri, `rate > 0`, aynı `(pair, period)` tek kayıt, `EUR/USD` ile `EUR/TRY ÷ USD/TRY` arasında kaba tutarlılık (tolerans şemada sabit, sayısal değer onaya tabi değil — teknik eşik).

### 1.5 `documents[]` — master belge envanteri (üç dosyada aynı şema)
```yaml
- id: DOC-ANK-FIN-004
  department: finans                 # DB slug (T4); validator bilinen listeye karşı doğrular
  subdepartment: null | enerji_gelistirme | ...
  folder: finance                    # üretilen dosyanın alt klasörü (serbest)
  type: Facility Agreement           # SPEC_03 §3/§5/§6 tipleri
  name: Fact                         # gösterilen başlık
  document_date: Fact
  effective_date: Fact | null
  version: DRAFT|V01|V02|EXECUTED|AMD01|AMD02|... # sabit küme
  status: draft|executed|amended|superseded|active   # DB enum (DOMAIN_MODEL §4)
  parties: [<whitelist adları>]
  key_facts: {<alan>: <ledger yolu referansı>}   # ör. dscr_covenant: project.finance.dscr_covenant.initial — değer TEKRAR YAZILMAZ
  supersedes: DOC-ID | null
  superseded_by: DOC-ID | null
  related: [DOC-ID]
  source_type: digital_pdf | scanned_pdf
  language: en | tr
  confidentiality: normal|restricted|board
  generate_in_phase: 3.1 | 5.1 | never    # T6
  tag: USER_FACT|AI_ASSUMPTION
```
`key_facts` **değer değil, ledger yolu** taşır (T2 ile tutarlı: tek doğruluk kaynağı). Phase 3.1 generator yolu çözümleyip değeri şablona koyar; validator yolun var olduğunu doğrular.

Phase 3.1'in 15 belgesi envanterde `generate_in_phase: 3.1` ile işaretli olur (Ankara: Facility zinciri, Licence + tadil, EPC, COD belgesi, Covenant Report, Production Report; İzmir: ÇED durum yazısı, arazi edinim, teknik rapor, önlisans/başvuru; company: Board Resolution). Zincirin geri kalan halkaları ve SPEC_05 §6'daki ~70 belgeye kadar olanlar envantere şimdi **girmez** (YAGNI) — 5.1'de genişler.

---

## 2. `USER_FACT` / `AI_ASSUMPTION` mekanizması (T2)

Tek kural: **bilgi taşıyan her yaprak, `tag` alanı olan bir mapping'in içindedir.** Üç görünüm:

```yaml
# (a) tekil değer
capacity_mw:
  initial: {value: <...>, tag: AI_ASSUMPTION, source_doc: DOC-ANK-DEV-002}
# (b) tutar
capex: {value: <...>, currency: EUR, tag: AI_ASSUMPTION}
# (c) liste kaydı — kayıt başına tek tag (alan alan değil)
covenant_tests:
  - {period: "Qn_YYYY", dscr: <...>, result: pass, doc: DOC-ANK-FIN-010, tag: AI_ASSUMPTION}
```
Etiketsiz kalabilen tek şey **kimlik/yapı anahtarları**: `meta.*`, `project.code/name/stage`, `documents[].id/type/version/status/folder/language/source_type/generate_in_phase/supersedes/superseded_by/related`, timeline anahtar adları, `key_facts` (yol referansı). Validator, şema modellerinde `Fact/Money/Event/kayıt` olarak tanımlı her yerde `tag`'i **zorunlu** kılar (Pydantic `Literal["USER_FACT","AI_ASSUMPTION"]`) — eksik/yanlış etiket = hata.

Onay akışı (PHASES 2.1 "Süreç"): ilk taslakta **her tag `AI_ASSUMPTION`**. Naci/ekip arkadaşı gözden geçirip onayladığı değerin tag'ini `USER_FACT` yapar (YAML'da tek kelime değişir; değer değişirse yeni değer + `USER_FACT`). Validator her iki tag'i de kabul eder; raporda "kaç USER_FACT / kaç AI_ASSUMPTION" sayısı yazar (`--summary`). Phase 3.1 başlamadan önce hangi eşik gerektiği SORU 4.

---

## 3. `seed_data/generator/validate_ledger.py`

### 3.1 Çalıştırma
- `python seed_data/generator/validate_ledger.py [--master seed_data/master] [--questions seed_data/evaluation/questions.json] [--summary]`
- Çıktı: stdout'a satır başına bir bulgu — `ERROR <dosya> <yaml.yolu>: <mesaj>` / `WARNING ...`; sonda `N error(s), M warning(s)`. Exit code `0` yalnızca `N == 0` ise. (Kabul kriteri "validator 0 hata" = exit 0.)
- Makefile: yeni hedef `validate-ledger` (`$(COMPOSE) run --rm -T --no-deps backend python seed_data/generator/validate_ledger.py`); `lint` hedefi sonuna da eklenir (T9 — prompt-doc diff ile aynı yer). `pyproject.toml` dev grubuna `pyyaml>=6`; `uv lock` + image rebuild (Phase 1.1'deki akış).
- Yapı: `ledger_schema.py` (Pydantic modelleri, §1) + `validate_ledger.py` (yükle → modelle (yapısal hatalar) → çapraz kurallar → rapor). Bağımsız, `app.*` import etmez (ADR-013).

### 3.2 Kurallar — kronoloji (SPEC_03 §2)
| # | Kural | Uygulandığı yer |
|---|---|---|
| C1 | Kaba sıra: `development_start < licence < financing_signed < financial_close < construction_start < commissioning < cod_actual ≤ operation_start` | Ankara |
| C2 | `epc_signed ≤ construction_end`; `epc_signed ≥ licence` | Ankara |
| C3 | `financial_close ≥ financing_signed`; ilk `drawdowns[].date ≥ financial_close` | Ankara |
| C4 | `cod_actual ≥ commissioning`; `licence_amendment > licence` | Ankara |
| C5 | `cod_expected_initial` ile `cod_actual` farkı varsa `change_orders` içinde COD konulu bir kayıt olmalı (SPEC_03 §10 "COD ertelemesi") — yoksa WARNING | Ankara |
| C6 | **İşletme yılı (T10):** yıldönümü bazlı — `n = floor((demo_today − cod_actual) / 365.25) + 1`; `operations.operating_year_on_demo_today.value == n` ve `n == 3` (kabul kriteri) | Ankara |
| C7 | `covenant_tests[].period` ve `monthly_production[].month` `≤ demo_today`; `drawdowns[].date ≤ demo_today` | Ankara |
| C8 | Belge tarihleri: `documents[].document_date ≤ demo_today`; `effective_date ≥ document_date`; zincirde `superseded_by`'ın tarihi `supersedes`'inkinden büyük | üç dosya |
| C9 | İzmir: dolu Event'ler kendi aralarında `development_start ≤ pre_licence_application ≤ pre_licence ≤ …`; `permits_completed[].date` dolu ve `≤ demo_today`; `latest_event.date` = dolu Event'lerin en büyüğü | İzmir |
| C10 | `meta.demo_today` dört dosyada aynı **ve** backend `.env`/`DEMO_TODAY` ile aynı (validator env'den okur; yoksa yalnızca dosyalar arası eşitlik) | hepsi |

### 3.3 Kurallar — finans tutarlılığı (SPEC_03 §3)
| # | Kural |
|---|---|
| F1 | `local_debt + eca_debt == total_debt` (aynı para birimi zorunlu) |
| F2 | `total_debt + equity == capex` (tolerans yok; tümü aynı para birimi) |
| F3 | `Σ drawdowns[].amount ≤ total_debt`; `outstanding_debt_as_of_demo_today ≤ Σ drawdowns` |
| F4 | `tenor_years.current ≥ tenor_years.initial` ve `dscr_covenant.current ≤ dscr_covenant.initial` (SPEC_03 §10: "gevşetme + uzatma"); `changed_by` her ikisinde de zincirdeki bir `AMD*` belgesi |
| F5 | `covenant_tests[]`: `result == pass` ⇔ `dscr ≥` o dönemde yürürlükteki covenant (dönem tarihi `changed_by` belgesinin `effective_date`'inden önceyse `initial`, sonra `current`) |
| F6 | `facility_chain` tam olarak `[DRAFT, V01, V02, EXECUTED, AMD01, AMD02]` versiyonlu belgelerden oluşur; `supersedes/superseded_by` bağları zinciri **doğrusal** kurar; `status=active/executed` yalnızca **son** halkada "güncel" (DOMAIN_MODEL §6: güncel belge tek) |
| F7 | `epc_contract_price` para birimi tanımlı; `epc_contract_current_doc` envanterde ve `type` EPC ailesinden |
| F8 | `key_facts` yol referansları çözülüyor (yol ledger'da var) |

### 3.4 Kurallar — İzmir izolasyonu, para birimi, isimler
| # | Kural |
|---|---|
| I1 | İzmir: `timeline.{licence, financing_signed, financial_close, epc_signed, construction_*, commissioning, cod_*, operation_start}` hepsi `null`; `finance`, `construction`, `operations` `null` (kabul kriteri "İzmir COD/lisans/finansman null") |
| I2 | İzmir `documents[].type` finans tipi (SPEC_03 §3 listesi) **içeremez** (SPEC_05 §6 "Finans 0") |
| I3 | İzmir `documents[]`/`key_facts` Ankara yoluna (`ankara_res.*`) referans veremez ve tersi (SPEC_05 §8 karıştırma) |
| M1 | Her `Money` `currency ∈ {EUR, USD, TRY}`; şemada `Money` olan alan düz sayı yazılmışsa hata ("her tutarda para birimi") |
| M2 | Kredi alanları (`*_debt`, `capex`, `equity`, `drawdowns`, `outstanding_*`, `epc_contract_price`) `EUR`; `budget_vs_actual` `TRY` (SPEC_03 §4 kararı) — aksi WARNING (karar Naci'nin, sert hata değil) |
| N1 | Dört dosyadaki **tüm** string değerlerde regex taraması: `\b[\w.'-]+(?:\s+[\w.'-]+){0,3}\s+(A\.Ş\.|Ltd\.(?:\s*Şti\.)?|Bank|Sigorta|GmbH|S\.A\.|Inc\.)` eşleşmeleri `company.name_whitelist` içinde olmalı; `public_institutions` muaf |
| N2 | `parties[].name`, `spv.name`, `lenders.*`, `epc_contractor`, `turbine_supplier`, `documents[].parties[]` değerleri whitelist'te |
| N3 | Whitelist SPEC_05 §4'teki 7 kurgusal adı kapsar (sabit liste validator içinde — spec metni) |
| D1 | `documents[].department` bilinen slug listesinde (`enerji_grubu, enerji_gelistirme, enerji_epc_insaat, enerji_bakim, finans, hukuk, mali_isler, idari_isler` — validator içinde sabit, `demo_departments_seed.py` ile aynı; T4) |
| D2 | `documents[].id` benzersiz ve `DOC-<PRJ>-<DEP>-<NNN>` biçiminde; `<PRJ>` dosyayla tutarlı (ankara → ANK …); `supersedes/superseded_by/related/changed_by/source_doc/doc` referansları çözülüyor |
| G1 | `generate_in_phase: 3.1` olan belgeler PHASES 3.1'deki 15 kalemle sayıca eşit (WARNING, sert değil) |

### 3.5 `questions.json` kontrolleri (aynı komut, ikinci aşama)
| # | Kural |
|---|---|
| Q1 | Şema (§4.1) — Pydantic; `category` sabit küme; `ask_as_user` ∈ {admin, yonetim, finans, hukuk, enerji}; `expected_department` slug veya null |
| Q2 | Kotalar (T7): toplam ≥ 30; `expected_project == "İzmir RES"` ≥ 9; `== "Ankara RES"` ≥ 20; `category` hallucination ≥ 3, isolation ≥ 3, authorization ≥ 3 |
| Q3 | `hallucination` ⇒ `expect_no_answer: true`; `authorization` ⇒ `ask_as_user == enerji` ve `expect_no_answer: true` (SPEC_05 §9) |
| Q4 | `expected_answer` `ledger:` ile başlıyorsa yol çözülüyor (SORU 7); `required_sources[]` envanterdeki bir `documents[].name` veya `type`'a eşleşiyor; `forbidden_sources[]` proje adı veya belge adı |
| Q5 | `id` benzersiz, `<PRJ>-<KAT>-<NNN>` biçiminde |

---

## 4. `seed_data/evaluation/questions.json` v1

### 4.1 Şema
```json
{
  "version": 1,
  "demo_today": "<DEMO_TODAY>",
  "questions": [
    {
      "id": "ANK-FIN-001",
      "category": "document|temporal|data|mixed|isolation|hallucination|authorization",
      "question": "...",
      "expected_answer": "ledger:ankara_res.project.finance.dscr_covenant.current",
      "expected_answer_aliases": [],
      "expected_project": "Ankara RES | İzmir RES | null",
      "expected_department": "finans | hukuk | enerji_grubu | ... | null",
      "required_sources": ["<envanter belge adı/tipi>"],
      "forbidden_sources": ["<proje adı veya belge adı>"],
      "ask_as_user": "admin|yonetim|finans|hukuk|enerji",
      "expect_no_answer": false,
      "notes": "<opsiyonel, insan için>"
    }
  ]
}
```
SPEC_05 §9 alanlarının hepsi korunur; eklenenler: kök `version/demo_today`, `notes`, `expected_project: null` (Bursa gibi olmayan proje için), `expected_department` slug. `expected_answer` **ledger yolu** (SORU 7); `expected_answer_aliases` v1'de boş bırakılır, onaylı değerler girince biçim varyantları (virgül/nokta ondalık, `x` soneki var/yok, tarih `DD.MM.YYYY`/ISO) doldurulur — plan rakam içermediği için burada örnek verilmiyor. `data`/`mixed` kategorileri v1'de **kullanılmaz** (Excel Phase 4.2) — şemada var, kota yok.

### 4.2 Dağılım (≥ 30; T7 örtüşme kuralıyla)
| Kova | Adet | Sayım alanı |
|---|---|---|
| Ankara RES | ≥ 20 | `expected_project` |
| İzmir RES | ≥ 9 | `expected_project` |
| hallucination | ≥ 3 | `category` |
| isolation | ≥ 3 | `category` |
| authorization | ≥ 3 | `category` |
| document / temporal | kalan | `category` |
Örtüşme örneği: "İzmir RES'in COD tarihi nedir?" hem İzmir'e hem hallucination'a sayılır. Hedef v1: ~34 soru (20 Ankara + 9 İzmir + 3 hallucination'ın 1'i İzmir'e sayılır + 3 isolation + 3 authorization'ın bir kısmı proje kotasına sayılır).

### 4.3 Soru kalıpları — kategori başına öneri (SORU: rakamsız; cevaplar ledger'dan gelecek)
**Ankara — document/temporal (SPEC_05 §9 minimum 20'si birebir):** development başlangıç tarihi; lisans tarihi; güncel kapasite; ilk lisans kapasitesi; kapasite tadili tarihi; financial close tarihi; toplam finansman; yerli banka kredisi; ECA kredisi; güncel faiz/margin; güncel DSCR covenant; ilk DSCR covenant; güncel Facility Agreement hangisi; kaç amendment var; EPC bedeli; güncel EPC sözleşmesi hangisi; COD tarihi; kaçıncı işletme yılı; son covenant testi sonucu; güncel outstanding debt. Ek adaylar (temporal): "DSCR covenant ne zaman ve hangi belgeyle değişti?", "Tenor ilk ne kadardı, şimdi ne kadar?", "COD beklenen tarihten saptı mı, neden?" (kural 6: yalnızca belgede yazan sebep).
**İzmir — document (minimum 9'u birebir):** hangi aşamada; ÇED durumu; ÇED tamamlandı mı; yapı ruhsatı var mı; lisans alındı mı; inşaata başlandı mı; hangi adımlar tamamlandı; hangi kritik adımlar bekliyor; en son gelişme.
**hallucination (`expect_no_answer: true`):** "İzmir RES'in COD tarihi nedir?", "Ankara RES'in ikinci EPC yüklenicisi kim?", "Bursa RES'in kapasitesi nedir?" (SPEC_05 §9) + aday: "İzmir RES'in kredi faizi nedir?" (finansman yok).
**isolation (`forbidden_sources` ile):** "İzmir RES'in kapasitesi nedir?" → yalnızca İzmir hedef kapasitesi, Ankara belgeleri yasak; "Ankara RES'in ÇED durumu nedir?" → İzmir ÇED belgeleri yasak (cevap: Ankara için ÇED tamamlanmış/lisanslı olduğu belgelerden); "Hangi projenin finansmanı kapanmış durumda?" → yalnızca Ankara kaynakları.
**authorization (`ask_as_user: enerji`, `expect_no_answer: true`):** "Ankara RES'in güncel DSCR covenant'ı nedir?" (finans belgesi, enerji göremez); "Toplam kredi tutarı nedir?"; "Son covenant test sonucu nedir?" — üçü de `retrieved_document_ids` boş beklentisiyle (Phase 1.2 kriteri 1'in eval karşılığı). Aday: `ask_as_user: hukuk` ile aynı finans sorusu (kota dışı, ek güvenlik).

---

## 5. Onay formu — Naci ve ekip arkadaşının dolduracağı alanlar (rakamsız)

Her satır: **alan** | **tür** | **kim** (N = Naci, F = enerji finansı arkadaşı, C = Claude taslak önerir) | **not**. İlk taslakta C doldurur, hepsi `AI_ASSUMPTION`; N/F onaylar → `USER_FACT`.

### 5.1 Şirket (`company.yaml`)
| Alan | Tür | Kim | Not |
|---|---|---|---|
| Holding/sponsor adı | metin (kurgusal, whitelist) | C→N | SPEC_05 §4 adlarından |
| Ankara SPV adı, hissedarlar ve payları | metin + yüzde listesi | C→N | paylar toplamı %100 (validator) |
| İzmir SPV adı, hissedarlar ve payları | metin + yüzde | C→N | |
| Yerli banka adı | metin | C→N | |
| ECA adı (kurgusal ajans) | metin | C→N | whitelist'e girer |
| EPC yüklenicisi, türbin tedarikçisi, teknik danışman, sigortacı, hukuk müşaviri adları | metin | C→N | hepsi kurgusal |
| Kamu kurumu adları (serbest kullanım) | liste | C | EPDK, TEİAŞ, ÇŞB … |
| Company-level belgeler (Board Resolution vb.): ad, tarih, dil | envanter | C→N | 3.1'de 1 belge |

### 5.2 Ankara RES — kimlik ve teknik
| Alan | Tür | Kim | Not |
|---|---|---|---|
| Lisans kapasitesi (ilk) | MW | F | |
| Kapasite (güncel, tadil sonrası) | MW | F | tadil > ilk |
| Türbin sayısı ve jenerik model sınıfı | adet + metin | F | kapasite/türbin tutarlı |
| İşletme yılı (`DEMO_TODAY`) | adet | validator hesaplar | 3 olmalı |

### 5.3 Ankara RES — zaman çizelgesi (hepsi tarih)
| Alan | Kim | Kısıt (validator) |
|---|---|---|
| Development başlangıcı | F | en erken |
| Önlisans | F | |
| Üretim lisansı | F | development'tan sonra |
| Lisans tadili (kapasite artışı) | F | lisanstan sonra |
| Finansman imzası (Facility EXECUTED) | F | lisanstan sonra |
| Financial close | F | imzadan sonra veya eşit |
| EPC imzası | F | lisans ≤ EPC ≤ inşaat bitişi |
| İnşaat başlangıcı / bitişi | F | FC'den sonra |
| Commissioning | F | inşaat bitişinden sonra |
| COD (ilk beklenen) | F | |
| COD (gerçekleşen) | F | commissioning'den sonra; `DEMO_TODAY`'de 3. yıl |
| Operasyon başlangıcı | F | ≥ COD |
| Facility DRAFT / V01 / V02 tarihleri | C→F | EXECUTED'dan önce, artan |
| Facility AMD01 / AMD02 tarihleri ve yürürlük tarihleri | F | EXECUTED'dan sonra, artan; AMD02'nin konusu SORU 1 |
| Change order'lar (tarih + konu) | C→F | COD ertelemesi varsa biri COD konulu |

### 5.4 Ankara RES — finansman
| Alan | Tür | Kim | Kısıt |
|---|---|---|---|
| Capex | tutar + EUR | F | |
| Equity | tutar + EUR | F | capex − borç |
| Toplam borç | tutar + EUR | F | |
| Yerli banka payı / ECA payı | tutar + EUR | F | toplamı = borç |
| Faiz bazı (ör. referans oran adı) + margin | metin + yüzde | F | |
| Tenor (ilk / güncel) | yıl | F | güncel ≥ ilk; değiştiren belge AMD01 |
| Grace | ay | F | |
| Geri ödeme profili | metin | F | |
| DSCR covenant (ilk / güncel) | oran | F | güncel ≤ ilk; değiştiren AMD01 |
| Drawdown'lar (tarih + tutar + EUR) | liste | C→F | FC'den sonra; toplam ≤ borç |
| Outstanding debt (`DEMO_TODAY`) | tutar + EUR | F | ≤ çekilen |
| Covenant testleri (çeyrek, DSCR, sonuç) | liste | C→F | `DEMO_TODAY`'e kadar; pass/fail covenant'la tutarlı; Phase 4.2 `Covenant_Report.xlsx` bunu kullanır |
| EPC sözleşme bedeli | tutar + EUR | F | |
| Debt/equity | türetilir | validator | |

### 5.5 Ankara RES — operasyon
| Alan | Tür | Kim | Not |
|---|---|---|---|
| Aylık üretim (ay, MWh, availability %, capacity factor %) | liste | C→F | kaç ay geriye gidileceği SORU 8; Phase 4.2 `Monthly_Production_<year>.xlsx` |
| Bütçe vs gerçekleşen (dönem, bütçe TRY, gerçek TRY) | liste | C→F | Phase 4.2 `Budget_vs_Actual_<year>.xlsx` |
| Olaylar (tarih, tür, belge) | liste | C | dramatik değil (SPEC_03 §7) |

### 5.6 İzmir RES
| Alan | Tür | Kim | Kısıt |
|---|---|---|---|
| SPV adı, hissedarlar | metin + yüzde | C→N | |
| Hedef kapasite | MW | F | tek değer (lisans yok) |
| Development başlangıcı | tarih | F | |
| Önlisans başvurusu / önlisans tarihi | tarih | F | |
| Arazi edinimi başlangıcı | tarih | F | |
| ÇED başvurusu tarihi; ÇED durumu | tarih + metin | F | `ongoing` |
| Tamamlanan adımlar (SPEC_03 §2 listesinden, tarihli) | liste | F | SORU 6 |
| Bekleyen kritik adımlar (tarihsiz) | liste | F | |
| En son gelişme (tarih + açıklama + belge) | Event | F | dolu tarihlerin en büyüğü |
| Lisans / finansman / FC / EPC / inşaat / COD / operasyon | — | — | **null**, form dışı |

### 5.7 FX (`fx_rates.yaml`)
| Alan | Tür | Kim | Not |
|---|---|---|---|
| EUR/TRY, USD/TRY, EUR/USD — dönem başına kur | oran | C→F | granülarite SORU 3 |

---

## 6. Kabul kriteri → kanıt

Testler `backend/tests/test_validate_ledger.py`'de; validator `t0_fixtures.py`'nin `generate.py`'yi yüklediği gibi `importlib` ile yüklenir. **Kural testleri sentetik, geçici mini-ledger'larla** çalışır (test içinde uydurulmuş tarih/tutar — demo ledger'ın değerleri değil; CLAUDE.md kuralı demo içeriğine dair, test fixture'ına değil, Phase 0.2/0.3 T0 seti gibi). Gerçek ledger'ı okuyan tek test `test_master_ledger_validates_clean`.

| Kriter (PHASES.md) | Test / komut | Kanıt |
|---|---|---|
| validator 0 hata | `make validate-ledger` (exit 0) + `test_validate_ledger.py::test_master_ledger_validates_clean` | stdout `0 error(s)` |
| Ankara zinciri DRAFT→V01→V02→EXECUTED→AMD01→AMD02 ledger'da | `::test_facility_chain_is_linear_and_complete` (F6, sentetik) + gerçek ledger testi | zincir bozulunca `ERROR … facility_chain` |
| Ankara 3. işletme yılı `DEMO_TODAY`'e göre | `::test_operating_year_is_anniversary_based` (C6; COD'u pencerenin içine/dışına koyan sentetik tarihler) + gerçek ledger | `ERROR … operating_year` |
| İzmir COD/lisans/finansman `null` | `::test_izmir_post_licence_fields_must_be_null` (I1, sentetik dolu alan → hata) + gerçek ledger | |
| Her tutarda para birimi | `::test_money_without_currency_is_error` (M1) + gerçek ledger | |
| ≥ 30 soru, İzmir ≥ 9, Ankara ≥ 20, hallucination/isolation/authorization ≥ 3 | `::test_question_quotas` (Q2, sentetik eksik kova → hata) + gerçek `questions.json` | `make validate-ledger` çıktısındaki kota özeti |
| Kronoloji / finans / isim whitelist / departman slug (kapsam) | `::test_chronology_rules` (C1–C4), `::test_finance_sums` (F1–F3), `::test_name_whitelist_regex` (N1), `::test_department_slug_known` (D1) | |

Ek: `make lint` validator'ı da çalıştırdığı için CI-benzeri koruma; `ruff` `seed_data/generator/`'ı tarar.

---

## SORU (Naci cevaplamalı)

1. **Facility AMD02 neyi değiştiriyor?** SPEC_05 §7 yalnızca AMD01'i tanımlıyor (DSCR gevşetme + tenor uzatma). Zincirde AMD02 zorunlu. Önerim: AMD02 **finansal olmayan** bir değişiklik (ör. geri ödeme takvimi/tanım düzeltmesi veya covenant test döneminin tanımı) — böylece "güncel DSCR/tenor" cevapları AMD01'e bağlı kalır, AMD02 yalnızca "güncel Facility Agreement hangisi?" sorusunu cevaplar. Uygun mu, yoksa AMD02 de sayısal bir değer mi değiştirsin (hangisi)?
2. **Lisans tadili adlandırması.** SPEC_05 timeline'da `licence_amendment_02` var, Amendment 01 yok; PHASES 3.1 "Licence + Amendment 2 (belge)". Önerim: tek lisans tadili (kapasite artışı), anahtar `licence_amendment`, belge adı "Licence Amendment 01". Onaylıyor musun?
3. **`fx_rates` granülaritesi.** Önerim: üç çift (EUR/TRY, USD/TRY, EUR/USD) × yıl bazında ortalama (ledger'ın kapsadığı yıllar) + `demo_today` spot. Çeyreklik gerekli mi (Phase 4.2 covenant raporu EUR'da olduğu için gerekmiyor gibi)?
4. **Faz kapanışı ve `USER_FACT` eşiği.** Kabul kriterleri `USER_FACT` şartı koymuyor. Önerim: 2.1 tüm değerler `AI_ASSUMPTION` iken raporda bir **onay tablosu** ile kapatılır (tag `phase-2-1`); onayladıkların ayrı bir "ledger onayı" commit'inde `USER_FACT` olur; Phase 3.1 bu commit'ten önce başlamaz (SPEC_05 §2 madde 8–10). Alternatif: tag'i onay sonrasına bırakmak. Hangisi?
5. **Envanter kapsamı.** Ledger 6 halkalı zincirin tamamını listeler; Phase 3.1'in "Facility zinciri 4" belgesi hangileri? Önerim: DRAFT, EXECUTED, AMD01, AMD02 dosyaya dönüşür; V01/V02 envanterde `generate_in_phase: 5.1` (revision history'de görünür, dosyası sonra). Uygun mu?
6. **İzmir'de tamamlanmış sayılacak adımlar.** SPEC_03 §2'deki 11 lisans-öncesi adımdan hangileri "tamamlandı" (tarihli), hangileri "bekliyor"? Önerim: Önlisans + Arazi Edinimi (kısmi) tamamlanmış; ÇED devam; Yapı Ruhsatı, Üretim Lisansı ve bağlantı/imar/kat'i proje adımları bekliyor — kesin küme sizin.
7. **`expected_answer` biçimi.** Önerim: `ledger:<yol>` referansı (rakam questions.json'da tekrarlanmaz, ledger değişince senkron sorunu olmaz; Phase 4.1 runner yolu çözer ve `expected_answer_aliases`'taki biçim varyantlarıyla karşılaştırır). Alternatif: SPEC örneğindeki gibi literal değer. Hangisi?
8. **Operasyon serilerinin uzunluğu.** Aylık üretim ve bütçe/gerçekleşen kaç ay/çeyrek geriye gitsin (COD'dan `DEMO_TODAY`'e kadar tam seri mi, yalnızca son işletme yılı mı)? Phase 4.2 workbook'larının derinliğini belirler. Önerim: tam seri (COD → `DEMO_TODAY`), covenant testleri çeyreklik aynı aralıkta.

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)
- Şema Pydantic v2 modelleri olarak `seed_data/generator/ledger_schema.py`'de; `jsonschema` eklenmiyor; `pyyaml` dev grubuna açıkça ekleniyor (T8).
- Etiket mekanizması: `Fact/Money/Event/kayıt` mapping'lerinde zorunlu `tag`; kimlik/yapı anahtarları etiketsiz (§2).
- `documents[].key_facts` değer değil ledger yolu taşır; `expected_answer` da yol (SORU 7'ye bağlı).
- Departman değerleri DB slug'ı (`finans` …), `finance` değil (T4).
- `questions.json` yolu `seed_data/evaluation/` (T5); kök sarmalayıcı `{version, demo_today, questions}`.
- Belge ID şeması `DOC-<ANK|IZM|CO>-<DEV|FIN|EPC|OPS|LEG|ADM>-<NNN>`.
- İşletme yılı yıldönümü bazlı (T10).
- Validator çıktısı satır bazlı stdout + exit code; `make validate-ledger` + `make lint` içine ekleme (T9).
- Kota sayımı: proje `expected_project`'ten, kategori `category`'den; örtüşme serbest (T7).
- `data`/`mixed` kategorileri v1'de boş (Excel 4.2).
- `tests/live/test_t0_live.py` ve `seed_data/t0/` bu fazda değişmez (T11).
- Envanter yalnızca Phase 3.1'in 15 belgesi + zincirin envanter-only halkaları; ~70 belgeye 5.1'de genişler.

## Doküman değişiklikleri
- `docs/ARCHITECTURE.md`: ADR-013'e "Phase 2.1 concretization" notu (Pydantic şema, tag kuralı, slug kararı, `questions.json` yolu, yıldönümü bazlı işletme yılı).
- `docs/SPEC_05_synthetic_veri_ve_evaluation.md`: **değiştirilmez** (spec Naci'nin); sapmalar rapor §5'te ve ADR notunda.
- `README.md`: "Truth ledger (Phase 2.1)" bölümü — dosyalar, `make validate-ledger`, onay akışı (`AI_ASSUMPTION → USER_FACT`), `seed_data/master/` düzenleme kuralı.
- `infra/.env.example`: değişiklik yok (`DEMO_TODAY` zaten var).
- `docs/reports/PHASE_2_1_REPORT.md` (şablon), **onay tablosu** (her `AI_ASSUMPTION` değer için satır: alan | taslak değer | onay ☐), `docs/PHASES.md` durum satırı, `git tag phase-2-1`.

## Uygulama sırası
1. `pyproject.toml` dev grubuna `pyyaml` → `uv lock` → image rebuild.
2. `seed_data/generator/ledger_schema.py` (Pydantic modelleri, §1) + `validate_ledger.py` iskeleti (yükle/modelle/rapor).
3. Kural setleri: kronoloji (§3.2) → finans (§3.3) → izolasyon/para birimi/isim/slug (§3.4) → questions (§3.5); her set için `tests/test_validate_ledger.py`'de sentetik testler (önce kırmızı, sonra yeşil).
4. `company.yaml`, `fx_rates.yaml`, `izmir_res.yaml`, `ankara_res.yaml` taslakları — **hepsi `AI_ASSUMPTION`**; SORU 1–8 cevaplarına göre. Değerler raporun onay tablosuna da yazılır.
5. `seed_data/evaluation/questions.json` v1 (≥ 30, §4).
6. `Makefile`: `validate-ledger`, `lint`'e ekleme; `make validate-ledger` → 0 hata.
7. `make test` + `make lint` yeşil → README, ADR-013 notu → rapor (+ onay tablosu) → `docs/PHASES.md` → commit + tag `phase-2-1` + push.

## Kritik dosyalar
- `seed_data/generator/ledger_schema.py`, `seed_data/generator/validate_ledger.py`
- `seed_data/master/ankara_res.yaml`, `seed_data/master/izmir_res.yaml`, `seed_data/master/company.yaml`, `seed_data/master/fx_rates.yaml`
- `seed_data/evaluation/questions.json`
- `backend/tests/test_validate_ledger.py`
- `Makefile`, `backend/pyproject.toml`
