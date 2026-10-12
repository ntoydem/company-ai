# İş Emri 2026-10-12-E — Adım 2 Raporu (kategori tablosu + C3'ün her sorusu)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — kod/belge değiştirilmedi, LLM çağrısı yok.

## 1. Kategori bazlı tablo (D emri, 99 soru, ayrı ortam)

| Kategori | C1 (Gemini) | C2 (Haiku/Haiku) | C3 (Haiku/Sonnet) |
|---|---|---|---|
| ambiguous | 1/6 | 1/6 | 2/6 |
| authorization | 3/3 | 3/3 | 3/3 |
| comparison | 0/3 | 2/3 | 3/3 |
| data | 1/4 (3 hata) | 1/4 | 1/4 |
| discovery | 2/18 (4 hata) | 4/18 | 4/18 |
| document | 30/39 (1 hata) | 28/39 | 29/39 |
| hallucination | 4/4 | 4/4 | 4/4 |
| isolation | 2/4 | 3/4 | 2/4 |
| mixed | 1/3 (1 hata) | 2/3 (1 hata) | 2/3 (1 hata) |
| temporal | 5/11 | 8/11 | 8/11 |
| term_mismatch | 4/4 | 4/4 | 4/4 |
| **TOPLAM DOĞRU** | **53/99** | **60/99** | **62/99** |

## 2. C3'ün başarısız olduğu 37 soru — tek satır, kök neden sınıfı

**Önemli ayrım:** 37 sorudan **4'ü** C1'de DOĞRU, C3'te YANLIŞ (gerçek C3-özgü gerileme —
bkz. §3). **33'ü** C1'de de ZATEN yanlış (sağlayıcıdan bağımsız, önceden var olan zayıflık).

| Soru | Kategori | Sınıf | Not |
|---|---|---|---|
| ANK-FIN-002 | document | (a)/(d) değer metni | C1'de de aynı hata |
| ANK-FIN-003 | document | (a)/(d) değer metni | C1'de de aynı hata |
| ANK-FIN-004 | document | (a)/(d) değer metni | C1'de de aynı hata |
| ANK-NEG-002 | document | (a)/(d) değer metni | C1'de de aynı hata |
| ANK-FIN-006 | temporal | (a)/(b) kaynak eksik | C1'de de aynı hata |
| ANK-FIN-010 | data | (a)/(b) kaynak eksik | C1'de HATA (HTTP 500), bkz. Adım 3 |
| ANK-FIN-012 | temporal | (a)/(b) kaynak eksik | C1'de de aynı hata |
| ANK-DAT-001 | data | (a)/(b) kaynak eksik | C1'de de aynı hata |
| ANK-DAT-003 | data | (a)/(b) kaynak eksik | C1'de HATA (HTTP 500) |
| ANK-EPC-005 | document | (a)/(b) kaynak eksik | C1'de de aynı hata |
| ANK-COR-001 | document | (a)/(b) kaynak eksik | C1'de de aynı hata |
| IZM-DEV-011 | temporal | (a)/(b) kaynak eksik | C1'de de aynı hata |
| GEN-AMB-002 | ambiguous | (c) abstain gerekirken cevapladı | C1'de de aynı hata |
| GEN-AMB-003 | ambiguous | (c) abstain gerekirken cevapladı | C1'de de aynı hata |
| GEN-AMB-004 | ambiguous | (c) abstain gerekirken cevapladı | C1'de de aynı hata |
| GEN-AMB-006 | ambiguous | (c) abstain gerekirken cevapladı | C1'de de aynı hata |
| IZM-ISO-004 | isolation | (c) abstain gerekirken cevapladı | C1'de de aynı hata |
| ANK-ISO-002 | isolation | **(c*) çapraz-proje referansı** | C1'de de VAR (C2'de yok) — bkz. §4 |
| ANK-MIX-001 | mixed | **backend hatası** | C1/C2/C3 ÜÇÜNDE DE — bkz. Adım 3 |
| GEN-DSC-001 | discovery | (a) discovery eşleşmesi | C1'de HATA (HTTP 500) |
| GEN-DSC-002 | discovery | (a) discovery eşleşmesi + (c*) | ÜÇÜNDE DE forbidden-hit var |
| GEN-DSC-006 | discovery | (a) discovery eşleşmesi | C1'de de aynı hata |
| GEN-DSC-007 | discovery | (a) discovery eşleşmesi | C1'de de aynı hata (G2 güvenlik ihlali de var, bkz. İş Emri D Adım4) |
| GEN-DSC-008 | discovery | (a) discovery eşleşmesi | C1'de de aynı hata |
| GEN-DSC-009 | discovery | (a) discovery eşleşmesi + (c*) | C3'e özgü forbidden-hit eklendi |
| GEN-DSC-010 | discovery | (a) discovery eşleşmesi + (c*) | C2 bunu GEÇTİ, C1/C3 kaldı |
| GEN-DSC-011 | discovery | (a) discovery eşleşmesi | C1'de HATA (HTTP 500) |
| GEN-DSC-013 | discovery | (a) discovery eşleşmesi | C1'de de aynı hata |
| GEN-DSC-001-M | discovery | (a) discovery eşleşmesi | C1'de HATA (HTTP 500) |
| GEN-DSC-006-M | discovery | (a) discovery eşleşmesi | C1'de HATA (HTTP 500) |
| GEN-DSC-008-M | discovery | (a) discovery eşleşmesi | C1'de de aynı hata |
| GEN-DSC-007-K | discovery | (a) discovery eşleşmesi | C1'de de aynı hata |
| GEN-DSC-011-K | discovery | (a) discovery eşleşmesi | C1'de HATA (HTTP 500) |
| **IZM-DEV-005** | document | **(c) C3-ÖZGÜ** | bkz. Adım 1 — belge bağlamda, model (Haiku+Sonnet) çekildi |
| **IZM-DEV-006** | document | **(a) C3-ÖZGÜ** | bkz. Adım 1 — belge inşaat konusuna hiç değinmiyor |
| **ANK-OPS-003** | document | **(d) C3-ÖZGÜ** | doğru değer (17.218 MWh), YANLIŞ kaynak atfı ("Monthly Production 2026" yerine "Aylık Üretim Raporu — Aralık 2023") |
| **ANK-NEG-004** | document | **(c\*) C3-ÖZGÜ** | bkz. §4 — Sonnet gönüllü olarak Kızılova RES'i anıp izolasyon ihlali yaptı; C1/C2 temiz |

## 3. Gerçek C3-özgü gerilemeler (4) — özet

Zaten Adım 1'de (IZM-DEV-005/006) ve bu raporun §4'ünde (ANK-NEG-004) ayrıntılı işlendi.
**ANK-OPS-003** yeni: C3 doğru DEĞERİ (17.218 MWh) verdi ama gerekli kaynak başlığı yerine
(`Aylık Üretim Raporu — Aralık 2023`) aynı rakamı içeren BAŞKA bir belgeyi
(`Monthly Production 2026`, Excel workbook) andı — içerik hatası değil, atıf/kaynak-seçimi
farkı (sınıf **d**, kriterin tek-kaynak zorunluluğu burada katı davranıyor; rakam gerçekten
her iki belgede de mevcut).

## 4. Yeni bulgu — Claude'un gönüllü çapraz-proje referansı (izolasyon riski)

**ANK-NEG-004** (Karatepe üretim lisansı sorusu): C3 (Sonnet) doğru cevabı verdikten SONRA,
sorulmadığı halde ekledi: *"Kızılova RES için üretim lisansının alındığına dair bir tarih
kaynaklarda yoktur..."* — bu, `forbidden_sources_hit: ["Kızılova RES"]` tetikledi
(izolasyon kontrolü). **C1 ve C2 bunu yapmadı** (yalnız Karatepe'yle sınırlı cevap verdi).

Bu desen TEK ÖRNEK değil — aynı "gönüllü çapraz-proje referansı" **4 soruda daha** görüldü
(`ANK-ISO-002`, `GEN-DSC-002/009/010`) ama bunlarda C1 (Gemini) de AYNI hatayı zaten
yapıyordu (yalnız `GEN-DSC-010`'da C2 temiz kaldı) — yani bu Claude'a ÖZGÜ bir davranış
DEĞİL, ama **Sonnet'te (C3) en sık görülen, Haiku'da (C2) en az görülen** bir eğilim
(5 soruda C3, 1 soruda C2, 2 soruda C1). Bu, GENEL bir "Sonnet daha ayrıntılı/gönüllü
yorum ekliyor" eğiliminin bir yan etkisi olabilir — doğrulanmadı, oynama yapılmadı, yalnız
rapor edildi.

## 5. Sınıf toplamları (37 soru)

| Sınıf | Adet |
|---|---|
| (a) discovery eşleşmesi | 14 |
| (a)/(b) kaynak eksik | 8 |
| (a)/(d) değer metni eşleşmedi | 4 |
| (c) abstain gerekirken cevapladı | 5 |
| (c*) çapraz-proje referansı (birincil, isolation) | 1 |
| backend hatası (ortak, 3 sağlayıcıda da) | 1 |
| **C3-özgü: (c) belge bağlamda model çekildi** | 1 |
| **C3-özgü: (a) belge soruyu hiç cevaplamıyor** | 1 |
| **C3-özgü: (d) doğru değer, yanlış kaynak atfı** | 1 |
| **C3-özgü: (c\*) çapraz-proje referansı** | 1 |
| **TOPLAM** | **37** |

**Not:** 3 discovery sorusunda (`GEN-DSC-002/009/010`) (a) ile birlikte ikincil (c*) belirtisi
de var (üstteki tabloda ayrıca işaretli, toplama tekrar eklenmedi).

Devam ediliyor: **Adım 3** (C1'deki 9 HTTP 500 hatasının teşhisi).
