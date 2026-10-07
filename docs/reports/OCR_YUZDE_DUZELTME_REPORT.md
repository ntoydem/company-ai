# Rapor — Taranmış belgede bozuk yüzde ("9020") düzeltmesi: seçenek (b) + (c)

**Tarih:** 07.10.2026  **Model:** Fable 5.1  **Karar:** Naci — (b) ve (c) onaylandı, (a) reddedildi (dijital metin katmanını kopyalamak taranmış belgelerin OCR test amacını bozar). **Bulgu:** 06.10.2026 taraması — `DOC-CO-ADM-003` (Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı, `scanned_pdf`, tr) s.3 "**9020** oranındaki hisse devri"; ledger `%20`; ocrmypdf `%` glifini "90" okudu. Prose ve ledger'a **dokunulmadı**. ADR-029.

## 0. Yedek
`make backup` → `data/backups/2026-10-07/` (postgres.dump 500 KB, documents.tar.gz 850 MB, excel.tar.gz, env.backup) — işlemden önce alındı.

## 1. (b) Generator: taranmış belgelerde OCR dostu yüzde
- `seed_data/generator/facts.py`: `format_percent(value, language, *, ocr_friendly=False)` — `tr` + `ocr_friendly` → `yüzde 20` (aksi halde `%20`; `en` değişmez `20%`). `format_value(...)` bayrağı yalnızca `percent` türüne iletir; `build_facts` bayrağı **yalnızca `source_type == "scanned_pdf"`** belgeler için açar. Tablo üreticileri (`_production_table`, `%97,5` gibi) ve eval'in `format_ledger_leaf`'i değişmedi. Prose (`[[ghi_share_pct]]`) ve ledger aynen.
- **Yalnızca DOC-CO-ADM-003 yeniden üretildi:** generator tüm belgeleri üretir; bu yüzden önce `seed_data/documents_tmp/` içine tam üretim yapıldı ve karşılaştırıldı: 79 PDF'nin **77'si içerik olarak (sayfa metni + gömülü görüntü baytları) birebir aynı**, yalnızca ADM-003'ün `.pdf` + `.digital.pdf` çifti farklı; manifest'te ADM-003 dışında hiçbir girdinin alanı değişmedi. Bayt düzeyinde ise WeasyPrint her koşuda PDF üstverisini (tarih/ID) değiştirdiğinden tüm dosyalar farklıydı — bu yüzden **yalnızca ADM-003'ün iki dosyası ve manifest'teki ADM-003 girdisi (+ `generated_at`)** `seed_data/documents/` içine alındı; diğer 77 dosya dokunulmadı → **sha256'ları değişmedi** (önce/sonra listesi karşılaştırıldı; yalnızca iki ADM-003 dosyası farklı). Not: `seed_data/documents/` `.gitignore`'da (üretilen çıktı, commit edilmez); hash kontrolü yerel disk üzerindedir.
- `make validate-documents` → 0 hata (G4: "yüzde 20" dijital PDF metninde var).
- **DB değişimi (idempotent, çift kayıt yok):** eski satır `3cba430a-…` (+ cascade: pages/chunks/job/review events) ve `data/documents/<id>/` silindi; `app.cli seed-demo-documents` yalnızca eksik olan ADM-003'ü oluşturdu (`was_created`: 73 × false, 1 × true, aynı `external_ref`), `wait-for-documents` → 74 hazır. Yeni satır `85f9eb7b-…`: `ready`, `approved`, 4 sayfa, 4 chunk. Belge sayısı 76 (74 manifest + 2 elle yüklenmiş test belgesi), öncekiyle aynı. Audit satırlarındaki eski belge id'si (`documents_retrieved`) FK'sız olduğundan kalır.

## 2. ADM-003 sayfa 3 (OCR sonrası `document_pages`, yeni kayıt)
> Alınan Karar — Yönetim kurulu tarafından yapılan değerlendirmeler neticesinde **yüzde 20 oranındaki hisse devri** oy birliğiyle kabul edilmiştir. İşbu DOC-CO-ADM-003 numaralı karar belgesinde belirtilen tüm şartların yerine getirilmesi hususunda genel müdürlük yetkilendirilmiştir. …

Manifest doğrulaması: `page_map["Alınan Karar"] = 3`, prose'da `[[ghi_share_pct]]` yalnızca "Alınan Karar" bölümünde → anahtar olgu hâlâ **3. sayfada**; `make validate-ocr` satırı `DOC-CO-ADM-003 | 3 | ghi_share_pct | yüzde 20 | ✅`.

## 3. (c) `make validate-ocr` — OCR sonrası kalite kapısı
- `scripts/validate_ocr.py` (+ Makefile hedefi `validate-ocr`, `.PHONY`; **`make lint`'in parçası değil** — DB gerektirir): taranmış belgeler (`--all` ile hepsi) için `manifest.key_facts_used` ↔ `document_pages` metni. Biçimden bağımsız: değer ve sayfa metni `scripts.eval_lib.fact_tokens` ile kanonik sayı/tarih token'larına indirgenir (`%20` = `yüzde 20` = `20`; `15 Kasım 2021` = `15.11.2021`; `45.000.000 EUR` = `45,000,000 EUR`; `1,25x` = `1.25`); sayısız metin olguları (`repayment_profile`, `ced_status`, `cod_deferral_reason`…) büyük/küçük harf + boşluk + Türkçe İ katlanarak alt dize. Olgu, prose'da `[[token]]`'ının geçtiği bölümün sayfasında (`page_map`) aranır; token bölümde yoksa (kapak olguları) tüm belgede. Fark varsa belge/sayfa/alan/beklenen + OCR metnindeki sayı/tarih token'ları listelenir; çıkış kodu 1.
- Birim testleri: `backend/tests/test_validate_ocr.py` (sayfa seçimi, biçim bağımsız karşılaştırma, "9020" ≠ "%20" yakalanır, kapak olgusu tüm sayfalara düşer).
- **Bugünkü çıktı:** `make validate-ocr` → **9 taranmış belge, 11 anahtar olgu, 11 eşleşti, 0 FARK**; `make validate-ocr ARGS="--all"` → **70 belge, 61 olgu, 61 eşleşti, 0 FARK**. (Önceki kayıtla koşulsaydı ADM-003 satırı `❌ FARK — OCR metnindeki sayı/tarih tokenları: …, 9020` verirdi; birim testi bu durumu sabitler.)

| Belge | Sayfa | Alan | Beklenen | Durum |
|---|---|---|---|---|
| DOC-ANK-DEV-001 | 3 / 3 / 2 | capacity_mw / licence_date / development_start | 48 MW / 15.06.2020 / 01.03.2018 | ✅ ✅ ✅ |
| DOC-ANK-EPC-002 | 2 | cod_actual / capacity_mw / cod_expected / cod_deferral_reason | October 15, 2023 / 60 MW / June 30, 2023 / COD deferral: grid connection works | ✅ ×4 |
| DOC-CO-ADM-001 | 3 | approved_spv | DEF Enerji Üretim A.Ş. | ✅ |
| DOC-CO-ADM-003 | 3 | ghi_share_pct | yüzde 20 | ✅ |
| DOC-IZM-DEV-001 | 2 / 3 | target_capacity_mw / pre_licence_date | 80 MW / 18.01.2024 | ✅ ✅ |
| (ANK-DEV-004, ANK-EPC-010, CO-ADM-008, IZM-DEV-008) | – | anahtar olgu yok | – | – |

## 4. Testler ve ölçüm
- `make test`: backend **551 passed** (15 deselected live_llm; +4 `test_validate_ocr.py`), şema doğrulaması OK, ocr-worker **18 passed**. `make lint`: ✅ (ruff + mypy strict + worker ruff + prompt dokümanı).
- `make eval EVAL_ARGS="--retrieval-only"`: recall@80 **42/42 (%100)** — ölçülebilir soru 42/76 (questions.json v5 ile 39'dan 42'ye çıkmıştı; hepsi korundu) → `results/retrieval-only_2026-10-07/recall_181239.*`.
- GEN-AMB-005 ("Toplantıda ne karar alındı?", yonetim) ×3, bayrak kapalı: 3 tekrarın **3'ünde "9020" yok**, G1–G3 3/3; 1–2. tekrar DOC-CO-ADM-008 (denetim komitesi) kararını aktardı, 3. tekrar ayrıca ADM-003'ü "**yüzde 20 oranındaki** hisse devri" olarak doğru aktardı → `results/consistency_2026-10-07/consistency_181340.*` (belirsiz soru beklentisi `clarify`; model yine kaynakları sıralayarak cevapladı — Tansu'da bekleyen ambiguous kararı, bu turla ilgisiz).

## 5. Kendi aldığım küçük kararlar
| Karar | Neden |
|---|---|
| Üretim tam yapıldı ama yalnızca ADM-003 dosyaları + manifest girdisi kopyalandı | generator tek belge seçeneği sunmuyor; bayt-aynılık diğer 77 dosya için ancak böyle korunur (WeasyPrint üstverisi her koşuda değişiyor) |
| `ocr_friendly` yalnızca `build_facts` içinde ve yalnızca `percent` türü için | tablo yüzdeleri (`Kullanılabilirlik (%)` sütunu) dijital belgelerde; `en` belgelerde `20%` zaten OCR'da sorunsuz (işaret sonda) |
| `validate_ocr` `scripts/` altında, `app` + `seed_data` okur | eval runner ile aynı yerleşim (ADR-013: backend `seed_data.generator`'ı import etmez; script eder) |
| Metin olgularında Türkçe İ → i katlaması | `casefold("İ")` iki kod noktası üretir, "EDİYOR" ↔ "ediyor" eşleşmezdi |

## 6. Gözlemler / açık noktalar (düzeltme yapılmadı)
- Committed-olmayan `seed_data/documents/manifest.json` (02.10.2026 üretimi) `expiration_date` anahtarını hiç taşımıyordu; yeni üretim DOC-ANK-OPS-009 için `2025-01-09` yazıyor (ADR-026 turunda DB doğrudan güncellenmiş, manifest yenilenmemişti). Bu turda manifest'in diğer girdileri değiştirilmedi; temiz kurulumda `make seed` zaten yeniden üretir. Not düşüldü.
- Taranmış belgelerde yalnızca `tr` yüzdeler risk taşıyordu; tarih/tutar/oran olguları 9 belgede OCR sonrası birebir eşleşiyor.

## 7. Doğruladığım üçüncü taraf davranışları
- WeasyPrint çıktısı bayt düzeyinde deterministik değil (aynı girdi, farklı sha256; sayfa metni ve gömülü JPEG baytları aynı) — PDF üstverisi.
- `app.cli seed-demo-documents` `external_ref` ile idempotent: var olanı "unchanged" bırakır, yalnızca eksik olanı yaratır (`demo_documents_seed._seed_one`).
