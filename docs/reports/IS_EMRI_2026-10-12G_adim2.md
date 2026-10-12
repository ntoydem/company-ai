# İş Emri 2026-10-12-G — Adım 2 Raporu (banka adları — Ç-12)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kapılar yeşil.

## Değişiklik

Anayasa v2.1 Ç-12'nin istisnası (gerçek bankalar, kurgusal ilişkiler içinde) artık
yürürlükte (PR #15/#16, 12.10.2026'da main'e birleşti). Kurgusal karşılıklar gerçek
adlarla değiştirildi — **sözleşme koşulları, oranlar, tutarlar DEĞİŞMEDİ** (yalnız isim):

| Kurgusal | Gerçek |
|---|---|
| PQR Bank | **Garanti BBVA** |
| LMN Bank | **Commerzbank AG** |
| DEF Bank | **Akbank** |
| bordro/vergi bankası | İş Bankası |

**Etkilenen alanlar** (global metin değişimi, 5 master yaml dosyası): `company.yaml`
(`parties`, `name_whitelist`), `ankara_res.yaml` (`lenders.local_bank`,
`guarantee_letters.lender`, tüm `documents[].parties`), `boztepe_res.yaml`
(`finance.lender`, tüm `parties`), `yesilova_res.yaml` (`finance.lender`, tüm `parties`),
`izmir_res.yaml` (`signed_undrawn_facility.lender`, `signed_unstarted_epc.advance_guarantee`,
tüm `parties`). Karatepe'nin teminat mektubu bankası (`guarantee_letters.lender`) aynı
global değişimle **Garanti BBVA** oldu.

Stale "Ç-12 bekliyor"/"BEKLE" notları (artık yanlış/kendine-referans olmuş) temizlendi;
`seed_data/generator/ledger_schema.py::SPEC_FICTIONAL_NAMES`'den "PQR Bank" çıkarıldı
(artık kurgusal değil, gerçek ad — `validate_ledger`'ın N3 kuralı bunu zorunlu
tutuyordu).

## "bordro/vergi bankası → İş Bankası" — N/A (company-ai kapsamında)

Grep ile doğrulandı: company-ai'de **bordro/payroll kavramı hiç yok** (`seed_data/`,
`backend/` içinde sıfır sonuç) — bu madde yalnızca AI-BalBal canvas demosunun kendi
verisiyle ilgili (NACI_CEVAP PR #21 §4'teki bordro aritmetik kontrolü), company-ai'nin
ledger/belge üretim hattında karşılığı yok. Uygulanacak bir yer bulunamadı.

## El düzenlemeli belgeler — DEĞİŞTİRİLMEDİ, otomatik doğru

7 hand-edited belge (`DOC-ANK-DEV-001`, `DOC-ANK-EPC-002`, `DOC-ANK-FIN-001`,
`DOC-ANK-FIN-004`, `DOC-ANK-FIN-006`, `DOC-IZM-DEV-003`, `DOC-CO-ADM-003`) kontrol
edildi: **hiçbiri banka adını düz metin olarak taşımıyor**, hepsi `[[counterparty]]`/
`[[parties_list]]` token'ları kullanıyor — ledger'daki parti adı değişince bu belgeler
otomatik doğru render edildi, prose dosyalarına DOKUNULMADI. Ayrıca hiçbir (hand-edited
veya değil) prose dosyasında banka adı düz metin olarak YOKTU (grep, sıfır sonuç) —
tüm üretim token-tabanlı, bu yüzden hiçbir LLM çağrısı/yeniden üretim gerekmedi.

## Regenerasyon

- `generate_documents.py`: 102 belge, 0 hata, **0 LLM çağrısı**.
- `make excel` (generate_excel + LibreOffice recalc + validate_excel): commit'li 7
  workbook + `manifest.json` yeniden üretildi — `Garanti BBVA`/`Commerzbank AG`/`Akbank`
  artık `parties` alanlarında, `PQR Bank`/`LMN Bank`/`DEF Bank` sıfır kalıntı.

## Test düzeltmesi

`backend/tests/test_demo_documents_seed.py::test_seed_records_ledger_parties_as_extra_field`
gerçek manifest'ten okuyordu, "PQR Bank" bekliyordu — **"Garanti BBVA"** olarak
güncellendi, hedefli koşuda geçti (diğer sahte/senaryo testlerindeki "PQR Bank" — örn.
`test_ask.py`, `test_documents.py` — rastgele bir fixture string'i, gerçek seed'le
ilgisiz, DOKUNULMADI).

## Doğrulama

- `validate_ledger --summary`: 0 hata, 1 uyarı (önceden var, ilgisiz).
- `generate_documents` + `validate_documents` (full): 0 hata, 0 uyarı.
- `make excel` → `validate_excel`: 0 hata.
- `make lint`: ✅.
- Hedefli test: `test_seed_records_ledger_parties_as_extra_field` ✅ (1 passed).
- Solo tam `make test`: Adım 6'da (iş emrinin kendi sırasına göre).

Devam ediliyor: **Adım 3** (üç dava dilekçesi — davacı adları).
