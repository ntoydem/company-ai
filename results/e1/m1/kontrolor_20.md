# Kontrolör örneklemi — 20 soru (bağımsız puanlama için)

Seçim: `random.Random(20261015).sample(ids, 20)` — soru kimlikleri sıralı listeden; cevap/kaynak metni S3 ham sonucundan aynen; puan ve gerekçe yeni puanlayıcıdan.

## ANK-DEV-001 (document, kullanıcı `enerji`)

**Soru:** Karatepe RES'in development süreci ne zaman başladı?
**Beklenti:** cevap var; kaynak kümesi ['Karatepe RES Üretim Lisansı']

**Cevap (aynen):**

```
Karatepe RES'in geliştirme süreci 01.03.2018 tarihinde başlamıştır. [K11]
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
Karatepe RES'in ilk halkası olan Facility Agreement — Draft belgesinde borçlunun en az 1,25x minimum borç servisi karşılama oranı (DSCR) tutturması gerektiği yazıyor [K51].

Bu değer Facility Agreement Amendment 02 ile önceki 1,25x seviyesinden değiştirilmiştir; güncel minimum DSCR 1,20x'tir [K32].
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
Karatepe RES'in güncel Facility Agreement'ı Facility Agreement Amendment 02'dir (Belge No DOC-ANK-FIN-006, Durum: Executed, Tarih ve Yürürlük: 15.03.2025) [K6]. Bu belge Facility Agreement Amendment 01 belgesini değiştirir [K6].
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
Güncel minimum DSCR eşiği 1,20x'tir ve 15.03.2025 tarihinden itibaren geçerlidir [K24]. Bu değer, Facility Agreement Amendment 02 ile önceki 1,25x seviyesinden değiştirilmiştir [K24][K40].

Test sıklığı için kaynaklarda belirtilen ifade şudur: DSCR, her raporlama döneminde test edilir [K40]. Güncel belgelerde test dönemleri için ayrı bir tarih listesi yoktur.

Q4 2024 covenant testiyle ilgili olarak, 20.01.2025 tarihinde sona eren test dönemi için bir waiver verilmiştir [K17]. Aynı dönem için Covenant Compliance Report'ta hesaplanan DSCR 1,24x olarak yazılmış ve genel covenant değerlendirmesi "fail" olarak sınıflandırılmıştır [K29].

Excel verisine göre:
Karatepe RES'in son covenant testinde gerçekleşen DSCR 1,37x olarak hesaplanmıştır.
```

**Kaynaklar:** ['Facility Agreement', 'Facility Agreement Amendment 02', 'Financial Model 2026', 'Karatepe RES Covenant Compliance Report — Q4 2024', 'Karatepe RES Waiver Letter — Q4 2024 Covenant Test']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** kaynak kümede değil (küme ['Covenant Report (workbook)'])

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-012 (temporal, kullanıcı `finans`)

**Soru:** Karatepe RES'in DSCR covenant'ı ne zaman ve hangi belgeyle değişti?
**Beklenti:** cevap var; kaynak kümesi ['Facility Agreement Amendment 02']

**Cevap (aynen):**

```
DSCR covenant'ı 15.03.2025 tarihinde Facility Agreement Amendment 02 (belge no. DOC-ANK-FIN-006, versiyon AMD02) ile değiştirilmiştir [K27][K32]. Bu tadil minimum DSCR'ı 1.20x olarak güncellemiş ve 15.03.2025 tarihinden itibaren geçerli kılmıştır [K32].

Bu değer, Facility Agreement Amendment 02 ile önceki 1.25x seviyesinden değiştirilmiştir [K37]. 1.25x değeri, 20.06.2022 tarihli Facility Agreement belgesinde (DOC-ANK-FIN-004) yer almaktadır [K41][K37]. Bu belge artık güncel değildir.
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
Kızılova RES'in ÇED süreci, 27.08.2026 tarihli ÇED Süreci Durum Yazısı'na göre devam etmektedir [K1]. Belgede, mevcut aşamanın "devam ediyor" durumunu koruduğu ve 12.09.2026 tarihli bir gelişmenin resmi kayıtlara intikal ettiği yazılmaktadır [K1].

Belgede bekleyen adım olarak, MNO Teknik Danışmanlık Ltd. nezdindeki onay süreçlerinin tamamlanması beklendiği belirtilmektedir [K21]. Ayrıca 27.08.2026 tarihli mutabakat metni çerçevesinde yeni bir aşamaya geçilmesinin öngörüldüğü yazmaktadır [K21]. İlgili güncellemeler ve revizyonlar tamamlandığında ÇED Süreci Durum Yazısı makamına resmi bilgilendirme yapılacağı belirtilmektedir [K21].

Belgede yürürlük tarihi henüz belirlenmedi [K2].
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
Hayır, belgelere göre ÇED süreci henüz tamamlanmamıştır; süreç devam etmektedir. 27.08.2026 tarihli ÇED Süreci Durum Yazısı'nda "Mevcut aşamada devam ediyor" durumunun geçerliliğini koruduğu belirtilmektedir [K1]. Aynı belgede, MNO Teknik Danışmanlık Ltd. nezdindeki onay süreçlerinin tamamlanmasının beklendiği yazılmaktadır [K23].
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
Bu adda bir proje kayıtlı değil; hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?
```

**Kaynaklar:** — · assist `term_mismatch`: 'Bu adda bir proje kayıtlı değil; hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?'; liste []
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=skipped, discovery=skipped

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-AUT-002 (authorization, kullanıcı `enerji`)

**Soru:** Karatepe RES'in toplam kredi tutarı nedir?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
Bu konuda kesin bilgi bulamadım.
Kastedilen, EPC sözleşme bedeli mi yoksa başka bir kredi veya finansman kalemi mi?
```

**Kaynaklar:** — · assist `clarify`: 'Kastedilen, EPC sözleşme bedeli mi yoksa başka bir kredi veya finansman kalemi mi?'; liste []
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
Karatepe RES Üretim Lisansı 15.06.2020 tarihlidir ve yürürlük tarihi de 15.06.2020'dir [K22], [K54].

Kızılova RES Önlisans Belgesi'nin tarihi 18.01.2024'tür [K33], [K65].
ÇED Süreci Durum Yazısı'nda ise "önlisans (15.01.2025)" adımının tamamlandığı yazılmıştır [K15].
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
**Karatepe RES:** Güncel toplam kurulu güç 24 MW'tır [K69]. Bu değer Licence Amendment 01 (Kapasite Tadili) ile önceki 21 MW seviyesinden değiştirilmiştir. Karatepe RES Üretim Lisansı'nda toplam kurulu güç 21 MW olarak kaydedilmiştir [K68]. Tesisin nominal kapasitesi de 24 MW olarak belirtilmiştir [K17].

**Kızılova RES:** Belgelerde 42 MW değeri planlanan hedef olarak geçmektedir [K9]. Kızılova RES için kurulu güç olarak açıkça belirtilmiş bir değer bulunmamaktadır.

Excel verisine göre:
Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.
```

**Kaynaklar:** ['Karatepe RES Üretim Lisansı', 'Kızılova RES Önlisans Belgesi', 'Licence Amendment 01 (Kapasite Tadili)', 'Provisional Acceptance & COD Certificate']
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

## GEN-DSC-004 (ambiguous, kullanıcı `enerji`)

**Soru:** Lisans durumu ne?
**Beklenti:** cevap yok

**Cevap (aynen):**

```
Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?
```

**Kaynaklar:** — · assist `disambiguate`: 'Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?'; liste []
**Puan:** önce ❌ → sonra ✅ (madde B)
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=pass, discovery=skipped

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
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Anapara Geri Ödeme Planı (84 Taksit)', 'Financial Model 2026', 'Ödeme Planı — Güncel', 'Garanti BBVA Faiz Belirleme Bildirimi', 'Avans Faturası — ABC2026000000184', 'Taksit #11 Banka Faiz Bildirimi', 'Aylık Faiz Bildirimi — Ekim 2026 Taksidi']
**Puan:** önce ❌ → sonra ❌
**Gerekçe:** güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-008 (discovery, kullanıcı `finans`)

**Soru:** Bütçe dosyası var mı?
**Beklenti:** cevap var; kaynak kümesi ['Budget vs Actual 2026']

**Cevap (aynen):**

```
«bütçe» ifadesini bütçe / gerçekleşen (Budget) olarak anladım.
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Yeşilova RES: Bankaya Giden İşletme Bütçesi (10.09.2026)
İsterseniz açayım.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Bankaya Giden İşletme Bütçesi']
**Puan:** önce ❌ → sonra ❌ (madde R7)
**Gerekçe:** güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi'])

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-012 (discovery, kullanıcı `yonetim`)

**Soru:** peki amendment var mı hiç?
**Beklenti:** cevap var; kaynak kümesi ['Facility Agreement Amendment 01']

**Cevap (aynen):**

```
«amendment» ifadesini tadil (değişiklik sözleşmesi) olarak anladım.
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Licence Amendment 01 (Kapasite Tadili) (10.02.2021)
İsterseniz açayım.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Licence Amendment 01 (Kapasite Tadili)']
**Puan:** önce ✅ → sonra ✅
**Gerekçe:** tüm kontroller geçti: value=skipped, kaynak kuralı=n/a, güvenlik=pass, assist=skipped, discovery=pass

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

