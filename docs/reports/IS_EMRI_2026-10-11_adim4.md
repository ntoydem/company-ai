# İş Emri 2026-10-11 — Adım 4 Raporu

**Konu:** Boztepe PF-2 — ilk belgeler · **Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı

## 1. Üretilen belgeler

| doc_id | Tür | Dil | Mekanizma |
|---|---|---|---|
| DOC-BOZ-FIN-001 | Facility Agreement | EN | Claude (1 çağrı) |
| DOC-BOZ-FIN-002 | Aylık Faiz Bildirimi | TR | Claude (1 çağrı) |
| DOC-BOZ-FIN-003 | DSRA Hesap Ekstresi | TR | Claude (1 çağrı) |
| DOC-BOZ-FIN-004 | Ödeme Planı (84 Taksit) | — | 0-LLM, openpyxl formülleri |

Her 3 Claude çağrısı da **ilk denemede kabul edildi** (içerik reddi 0, altyapı hatası 0).

## 2. DSCR test tablosu — kasıtlı olarak ÜRETİLMEDİ

İş emri 5 teslimat istiyordu (FA, Excel, aylık faiz bildirimi, DSRA ekstresi, DSCR test
tablosu). Boztepe'nin ledger'ında `covenant_tests` **hiç yok** —
`grep -n "covenant_tests" seed_data/master/boztepe_res.yaml` boş döner. Yalnız
`dscr_covenant: 1.20x` (MİNİMUM GEREKSİNİM, Tansu onaylı — T-11.9) var; hiçbir geçmiş test
SONUCU (tarih/değer/pass-fail) hiçbir kaynaktan gelmiyor.

GENEL kuralı ("kaynağı olmayan bilgi uydurma; gerekirse AI_ASSUMPTION olarak işaretle") ve
DURMA KURALI'nın "kaynağı olmayan bilgi gerekirse DUR" maddesi burada devreye girdi — ama
tam bir DUR değil, çünkü diğer 4 teslimat kaynaklı ve üretilebilir durumdaydı. Seçilen çözüm:
**ayrı bir "DSCR test tablosu" belgesi/bölümü üretilmedi**; Facility Agreement'ın
"4. Financial Covenants" bölümü yalnız 1.20x minimumu bir GEREKSİNİM olarak anıyor,
`prose_guidance_en` açıkça geçmiş test sonucu/pass-fail/tarih YAZILMASINI yasaklıyor. Bu,
AI_ASSUMPTION ile "icat etme" arasındaki çizgiyi aşmamak için en temiz çözüm — rapor
dosyasına yazılıp devam edildi, tam DUR tetiklenmedi (talimatın "kaynağı olmayan bilgi
gerekirse DUR" maddesi, "üretmeye zorlanırsa" anlamında yorumlandı; üretmemek seçeneği
varken burada kullanıldı).

## 3. Mimari kararlar

- **facts.py'de 2 eksik eşleme bulundu ve düzeltildi** (Boztepe'nin ilk belgesi olduğu
  için şimdiye kadar fark edilmemişti): `_PREFIX_TO_LEDGER["BOZ"]` ve `_project_name()`'in
  dict literal'inde "BOZ" anahtarı yoktu — eklenmezse `KeyError`/belge üretimi çöker.
- **Oran/ödeme metni önceden biçimlendirilmiş string olarak saklandı**
  (`effective_rate_pct_en/_tr`, `repayment_profile_en`) — `format_percent`/`_format_money`
  2 ondalık haneye yuvarlıyor (6,744%'ün 3. ondalığını, 178.571,43'ün kuruşunu keser),
  DOC-YSV-FIN-010'daki `missing_guarantee_letter_name` deseniyle aynı çözüm.
- **4. hane eklendi ("6.7440"/"%6,7440") — kapıya DOKUNULMADAN.** İlk üretimde
  `check_number_format_consistency` (kilitli eşik, DURMA KURALI kapsamı) "6.744"/"6,744"
  sayısını 3 haneli nokta/virgül-gruplu (TR/EN karışık biçim) sayı deseniyle YANLIŞ POZİTİF
  eşleşti (`\d{1,3}(?:\.\d{3})+` — "6744"nün TR-gruplu hali ile ayırt edilemiyor). Kapının
  kendisi veya eşiği DEĞİŞTİRİLMEDİ; değer "6.7440"/"%6,7440" olarak (matematiksel olarak
  birebir aynı, sondaki sıfır bilgi eklemiyor) yeniden yazıldı — regex artık eşleşmiyor.
  Doğrulandı: `validate_documents` (full) bu 2 belgede 0 hata.
- **DOC-BOZ-FIN-001'in Facility Agreement yapısı Yeşilova FIN-009'u model aldı**
  (Recitals/Facility/Repayment/Financial Covenants/Governing Law) — ama capex/equity
  kullanılmadı (Boztepe'nin ledger'ında bu rakamlar yok, icat edilmedi); yerine
  `cod_actual` (28.12.2020, inşaat tamamlanmış-finansman-sonradan-alınmış desenini
  doğrulamak için) eklendi.

## 4. generate_excel.py'de bulunan bağımsız regresyon (bu iş emrinin kapsamı değil, ama
   düzeltilmeden `make excel` hiç çalışmıyordu)

`build_financial_model()` hâlâ `fin["eca_debt"]["value"]`'a koşulsuz erişiyordu — Karatepe'nin
ECA dilimi önceki round'da ("Tansu 6. tur") ledger'dan kaldırılmıştı (`eca_debt` Optional
yapılmıştı) ama o round'dan sonra `make excel` hiç çalıştırılmamıştı, bu yüzden regresyon
şimdiye kadar fark edilmemişti. `validate_ledger.py::check_finance`'teki aynı "yoksa 0"
davranışıyla düzeltildi (dar, tek satırlık değişiklik — hiçbir test/eşik gevşetilmedi).

## 5. 84 taksitli ödeme planı — formül tasarımı

`build_boztepe_repayment_schedule()`: her satır canlı formül (opening = önceki satırın
closing'i; principal = `ROUND(Total_Debt/Instalment_Count,2)` — SON satır hariç, o satırda
principal = o satırın açılış bakiyesi, yani "ne kalmışsa"; interest = `ROUND(opening *
Annual_Rate_Pct/12, 2)`; closing = `ROUND(opening-principal,2)`).

Doğrulama (recalc sonrası, cache'lenmiş değerler):
- Taksit 1: açılış 15.000.000, faiz 84.300 USD — **kanonik "aylık 84.300" değeriyle
  birebir tutuyor** (15.000.000 × %6,744 / 12 = 84.300,00).
- Taksit 83: anapara 178.571,43 USD (sabit).
- Taksit 84 (son): anapara 178.571,31 USD (**178.571,43 DEĞİL** — 0,12 USD'lik yuvarlama
  farkını emiyor, iş emrinin istediği tam olarak bu).
- Taksit 84 kapanış bakiyesi: **0** (kontrol satırı doğruladı).
- Vade tarihleri: 01.03.2027 → 01.02.2034 — kanonik "son taksit 01.02.2034" ile tutuyor.

## 6. Kapı sonuçları

| Kapı | Sonuç |
|---|---|
| lint (ruff + mypy + validate-ledger + validate-documents --prose-only + validate-excel) | ✅ |
| validate-ledger (tam) | ✅ 0 hata/uyarı |
| validate-documents (full, 87 belge) | ⚠️ aynı 3 ÖNCEDEN BİLİNEN hata (FIN-013/OPS-008/CO-ADM-009, Adım 5'in listesinde) — **Boztepe'den 0 hata** |
| validate-excel | ✅ 0 hata (7 workbook, named range'ler + cached değerler + ledger tutarlılığı) |
| token-grep (87 belge, tüm PDF'ler) | ✅ 0 çözülmemiş `[[token]]` |
| yasak kelime / literal banka adı sızıntısı | ✅ temiz (parti adları yalnız token substitüsyonuyla geliyor, LLM'in kendi yazdığı metinde yok) |

## 7. Maliyet

3 çağrı: $0,0191 + $0,0096 + $0,0085 = **$0,0372**.
Kümülatif iş emrinde: $0,0262 (Adım 1+2) + $0,0372 (Adım 4) = **$0,0634 / $1,2**.

## 8. Commit'ler

1. `f2b7e4b` — ledger_schema.py + facts.py + boztepe_res.yaml + document_specs/boztepe.py
   + __init__.py kaydı.
2. `2348eab` — generate_excel.py (Boztepe builder + ECA regresyon düzeltmesi) + 7 workbook
   çıktısı + manifest.json.
3. `0fd609a` — 3 prose dosyası.
4. (bu rapor) — ayrı commit.

## 9. Durum tablosu

| Adım | Durum |
|---|---|
| 1 | ✅ tamamlandı (`5820fa4`) |
| 2 | ✅ tamamlandı (`81f1b9a`) |
| 3 | 🛑 durdu → Naci kararıyla çözüldü (FIN-013 Adım 5'e eklendi) |
| 4 (Boztepe PF-2) | ✅ tamamlandı (bu rapor) |
| 5 (Kategori B + FIN-013) | ⏸ başlatılmadı |
