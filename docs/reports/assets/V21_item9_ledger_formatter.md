# V21 R9 — ledger değer biçimlendirici genişletmesi: 13 "belge" kaydı tek tek

Kaynak sınıflama: `docs/reports/assets/T1_A_comertlik.md` §"(d) alt kırılımı" — "cevap var, değer
doğrulanmadı" 13 soru (+4 discovery `expect_no_answer` skip'i, ayrı konu, R3'e bakınız).
Yöntem: her sorunun `expected_answer` ledger yolu `seed_data/master/*.yaml`'da elle okundu,
gerçek canlı cevap metni (`results/m1_final_2026-10-16/results.json` ve `results/s3_rescored/
results.json`) karşılaştırıldı. **Yalnızca genişletme — hiçbir mevcut (önceden formatlanan)
alan değişmedi**; aşağıdaki üç kategori sadece önceden `None` dönen durumlara yeni bir biçim
ekliyor (`scripts/eval_lib.py::_literal_text_groups` / `_structural_money`).

| Soru | Ledger yolu | Ham değer | V21 sonrası durum | Gerekçe |
|---|---|---|---|---|
| ANK-FIN-015 | `...finance.drawdowns[0].amount.value` | `8000000` (+ `currency: USD` kardeşi) | **yeni doğrulanıyor** (yapısal para fallback) | Cevap literal "8.000.000 USD" diyor (M1 + S3r) — tam eşleşiyor. |
| ANK-OPS-002 | `...operations.incidents[0].type.value` | `"Türbin dişli kutusu arızası (T-07), 11 gün duruş"` | **yeni doğrulanıyor** (literal metin fallback, virgülle 2 bağımsız yan tümce) | Türkçe serbest metin, Türkçe harf içeriyor; cevap her iki yan tümceyi de (bitişik olmasa da) içeriyor. |
| ANK-EPC-004 | `...construction.change_orders[0].subject.value` | `"COD deferral: grid connection works"` | **hâlâ doğrulanamıyor** (bilerek) | İngilizce sözleşme alıntısı; gerçek cevaplar Türkçe paraphrase kullanıyor ("şebeke bağlantı işleri" — M1, "Proje... " — S3r), İngilizce metni asla birebir alıntılamıyor. Literal fallback Türkçe-harf kapısıyla bilerek devre dışı — yanlış regresyon riski (M1/S3r'de her iki cevap da doğru ama literal İngilizce eşleşmezdi). |
| ANK-FIN-010 | `...finance.covenant_tests[-1].result` | `"pass"` | **hâlâ doğrulanamıyor** (bilerek) | Ledger/Excel yalnızca İngilizce "pass"/"fail" içeriyor (`generate_excel.py:255,323` — formül sonucu); hiçbir üretilen belge/prose'da Türkçe karşılığı yok (hand-verify: yok). Alias eklenmedi — "doğrulanamazsa alias eklenmez" kuralına göre. |
| IZM-DEV-001 | `project.stage` | `"development"` | **hâlâ doğrulanamıyor** (bilerek) | Salt kod sınıflandırması (`validate_ledger.py:1101-1107`, SPV şekli seçimi) — hiçbir üretilen belgede/prose'da yazılı değil, hand-verify edilecek bir metin yok. Alias eklenmedi. |
| ANK-FIN-008 | `...finance.facility_chain[-1]` | `"DOC-ANK-FIN-006"` | **tasarım gereği, gap değil** | Belge kimliği (`DOC-*`) — `required_sources` ile kontrol ediliyor, literal metin değil. |
| ANK-FIN-009 | `...finance.facility_chain` | `[DOC-ANK-FIN-001..006]` | **tasarım gereği, gap değil** | Belge kimlikleri listesi, aynı sebep. |
| ANK-EPC-002 | `...construction.epc_contract_current_doc` | `"DOC-ANK-EPC-..."` | **tasarım gereği, gap değil** | Belge kimliği. |
| ANK-FIN-012 | `...finance.dscr_covenant.changed_by` | `"DOC-ANK-FIN-006"` | **tasarım gereği, gap değil** | Belge kimliği. |
| CO-NEG-005 | `company.documents[7].id` | `"DOC-CO-..."` | **tasarım gereği, gap değil** | Belge kimliği. |
| ANK-MIX-002 | `...operations.budget_vs_actual[3]` | `{period, budget, actual}` dict | **tasarım gereği, gap değil** | `questions.json` notu (ANK-MIX-003 ile aynı desen): MIXED'te değer kontrolü bilerek atlanır, kaynak+answered puanlanır. |
| ANK-MIX-003 | `...operations.budget_vs_actual[5]` | `{period, budget, actual}` dict | **tasarım gereği, gap değil** | Aynı — soru metninin kendi notu: "Değer kontrolü atlanır (dict), kaynak+answered puanlanır." |
| IZM-DEV-008 | `...development.pending_steps` | liste, serbest metin öğeleri | **ayrı mekanizma (V21 R6)** | Literal fallback değil — liste kapsamı sayaçı (`expected_items`, opt-in); bkz. V21 raporu §6. |

## Özet

- **Yeni doğrulanan VE geçen:** 2 — ANK-FIN-015, ANK-OPS-002 (her ikisinin de gerçek M1/S3r
  cevabı doğru değeri içeriyor; yeni zorunlu hale gelen `value_check` bu iki soruyu düşürmedi).
- **Yeni doğrulanan VE düşen:** 0 — hiçbir soru bu üç fallback yüzünden yeni fail olmadı
  (ANK-FIN-010/IZM-DEV-001 bilerek fallback kapsamı DIŞINDA bırakıldı, tam da bu riski
  önlemek için — aşağıya bakınız).
- **Hâlâ doğrulanamıyor (bilerek, veri/alias eksik):** 2 — ANK-EPC-004 (İngilizce alıntı),
  ANK-FIN-010 + IZM-DEV-001 birlikte 2 (enum kodu, hiçbir belgede Türkçe karşılığı yok).
- **Tasarım gereği, hiç gap olmayan:** 6 — ANK-FIN-008/009/012, ANK-EPC-002, CO-NEG-005
  (belge kimliği), ANK-MIX-002/003 (MIXED'te bilerek atlanan dict).
- IZM-DEV-008 ayrı bir mekanizmayla (R6, liste kapsamı sayacı) ele alınıyor, bu tablonun
  kapsamı dışında.

**Kontrolöre öneri (v14):** Yok — bu üç kategorinin hiçbiri questions.json değişikliği
gerektirmiyor (R9 saf puanlayıcı genişlemesi). ANK-FIN-010/IZM-DEV-001 için risk: gerçek bir
Türkçe karşılık belgelerde/prose'da üretilirse (gelecek bir faz), o zaman alias eklenebilir.
