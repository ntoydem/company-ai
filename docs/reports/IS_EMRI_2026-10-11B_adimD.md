# İş Emri 2026-10-11-B — Adım D Raporu (solo `make test`)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **hedef karşılandı: 0 hata**

## 1. İlk koşu — 4 hata (beklenen, Hukuk partisinin doğal sonucu)

```
FAILED tests/test_demo_documents_seed.py::test_seed_creates_87_pdfs_plus_7_workbooks_and_queues_pdf_jobs
FAILED tests/test_demo_documents_seed.py::test_seed_is_idempotent
FAILED tests/test_demo_documents_seed.py::test_financial_model_is_seeded_normal_after_question_15
FAILED tests/test_demo_documents_seed.py::test_refresh_resyncs_only_named_gate_fields_from_the_manifest
4 failed, 653 passed, 15 deselected
```

**3'ü** Adım 5'te de görülen desen: Adım C'nin +15 belgesi sonrası eski sayım testleri
(94→109, 87→102 PDF) güncellenmemiş kalmıştı. **4.'sü yeni bir desen:**
`test_financial_model_is_seeded_normal_after_question_15` "hiçbir belge restricted
olmasın (DOC-ANK-FIN-008 hariç)" diyordu — ama Hukuk partisinin 15 dava belgesi artık
**kasıtlı olarak** `restricted` (kaynak: "Dava belgeleri restricted, Soru 15 = A").

Hiçbiri bir gate/eşik/hand-edited/kaynaksız-bilgi sorunu DEĞİL — yalnız testlerin eski
korpus boyutuna/varsayımına bağlı kalmış olması. ÖNCEDEN VERİLMİŞ KARAR 4 ruhuyla
("kapı yanlış-pozitifi çıkarsa kapıya dokunma, değeri eşdeğer biçimde yaz") davranıldı:
testlerin KENDİSİ güncellendi, hiçbir eşik/doğrulama mantığı gevşetilmedi.

**Düzeltme:**
- 3 sayım testi: 94→109, 87→102 PDF (workbook 7 değişmedi).
- 4. test: "hiçbir belge restricted olmasın" → "**hukuk dışında** hiçbir belge restricted
  olmasın" (orijinal amacı — yanlışlıkla restricted kalan bir belge olmaması —
  korunarak daraltıldı; `d.department != "hukuk"` filtresi eklendi).

## 2. İkinci koşu — 0 hata

```
657 passed, 15 deselected, 14 warnings in 794.33s (0:13:14)   # backend
18 passed, 1 warning in 6.94s                                 # ocr-worker
```

`make test` tam koşusu (backend + şema assert + ocr-worker): **0 hata, 0 kalan uyarı dışı
sorun.** Hedef karşılandı.

## 3. Commit

`f6b8140` — `backend/tests/test_demo_documents_seed.py` güncellemesi.

Devam ediliyor: **Adım E** (bitiş bildirimi).
