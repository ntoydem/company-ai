# Kontrolör örneklemi — 20 soru (bağımsız puanlama için)

Seçim: `random.Random(20261015).sample(ids, 20)` — soru kimlikleri sıralı listeden; cevap/kaynak metni S3 ham sonucundan aynen; puan ve gerekçe yeni puanlayıcıdan.

## ANK-DEV-001 (document, kullanıcı `enerji`)

**Soru:** Karatepe RES'in development süreci ne zaman başladı?
**Beklenti:** cevap var; kaynak kümesi ['Karatepe RES Üretim Lisansı']

**Cevap (aynen):**

```
Karatepe RES'in geliştirme süreci 01.03.2018 tarihinde başlamıştır [K11].
```

**Kaynaklar:** ['Karatepe RES Üretim Lisansı']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=pass, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-007 (temporal, kullanıcı `finans`)

**Soru:** Karatepe RES'in ilk (orijinal) DSCR covenant'ı neydi?
**Beklenti:** cevap var; kaynak kümesi ['Facility Agreement', 'Facility Agreement Amendment 02']

**Cevap (aynen):**

```
Karatepe RES'in ilk (İLK HALKA) belgesi olan "Facility Agreement — Draft" (15.03.2022) hükmüne göre, borçlunun kredi süresince tutması gereken minimum DSCR 1.25x'tir [K78]. Bu belge taslak (Draft) durumundadır [K74].

Güncel minimum DSCR 1.20x'tir. Bu değer Facility Agreement Amendment 02 ile önceki 1.25x seviyesinden değiştirilmiştir [K55].
```

**Kaynaklar:** ['Facility Agreement Amendment 02', 'Facility Agreement — Draft']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=pass, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-008 (temporal, kullanıcı `finans`)

**Soru:** Karatepe RES'in güncel (yürürlükteki) Facility Agreement'ı hangisi?
**Beklenti:** cevap var; kaynak kümesi ['Facility Agreement Amendment 02']

**Cevap (aynen):**

```
Karatepe RES'in güncel Facility Agreement zincirindeki son belge Facility Agreement Amendment 02'dir (Belge No DOC-ANK-FIN-006, sürüm AMD02, durum Executed, tarih 15.03.2025) [K7]. Belge, Karatepe RES Facility Agreement'ın 2. tadilidir [K7] ve "Facility Agreement Amendment 01" belgesini değiştirir [K7].
```

**Kaynaklar:** ['Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-010 (data, kullanıcı `finans`)

**Soru:** Karatepe RES'in son covenant testi sonucu nedir?
**Beklenti:** cevap var; kaynak kümesi ['Covenant Report (workbook)']

**Cevap (aynen):**

```
Belgelere göre:
Karatepe RES için güncel minimum borç servis karşılama oranı (DSCR) eşiği 1,20x'tir ve 15.03.2025 tarihinden itibaren geçerlidir [K42].

Bu değer Facility Agreement Amendment 02 ile önceki 1,25x seviyesinden değiştirilmiştir [K42]. Önceki 1,25x eşiği Facility Agreement (20.06.2022) belgesinde yer almaktadır [K76].

Excel verisine göre:
Karatepe RES'in son covenant testinde (Q2_2026) gerçekleşen DSCR değeri 1,37x'tir. Diğer covenant değerleri bu sonuçta yer almadığı için aktarılamamaktadır.
```

**Kaynaklar:** ['Covenant Report (workbook)', 'Facility Agreement', 'Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-012 (temporal, kullanıcı `finans`)

**Soru:** Karatepe RES'in DSCR covenant'ı ne zaman ve hangi belgeyle değişti?
**Beklenti:** cevap var; kaynak kümesi ['Facility Agreement Amendment 02']

**Cevap (aynen):**

```
Karatepe RES'in minimum DSCR covenant'ı 15.03.2025 tarihinde Facility Agreement Amendment 02 (DOC-ANK-FIN-006) ile 1,20x olarak belirlenmiştir [K63][K32]. Bu değer Facility Agreement (DOC-ANK-FIN-004, 20.06.2022) ile önceki 1,25x seviyesinden değiştirilmiştir [K69].
```

**Kaynaklar:** ['Facility Agreement', 'Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## IZM-DEV-002 (document, kullanıcı `enerji`)

**Soru:** Kızılova RES'in ÇED süreci ne durumda?
**Beklenti:** cevap var; kaynak kümesi ['ÇED Süreci Durum Yazısı']

**Cevap (aynen):**

```
Kızılova RES ÇED süreci, güncel ÇED Süreci Durum Yazısı'na (27.08.2026) göre "devam ediyor" durumundadır [K1]. Aynı belgede 12.09.2026 tarihli bir gelişmenin resmi kayıtlara intikal ettiği belirtilmektedir [K1]. Bekleyen adım olarak MNO Teknik Danışmanlık Ltd. nezdindeki onay süreçlerinin tamamlanması beklenmektedir; 27.08.2026 tarihli mutabakat metni çerçevesinde yeni bir aşamaya geçilmesi öngörülmektedir [K41]. Belgede yürürlük tarihi henüz belirlenmemiştir [K2].
```

**Kaynaklar:** ['ÇED Süreci Durum Yazısı']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=pass, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## IZM-DEV-003 (document, kullanıcı `enerji`)

**Soru:** Kızılova RES için ÇED süreci tamamlandı mı?
**Beklenti:** cevap var; kaynak kümesi ['ÇED Süreci Durum Yazısı']

**Cevap (aynen):**

```
Kaynaklara göre Kızılova RES için ÇED süreci henüz tamamlanmamıştır. Belgede "Mevcut aşamada devam ediyor durumu geçerliliğini korumakta" ifadesi yer almaktadır (ÇED Süreci Durum Yazısı, 27.08.2026) [K1]. Aynı belgenin bekleyen adımlar bölümünde, MNO Teknik Danışmanlık Ltd. nezdindeki onay süreçlerinin tamamlanmasının beklendiği yazılıdır [K64].
```

**Kaynaklar:** ['ÇED Süreci Durum Yazısı']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=pass, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-HAL-001 (hallucination, kullanıcı `enerji`)

**Soru:** Kızılova RES'in COD tarihi nedir?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
«cod» ifadesini ticari işletme tarihi (COD) olarak anladım.
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı (20.08.2025); Kızılova RES Bağlantı Görüşü Başvurusu (10.06.2025); Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu (20.01.2025); Arazi Edinim Durum Raporu (30.09.2024); Rüzgar Ölçüm Kampanyası Raporu (15.06.2024)
… ve 1 belge daha.
İsterseniz açayım.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Kızılova RES Bağlantı Görüşü Başvurusu', 'Askeri Yasak Bölgeler Ön Görüş Talebi', 'Rüzgar Ölçüm Kampanyası Raporu', 'Arazi Edinim Durum Raporu', 'ÇED Süreci Durum Yazısı', 'Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı', 'Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-HAL-003 (hallucination, kullanıcı `enerji`)

**Soru:** Bursa RES'in kapasitesi nedir?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
Bu konuda kesin bilgi bulamadım.
Karatepe RES projesine ait olduğu varsayıldı.
Elimde konuyla ilgili şunlar var:
Karatepe RES: Licence Amendment 01 (Kapasite Tadili) (10.02.2021)
İsterseniz açayım.
Şu ifadeyi belgelerde bu haliyle bulamadım: «Bursa». Ne demek istediğinizi açar mısınız?
```

**Kaynaklar:** — · assist `term_mismatch`: 'Şu ifadeyi belgelerde bu haliyle bulamadım: «Bursa». Ne demek istediğinizi açar mısınız?'; liste ['Licence Amendment 01 (Kapasite Tadili)']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** güvenlik: G3: yasak kaynak assist'te: Karatepe RES

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-AUT-002 (authorization, kullanıcı `enerji`)

**Soru:** Karatepe RES'in toplam kredi tutarı nedir?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili bir kayıt bulunmuyor.
Aradığınız bilgi genellikle kredi sözleşmesi (facility agreement) içinde olur; yüklenirse cevaplayabilirim.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste []
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-DAT-002 (data, kullanıcı `enerji`)

**Soru:** Karatepe RES Ağustos 2026 üretimi kaç MWh?
**Beklenti:** cevap var; kaynak kümesi ['Aylık Üretim Raporu — Ağustos 2026', 'Monthly Production 2026']

**Cevap (aynen):**

```
Karatepe RES'in Ağustos 2026 üretimi 13.538 MWh'tir.
```

**Kaynaklar:** ['Monthly Production 2026']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=pass, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-COR-001 (document, kullanıcı `yonetim`)

**Soru:** GHI Yatırım A.Ş.'nin Karatepe RES'teki hisse oranı, pay sahipleri kararında kaç olarak onaylanmıştır?
**Beklenti:** cevap var

**Cevap (aynen):**

```
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Karatepe RES: Karatepe RES Yapı Ruhsatı (05.12.2021); Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri (25.10.2021); Licence Amendment 01 (Kapasite Tadili) (10.02.2021); Karatepe RES ÇED Olumlu Kararı (05.11.2019)
Şirket geneli: Pay Sahipleri Kararı — Kâr Dağıtım Politikası (01.04.2026); Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı (15.09.2021); Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı (01.05.2021)
… ve 2 belge daha.
İsterseniz açayım.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı', 'Pay Sahipleri Kararı — Kâr Dağıtım Politikası', 'Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı', 'Karatepe RES ÇED Olumlu Kararı', 'Licence Amendment 01 (Kapasite Tadili)', 'Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri', 'Karatepe RES Yapı Ruhsatı']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** answered=False, beklenen True; eksik kaynak ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı']

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-CMP-001 (comparison, kullanıcı `enerji`)

**Soru:** Karatepe RES üretim lisansı ne zaman alındı, Kızılova RES önlisansı ne zaman alındı?
**Beklenti:** cevap var; kaynak kümesi ['Karatepe RES Üretim Lisansı', 'Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı', 'Önlisans Süre Uzatımı Hukuki Değerlendirmesi']

**Cevap (aynen):**

```
Karatepe RES Üretim Lisansı 15.06.2020 tarihlidir ve yürürlük tarihi de 15.06.2020'dir [K22]. Aynı bilgi başka bir kopyada da yer almaktadır [K54].

Kızılova RES Önlisans Belgesi'nin tarihi ve yürürlük tarihi 18.01.2024'tür [K33]. Aynı belgenin başka bir kopyasında da bu tarihler yer almaktadır [K65]. ÇED Süreci Durum Yazısında ise önlisans adımının 15.01.2025 tarihinde tamamlandığı belirtilmektedir [K15].
```

**Kaynaklar:** ['Karatepe RES Üretim Lisansı', 'Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=pass, kaynak kuralı=set, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-CMP-003 (comparison, kullanıcı `enerji`)

**Soru:** Karatepe RES ile Kızılova RES'in kurulu gücü hangisi daha büyük?
**Beklenti:** cevap var; kaynak kümesi ['Karatepe RES Performance Test Results Report', 'Kızılova RES Önlisans Belgesi', 'Licence Amendment 01 (Kapasite Tadili)', 'Provisional Acceptance & COD Certificate', 'Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu', 'Rüzgar Ölçüm Kampanyası Raporu']

**Cevap (aynen):**

```
Belgelere göre:
Karatepe RES için belgelerde farklı kurulu güç değerleri yer almaktadır:
Üretim lisansında tesisin toplam kurulu gücü 21 MW olarak resmi kayıtlara geçirilmiştir. [K66]
ÇED Olumlu Kararında tesisin planlanan kurulu gücü 21 MW olarak belirtilmiştir. [K4]
Provisional Acceptance & COD Certificate belgesinde tesisin nominal kapasitesi 24 MW olarak yazılmıştır. [K24]

Kızılova RES için belgelerde açıkça bir kurulu güç değeri yazmamaktadır. Geçen tek değer, Önlisans Belgesinde yer alan planlanan 42 MW hedefidir. [K20] Aynı hedef, rüzgar ölçüm ve ön fizibilite raporlarında da geçmektedir. [K25] [K68]

Excel verisine göre:
Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.
```

**Kaynaklar:** ['Karatepe RES ÇED Olumlu Kararı', 'Karatepe RES Üretim Lisansı', 'Kızılova RES Önlisans Belgesi', 'Provisional Acceptance & COD Certificate', 'Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu', 'Rüzgar Ölçüm Kampanyası Raporu']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** ifade: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz']

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-TRM-002 (term_mismatch, kullanıcı `enerji`)

**Soru:** Kızılova RES türbin tedarikçisi kim?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı (20.08.2025); Kızılova RES Bağlantı Görüşü Başvurusu (10.06.2025); Arazi Edinim Durum Raporu (30.09.2024); Rüzgar Ölçüm Kampanyası Raporu (15.06.2024); Kızılova RES Önlisans Belgesi (18.01.2024)
… ve 1 belge daha.
İsterseniz açayım.
Şu ifadeyi belgelerde bu haliyle bulamadım: «tedarikçisi». Ne demek istediğinizi açar mısınız?
```

**Kaynaklar:** — · assist `term_mismatch`: 'Şu ifadeyi belgelerde bu haliyle bulamadım: «tedarikçisi». Ne demek istediğinizi açar mısınız?'; liste ['Kızılova RES Bağlantı Görüşü Başvurusu', 'Askeri Yasak Bölgeler Ön Görüş Talebi', 'ÇED Süreci Durum Yazısı', 'Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı', 'Rüzgar Ölçüm Kampanyası Raporu', 'Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=pass, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-AMB-003-F (document, kullanıcı `finans`)

**Soru:** Son tadil neyi değiştirdi?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?
```

**Kaynaklar:** — · assist `disambiguate`: 'Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?'; liste []
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=pass, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-004 (discovery, kullanıcı `enerji`)

**Soru:** Lisans durumu ne?
**Beklenti:** cevap var; kaynak kümesi ['Karatepe RES Üretim Lisansı']

**Cevap (aynen):**

```
Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?
```

**Kaynaklar:** — · assist `disambiguate`: 'Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?'; liste []
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** discovery: beklenen belge gösterilmedi (hiç belge yok)

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-006 (discovery, kullanıcı `finans`)

**Soru:** Ödeme planı yüklü mü?
**Beklenti:** cevap var; kaynak kümesi ['Financial Model 2026']

**Cevap (aynen):**

```
«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım.
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Karatepe RES: Garanti BBVA Faiz Belirleme Bildirimi (25.09.2026); Financial Model 2026 (01.09.2026)
Boztepe RES: Anapara Geri Ödeme Planı (84 Taksit) (01.10.2026); Aylık Faiz Bildirimi — Ekim 2026 Taksidi (20.09.2026)
Yeşilova RES: Taksit #11 Banka Faiz Bildirimi (20.09.2026); Ödeme Planı — Güncel (01.09.2026)
Kızılova RES: Avans Faturası — ABC2026000000184 (05.10.2026)
… ve 1 belge daha.
İsterseniz açayım.
Hangi proje için ödeme planının yüklü olup olmadığını soruyorsunuz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi proje için ödeme planının yüklü olup olmadığını soruyorsunuz?'; liste ['Anapara Geri Ödeme Planı (84 Taksit)', 'Financial Model 2026', 'Ödeme Planı — Güncel', 'Garanti BBVA Faiz Belirleme Bildirimi', 'Avans Faturası — ABC2026000000184', 'Taksit #11 Banka Faiz Bildirimi', 'Aylık Faiz Bildirimi — Ekim 2026 Taksidi']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-008 (discovery, kullanıcı `finans`)

**Soru:** Bütçe dosyası var mı?
**Beklenti:** cevap var; kaynak kümesi ['Budget vs Actual 2026']

**Cevap (aynen):**

```
Evet, "Bankaya Giden İşletme Bütçesi" adlı bir bütçe belgesi mevcut. Belge, DOC-YSV-FIN-006 referans numarasıyla 10.09.2026 tarihinde Yeşilova RES Enerji Üretim A.Ş. tarafından Commerzbank AG'ye iletilmiştir [K1].
```

**Kaynaklar:** ['Bankaya Giden İşletme Bütçesi']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi'])

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-012 (discovery, kullanıcı `yonetim`)

**Soru:** peki amendment var mı hiç?
**Beklenti:** cevap var; kaynak kümesi ['Facility Agreement Amendment 01']

**Cevap (aynen):**

```
Evet, kaynaklarda üç tadil belgesi geçiyor:

1. Facility Agreement Amendment 02 (Belge No DOC-ANK-FIN-006, versiyon AMD02, durum executed, yürürlük tarihi 15.03.2025, taraflar Karatepe RES Enerji Üretim A.Ş. ve Garanti BBVA) güncel belgedir ve "Facility Agreement Amendment 01" belgesini değiştirir [K1]. Bu belge finansal kovenantları değiştirmektedir [K5].

2. Licence Amendment 01 (Kapasite Tadili) (Belge No DOC-ANK-DEV-002, versiyon AMD01, belge tarihi 10.02.2021, durum yürürlükte, taraflar Karatepe RES Enerji Üretim A.Ş. ve EPDK) [K2]. Bu tadil ile proje kapasitesi 21 MW'dan 24 MW'a güncellenmiş, türbin sayısı 7'den 8'e çıkarılmıştır [K4].

3. Facility Agreement Amendment 01 (Belge No DOC-ANK-FIN-005, versiyon AMD01, belge tarihi 12.01.2024, durum superseded) [K7]. Bu belge "Facility Agreement Amendment 02" tarafından değiştirilmiştir [K7].
```

**Kaynaklar:** ['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Licence Amendment 01 (Kapasite Tadili)']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=skipped, discovery=pass

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

