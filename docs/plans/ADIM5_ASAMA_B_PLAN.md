# Adım 5, Aşama B Planı — demo_today, şema genelleştirmesi, Kızılova finans/EPC, AI_ASSUMPTION denetimi, eval soru revizyonu

**Dal:** `feat/adim5-veri-kutuphanesi` (Aşama A'nın üstüne). **Kod yok** (tek istisna: §6 — `check_conflict_groups` birim testleri, zaten yazıldı/commit edildi). **Canlı DB'ye dokunulmadı, canlı Gemini çağrısı yapılmadı.**

Bu plan, Aşama A raporunun (`docs/reports/ADIM5_ASAMA_A_REPORT.md`) §9'unda bırakılan dört açık maddeyi ve Naci'nin bu round için istediği beşinci maddeyi (eval soru revizyonu) kapsar. Hiçbiri henüz uygulanmadı — hepsi Naci'nin SORU cevaplarını bekliyor.

---

## 1. demo_today: 15.09.2026 → 06.10.2026 (T-7 varsayımı)

### 1.1 Etki listesi

| Katman | Etki | Risk |
|---|---|---|
| `backend/app/core/config.py::Settings.demo_today` | Varsayılan değer `date(2026, 9, 15)` → `date(2026, 10, 6)`. Kod hiçbir yerde `demo_today`'i doğrudan okumuyor (ADR-026) — yalnızca `app/services/temporal.py::today()` üzerinden. | Düşük — tek satır. |
| `.env` / `infra/.env.example` | `DEMO_TODAY=2026-09-15` → `2026-10-06`. | Düşük. |
| `seed_data/master/*.yaml` (4 dosya: `ankara_res`, `izmir_res`, `company`, `fx_rates`) | `meta.demo_today` dördünde de aynı anda değişmeli (C10 kuralı: "files disagree" — dosyalar arasında uyuşmazlık zaten hata). | Düşük, mekanik. |
| `validate_ledger.py` C6/C7/C8/C9 kuralları | Hepsi "demo_today'den SONRA tarihli olamaz" yönünde (tek taraflı eşitsizlik). demo_today'i **ileri** almak bu kuralları gevşetir, hiçbirini **kırmaz** — yeni bir tarih ihlali doğmaz. | Yok. |
| `operating_year(demo_today, cod)` (C6) | `cod_actual = 2023-10-15`. 06.10.2026, hâlâ 3. yıldönümünden (15.10.2026) önce → **işletme yılı yine 3**, değişmiyor. Şans eseri — ileride demo_today 15.10.2026'yı geçerse bu alanın da güncellenmesi gerekecek, not edildi. | Yok (bu spesifik tarih için). |
| `finance.outstanding_debt_as_of_demo_today` (F9, `debt_math.outstanding_on`) | 06.10.2026, 8. taksidin vade tarihinden (07.10.2026) **1 gün önce** — aynı yarı yıl (H2_2026) içinde ve taksit henüz düşmemiş. `outstanding_on` bir yarı yılın kapanışını atomik döndürüyor (gün bazlı ara değer yok) → **değer değişmiyor** (hâlâ 11.671.800 USD). Doğrulama: gerçek `debt_math.py` ile tekrar çalıştırılmalı (bu planda yapılmadı, uygulama anında yapılacak). | Düşük ama **sınırda** — 07.10.2026'dan sonraki bir tarih seçilseydi değer değişirdi. |
| `finance.covenant_tests` / `cfads_by_quarter` son satırı (Q2_2026) | Aynı kalır; demo_today hâlâ Q3_2026 içinde (06.10 → Q4_2026 değil, Q3_2026 — Ekim Q4'e girer, HAYIR: Ekim-Aralık = Q4. 06.10.2026 Q4_2026 içinde). **Dikkat:** demo_today Q3'ten Q4'e geçiyor; `covenant_tests`'in son satırı hâlâ Q2_2026 (Temmuz 2026'da üretilen rapor) — bu zaten "son bilinen rapor" ise sorun yok, ama "demo_today'e en yakın rapor" beklentisiyle yeni bir Q3_2026 satırı eklenmesi gerekip gerekmediği ayrı bir karar. | **Orta** — Naci'nin kararı gerekiyor (SORU 1). |
| `operations.monthly_production` son ay | Şu an `2026-08` ile bitiyor. demo_today Ekim'e kaydığında "en son üretim ayı" beklentisi Eylül (ve belki Ekim) verisini de ister mi? Hiçbir validator kuralı bunu zorlamıyor (yalnızca "demo_today'den sonra olamaz" kontrolü var, "demo_today'e kadar tam olmalı" kontrolü yok) — ama eval'de "bu ayki üretim ne kadar?" tipi bir soru varsa cevapsız kalabilir. | **Orta** — SORU 1'in bir parçası. |
| `questions.json` — 11 `temporal` kategorili soru (§Ek: liste) | Her biri gözden geçirilmeli: "kaçıncı işletme yılı" (ANK-OPS-001, değişmiyor — yukarıda), "sigorta bitmiş mi" (ANK-OPS-004, poliçe zaten 2025-01-09'da bitmiş — hâlâ bitmiş, değişmiyor), COD sapması (ANK-EPC-004, tarih farkı değişmiyor). Hiçbiri demo_today'e **doğrudan** bağlı bir sayısal beklenti taşımıyor — risk düşük ama tek tek doğrulanmalı. | Düşük, doğrulama gerekli. |
| `test_excel_engine.py::test_outstanding_debt_today_refuses_a_stale_snapshot` (ADR-026) | `today=date(2026, 9, 16)` ile çağrılıp "demo_today'den 1 gün sonrası reddedilir" test ediyor. demo_today değişince bu test `date(2026, 10, 7)` kullanmalı. | Düşük, mekanik — tek satır. |
| `docs/PHASES.md`, diğer raporlar | "15.09.2026" birçok eski raporda literal geçiyor (tarihsel kayıt, DOKUNULMAZ — geçmişi yeniden yazmak yanlış olur). Yalnızca **canlı/güncel** config ve ledger değişir. | Yok (bilinçli, dokunulmayacak). |

### 1.2 Doğrulama planı (uygulama anında)

1. `meta.demo_today`'i 4 dosyada değiştir → `make validate-ledger` (C6/C7/C8/C9/C10, F9/F10/F11) 0 hata vermeli.
2. `debt_math.outstanding_on(rows, date(2026,10,6))` gerçek kodla tekrar çalıştırılıp 11.671.800 USD çıktığı teyit edilsin (yukarıdaki "şans eseri değişmiyor" iddiası kod ile doğrulanmalı, el hesabıyla değil).
3. `make excel` (workbook'un `_meta` sayfasındaki `Ledger_DemoToday` güncellenir) + `make validate-excel`.
4. 11 temporal sorunun her biri tek tek: değer hâlâ doğru mu?
5. `test_outstanding_debt_today_refuses_a_stale_snapshot`'ın sabit tarihini güncelle.

---

## 2. Şemanın 2 projeden N projeye genelleştirilmesi

### 2.1 Mevcut hardcode envanteri

`ledger_schema.py`:
- `AnkaraProject`/`AnkaraLedger`, `IzmirProject`/`IzmirLedger` — **iki bespoke Pydantic sınıf ağacı**, proje adı sınıf adına gömülü. `AnkaraTimeline` 13 alan (tam operasyonel), `IzmirTimeline` aynı alanları `None`'a sabitliyor (lisans sonrası alanlar).
- `CompanyLedger.spvs: list[CompanySpv]` — Adım 5'te zaten genel/kayıt-tarzı (7 koda genişletildi); yalnızca ad+hissedarlık, derin ledger yok.

`validate_ledger.py`:
- `LEDGER_FILES = {"company": ..., "ankara_res": ..., "izmir_res": ..., "fx_rates": ...}` ve `PROJECT_PREFIX = {"ankara_res": "ANK", "izmir_res": "IZM", "company": "CO"}` — **sabit 4/3 girişli dict**.
- `QUOTAS = {"Kızılova RES": 12, "Karatepe RES": 35}`, `_DISTRIBUTION_TARGETS = {"ankara_res": 45, "izmir_res": 15, "company": 10}` — sabit sayılar, yalnız 2 proje.
- `validate()` fonksiyonu — her proje için **elle yazılmış if-bloğu** (`if isinstance(ankara, ls.AnkaraLedger): check_chronology(...)`, `if isinstance(izmir, ls.IzmirLedger): ...`). Yeni bir proje eklemek = yeni bir if-bloğu yazmak.
- `check_cross_project_refs` — **ikili (pairwise)** hardcode: `for name, other in (("ankara_res", "izmir_res"), ("izmir_res", "ankara_res"))`. 7 proje için bu `O(N²)` elle yazılan tuple listesine çıkar — sürdürülemez.
- `IZMIR_POST_LICENCE_KEYS` — İzmir'e özel, lisans-sonrası alanların `None` olması gerektiğini kontrol eden sabit liste.

### 2.2 Önerilen tasarım — EKLEMELİ (additive), MEVCUT KODU DEĞİŞTİRMEDEN

609 testin tamamı `AnkaraLedger`/`IzmirLedger` sınıflarını, `"ankara_res"`/`"izmir_res"` anahtarlarını ve bu iki projenin **tam olarak bu şekilde var olduğunu** varsayıyor (fixture'lar, `load_ledger_raws()["ankara_res"]`, `ensure_generated_documents()` vb.). Bu iki sınığı/anahtarı **yeniden adlandırmak veya kaldırmak çok yüksek riskli** olur. Bunun yerine:

1. **Yeni, jenerik bir proje şekli ekle** (üçüncü bir seçenek, Ankara/İzmir şekillerinin YANINDA): `GenericDevelopmentLedger` / `GenericDevelopmentProject` — İzmir'inkiyle aynı "geliştirme aşaması, finance/construction None" şekli, ama proje koduna/adına Literal ile bağlı DEĞİL (serbest `code: str`, `name: str`). 5 yeni SPV (Yeşilova, Boztepe, Güneşalan, Akyar, Demirci) bu şekli kullanır — her biri kendi `seed_data/master/<kod>.yaml` dosyasında.
2. `LEDGER_FILES`/`PROJECT_PREFIX`, **`company.yaml`'ın `spvs` listesinden türetilir** (tek kaynak — zaten Adım 5'te `name_whitelist` için aynı prensip uygulandı). Sabit dict yerine `company.yaml` okunduktan sonra inşa edilen bir yapı. Ankara/İzmir'in özel girişleri (`"ankara_res": "ankara_res.yaml"`, kod `ANK`) **aynen kalır** — yalnızca 5 yeni girdi eklenir, hiçbiri silinmez/yeniden adlandırılmaz.
3. `validate()`'teki elle yazılmış if-bloklarının yanına, **yeni** bir döngü eklenir: `for code in GENERIC_PROJECT_CODES: check_generic_development_project(...)` — Ankara/İzmir'in özel branch'lerine hiç dokunmadan, sadece 5 yeni proje için minimal bir kontrol seti (G1 benzeri belge sayısı, D2 önek, C7-C9 tarih kontrolleri — zaten jenerik/raw-dict üzerinde çalışan fonksiyonlar, örn. `check_document_dates` zaten dosya-bağımsız).
4. `check_cross_project_refs` — ikili tuple yerine, **her dosya için "diğer TÜM projelerin önekleri"** taranacak şekilde genelleştirilir (`PROJECT_PREFIX`'teki kendisi hariç her girişi dolaşan bir döngü) — bu fonksiyonun KENDİSİ değişir (yeniden yazılır, ama DAVRANIŞI aynı kalır: hâlâ "başka projeye referans var mı" sorusunu soruyor, sadece artık N-1 projeyi kontrol ediyor, 1 değil). Mevcut Ankara/İzmir testleri (`test_cross_project_reference_is_error`) davranış değişmediği için yeşil kalır.
5. `_DISTRIBUTION_TARGETS`/`QUOTAS` — Ankara/İzmir'in sayıları **aynen kalır**; 5 yeni proje için ayrı, daha gevşek bir hedef (örn. "her biri ≥ 5 belge, ±%50 tolerans") eklenir, mevcut iki satır dokunulmaz.

### 2.3 Göç adımları (sıra)

1. `GenericDevelopmentProject`/`GenericDevelopmentLedger` şema sınıflarını ekle (yeni dosya veya `ledger_schema.py`'nin sonuna) — **mevcut hiçbir sınıf değişmez**.
2. 5 yeni SPV için `seed_data/master/<kod>.yaml` iskeletleri yaz (§2.4).
3. `validate_ledger.py`'ye yeni, additive bir `check_generic_development_project` fonksiyonu + `validate()`'e bir döngü ekle — mevcut if-bloklarının **üstüne**, aralarına değil.
4. `check_cross_project_refs`'i ikiliden N-yönlüye genelleştir (bu TEK mevcut fonksiyon değişir; davranışı pin'leyen mevcut test aynen geçmeli).
5. `LEDGER_FILES`/`PROJECT_PREFIX`'e 5 yeni girdi ekle (dict'in KENDİSİ, sabit değil, `company.yaml`'dan türetilmiş olabilir veya elle genişletilmiş 9 girdili bir dict olarak kalabilir — ikisi de "mevcut 2 girdiye dokunmama" şartını karşılıyor; SORU 3).
6. `make test` her adımdan sonra tek başına çalıştırılır; 609 test hiçbir noktada kırılmamalı (hepsi additive).

### 2.4 Yeni SPV ledger iskeleti (her biri için, `seed_data/master/<kod>.yaml`)

```yaml
# <Proje Adı> — truth ledger (Adım 5, Aşama B)
meta:
  schema_version: 1
  demo_today: 2026-10-06
  currency_note: "Finansman yok (geliştirme aşaması); tutar alanı yok."

project:
  code: <KOD>_RES|_GES
  name: <Proje Adı>
  stage: development
  spv:
    name: {value: "<Proje> Enerji Üretim A.Ş.", tag: USER_FACT}
    shareholders:
      - {name: {value: "XYZ Enerji A.Ş.", tag: USER_FACT}, share_pct: {value: 100, tag: USER_FACT}}
  capacity_mw:
    target: {value: <MW>, tag: USER_FACT, source_doc: null}
  turbines: null
  timeline: { ... IzmirTimeline ile aynı şekil, lisans-sonrası alanlar null ... }
  finance: null
  construction: null
  operations: null
  development: { ced_status, permits_completed, pending_steps, latest_event — Kızılova'nınkiyle aynı şekil }

documents: []  # Aşama B'de boş; Enerji/Hukuk partilerinde doldurulur
```

---

## 3. Kızılova RES finans/EPC modeli (LNTP, 30M USD imzalı-kullanılmamış kredi, EPC imzalı)

Tansu'nun Kızılova için verdiği gerçekler (ADIM5_PLAN.md §1.1/§1.3'ten): bir kredi ailesi **imzalı ama kullandırılmamış** ("Garanti BBVA 2026-KZ" referanslı, kurgusal adla kalacak — SORU 3, Adım 5 Aşama A), LNTP (Limited Notice to Proceed) verilmiş, mühendislik/tasarım ve türbin rezervasyonu yapılmış, ama **inşaat/kullandırım belgesi İKİSİ de yok** (İ-1 kararı — kasıtlı, kullandırım talebi/ilerleme raporu üretilmeyecek).

### 3.1 Şema değişikliği gereksinimi

`IzmirProject.finance: None` ve `.construction: None` **hard-type** — Pydantic seviyesinde bu alanlar her zaman `None` olmak zorunda (`Literal`'a benzer bir zorlama, `None` tipiyle). Bunu değiştirmeden Kızılova'ya "imzalı ama 0 kullandırılmış" bir `Finance` nesnesi veya "EPC imzalı ama inşaat başlamamış" bir `Construction` nesnesi **eklenemez**.

**İki seçenek:**
- **(A) `IzmirProject.finance`/`.construction` tipini `Finance | None`/`Construction | None` yap** (zaten `Finance`/`Construction` sınıfları var, Ankara'nınki) — ama Ankara'nın `Finance` şeması `drawdowns`/`covenant_tests`/`repayment_schedule`/`cfads_by_quarter` gibi **operasyonel** alanları zorunlu kılıyor (`list[Drawdown]`, boş liste olabilir ama alan yine de var olmalı) — Kızılova'nın "imzalı, hiç çekilmemiş" durumu için bu alanların çoğu anlamsız/boş kalır. Şemayı "kirletir."
- **(B) Yeni, daha hafif bir `SignedUndrawnFacility` şekli ekle** (`contract_amount`, `lenders`, `interest.base`, `signed_date`, `lntp_date` gibi yalnızca "imzalandı" durumuna ait alanlar; `drawdowns`/`covenant_tests`/`repayment_schedule` YOK). `IzmirProject.finance: SignedUndrawnFacility | None`. **Önerilen** — Ankara'nın operasyonel şemasını kirletmez, Kızılova'nın gerçek durumunu (imzalı-kullanılmamış) doğru temsil eder, ve 5 yeni SPV'den finansmanı olan biri çıkarsa (örn. Yeşilova, Boztepe — ADIM5_PLAN.md'de "4 kredi ailesi" deniyor, yani onlar da işletmede/kredili) aynı şekli paylaşabilir.

Aynı mantık `construction` için: Kızılova'nın EPC'si **imzalı**, inşaat **başlamamış** — `epc_contractor`/`epc_contract_price`/`epc_contract_current_doc` dolu olabilir ama `change_orders`/fiili ilerleme alanları yok. Benzer bir hafif `SignedUnstartedEpc` şekli önerilir.

### 3.2 Etkilenen belge türleri

- **Finans:** Facility Agreement (imzalı, `status: executed`, `version: EXECUTED` — ama `key_facts`'te `drawn_amount`/`outstanding` YOK, yalnızca `signed_amount`). LNTP mektubu (yeni tür). Kullandırım talebi/inşaat ilerleme raporu — **üretilmeyecek** (İ-1).
- **Enerji/EPC:** EPC Contract (imzalı). Türbin rezervasyon/tedarik mektubu (yeni tür, mühendislik/tasarım). Mühendislik/tasarım raporu.
- **Hukuk:** (ADIM5_PLAN.md §1.1'de ayrıca "Kızılova yüklenici ihtilafı (ihtarname)" var — bu EPC'nin imzalı ama inşaatın başlamamış olmasıyla ilgili bir anlaşmazlık senaryosu, bu planın kapsamı dışında, Hukuk partisinde ele alınacak.)

---

## 4. AI_ASSUMPTION denetimi — Aşama A'da türetilen her değer

Aşama A sırasında, Tansu'nun vermediği ama ledger'ın tutarlı olması için gereken değerler `AI_ASSUMPTION` etiketiyle türetildi. Aşağıdaki tablo, Aşama A'nın commit'inden (`aedb207`) çıkarılan **her** yeni `AI_ASSUMPTION` değerini listeler.

| Değer | Nerede kullanılıyor | Tansu'ya sorulacak mı? |
|---|---|---|
| Karatepe `capacity_mw.initial = 22 MW` | DOC-ANK-DEV-001 (Üretim Lisansı) key_fact; DOC-ANK-DEV-005 (ÇED) key_fact | **Evet** — Tansu yalnız güncel 24 MW'ı verdi; 22 MW tamamen icat, DOC-ANK-DEV-002'nin (Licence Amendment) anlatısını korumak için seçildi. Tansu'nun gerçek bir ilk kapasite rakamı varsa onunla değişmeli. |
| Karatepe `financing_signed`/`financial_close` = 2021-11-20 / 2021-11-25 | DOC-ANK-FIN-004, DOC-ANK-FIN-010/011/012/013 tarihleri | **Evet** — Tansu hiç tarih vermedi; `construction_start` (2022-01-10, değişmedi) ile kronolojik tutarlılık için seçildi. Gerçek bir imza tarihi varsa önemli ölçüde değişebilir. |
| Karatepe `capex = 20.000.000 USD`, `equity = 6.400.000 USD` | Financial Model workbook, DOC-ANK-FIN-004/010 key_facts | **Evet** — standart %70/30 borç/özkaynak oranından türetildi, Tansu'nun verdiği hiçbir rakama dayanmıyor. |
| Karatepe `grace_months = 10` | DOC-ANK-FIN-004 key_fact | **Düşük öncelik** — imza-ilk taksit boşluğundan türetildi, hiçbir eval sorusu veya F-kuralı buna dayanmıyor (bilgi amaçlı alan). |
| Karatepe `base_rate_pct_by_year` (14 satır, Term SOFR 2022-2035) | `debt_math.py` hesaplamalarının girdisi (F10) | **Hayır, muhtemelen gerekmez** — "fictional" olarak zaten etiketli (Phase 4.2'den devam eden bir desen, EURIBOR'un da fictional olduğu not edilmişti); gerçek SOFR geçmişi istenmiyor, iç tutarlılık yeterli. |
| Karatepe `repayment_schedule` 24 satırın 22'si (8. ve belirtilen anchor'lar hariç) | `debt_math.py` → outstanding/DSCR hesapları (F9-F11) | **Hayır** — Tansu'nun 2 anchor'ına (8. taksit 412.500 USD/07.10.2026, 9. taksit tarihi 07.04.2027) tam uyacak şekilde `debt_math.py` ile doğrulanarak türetildi; iç tutarlılık matematiksel olarak zorunlu, tek çözüm değil ama geçerli bir çözüm. |
| Karatepe `cfads_by_quarter` (11 satır) | `debt_math.py` → covenant_tests.dscr ile ≤0,01 tolerans eşleşmesi (F10) | **Hayır** — covenant_tests'in (Tansu'dan gelmeyen, önceki round'dan kalan) DSCR değerlerini üretecek şekilde ters türetildi. |
| `RST Turbines GmbH` (türbin tedarikçisi adı) | `construction.turbine_supplier`, DOC-ANK-OPS-010/011 | **Hayır** — SORU 3'ün (banka adı) mantığı OEM'e de uygulandı: kurgusal isim, Tansu gerçek bir marka istemedi/vermedi. |
| Karatepe `tenor_years.changed_by = DOC-ANK-FIN-006` (AMD* referansı, tenor fiilen değişmemesine rağmen) | F4 kuralının "changed_by bir AMD* belgesi olmalı" şartı | **Hayır** — yapısal bir zorunluluk (validator kuralı), gerçek bir veri varsayımı değil. |
| Kızılova `pre_licence_expiry` belge referansı (`doc: DOC-IZM-DEV-001`) | `timeline.pre_licence_expiry` | **Düşük öncelik** — Tansu tarihi (15.01.2027) verdi, hangi belgenin bunu taşıdığı (önlisans belgesinin kendisi mi, ayrı bir belge mi) varsayım. |
| 5 yeni SPV'nin `company.yaml`'daki kayıtları (ad, %100 XYZ hissedarlığı) | `CompanySpv` listesi | **Hayır** — ADIM5_PLAN.md §1.1'de Tansu'nun verdiği isimlerin doğrudan transkripsiyonu, ek varsayım yok. |

### 4.1 Tansu'ya taslak soru listesi (T-10) — **henüz gönderilmedi**

> **T-10.1 (Karatepe ilk kapasite):** Karatepe RES'in lisans alırken ilk onaylanan kapasitesi kaç MW'tı? (Şu an demo'da 22 MW olarak varsayıldı, güncel 24 MW'a bir kapasite tadili ile çıktığı anlatılıyor — bu anlatı gerekli mi, yoksa Karatepe hep 24 MW mı?)
> **T-10.2 (Karatepe finansman tarihi):** Karatepe'nin kredi sözleşmesi hangi tarihte imzalandı / financial close'a ulaştı?
> **T-10.3 (Karatepe capex/equity):** Karatepe'nin toplam capex ve özkaynak tutarları nedir (USD)? (Şu an %70/30 borç/özkaynak oranından türetildi.)
> **T-10.4 (Kızılova kredi/EPC detayları):** Kızılova'nın imzalı-kullanılmamış kredisinin ve EPC sözleşmesinin tam tutarları, taraf (banka/müteahhit) adları, imza tarihleri nedir?

---

## 5. Eval soruları — dayandığı bilgi artık var olmayan/değişen sorular

Aşağıdaki sorular, Aşama A'nın finansal yeniden yapılandırmasıyla **anlamsal temeli değişen veya zayıflayan** sorulardır (yalnızca görünen-ad değişen ~90 soru hariç — onlar Aşama A raporunda listelendi). **Hiçbiri henüz değiştirilmedi** — karar Naci'nin.

| ID | Soru | Eski dayanak | Yeni durum | Önerilen sınıf |
|---|---|---|---|---|
| ANK-FIN-004, ANK-NEG-002 | "...ECA kredisi ne kadar?" / "...ihracat kredi kurumu kredisi ne kadar?" | ECA 30M EUR ile gerçek bir kredi ortağıydı | `eca_debt = 0 USD` — belge bunu doğrudan anlatıyor ("export credit agency (ECA) facility of 0 EUR") | **(a) Olduğu gibi kalsın** (0, belge-temelli, SOURCE GROUNDING ile tutarlı) **veya (b) soruyu "ECA katılımı var mı?" biçimine çevir** (boolean/negatif-stil, "hayır" bekler) — Önerim: (b), çünkü "ne kadar?" sorup "0" cevabı almak bir kullanıcıya hata gibi görünebilir. |
| ANK-FIN-013, ANK-NEG-001, ANK-NEG-003 | "...tenor'u ilk ne kadardı, şimdi ne kadar?" / "...vadesi kaç yıl?" | Tenor 12→14 yıl GERÇEKTEN değişiyordu (iki farklı halka, iki farklı değer) | Tenor artık 13→13 (değişmiyor) — ANK-FIN-013'ün "iki değer birlikte" notu artık yanlış (tek değer var); ANK-NEG-001/003'ün "model 12 ve 14'ü birlikte verirse 14 geçmeli" notu da geçersiz (tek değer, ambiguity yok) | **ANK-FIN-013: soruyu kaldır veya başka bir initial≠current alana (örn. DSCR 1,25→1,20) çevir** (Önerim: DSCR'a çevir — zaten test_eval_lib.py'da bu değişikliği yaptım, ANK-FIN-013'ün KENDİSİ hâlâ tenor soruyor). **ANK-NEG-001/003: notu güncelle, soru/beklenti aynı kalabilir** (tenor hâlâ bir "vade" sorusu, yalnızca tek değerli — negatif kontrol amacı bozulmuyor). |
| ANK-FIN-015 | "...ilk kredi çekim bildiriminde belirtilen tutar nedir?" | Not alanı "ilk çekim 2021-12-15, 15.000.000 EUR" diyor (sabit metin) | Gerçek değer artık 2022-07-15, 8.000.000 USD (yol otomatik çözülüyor, SORUN YOK) — yalnızca `notes` alanı (insan-okur dokümantasyon, skor etkilemiyor) yanlış | **Not metnini güncelle** (kozmetik, düşük öncelik). |
| ANK-FIN-007 | "...ilk (orijinal) DSCR covenant'ı neydi?" | DSCR her zaman 1,25 idi (değişmedi) | Değişmedi, ama kaynak belge (DOC-ANK-FIN-004) artık farklı tarihli/isimli | **Değişiklik gerekmiyor**, yalnız bilgi amaçlı. |
| GEN-AMB-002 | "Raporda belirtilen DSCR değeri kaç?" (ambiguous, dev AMB seti) | Zaten Aşama A raporunda "korpus-gereği gerçekten belirsiz değil" olarak not edilmişti (İzmir'de hiç Covenant Report yok) | Değişmedi — bu madde **yeni** bir bulgu değil, Aşama A'nın bilinen sınırlaması; burada yalnız hatırlatma amaçlı. | Değişiklik önerilmiyor (Adım 4'ün kararı geçerli: kriter gevşetilmez). |

**Not:** Yukarıdaki tablo **öneri** sunuyor, hiçbirini uygulamadım. "Sessizce 0 beklentisine çevirme" talimatına uyarak ANK-FIN-004/ANK-NEG-002'nin mevcut hâli (0 USD, otomatik çözülüyor) **değiştirilmedi** — Naci'nin SORU 4'teki kararına göre (a) olduğu gibi bırakılacak ya da (b) yeniden yazılacak.

---

## 6. `check_conflict_groups` birim testleri (TEK kod değişikliği bu round'da)

`backend/tests/test_validate_ledger.py`'ye 6 yeni test eklendi:
- `find_conflict_groups`'un saf fonksiyon davranışı (iç içe dict/liste gezintisi, path inşası, `deliberate_conflict` bayrağının doğru taşınması) — dosya I/O'suz, sentetik bir ağaç üzerinde.
- Boş ağaç için boş sonuç.
- İki farklı DOSYA arasında bir grubun birleşebildiği (cross-file aggregation).
- Gerçek Karatepe ledger'ı mutasyonla bozularak: tek üyeli grup hatası, `deliberate_conflict` eksik üye hatası, yazım hatalı grup adının iki tekil gruba bölünmesi (her ikisi de hata vermeli).

`make lint`: temiz. `make test` (tek başına, 900s): **çalışıyor** — sonuç bu raporun sonunda (§7).

---

## 7. SPEC_05 §4 isim listesi — tamamlandı (yalnız doküman)

`docs/SPEC_05_synthetic_veri_ve_evaluation.md` §4, Adım 5'in yeni isim listesiyle güncellendi: holding (XYZ Enerji A.Ş.), 7 SPV, RST Turbines GmbH, mevcut diğer taraflar (JKL/MNO/PQR/VWX/STU/KLM) ve GHI'nin tarihsel-referans notu. **Not:** §6 (dağılım, "Ankara ≈ 45, İzmir ≈ 15"), §8 (proje karıştırma testi), §9'un örnek JSON'u (`"Ankara RES"`) hâlâ eski adları taşıyor — bu plan yalnız §4'ü kapsadığı için **dokunulmadı**, ayrı bir doküman geçişi olarak flaglanıyor (SORU 5).

---

## 8. Kapsam kesinleştirmesi (uygulandı, bu plan boyunca)

- **Canlı DB'ye dokunulmadı** — hiçbir `docker compose run`/`exec`, test DB dışında bir `DATABASE_URL` kullanmadı.
- **Canlı Gemini çağrısı yapılmadı.**
- **main'e birleştirme yok.**
- `EK_F_MODE`/`ASSIST_MODE`: `.env`'de ve çalışan backend sürecinde `false` olarak yeniden doğrulandı (§9).

---

## 9. SORU (Naci cevaplamalı)

1. **demo_today (§1):** 06.10.2026'ya geçince `covenant_tests`/`cfads_by_quarter`'a bir Q3_2026 satırı eklensin mi (demo_today'e daha yakın bir "son rapor" için), yoksa Q2_2026 "son bilinen rapor" olarak kalsın mı? Önerim: **Q2_2026 kalsın** — Tansu yeni bir çeyrek verisi vermedi, icat etmek yeni bir AI_ASSUMPTION katmanı ekler; "son rapor Temmuz'da" demo için yeterli bir gerçeklik.
2. **demo_today uygulama zamanı:** Bu değişiklik Aşama B'nin parçası olarak **şimdi** mi uygulansın (kod yok dediniz ama bu saf veri/config değişikliği, "kod" sayılmıyor gibi duruyor — netleştirme istiyorum), yoksa yalnızca bu planın onayı + ayrı bir "Aşama C" implementasyon turu mu bekleniyor? Önerim: **ayrı bir uygulama turu** — demo_today'in etki alanı (§1.1 tablosu) tek başına dikkatli bir doğrulama turu gerektiriyor, Aşama B'nin diğer maddeleriyle karıştırılmasın.
3. **Şema genelleştirmesi (§2.3 madde 5):** `LEDGER_FILES`/`PROJECT_PREFIX` `company.yaml`'dan **dinamik türetilsin** mi (daha az tekrar, ama `validate_ledger.py`'nin `company.yaml`'ı en-başta-okuma sırasına bağımlı hâle gelmesi riski) yoksa **elle 9 girdili bir dict** olarak mı genişletilsin (daha basit, ama "tek kaynak" ilkesini kısmen bozar)? Önerim: **elle genişletme** — Aşama B'nin "609 testi asla kırma" önceliğiyle en uyumlu, en az sürpriz.
4. **ANK-FIN-004/ANK-NEG-002 (ECA kredisi, §5):** (a) olduğu gibi (0 USD, belge-temelli) mi kalsın, yoksa (b) "ECA katılımı var mı?" biçiminde yeniden mi yazılsın? Önerim: **(b)**.
5. **SPEC_05 §6/§8/§9 (§7):** bu planın kapsamı dışında bırakıldı — ayrı bir doküman geçiş turu açılsın mı, yoksa Adım 5 tamamen bitene kadar beklesin mi? Önerim: **Adım 5 bitene kadar beklesin** — belge sayıları (§6) ve örnekler (§9) henüz nihai değil (yeni partiler geldikçe değişecek), tek seferde güncellemek daha verimli.
6. **Şema genelleştirmesinin (§2) ve Kızılova finans/EPC modelinin (§3) UYGULANMASI:** bu plan onaylandıktan sonra hangi partiyle başlasın — Enerji/Hukuk/Mali partilerinden ÖNCE bir "Aşama C: şema genelleştirmesi" turu mu, yoksa Mali partisi başlarken mi (ihtiyaç anında)? Önerim: **Mali partisi başlamadan önce, ayrı bir Aşama C** — Kızılova'nın finans modeli olmadan Mali partinin "4 kredi ailesi" hedefinin 2'si (Kızılova dahil) baştan eksik kalır.

---

**Bu plan onaylanana kadar hiçbir uygulama adımı başlamaz.** Push edildi, dur.
