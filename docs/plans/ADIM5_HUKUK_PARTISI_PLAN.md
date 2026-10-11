# Adım 5 — Hukuk Partisi Planı

**Tarih:** 11.10.2026 · **Durum:** plan, **ledger/belge değiştirilmedi** · **Dayanak:** `NACI_CEVAP_2026-10-08.md` §"Hukuk" (AI-BalBal PR #13) + `docs/plans/ADIM5_PLAN.md` §1.2/§1.3/§4 (Hukuk satırı) · **Dal:** `feat/adim5-veri-kutuphanesi` · **Sıra:** PF'den sonraki parti (parti sırası: PF → **Hukuk** → Enerji → Mali İşler → İdari İşler → İK).

Tansu'nun verdiği 5 dava: Karatepe (kamulaştırma/irtifak), Yeşilova (tazminat/arazi tahsis), Boztepe (imar iptali, Ankara 2. İdare, duruşma 28.10.2026), Kızılova (yüklenici ihtilafı, ihtarname aşaması), Demirci (TEA olumsuz görüşüne itiraz). Akyar ve Güneşalan'da dava **yok** — bu iki proje Hukuk partisinden hiçbir belge almayacak.

---

## 1. Belge listesi (SPV bazında)

### Karatepe — Kamulaştırma ve İrtifak Bedeli Tespiti
| Belge | Üretim |
|---|---|
| Dava dilekçesi | LLM |
| Duruşma tutanağı / bilirkişi raporu (bedel tespiti) | LLM |
| Legal Review Memo (ek, dava özelinde) | LLM |

Zaten var: 2 Legal Review Memo (`DOC-ANK-LEG-001/002`, genel — araziden/sözleşme uyumundan, kamulaştırma davasına özel değil).

### Yeşilova — Tazminat (Arazi Tahsis)
| Belge | Üretim |
|---|---|
| Dava dilekçesi | LLM |
| Duruşma tutanağı / mahkeme kararı (sonuçlanmadıysa: **missing_document**, henüz yok) | LLM |
| Legal Review Memo (yeni, Yeşilova'nın ilk hukuk belgesi) | LLM |

### Boztepe — İmar İptali
| Belge | Üretim |
|---|---|
| Dava dilekçesi | LLM |
| Duruşma celp/tebliğ belgesi (28.10.2026) | kodla (form, sabit yapı) |
| Legal Review Memo (yeni, Boztepe'nin ilk hukuk belgesi) | LLM |

### Kızılova — Yüklenici İhtilafı (İhtarname Aşaması)
| Belge | Üretim |
|---|---|
| İhtarname (ABC İnşaat A.Ş.'ye) | kodla (resmi, kısa, sabit yapı) |
| Hukuki görüş notu | LLM |

**Not:** "ihtarname aşaması" — henüz dava açılmamış. Dava dilekçesi **üretilmez** (missing_document, kasıtlı — bir ihtilaf her zaman davaya dönüşmez, bu aşamada doğru olan budur).

### Demirci — TEA Olumsuz Görüşüne İtiraz
| Belge | Üretim |
|---|---|
| TEA'nın olumsuz görüş yazısı | kodla (resmi kurum yazısı, sabit yapı) |
| İtiraz dilekçesi | LLM |
| Legal Review Memo (yeni, Demirci'nin ilk hukuk belgesi) | LLM |

### Matris-güdümlü ek: Legal Review Memo genişletmesi
`Legal Review Memo` zaten Karatepe (2) + Kızılova (2) ile ≥2 proje şartını karşılıyor; yukarıdaki yeni Yeşilova/Boztepe/Demirci eklemeleriyle **4 projeye** çıkıyor.

---

## 2. Tuzak türü etiketleri

NACI_CEVAP'ın "Kasıtlı tuzaklar" listesindeki hiçbir kalem **Hukuk departmanına ait değil** (hepsi fatura/PO/personel-belge türünde, Mali İşler/İdari İşler kapsamında) — Hukuk partisinin kendi tuzakları bu listede yok, aşağıdakiler yapısal olarak ortaya çıkan türler:

| Tuzak | Tür | Nerede |
|---|---|---|
| Kızılova'da dava dilekçesi yok (henüz ihtarname aşaması) | **missing_document** | Bilinçli — her ihtilaf davaya dönüşmez |
| Yeşilova/Karatepe davalarının duruşma/karar belgesi (sonuçlanmadıysa) | **missing_document** | Tansu'nun cevabına bağlı (T-12.1/T-12.2) |
| Dava dilekçesi taslak → sunulan sürümü (varsa) | **version_difference** | supersedes/version zinciri, conflict_group YOK (PF'deki Yeşilova ödeme planı deseniyle aynı) |
| Aynı duruşmanın iki bildirim kopyası (varsa) | **duplicate** | Tansu'nun cevabına bağlı, bu round'da modellenmedi |

Hiçbir **genuine_conflict** kalemi şu an bilinmiyor — NACI_CEVAP'ta Hukuk'a özel bir "iki kaynak farklı sayı söylüyor" tuzağı yok.

---

## 3. key_facts kaynakları

Mevcut Legal Review Memo deseni (`key_facts: {}`, yalnız `parties`/`related` ile bağlanan saf anlatı belgesi) yeni belgelerin çoğu için de geçerli — dava dilekçesi/duruşma tutanağı gibi belgelerin **sayısal bir facts'i yok** (tutar/tarih varsa T-12 tablosundan gelecek). Yalnız sayısal veri taşıyan belgeler:
- Boztepe duruşma belgesi: `hearing_date` (28.10.2026, Tansu'dan zaten var — yeni bir alan, `Finance`'e değil `Development`/ayrı bir `LegalCase` şekline).
- Demirci TEA yazısı: `tea_opinion_date`, varsa ret gerekçesi (metin).
- Karatepe/Yeşilova'nın bedel/tazminat tutarları: T-12.1/T-12.2 cevaplanırsa.

---

## 4. T-12. Tansu'dan gelmesi gereken eksik değerler

| Kod | Proje | Eksik değer | Şu anki varsayım | Cevap |
|---|---|---|---|---|
| T-12.1 | Karatepe | Kamulaştırma davası: mahkeme adı, dava no, duruşma/karar tarihi, talep/belirlenen bedel | Hiç yok | |
| T-12.2 | Yeşilova | Tazminat davası: mahkeme adı, dava no, duruşma/karar tarihi, talep edilen tutar | Hiç yok | |
| T-12.3 | Boztepe | İmar iptali davası: dava no, talep edilen sonuç/gerekçe (mahkeme + duruşma tarihi zaten verildi: Ankara 2. İdare, 28.10.2026) | Hiç yok | |
| T-12.4 | Kızılova | Yüklenici ihtilafı: ihtarname tarihi, ihtilafın konusu/tutarı, taraf (ABC İnşaat mı?) | Hiç yok | |
| T-12.5 | Demirci | TEA itirazı: TEA'nın olumsuz görüş tarihi, itiraz tarihi, mercii, gerekçe | Hiç yok | |
| T-12.6 | Boztepe | Kredi (2024-BZ) imza günü | **AI_ASSUMPTION**: 2024-05-02 (Naci, 11.10.2026 — ödeme günleri ayın 1'i/2'si ile uyumlu, "ilk 3 yıl yalnız faiz" Mayıs 2027'de bitecek şekilde seçildi; zaten ledger'a işlendi) | |

---

## 5. Şema ihtiyacı

- **Yeni department yok** — `hukuk` zaten `DepartmentSlug`'da (PF/İK'nın aksine).
- **Yeni, küçük bir `LegalCase`-şekilli yapı önerilir** (Optional, her SPV için): `case_court: Fact | None`, `case_number: Fact | None`, `hearing_date: date | None`, `claimed_amount: Money | None`, `status: Fact | None` — T-12 cevapları geldiğinde doldurulacak; şimdi eklemek cevaplar gelmeden anlamsız (icat riskini önlemek için **cevaplar gelince** eklenmesi önerilir, bu plan turunda eklenmedi).
- `GuaranteeLetter`/`AnnualInterestPaid` gibi önceki T-11 turlarında kurulan "proje-genel küçük Optional alan" deseni burada da geçerli.

---

## 6. LLM çağrı sayısı ve kota

~9-10 LLM belgesi (dava dilekçeleri ×4-5, duruşma/karar belgeleri ×2-3 — sonuçlanmışsa, Legal Review Memo ×3 yeni, itiraz dilekçesi ×1) + ~3 kodla belge (ihtarname, Boztepe duruşma tebliği, TEA yazısı). `MAX_ATTEMPTS=3`, gözlenen ret oranı bu PF-1 turunda **%0** (3/3 belge ilk denemede kabul edildi) — kabaca **~10-12 LLM çağrısı** bekleniyor, `CALL_SPACING_S=13` ile toplam bekleme ~2 dakikanın altında. Gemini free-tier günlük 500 limitinin çok altında, tek oturumda biter.

---

## 7. Doğrulama kapıları

Aynı desen: `make lint` → `make validate-ledger` → `generate_prose.py --only <doc-id>` (sırayla, her belge sonrası prose'daki her sayı/tarihin `[[token]]` içinde olduğu grep'le kontrol edilir) → `make validate-documents` (full, G1-G6) → her kasıtlı tuzağın (missing_document'lar dahil) doğru temsil edildiğinin kontrolü → `make test` (tek başına, 900s, en sonda).

---

## 8. Belge türü × proje matrisine etkisi

Hedef: **≥3 tür**, her biri **≥2 projede**, her proje **≥2 belge**. Bu plan uygulanırsa:
- `Legal Review Memo`: Karatepe+Kızılova+Yeşilova+Boztepe+Demirci = **5 proje** (zaten ≥3 tür/≥2 proje şartı fazlasıyla karşılanıyor, PF'nin kendi turundan beri).
- `Covenant Report`/`Insurance Notice`/`Facility Agreement`/`Bank Interest Notice`/`Budget Approval`/`Legal Opinion` — PF'den beri zaten ≥2 proje (bkz. Adım 3 raporu).

**Bulgu (risk, §9'a taşındı):** Akyar ve Güneşalan'ın **hiç davası yok** — bu plan onlara **hiçbir belge vermiyor**. Şu an bu iki projenin ledger'ında **sıfır belge** var (Boztepe/Demirci de şu ana kadar sıfırdı, bu plan onları da ≥2'ye çıkarıyor — ama Akyar/Güneşalan Hukuk'tan sonra da sıfırda kalacak, Enerji/Mali/İdari partilerinden ilk belgelerini bekliyorlar).

---

## 9. Riskler

- **Akyar/Güneşalan Hukuk'tan belge almıyor** — "her proje ≥2 belge" şartı bu parti SONUNDA hâlâ karşılanmıyor (2/7 proje sıfırda kalıyor). Enerji veya Mali İşler partisi bunları önceliklendirmeli.
- **T-12.1/T-12.2'nin duruşma/karar durumu bilinmeden** hangi belgenin missing_document (sonuçlanmadı) hangisinin var (sonuçlandı) olduğu belirlenemez — yanlış tahmin "icat" riski taşır.
- **Boztepe'nin duruşma tarihi (28.10.2026) demo_today'den (06.10.2026) SONRA** — PF'deki Kızılova/Yeşilova örüntüsüyle aynı: duruşma celp/tebliğ belgesi duruşmadan ÖNCE (demo_today'e yakın) tarihli olmalı, duruşmanın SONUCUNU anlatan bir belge henüz üretilemez (olay gelecekte).
- **Kızılova'nın ihtarnamesi ile EPC ihtilafının PF/Enerji sınırı** — ABC İnşaat zaten PF'nin (teminat mektubu) ve muhtemelen Enerji/EPC'nin (hakediş) ortak tarafı; ihtarnamenin KONUSU (örn. gecikme mi, kalite mi) EPC tarafıyla çakışmamalı, T-12.4 netleşince kontrol edilmeli.

---

## 10. SORU listesi + önerilerim

1. **T-12 tablosunun kendisi** — ayrı bir soru değil, cevap bekleyen bir veri talebi (§4).
2. **LegalCase şeması ne zaman eklensin** — cevaplar gelmeden mi (alanları Optional/pending bırakarak), yoksa cevaplar gelince mi? **Önerim:** cevaplar gelince — Optional alan eklemek kendi başına risksiz ama hangi alanların GEREKTİĞİ (örn. "duruşma sonucu" alanı, dava bitmediyse hiç kullanılmayacak) cevaplar gelmeden tam bilinmiyor.
3. **Akyar/Güneşalan'ın ilk belgeleri hangi partiden gelsin** — Enerji mi, Mali İşler mi? **Önerim:** Enerji — ikisi de aktif/geliştirme aşamasında teknik projeler, en doğal ilk belgeleri (bağlantı görüşü, teknik rapor) o partiden gelir.
4. **Kızılova ihtarnamesinin içeriği EPC ile çakışmasın diye** sınır nasıl çizilsin? **Önerim:** ihtarname yalnız "sözleşme ihlali iddiası" düzeyinde kalsın (hangi madde, ne zamandan beri), somut hakediş/ödeme tutarlarına girmesin — onlar zaten PF/Enerji'de.

---

**T-12 tablosu — Tansu'ya gönderilebilir** (boş Cevap sütunuyla):

| Kod | Proje | Eksik değer | Şu anki varsayım | Cevap |
|---|---|---|---|---|
| T-12.1 | Karatepe | Kamulaştırma davası: mahkeme adı, dava no, duruşma/karar tarihi, talep/belirlenen bedel | Hiç yok | |
| T-12.2 | Yeşilova | Tazminat davası: mahkeme adı, dava no, duruşma/karar tarihi, talep edilen tutar | Hiç yok | |
| T-12.3 | Boztepe | İmar iptali davası: dava no, talep edilen sonuç/gerekçe (mahkeme + duruşma tarihi zaten verildi: Ankara 2. İdare, 28.10.2026) | Hiç yok | |
| T-12.4 | Kızılova | Yüklenici ihtilafı: ihtarname tarihi, ihtilafın konusu/tutarı, taraf (ABC İnşaat mı?) | Hiç yok | |
| T-12.5 | Demirci | TEA itirazı: TEA'nın olumsuz görüş tarihi, itiraz tarihi, mercii, gerekçe | Hiç yok | |
| T-12.6 | Boztepe | Kredi (2024-BZ) imza günü | AI_ASSUMPTION: 2024-05-02 (zaten ledger'a işlendi) | |

---

## 11. Naci cevapları (11.10.2026)

§10'daki SORU listesine cevaplar — işlenmiş, uygulanacak kararlar:

1. **LegalCase şeması ne zaman eklensin (SORU 2):** Önerilen seçenek (cevaplar gelince) onaylandı. T-12.1-6 cevapları Tansu'dan gelmeden `LegalCase`-şekilli yeni bir yapı eklenmiyor — hangi alanların gerçekten gerektiği (örn. "duruşma sonucu") cevaplar gelmeden icat riski taşır.
2. **Akyar/Güneşalan'ın ilk belgeleri hangi partiden gelsin (SORU 3):** Enerji partisinden — önerilen seçenek onaylandı (ikisi de aktif/geliştirme aşamasında teknik projeler, en doğal ilk belgeleri bağlantı görüşü/teknik rapor).
3. **Kızılova ihtarnamesinin EPC ile çakışmaması (SORU 4):** Önerilen sınır onaylandı — ihtarname YALNIZ "sözleşme ihlali iddiası" düzeyinde kalır (hangi madde, ne zamandan beri); somut hakediş/ödeme tutarına GİRMEZ, bu zaten PF/Enerji partisinin kapsamında.

Bu üç karar, Hukuk partisinin bir sonraki üretim turunda (T-12 cevapları geldikten sonra) doğrudan uygulanacak; bu turda production yapılmadı (plan-only).
