# İş Emri 2026-10-12-G — Adım 4 Raporu (Boztepe AI_ASSUMPTION — veri dondurma kuralı)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kapılar yeşil, harcama $0,0228.

## Bağlam

İş Emri 2026-10-11 Adım 4 (Boztepe PF-2) zamanında eski DURMA KURALI gereği 3 kalem
BİLEREK üretilmemişti (kaynak yok, icat etme). PR #23'ün "veri dondurma" politikası
(NACI_CEVAP_2026-10-12.md §8) artık BUNU TERSİNE ÇEVİRİYOR: eksik/belirsiz bir değer
için artık DUR demek yerine tutarlı bir değer seçip `AI_ASSUMPTION` ile işaretleyip
devam et. Bu adımda üç kalem dolduruldu:

## 1. DSCR test tablosu

**Önce:** Boztepe'de `covenant_tests` hiç yoktu — `DOC-BOZ-FIN-001`'in (Facility
Agreement) kendi yönergesi açıkça "no DSCR test history exists... none may be
invented" diyordu.

**Şimdi:** `boztepe_res.yaml`'a `covenant_tests` eklendi — `dscr_covenant: 1,20x`
minimumuyla tutarlı, ikisi de geçti:
```yaml
covenant_tests:
  - {period: Q4_2024, dscr: 1.28, result: pass, doc: null, tag: AI_ASSUMPTION}
  - {period: Q4_2025, dscr: 1.31, result: pass, doc: null, tag: AI_ASSUMPTION}
```
Karatepe (`DOC-ANK-FIN-007`) ve Yeşilova'nın (`DOC-YSV-FIN-010`) deseniyle AYNI: geçmiş
test sonucu Facility Agreement'ın İÇİNE değil, **ayrı bir Covenant Report'a**
(**DOC-BOZ-FIN-005**, yeni, `ExtraTable(kind="covenant_tests", ledger_key="boztepe_res")`
— kod tarafından ledger'dan üretilen tablo, prose'a gömülü değil). Facility Agreement'ın
kendi yönergesi DEĞİŞMEDİ (hâlâ yalnız minimumu anıyor, geçmiş test sonucu anmıyor) —
bu, önceki kararın isabetli kısmıydı, bozulmadı.

## 2. Boztepe kredi sözleşmesi uygulanacak hukuk maddesi

**Önce:** render edilen metin **dairesel/anlamsız** bir cümleydi: *"shall be governed by
the law designated by the Parties in the Facility documentation"* — hangi hukukun
uygulanacağını hiç söylemiyordu (kendi kendine atıfta bulunuyordu).

**Şimdi:** `Finance.governing_law` (yeni, generic, optional alan) eklendi —
**"Türkiye Cumhuriyeti kanunları"** (AI_ASSUMPTION, gerekçe: borçlu ve kreditör ikisi de
Türkiye'de kurulu/yerleşik — tutarlı bir seçim). `DOC-BOZ-FIN-001` 1 Claude çağrısıyla
yeniden üretildi; render: *"This Agreement is governed by Türkiye Cumhuriyeti
kanunları."* — açık, dairesel değil.

## 3. DSRA ekstresi tarihi

**Önce:** `document_date: 2026-09-30` ("ay sonu ekstresi; demo_today öncesi" — gevşek,
demo_today'le DOLAYLI bağlantılı).

**Şimdi:** `document_date: 2026-10-06` — **demo_today'in (06.10.2026) kendisiyle**
birebir aynı, tutarlı bir anlık görüntü tarihi (adı "Ekim 2026" olarak güncellendi;
LLM çağrısı gerekmedi, yalnızca token substitüsyonu).

## Üretim

`generate_prose.py --provider anthropic --only DOC-BOZ-FIN-001 --only DOC-BOZ-FIN-005
--force`: **2 çağrı, 2504+1777 token, $0,0228**, 0 altyapı hatası, 0 içerik reddi.

## Test düzeltmesi

Belge sayısı +1 (DOC-BOZ-FIN-005) — `test_demo_documents_seed.py`'deki sabitler
(105→**106** PDF, 112→**113** toplam) güncellendi, hedefli koşu **8/8** ✅.

## Doğrulama

- `validate_ledger --summary`: 0 hata, 1 uyarı (önceden var, ilgisiz).
- `generate_documents` (106 belge, önceden 105) + `validate_documents` (full): 0 hata,
  0 uyarı.
- Render kontrolü (PyMuPDF): her üç düzeltme de render edilen metinde doğrulandı.
- `make lint`: ✅.
- Hedefli test: `test_demo_documents_seed.py` 8/8 ✅.
- Harcama: **$0,0228** (Adım 4) + $0,0532 (Adım 3) = **$0,076 / $2,0**.

Devam ediliyor: **Adım 5** (Anayasa kopyası).
