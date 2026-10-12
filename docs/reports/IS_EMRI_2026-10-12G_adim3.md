# İş Emri 2026-10-12-G — Adım 3 Raporu (üç dava dilekçesi — davacı adları)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kapılar yeşil, harcama $0,0532
(bütçe $2,0'ın çok altında).

## Bağlam

İş Emri 2026-10-11-B Adım A'da üç dava dilekçesi, davacının (kurgusal) adı kaynakta
olmadığı için **atlanmıştı** ("Tansu'ya soru" olarak raporlanmıştı, isim icat
edilmemişti). PR #23 (`NACI_CEVAP_2026-10-12.md` §6) üç ismi de verdi:

| Dava | Davacı | Belge |
|---|---|---|
| Karatepe — Elektrik Direği İhlali (Ankara 1. Asliye Hukuk, 2026/356 E.) | **Ramazan Öztürk** (komşu parsel maliki) | **DOC-ANK-LEG-010** (yeni) |
| Yeşilova — Arazi Tahsis Tazminatı (Çanakkale 1. Asliye Hukuk, 2025/208 E.) | **Hasan Çelik** (arazi maliki) | **DOC-YSV-LEG-002** (yeni) |
| Yeşilova — Sınır İhlali (Çanakkale 2. Asliye Hukuk, 2026/511 E.) | **Ayşe Doğan** (komşu parsel maliki) | **DOC-YSV-LEG-003** (yeni) |

Üçü de kurgusal, ürün sahibi onaylı — `AI_ASSUMPTION` gerekmedi, `tag: USER_FACT`.

## Şema değişikliği — `legal_case_2`

Karatepe'nin ve Yeşilova'nın `legal_case` alanı (`LegalCase | None`) **tekildi** — her
iki projenin de zaten BİRER davası vardı (Karatepe: T-12.1 kamulaştırma; Yeşilova:
T-12.2 arazi tahsis tazminatı). Elektrik Direği (Karatepe'nin 2. davası) ve Sınır
İhlali (Yeşilova'nın 2. davası) için `seed_data/generator/ledger_schema.py`'ye
`legal_case_2: LegalCase | None = None` eklendi (`AnkaraProject` ve `OperatingProject`
— ikinci bir liste yerine ikinci bir alan: mevcut `project.legal_case.*` `key_facts`
referanslarını bozmadan, bu iş emrinin somut ihtiyacına (proje başına en fazla 2 dava)
tam oturan minimal değişiklik).

## Ledger

- `ankara_res.yaml`: yeni `legal_case_2` bloğu (Elektrik Direği, 240.000 TRY ecrimisil,
  durum "Bekliyor" — ön inceleme yapılmadı).
- `yesilova_res.yaml`: mevcut `legal_case.plaintiff` **"Arazi Maliki (kurgusal kişi,
  ismi henüz verilmedi)"** → **"Hasan Çelik (arazi maliki)"**; yeni `legal_case_2`
  bloğu (Sınır İhlali, 85.000 TRY ecrimisil).

## Belgeler — yeni 3 petition + spec

`DOC-ANK-LEG-010`, `DOC-YSV-LEG-002`, `DOC-YSV-LEG-003` — her biri `DOC-ANK-LEG-004`'ün
(T-12.1'in zaten üretilmiş dilekçesi) birebir deseniyle: `family="letter"`,
`prose_guidance_tr` davacı/davalı/konu/tutar/tarih token'larıyla, "davanın sonucu
hakkında yorum yapma" kısıtıyla. `parties:` listesi SPV + davacının gerçek (kurgusal)
adını taşıyor. `confidentiality: restricted` (diğer dava belgeleriyle aynı).

`DOC-YSV-LEG-001`'in (T-12.2'nin önceki iç yazışması, davacıyı rolüyle anan) kendi
yönergesine DOKUNULMADI — o belge yazıldığı tarihte isim bilinmiyordu, bu geçmişe dönük
olarak "yanlış" değil, metne dokunmak gereksiz bir yeniden üretim/LLM maliyeti olurdu.

## Üretim

`generate_prose.py --provider anthropic --only DOC-ANK-LEG-010 --only DOC-YSV-LEG-002
--only DOC-YSV-LEG-003`: **3 çağrı, 4089+4501 token, $0,0532**, 0 altyapı hatası, 0
içerik reddi. Render edilen metinler davacı/davalı/mahkeme/dosya no/tutar/tarihleri
AÇIKÇA ve doğru taşıyor (PyMuPDF ile doğrulandı).

## Test düzeltmesi

`backend/tests/test_demo_documents_seed.py`: belge sayısı sabitleri (102→**105** PDF,
109→**112** toplam) üç yeni belgeyi yansıtacak şekilde güncellendi (3 yerde) — hedefli
koşu: **8 passed**.

## Doğrulama

- `validate_ledger --summary`: 0 hata, 1 uyarı (önceden var, ilgisiz).
- `generate_documents` (105 belge, önceden 102) + `validate_documents` (full): 0 hata,
  0 uyarı.
- `make lint`: ✅.
- Hedefli test: `test_demo_documents_seed.py` 8/8 ✅.
- Solo tam `make test`: Adım 6'da.
- Harcama: **$0,0532** (Adım 3) + $0 (Adım 0-2) = **$0,0532 / $2,0**.

Devam ediliyor: **Adım 4** (Boztepe AI_ASSUMPTION — DSCR test tablosu, hukuk maddesi,
DSRA tarihi).
