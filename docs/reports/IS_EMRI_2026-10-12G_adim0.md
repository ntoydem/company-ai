# İş Emri 2026-10-12-G — Adım 0 Raporu (F kalıntısı)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kapılar yeşil.

## (a) IZM-DEV-003 pending_steps — tag + gerekçe düzeltmesi

F Adım 2'de eklenen iki hücre düzeltildi (`seed_data/master/izmir_res.yaml`):
- `tag: USER_FACT` → **`AI_ASSUMPTION`** (ikisi de sabit bir ledger USER_FACT değeri
  değil, "önceki adımlar/önlisans durumu" çıkarımıydı).
- "Yapı Ruhsatı" hücresinin gerekçe cümlesi ("ÇED, imar kesinleşmesi... tamamlanmadan
  başvurulamaz") kaldırıldı — yalnız **"Henüz alınmamıştır."** kaldı.
- "Üretim Lisansı" hücresi aynı kaldı (zaten yalnız durum bilgisi veriyordu), tag
  AI_ASSUMPTION yapıldı.

## (b) "İnşaat Başlangıcı" — yeni PreLicenceStep

`seed_data/generator/ledger_schema.py::PRE_LICENCE_STEPS`/`PreLicenceStep`'e **"İnşaat
Başlangıcı"** eklendi. `izmir_res.yaml`'da yeni satır:

```yaml
- {step: "İnşaat Başlangıcı", expected: "Henüz başlanmamıştır.", tag: AI_ASSUMPTION}
```

`project.timeline.construction_start: null` (satır 37) ile tutarlı. IZM-DEV-003 yeniden
üretildi; "Bekleyen Kritik Adımlar" tablosunda artık 7 satır var (doğrulandı, PyMuPDF ile
render kontrolü).

## (c) questions.json — ANK-FIN-006/012 required_sources düzeltmesi

Ledger'ın kendi `ankara_res.project.finance.dscr_covenant.changed_by` alanı
**DOC-ANK-FIN-006** ("Facility Agreement Amendment 02") diyor; `questions.json`'daki
`required_sources` ise "Facility Agreement Amendment 01" (DOC-ANK-FIN-005) yazıyordu —
F-Adım2'de zaten "eski test tanımı" olarak teşhis edilmişti, şimdi düzeltildi:

```diff
- "Facility Agreement Amendment 01"
+ "Facility Agreement Amendment 02"
```

**Beklenen cevap/eşik DEĞİŞMEDİ** (`expected_answer: ledger:...dscr_covenant.current.value`
/`.changed_by` aynı kaldı) — yalnız hangi belgenin bu cevabı doğrulaması gerektiği
düzeltildi. **Doğrulama (kritik):** ilk denemede `replace_all` ile 2 EK soruyu
(`GEN-DSC-005`, `GEN-DSC-012`, sonra fark edilen `GEN-DSC-013` — hepsi "Amendment var mı?"
tipi genel discovery soruları, DSCR'yle ilgisiz, orijinalde kasıtlı olarak Amendment 01'e
işaret ediyorlardı) yanlışlıkla "Amendment 02"ye çevirmişti; üç soru da Amendment 01'e geri
alındı. Son durum, git HEAD ile programatik karşılaştırmayla doğrulandı: **yalnız
ANK-FIN-006 ve ANK-FIN-012 değişti**, başka hiçbir soru dokunulmadı.

## (d) F Adım 4 raporu

Zaten mevcut ve commit edilmiş (`docs/reports/IS_EMRI_2026-10-12F_adim4.md`, önceki
oturumda) — ek işlem gerekmedi.

## Doğrulama

- `validate_ledger --summary`: 0 hata, 1 uyarı (önceden var, ilgisiz).
- `generate_documents`: 102 belge, 0 hata.
- `validate_documents` (full): 0 hata, 0 uyarı.
- IZM-DEV-003 render kontrolü: yeni 3 satır (Yapı Ruhsatı/Üretim Lisansı/İnşaat
  Başlangıcı) metinde doğrulandı.
- `make lint`: ✅ (ruff+format+mypy+ocr-worker+validate-ledger+validate-documents
  --prose-only+validate-excel).

Devam ediliyor: **Adım 1** (Yeşilova türbin/MW — T-14.1=B).
