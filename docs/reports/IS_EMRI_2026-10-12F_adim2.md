# İş Emri 2026-10-12-F — Adım 2 Raporu (belge içeriği eksikleri)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kapılar yeşil, bütçe $1,5 aşılmadı
(gerçek harcama: $0,0177).

## 1. IZM-DEV-003 (ÇED Süreci Durum Yazısı) — bekleyen adımlar tablosu

`seed_data/master/izmir_res.yaml` → `project.development.pending_steps`'teki iki boş
hücre ledger-only bir değişiklikle dolduruldu (prose **hand-edited** olduğu için
DOKUNULMADI — `extra_table` kodun her çalıştırmada ledger'dan ÜRETTİĞİ, prose'dan
BAĞIMSIZ bir tablo, bkz. `DocumentSpec.extra_table`/`kind="pending_steps"`):

```yaml
- {step: "Yapı Ruhsatı", expected: "Henüz alınmamıştır — ÇED, imar kesinleşmesi, kat'i
   proje onayı ve bağlantı anlaşması tamamlanmadan başvurulamaz.", tag: USER_FACT}
- {step: "Üretim Lisansı", expected: "Henüz alınmamıştır — bugüne kadar yalnızca
   önlisans (15.01.2025) alınmıştır.", tag: USER_FACT}
```

Üretilen PDF'te (`DOC-IZM-DEV-003`, "Bekleyen Kritik Adımlar" tablosu) artık bu iki
satır açık düz cümle içeriyor (doğrulandı, bkz. §5).

**"İnşaata henüz başlanmamıştır" — UYGULANAMADI, Tansu'ya soru:** bu bilgi
`PreLicenceStep` sabit sözlüğünde ("Önlisans", "Süre Uzatımı Başvurusu", ...,
"Üretim Lisansı") YOK — "İnşaat" bir satır olarak eklenemez (spec değişikliği
gerektirir, iş emri kapsamı dışında). Bu bilgiyi DOC-IZM-DEV-003'ün prose'una (Süreç
Durumu/Bekleyen Adımlar bölümleri) serbest metin olarak eklemek de mümkün değil:
belge **hand-edited** listede (`DOC-IZM-DEV-003`, `test_generate_prose_guard.py`) —
"el düzenlemeli belge yeniden üretilecekse DUR" kuralı burada devreye girer, ama
bu tek alt-bilgiyi atlayıp işe devam etmek "ledger'da olmayan bilgi → o belgeyi atla,
DURMA" ruhuyla tutarlı (ledger'da bilgi VAR — `construction_start: null` — ama onu
YAZACAK bir mekanizma yok). **Tam DUR tetiklenmedi, bu tek alt-görev atlandı.**
SORU (Tansu/Naci): `PreLicenceStep` sözlüğüne "İnşaat" eklensin mi (spec kararı), yoksa
bu bilgi hiç dokümante edilmeyecek mi (IZM-DEV-006 kalıcı olarak "belgede yok" mu
kalacak)?

## 2. E-Adım2'nin 12 sorusu — "belge AÇIKÇA içeriyor mu?" yöntemiyle tek tek

Yöntem: ilgili `required_sources` belgesinin render edilmiş metni PyMuPDF ile okunup
(scanned_pdf tipi belgelerde `.digital.pdf` eşlenik dosyası kullanıldı — rasterize
edilen "taranmış" sunum dosyasının bilerek metin katmanı yok, bu bir hata değil)
soru-cevap aranır; ledger'daki karşılık ile karşılaştırılır.

| Soru | Belge | Açıkça var mı? | Sonuç/aksiyon |
|---|---|---|---|
| ANK-FIN-002 | DOC-ANK-FIN-004 (facility, el düzenlemeli) | Belge "14.000.000 USD" diyor ama ledger'ın güncel `total_debt`=13.600.000 USD, `source_doc: DOC-ANK-FIN-007` (**kasıtlı çakışma** — `deliberate_conflict: true`, not: "sözleşme tutarı 14M, fiilen kullandırılan 13,6M"); DOC-ANK-FIN-007'nin kendi metninde de 13,6M rakamı YOK (yalnız DSCR + 11.671.800 USD "kalan borç" var) | **Düzeltme uygulanmadı** — DOC-ANK-FIN-007'nin `key_facts`'inde `total_debt` hiç yok (yalnız `dscr`, `outstanding_debt`); bunu eklemek "boş hücre/cümle doldurma" değil, yeni bir ledger↔belge KABLOLAMASI (yapısal spec değişikliği) — bu iş emrinin kapsamını aşıyor. Öneri olarak not edildi, UYGULANMADI. Ayrıca DOC-ANK-FIN-004 hand-edited. |
| ANK-FIN-003 | DOC-ANK-FIN-004 | Aynı — `local_debt`=13.600.000, `source_doc: DOC-ANK-FIN-007`, aynı eksik kablolama | Yukarıdakiyle aynı gerekçe, UYGULANMADI |
| ANK-FIN-004 | DOC-ANK-FIN-004 (hand-edited) | **EVET, açıkça var**: "no separate export credit agency (ECA) tranche forms part of this structure" | İçerik zaten doğru/açık — düzeltme gerekmiyor; olası başarısızlık retrieval/atıf sorunu, belge içeriği değil |
| ANK-NEG-002 | DOC-ANK-FIN-004 | Aynı (ECA) | Aynı, içerik zaten doğru |
| ANK-FIN-006 | "Facility Agreement Amendment 01" (= DOC-ANK-FIN-005) | Belge genel değişiklik şartlarından bahsediyor, DSCR/covenant'tan HİÇ bahsetmiyor — ama bu beklenen: ledger'ın kendi `dscr_covenant.changed_by` alanı **DOC-ANK-FIN-006**'yı gösteriyor, DOC-ANK-FIN-005'i değil | **Eski/yanlış test tanımı** (`questions.json`'daki `required_sources` değeri güncel değil) — belge içeriği sorunu DEĞİL, `questions.json` bu iş emrinin kapsamında DEĞİŞTİRİLMEDİ. Not: DOC-ANK-FIN-006 de hand-edited. |
| ANK-FIN-012 | Aynı | Aynı | Aynı (eski test tanımı), UYGULANMADI |
| ANK-FIN-010 | Covenant Report (workbook) | — | Excel-kaynaklı, belge içeriği kapsamı dışı. Adım 1'in Excel düzeltmesinden sonra bu soru artık GEÇİYOR (eski 9-soru listesindeydi, düzeltme sonrası kalan hata listesinde YOK) |
| ANK-DAT-001 | Covenant Report (workbook) | — | Aynı — Excel-kaynaklı, Adım 1 sonrası artık GEÇİYOR |
| ANK-DAT-003 | Financial Model 2026 (workbook) | — | Excel-kaynaklı, kapsam dışı; Adım 1 sonrası HÂLÂ başarısız (ayrı bir içerik/eşleşme sorunu, HTTP 500 değil) — bu iş emrinin "belge içeriği" kapsamına girmiyor, dokunulmadı |
| ANK-EPC-005 | DOC-ANK-EPC-008 (Performance Test Results) | **EVET, açıkça var**: "the facility achieved the targeted 24 MW threshold" | İçerik doğru/açık — düzeltme gerekmiyor; retrieval/atıf sorunu |
| ANK-COR-001 | DOC-CO-ADM-003 (hand-edited, `source_type: scanned_pdf`) | **EVET, açıkça var** (`.digital.pdf` ile doğrulandı): "%20 oranındaki hisse devri oy birliğiyle kabul edilmiştir" | İçerik zaten doğru, hand-edited → dokunulamaz zaten; ayrıca gerek yok. **Not:** servis edilen (rasterize) dosya pymupdf ile boş metin döner — bu TASARLANMIŞ bir davranıştır (taranmış belge simülasyonu, OCR öncesi), bir hata/bug değildir — gerçek içerik `.digital.pdf` eşleniğinde |
| IZM-DEV-011 | DOC-IZM-LEG-004 (hand-edited DEĞİL) | Eskiden **HAYIR, dolaylı**: "15.01.2025 tarihli idari kararlar" diyordu, "önlisans tarihi" ifadesiyle eşlemiyordu | **DÜZELTİLDİ** (bkz. §3) |

### Özet
- 2 soru (ANK-FIN-004, ANK-NEG-002) ve 2 soru (ANK-EPC-005, ANK-COR-001): belge içeriği
  zaten AÇIK/doğru — düzeltme gereksiz, başarısızlık (varsa) retrieval/atıf kaynaklı.
- 2 soru (ANK-FIN-006, ANK-FIN-012): `questions.json`'daki eski/yanlış kaynak tanımı —
  belge içeriği sorunu değil, dosyaya DOKUNULMADI (kapsam dışı).
- 3 soru (ANK-FIN-010, ANK-DAT-001, ANK-DAT-003): Excel-kaynaklı, kapsam dışı; ilk ikisi
  Adım 1 sonrası artık geçiyor.
- 2 soru (ANK-FIN-002, ANK-FIN-003): gerçek bir ledger↔belge kablolama boşluğu var
  (DOC-ANK-FIN-007'nin `key_facts`'i `total_debt`/`local_debt`'i hiç içermiyor) ama bunu
  doldurmak yeni bir yapısal bağlama ekler — "boş hücre doldur" kapsamını aşıyor, ÖNERİ
  olarak not edildi, uygulanmadı (ayrıca kaynak belge zaten hand-edited).
- 1 soru (IZM-DEV-011): gerçek, düzeltilebilir boşluk — **düzeltildi**.

## 3. IZM-DEV-011 düzeltmesi

`seed_data/generator/document_specs/izmir.py` → `DOC-IZM-LEG-004` spec'ine
`prose_guidance_tr` eklendi (bu mekanizma — "Düzeltme B", `generate_prose.py`'nin
`_build_prompt`'u — zaten mevcuttu, kullanılmamıştı):

```python
prose_guidance_tr=(
    "Değerlendirme Kapsamı bölümünde önlisans tarihini açıkça belirt: "
    "\"önlisans tarihi [[pre_licence_date]]'dir\" gibi bir cümleyle, yalnızca "
    "dolaylı bir idari karar referansı olarak değil."
),
```

`[[pre_licence_date]]` zaten `key_facts: {pre_licence_date: project.timeline.pre_licence.date}`
ile ledger'a bağlıydı — eksik olan yalnız LLM'e yön veren yönergeydi (IZM-DEV-003
düzeltmesinden farklı: burada tablo değil, serbest prose).

**Regenerasyon:** `--provider anthropic --only DOC-IZM-LEG-004 --force`,
`PROSE_BUDGET_USD=1.5` — **1 çağrı, 1227+1527 token, $0,0177** (bütçenin çok altında).
Yeni metin: *"Projenin önlisans tarihi 15.01.2025'dir."* — doğrulandı (bkz. §5).

## 4. Harcama

Toplam Adım 2 LLM harcaması: **$0,0177** (1 çağrı, DOC-IZM-LEG-004). $1,5 bütçesi
AŞILMADI, DUR tetiklenmedi.

## 5. Doğrulama

- `generate_documents.py` tüm 102 belgeyi yeniden üretti (0 hata).
- `validate_ledger --summary`: 0 hata, 1 uyarı (önceden var olan, ilgisiz: "izmir_res.yaml
  documents: G1: 21 documents, SPEC_05 §6 target ~15").
- `validate_documents` (full, başlık+sayı biçimi+dil+token-grep+self-reference dahil):
  **0 hata, 0 uyarı**.
- DOC-IZM-DEV-003 ve DOC-IZM-LEG-004'ün render edilmiş metni PyMuPDF ile tekrar okunup
  yeni cümleler teyit edildi.
- `make lint`: ✅ (ruff+format+mypy+ocr-worker lint+validate-ledger+validate-documents
  --prose-only+validate-excel).
- Solo `make test`: Adım 4'te raporlanacak (bu adımın parçası değil, ayrı commit).

Devam ediliyor: **Adım 3** (discovery eşleştirme kusuru — yalnız teşhis).
