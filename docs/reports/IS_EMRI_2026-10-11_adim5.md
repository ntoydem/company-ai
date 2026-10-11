# İş Emri 2026-10-11 — Adım 5 Raporu (Kategori B + FIN-013)

**Konu:** `counterparty` kök neden düzeltmesi + 20 belge · **Tarih:** 11.10.2026 ·
**Durum:** ✅ tamamlandı — **İş emrinin tamamı bitti** (solo `make test`: 0 hata)

## 1. Kök neden düzeltmesi

`facts.py::build_facts()`'te `counterparty` eskiden tek taraflı belgelerde sessizce
`spv_name`'e düşüyordu — SPV kendi kendinin "karşı tarafı" gibi görünüyordu. Bu, aynı
cümlede `[[spv_name]]` ile birlikte kullanılınca self-reference hatasına yol açıyordu
(DOC-ANK-OPS-008, DOC-CO-ADM-009 — Adım 3'ün bulguları). Düzeltme:
`counterparty`/`counterparty_list` artık **yalnız gerçek bir karşı taraf varsa** facts
dict'ine eklenir (tıpkı Adım 1'in `counterparty_list`'i gibi). Tek taraflı bir belgenin
prose'u hâlâ `[[counterparty]]` kullanırsa artık **"bilinmeyen token" olarak reddedilir**
— sessizce yanlış bir değere düşmez.

Manifest/DB'nin `counterparty` alanı (backend NOT NULL) ayrı bir amaç taşıdığı için orada
spv_name fallback'i BİLEREK korundu — yalnız LLM'e giden facts dict'inden kaldırıldı.

**Ek bulgu (regenerasyon sırasında):** DOC-CO-ADM-009'un ilk yeniden üretimi
`[[parties_list]]` + `[[spv_name]]`'i AYNI CÜMLEDE kullanarak aynı hatayı farklı bir
cümlede tekrar üretti (parties_list de SPV'yi içeriyor — counterparty_list ile aynı
risk). `generate_prose.py`'nin sistem promptuna "KURAL 3/RULE 3" eklendi (bu ikiliyi asla
aynı cümlede kullanma); 2. denemede düzeldi. **Not:** bu, kapının (validator'ın) kendisine
dokunmak DEĞİL — kapı ilk denemede DOĞRU ŞEKİLDE başarısız oldu, ben girdiyi (sistem
promptunu) düzelttim ki kapıyı geçebilsin. DURMA KURALI'nın "aynı kapı 2 kez başarısız
olursa dur" maddesi tetiklenmedi çünkü 2. deneme başarılı oldu.

## 2. 6+1 belgeye gerçek karşı taraf (AI_ASSUMPTION)

| doc_id | Karşı taraf | Not |
|---|---|---|
| DOC-ANK-DEV-001 | EPDK | **hand-edited** — prose'a dokunulmadı, yalnız `parties` listesi |
| DOC-ANK-DEV-004 | İlçe Belediyesi | |
| DOC-ANK-DEV-005 | ÇŞİDB | |
| DOC-ANK-OPS-005 | Enercon Servis Türkiye | |
| DOC-IZM-DEV-001 | EPDK | belge USER_FACT, karşı taraf AI_ASSUMPTION (ayrı not) |
| DOC-IZM-DEV-008 | MSB | |
| **DOC-IZM-DEV-006** (plan dışı) | ÇŞİDB | iş emrinin 6'lık listesinde YOK — kök neden düzeltmesi sırasında generate_documents.py'nin "unknown placeholder" hatasıyla kendiliğinden ortaya çıktı |

6'sı da (DOC-ANK-DEV-001 hariç) mevcut prose'ları `[[counterparty]]`'yi ZATEN anlamlı
kullanıyordu (örn. "onaylanan ruhsat", "ile koordineli") — yeniden üretim GEREKMEDİ, yalnız
ledger `parties` listesi genişletildi ve `generate_documents.py` yeniden çalıştırıldı.

**DOC-ANK-DEV-001 özel durum:** prose hand-edited (`prose/DOC-ANK-DEV-001.yaml
hand_edited:`). Prose'a DOKUNULMADI (GENEL kuralı + DURMA KURALI). Yalnız ledger'ın
`parties` listesine EPDK eklendi — hand-edited metin zaten `[[counterparty]]`'yi anlamlı
kullanıyordu ("İlgili mevzuat çerçevesinde [[counterparty]] kurumunun denetim yetkisi
saklı tutulmuştur"), token artık EPDK'ya çözülüyor.

## 3. 13 iç belgeden karşı taraf token'ı kaldırıldı

DOC-ANK-ADM-001, DOC-ANK-OPS-001/006/007/008, DOC-CO-ADM-005/007/008/009/010,
DOC-IZM-ADM-001/002/003 — tek taraflı, `[[counterparty]]` artık facts dict'inde yok.
13'ü de `generate_documents.py`'nin "unknown placeholder" hatasıyla tek tek yakalandı
(hiçbiri hand-edited değildi, önceden doğrulandı) ve 1'er Claude çağrısıyla yeniden
üretildi — hepsi ilk denemede kabul edildi (DOC-CO-ADM-009 hariç, bkz. §1).

## 4. DOC-ANK-FIN-013 (Adım 3'ten kalan, Naci'nin kararıyla eklendi)

Hand-edited DEĞİL (doğrulandı). Kök neden Adım 1'in DOC-IZM-LEG-002 bulgusuyla aynı:
`"specifically including [[parties_list]] and [[spv_name]]"`. Aynı çözüm uygulandı
(`prose_suppress_facts={"parties_list"}` + guidance → `[[counterparty_list]]` kullan).
1 çağrı, ilk denemede kabul.

## 5. Kapı sonuçları

| Kapı | Sonuç |
|---|---|
| lint (ruff + mypy + validate-ledger + validate-documents --prose-only + validate-excel) | ✅ |
| validate-ledger (tam) | ✅ 0 hata/uyarı |
| validate-documents (full, 87 belge) | ✅ **0 hata** (Adım 3'teki 3 hatadan 0'a) |
| token-grep (87 belge) | ✅ 0 çözülmemiş `[[token]]` |
| **solo `make test`** (backend 657 + ocr-worker 18, şema assert) | ✅ **0 hata — hedef karşılandı** |

İlk solo `make test` koşusu 3 hata verdi (`test_demo_documents_seed.py` — Adım 4'ün
+3 PDF/+1 workbook'u sonrası 84+6=90 bekleyen eski sayım testleri). Bu, kaynağı olmayan
bilgi/hand-edited/kilitli eşik DEĞİL — yalnız güncel korpus boyutuna uyum (90→94,
84→87, 6→7); testler güncellendi, gevşetme yapılmadı. 2. solo koşu: **657 passed + 18
passed, 0 failed.**

## 6. Maliyet

| Grup | Tutar |
|---|---|
| 7 doküman (DOC-ANK-FIN-013 dahil, 1. deneme) | $0,0698 + $0,0104 (FIN-013) |
| 6 doküman (ikinci grup) | $0,0708 |
| DOC-CO-ADM-009 2. deneme (KURAL 3 sonrası) | $0,0158 |
| **Adım 5 toplamı** | **$0,1564** |

**Kümülatif iş emri:** $0,0262 (Adım 1+2) + $0,0372 (Adım 4) + $0,1564 (Adım 5) =
**$0,2198 / $1,2.**

## 7. Commit'ler

1. `f4ce812` — facts.py/generate_documents.py/generate_prose.py (kök neden + KURAL 3).
2. `be9f4c6` — ankara_res.yaml + izmir_res.yaml (7 karşı taraf eklendi).
3. `22bc15c` — ankara_finance.py + DOC-ANK-FIN-013 prose.
4. `949bc3a` — 13 iç belgenin prose'u.
5. `e5a3395` — test_demo_documents_seed.py (90→94).
6. (bu rapor) — ayrı commit.

## 8. İş emri tamamlandı — final durum tablosu

| Adım | Durum |
|---|---|
| 1 | ✅ tamamlandı (`5820fa4`) |
| 2 | ✅ tamamlandı (`81f1b9a`) |
| 3 | 🛑 durdu → Naci kararıyla çözüldü |
| 4 (Boztepe PF-2) | ✅ tamamlandı (`bf70e2a`) |
| 5 (Kategori B + FIN-013) | ✅ tamamlandı (bu rapor) |
| **Solo `make test` (hedef: 0 hata)** | ✅ **0 hata** |

İş emrinin tamamı bitti. Kümülatif maliyet $0,2198 / $1,2 (bütçenin %18'i). El
düzenlemeli belgeler (FIN-001, FIN-004, DEV-001, EPC-002, FIN-006, IZM-DEV-003,
CO-ADM-003) hiçbiri yeniden üretilmedi/üzerine yazılmadı. Hiçbir test/kapı eşiği
gevşetilmedi.
