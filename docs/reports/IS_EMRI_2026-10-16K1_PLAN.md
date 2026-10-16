# İş Emri 2026-10-16K1 — Kızılova önlisans tarihi tek değere: PLAN

**Tarih:** 16.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `b9bfb54`) · **Ürün 1** · **Dayanak:** Tansu 16.10 WA madde 4 + v14 önerisi "Veri düzeltmesiyle birlikte kontrol edilecekler" · **Durum:** yalnız plan; hiçbir dosya, veri ya da canlı satır değişmedi (canlı DB'de yalnız `SELECT` çalıştırıldı).

## 1. Çelişki tam olarak nerede

| Yer | Bugün | Kaynak mı, türev mi |
|---|---|---|
| `seed_data/master/izmir_res.yaml:27` `timeline.pre_licence.date` | **2025-01-15** (ÖL/13085-3) | kanonik, değişmez |
| `izmir_res.yaml:59` `permits_completed` "Önlisans" · `:78` üretim lisansı notu · `:29` expiry 2027-01-15 | 15.01.2025 ile uyumlu | değişmez |
| **`izmir_res.yaml:143-144`** `DOC-IZM-DEV-001.document_date` / `effective_date` | **2024-01-18** | **değişecek tek kaynak satırlar** |
| `seed_data/documents/manifest.json:4395-4441` (`file`, `digital_file`, `document_date`, `effective_date`, `facts_used`) | 2024-01-18 / "18.01.2024" | türev: `generate_documents.py` ledger'dan yazar; **git'te izlenmez** (`.gitignore:22`) |
| Belge PDF'i `2024-01-18_IZM_RES_Önlisans_EXECUTED_active{,.digital}.pdf` | — | türev, gitignore'lu; dosya adı `document_date`'ten gelir (`generate_documents.py:186-190`) |
| Belge metni: `prose/DOC-IZM-DEV-001.yaml` (**`hand_edited` YOK**, token'lı) | s.1 kapak "Belge/Yürürlük Tarihi 18.01.2024"; s.2 mektup başlığı tarihi 18.01.2024; s.3 "**[[effective_date]]** itibarıyla yürürlüğe giren hükümler" → 18.01.2024 ve "**[[pre_licence_date]]** (15.01.2025) tarihinde başlatılan işlemler silsilesi, **[[document_date]]** (18.01.2024) tarihli resmi evrak ile teyit edilmiştir" | prose'da rakam yok; tarihler token → ledger düzelince metin kendiliğinden düzelir, **LLM çağrısı gerekmez** |
| Canlı DB `documents` (id `4cae7f3e-…`) | `document_date`=`effective_date`=2024-01-18 | seed ile 12.10'da yüklendi |
| Canlı `document_chunks` | 4 parça; **3'ü** (s.1-3) 18.01.2024/"18.01," içeriyor; tüm canlı DB'de bu tarihi taşıyan başka parça **yok** | OCR türevi |

Kod/test/eval'de `2024-01-18`/`18.01.2024` yok (`backend/`, `scripts/`, `ocr-worker/`, `questions.json`, `smoke.json` tarandı). Diğer geçişler yalnız geçmiş rapor/sonuç dosyaları (`docs/reports/*`, `results/*`, `logs/`) — tarihsel kayıt, **dokunulmaz**.

## 2. Düzeltme yolu (repo)

1. `izmir_res.yaml:143-144` → `2025-01-15` (tag `USER_FACT` kalır; satır üstüne "K1, Tansu 16.10 madde 4" yorumu).
2. `generate_documents` (`scripts/seed_demo.sh:15` ile aynı komut) → 106 belge + manifest yeniden yazılır; DEV-001 dosya adı `2025-01-15_…` olur. Eski iki `2024-01-18_…pdf` silinir (generator temizlemiyor; gitignore'lu).
3. Prose'a dokunulmaz (bkz. SORU 2). `generate_prose` çalışmaz.
4. Beklentiler: `validate_ledger` C8 (`document_date ≤ demo_today`, `effective ≥ document_date`) geçer; `validate_documents` (facts metinde mi) geçer; `validate_excel` etkilenmez (workbook'lar belge tarihini kullanmaz); `make test` — bu tarihe bağlı test yok, değişmez beklenir.
5. Git'e giren değişiklik: **yalnız ledger'ın 2 satırı** (+ rapor). Commit'ten sonra `cetvel-v2.1-v14` etiketi Tansu sırasına göre (§6 SORU 4) bu commit'e/sonrasına konur.

## 3. Canlıya yansıtma

`ensure_demo_documents` var olan `external_ref`'e **hiç dokunmaz**; `refresh_demo_document_metadata` yalnız yetki alanlarını eşitler; OCR worker var olan sayfa/parçaları silmez. Yani içerik güncelleme yolu bugün yok. İki seçenek:

**A (önerilen, kod yok):** yalnız bu belgeyi sil + yeniden seed.
1. Yedek: `pg_dump -Fc` → `data/backups/live_pre_K1_<TS>.dump` + `tar` `data/documents/4cae7f3e-…/` (3 dosya; 3,7 GB'lık tam tar gerekmez). `pg_restore --list` ile oku.
2. `DELETE FROM documents WHERE external_ref='DOC-IZM-DEV-001'` (CASCADE: 4 sayfa, 4 parça, iş satırları, 1 metadata önerisi; review event 0). Klasörü yedeğe taşı.
3. `make seed-demo-documents` → yalnız eksik ref oluşur: **yeni UUID**, aynı başlık/departman/proje/klasör (Enerji kökü)/`approved`/`parties`; `_relink_chain` DOC-IZM-LEG-004'ün `related` bağını yeni UUID'ye çevirir; OCR ≈ 1-2 dk; `wait-for-documents`.
4. Kesinti: container durmaz/yeniden başlamaz; yalnız 2→3 arası (~2 dk) bu belge aramada yok. Sessiz saatte.

**B (UUID korunur, kod gerekir):** yeni CLI (`reingest-demo-document`: dosyayı değiştir, sayfa/parça sil, tarihleri manifest'ten yaz, iş kuyruğa koy) + test. Daha büyük kapsam; önerilmez.

**Audit/kaynak kartı etkisi:** `audit_log` belgeye FK'siz; 52 satır eski UUID'yi `documents_retrieved`/`chunks_retrieved`'da, kaynak kartı anlık görüntüsünü (`sources[].document_date: "2024-01-18"`) `sources` jsonb'de tutuyor. A'da bu satırlar **değişmez** (geçmişte ne gösterildiyse o — doğru davranış), eski UUID artık açılmaz. Emsal: 12.10 I emri tam reset'i tüm UUID'leri değiştirdi; audit'te zaten öksüz UUID var (`08e0a053-…`). Yeni cevaplarda kart 15.01.2025 gösterir.

**Geri alma:** `OPERATIONS.md §2` — `stop backend ocr-worker` → `pg_restore --clean --if-exists live_pre_K1_<TS>.dump` → klasörü geri koy → başlat → §3 doğrulama listesi. K1 sonrası audit satırları gider (sayısı rapora). Repo tarafı: ledger commit'i `git revert` + `generate_documents`.

**Ç-15/6:** Bu bir **üretim ortamı yazma işlemidir** (DELETE + yeni satır + dosya silme). Dump + klasör tarı alınırsa **geri alınabilir**, fakat geri alma da yıkıcıdır (dump sonrası audit satırları silinir) ve eski belge UUID'si yalnız dump'tan restore ile geri gelir. Bu yüzden Ç-15/6 kapsamında **ayrı açık onay** ister ("ONAY K1 CANLI"); repo commit'i ile canlı adım ayrı onaylanabilir.

## 4. Etkilenen sorular (cetvel/soru seti değişmez)

M1 v14 (`results/v14/m1/results.json`) — altısı da **geçti**, ama beşi iki tarih veriyor:

| Soru | Bugün cevaptaki önlisans tarihleri | Düzeltme sonrası beklenen |
|---|---|---|
| GEN-CMP-001 | 15.06.2020 + **18.01.2024** (Önlisans Belgesi, K33/K65) + 15.01.2025 (ÇED yazısı) | Kızılova için tek tarih 15.01.2025, iki belgeden |
| GEN-CMP-002 | sabit cümle ✅ + aynı ikili | sabit cümle + 15.06.2020 / 15.01.2025 ayrı ayrı |
| IZM-DEV-001 | "K1'de 15.01.2025, K9'da 18.01.2024" (+20.01.2025 arazi, 12.09.2026) | aşama "ÇED devam ediyor"; tarih geçerse yalnız 15.01.2025 |
| IZM-DEV-007 | "15.01.2025 … belgenin tarihi 18.01.2024 … hangisi doğru karar verilmemiştir" | önlisans 15.01.2025, çelişki uyarısı yok |
| IZM-DEV-011 | yalnız 15.01.2025 (LEG-004'ten) | değişmez |
| ANK-ISO-002 | "hem 15.01.2025 hem 18.01.2024" | Kızılova: yalnız önlisans, 15.01.2025 |

Puan etkisi: 6/6 zaten geçiyor → skor değişimi beklenmez; kazanç doğruluk/okunabilirlik (kontrolör KY listesi `M1_KY_LISTESI.md` #2, #8 kapanır).

## 5. Doğrulama planı

**LLM'siz (önce/sonra):** (a) `validate_ledger`, `validate_documents`, `validate_excel` 0 hata; (b) manifest DEV-001 `document_date`/`effective_date`/`facts_used` = 2025-01-15/15.01.2025, dosya adı yeni; (c) `pdftotext`/PyMuPDF ile digital PDF'te `18.01.2024` sayısı 0; (d) `make test` yeşil (sayı rapora); (e) canlı SQL: `documents` 113, DEV-001 tarihleri 2025-01-15, `ingestion_status=ready`, parça sayısı 4 (±), tüm `document_chunks`/`document_pages`'te `18.01.2024`/`18.01,` = **0** (bugün 3/2), LEG-004 `related_document_ids` = yeni UUID; (f) `make validate-ocr ARGS=--all`; (g) `smoke_live.py` 9/9; (h) `/api/search?q=Önlisans` (enerji) kartı 15.01.2025.
**LLM'li (yalnız onaylanırsa):** `run_eval.py --ids` ile yalnız 6 soru, canlı yapılandırma (Haiku + ANSWER_THINKING), ×1 (istenirse ×3). M1'de bu 6 soru ≈ 184 k giriş / 8,7 k çıkış token → **≈ 0,05 USD/koşu**, ×3 ≈ 0,15 USD (cost.json eksik saydığı için üst sınır 0,25 USD). Ölçüt: Kızılova için 18.01.2024 geçmemesi + 6/6 geçme. 99 soruluk koşu bu emirde yok.

## 6. Riskler ve açık sorular

- **Risk:** prose cümlesi düzeltme sonrası "15.01.2025 tarihinde başlatılan işlemler silsilesi, 15.01.2025 tarihli resmi evrak ile teyit edilmiştir" olur — tutarlı ama totolojik.
- **Risk:** DELETE→OCR arası ~2 dk bu belge yok; yük saatinde soruya eksik cevap.
- **Risk (kapsam dışı bulgu):** **DOC-IZM-LEG-004** "Önlisans Süre Uzatımı Hukuki Değerlendirmesi" `document_date` **01.11.2023**, ama içinde önlisans 15.01.2025 anılıyor — verilmemiş önlisansın süre uzatımı değerlendirmesi (bugün de vardı; K1 ile görünürleşir). Düzeltilecekse o da kapıdan önce olmalı.
- **Risk:** feat dalı canlıya bind-mount'lu; generator/seed bu daldan koşar (bellek notu) — dal değişmeden uygulanmalı.

**SORU 1 (Naci):** Canlı yöntem A (sil + yeniden seed, yeni UUID, kod yok) mı, B (UUID korunur, yeni CLI + test) mı? Önerim **A**.
**SORU 2 (Tansu):** Prose'daki totolojik cümle olduğu gibi kalsın mı (önerim: **kalsın**, metin token'dan gelir, LLM yok), yoksa elle düzeltilip `hand_edited` notu mu eklensin?
**SORU 3 (Tansu):** LEG-004'ün 01.11.2023 tarihi bu emirde mi düzeltilsin, ayrı emir mi, olduğu gibi mi kalsın? Önerim: **ayrı küçük emir, kapıdan önce**; K1'e karıştırılmasın.
**SORU 4 (Naci/Tansu):** Sıra Tansu notundaki gibi mi: K1 commit + canlı → `cetvel-v2.1-v14` etiketi K1 sonrası commit'e? (Etiket henüz yok.) LLM'li 6-soru koşusu ×1 mi ×3 mü, yoksa hiç mi?

## [ANAYASA KONTROLÜ]
```
Ürün etiketi      : Ürün 1
T-9 (önce plan)   : Yalnız plan; onaysız uygulama yok. Bu commit yalnız bu dosyayı ekler.
Ç-15/6            : Canlı adım (§3) geri alınamaz-üretim-işlemi sınıfında ele alındı: yedek + geri alma
                    yolu var, ama ayrı açık onay ("ONAY K1 CANLI") olmadan yapılmaz. Bu oturumda canlıya
                    yazma YOK — yalnız SELECT; container durdurulmadı; .env okunmadı/değişmedi.
Ç-16              : Kod/test/prompt/şema/soru seti/cetvel değişmedi. Kapsam dışı bulgu (LEG-004 tarihi)
                    yalnız SORU 3 olarak yazıldı.
Gizli bilgi / yeni bağımlılık : Yok.
Kendi başına verilen kararlar : plan yeri docs/reports/ (emirdeki yol); önerilen yöntem A; maliyet M1
                    token sayılarından tahmin.
```
