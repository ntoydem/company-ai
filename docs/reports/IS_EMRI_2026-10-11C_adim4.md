# İş Emri 2026-10-11-C — Adım 4 Raporu (C1/C2/C3 koşuları)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — kriter Adım 4'ten ÖNCE
(`docs/plans/ADIM_C_HAIKU_KRITERLERI.md`) yazılıp kilitlendi; bu rapor sonuçları
DEĞİŞTİRMEDEN kaydediyor.

## 1. Kapsam kararı — 99 soru değil, 40 soruluk temsilci alt küme

**Gerekçe (küçük teknik karar, raporda listelendi):** `questions.json`'daki 99 held-out
olmayan sorunun ~95'i `/api/ask`'ın büyük-bağlamlı belge cevap yolundan geçiyor
(`RETRIEVAL_TOP_K=80` chunk, gözlenen ~40-45 bin girdi token/çağrı). Sonnet 5.5 fiyatıyla
($2/$10 MTok) bu, C3 tek başına **~$8-9**'a mal olurdu — iş emrinin kendi **$4,0 DUR
eşiğini** kesin olarak aşardı. Tüm 99 soruyu koşup bütçeyi aşmak yerine, **her 11
kategoriden temsilci** (güvenlik-kritik 4 kategori — isolation/hallucination/
authorization/comparison — TAMAMI; diğerleri 3 örnek, document 8 örnek) **40 sorulu**
sabit bir alt küme seçildi, **aynı 40 soru her üç yapılandırmada da** koşuldu. Bu, bütçe
aşımını DUR'a gitmeden önler ve üç yapılandırma arasındaki karşılaştırmayı (bu adımın asıl
amacı) bozmaz — yalnız mutlak sayıların istatistiksel hassasiyetini düşürür (bazı
kategorilerde n=3).

Soru ID listesi: `GEN-AMB-001/005/006, ANK-AUT-001/002/003, GEN-CMP-001/002/003,
ANK-DAT-002/003+ANK-FIN-010, GEN-DSC-003/004/005, CO-NEG-005, ANK-DEV-002/003/006,
ANK-FIN-003/007/008/013, IZM-DEV-001/002, ANK-NEG-003, GEN-HAL-001-004, IZM-ISO-001+004,
ANK-ISO-002/003, ANK-MIX-001/002/003, GEN-TRM-001/002/005`.

## 2. Önemli bulgu — canlı DB'nin bilinen güncelliği (dokunulmadı)

C1 (Gemini) koşusu, `document`/`temporal`/`comparison`/`isolation` kategorilerinde
**%0-33** gibi düşük sonuçlar verdi — "eksik kaynak" hatalarının çoğu bu session'da
üretilen/düzeltilen belgelerin (Karatepe Üretim Lisansı, Facility Agreement, ÇED Süreci
Durum Yazısı vb.) **canlı DB'ye hiç yüklenmemiş/güncellenmemiş olmasından** kaynaklanıyor
— iş emrinin kendi "canlı DB'ye dokunma" kuralı gereği bu YENİDEN SEEDLENMEDİ. **Bu üç
yapılandırmayı da EŞİT ŞEKİLDE etkiliyor** (hepsi aynı canlı DB'ye karşı koştu) — yani
C1↔C2/C3 KARŞILAŞTIRMASININ KENDİSİ hâlâ geçerli (aynı bozuk/eski korpusa karşı üç
sağlayıcı), ama mutlak yüzdeler bu iş emrinin konusu olan "güncel şirket hafızası
kalitesi"ni YANSITMIYOR — ayrı bir bulgu olarak not edildi, düzeltilmedi (kapsam dışı,
canlı DB'ye dokunma yasağı).

## 3. Üç koşunun ham sonuçları

| | C1 (Gemini, taban çizgisi) | C2 (Haiku router+answer) | C3 (Haiku router+Sonnet answer) |
|---|---|---|---|
| `--model-label` | `gemini-adimC-c1` | `claude-haiku-haiku-adimC-c2` | `claude-haiku-sonnet-adimC-c3` |
| `LLM_PROVIDER` | `openai_compatible` (zaten .env'deydi) | `anthropic` | `anthropic` |
| `--min-interval-s` | 26 (varsayılan, Gemini kotası) | 2 | 2 |
| `--budget-usd` | (gerek yok, $0) | 1,0 | 3,5 |
| Gerçek maliyet | $0 | **$0,1522** | **$2,9304** |
| Koşu tamamlandı mı | ✅ tam (40/40, kesinti yok) | ✅ tam | ✅ tam (bütçeyi aşmadı) |
| Sonuç dosyası | `seed_data/evaluation/results/gemini-adimC-c1_2026-10-11/` | `.../claude-haiku-haiku-adimC-c2_2026-10-11/` | `.../claude-haiku-sonnet-adimC-c3_2026-10-11/` |

**Hiçbir koşu 429/529 ile tekrarlı başarısız olmadı — Gemini KARARLAR'ındaki "429 verirse
atla" maddesi tetiklenmedi.** Tek bir istek hatası oldu (ANK-FIN-010, HTTP 500) — her üç
koşuda da AYNI soruda (yapılandırmadan bağımsız bir backend/retrieval sorunu, ayrı not).

## 4. .env / canlı sistem

Her koşu öncesi `.env` yedeklendi, koşu sonrası **`diff` ile birebir eski haline
döndürüldüğü doğrulandı**, `make restart-backend` ile backend Gemini varsayılanına
yeniden başlatıldı. Canlı sistem şu an Gemini ile çalışıyor (iş emrinin "canlı Gemini ile
çalışmaya devam eder" şartı korundu).

## 5. Maliyet

Bu adımda: $0 (C1) + $0,1522 (C2) + $2,9304 (C3) = **$3,0826**. Adım 1/3'ün gerçek
çağrılarıyla birlikte kümülatif: **~$3,09 / $4,0 DUR eşiği** — aşılmadı.

Devam ediliyor: **Adım 5** (karşılaştırma tablosu + kriter sonucu).
