# İş Emri 2026-10-11-C — Adım 5 Raporu (karşılaştırma + kriter sonucu)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **iş emrinin tamamı bitti**

Kriter `docs/plans/ADIM_C_HAIKU_KRITERLERI.md`'de sonuçlardan ÖNCE kilitlendi ve
DEĞİŞTİRİLMEDİ. Bu rapor yalnız sonucu bildiriyor — **hiçbir prompt/ayar/eşik
oynatılmadı.**

## 1. Kategori bazlı karşılaştırma (C1 = Gemini taban çizgisi)

| Kategori | C1 | C2 (Haiku/Haiku) | C2 kriteri | C3 (Haiku/Sonnet) | C3 kriteri |
|---|---|---|---|---|---|
| ambiguous | %33,3 | %0,0 | ❌ **gerileme** | %66,7 | ✅ |
| authorization | %100,0 | %100,0 | ✅ | %100,0 | ✅ |
| comparison | %0,0 | %0,0 | ✅ (eşit) | %0,0 | ✅ (eşit) |
| data | %50,0 | %33,3 | ❌ **gerileme** | %33,3 | ❌ **gerileme** |
| discovery | %33,3 | %66,7 | ✅ | %66,7 | ✅ |
| document | %25,0 | %12,5 | ❌ **gerileme** | %12,5 | ❌ **gerileme** |
| hallucination | %100,0 | %100,0 | ✅ | %100,0 | ✅ |
| isolation | %25,0 | %25,0 | ✅ (eşit) | %25,0 | ✅ (eşit) |
| mixed | %66,7 | %66,7 | ✅ (eşit) | %66,7 | ✅ (eşit) |
| temporal | %0,0 | %0,0 | ✅ (eşit) | %0,0 | ✅ (eşit) |
| term_mismatch | %100,0 | %100,0 | ✅ | %100,0 | ✅ |

## 2. "Bilmiyorum" (abstention) doğruluğu

| | C1 | C2 | C3 |
|---|---|---|---|
| Doğru abstain / toplam `expect_no_answer` | 12/14 | 11/14 | 13/14 |
| Oran | %85,7 | **%78,6 ❌ gerileme** | %92,9 ✅ |

## 3. Kritik bulgu sayısı (G1–G3 güvenlik değişmezi ihlali)

| | C1 | C2 | C3 |
|---|---|---|---|
| İhlal sayısı | 0 | 0 ✅ | 0 ✅ |

(C1'de 1 soru `skipped` — HTTP 500 hatası nedeniyle güvenlik kontrolü hiç çalışmadı, bu bir
İHLAL değil, değerlendirilememe. 0 ihlal sayısına dahil edilmedi.)

## 4. KRİTER SONUCU (kilitli kritere göre, mekanik)

**C2 (router=Haiku + answer=Haiku): ❌ BAŞARISIZ.**
4 metrik C1'den daha kötü: `ambiguous` (%33,3→%0,0), `data` (%50,0→%33,3), `document`
(%25,0→%12,5), abstention doğruluğu (%85,7→%78,6). Kriter "tek bir metrik dahi" dediği
için tek bu 4'ü bile yeterli — BAŞARISIZ.

**C3 (router=Haiku + answer=Sonnet): ❌ BAŞARISIZ.**
2 metrik C1'den daha kötü: `data` (%50,0→%33,3), `document` (%25,0→%12,5). Diğer her
metrik C1'e eşit veya daha iyi (abstention %85,7→%92,9 daha iyi; `ambiguous` %33,3→%66,7
daha iyi) — ama kriterin "tolerans yok" şartı gereği bu 2 gerileme tek başına yeterli:
BAŞARISIZ.

**Hiçbir yapılandırma kriteri karşılamadı — C2 ve C3 ikisi de reddedildi.**

## 5. Teşhis notu (kritere etkisi YOK, bilgi amaçlı — oynama yapılmadı)

`data` ve `document` kategorilerindeki gerileme **C2 VE C3'te BİREBİR AYNI** (%33,3 ve
%12,5) — bu, Claude'un cevap kalitesiyle ilgili bir fark DEĞİL (iki farklı answer modeli
—Haiku ve Sonnet— aynı sonucu veriyor); muhtemelen **router** (her ikisinde de Haiku) veya
**retrieval** katmanındaki bir davranış farkı. Bu iki kategorideki C1 başarısızlıklarının
çoğu da (Adım 4 §2) canlı DB'nin güncel olmamasından kaynaklanıyordu — aynı kök neden iki
Claude yapılandırmasını da aynı şekilde vurmuş olabilir. **Bu bir hipotezdir, doğrulanmadı
— kapsam dışı (prompt/ayar değişikliği yapılmadı, iş emrinin kendi "sonuca göre oynama"
yasağı gereği).**

## 6. Sonuç ve öneri (yorum, karar DEĞİL)

İş emrinin kriteri açık ve net biçimde karşılanmadı: **backend'i Claude'a taşımak bu
ölçümle desteklenmiyor.** `LLM_PROVIDER=anthropic` kod olarak çalışır durumda bırakıldı
(Adım 3, canlıda KAPALI/varsayılan Gemini) — ileride (a) canlı DB güncellenip ölçüm
tekrarlanırsa veya (b) `data`/`document` kategorilerindeki ortak gerilemenin kök nedeni
bulunursa yeniden değerlendirilebilir. Bu iş emri bu kararı ALMIYOR, yalnız ölçüyor.

## 7. Maliyet (toplam, iş emri 2026-10-11-C)

Adım 1 (~$0,0001) + Adım 3 smoke test (~2 çağrı, ~$0,01) + Adım 4 (C1 $0 + C2 $0,1522 +
C3 $2,9304) = **~$3,09 / $4,0 DUR eşiği** — aşılmadı.

## 8. Commit'ler (bu iş emrinde, sırayla)

`96ffd1f` (Adım1) → `ab4e893` (Adım2) → `55b3e00`+`73643f5`+`0608469` (Adım3) →
`2204049` (Adım4 kriter) → `e976f3d` (Adım4 koşular) → bu rapor (Adım5).

## 9. Final durum tablosu

| Adım | Durum |
|---|---|
| 1 (Haiku rate-limit) | ✅ |
| 2 (Gemini kullanım taraması) | ✅ |
| 3 (LLM_PROVIDER=anthropic + testler) | ✅ lint+test 0 hata |
| 4 (kriter + C1/C2/C3 koşuları) | ✅ |
| 5 (karşılaştırma) | ✅ **C2 ❌, C3 ❌ — ikisi de kriteri karşılamadı** |
