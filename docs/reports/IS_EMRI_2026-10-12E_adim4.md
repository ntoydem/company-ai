# İş Emri 2026-10-12-E — Adım 4 Raporu (öneriler — karar DEĞİL)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — **bu bölüm bir karar vermiyor, yalnız
sıralı öneri sunuyor.** Hiçbir kod/belge/eşik değiştirilmedi.

## Hangi sınıf kaç soruyu etkiliyor (Adım 2/3'ün sayıları)

| Sınıf | Soru sayısı | Sağlayıcı bağımlı mı? |
|---|---|---|
| (a) discovery eşleştirme kusuru | 14 (+4'ü C1'de ayrıca backend hatası) | Hayır — üçünde de aynı |
| (a)/(b) kaynak eksik (document/data/temporal) | 8 | Hayır — üçünde de aynı |
| (a)/(d) değer metni eşleşmedi | 4 | Hayır — üçünde de aynı |
| (c) abstain gerekirken cevaplama | 5 | Hayır (üçünde de var) ama en az C2'de |
| (c*) çapraz-proje referansı (izolasyon riski) | 5 (1'i C3-özgü) | **Kısmen** — en sık C3/Sonnet'te (5), sonra C1/Gemini (2), en az C2/Haiku (1) |
| Gemini'ye özgü backend hatası (HTTP 500) | 8 | **Evet** — yalnız Gemini yolunda |
| Ortak backend hatası (ANK-MIX-001) | 1 | Hayır |
| C3-özgü gerçek gerileme (IZM-DEV-005/006, ANK-OPS-003) | 3 | **Evet** — yalnız Claude'da |

## Öneri sıralaması (etkiye göre — karar değil)

**1. Discovery eşleştirme kusuru (14-18 soru, en büyük hacim) — KÜTÜPHANE/ÖZELLİK işi.**
Sağlayıcıdan tamamen bağımsız (Gemini'de de %11-14 civarında kalıyor). Öneri: önce
`pending_documents` eşleştirme mantığının/discovery sorularının kendisinin incelenmesi
— bu bir prompt veya model seçimi sorunu DEĞİL, muhtemelen belge kütüphanesinin discovery
sorularının beklediği belgeleri içermemesi veya eşleştirme kriterinin aşırı katı olması.

**2. Kaynak eksikliği + değer metni eşleşmesi (12 soru) — KÜTÜPHANE/İÇERİK işi.**
Sağlayıcıdan bağımsız. Öneri: bu 12 sorunun her biri için belgenin AÇIKÇA beklenen metni
içerip içermediği tek tek doğrulanmalı (Adım 1'deki yöntemle) — bazıları gerçek içerik
boşluğu, bazıları aşırı katı metin eşleşmesi olabilir; ayrım yapılmadan genellenemez.

**3. Abstain/çapraz-proje kalibrasyonu (10 soru) — PROMPT işi, model seçiminden kısmen
etkileniyor.** Ambiguity (abstain) sorunu TÜM sağlayıcılarda var — promptun "belirsiz
sorularda cevap verme" talimatı güçlendirilebilir (tüm sağlayıcılara fayda sağlar).
Çapraz-proje referansı Sonnet'te en sık — bu NOKTADA promptun "yalnız sorulan projeye
odaklan, başka projeyle karşılaştırma/istisna belirtme yapma" talimatı daha açık
yazılırsa özellikle Sonnet'in gönüllü ayrıntı ekleme eğilimini frenleyebilir.

**4. Gemini'ye özgü backend hatası (8 soru) — KOD işi, ACİL ve CANLI.** Bu, Claude
taşıma kararından TAMAMEN bağımsız: **canlı sistem ŞU AN Gemini kullanıyor** ve bu hata
canlıda da üretilebilir (discovery/data/document sorularında olası). Öneri: traceback
elde edilecek bir ortamda (loglar kaybolmadan) yeniden üretilip kök nedeni bulunmalı —
bu, migrasyon kararından ÖNCE bile ele alınması gereken bağımsız bir kalite sorunu.

**5. Ortak backend hatası (ANK-MIX-001, 1 soru) — KOD işi.** Küçük hacim ama üç
sağlayıcıyı da etkiliyor; MIXED soru tipinin Excel-birleştirme kodunda bir kusur olabilir.

**6. C3-özgü gerçek gerilemeler (3 soru, document kategorisi) — MODEL SEÇİMİ işi.**
En küçük hacim ama D emrinin kriterini REDDETTİREN tek şey bu. Öneri: bu 3 sorunun
davranışı (belge bağlamda olsa da modelin cevaplamayı reddetmesi/yanlış kaynak seçmesi)
izlenmeye değer — ama 99 sorudan 3'ü, genel tabloyu (toplam doğru C3=62 > C1=53) tersine
çevirecek ölçekte değil.

## Özet ayrım

- **Kütüphane (belge) işi:** discovery eşleştirme (14-18) + kaynak/değer eksikliği (12) =
  **26-30 soru**, en büyük hacim, sağlayıcıdan bağımsız.
- **Getirme/prompt işi:** abstain/çapraz-proje kalibrasyonu (10 soru), sağlayıcıdan
  bağımsız ama Sonnet'te biraz daha belirgin.
- **Kod hatası (backend):** Gemini'ye özgü (8) + ortak (1) = **9 soru**, migrasyon
  kararından bağımsız, canlıyı da etkiliyor.
- **Model seçimi:** yalnız **3 soru** (gerçek C3-özgü document gerilemesi) — en küçük
  hacim.

**Karar bu raporun kapsamı dışında — yalnız öncelik sırası ve sınıflandırma sunuldu.**
