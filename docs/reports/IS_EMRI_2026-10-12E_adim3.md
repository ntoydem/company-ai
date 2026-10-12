# İş Emri 2026-10-12-E — Adım 3 Raporu (C1'deki 9 HTTP 500 hatası)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — **düzeltme yapılmadı**, kod/belge
değiştirilmedi. **Kısıt:** ayrı eval ortamı (`company-ai-eval`) D emrinin Adım 5'inde
durdurulup kaldırıldı — konteyner logları (traceback) bu işlemle birlikte silindi,
yeniden kurulmadı (talimat gereği). Bu rapor yalnız `results.json`'daki hata gövdesi ve
üç sağlayıcı arasındaki üreme (reproducibility) deseninden çıkarılabilen kanıtla
sınırlıdır.

## 1. Mevcut kanıt

Her 9 hatanın gövdesi BİREBİR aynı, genel (whitelist'siz) bir mesaj:
```
{"detail":"Beklenmeyen bir hata oluştu. Lütfen daha sonra tekrar deneyin.","request_id":"..."}
```
Bu, `backend/app/core/errors.py::unhandled_exception_handler`'ın (HTTP 500,
`GENERIC_ERROR_MESSAGE`) imzasıdır — **`LLMError` ailesinin DEĞİL** (o aile her zaman 503
ve farklı bir mesaj döner, `llm_exception_handler`). Yani bu 9 hata **LLM sağlayıcısının
kendisinden (429/503/zaman aşımı) gelmiyor** — uygulamanın kendi kodunda, LLM çağrısından
ÖNCE veya SONRA, yakalanmamış bir istisna var.

## 2. Sınıflama — her hata, üç sağlayıcıda üreme durumuyla

| Soru | Kategori | C1 | C2 | C3 | Sınıf |
|---|---|---|---|---|---|
| GEN-DSC-001 | discovery | 500 | ✅ çalıştı | ✅ çalıştı | **Gemini'ye özgü** |
| GEN-DSC-011 | discovery | 500 | ✅ çalıştı | ✅ çalıştı | **Gemini'ye özgü** |
| GEN-DSC-001-M | discovery | 500 | ✅ çalıştı | ✅ çalıştı | **Gemini'ye özgü** |
| GEN-DSC-011-K | discovery | 500 | ✅ çalıştı | ✅ çalıştı | **Gemini'ye özgü** |
| ANK-FIN-011 | document | 500 | ✅ çalıştı, geçti | ✅ çalıştı, geçti | **Gemini'ye özgü** |
| ANK-FIN-010 | data | 500 | ✅ çalıştı (yanlış cevap) | ✅ çalıştı (yanlış cevap) | **Gemini'ye özgü** |
| ANK-DAT-001 | data | 500 | ✅ çalıştı (yanlış cevap) | ✅ çalıştı (yanlış cevap) | **Gemini'ye özgü** |
| ANK-DAT-003 | data | 500 | ✅ çalıştı (yanlış cevap) | ✅ çalıştı (yanlış cevap) | **Gemini'ye özgü** |
| ANK-MIX-001 | mixed | 500 | **500 (farklı request_id)** | **500 (farklı request_id)** | **ORTAK backend hatası** |

**Sonuç: 8/9 yalnız Gemini (C1) yolunda üretiliyor, Claude (C2 VE C3, iki farklı answer
modeliyle) yolunda HİÇBİRİNDE üretilmiyor — güçlü, tekrarlanan bir kanıt.** `ANK-MIX-001`
ayrı: üç sağlayıcıda da (üç farklı `request_id` ile, yani üç kez bağımsız tetiklenerek)
500 veriyor — bu belirli sorunun kendi verisinde/işleme yolunda, LLM sağlayıcısından
TAMAMEN bağımsız bir hata olduğunu gösteriyor.

## 3. Kök neden — DOĞRULANAMADI (traceback yok), kanıta dayalı HİPOTEZ

**`ANK-MIX-001` (ortak hata):** `mixed` kategorisi `/api/ask`'ta router + belge cevabı +
Excel planı + Excel yorumu olmak üzere 4 LLM çağrısı ve ek bir Excel/DuckDB işleme adımı
içerir (`excel_ask.py::answer_data_question`). Üç sağlayıcıda da bağımsız olarak çöktüğü
için hata **LLM çağrılarının ARASINDA/SONRASINDA çalışan Python kodunda** olmalı — en
olası adaylar: bu sorunun özel Excel/DuckDB sorgusu (`excel_ask.py`) veya `ask.py`'nin
MIXED birleştirme mantığı. **Bu bir hipotezdir, traceback'le doğrulanmadı.**

**8 Gemini'ye özgü hata:** Hepsi `llm.complete()` BAŞARIYLA döndükten SONRA tetikleniyor
olmalı (aksi halde `LLMError`→503 olurdu, 500 değil) — yani Gemini'nin DÖNDÜRDÜĞÜ metnin
BİÇİMİ/İÇERİĞİ, `ask.py`/`eval` sonrası işleme kodunun (örn. `tr_format.polish_answer`,
`answer_prompt.order_sources`, `split_question_line`, ya da discovery/pending_documents
eşleştirme adımı) beklemediği bir şekle bürünüyor ve bu kod bir istisna fırlatıyor. Claude
(Haiku/Sonnet, ikisi de) bu belirli giriş setinde bu şekli hiç ÜRETMİYOR — bu yüzden aynı
kod yolu Claude'la hiç tetiklenmiyor. **Hangi fonksiyon/satır olduğu DOĞRULANAMADI** —
konteyner logları silinmiş durumda; yeniden kurup tekrar tetiklemek bu iş emrinin "ortamı
yeniden kurma" kısıtını ihlal ederdi.

## 4. Belirsiz bırakılan (dürüstçe)

Gemini'ye özgü 8 hatanın TAM kod satırı/istisna türü **belirsiz** — yalnız "LLM çağrısından
SONRAKİ bir işleme adımı, Gemini'nin belirli bir çıktı şekliyle tetikleniyor" sonucu
çıkarılabiliyor. Düzeltme için traceback gerekir; bu iş emri onu sağlayamıyor (ortam kapalı,
yeniden kurulmadı). **Düzeltme YAPILMADI** (talimat).
