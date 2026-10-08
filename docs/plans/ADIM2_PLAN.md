# Adım 2 Planı — B tutukluğu için kod düzeltmeleri (Tansu Ürün 1 §B; B ölçümü bulguları)

**Tarih:** 08.10.2026 · **Durum:** plan, Naci onayı bekliyor; **uygulama yok** · **Dayanak:** `docs/reports/B_OLCUM_REPORT.md` §3.3–3.4 (resmi: bayrak açık 8/13, sabit cümle tek başına 0, G1–G3 26/26), `docs/plans/URUN1_NOT_PLAN.md` §3 Adım 2 · **Kapsam dışı:** prompt değişikliği (Ç-1 A: cevap eşiği aynı), çok turlu hafıza (Ç-2 A, istemci), terim tanımı (Ç-3 Tansu'da), V3 belirsizlik tespiti (birleşmedi), yetki modeli (Tansu #15 cevabı bekler) · **Held-out:** `questions.json` `held_out` HO-DSC-01…06 — Adım 2 bitene kadar **koşulmaz, bakılmaz**; sonra bir kez ölçülür.

## 1. Değişiklikler → hangi sorunun nedenini kapatıyor

| # | Değişiklik (dosya) | Ne yapar | Kapattığı neden | Etkilenen ölçüm soruları | Büyüklük |
|---|---|---|---|---|---|
| D1 | **Workbook'lar metadata adayı** — `assist.available_from_metadata` (ve `build_zero_chunk_assist` / `build_insufficient_assist`): aday küme `allowed` içindeki **tüm** belgeler (xlsx/xlsm/csv dahil); bugün yalnızca `search_metadata` → zaten tüm `documents` tablosunda arıyor, ama parça yoksa `build_zero_chunk_assist` metadata'yı yalnızca terim bazlı çağırıyor | "X var mı / yüklü mü" sorusunda Excel belgeleri "elimde şunlar var"a girer; retrieval (chunk) değişmez (SPEC_04: workbook RAG belgesi değil) | DSC-001/006 (yetkili kullanıcıda), DSC-008 (yetkili kullanıcıda), DSC-011 belge yarısı | S |
| D2 | **Kavram sözlüğü başlık aramasında** — `search_glossary.expand_terms` (ve yeni `CONCEPT_GLOSSARY`: "finansal model" → financial model, cash flow, debt schedule, DSCR, budget; "ödeme planı" → repayment schedule, debt, instalment; "bütçe" → budget; "sözleşme" → agreement, contract; "lisans" → licence, önlisans) `document_repo.search_metadata`'ya uygulanır: başlık/tür ILIKE için sorgu terimi + eş anlamlılar (çok kelimeli anahtar) | İngilizce başlıklı belgeler ("Financial Model 2026", "Budget vs Actual 2026") Türkçe soruyla metadata'da bulunur; `unmatched_terms` "finansal/modeli"yi eşleşmeyen saymaz | DSC-001/006/008 (`term_mismatch` → `clarify` + liste), DSC-002/005 zaten ✓ | S–M |
| D3 | **`GENERIC_TERMS` genişletme** (`assist.py`): fiil/soru sözcükleri "bitiyor, biter, demek, biliyor, musun, yüklü, dosyası, nerede, hangisi, neler, var, mı" — yalnızca genel Türkçe kelimeler, gerekçeli (R1 kuralı) | Yanlış `term_mismatch` türü ve gülünç soru metni ("«demek», «biliyor», «musun» bulamadım") kalkar → `clarify` + liste | DSC-003/013 (tür), DSC-006/008 (metin) | S |
| D4 | **Kısaltma istisnası metadata eşleşmesinde** — `available_from_metadata` için `MIN_SPECIFIC_TERM_CHARS=4` yerine `_can_be_specific` mantığı (3–5 harf **büyük harfli** kısaltma geçer: ÇED, EPC, COD, DSCR) | "ÇED raporu nerede?" → Ankara ÇED Olumlu Kararı + ÇED Süreci Durum Yazısı listelenir | DSC-007 | S |
| D5 | **Varlık sorusu → liste zorunlu** — model cevapsızken `assist.available` boşsa ve soru varlık kalıbıysa ("var mı", "yüklü mü", "nerede", "hangi dosyada", "neler"), metadata araması **soru terimlerinin tamamıyla** (kavram sözlüğü dahil) bir kez daha denenir; yine boşsa `clarify` şablonu + "yetkiniz dahilinde bu konuda belge göremiyorum" cümlesi **yalnızca** Tansu #15 B cevabında (yoksa bugünkü şablon) | Sabit cümle tek başına 0'ı garantiye alır; yetki durumunda P-2 korunur (ad dönmez) | DSC-001/006/008 (yetkisiz durum), DSC-003 | S |
| D6 | **Eval:** `discovery_check` için `available` eşleşmesinde belge **türü** de kabul (bugün başlık/tür `_source_satisfied` ile zaten); `results.json`'a `discovery_check` yazımı ✓ (yapıldı) | ölçüm izlenebilirliği | — | S (yapıldı) |

Yapılmayacaklar (bu adımda): prompt kural 2/11 metni; `MIN_SPECIFIC_TERM_CHARS` değeri (yalnızca kısaltma istisnası); V3; workbook içeriğinin belge hattına girmesi (SPEC_04).

## 2. Ölçüm
- Önce: `make test` + `make lint`; LLM'siz kuru koşu — 13 resmi discovery sorusu için `available` tahminini metadata/glossary yoluyla hesapla (0 çağrı), beklenen: 001/006/008 yetkili kullanıcıda listede, 007'de iki ÇED belgesi, 003/013 `clarify`.
- Sonra bayrak açık: 13 resmi soru ×1 (13 çağrı) → **resmi ikinci ölçüm**, hedef ≥ 11/13, sabit cümle tek başına 0, G1–G3 13/13; + R1'in 14 %100-kategorisi ×1 (14 çağrı, G1–G3 regresyonu ve yeni cevapsızlık 0); toplam ≤ 27 çağrı. Tek G1–G3 ihlalinde dur.
- En son held-out HO-DSC-01…06 ×1 (6 çağrı), **ayar sonrası bir kez**; sonuç raporda "held-out" satırı olarak (eşik yorumuna girmez).
- Bayrak ölçüm sonrası kapalı.

## 3. Bitiş kriteri
Resmi 13 soruda ≥ 11/13 **ve** sabit cümle tek başına 0 **ve** G1–G3 %100 **ve** R1 14 sorusunda cevaplanma/G1–G3 gerilemesi 0. Held-out sonucu ne olursa olsun raporlanır, eşik değiştirilmez.

## SORU
1. D5'teki "yetkiniz dahilinde bu konuda belge göremiyorum" cümlesi Tansu #15 cevabına bağlı — cevap gelmeden D1–D4 + D6 ile başlanabilir mi?
2. Kavram sözlüğü kodda (B, bugünkü) mı, admin tablosunda (A, İ-7) mı — Adım 2 kodda başlar, taşıma ayrı iş?
