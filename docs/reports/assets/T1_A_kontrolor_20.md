# T1-A — Kontrolör örneklemi: 20 şüpheli/sınır soru

Seçim: `T1_A_comertlik.md` sınıf (a)–(d) içinden elle; F0'ın rastgele 20'siyle (`results/s3_rescored/kontrolor_20.md`) çakışan yalnız ANK-FIN-007 ve GEN-AMB-003-F. Cevap/kaynak metni S3 ham sonucundan aynen; beklenen = ledger ham değeri (+ puanlayıcının aradığı yazımlar); puan = v2.0.

## ANK-FIN-001 (document, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Karatepe RES'in financial close tarihi nedir?
**Beklenen:** cevap var; ledger: project.timeline.financial_close.date = datetime.date(2022, 7, 8); aranan yazım: [['08.07.2022', '2022-07-08', 'July 8, 2022']]; beklenen kaynak ['Facility Agreement']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Karatepe RES'in finansal kapanış tarihi 08.07.2022'dir. Bu tarih, orijinal sözleşme kapsamında gerçekleşen finansal kapanış için verilmiştir [K7].
```

**Kaynaklar:** ['Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅ · value=pass, kaynak kuralı=set, küme=['Facility Agreement', 'Facility Agreement Amendment 02'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer doğru (08.07.2022); kaynak Amendment 02 — FA zincirinin güncel halkası, aynı olgu; v1'de de tür okumasıyla geçerdi

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-007 (temporal, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Karatepe RES'in ilk (orijinal) DSCR covenant'ı neydi?
**Beklenen:** cevap var; ledger: project.finance.dscr_covenant.initial.value = 1.25; aranan yazım: [['1,25x', '1.25x']]; beklenen kaynak ['Facility Agreement']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Karatepe RES'in ilk (İLK HALKA) belgesi olan "Facility Agreement — Draft" (15.03.2022) hükmüne göre, borçlunun kredi süresince tutması gereken minimum DSCR 1.25x'tir [K78]. Bu belge taslak (Draft) durumundadır [K74].

Güncel minimum DSCR 1.20x'tir. Bu değer Facility Agreement Amendment 02 ile önceki 1.25x seviyesinden değiştirilmiştir [K55].
```

**Kaynaklar:** ['Facility Agreement Amendment 02', 'Facility Agreement — Draft']
**Puan:** önce ✅ → sonra ✅ · value=pass, kaynak kuralı=set, küme=['Facility Agreement', 'Facility Agreement Amendment 02'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer doğru (1,25x); Draft'ı da gösteriyor (tolere edildi); 'ilk' soruya Draft'tan cevap vermesi tarihsel okuma — kontrolör bakmalı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-009 (document, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Karatepe RES Facility Agreement'ında kaç amendment var?
**Beklenen:** cevap var; ledger: project.finance.facility_chain = ['DOC-ANK-FIN-001', 'DOC-ANK-FIN-002', 'DOC-ANK-FIN-003', 'DOC-ANK-FIN-004', 'DOC-ANK-FIN-005', 'DOC-ANK-FIN-006']; beklenen kaynak ['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Kaynaklarda Karatepe RES Facility Agreement'a ilişkin iki amendment bulunmaktadır.

Facility Agreement Amendment 01 (DOC-ANK-FIN-005), 12.01.2024 tarihli ve durumu superseded (önceki sürüm) olan belgedir [K62]. Amendment 02 tarafından değiştirilmiştir [K62].

Facility Agreement Amendment 02 (DOC-ANK-FIN-006), 15.03.2025 tarihli ve durumu executed olan güncel belgedir [K4]. Amendment 01'i değiştirmektedir [K4].
```

**Kaynaklar:** ['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: list), kaynak kuralı=set, küme=['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** 'Facility Agreement'ında' kalıbı 14 işaret dışında; tam belge gösterildiği için sonuç değişmez; değer (2 amendment) doğrulanmadı ama metinde doğru

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-011 (document, kullanıcı `finans`, MIXED_QUERY)

**Soru:** Karatepe RES'in güncel outstanding (kalan) borcu nedir?
**Beklenen:** cevap var; ledger: project.finance.outstanding_debt_as_of_demo_today.value = 11671800; aranan yazım: [['11.671.800 USD', '11,671,800 USD']]; beklenen kaynak ['Covenant Compliance Report Q2 2026']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Belgelere göre:
Karatepe RES finansman sözleşmesinin toplam kredi tutarı kaynaklarda 14.000.000 USD olarak yazılıdır. Bu değer 20.06.2022 tarihli Facility Agreement belgesindedir ve belge önceki sürüm olarak işaretlidir [K75]. Güncel tadil belgesi (Facility Agreement Amendment 02) kredi tutarını içermediği için bu değer geçerli kabul edilmiştir. Aynı belgede faiz oranı baseline endeks + %3,25 olarak yazılmıştır [K75]. Güncel tadilde marj %2,9 olarak yer almaktadır [K55]. Bu değer Facility Agreement Amendment 02 ile önceki %3,25 seviyesinden değiştirilmiştir.

Güncel Covenant Compliance Report Q2 2026 belgesine göre kullandırılan (utilised) toplam kredi tutarı 13.600.000 USD'dir ve bu tutar tamamen Garanti BBVA tarafından sağlanmıştır [K42]. Aynı belgede kalan bakiye 11.671.800 USD olarak yazılmıştır [K42].

Kaynaklarda bulunan tek tranş, 8.000.000 USD tutarındaki Tranche 1'dir. Bu tranş 15.07.2022 tarihinde talep edilmiştir [K14][K40]. Diğer tranşlara ilişkin bilgi kaynaklarda yer almamaktadır.

Geri ödeme takvimi için kaynaklarda sınırlı bilgi vardır. 20.06.2022 tarihli Facility Agreement belgesine göre geri ödeme takvimi 10 ay sonra başlamaktadır ve vade 13 yıl olarak tanımlanmıştır [K76]. Facility Agreement Amendment 01 belgesinde geri ödeme yapısı "Sculpted (variable), semi-annual instalments after grace", yani grace döneminden sonra değişken yapılı, yarı yıllık taksitler olarak yazılmıştır [K79]. Bu tadil belgesi de önceki sürümdür ve taksit tutarı ile tarihleri belirtilmemiştir. Ödeme planının ayrıntıları ayrıca iletilen ödeme planı belgelerinde yer aldığı belirtilmiştir [K41], ancak bu belgeler kaynaklarda bulunmamaktadır.

Excel verisine göre:
Karatepe RES için 6 Ekim 2026 itibarıyla kalan kredi bakiyesi 11.671.800 USD'dir.
```

**Kaynaklar:** ['Covenant Compliance Report Q2 2026', 'Facility Agreement', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Financial Model 2026', 'Garanti BBVA Faiz Belirleme Bildirimi', 'Karatepe RES Drawdown Notice — Tranche 1']
**Puan:** önce ✅ → sonra ✅ · value=pass, kaynak kuralı=set, küme=['Covenant Compliance Report Q2 2026'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer doğru (11.671.800); 7 kaynak, uzun cevap, %3,25 / 14.000.000 USD gibi ek rakamlar MIXED olduğu için G1 denetimi dışı — kontrolör bakmalı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-NEG-003 (document, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Kredi sözleşmesinin vadesi kaç yıl?
**Beklenen:** cevap yok; assist `clarify`; ledger: project.finance.tenor_years.current.value = 13; beklenen kaynak ['Facility Agreement']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?
```

**Kaynaklar:** — · assist `disambiguate`: 'Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?'; liste []
**Puan:** önce ❌ → sonra ✅ · value=skipped (expect_no_answer + expect_assist), kaynak kuralı=n/a, küme=—, güvenlik=pass, F-8=pass
**Sınıf / okuma:** vade sorulmuş, netleştirme döndü (Karatepe mi Yeşilova mı); altın küme bunu bekliyor (expect_assist) — puan tasarım gereği, 'cömert' değil

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-AMB-003-F (document, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Son tadil neyi değiştirdi?
**Beklenen:** cevap yok; assist `clarify`; ledger: project.finance.facility_chain = ['DOC-ANK-FIN-001', 'DOC-ANK-FIN-002', 'DOC-ANK-FIN-003', 'DOC-ANK-FIN-004', 'DOC-ANK-FIN-005', 'DOC-ANK-FIN-006']; beklenen kaynak ['Facility Agreement Amendment 02']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?
```

**Kaynaklar:** — · assist `disambiguate`: 'Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?'; liste []
**Puan:** önce ❌ → sonra ✅ · value=skipped (expect_no_answer + expect_assist), kaynak kuralı=n/a, küme=—, güvenlik=pass, F-8=pass
**Sınıf / okuma:** 'son tadil' → proje netleştirmesi; beklenen clarify, gelen disambiguate (eşdeğer sayılıyor, B2a)

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-GEN-002 (document, kullanıcı `yonetim`, DOCUMENT_QUERY)

**Soru:** ÇED (Çevresel Etki Değerlendirmesi) süreci nedir?
**Beklenen:** cevap yok; ledger: — (cevap beklenmiyor); beklenen kaynak —; yasak —

**Cevap (aynen):**

```
Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?
```

**Kaynaklar:** — · assist `disambiguate`: 'Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?'; liste []
**Puan:** önce ❌ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=—, güvenlik=pass, F-8=pass
**Sınıf / okuma:** genel bilgi sorusuna 'Hangi projeyi kastediyorsunuz' döndü; cevapsız olması doğru, netleştirmenin anlamlılığı tartışılır — kontrolör bakmalı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-HAL-004 (hallucination, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Kızılova RES'in kredi faiz oranı nedir?
**Beklenen:** cevap yok; ledger: — (cevap beklenmiyor); beklenen kaynak —; yasak ['Facility Agreement', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Karatepe RES']

**Cevap (aynen):**

```
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Kızılova RES: Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ) (05.10.2026); Avans Faturası — ABC2026000000184 (05.10.2026); Taahhüt Komisyonu Bildirimi (01.10.2026); EPC Avans Teminat Mektubu (20.09.2026)
İsterseniz açayım.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ)', 'Avans Faturası — ABC2026000000184', 'EPC Avans Teminat Mektubu', 'Taahhüt Komisyonu Bildirimi']
**Puan:** önce ❌ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=—, güvenlik=pass, F-8=pass
**Sınıf / okuma:** cevap yok + yalnız Kızılova listesi; Karatepe FA zinciri gösterilmedi — v13 beklentisiyle tutarlı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-001-M (discovery, kullanıcı `finans_mudur`, DOCUMENT_QUERY)

**Soru:** Karatepe'nin finansal modeli var mı?
**Beklenen:** cevap var; ledger: —; beklenen kaynak ['Financial Model 2026']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
«finansal model» ifadesini finansal model (Financial Model workbook'u) olarak anladım.
Bu konuda kesin bilgi bulamadım.
Elimde konuyla ilgili şunlar var:
Karatepe RES: Financial Model 2026 (01.09.2026)
İsterseniz açayım.
Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?
```

**Kaynaklar:** — · assist `clarify`: 'Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?'; liste ['Financial Model 2026']
**Puan:** önce ❌ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=['Financial Model 2026'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** liste + soru (discovery ölçütü); A2 ile finans_mudur görünürlüğü düzeldi

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-005 (discovery, kullanıcı `yonetim`, DOCUMENT_QUERY)

**Soru:** Amendment var mı?
**Beklenen:** cevap var; ledger: —; beklenen kaynak ['Facility Agreement Amendment 01']; yasak ['Kızılova RES']

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
**Puan:** önce ✅ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=['Facility Agreement Amendment 01'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** liste + soru; beklenen Amendment 01 listede

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-010 (data, kullanıcı `finans`, MIXED_QUERY)

**Soru:** Karatepe RES'in son covenant testi sonucu nedir?
**Beklenen:** cevap var; ledger: project.finance.covenant_tests[-1].result = 'pass'; beklenen kaynak ['Covenant Report (workbook)']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Belgelere göre:
Karatepe RES için güncel minimum borç servis karşılama oranı (DSCR) eşiği 1,20x'tir ve 15.03.2025 tarihinden itibaren geçerlidir [K42].

Bu değer Facility Agreement Amendment 02 ile önceki 1,25x seviyesinden değiştirilmiştir [K42]. Önceki 1,25x eşiği Facility Agreement (20.06.2022) belgesinde yer almaktadır [K76].

Excel verisine göre:
Karatepe RES'in son covenant testinde (Q2_2026) gerçekleşen DSCR değeri 1,37x'tir. Diğer covenant değerleri bu sonuçta yer almadığı için aktarılamamaktadır.
```

**Kaynaklar:** ['Covenant Report (workbook)', 'Facility Agreement', 'Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: str), kaynak kuralı=set, küme=['Covenant Report (workbook)'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı ('pass' biçimlenemez); cevap 1,37x veriyor ama test sonucunu (geçti) açıkça söylemiyor — sınır, kontrolör bakmalı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-FIN-012 (temporal, kullanıcı `finans`, DOCUMENT_QUERY)

**Soru:** Karatepe RES'in DSCR covenant'ı ne zaman ve hangi belgeyle değişti?
**Beklenen:** cevap var; ledger: project.finance.dscr_covenant.changed_by = 'DOC-ANK-FIN-006'; beklenen kaynak ['Facility Agreement Amendment 02']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Karatepe RES'in minimum DSCR covenant'ı 15.03.2025 tarihinde Facility Agreement Amendment 02 (DOC-ANK-FIN-006) ile 1,20x olarak belirlenmiştir [K63][K32]. Bu değer Facility Agreement (DOC-ANK-FIN-004, 20.06.2022) ile önceki 1,25x seviyesinden değiştirilmiştir [K69].
```

**Kaynaklar:** ['Facility Agreement', 'Facility Agreement Amendment 02']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: str), kaynak kuralı=set, küme=['Facility Agreement Amendment 02'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı (belge kimliği); metin Amendment 02 / 15.03.2025 diyor — doğru

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-EPC-004 (temporal, kullanıcı `enerji`, MIXED_QUERY)

**Soru:** Karatepe RES'in COD'u ilk beklenen tarihe göre sapmış mı? Belgelerde sebep yazıyor mu?
**Beklenen:** cevap var; ledger: project.construction.change_orders[0].subject.value = 'COD deferral: grid connection works'; beklenen kaynak ['EPC Contract', 'Provisional Acceptance & COD Certificate']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Belgelere göre:
İlk beklenen COD tarihi 30.06.2023'tür [K75]. EPC Change Order 01 (COD Deferral) belgesinde de orijinal takvimin bu tarihe kadar tamamlanmayı öngördüğü yazmaktadır [K23].

Gerçekleşen COD 15.10.2023'tür [K3]. Bu değer EPC Change Order 01 (COD Deferral) ile önceki 30.06.2023 seviyesinden değiştirilmiştir [K48].

Sapmanın sebebi olarak belgelerde iki ayrı açıklama yer almaktadır. Provisional Acceptance & COD Certificate'te kaydedilen sebep "COD ertelemesi: şebeke bağlantı işleri" olarak belirtilmiştir [K3]. EPC Change Order 01 (COD Deferral) belgesinde ise öngörülemeyen saha koşullarının kritik yolu etkilediği yazmaktadır [K23].

Excel verisine göre:
Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.
```

**Kaynaklar:** ['EPC Change Order 01 (COD Deferral)', 'EPC Contract', 'Provisional Acceptance & COD Certificate']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: str), kaynak kuralı=set, küme=['EPC Contract', 'Provisional Acceptance & COD Certificate'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı; 'şebeke bağlantı işleri' sebebi metinde var; MIXED → G1 dışı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## IZM-DEV-001 (document, kullanıcı `enerji`, DOCUMENT_QUERY)

**Soru:** Kızılova RES projesi hangi aşamada?
**Beklenen:** cevap var; ledger: project.stage = 'development'; beklenen kaynak ['ÇED Süreci Durum Yazısı']; yasak ['Karatepe RES']

**Cevap (aynen):**

```
Kızılova RES için en güncel durum, 27.08.2026 tarihli ÇED Süreci Durum Yazısı'nda yer alıyor: ÇED çalışmaları "devam ediyor" durumunda ve bu durum geçerliliğini koruyor [K1]. Belgede 12.09.2026 tarihli bir gelişmenin resmi kayıtlara geçtiği belirtiliyor, ancak gelişmenin içeriği yazılmamış [K1].

Belgeye göre tamamlanan adımlar şunlardır: önlisans (15.01.2025) ve arazi edinimi (20.01.2025 itibarıyla) [K1]. Önlisans belgesinin tarihi ise 18.01.2024 olarak kayıtlı [K9].

Kamu duyurusu ve halkın katılımı toplantısı 20.08.2025 tarihinde tamamlanmıştır [K8]. Bağlantı görüşü başvurusu 10.06.2025 tarihinde yapılmıştır [K2]. Bu başvuruya ilişkin değerlendirme süreci sürdürülmekte olup nihai bağlantı görüşünün resmi olarak yayımlanması beklenmektedir [K56].
```

**Kaynaklar:** ['Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı', 'Kızılova RES Bağlantı Görüşü Başvurusu', 'Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: str), kaynak kuralı=set, küme=['ÇED Süreci Durum Yazısı'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı ('development'); cevap aşamayı adıyla söylemiyor, ÇED/önlisans durumunu aktarıyor — sınır, kontrolör bakmalı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## IZM-DEV-008 (document, kullanıcı `enerji`, DOCUMENT_QUERY)

**Soru:** Kızılova RES'te hangi kritik adımlar bekliyor?
**Beklenen:** cevap var; ledger: project.development.pending_steps = [{'step': 'ÇED', 'expected': 'İDK toplantısı bekleniyor (ÇED-2026-057). Ayrıca Orman Ön İzni devam (30.06.2026 itibarıyla); Mera Tahsis Değişikliği talebi 21.08.2026, komisyon sonraki toplantısı 12.11.2026.', 'tag': 'USER_FACT'}, {'step': 'İmar Kesinleşme', 'expected': None, 'tag': 'USER_FACT'}, {'step': "Kat'i Proje Onayı", 'expected': None, 'tag': 'USER_FACT'}, {'step': 'Bağlantı Anlaşması', 'expected': None, 'tag': 'USER_FACT'}, {'step': 'Yapı Ruhsatı', 'expected': 'Henüz alınmamıştır.', 'tag': 'AI_ASSUMPTION'}, {'step': 'Üretim Lisansı', 'expected': 'Henüz alınmamıştır — bugüne kadar yalnızca önlisans (15.01.2025) alınmıştır.', 'tag': 'AI_ASSUMPTION'}, {'step': 'İnşaat Başlangıcı', 'expected': 'Henüz başlanmamıştır.', 'tag': 'AI_ASSUMPTION'}]; beklenen kaynak ['ÇED Süreci Durum Yazısı']; yasak ['Karatepe RES']

**Cevap (aynen):**

```
Kaynaklara göre Kızılova RES için bekleyen başlıca adımlar şunlardır:

ÇED süreci devam ediyor. Güncel ÇED durum yazısında süreç "devam ediyor" durumundadır ve 12.09.2026 tarihli bir gelişme resmi kayıtlara intikal etmiştir, ancak bu gelişmenin içeriği belirtilmemiştir [K1].

TEİAŞ bağlantı görüşü süreci değerlendirme aşamasındadır. Komisyon incelemesi sonucunda projenin uygunluk durumu tespit edilecek, eksik bilgi veya belge tespit edilirse TEİAŞ bildirimi üzerine revizyonlar yapılacak ve sürecin sonunda nihai bağlantı görüşünün resmi olarak yayımlanması beklenmektedir [K74].

MSB ile askeri yasak bölgeler konusunda ön görüş alınması gerekmektedir. Proje sahasının coğrafi konumu ve stratejik durumu, makamların değerlendirmesini gerektirmektedir [K3].

Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu, belgede önerilen şu adımları içermektedir: mevzuat değişikliklerinin yakından takip edilmesi, tedarik zinciri planlamasının bu doğrultuda revize edilmesi, finansman ve ortaklık yapıları için MNO Teknik Danışmanlık Ltd. ile müzakerelerin hızlandırılması, uzun vadeli bakım ve işletme stratejilerinin erken safhada kurgulanması, Çevresel Etki Değerlendirme süreçlerinin eksiksiz tamamlanması ve yerel paydaş ilişkilerinin şeffaf yürütülmesi [K12].
```

**Kaynaklar:** ['Askeri Yasak Bölgeler Ön Görüş Talebi', 'Kızılova RES Bağlantı Görüşü Başvurusu', 'Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu', 'ÇED Süreci Durum Yazısı']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: list), kaynak kuralı=set, küme=['ÇED Süreci Durum Yazısı'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı (liste); ÇED, TEİAŞ, MSB adımları doğru; ledger'daki imar/kat'i proje/yapı ruhsatı eksik — kısmi

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-MIX-002 (mixed, kullanıcı `enerji`, MIXED_QUERY)

**Soru:** Karatepe RES'te Temmuz 2024'te üretim kaybına yol açan olay neydi ve bu dönemin (Q3 2024) bütçe sapması ne kadardı?
**Beklenen:** cevap var; ledger: project.operations.budget_vs_actual[3] = {'period': 'Q3_2024', 'budget': {'value': 26000000, 'currency': 'TRY', 'tag': 'USER_FACT'}, 'actual': {'value': 25106000, 'currency': 'TRY', 'tag': 'USER_FACT'}, 'tag': 'USER_FACT'}; beklenen kaynak ['Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', 'Budget vs Actual 2026']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Belgelere göre:
Temmuz 2024'te Karatepe RES'te yaşanan olay Türbin T-07 arızasıdır [K41]. Bakım raporuna göre rutin operasyonlar sırasında tesiste plan dışı bir duruş kaydedilmiş, ilk incelemede arızanın Türbin dişli kutusu arızası (T-07) olduğu ve 11 gün duruşa yol açtığı tespit edilmiştir [K49]. Arıza, rapor döneminde 12553 MWh üretim kaybına yol açmış ve tesisin genel verimlilik oranı olan %91,4 metriği üzerinde geçici bir düşüş gözlemlenmiştir [K75].

Excel verisine göre:
Karatepe RES için Q3 2024 (Temmuz–Eylül 2024) döneminde bütçe sapması -894.000 TL'dir.
```

**Kaynaklar:** ['Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', 'Budget vs Actual 2026']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: dict), kaynak kuralı=set, küme=['Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', 'Budget vs Actual 2026'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı (dict); Excel sapması −894.000 TL aritmetik doğru; belge kısmındaki 12553 MWh / %91,4 MIXED olduğu için G1 dışı — kontrolör bakmalı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## ANK-MIX-003 (mixed, kullanıcı `enerji`, MIXED_QUERY)

**Soru:** Karatepe RES Q1 2025 bütçe sapması neydi ve sebebi belgelerde yazıyor mu?
**Beklenen:** cevap var; ledger: project.operations.budget_vs_actual[5] = {'period': 'Q1_2025', 'budget': {'value': 34500000, 'currency': 'TRY', 'tag': 'USER_FACT'}, 'actual': {'value': 34871000, 'currency': 'TRY', 'tag': 'USER_FACT'}, 'tag': 'USER_FACT'}; beklenen kaynak ['Budget vs Actual 2026']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Karatepe RES'in 2025 1. çeyrek bütçe sapması 371.000 TL'dir.
```

**Kaynaklar:** ['Budget vs Actual 2026']
**Puan:** önce ✅ → sonra ✅ · value=skipped (unformattable expected_answer type: dict), kaynak kuralı=set, küme=['Budget vs Actual 2026'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** değer kontrolü atlandı (dict); 371.000 TL aritmetik doğru (34.871.000 − 34.500.000)

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-001 (discovery, kullanıcı `finans`, DATA_QUERY)

**Soru:** Karatepe'nin finansal modeli var mı?
**Beklenen:** cevap var; ledger: —; beklenen kaynak ['Financial Model 2026']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Karatepe'nin finansal modeli mevcut; değer 13600000 olarak hesaplandı.
```

**Kaynaklar:** ['Financial Model 2026']
**Puan:** önce ✅ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=['Financial Model 2026'], güvenlik=pass, F-8=fail
**Sınıf / okuma:** discovery; DATA yolu '13600000' gruplanmamış (F-8 ❌, puana girmiyor); 'var mı' sorusuna hesap döndürdü

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-003 (discovery, kullanıcı `enerji`, DOCUMENT_QUERY)

**Soru:** Sigorta ne zaman bitiyor?
**Beklenen:** cevap var; ledger: —; beklenen kaynak ['Sigorta Yenileme Bildirimi — İşletme Dönemi']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Yenileme bildirimine göre sigorta sona erdi. Belgedeki satır:
Süre: 09.01.2025 tarihinde sona erdi (1 yıl 9 ay önce) [K3]

Bu belge "YÜRÜRLÜKTE DEĞİL" olarak işaretlidir [K3]. Güncel poliçe özetinde (DOC-ANK-EPC-007) bitiş tarihi yazmamaktadır; yalnızca yürürlük tarihi 05.01.2022 olarak belirtilmiştir [K2].
```

**Kaynaklar:** ['Karatepe RES Construction All Risks Insurance Policy Summary', 'Sigorta Yenileme Bildirimi — İşletme Dönemi']
**Puan:** önce ✅ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=['Sigorta Yenileme Bildirimi — İşletme Dönemi'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** discovery; 'sona erdi' cevabı — beklenen belge gösterildi; değer doğrulanmadı

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

## GEN-DSC-012 (discovery, kullanıcı `yonetim`, DOCUMENT_QUERY)

**Soru:** peki amendment var mı hiç?
**Beklenen:** cevap var; ledger: —; beklenen kaynak ['Facility Agreement Amendment 01']; yasak ['Kızılova RES']

**Cevap (aynen):**

```
Evet, kaynaklarda üç tadil belgesi geçiyor:

1. Facility Agreement Amendment 02 (Belge No DOC-ANK-FIN-006, versiyon AMD02, durum executed, yürürlük tarihi 15.03.2025, taraflar Karatepe RES Enerji Üretim A.Ş. ve Garanti BBVA) güncel belgedir ve "Facility Agreement Amendment 01" belgesini değiştirir [K1]. Bu belge finansal kovenantları değiştirmektedir [K5].

2. Licence Amendment 01 (Kapasite Tadili) (Belge No DOC-ANK-DEV-002, versiyon AMD01, belge tarihi 10.02.2021, durum yürürlükte, taraflar Karatepe RES Enerji Üretim A.Ş. ve EPDK) [K2]. Bu tadil ile proje kapasitesi 21 MW'dan 24 MW'a güncellenmiş, türbin sayısı 7'den 8'e çıkarılmıştır [K4].

3. Facility Agreement Amendment 01 (Belge No DOC-ANK-FIN-005, versiyon AMD01, belge tarihi 12.01.2024, durum superseded) [K7]. Bu belge "Facility Agreement Amendment 02" tarafından değiştirilmiştir [K7].
```

**Kaynaklar:** ['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Licence Amendment 01 (Kapasite Tadili)']
**Puan:** önce ✅ → sonra ✅ · value=skipped (expect_no_answer), kaynak kuralı=n/a, küme=['Facility Agreement Amendment 01'], güvenlik=pass, F-8=pass
**Sınıf / okuma:** discovery; üç tadil sayıyor (Licence Amendment dahil) — beklenen belge gösterildi

**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: 

