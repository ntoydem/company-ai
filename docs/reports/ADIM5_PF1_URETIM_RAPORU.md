# ADIM 5 — PF-1 Düzeltme Üretim Raporu (11.10.2026)

Tansu'nun PF-1'in 3 LLM belgesinde bulduğu anlam hatalarının düzeltilmesi (+ Karatepe
DOC-ANK-DEV-002'nin kapasite/türbin anlatısı). Canlı DB yok, main'e merge yok, bayraklar
kapalı (`EMBEDDINGS_ENABLED=false`). Her adım ayrı commit.

## 0. Loop durumu

`ScheduleWakeup(stop:true)` çağrıldı (önceki görevde) — 1 bekleyen wakeup iptal edildi.
`CronList` boş (`No scheduled jobs.`), bu görevin başında ve sonunda tekrar doğrulandı.
"Resuming /loop wakeup" mesajı görülmedi.

## 1. Commit'ler (sırayla)

| # | Commit | İçerik |
|---|---|---|
| 1 | `8cddf87` | Şema/ledger/facts/spec hazırlığı (4 belge, 0 LLM) |
| 2 | `7069eb5` | Düzeltme 1/4 — Kızılova FA taahhüt komisyonu oranı |
| 3 | `1a3c0bb` | Düzeltme 2/4 — Yeşilova FA recital ayrımı BAŞARISIZ (kota), başlıklar geri alındı |
| 4 | `18117a1` | Düzeltme 2b/4 — Yeşilova FA prose, KISMİ düzeltme |
| 5 | `21f2c37` | Düzeltme 3/4 — Yeşilova Annex F `effective_date` token kaldırıldı |
| 6 | `6fea4e8` | Düzeltme 4/4 — Karatepe DOC-ANK-DEV-002 kapasite/türbin anlatısı |
| 7 | `87953ae` | Hukuk planı SORU cevapları (§11, "Naci cevapları") |
| 8 | `4cb9a59` | `docs/SORULAR_NACIDEN_4-2026-10-11.md` kopyası (company-ai) |

Tümü `feat/adim5-veri-kutuphanesi`'e push edildi.

## 2. Özet tablo — 4 belge

| Belge | Durum | LLM çağrısı (başarılı/toplam) | Retry |
|---|---|---|---|
| DOC-IZM-FIN-004 (Kızılova FA) | ✅ Düzeltildi | 1/1 | 0 |
| DOC-YSV-FIN-009 (Yeşilova FA) | ⚠️ KISMİ — bkz. §4 | 1/4 (3 başarısız 429, "no attempt made") | 1 (izinli hak kullanıldı, tükendi) |
| DOC-YSV-FIN-010 (Yeşilova Annex F) | ✅ Düzeltildi | 1/1 | 0 |
| DOC-ANK-DEV-002 (Karatepe kapasite) | ✅ Düzeltildi | 1/1 | 0 |

**Toplam LLM çağrısı bu görevde:** 4 başarılı + 3 başarısız (rate-limit, içerik reddi değil) = 7
invocation; başarısız 3 invocation'ın her biri kendi içinde `MAX_ATTEMPTS=3` iç deneme yaptı
(üçü de 429), yani Gemini API'ye toplam ham istek sayısı muhtemelen 4 (başarılı) + 9 (başarısız iç
denemeler) = ~13'tür. Önceki rapor bu günün kota kullanımını 3/500 olarak bildirmişti; bu görev
sonunda **7/500 başarılı çağrı** (kümülatif), 429 yanıtlarının kotaya ayrıca sayılıp
sayılmadığı doğrulanamadı (Google tarafı davranışı belgelenmemiş).

**Süre:** Hazırlık + 3 başarılı çağrı (Issue 1,3,4) ~3 dk (13s aralıklarla). DOC-YSV-FIN-009'un
tek izinli retry'si için 3 ayrı deneme ve aralarında kademeli bekleme (ilk deneme hemen, sonra
~90s, sonra ~180s, sonra ~300s) — toplam ~10 dk, hepsi 429 ile sonuçlandı. Üretim fazının toplam
süresi (groundwork commit'ten son başarılı commit'e) ~33 dk.

## 3. DOC-IZM-FIN-004 — Kızılova Facility Agreement (DÜZELTİLDİ)

**Değişiklik:** `commitment_fee_rate` yeni bir token oldu (ledger: `SignedUndrawnFacility.commitment_fee_rate`,
değer %0,80, `tag: USER_FACT`, not: "ÜRÜN SAHİBİ ONAYLI/kaynak: NACI_CEVAP §3.2, 30.000.000 x oran x 92/360 = 61.333").
Prose artık oranı, tutarı ve ödeme tarihini 3 ayrı cümlede anlatıyor.

**Render edilmiş metin (TAM, PDF'ten çıkarıldı):**

> ### 1. Definitions and Interpretation
> This facility agreement, bearing document reference DOC-IZM-FIN-004 and titled Kızılova RES
> İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ), is entered into as of October 5, 2026 and
> becomes effective on October 5, 2026. It establishes the core financial terms and obligations
> between the entities listed under Kızılova RES Enerji Üretim A.Ş., PQR Bank, including Kızılova
> RES Enerji Üretim A.Ş. and PQR Bank.
> The agreement governs the overall framework for Kızılova RES with current status designated
> as Executed. All terms and interpretation principles set forth in this text shall be applied in
> accordance with document version EXECUTED.
>
> ### 2. The Facility
> Under the terms of this agreement, the lenders make available to Kızılova RES Enerji Üretim A.Ş.
> a facility in an aggregate limit of 30,000,000 USD. The facility is established exclusively to
> support the financing objectives of Kızılova RES.
> The financial commitments supplied by PQR Bank and the participants under Kızılova RES Enerji
> Üretim A.Ş., PQR Bank shall be utilized solely for permitted corporate purposes. The allocation
> and administration of funds remain governed by document reference DOC-IZM-FIN-004.
>
> ### 3. Conditions Precedent to Drawdown
> The right of Kızılova RES Enerji Üretim A.Ş. to issue a utilization request is subject to the
> prior satisfaction of all prerequisite conditions. A primary requirement for any disbursement is
> the full satisfaction of Üretim lisansının alınması.
> Upon verification that all conditions precedent have been met to the satisfaction of PQR Bank,
> funds may be drawn. Failure to satisfy these requirements may prevent utilization under version
> EXECUTED.
>
> ### 4. Commitment Fee
> **The borrower shall pay a commitment fee calculated by applying 0.8% to the unutilized portion
> of the commitments. The resulting fee amount is set as 61,333 USD.**
> The commitment fee shall accrue starting from October 5, 2026 and shall be payable on January 5,
> 2027. Payments shall be processed by Kızılova RES Enerji Üretim A.Ş. to the designated accounts
> of PQR Bank.
>
> ### 5. Governing Law
> This agreement, identified as DOC-IZM-FIN-004, and any non-contractual obligations arising out
> of it shall be governed by applicable legal standards. The relationship between Kızılova RES
> Enerji Üretim A.Ş. and PQR Bank shall be interpreted under these governing principles.
> The entities named in Kızılova RES Enerji Üretim A.Ş., PQR Bank agree that any dispute arising
> under Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ) shall be referred to the
> competent judicial forums. This clause remains effective for all matters concerning document
> version EXECUTED and status Executed.

**Doğrulama:** Oran % olarak (`0.8%`), tutar USD olarak (`61,333 USD`) doğru biçimlendi —
istenen format tam karşılanıyor. İcat edilmiş somut hüküm yok (cezasız erken ödeme / belirli cure
süresi / belirli yetkili mahkeme / belirli faiz hesap yöntemi — hiçbiri metinde yok, hepsi genel
ifadeyle bırakılmış).

**Kapılar:** lint ✅, validate-ledger ✅, validate-documents (full) ✅, token-grep (prose'ta
`[[token]]` dışı 2+ hane yok) ✅, G1-G3 ✅ (bkz. §6).

## 4. DOC-YSV-FIN-009 — Yeşilova Facility Agreement (KISMİ DÜZELTME — AÇIK İŞ)

**Hedef:** capex/equity yalnız BİR recital cümlesinde geçsin; "kredi capex'i finanse eder" /
"çekim özkaynak katkısına bağlıdır" ilişkileri kurulmasın.

**1. üretim (`9c9fc3c`'teki orijinal, bu görevde DÜZELTİLEN versiyon) neydi:**
- "This credit facility is dedicated exclusively to funding eligible capital expenditure
  requirements designated under [[capex]]" — **yasak ilişki** (kredi capex'i finanse eder).
- "The obligation of the borrower to draw upon the facility is contingent upon the contribution
  of required sponsor equity" — **yasak ilişki** (çekim özkaynağa bağlı).
- "Early prepayments shall be processed... without penalty" — **icat edilmiş somut hüküm**
  (kaynakta yok).

**Bu görevdeki 1. deneme (headings güçlendirilmeden, `7069eb5`'ten önce üretilen ilk sürüm,
şimdi commit `18117a1`'de kayıtlı) bu üç sorunu da ortadan kaldırdı** ama YENİ bir sorun
yarattı: capex/equity artık "2. The Facility" bölümünde, "1. Recitals" bölümünde değil.

**Render edilmiş metin (TAM, mevcut/commit'li sürüm):**

> ### 1. Recitals and Definitions
> İşbu tesis sözleşmesi, June 3, 2023 tarihinde Yeşilova RES Enerji Üretim A.Ş., LMN Bank
> arasında akdedilmiştir. Belge, Yeşilova RES Facility Agreement (2023-YS) başlığını taşımakta
> olup DOC-YSV-FIN-009 referans numarası ve EXECUTED sürümü ile kayıt altına alınmıştır.
> Sözleşmenin borçlu tarafı olan Yeşilova RES Enerji Üretim A.Ş., projenin yürütülmesinden
> sorumlu özel amaçlı şirkettir. Finansman sağlayan taraf olarak LMN Bank belirlenmiş olup işbu
> belge Executed statüsündedir.
> İlgili finansal yapının yürürlük tarihi June 3, 2023 olarak kabul edilmiştir. Sözleşme
> kapsamındaki temel kavramlar ve taraf yükümlülükleri takip eden maddelerde düzenlenen
> esaslara tabidir.
>
> ### 2. The Facility (Supplementary Financing)
> Sağlanan ek finansman imkanı, Yeşilova RES kapsamında ihtiyaç duyulan yatırımların
> desteklenmesini amaçlamaktadır. Kredi tesisi çerçevesinde tahsis edilen toplam borç tutarı
> 2,352,000 USD olarak belirlenmiştir.
> **Projenin toplam sermaye harcaması 26,400,000 USD tutarında öngörülmektedir. Söz konusu
> harcamaların finansmanı amacıyla taahhüt edilen özkaynak katkısı 24,048,000 USD
> seviyesindedir.**
> Kredi kullanımında uygulanacak marj oranı 1.5% olarak uygulanacaktır. Kullanım şartları ve ek
> finansman tahsis esasları genel kredi koşullarına göre yürütülecektir.

Kalın kısım hâlâ istenen sınırı ihlal ediyor: capex/equity "The Facility" bölümünde, "Recitals"ta
değil (yapısal hata), ve "harcamaların finansmanı amacıyla taahhüt edilen özkaynak" ifadesi
equity'nin capex'i finanse ettiğini söylüyor — bu YASAKLANAN "kredi capex'i finanse eder"
ifadesinden farklı (burada equity'den bahsediyor, krediden değil) ama yine de capex/equity
ilişkisini The Facility bölümüne taşıyarak istenen ayrımı bozuyor.

**Tek izinli yeniden deneme (headings güçlendirildi — bkz. `1a3c0bb`'nin diff'i):**
`section_headings_en` şu şekilde değiştirildi: `"1. Recitals (Project Capex and Equity
Background)"`, `"2. The Facility (Supplementary Financing, Unrelated to Capex)"`. Üç ayrı
`generate_prose.py --only DOC-YSV-FIN-009 --force` çağrısı denendi (hemen, ~90s sonra, ~180s
sonra, ~300s sonra bekleyerek) — **üçü de** Gemini'den sürekli `429` aldı, iç `MAX_ATTEMPTS=3`
döngüsü de tükendi, `errors: ["no attempt made"]` ile sonuçlandı (bu bir **içerik reddi değil**,
LLM hiç yanıt veremedi).

**Karar:** "yine kırmızıysa dur, prose'u elle düzeltme" kuralı uygulandı. Başlıklar, commit'li
(düzeltilmiş-ama-tam-değil) prose ile eşleşmesi için eski haline (`"1. Recitals and
Definitions"` / `"2. The Facility (Supplementary Financing)"`) döndürüldü — bu sayede repo
validator'ları (lint/validate-documents) geçer durumda, ama **Tansu'nun istediği yapısal
ayrım hâlâ tam karşılanmıyor**. Açık iş: kota uygun olduğunda `DOC-YSV-FIN-009`'u tekrar
`--force` ile üretmek (gerekirse headings'i üçüncü kez ayarlayarak).

**Kapılar (mevcut sürüm için):** lint ✅, validate-ledger ✅, validate-documents (full) ✅,
token-grep ✅ (prose'ta yalnız `[[token]]` içinde sayı var), G1-G3 ✅ — **ancak bunlar yapısal/
biçimsel kapılar, Tansu'nun semantik isteğini doğrulamaz** (otomatik tarayıcı bu tür bir anlam
hatasını yakalayamıyor, bu nedenle manuel inceleme ile bulundu).

## 5. DOC-YSV-FIN-010 — Yeşilova Annex F Raporu (DÜZELTİLDİ)

**Değişiklik:** `generate_prose.py`'ye eklenen `suppressed_placeholders` mekanizması, belgenin
`effective_date`'i yoksa (`doc.get("effective_date") is None`) bu token'ı LLM'e hiç önermiyor.

**Render edilmiş metin (TAM, PDF'ten çıkarıldı):**

> ### 1. Purpose and Scope
> This document sets out the annual Annex F reporting requirements for Yeşilova RES as managed
> by Yeşilova RES Enerji Üretim A.Ş.. It provides a formal evaluation of the financial standing
> and covenant compliance for the period ending in 2025. The information presented is prepared
> for review by LMN Bank and the broader group outlined in Yeşilova RES Enerji Üretim A.Ş., LMN
> Bank.
> The scope of this submission encompasses all relevant financial records and covenant
> calculations governed by reference document DOC-YSV-FIN-010. Released under version 2025 on
> October 1, 2026, this report reflects an official status of Draft. The primary objective
> remains ensuring total operational transparency and fulfillment of technical reporting
> covenants.
>
> ### 2. Compliance Summary
> Throughout the relevant monitoring timeframe, Yeşilova RES Enerji Üretim A.Ş. tracked core
> financial indicators to ensure full alignment with project finance documents for Yeşilova RES.
> The calculations established a historic debt service coverage ratio of 3.60x, taking into
> account total interest payments of 104,500 USD made during the reporting year. These
> operational figures confirm the stable financial posture of the project.
> Following the thorough review of operational obligations, the formal outcome is recorded as
> pass. All necessary disclosures have been delivered to LMN Bank in compliance with established
> monitoring procedures. Ongoing operational updates will continue to be shared across the
> finance parties referenced in Yeşilova RES Enerji Üretim A.Ş., LMN Bank.
>
> ### 3. Covenant Test History (tablo, kod ile üretildi, LLM değil)
> | Period | DSCR | Result |
> |---|---|---|
> | Q4_2024 | 3.90x | Pass |
> | Q4_2025 | 3.60x | Pass |

Üst bilgi bloğunda "Effective Date: effective date not yet set" hâlâ görünüyor (bu token/facts
seviyesinde, LLM'in yazdığı bir yer değil — belge PDF şablonunun sabit üst-bilgi tablosu);
gövde metninde `[[effective_date]]` artık hiç kullanılmıyor.

**Doğrulama:** Yalnız 2025 verisi (DSCR 3,6x, 2025 faiz toplamı 104.500 USD); taksit #11/2026
olayına hiçbir atıf yok. Yasak değer taraması tekrarlandı — `18.240`, `18.912`, `taksit #?11`,
`11. taksit`, `#11`, `2026` deseni için grep: **temiz** (yalnız üst bilgideki `document_date:
October 1, 2026` facts-seviyesi token çıktısı var, bu yasaklı değil — döküm tarihi 2026, demo_today
15.09.2026'ya göre tutarlı, "olay" değil).

**Kapılar:** lint ✅, validate-ledger ✅, validate-documents (full) ✅, token-grep ✅, G1-G3 ✅.

## 6. DOC-ANK-DEV-002 — Karatepe Lisans Tadili (DÜZELTİLDİ)

**Ön kontrol:** `prose/DOC-ANK-DEV-002.yaml` içinde `hand_edited:` anahtarı YOK — regenerate
serbestti.

**Değişiklik:** Yeni token'lar — `capacity_mw_initial`, `turbine_count`, `turbine_count_initial`
(ledger: `Turbines.count_initial`, değer 7, `tag: USER_FACT`, kaynak: DOC-ANK-DEV-001; Tansu'nun
T-11.1 onayı). Bölüm başlığı "Güncellenen Kapasite Bilgisi" → "Kapasite ve Türbin Sayısı
Değişikliği" olarak genişletildi (ilk/güncel değerleri birlikte anlatması için).

**Render edilmiş metin (TAM, PDF'ten çıkarıldı):**

> ### Tadil Gerekçesi
> Karatepe RES projesi kapsamında Karatepe RES Enerji Üretim A.Ş. tarafından yürütülen lisans
> süreçlerinde güncelleme ihtiyacı doğmuştur. Karatepe RES Enerji Üretim A.Ş. ile Karatepe RES
> Enerji Üretim A.Ş. arasında mutabık kalınan teknik değerlendirmeler sonucunda mevcut
> kapasitenin revize edilmesi uygun görülmüştür.
> Saha koşulları ve güncel teknik değerlendirmeler ışığında projenin verimliliğini artırmak
> amacıyla işbu DOC-ANK-DEV-002 numaralı belgenin hazırlanması gerekmiştir. Yapılan düzenlemeler
> ilgili mevzuata ve tarafların ortak kararlarına uygun şekilde tasarlanmıştır.
>
> ### Kapasite ve Türbin Sayısı Değişikliği
> **Proje başlangıcında 21 MW olan toplam kurulu güç kapasitesi, gerçekleştirilen tadil
> sonrasında 24 MW seviyesine güncellenmiştir. Bu kapsamda başlangıçta planlanan 7 adet türbin
> sayısı da 8 adet olarak yeniden düzenlenmiştir.**
> Yapılan teknik güncellemeler, projenin genel işletme düzenine ve ilgili lisans şartlarına
> entegre edilmiştir. Belirtilen parametre değişiklikleri Licence Amendment 01 (Kapasite Tadili)
> düzenlemesi altında kayıt altına alınarak AMD01 sürümü ile geçerlik kazanmıştır.
>
> ### Yürürlük
> İşbu lisans tadil metni 10.02.2021 tarihinde düzenlenmiş olup 10.02.2021 itibarıyla yürürlüğe
> girecektir. Belge 10.02.2021 tarihi itibarıyla imzalanarak taraflar arasında hukuki geçerlilik
> kazanmıştır.
> Metin, genel sözleşme hükümleri çerçevesinde Yürürlükte statüsünde yürürlükte kalacak ve
> tarafların hak ile yükümlülüklerini belirlemeye devam edecektir. Önceki lisans koşullarının bu
> tadil ile çelişen hükümleri yürürlükten kaldırılmıştır.

**Not (önceden bilinen, bu görevde yeniden doğrulanmadı):** "Tadil Gerekçesi" bölümünde
`[[spv_name]]` ve `[[counterparty]]` ikisi de Karatepe SPV'sine çözülüyor ("Karatepe RES Enerji
Üretim A.Ş. ile Karatepe RES Enerji Üretim A.Ş. arasında") — bu facts.py'nin bu belge türü için
`counterparty`'yi SPV'nin kendisine eşlemesinden kaynaklanan, PF-1 öncesi var olan bir kusur,
bu görevin kapsamı dışında (Tansu'nun bu konuda bir T-11/bu-tur talebi yok).

**Doğrulama:** İlk kapasite (21 MW/7 türbin) ve güncel kapasite (24 MW/8 türbin) ikisi de tek
cümlede, açıkça "başlangıç→güncel" ilişkisiyle anlatılıyor.

**Kapılar:** lint ✅, validate-ledger ✅, validate-documents (full) ✅, token-grep ✅, G1-G3 ✅.

## 7. G1-G3 ve diğer gate sonuçları (ortak, 4 belge + tüm 84 belge)

| Gate | Komut | Sonuç |
|---|---|---|
| ruff + mypy (backend), ruff (ocr-worker) | `make lint` (ilk 2 adım) | ✅ |
| validate-ledger | `make lint` (3. adım) / `python -m seed_data.generator.validate_ledger` | ✅ 0 hata/uyarı |
| validate-documents --prose-only | `make lint` (4. adım) | ✅ 0 hata/uyarı |
| validate-excel | `make lint` (5. adım) | ✅ 0 hata |
| generate_documents (tüm 84 belge, LLM yok) | `python -m seed_data.generator.generate_documents` | ✅ hatasız, `manifest.json` (84 belge) |
| validate-documents (full) | `python -m seed_data.generator.validate_documents` | ✅ 0 hata/uyarı |
| token-grep (4 prose dosyası, `[[token]]` dışı 2+ hane) | özel grep (bu rapor için) | ✅ temiz (4/4) |
| Yasak değer taraması (DOC-YSV-FIN-010) | grep (18.240/18.912/taksit #11/2026-olay) | ✅ temiz |

**G1-G3** etiketleri bu projede ayrı adlandırılmış bir kontrol listesi değil — yukarıdaki
lint/validate-ledger/validate-documents/validate-excel dörtlüsü aynı `make lint` hedefinin
sırayla çalışan adımları; hepsi tek komutla doğrulandı (son çalıştırma: tüm adımlar ✅).

## 8. `make test`

Solo çalıştırıldı (aynı test DB'sinde ikinci bir koşu başlatılmadı), exit code 0:

- Backend: **622 passed, 15 deselected** (deselected = `live_llm` marker'lı canlı-LLM testleri,
  varsayılan olarak hariç — `make test-llm` ile ayrı çalıştırılır), 787.09s (13:07).
- `assert-pipeline-schema`: `pipeline schema present` — `document_chunks`, `document_pages`,
  `documents`, `ingestion_jobs` tabloları doğrulandı.
- ocr-worker: **18 passed**, 7.03s.
- Toplam: **640 passed, 0 failed**.
