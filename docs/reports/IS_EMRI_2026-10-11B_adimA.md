# İş Emri 2026-10-11-B — Adım A Raporu (Hukuk tarafları — araştırma, kod yok)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **DURMADAN Adım B'ye geçiliyor** (talimat gereği)

## 1. Kaynaklar

- `docs/plans/ADIM5_TANSU_PR21_ISLEME_PLANI.md` §5/§9.4 — ilk 18 belgelik Hukuk listesi önerisi.
- AI-BalBal `docs/naci-notlari` dalı → `docs/NACI_NOTU_URUN1.md` §D.1.3 — karşı taraf cari
  listesi çekirdeği (banka/EPC/türbin/sigorta/kamu kurumu/mülk sahibi türleri).
- AI-BalBal PR #21 (`docs/naci-cevap-6-2026-10-11` dalı) → `docs/NACI_CEVAP_2026-10-11.md`
  §1 (T-12, **"Hepsi ürün sahibi onaylıdır, AI_ASSUMPTION gerekmez"**), §3.5 (banka adları —
  **kapsam dışı, Ç-12**), §3.6 (KGF — bu listeye girmiyor), §5 (bilinçli bırakılanlar).

**Kaynak önceliği uygulandı: canvas (T-12 cevabı, ürün sahibi onaylı) > notlar (§D.1.3) >
ledger.** T-12 cevabı en ayrıntılı ve en yeni kaynak olduğu için asıl taraf/tarih/tutar
bilgisi oradan alındı.

## 2. KRİTİK BULGU — ID çakışması (plan/ledger çelişkisi, DURMADAN çözüldü)

Planın önerdiği `DOC-ANK-LEG-001/002/003` **zaten ankara_res.yaml'da var ve BAŞKA belgeler**
(Hukuki Görüş — Finansman Ön Koşulları / Arazi Kullanım Hakkı İnceleme Notu / Sözleşme Uyum
Değerlendirmesi — bu oturumun önceki adımlarında defalarca üretilen, tamamen farklı konulu
belgeler). Plan bu 3 ID'yi tahsis ettiğinde ledger'ın güncel hali görülmemiş. Bu bir
"plan/ledger çelişkisi" ama DURMA KURALI'nın kastettiği türden bir AMBİGÜİTE değil — çözümü
tektir ve bariz (sıradaki boş numaralardan devam et): **küçük teknik detay** olarak kendim
çözdüm (CLAUDE.md "isimlendirme ... kendin karar ver, raporda listele"), DURMADAN devam
ediyorum. Karatepe'nin hukuk davası belgeleri **DOC-ANK-LEG-004'ten başlayarak** numaralandı.

## 3. Rule 1 uygulaması — isimsiz özel kişi bulunan 3 süreç ATLANDI

Kaynakta (T-12 cevabı) şu üç davanın davacısı **"(kurgusal kişi)"** olarak işaretli, **özel bir
ad verilmemiş**:
- T-12.1b (Karatepe, elektrik direği ihlali) — davacı "komşu parsel maliki (kurgusal kişi)".
- T-12.2 (Yeşilova, tazminat/arazi tahsis) — davacı "arazi maliki (kurgusal kişi)".
- T-12.2b (Yeşilova, sınır ihlali) — davacı "komşu parsel maliki (kurgusal kişi)".

**ÖNCEDEN VERİLMİŞ KARAR 1** birebir bu durumu kapsıyor: "Özel kişi adı ... kaynakta yoksa
UYDURMA: o belgeyi atla, rapora 'Tansu'ya soru' yaz, devam et." Bu üç sürecin **dava
dilekçesi** belgeleri (davacının kendisini isimle anması gereken tek belge türü) ÜRETİLMEDİ.
**Tansu'ya soru:** Bu üç davanın davacısının (gerçek olmayan, kurgusal) adı ve soyadı nedir?

Her üç süreç için ise **isim gerektirmeyen** ikinci bir belge (hukuk danışmanı yazışması,
bilirkişi/duruşma kayıtları gibi) varsa o ÜRETİLDİ — davacıya yalnız rolüyle ("arazi maliki",
"davacı") atıfta bulunarak, hiçbir isim icat etmeden (bkz. §4, Yeşilova LEG-001).

## 4. Tam tablo (18 planlı süreç → 15 üretilecek belge + 3 atlanan)

| Yeni doc_id | Proje | Süreç (T-12.x) | Taraflar | Kaynak | Kaynak türü | El düzenlemeli mi |
|---|---|---|---|---|---|---|
| DOC-ANK-LEG-004 | Karatepe | T-12.1 dava dilekçesi | Karatepe RES Enerji Üretim A.Ş. (davacı) · Enerji ve Tabii Kaynaklar Bakanlığı (davalı) | NACI_CEVAP §1 | canvas (ürün sahibi onaylı) | Hayır (yeni) |
| DOC-ANK-LEG-005 | Karatepe | T-12.1 idare savunması | aynı | NACI_CEVAP §1 | canvas | Hayır |
| DOC-ANK-LEG-006 | Karatepe | T-12.1 bilirkişi raporu (15.09.2025) | aynı | NACI_CEVAP §1 | canvas | Hayır |
| DOC-ANK-LEG-007 | Karatepe | T-12.1 duruşma tutanağı (10.01.2026) | aynı | NACI_CEVAP §1 | canvas | Hayır |
| DOC-ANK-LEG-008 | Karatepe | T-12.1 mahkeme kalemi e-postası (`.eml`, 15.09.2026) | Karatepe RES Enerji Üretim A.Ş. · Ankara 4. İdare Mahkemesi (yazı işleri) | NACI_CEVAP §1 | canvas | Hayır |
| DOC-ANK-LEG-009 | Karatepe | T-12.1 karşı taraf avukatı e-postası (`.eml`, 10.09.2026) | Karatepe RES Enerji Üretim A.Ş. · Enerji ve Tabii Kaynaklar Bakanlığı (vekili, rol olarak) | NACI_CEVAP §1 | canvas | Hayır |
| ~~T-12.1b dava dilekçesi~~ | Karatepe | elektrik direği ihlali | **ATLANDI** — davacı isimsiz | NACI_CEVAP §1 | canvas | — |
| DOC-YSV-LEG-001 | Yeşilova | T-12.2 hukuk danışmanı yazışması (`.msg`, 14.09.2026) | Yeşilova RES Enerji Üretim A.Ş. (tek taraf; "arazi maliki" rol olarak anılır, isim yok) | NACI_CEVAP §1 | canvas | Hayır |
| ~~T-12.2 dava dilekçesi~~ | Yeşilova | tazminat/arazi tahsis | **ATLANDI** — davacı isimsiz | NACI_CEVAP §1 | canvas | — |
| ~~T-12.2b dava dilekçesi~~ | Yeşilova | sınır ihlali | **ATLANDI** — davacı isimsiz | NACI_CEVAP §1 | canvas | — |
| DOC-BOZ-LEG-001 | Boztepe | T-12.3 dava dilekçesi (22.05.2026) | Boztepe RES Enerji Üretim A.Ş. (davacı) · İlçe Belediyesi (davalı) | NACI_CEVAP §1 | canvas | Hayır |
| DOC-BOZ-LEG-002 | Boztepe | T-12.3 belediye savunması (25.06.2026) | aynı | NACI_CEVAP §1 | canvas | Hayır |
| DOC-BOZ-LEG-003 | Boztepe | T-12.3 YD reddi kararı (10.07.2026) | aynı | NACI_CEVAP §1 | canvas | Hayır |
| DOC-BOZ-LEG-004 | Boztepe | T-12.3 bilirkişi keşif tutanağı (26.09.2026) | aynı | NACI_CEVAP §1 | canvas | Hayır |
| DOC-IZM-LEG-005 | Kızılova | T-12.4 noter ihtarnamesi (29.09.2026) | Kızılova RES Enerji Üretim A.Ş. · ABC İnşaat A.Ş. | NACI_CEVAP §1 | canvas | Hayır |
| DOC-IZM-LEG-006 | Kızılova | T-12.4b Mera talep yazısı (21.08.2026) — **yalnız talep, sonuç YOK** (ÖNCEDEN VERİLMİŞ KARAR 5) | Kızılova RES Enerji Üretim A.Ş. · Valilik Mera Komisyonu | NACI_CEVAP §1 | canvas | Hayır |
| DOC-DMR-LEG-001 | Demirci | T-12.5 TEA itiraz dilekçesi (22.09.2026) — **sonuç belgesi YOK** (kaynak: "sonuç belgesi üretilmez") | Demirci RES Enerji Üretim A.Ş. · TEİAŞ | NACI_CEVAP §1 | canvas | Hayır |
| DOC-AKY-LEG-001 | Akyar | T-12.5b kamulaştırma ön değerlendirme notu (dava değil) | Akyar GES Enerji Üretim A.Ş. (tek taraf; "malik" rol olarak anılır, isim yok) | NACI_CEVAP §1 | canvas | Hayır |

**Güneşalan:** dava yok (NACI_CEVAP §1 son satır) — hiçbir belge üretilmiyor, zaten plana da
girmemişti.

**Toplam: 15 belge üretilecek, 3 atlandı (hepsi aynı nedenle: isimsiz özel kişi).**

## 5. .eml/.msg desteği

`backend/app/models/document.py` ve `seed_data/generator/ledger_schema.py::Document.
source_type` yalnız `digital_pdf | scanned_pdf | xlsx` kabul ediyor — **`.eml`/`.msg` desteği
YOK** (CLAUDE.md "V0 kapsamı dışında": Word/e-posta ingest). **ÖNCEDEN VERİLMİŞ KARAR 3**
gereği: DOC-ANK-LEG-008/009 (2 Karatepe e-postası) ve DOC-YSV-LEG-001 (Yeşilova `.msg`)
**mevcut `letter` ailesiyle, e-posta çıktısı düzeninde PDF olarak üretilecek** (gövdede
"Kimden/Kime/Tarih/Konu" alanları düz metin olarak yazılır — altyapıya (template/Family/
source_type) HİÇBİR değişiklik yapılmadı).

## 6. Diğer bulgular (küçük teknik düzeltmeler, raporda listelendi)

- `facts.py::_PREFIX_TO_LEDGER` ve `_project_name()`'de **"DMR"/"AKY" eksik** (Adım 4'te
  "BOZ" eklenmişti, "DMR"/"AKY" o zaman hiç belge üretmediği için atlanmıştı) — DOC-DMR-LEG-001
  ve DOC-AKY-LEG-001 üretilmeden önce eklenmesi gerekiyor (0-LLM, dar kapsamlı kod düzeltmesi,
  Adım 4'teki "BOZ" düzeltmesiyle birebir aynı desen). Adım B/C'de yapılacak.
- `generate_documents.py::_PROJECT_CODE` zaten BOZ/DMR/AKY/GNS'yi içeriyor (önceki round'da
  eklenmiş) — ek işlem gerekmiyor.

## 7. Kapsam dışı kalanlar (iş emrinin kendi listesi + T-12 cevabının netleştirdikleri)

- Banka adları (Ç-12) — T-12 cevabı gerçek adlara dönülmesini istiyor ama **bu iş emrinde
  KAPSAM DIŞI**; Hukuk belgelerinde zaten hiçbir banka adı doğrudan geçmiyor (yalnız T-12.3'te
  "Kurum / resmî ödeme" türü bilirkişi avansı geçiyor, banka adı yok) — dokunulmadı.
  DOC-ANK-LEG-004/005/006/007/008/009'da da banka yok.
- KGF — Hukuk listesine hiç girmiyor (Boztepe kredi sözleşmesi hukuk maddesi de kapsam dışı).
- Mera/TEA sonuç belgeleri — kaynağın kendisi "üretilmez" diyor + ÖNCEDEN VERİLMİŞ KARAR 5.

Devam ediliyor: **Adım B** (ledger `parties`/`documents` güncellemesi).
