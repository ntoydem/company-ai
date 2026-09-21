# SPEC 01 — Ürün, kapsam ve altyapı

## 1. Ürün vizyonu
Kullanıcı tek bir Company AI web uygulamasına giriş yapar; belge görüntüler, yükler, şirket belgelerine doğal dilde soru sorar, Excel dosyalarını doğal dille analiz eder ve **her cevabın hangi kaynaktan geldiğini görür**. Sistem ileride e-mail, ERP ve operasyon verilerini aynı hafıza altında birleştirebilecek şekilde tasarlanır; V0'da bunlar YOKTUR.

Organizasyon yapısı:
- Enerji Grubu → Geliştirme (Development), EPC / İnşaat, Bakım
- Finans
- Hukuk
- Mali İşler
- İdari İşler

Finans / Mali İşler sınırı (karar): **Finans** = proje finansmanı, kredi, hazine, banka ilişkileri, finansal model, covenant. **Mali İşler** = muhasebe, vergi, fatura, ödeme, denetim, SGK.

## 2. Dil
UI ve README Türkçe (tr-TR, DD.MM.YYYY). Örnek UI metinleri: Belge Yükle, Belgeler, Projeler, Finans, Hukuk, Kaynaklar, Erişim Yetkileri, Yönetim, AI'ya Sor, Genel Sor, Sorunuzu yazın. Kod/şema/API İngilizce. AI varsayılan Türkçe cevap verir; kaynak İngilizce olsa bile.

## 3. V0 kapsamı
**Var:** kullanıcı girişi, rol + departman yetkilendirmesi, proje yönetimi, doküman yükleme (web), OCR/sayfa bazlı metin/indexleme, metadata, AI metadata önerisi, doküman soru-cevap, kaynak gösterme, Excel analiz motoru, mixed query (basit), audit log, demo veri seti, otomatik testler, Proxmox deployment, backup/restore.
**Yok:** CLAUDE.md'deki liste. Scope büyütülmez.

## 4. Topoloji
```
Proxmox → Ubuntu 24.04 VM (4 vCPU, 6→16 GB, 100 GB NVMe) → Docker Compose
  caddy        :8080 (LAN, HTTP)  → frontend (static) + /api → backend
  frontend     Vite build, Caddy tarafından servis edilir
  backend      FastAPI
  postgres     pgvector/pgvector:pg16 — DB: company_ai
  ocr-worker   ocrmypdf + PyMuPDF; ingestion_jobs tablosunu poll eder
  embed        bge-m3 (opsiyonel, profile full, EMBEDDINGS_ENABLED)
```
Tek VM, tek compose projesi. Paperless/Tika/Gotenberg/Valkey yok; PDF/xlsx/csv (+png/jpg tarama) yeterli.

## 5. Stack
CLAUDE.md'de sabitlenmiştir. Ek notlar:
- LLM env: `LLM_PROVIDER=openai_compatible|anthropic`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL_CLASSIFY`, `LLM_MODEL_ANSWER`, `LLM_TIMEOUT_S`, `LLM_MAX_OUTPUT_TOKENS`.
- Varsayılan: Gemini OpenAI-uyumlu endpoint; sınıflandırma Flash-Lite sınıfı, cevap Flash sınıfı. Model adları `.env.example`'da güncel resmi dokümandan alınır.
- Gemini'de "thinking" token'ları çıkış olarak faturalanır; `reasoning`/thinking bütçesi düşük tutulur. Token sayıları her çağrıda kaydedilir.
- Secrets yalnızca `.env`. `.env` commit edilmez; `.env.example` tüm değişkenleri açıklamalı listeler.

## 6. Belge hattı (ingestion pipeline)
1. Upload → dosya `$DATA_ROOT/documents/<uuid>/original.<ext>`, `documents` kaydı (`ingestion_status=uploaded`), `ingestion_jobs` kaydı.
2. `ocr-worker` job'ı alır: PDF ise `ocrmypdf --skip-text --language tur+eng --rotate-pages --deskew` → `ocr.pdf`; png/jpg ise önce PDF'e çevrilir. Hata → `failed` + sebep.
3. Sayfa bazlı metin: PyMuPDF ile her sayfa → `document_pages(document_id, page_number, text)`.
4. Chunking (~800 token, 100 overlap, sayfa sınırı korunur) → `document_chunks(page_number dolu)`; Postgres FTS; embedding açıksa vektör.
5. `ingestion_status=ready`.
Depolama `DocumentStore` arayüzü arkasındadır (`store/get_file/get_text`); ileride SharePoint/başka depo takılabilir. Metadata'nın tek kaynağı Postgres'tir.

## 7. İki ayrı AI çalışma modu — KESİNLİKLE ayrı
**A — Production Company AI:** varsayım YAPMA, rakam/tarih/olay UYDURMA, eksik bilgiyi model bilgisiyle doldurma. Kaynak yoksa: "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım."
**B — Synthetic Demo Data Generator:** yalnızca `seed_data/generator/` altında çalışır; eksik değerleri kontrollü üretir, her üretilen değer ledger'da `AI_ASSUMPTION` etiketiyle durur. Prensip: **minimum yaratıcılık + maksimum tutarlılık**. Generator kodu production backend'e import edilmez.

## 8. Gelecek mimari (implement ETME)
Router → Document AI (belge hattı) | Data AI (Excel/SQL) | Email AI (M365, V0 dışı) → AI Reasoning → Answer + Sources. Provider ve retrieval abstraction'ları bu yönde genişlemeyi engellememeli; ama bugün yalnızca ilk ikisi vardır.
