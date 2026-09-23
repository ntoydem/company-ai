# Phase 2.1 Raporu — Truth ledger + validator + golden questions v1

**Tarih:** 23.09.2026  **Model:** Claude Fable 5.1  **Tag:** phase-2-1  **Commit:** `git rev-list -n1 phase-2-1`

> **ONAY KAPISI (SORU 4 cevabı):** Bu faz `phase-2-1` tag'inde **taslak** olarak kapandı — 269 değerin tamamı `AI_ASSUMPTION`. **Ledger onayı: 23.09.2026** — Naci ve enerji finansı ortağı taslağı **değişiklik olmadan** onayladı (İzmir'in PARTNER-REVIEW satırları dahil); 269 değerin tamamı ayrı bir "ledger onayı" commit'inde (`git log --grep 'ledger onayı'`) `USER_FACT` yapıldı, `make validate-ledger` → `USER_FACT=269 AI_ASSUMPTION=0`, 0 hata. Adım 3.1 kapısı **açık** (SPEC_05 §2 madde 8–10).

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | validator 0 hata | ✅ | `make validate-ledger` → `0 error(s), 0 warning(s)`; `tests/test_validate_ledger.py::test_master_ledger_validates_clean` |
| 2 | Ankara zinciri (DRAFT→V01→V02→EXECUTED→AMD01→AMD02) ledger'da | ✅ | `ankara_res.yaml` `project.finance.facility_chain` + `documents` DOC-ANK-FIN-001…006; kural F6 (`::test_facility_chain_is_linear_and_complete`, `::test_facility_chain_must_have_single_current_link`) |
| 3 | Ankara 3. işletme yılı `DEMO_TODAY`'e göre | ✅ | kural C6 yıldönümü bazlı hesaplar ve `operating_year_on_demo_today` ile karşılaştırır (`::test_operating_year_is_anniversary_based`, `::test_cod_outside_third_year_window_is_error`) |
| 4 | İzmir COD/lisans/finansman `null` | ✅ | şema (`IzmirTimeline` post-licence alanları `None`) + kural I1 (`::test_izmir_post_licence_fields_must_be_null`, `::test_izmir_cannot_carry_finance_documents`) |
| 5 | her tutarda para birimi | ✅ | `Money` modeli `currency` zorunlu (`::test_money_without_currency_is_error`) |
| 6 | ≥ 30 soru (İzmir ≥ 9, Ankara ≥ 20, hallucination ≥ 3, isolation ≥ 3, authorization ≥ 3) | ✅ | 43 soru: Ankara 29, İzmir 13, hallucination 4, isolation 4, authorization 3 (örtüşme kuralı, plan T7); kural Q2 (`::test_question_quotas`) |

## 2. Yapılanlar
- `seed_data/master/{company,ankara_res,izmir_res,fx_rates}.yaml` — taslak ledger, 269 etiketli değer, hepsi `AI_ASSUMPTION`.
- `seed_data/generator/ledger_schema.py` — Pydantic v2 şeması (`extra="forbid"`; `Fact/Money/Event` + etiketli kayıtlar; İzmir'de lisans sonrası alanlar tipte `None`).
- `seed_data/generator/validate_ledger.py` — `python -m seed_data.generator.validate_ledger [--summary]`; kurallar C1–C10 (kronoloji), F1–F8 (finans), I1–I3 (İzmir izolasyonu), M1–M2 (para birimi), N1–N3 (isim whitelist), D1–D2 (belge kimlikleri/slug), G1, Q1–Q5 (questions.json). Exit 0 ⇔ 0 hata.
- `seed_data/evaluation/questions.json` v1 — 43 soru, `expected_answer` = `ledger:<dosya>.<yol>` (SORU 7).
- `backend/tests/test_validate_ledger.py` — 21 test: gerçek ledger temiz + her kural için "bir şeyi boz, kural ateşlensin" (geçici değerlerle, demo rakamı assert edilmez).
- `make validate-ledger` hedefi; `make lint` de validator'ı çalıştırıyor. `pyyaml` dev grubuna eklendi.
- SORU cevapları uygulandı: AMD02 finansal olmayan (geri ödeme takvimi eki / covenant test dönemi tanımı); tek `licence_amendment`, "Licence Amendment 01"; fx yıllık ortalama + spot; DRAFT/EXECUTED/AMD01/AMD02 `generate_in_phase: 3.1`, V01/V02 `5.1`; operasyon serileri tam (COD → `DEMO_TODAY`: 34 ay üretim, 11 çeyrek bütçe, 11 covenant testi).

## 3. Değişen dosyalar
Yeni: `seed_data/__init__.py`, `seed_data/generator/{__init__,ledger_schema,validate_ledger}.py`, `seed_data/master/*.yaml` (4), `seed_data/evaluation/questions.json`, `backend/tests/test_validate_ledger.py`. Değişen: `Makefile`, `README.md`, `backend/pyproject.toml`, `backend/uv.lock`, `docs/ARCHITECTURE.md` (ADR-013 notu), `docs/PHASES.md`.

## 4. Testler
- Backend: **149 geçti** (21'i validator), 3 atlandı (`live_llm`). ocr-worker: 9 geçti. `assert-pipeline-schema`: geçti.
- `make lint`: ruff/format/mypy temiz; prompt-doc güncel; validator 0 hata.
- `make validate-ledger --summary`: `tags: USER_FACT=0 AI_ASSUMPTION=269`, `0 error(s), 0 warning(s)`.
- Migration: yok (ledger uygulama DB'sine girmez — DOMAIN_MODEL §4).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Şema Pydantic v2 (`jsonschema` yok) | Zaten bağımlılık; `extra="forbid"` yazım hatasını yakalıyor | Generator/Excel aynı modelleri kullanabilir |
| Etiket: her `Fact/Money/Event`/liste kaydında zorunlu `tag`; kimlik anahtarları etiketsiz | SPEC_05 §3 tutarsızdı (plan T2) | Validator eksik etiketi hata sayar |
| `documents[].department` DB slug'ı (`finans`), SPEC örneğindeki `finance` değil | Phase 1.2 slug kümesiyle tutarlılık | `questions.json.expected_department` de slug |
| `questions.json` yolu `seed_data/evaluation/` | SPEC_05 §1 + `.gitignore` | Kök `evaluation/` açılmadı |
| `key_facts` ve `expected_answer` değer değil ledger yolu | Tek doğruluk kaynağı; senkron sorunu yok | Phase 3.1 generator ve 4.1 runner yolu çözer (`[-1]` desteklenir) |
| İşletme yılı yıldönümü bazlı (`floor((demo_today−cod)/365.25)+1`) | Spec tanımsızdı (T10) | COD, `DEMO_TODAY`'den 2–3 yıl önce olmalı |
| `company.yaml`'a `name_whitelist` + `public_institutions` | Whitelist'in yeri tanımsızdı (T12) | N1 taraması bu listeye bakar |
| AMD02 `status: executed`, öncekiler `superseded`/`draft` | "Güncel belge tek" (DOMAIN_MODEL §6) | F6 tam olarak son halkayı güncel sayar |
| Envanter yalnızca Phase 3.1'in 15 belgesi + V01/V02/Change Order (5.1) | YAGNI; ~70 belge 5.1'de | G1 uyarısı 15'i sayar |
| `data`/`mixed` kategorileri boş | Excel Phase 4.2 | Kota yok |

## 6. Açık sorular (Naci cevaplamalı)
Yok — §10 onay tablosu dışında. (SORU 1–8 uygulandı.)

## 7. Riskler / sonraki phase için notlar
- **PARTNER-REVIEW (SORU 6) — kapandı:** İzmir'de tamamlanmış sayılan adımlar *Önlisans + Arazi Edinimi (kısmi)*, ÇED devam, kalan 8 adım bekliyor — ortak 23.09.2026'da onayladı (`USER_FACT`).
- Ledger onaylanınca Adım 0'ın geçici T0 seti (`seed_data/t0/`, `tests/live/test_t0_live.py`'deki değerler) Phase 3.1'de kaldırılır; T0 değerleri ledger'ı bağlamaz (plan T11). Bu taslakta DSCR/tenor değerleri T0 ile aynı seçildi (SPEC_05 §3/§9 örnekleriyle uyumlu), ama onayda değişebilir.
- `key_facts` ve `expected_answer` yolları ledger yeniden düzenlenirse (örn. covenant testi eklenince `[10]` indeksi kayar) kırılır — validator F8/Q4 yakalar; sabit indeks yerine `[-1]` tercih edildi, yalnızca DOC-ANK-FIN-007/OPS-001 sabit indeks kullanıyor.
- İsim taraması (N1) yalnızca `A.Ş./Ltd./Bank/Sigorta/GmbH/S.A./Inc.` sonekli kalıpları yakalar; soneksiz gerçek isimler (kişi adı vb.) yakalanmaz — Phase 5.1 `validate_dataset.py` "Demo Safety" burada genişletmeli.
- Phase 3.1 not: `DOC-ANK-EPC-003` (Change Order) `5.1`'de üretileceği için "COD neden sapmış?" sorusuna (ANK-EPC-004) 3.1 setinde "belirtilmemiş" cevabı kabul edilir.
- Phase 4.1 not: `expected_answer` yolları `ledger:` ile başlar; runner `resolve_path` benzeri bir çözücü ve biçim normalizasyonu (`1,20x/1.20/1,2`) gerektirir; `expected_answer_aliases` v1'de boş.

## 8. Doğruladığım üçüncü taraf davranışları
- PyYAML 6.0.3 `safe_load`: ISO tarih skalerlerini `datetime.date`'e çevirir (şema `date` tipini doğrudan alır); **flow mapping içinde `[`** (`{k: a[0].b}`) sequence olarak parse edilir — yol referansları tırnaklanmalı (ilk çalıştırmada yakalandı, düzeltildi; validator artık YAML hatasını `ERROR <dosya> <file>` olarak raporluyor, traceback vermiyor).
- Pydantic v2 `Literal[None]`/`None` tipli alan: doldurulmuş değeri "Input should be None" ile reddediyor — İzmir izolasyonunun şema katmanı; kural I1 ayrıca okunur mesaj veriyor.
- Python 3.12 PEP 695 generic fonksiyon (`def parse_model[M: BaseModel]`) ruff `target-version=py312` ile sorunsuz.

## 9. Kaynak kullanımı
- LLM çağrısı yok. Validator tek çalıştırma < 1 sn; `test_validate_ledger.py` 21 test ≈ 10 sn (her test master klasörünü kopyalar).

## 10. Onay tablosu — `AI_ASSUMPTION` → `USER_FACT`
**Durum: tamamı onaylandı, 23.09.2026, değişiklik yok** (☐ kutuları tarihsel kayıt olarak bırakıldı; her satır `USER_FACT`). İzmir'in PARTNER-REVIEW satırları ortak tarafından onaylandı. Seriler (aylık üretim, bütçe, kur) dosyada satır satır; burada özet.

### 10.1 Şirket (`company.yaml`)
| Alan | Taslak değer | Onay |
|---|---|---|
| Holding | ABC Enerji A.Ş. | ☐ |
| Ankara SPV / paylar | DEF Enerji Üretim A.Ş. — ABC Enerji %80, GHI Yatırım %20 | ☐ |
| İzmir SPV / paylar | DEF İzmir Rüzgar Enerji A.Ş. — ABC Enerji %100 | ☐ |
| Yerli banka / ECA | PQR Bank / VWX Export Credit Agency | ☐ |
| EPC / türbin / danışman / sigorta / hukuk | JKL İnşaat A.Ş. / XYZ Wind Turbines GmbH / MNO Teknik Danışmanlık Ltd. / STU Sigorta / KLM Hukuk Bürosu | ☐ |
| Board Resolution (DOC-CO-ADM-001) | 15.09.2021, Ankara RES finansman onayı, TR, `board` gizlilik | ☐ |

### 10.2 Ankara RES — teknik
| Alan | Taslak değer | Onay |
|---|---|---|
| Lisans kapasitesi (ilk) | 48 MW | ☐ |
| Kapasite (güncel, tadil sonrası) | 60 MW | ☐ |
| Türbin | 12 × 5 MW sınıfı kara tipi | ☐ |

### 10.3 Ankara RES — zaman çizelgesi
| Olay | Taslak tarih | Onay |
|---|---|---|
| Development başlangıcı | 01.03.2018 | ☐ |
| Önlisans | 20.11.2018 | ☐ |
| Üretim lisansı (DOC-ANK-DEV-001) | 15.06.2020 | ☐ |
| Licence Amendment 01 — kapasite 48→60 MW (DOC-ANK-DEV-002) | 10.02.2021 | ☐ |
| Facility Agreement DRAFT / V01 / V02 | 15.06.2021 / 20.07.2021 / 25.08.2021 | ☐ |
| Facility Agreement EXECUTED (financing_signed) | 30.09.2021 | ☐ |
| EPC imzası | 20.10.2021 | ☐ |
| Financial close | 15.11.2021 | ☐ |
| İnşaat başlangıç / bitiş | 10.01.2022 / 31.08.2023 | ☐ |
| Change Order 01 — COD ertelemesi (şebeke bağlantı işleri) | 12.05.2023 | ☐ |
| COD ilk beklenen | 30.06.2023 | ☐ |
| Commissioning | 20.09.2023 | ☐ |
| COD gerçekleşen = operasyon başlangıcı | 15.10.2023 (→ 15.09.2026'da 3. yıl) | ☐ |
| Facility AMD01 — DSCR 1,25→1,20x, tenor 12→14 yıl | 15.03.2025 | ☐ |
| Facility AMD02 — finansal olmayan (geri ödeme eki / covenant dönem tanımı) | 20.02.2026 | ☐ |
| Covenant Report Q2 2026 (DOC-ANK-FIN-007) | 20.07.2026 | ☐ |
| Aylık Üretim Raporu Ağustos 2026 (DOC-ANK-OPS-001) | 05.09.2026 | ☐ |

### 10.4 Ankara RES — finansman (EUR)
| Alan | Taslak değer | Onay |
|---|---|---|
| Capex | 72.000.000 | ☐ |
| Equity | 21.600.000 (%30) | ☐ |
| Toplam borç | 50.400.000 (%70) | ☐ |
| Yerli banka / ECA | 20.400.000 / 30.000.000 | ☐ |
| Faiz | EURIBOR 6M + %3,25 | ☐ |
| Tenor ilk / güncel | 12 / 14 yıl (AMD01) | ☐ |
| Grace | 24 ay | ☐ |
| Geri ödeme profili | Sculpted, 6 aylık taksit | ☐ |
| DSCR covenant ilk / güncel | 1,25x / 1,20x (AMD01) | ☐ |
| Drawdown'lar | 15.12.2021 15,0M; 30.06.2022 15,0M; 15.12.2022 12,0M; 30.06.2023 8,4M (Σ 50,4M) | ☐ |
| Outstanding (15.09.2026) | 44.100.000 | ☐ |
| Covenant testleri (11 çeyrek, Q4_2023→Q2_2026) | 1,42 · 1,38 · 1,31 · 1,27 · **1,24 (fail, Q4_2024 — AMD01'i tetikler)** · 1,23 · 1,29 · 1,33 · 1,36 · 1,34 · 1,37 | ☐ |
| EPC bedeli | 41.500.000 | ☐ |

### 10.5 Ankara RES — operasyon
| Alan | Taslak değer | Onay |
|---|---|---|
| Aylık üretim (34 ay, 2023-11→2026-08) | CF %24–39 mevsimsel, availability %96–98; 2024-07 arıza ayı %91,4 — `ankara_res.yaml` `monthly_production` | ☐ |
| Bütçe vs gerçekleşen (TRY, 11 çeyrek) | çeyreklik OPEX 18,5M (2023) → 26M (2024) → 34,5M (2025) → 42M (2026); gerçekleşen ±%6 | ☐ |
| Olaylar | 08.07.2024 türbin dişli kutusu arızası (T-07, 11 gün); 22.01.2025 şebeke kesintisi (2 gün) | ☐ |

### 10.6 İzmir RES — **PARTNER-REVIEW gerekli**
| Alan | Taslak değer | Onay |
|---|---|---|
| Hedef kapasite | 80 MW | ☐ |
| Development başlangıcı | 01.02.2023 | ☐ |
| Önlisans başvurusu / önlisans (DOC-IZM-DEV-001) | 10.05.2023 / 18.01.2024 | ☐ |
| Arazi edinimi başlangıcı / durum raporu (DOC-IZM-DEV-002) | 02.04.2024 / 30.09.2024 (kısmi) | ☐ |
| Teknik rapor (DOC-IZM-DEV-004) | 20.01.2025 | ☐ |
| ÇED başvurusu | 05.03.2025 | ☐ |
| ÇED durumu / en son gelişme (DOC-IZM-DEV-003) | ongoing / 27.08.2026 İDK toplantısı, ek bilgi talebi | ☐ |
| **Tamamlanan adımlar (PARTNER-REVIEW)** | Önlisans (18.01.2024), Arazi Edinimi — kısmi (30.09.2024) | ☐ ortak |
| **Bekleyen adımlar (PARTNER-REVIEW)** | ÇED (devam), İmar Kesinleşme, Kat'i Proje Onayı, Bağlantı Anlaşması, Askeri Yasak Yazısı, TEA Yazısı, Yapı Ruhsatı, Üretim Lisansı | ☐ ortak |
| Lisans / finansman / FC / EPC / inşaat / COD / operasyon | `null` (tasarım gereği; onay konusu değil) | — |

### 10.7 FX (`fx_rates.yaml`, kurgusal)
| Dönem | EUR/TRY | USD/TRY | EUR/USD | Onay |
|---|---|---|---|---|
| 2018 / 2019 / 2020 | 5,67 / 6,35 / 8,03 | 4,81 / 5,67 / 7,02 | 1,1788 / 1,1199 / 1,1439 | ☐ |
| 2021 / 2022 / 2023 | 10,44 / 17,38 / 25,76 | 8,86 / 16,55 / 23,75 | 1,1783 / 1,0501 / 1,0846 | ☐ |
| 2024 / 2025 / 2026 (ort.) | 35,55 / 41,20 / 46,80 | 32,85 / 37,90 / 43,10 | 1,0822 / 1,0871 / 1,0858 | ☐ |
| 15.09.2026 spot | 47,35 | 43,60 | 1,0860 | ☐ |

### 10.8 Belge envanteri (15 belge Phase 3.1'de üretilir, 3 belge 5.1)
Ankara: DEV-001 Üretim Lisansı (tr, taranmış), DEV-002 Licence Amendment 01 (tr), FIN-001 Draft, FIN-004 EXECUTED, FIN-005 AMD01, FIN-006 AMD02, FIN-007 Covenant Report Q2 2026 (hepsi en), EPC-001 EPC Contract (en), EPC-002 COD Certificate (en, taranmış), OPS-001 Üretim Raporu (tr); 5.1: FIN-002 V01, FIN-003 V02, EPC-003 Change Order 01. İzmir: DEV-001 Önlisans (tr, taranmış), DEV-002 Arazi Edinim Raporu, DEV-003 ÇED Durum Yazısı, DEV-004 Teknik Rapor (tr). Company: ADM-001 Board Resolution (tr, taranmış, `board`). Tüm Facility/EPC/lisans belgeleri `normal` gizlilik (finans/enerji kullanıcıları soruları cevaplayabilsin diye). ☐
