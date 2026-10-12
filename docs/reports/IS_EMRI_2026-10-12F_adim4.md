# İş Emri 2026-10-12-F — Adım 4 Raporu (solo `make test`)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — **0 hata.**

## Sonuç

```
backend:     682 passed, 15 deselected, 14 warnings in 827.46s (0:13:47)
ocr-worker:  18 passed, 1 warning in 6.59s
pipeline schema: present (document_chunks, document_pages, documents, ingestion_jobs)
```

Tek koşu (solo), paylaşılan test DB'si üzerinde, `make test` ile. Uyarılar önceden var
olan, ilgisiz (JWT anahtar uzunluğu test fixture'larında, WeasyPrint/anyio deprecation) —
bu iş emrinin kapsamına girmiyor, dokunulmadı.

## İş Emri 2026-10-12-F — genel özet (4 adım tamamlandı)

1. **Kod hataları:** 9 sorunun ortak kök nedeni (`polars.exceptions.ComputeError`,
   `app/excel/calc.py::_frame`) bulundu ve düzeltildi; E emrinin "Gemini'ye özgü"
   hipotezi traceback'le YANLIŞLANDI (tek, sağlayıcıdan bağımsız kök neden).
2. **Belge içeriği:** IZM-DEV-003'ün bekleyen-adımlar tablosu + IZM-DEV-011'in belge
   içeriği (DOC-IZM-LEG-004) düzeltildi (1 Claude çağrısı, $0,0177, bütçenin çok altında);
   kalan 10+1 sorudan çoğu zaten içerik-doğru (retrieval sorunu) veya hand-edited/Excel-
   kaynaklı/eski test tanımı nedeniyle kapsam dışı — raporlandı, uygulanmadı.
3. **Discovery eşleştirme kusuru:** iki somut, veriyle doğrulanmış kök neden teşhis
   edildi (`common_threshold` küratörlü glossary terimlerini de eliyor;
   `is_existence_question()` terim-tanımı kalıplarını tanımıyor) — düzeltme ÖNERİLDİ,
   UYGULANMADI (talimat gereği).
4. **Solo `make test`:** 0 hata.

Tüm kapılar (`make lint`, `validate_ledger`, `validate_documents`, `validate_excel`)
boyunca yeşil kaldı; $1,5 bütçe aşılmadı (toplam harcama $0,0177); canlı DB/`.env`/backend'e
dokunulmadı; held-out ve el düzenlemeli belgelere dokunulmadı.
