# Phase 5.1 — Tam dataset (~70) + consistency checks: Implementation Plan

## Bağlam ve tespitler

Okunanlar: `docs/PHASES.md` (Phase 5.1 + 4.3'ün ertelediği notlar), `docs/SPEC_05_synthetic_veri_ve_evaluation.md` (tamamı), `docs/reports/PHASE_4_3_REPORT.md` §7/§8, ve kod: `seed_data/master/{ankara_res,izmir_res,company,fx_rates}.yaml`, `seed_data/generator/{ledger_schema,validate_ledger,document_specs,generate_documents,validate_documents,generate_prose,facts,generate_excel,validate_excel,debt_math}.py`, `backend/app/services/{demo_departments_seed,demo_users_seed,demo_documents_seed}.py`, `backend/tests/test_demo_documents_seed.py`, `scripts/{seed_demo.sh,eval_lib.py,run_eval.py}`, `seed_data/evaluation/questions.json`, `docs/ARCHITECTURE.md` ADR-013.

### Tespitler (T)

- **T1 — Ledger şeması Phase 5.1'i zaten bekliyor.** `Document.id` pattern'i `DOC-(ANK|IZM|CO)-(DEV|FIN|EPC|OPS|LEG|ADM)-\d{3}` — **LEG** (Hukuk) ve **ADM** (İdari/Mali) grupları hiç kullanılmamış olsa da şemada zaten var. `GeneratePhase` zaten `"5.1"` değerini taşıyor ve **3 belge zaten `generate_in_phase: "5.1"` ile ledger'da tam olarak var**: `DOC-ANK-FIN-002` (Facility V01), `DOC-ANK-FIN-003` (Facility V02), `DOC-ANK-EPC-003` (Change Order 01) — tarih, taraf, `key_facts` dahil eksiksiz. Bunlar için yeni ledger girişi gerekmiyor, yalnızca `document_specs.py` + prose + render.
- **T2 — `validate_dataset.py` diye ayrı bir dosya yok; SPEC_05 §11'in kategorileri zaten `validate_ledger.py`'de fonksiyon fonksiyon var** (ADR-013 bunu zaten söylüyor): Chronology→`check_chronology`/`check_izmir_timeline`/`check_document_dates` (C1-C10), Finance→`check_finance`/`check_debt_schedule` (F1-F11), Project Isolation→`check_izmir_isolation`/`check_cross_project_refs` (I1-I3), Demo Safety→`check_names` (N1-N3). **Technical, Legal (amendment↔related) ve Version (tek güncel belge) kategorileri eksik veya yalnızca Facility zincirine özel (F6).** Yeni bir `validate_dataset.py` dosyası açmak yerine (spec adı ile kod adı arasındaki bu ayrım zaten kabul edilmiş bir sapma) `validate_ledger.py`'ye üç yeni fonksiyon ekleniyor: `check_version_links` (genel supersedes/superseded_by karşılıklılığı + zincir başına tek güncel belge — F6'nın Facility-özel halinin genellenmişi), `check_technical` (türbin sayısı × sınıf kapasitesi ≈ `capacity_mw.current`), `check_document_distribution` (SPEC_05 §6 dağılımı: ≤80 sert tavan ERROR, proje/departman kova aralıkları ve 8-10 taranmış PDF WARNING).
- **T3 — `hand_edited:` koruması kod değişikliği gerektirmiyor.** 6 dosya işaretli (`DOC-ANK-DEV-001/FIN-001/FIN-004/FIN-005/EPC-002`, `DOC-IZM-DEV-003`) — hiçbiri bu fazda dokunulan/yeni belge değil. `generate_prose.py --only <52 yeni id>` kullanmak yeter; `is_hand_edited()` zaten korur, `--force` bile ezmez.
- **T4 — "3.1" hardcode'u dört yerde.** `generate_documents.py` (`_nearest_generated`, `_revision_rows`, `related_refs` filtresi, ana döngü) yalnızca `generate_in_phase == "3.1"` render eder; `validate_documents.py::validate_generated` `len(entries) != 15` (G6) sabit sayı kontrolü yapar. İkisi de genellenecek: `GENERATED_PHASES = {"3.1", "5.1"}` sabiti + G6'nın sabit-sayı dalı kaldırılıp yalnızca `manifest_ids == expected_ids` (zaten var) + yeni `check_document_distribution`'ın ≤80 kontrolüne bırakılıyor.
- **T5 — `document_specs.py` 254 satır/15 belge ≈ 17 satır/belge; 70 belgede ≈ 1200 satır olur** (CLAUDE.md: 400+ satırlık dosya istenmiyor). Tek dosya yerine `seed_data/generator/document_specs/` paketi: `ankara_development.py`, `ankara_finance.py`, `ankara_epc.py`, `ankara_operations.py`, `ankara_legal.py`, `ankara_admin.py`, `izmir.py`, `company.py`, her biri kendi `SPECS: dict[str, DocumentSpec]` parçasını export eder; `__init__.py` hepsini birleştirip `SPECS` adıyla dışa verir (`dataclass`lar aynı `document_specs.py::DocumentSpec`'te kalır, artık `_base.py`'de).
- **T6 — Yeni belgelerin çoğu yeni bir ledger rakamı gerektirmiyor.** 52 yeni belgenin `key_facts`'i mevcut alanlara işaret edecek (ör. Waiver Letter → `covenant_tests[4]`, Bakım Raporu → `incidents[0]` + `monthly_production[8]`). Sıfır yeni whitelist adı gerekiyor: Hukuk belgeleri "KLM Hukuk Bürosu" (zaten `company.yaml`'da `legal_counsel`), sigorta belgeleri "STU Sigorta" (zaten `insurer`) kullanıyor — ikisi de zaten whitelisted ama şu ana kadar hiçbir belgede kullanılmamıştı. Birkaç yeni `key_facts` adı (`incident_type`, `waiver_reason` gibi) `facts.py::_FIELD_KIND`'a metin-geçişli (mevcut `repayment_profile` deseni) yeni giriş ister — rakam değil, biçimlendirme kuralı.
- **T7 — Temmuz 2024 arızası, Q3 2024 bütçe sapmasının "pozitif sebep" örneğini hiç yeni rakam eklemeden çözüyor.** `incidents[0]` (2024-07-08, T-07 dişli kutusu arızası, 11 gün duruş) ile `monthly_production[8]` (2024-07, 12.553 MWh, availability %91,4 — çevresindeki aylara göre düşük) zaten ledger'da, birbirine hiç bağlanmamış. Yeni `DOC-ANK-OPS-005` ("Bakım Raporu — Temmuz 2024") bu ikisini anlatan bir belge; `ANK-MIX-002` artık **cevaplı** (sebep belgede var) olacak şekilde güncellenecek. **Ocak 2025 şebeke kesintisi (`incidents[1]`) bilerek belgelenmiyor** — "sebep belgede yok" negatif örneği için yeni bir çeyrek (Q1 2025) kullanılacak, kod değişikliği gerekmiyor (zaten belgesiz).
- **T8 — `general` kategorisi mevcut `check_questions`'ın Q4 kuralıyla çelişiyor.** Bugün: `expect_no_answer=False` VE `expected_answer=None` olan bir soru hataya düşer ("answerable question needs an expected_answer") — GENERAL sorular tam olarak bu şekli istiyor (cevaplanır ama ledger'dan gelen bir değeri yok). `check_questions` bu kural için `category == "general"` istisnası alacak. `eval_lib.py::resolve_expected`/`score_question`'a da `general` için ayrı bir dal gerekiyor: `passed = outcome.answered and outcome.query_type == "GENERAL_QUERY" and not outcome.cited_titles and not outcome.cited_files` (ledger değer kontrolü yok — zaten `Question.expected_answer=None`).
- **T9 — Backend'de sabit sayı varsayan tek yer `test_demo_documents_seed.py`** (`15`, `19`); `scripts/seed_demo.sh`'deki `wait-for-documents --timeout 600` 70 belge + 9 taranmış OCR için biraz dar olabilir (Phase 3.1'de 15 belge için ölçülmemiş kesin süre var ama RAM/disk kullanımı ihmal edilebilir düzeydeydi — bkz. PHASE_3_1_REPORT §9). `Makefile`/`validate_ledger.py`'deki `MIN_QUESTIONS=30`, `QUOTAS={"İzmir RES":9,"Ankara RES":20}`, `CATEGORY_QUOTAS` da büyüyecek.
- **T10 — Excel tutarlılığı zaten otomatik.** `generate_excel.py` ve `generate_documents.py` **aynı** `seed_data/master/*.yaml`'ı okuyor; yeni belgeler Excel'in okuduğu dizilere (`budget_vs_actual`, `monthly_production`, `covenant_tests`, `outstanding_debt_as_of_demo_today`) **yeni satır eklemiyor**, yalnızca var olanlara metinsel olarak atıfta bulunuyor — ayrı bir "Excel ↔ PDF tutarlılık" modülüne gerek yok; `make validate-excel` bu fazda değişmeden geçmeli (SORU 5'e cevap).

---

## 1. Hedef dağılım (SPEC_05 §6 aritmetiği)

| Kova | SPEC hedefi | Mevcut | Eklenecek |
|---|---|---|---|
| Ankara Development/lisans | 6 | 2 | +4 |
| Ankara Finans (zincir dahil) | 14 | 7 | +7 |
| Ankara EPC/Construction | 10 | 3 | +7 |
| Ankara Operation | 10 | 1 | +9 |
| Ankara Hukuk | 3 | 0 | +3 |
| Ankara Mali/İdari | 2 | 0 | +2 |
| **Ankara toplam** | **45** | **13** | **+32** |
| İzmir Development | 8 | 4 | +4 |
| İzmir Hukuk | 4 | 0 | +4 |
| İzmir Finans | 0 | 0 | +0 |
| İzmir Mali/İdari | 3 | 0 | +3 |
| **İzmir toplam** | **15** | **4** | **+11** |
| **Company toplam** | **10** | **1** | **+9** |
| **GENEL TOPLAM** | **70** | **18** | **+52** |

("Mevcut" = ledger'da zaten var olan PDF girişleri, generate_in_phase 3.1 **veya** 5.1; Excel workbook'lar — `generate_in_phase: "4.2"` — bu sayıma dahil değil, SPEC_05 §5/§6 WeasyPrint belgelerini tanımlıyor, Excel ayrı bir Phase 4.2 girişimi — **kendi kararım**, SORU 2'de teyit isteniyor.) 70 rakamı ≤80 tavanının altında, 8-10 taranmış PDF hedefi: mevcut 4 + yeni 5 = **9**.

## 2. Yeni belge envanteri (52 + 3 zaten-5.1 = 55 `document_specs` girişi)

Tabloda: kaynak türü `D`=digital_pdf, `S`=scanned_pdf. Dil `tr`/`en`. Hepsi `generate_in_phase: "5.1"`, `tag: AI_ASSUMPTION` (Naci onayına kadar). FIN-008/009 ve OPS-002/003 Excel workbook'ları zaten kullandığı için yeni PDF'ler bir sonraki boş numaradan başlıyor (FIN-010, OPS-004).

**Ankara — Development (+4, id DEV-003..006)**
| id | Başlık | Dept/Subdept | Kaynak | İçerik açısı / key_facts |
|---|---|---|---|---|
| DEV-003 | Bağlantı Anlaşması | enerji_grubu/enerji_gelistirme | D, tr | TEİAŞ ile şebeke bağlantısı; `financing_signed` öncesi bir tarih |
| DEV-004 | Yapı Ruhsatı | enerji_grubu/enerji_gelistirme | **S**, tr | `construction_start` öncesi belediye ruhsatı |
| DEV-005 | ÇED Olumlu Kararı | enerji_grubu/enerji_gelistirme | D, tr | `licence` öncesi, ÇŞB; `capacity_mw.initial` |
| DEV-006 | Saha Kullanım Hakkı Sözleşmesi | enerji_grubu/enerji_gelistirme | D, tr | arazi kullanım hakkı, inşaat öncesi |

**Ankara — Finans (+7, id FIN-010..016)**
| id | Başlık | Kaynak | İçerik açısı / key_facts |
|---|---|---|---|
| FIN-010 | Common Terms Agreement | D, en | `financing_signed` tarihli, ortak tanımlar; `total_debt`, `lenders` |
| FIN-011 | Security Agreement (Share Pledge) | D, en | SPV pay rehni; `financial_close` |
| FIN-012 | Account Pledge Agreement | D, en | proje hesap rehni |
| FIN-013 | Insurance Assignment Agreement | D, en | STU Sigorta'ya temlik |
| FIN-014 | Drawdown Notice — Tranche 1 | D, en | ilk çekim `drawdowns[0]` (2021-12-15, 15.000.000 EUR) |
| FIN-015 | Waiver Letter — Q4 2024 Covenant Test | D, en | `covenant_tests[4]` (1,24, fail) sonrası feragat; AMD01'e giden köprü |
| FIN-016 | Covenant Compliance Report — Q4 2024 | D, en | tarihsel covenant raporu, `covenant_tests[4]` |

**Ankara — EPC/Construction (+7, id EPC-004..010)**
| id | Başlık | Kaynak | İçerik açısı / key_facts |
|---|---|---|---|
| EPC-004 | Mechanical Completion Certificate | D, en | `commissioning` öncesi |
| EPC-005 | Independent Engineer's Completion Report | D, en | MNO Teknik Danışmanlık |
| EPC-006 | Punch List Closure Confirmation | D, en | `cod_actual` civarı |
| EPC-007 | Construction All Risks Insurance Policy Summary | D, en | STU Sigorta, inşaat dönemi |
| EPC-008 | Performance Test Results Report | D, en | `capacity_mw.current` doğrulaması |
| EPC-009 | Warranty & Defects Liability Certificate | D, en | `cod_actual` + 1 yıl |
| EPC-010 | Grid Connection Completion Certificate | **S**, tr | TEİAŞ, `commissioning` civarı |

**Ankara — Operation (+9, id OPS-004..012)**
| id | Başlık | Kaynak | İçerik açısı / key_facts |
|---|---|---|---|
| OPS-004 | O&M Agreement | D, en | JKL İnşaat, `operation_start` sonrası |
| OPS-005 | **Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)** | D, tr | `incidents[0]`, `monthly_production[8]` — **ANK-MIX-002'nin pozitif sebep kaynağı** |
| OPS-006 | Aylık Üretim Raporu — Aralık 2023 | D, tr | `monthly_production[1]` |
| OPS-007 | Aylık Üretim Raporu — Haziran 2025 | D, tr | `monthly_production[19]` |
| OPS-008 | Yıllık Performans Raporu — 2. İşletme Yılı | D, tr | `operating_year_on_demo_today` bağlamı, geçmiş yıl |
| OPS-009 | Sigorta Yenileme Bildirimi — İşletme Dönemi | D, tr | STU Sigorta |
| OPS-010 | Kullanılabilirlik Garantisi Uyum Raporu | D, en | XYZ Wind Turbines GmbH, `availability_pct` |
| OPS-011 | Yedek Parça Tedarik Sözleşmesi | D, en | XYZ Wind Turbines GmbH |
| OPS-012 | Yıllık Bakım Planı — 2026 | D, tr | rutin planlama, rakamsız |

**Ankara — Hukuk (+3, id LEG-001..003)** — hepsi KLM Hukuk Bürosu, department `hukuk`
| id | Başlık | Kaynak |
|---|---|---|
| LEG-001 | Hukuki Görüş — Finansman Ön Koşulları | D, en |
| LEG-002 | Arazi Kullanım Hakkı Hukuki İnceleme Notu | D, tr |
| LEG-003 | Sözleşme Uyum Değerlendirmesi — EPC ve Finansman | D, tr |

**Ankara — Mali/İdari (+2, id ADM-001..002)**
| id | Başlık | Dept | Kaynak |
|---|---|---|---|
| ADM-001 | Yıllık İşletme Bütçesi Onayı — 2026 | mali_isler | D, tr |
| ADM-002 | Sigorta Programı Yıllık Gözden Geçirme Notu | idari_isler | D, tr |

**İzmir — Development (+4, id DEV-005..008)** — `pending_steps`/`ced_status` **değişmiyor** (kendi kararım, §"Kendi kararlarım"), yalnızca renk/tarihçe ekliyor
| id | Başlık | Kaynak |
|---|---|---|
| DEV-005 | Bağlantı Görüşü Başvurusu (TEİAŞ, henüz sonuçlanmadı) | D, tr |
| DEV-006 | Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı | D, tr |
| DEV-007 | Rüzgar Ölçüm Kampanyası Raporu | D, tr |
| DEV-008 | Askeri Yasak Bölgeler Ön Görüş Talebi (yanıt bekleniyor) | **S**, tr |

**İzmir — Hukuk (+4, id LEG-001..004)** — KLM Hukuk Bürosu, department `hukuk`
| id | Başlık | Kaynak |
|---|---|---|
| LEG-001 | Arazi Mülkiyeti Hukuki İnceleme Notu | D, tr |
| LEG-002 | Kira/İrtifak Hakkı Sözleşmesi Taslağı (**status: draft**) | D, tr |
| LEG-003 | Şirket Yapısı Hukuki Görüşü — İzmir SPV | D, tr |
| LEG-004 | Önlisans Süre Uzatımı Hukuki Değerlendirmesi | D, tr |

**İzmir — Mali/İdari (+3, id ADM-001..003)**
| id | Başlık | Dept | Kaynak |
|---|---|---|---|
| ADM-001 | İzmir RES Geliştirme Bütçesi Onayı | mali_isler | D, tr |
| ADM-002 | Saha Güvenliği ve İdari Düzenlemeler Notu | idari_isler | D, tr |
| ADM-003 | Proje Maliyet Takip Notu — Geliştirme Aşaması | mali_isler | D, tr |

**Company (+9, id CO-ADM-002..010)**
| id | Başlık | Kaynak |
|---|---|---|
| ADM-002 | YK Kararı — İzmir RES Geliştirme Bütçesi Onayı | D, tr |
| ADM-003 | Pay Sahipleri Kararı — GHI Yatırım Ortaklık Onayı | **S**, tr |
| ADM-004 | Grup Sigorta Programı Özeti | D, tr |
| ADM-005 | Yıllık Yönetim Raporu — 2025 | D, tr |
| ADM-006 | Grup İlişkili Taraf Hizmet Sözleşmesi | D, tr |
| ADM-007 | Kurumsal Yönetim ve Uyum Politikası | D, tr |
| ADM-008 | YK Kararı — Denetim Komitesi Ataması | **S**, tr |
| ADM-009 | Grup Risk Raporu — 2026 | D, tr |
| ADM-010 | Pay Sahipleri Kararı — Kâr Dağıtım Politikası | D, tr |

Artı **3 zaten-ledger'da-var**: `DOC-ANK-FIN-002` (V01), `DOC-ANK-FIN-003` (V02), `DOC-ANK-EPC-003` (Change Order 01) — yeni ledger girişi yok, yalnızca `document_specs` + prose + render.

Yeni whitelist adı: **yok**. Yeni ledger rakamı: **yok** (hepsi mevcut alanlara `key_facts` ile atıf yapıyor; bazıları `key_facts: {}` — salt betimleyici). `facts.py::_FIELD_KIND`'a birkaç metin-geçişli yeni giriş (`incident_type` gibi) eklenecek.

## 3. `hand_edited:` koruması

Kod değişikliği yok (T3). `make prose --only DOC-ANK-DEV-003 --only DOC-ANK-DEV-004 …` (52 yeni id) çalıştırılacak; `generate_prose.py`'nin varsayılan tam-taramalı modu (`--only` verilmezse tüm `SPECS`) da güvenli — var olan 18 belgenin prose'u zaten diskte olduğu için "atlandı (zaten var)" der, hand_edited kontrolüne bile gerek kalmadan dokunmaz.

## 4. `validate_dataset` — `validate_ledger.py`'ye üç yeni fonksiyon (T2)

```python
def check_version_links(raws, ledgers, report) -> None:
    """Genel V-kuralı: supersedes/superseded_by karşılıklı olmalı (A.supersedes=B ise
    B.superseded_by=A) ve bu ilişkiyle bağlı her zincirde tam olarak bir belge güncel
    (status != superseded) olmalı. F6'nın Facility-özel mantığının genellenmişi;
    yalnızca supersedes/superseded_by GERÇEKTEN dolu olan belgeler için çalışır — Licence
    → Licence Amendment gibi `related` ile bağlı ama supersedes kullanmayan ilişkiler
    (farklı semantik: "amended" durumu, belge geçersiz olmuyor) bu kuralın dışında kalır."""

def check_technical(ankara, report) -> None:
    """T1: türbin sayısı × jenerik sınıf (5 MW) ≈ capacity_mw.current (±1 MW tolerans,
    WARNING) — 12×5=60 zaten tutuyor, gelecekte biri türbin sayısını değiştirip
    kapasiteyi unutursa yakalar."""

def check_document_distribution(raws, ledgers, report) -> None:
    """SPEC_05 §6: toplam belge sayısı > 80 ise ERROR; proje/kova sayıları SPEC'in
    "yaklaşık" aralığının (±30%) dışındaysa WARNING; taranmış (scanned_pdf) sayısı
    8-10 aralığı dışındaysa WARNING. G1'in eski sabit-15 uyarısının yerini alır."""
```
`check_questions`'a T8'deki tek satırlık istisna: `category == "general"` iken `expected_answer is None` Q4 hatasına düşmez.

`validate_documents.py::validate_generated`'daki `len(entries) != 15` (G6) sabit-sayı dalı **kaldırılıyor** — zaten var olan `manifest_ids != expected_ids` (SPECS anahtarlarıyla küme eşitliği) tek başına yeterli ve daha doğru; üst sınır artık `check_document_distribution`'da.

## 5. `questions.json` v2 — hedef ~65

- `QuestionCategory` += `"general"` (`ledger_schema.py`).
- **Yeni `general` sorular (≥3, kendi kararım — CATEGORY_QUOTAS'a `general: 3` eklenir):** "DSCR ne demek?", "ÇED süreci nedir?", "Covenant testi ne işe yarar?" — `expected_answer: null`, `expected_project: null`, `required_sources: []`, `ask_as_user: "yonetim"`.
- **`ANK-MIX-002` güncellenir** (T7): artık `expect_no_answer: false`, belge tarafı `DOC-ANK-OPS-005`'i (Bakım Raporu) kaynak gösterip T-07 arızasını sebep olarak verir; `required_sources` += "Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)".
- **Yeni `ANK-MIX-003`** (negatif sebep, T7): "Ankara RES Q1 2025 bütçe sapmasının sebebi belgelerde yazıyor mu?" — `expect_no_answer: false`, cevap Excel farkı + `NO_REASON_TEXT` (hiçbir belge Ocak 2025 kesintisini anlatmıyor).
- Yeni belgelere değen ~12-15 `document`/`temporal`/`isolation` sorusu (ör. "Ankara RES'in bağlantı anlaşması ne zaman imzalandı?", "Hangi belge Q4 2024 covenant testinin feragat aldığını gösterir?", "İzmir RES'te hukuk departmanının belgesi var mı?" gibi — mevcut 48'in üzerine, dağılımı SPEC_05 §9'daki minimum soru listesiyle hizalı).
- `MIN_QUESTIONS` 30→60, `QUOTAS` `{"İzmir RES": 12, "Ankara RES": 35}` (kendi kararım, ~65 hedefiyle orantılı), `CATEGORY_QUOTAS` += `general: 3` (diğerleri aynı).
- `eval_lib.py`: `score_question`'a `category == "general"` dalı (T8) — `passed = outcome.answered and outcome.query_type == "GENERAL_QUERY" and not outcome.cited_titles and not outcome.cited_files`; `HUNDRED_PERCENT_CATEGORIES`'e **eklenmiyor** (genel tanım soruları isolation/hallucination/authorization kadar kritik değil — %80 eşiği, kendi kararım).
- `run_eval.py`/`AskOutcome`: `query_type`/`cited_files` zaten Phase 4.3'ten var, ek alan gerekmiyor.

## 6. Excel tutarlılığı (T10, SORU 5'e cevap)

Yeni belge yok yeni Excel satırı gerektirmiyor; `make validate-excel` bu fazda **değişmeden** geçmeli. Kanıt: `make lint` (Excel doğrulayıcısı zaten parçası) yeşil kalır.

## 7. Backend/script/doküman güncellemeleri (T9)

- `backend/tests/test_demo_documents_seed.py`: `15`→70 (veya nihai sayı), `19`→74.
- `scripts/seed_demo.sh`: `wait-for-documents --timeout 600` → `1800` (9 taranmış + 61 dijital; RAM/disk endişesi yok, yalnızca OCR sırası uzuyor).
- `README.md`: "Demo veri (Phase 3.1)" başlığı/rakamları Phase 5.1 sayılarına güncellenir; "Hukuk departmanının 15 belge içinde kendi belgesi yok" notu **kaldırılır** (artık var — 7 Hukuk belgesi).
- `docs/ARCHITECTURE.md` ADR-013: "Phase 5.1 concretization" paragrafı (70 belge, LEG/ADM grupları, `document_specs/` paketi, `check_version_links`/`check_technical`/`check_document_distribution`).
- `docs/DOMAIN_MODEL.md`: `QuestionCategory` satırına `general` eklenir.
- `docs/PHASES.md`: Phase 5.1 satırı + Phase 4.3'ün ertelediği notların kapandığı işaretlenir.

## 8. Kabul kriterleri → kanıt

| Kriter | Kanıt |
|---|---|
| validator 0 hata | `make validate-ledger --summary` çıktısı 0 error; `make lint` tamamı yeşil |
| görüntü PDF'ler `ready` | `make seed` sonrası DB'de `source_type='scanned_pdf'` olan 9 belgenin `ingestion_status='ready'` olduğu bir sorgu/test |
| eval isolation/hallucination/authorization %100, diğerleri ≥%80 | `make eval` tam koşu, `results.md` kategori tablosu |
| belge ≤80 | `check_document_distribution` ERROR testi + gerçek sayı (70) `validate_documents.py::test_...` |
| `hand_edited` korunuyor | `test_generate_prose_guard.py` (mevcut, değişmez) + `make prose` sonrası 6 dosyanın diff'siz kaldığının kontrolü |

---

## SORU (Naci cevaplamalı)

1. **Kapsam: tam 70 mi (52 yeni belge, tablo yukarıda), yoksa daraltılmış (~55-58) mi?** 52 yeni belge = ~52 LLM prose çağrısı (`make prose`, ~13 sn aralık + olası yeniden deneme ⇒ tahmini 15-25 dk) + render + doğrulama + OCR (9 taranmış) + `questions.json` v2 (+17 soru) + `make eval` tam koşusu (65 soru × 26 sn ⇒ ~30 dk) — bu fazın en büyük içerik yükü şimdiye kadarki en büyüğü. Daraltılmış seçenek: en "dolgu" nitelikli 5-8 belgeyi çıkar (ör. 2 YK kararı, spare parts, risk raporu, kâr dağıtım politikası) → ~62-65 toplam, SPEC'in "~70" toleransı içinde kalır, daha az yük. **Önerim: tam 70** (tablo zaten hazır, kova hedefleriyle birebir örtüşüyor) ama onayını istiyorum.
2. **Excel workbook'lar (4 adet, zaten var) ~70/≤80 kotasına dahil mi?** Önerim **hayır** (SPEC_05 §5/§6 WeasyPrint/PDF belgelerini tanımlıyor; Excel Phase 4.2'nin ayrı girişimi) — onaylıyor musun?
3. **`questions.json` MIN_QUESTIONS/QUOTAS/CATEGORY_QUOTAS yeni sayıları** (§5: 60/İzmir 12-Ankara 35/general 3) onaylı mı, yoksa farklı sayılar mı istiyorsun?
4. **İzmir'in gelişim aşaması ilerlemiyor** (`pending_steps`/`ced_status` aynı kalıyor, yeni belgeler yalnızca renk/tarihçe ekliyor, CLAUDE.md'nin "İzmir RES: development, ÇED tamamlanmamış" sabitini koruyor) — bu doğru varsayım mı, yoksa bu fazda İzmir'i bir adım ilerletmek (ör. "Askeri Yasak Yazısı"nı tamamlanmış göstermek) ister misin?
5. **`ANK-MIX-002`'nin anlamının değişmesi** (eskiden "sebep yok" negatif örneği idi, şimdi Bakım Raporu ile "sebep var" pozitif örneğine dönüşüyor, negatif örnek yeni `ANK-MIX-003`'e taşınıyor) — onaylı mı?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- `document_specs.py` → `document_specs/` paketi (8 dosya, proje/kova başına); `DocumentSpec`/`ExtraTable` `document_specs/_base.py`'ye taşınır.
- Yeni Finans/EPC/Operation belgelerinin çoğu `key_facts: {}` (salt betimleyici) veya mevcut tek bir ledger alanına işaret ediyor — yeni sayısal ledger alanı **yok**.
- Hukuk belgeleri "KLM Hukuk Bürosu", sigorta belgeleri "STU Sigorta" kullanıyor (ikisi de zaten whitelisted, ilk kez kullanılıyor).
- `general` kategorisi `HUNDRED_PERCENT_CATEGORIES`'e girmiyor, `DEFAULT_THRESHOLD_PCT` (%80) kullanıyor.
- `check_version_links`/`check_technical`/`check_document_distribution` `validate_ledger.py`'de kalıyor — SPEC'in ayrı `validate_dataset.py` adı Phase 2.1'den beri kabul edilmiş bir sapma, yeni dosya açılmıyor.
- `validate_documents.py`'nin G6 sabit-15 dalı kaldırılıyor (küme eşitliği zaten tam kontrol; üst sınır `check_document_distribution`'a taşınıyor).
- `wait-for-documents --timeout` 600→1800 (dev deneyimi için; RAM/disk bütçesi risk değil).
- Yeni scanned belgeler: `DOC-ANK-DEV-004`, `DOC-ANK-EPC-010`, `DOC-IZM-DEV-008`, `DOC-CO-ADM-003`, `DOC-CO-ADM-008` (toplam taranmış 9).

## Uygulama sırası

1. `ledger_schema.py`: `QuestionCategory` += `"general"`.
2. 52 yeni belge girişini `ankara_res.yaml`/`izmir_res.yaml`/`company.yaml`'a ekle (`generate_in_phase: "5.1"`, `tag: AI_ASSUMPTION`); `facts.py::_FIELD_KIND`'a gereken metin-geçişli girişleri ekle.
3. `make validate-ledger` 0 hataya kadar düzelt (yeni `check_version_links`/`check_technical`/`check_document_distribution` da bu adımda yazılır).
4. `document_specs.py` → `document_specs/` paketine böl; 55 `DocumentSpec` girişini ekle (3 zaten-5.1 + 52 yeni).
5. `generate_documents.py`: `GENERATED_PHASES = {"3.1","5.1"}`, dört çağrı noktasını güncelle.
6. `make prose --only <52 id>` (LLM, commitli çıktı).
7. `generate_documents.py` çalıştır → `validate_documents.py` (G6 basitleştirilmiş) → 0 hata.
8. `questions.json` v2 (§5), `validate_ledger.py::check_questions` `general` istisnası, `eval_lib.py` `general` skorlama dalı.
9. `test_demo_documents_seed.py` sayıları, `scripts/seed_demo.sh` timeout.
10. `make seed` (reset-demo + seed) uçtan uca, taranmış belgelerin `ready` olduğunu doğrula.
11. `make eval` tam koşu, eşikleri doğrula.
12. `make validate-excel`/`make lint` tamamı yeşil olduğunu doğrula (Excel'e dokunulmadı).
13. README/ARCHITECTURE/DOMAIN_MODEL/PHASES güncelle → rapor → commit + tag `phase-5-1` + push.

## Kritik dosyalar

- `seed_data/master/{ankara_res,izmir_res,company}.yaml`, `seed_data/generator/ledger_schema.py`
- `seed_data/generator/document_specs/` (yeni paket), `seed_data/generator/{generate_documents,validate_documents,generate_prose,facts}.py`
- `seed_data/generator/validate_ledger.py` (üç yeni check fonksiyonu)
- `seed_data/evaluation/questions.json`, `scripts/eval_lib.py`
- `backend/tests/test_demo_documents_seed.py`, `scripts/seed_demo.sh`
