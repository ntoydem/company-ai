# İş Emri 2026-10-16P2 — B-01 + Excel proje ayrımı: PLAN

**Tarih:** 16.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `3026264`) · **Ürün 1** · **Ç-15/3 (erişim) + Ç-15/8 (prompt) → T-9: kod öncesi plan, onay bekleniyor**

**Dayanak** (`ftansu/AI-BalBal` ana dal `d7aa089`, salt okundu):
- `docs/yazismalar/2026-10-16_naciye-karar-excel-proje-ayrimi.md` (PR #52)
- `docs/yazismalar/2026-10-16_naciye-2044-sorularina-cevap.md` S9
- `docs/yazismalar/2026-10-16_naciye-acik-kararlar.md` §C
- `kontrolor/bilgilendirmeler/2026-10-15_NACI_DIKKATINE.md` B-01
- `kontrolor/durum/2026-10-15_KONTROLOR_DURUM_RAPORU.md` B-5, D-2
- company-ai `docs/reports/IS_EMRI_2026-10-16M1.md` §5 (B-01 teşhisi)

**Okunan anayasa:** `00-cekirdek.md` (Ç-15, Ç-16, Ç-17), `01-urun.md` (Ü-3, Ü-8), `02-teknik.md` (T-4, T-5, T-9 + ADT-4).

**Durum:** Yalnız plan. Kod, prompt, ayar, şema, puanlayıcı, soru seti ve canlı servis değişmedi. Ölçüm, eval DB'nin dışa aktarılmış audit satırlarından (`logs/{s3,m1,n1}_audit.jsonl`, eval DB'den `SELECT` ile alınmıştı) ve `results/` dosyalarından yapıldı. Yeni LLM çağrısı yapılmadı. Hesap motoru yerelde, seed workbook'larıyla, LLM'siz ve DB'siz çalıştırıldı (§1.3).

---

## 1. B-01: tanım ve kök neden

### 1.1 Tanım (kontrolör, 15.10.2026, canlı sistem)

B-01 başlığı ilk açıldığında "Excel içeriğine hiçbir hat ulaşamıyor" idi. Kontrolör D-2 ile bunu daralttı: **"Karatepe dışı Excel dosyalarına (Yeşilova/Boztepe ödeme planı) ulaşılamıyor."** Karatepe Excel'leri çalışıyor.

| # | Soru (kontrolörün canlı denemesi) | Balbal | Beklenen |
|---|---|---|---|
| 1 | "Yeşilova kredi ödeme planında 12. taksitin anapara tutarı nedir" | Yalnız belge hattı çalıştı. "Ödeme Planı — Güncel" listelendi, "kesin bilgi bulamadım" dendi. | 98.000 USD |
| 2 | "Yeşilova 2027'de hangi kredi ödemelerini yapacak?" | Yalnız belge listesi döndü. | 2027 satırları (Excel'de var) |
| 3 | "Yeşilova'nın bir sonraki kredi ödemesi ne zaman" | Vade 14.10.2026 ve faiz 18.912 USD banka bildiriminden doğru. Anapara verilmedi. | 14.10.2026 · 98.000 USD anapara + 18.912 USD faiz |

**Ölçülmüş örnek** (M1 §5): audit `ea2a42d1…`, 15.10.2026 16:59 UTC. `query_type = DOCUMENT_QUERY`, `excel_files_used = []`. Router'ın gerekçesi: *"repayment schedule amount stated in the loan agreement's payment plan"*. Karşılaştırma için: benzer soru ("… 11. taksitin vadesi ve anaparası") 13.10'da DATA'ya gitmiş ve Excel'den doğru cevap almıştı (98.000 USD).

**99 soruluk sette B-01 sorusu yok.** Yeşilova/Boztepe ödeme planından cevap bekleyen soru sayısı 0. Bu yüzden B-01 kapı skorunu bugün etkilemiyor; etkilenen soru sayısı 0, geçme durumu ölçülemez. Kontrolör bunu B-5'te yazmıştı.

### 1.2 Kök neden: üç katman (birincisi kanıtlı)

1. **Router (kanıtlı, engelleyici).** `router.py::ROUTER_SYSTEM_PROMPT` Excel tarafını yalnız dört türle tanımlıyor: *financial model, covenant report, budget vs actual, monthly production*. Ödeme planı workbook'ları ve "taksit / anapara / vade" sözcükleri DATA ipucu değil. Prompt ayrıca "sözleşmede *yazan* rakam DOCUMENT'tır" diyor. Bu yüzden model "ödeme planındaki tutar"ı sözleşme maddesi sanıyor. Soru DOCUMENT'a gidince Excel hattı **hiç çalışmıyor**. Ters yönde geri düşüş yok: DOCUMENT boş dönünce Excel denenmiyor (ADR-010; DATA→DOCUMENT tek yön).
2. **Başlık satırı (kod okumasıyla ve yerel çalıştırmayla doğrulandı; canlıda ölçülmedi).** `calc.py::CachedValueEngine.load` sütun adlarını her sayfanın **1. satırından** alıyor. Ödeme planı sayfalarında 1. satır bir unvan satırı ("Ödeme Planı — Yeşilova RES"). Gerçek başlık Yeşilova'da 4. satırda, Boztepe'de 7. satırda. Planlayıcıya giden katalog şöyle:
   - Yeşilova: `deme_plan_ye_ilova_res, col_b, col_c, col_d, col_e`
   - Boztepe: `boztepe_res_anapara_geri_deme_plan_84_taksit, col_b … col_g`

   Ayrıca bütün sütunlar metin tipinde. Başlık satırı ve önsöz satırları veri gibi okunuyor. Sonuçlar:
   - Planlayıcı "anapara" sütununu adından bulamıyor, tahmin etmek zorunda kalıyor.
   - Tarih filtresi (`vade <= TODAY`) ve gelecek tarih koruması (`future_guard`) çalışmıyor, çünkü tarih sütunu yok.
   - Para birimi sütun adından okunamıyor ("98.000", USD'siz).

   13.10'daki doğru cevap bu zayıflığa rağmen geldi. Tekrarlanabilir değil.
3. **Eski sürüm katalogda.** `Ödeme Planı — Mart 2026` (`superseded`) güncel planla aynı tabloyla katalogda. Katalog satırında sürüm durumu yazmıyor. Planlayıcı eski sürümü seçebilir (değişmez kural 5).

**B-01'e komşu, bu paketin dışında:**
- **1×1 sınırı (ADR-011).** Örnek 2 ("2027'de hangi ödemeler", çok satır) ve örnek 3'ün "ne zaman + ne kadar" çifti tek hücre değil. Motor tablo döndürünce bugün seçenekli netleştirme soruyor. Bunun çözümü (kodla biçimlenen küçük sonuç tablosu) ayrı plan konusu.
- **GEN-DSC-006 "Ödeme planı yüklü mü?"** Adsız keşif sorusu. Kaybın sebebi G3 yabancı proje listesi (proje ekseni). Sözlük ek notu (kontrolör) doğru ama bu soruyu çevirmiyor.

### 1.3 Excel yolunda proje ayrımı: bugün nasıl çalışıyor (kod okuması)

Akış:
1. `ask_router._run` → `excel_ask.answer_data_question`.
2. `allowed_document_ids` (ADR-004) → `document_repo.list_excel_by_ids` (yetkili **tüm** hazır workbook'lar, başlık sırasıyla) → `_load_workbooks` → `_catalogue` → planlayıcı (Sonnet) → `run_function` veya `run_sql` → cevap modeli → audit.

Hangi workbook'un hangi projeye ait olduğu `documents.project_id` alanında **zaten var**. Seed, manifestteki `project_code`'dan dolduruyor. Ama Excel yolu bu bilgiyi hiç okumuyor:
- **Daraltma yok.** Belge yolundaki `narrow_allowed` (ADR-031) Excel yolunda çağrılmıyor. Finans, finans_mudur ve yonetim kullanıcıları 7 workbook'un 7'sini görüyor (4 Karatepe, 2 Yeşilova, 1 Boztepe). Karatepe sorusunda da Yeşilova/Boztepe tabloları katalogda.
- **Katalogda proje yok.** Satırda yalnız dosya adı, başlık ve tür var.
- **Fonksiyonlar proje bilmiyor.** `_first_named` ve `__debt` / `__production` taramaları "listede ilk uyan dosya"yı alıyor. Yerel deneme (LLM'siz, 7 seed workbook):

| Çağrı | 7 workbook ile | Yalnız Yeşilova workbook'larıyla |
|---|---|---|
| `outstanding_debt(as_of=today)` | **11.671.800 USD — `Financial_Model_2026.xlsx` (Karatepe) Debt!H9** | `FunctionError` → "veri yok" |
| `outstanding_debt(as_of=2026-10)` | **11.671.800 USD — Karatepe** | `FunctionError` |
| `dscr(Q2_2026)` | **1,37x — `Covenant_Report.xlsx` (Karatepe)** | `FunctionError` |

Yani "Yeşilova'nın kalan kredi borcu ne kadar?" sorusu DATA'ya gider ve planlayıcı `outstanding_debt`'i seçerse cevap **Karatepe'nin rakamı** olur. Bu kendinden emin yanlıştır ve proje karışmasıdır. Bugün bu soru setinde yok, o yüzden ölçülmedi.

**B-01 ile bağı:** B-01 düzeltmesi (router) Yeşilova/Boztepe sorularını Excel'e **daha çok** gönderecek. Proje ayrımı yokken bu, yukarıdaki riski canlıya taşır.

## 2. Ölçüm (LLM'siz; S3, M1 ve N1 audit satırları)

"21 Excel sorusu" için tek bir liste bulamadım. Ortak not ve kontrolör raporunda sayı olarak geçiyor. Bu yüzden ölçü kümesini şöyle tanımladım: **S3, M1 veya N1 koşusundan en az birinde DATA/MIXED'e gitmiş 20 soru.** Buna workbook kaynağı bekleyen ama hep DOCUMENT'a giden 5 keşif sorusu eklenince 25 oluyor.

| Koşu | Excel'e giden soru | Kullanılan workbook (soru başına) | Yabancı proje workbook'u | Excel'e gidip geçen (v2.2) |
|---|---|---|---|---|
| S3 (14.10) | 20 | 11 | **0** | 12 (ham S3 puanı; kontrolörün "20'nin 12'si" sayısıyla aynı) |
| M1 (16.10, resmî 71/99) | 19 | 12 | **0** | 9 |
| N1 (canlı kod) | 16 | 10 | **0** | 10 |

- Kullanılan workbook'ların **hepsi Karatepe'ye ait**, soruların hepsi de Karatepe sorusu. Yabancı proje kullanımı = 0. Ama bu bir **kanıt değil**: setteki 99 sorunun hiçbiri Karatepe dışı bir workbook istemiyor (kontrolör B-5). Risk ancak Yeşilova/Boztepe sorusuyla ölçülebilir (§8).
- Katalogda yabancı proje tablosu bulunan sorular: finans, finans_mudur ve yonetim kullanıcısıyla sorulan Excel soruları. Bu kullanıcılarla 7 workbook'un hepsi planlayıcıya gidiyor. Enerji kullanıcısı yalnız Karatepe'nin 2 operasyon dosyasını görüyor.
- B-01'den etkilenen soru: **0** (§1.1).

## 3. Önerilen yöntem (PR #52 hedefleri)

**İlke: AI anlar, kod uygular.** Router (AI) soru Excel'e mi gidecek, buna karar verir. Planlayıcı (AI) hangi tablo veya fonksiyon olduğunu seçer. **Hangi projenin dosyalarının aday olacağına kod karar verir:** yetki kümesinin içinden, belge yolundaki kuralla aynı şekilde. Kullanıcının görmediği workbook hiçbir adımda prompta girmez (T-5).

### 3.1 Proje ayrımı (kod, prompt değişmez)

| Hedef (PR #52 §3) | Uygulama |
|---|---|
| 1. Proje adı geçiyorsa yalnız o projenin workbook'ları | `answer_data_question`, kullanıcının **kendi sorusundan** `named_project_codes` (ADR-033) okur. Router'ın yeniden yazdığı alt soru kullanılmaz; belge yolundaki ADR-031 Şart 1 ile aynı. Ardından `narrow_allowed(session, allowed, named)` → `allowed ∩ (proje ∈ adlı ∪ grup)` çalışır. Katalog, fonksiyonlar ve SQL yalnız bu kümeyi görür. Başka projenin dosyası katalogda yoksa fonksiyon onu seçemez (§1.3 tablosunun sağ sütunu). |
| 2. Proje adı yok + birden çok projede uygun dosya | Plan çalıştıktan sonra, cevap modelinden **önce**, kod bakar: planın kullandığı workbook'un türünü (`document_type`) yetki kümesinde taşıyan **projeler** hangileri? Birden fazlaysa rakam atılır (hiç gösterilmez, modele gitmez). Cevap tek netleştirici sorudur: "Hangi proje için sormak istiyorsunuz (Boztepe RES, Yeşilova RES)?" Seçenekler yalnız o veriye sahip projelerdir, metinde rakam yoktur (G1). Bu, P1 planındaki ilkeyle aynı. Cevap modeli çağrılmaz. Tek proje kalırsa bugünkü gibi cevap verilir (§9 S-2). |
| 3. Grup belgesi aynı mantık | `narrow_allowed` grup kapsamını zaten içeriyor. Bugün grup kapsamlı workbook yok. Kural, gelecekte yüklenecek dosyalar için hazır olur. |
| 4. Filtre yetki kümesinin içinden | Daraltma `allowed_document_ids`'ten **sonra** gelir ve yalnız aday çıkarır. Yetki girdisi olarak kullanılmaz. `/api/excel/ask` doğrudan ucu da aynı fonksiyondan geçer. |

**İki proje adı geçen Excel sorusu** (Ü-3: "her projeye ayrı cevap"): Bu pakette katalog iki projeye daralır. Plan tek projenin dosyasına dokunursa cevap verilmez, "hangisi?" diye sorulur. Proje proje ayrı Excel cevabı (iki plan, iki kaynak) bu paketin dışında (§9 S-3).

**Hesap motoru fonksiyonlarının imzası değişmez.** PR #52 imza değişikliği öngörüyordu. Daraltma katalog düzeyinde yapılınca fonksiyonlara zaten yalnız doğru projenin dosyaları gider. Proje bilgisi tek bir noktada uygulanır; beş fonksiyona ayrı ayrı dağılmaz (§10).

### 3.2 B-01 (router ipucu + başlık satırı + sürüm durumu)

**a) Router ipucu — "madde 12" (prompt, Ç-15/8, ayrı onay).** Madde 12'nin kendi metni repolarda yok. Yalnız üç yerde atıf var (WA verimlilik cevabı §5: "tüm ödeme planı workbook'ları için genel ipucu"; bilgi katmanı şeması §5: "taksit, anapara, vade"; PR #52 §5). Kaynağı 13.10 mimari görüş notu §7.1 ("sabit listede ödeme planları yok"). Önerilen metin değişikliği `ROUTER_SYSTEM_PROMPT` içinde **iki yerde**:
- Excel tanımına: *"… monthly production, **loan repayment schedules (ödeme planı: instalment number, due date, principal, interest per instalment)**; figures computed by a calculation engine."*
- DATA_QUERY tanımına: *"**A value read from a repayment schedule row — an instalment's (taksit) due date (vade), principal (anapara) or interest, the next or a numbered instalment — is DATA_QUERY, even when the question says 'ödeme planında'. Only repayment terms written in a loan agreement (tenor, agreed number of instalments, grace period) are DOCUMENT_QUERY.**"*

Yeni bir örnek satır da eklenir. Proje adı yerine genel bir soru kullanılır, kontrolör sorusu prompta kopyalanmaz: `Q: Ödeme planında 5. taksitin vadesi ne? -> DATA_QUERY`.

Genel ipucu dosya adı saymaz. Kullanıcının yüklediği her ödeme planına uygulanır. Dinamik katalog (router'a kullanıcının gördüğü workbook türlerini vermek) daha sağlam olurdu, ama router'dan önce yetki sorgusu ve daha uzun prompt gerektirir. Kapıdan sonraya bırakıyorum (§10).

**b) Başlık satırı bulma (kod).** `CachedValueEngine.load` başlığı 1. satırda sabit bırakmaz. İlk 10 satırda şu koşulu sağlayan ilk satırı başlık sayar: **en az 3 dolu hücre var ve hepsi metin.** Bulunamazsa 1. satır kullanılır, yani bugünkü davranış. Başlığın üstündeki önsöz satırları ("Toplam Kredi (USD)", "Anlık görüntü tarihi") ayrı bir küçük anahtar/değer tablosuna (`…__<sheet>_info`) alınır, kaybolmaz.
- **Yerelde denendi (7 seed workbook, 22 görünür sayfa):** Karatepe'nin 19 sayfasının hepsinde başlık 1. satırda kalıyor, yani tablolar bugünküyle aynı. Yeşilova'da 4. satır, Boztepe'de 7. satır seçiliyor.
- Eşik bilerek 3. "En az 2" ile denendiğinde Covenant Report'un 11 çeyrek sayfası (anahtar/değer düzeni, 3. satır `Period | Q2_2026`) yanlışlıkla başlık sayılıyordu.
- Karatepe tablolarının aynı kalması testle sabitlenir.
- Yeşilova'da sütunlar `taksit_no, vade, anapara_usd, faiz_usd, durum_…` olur, Boztepe'de benzer şekilde. Sayı ve tarih tipleri düzelir. `future_guard` `vade` sütununu bulur. Para birimi sütun adından gelir (USD).

**c) Sürüm durumu katalogda (kod + planlayıcı promptuna bir cümle, Ç-15/8).** Katalog satırına `project`, `status` ve gerekiyorsa `superseded by` eklenir. Bu veri; kod yazar. `PLAN_SYSTEM_PROMPT`'a bir cümle eklenir: *"Use the current version of a workbook; use a superseded one only when the question names that older version or date."* Kaynak kartı ve audit zaten dosya adını gösteriyor. Hangi sürümün kullanıldığı görünür kalır (kural 4).

**Bu paketle beklenen B-01 sonucu** (tahmin, ölçülmedi):

| Örnek | Sonuç |
|---|---|
| 1 | Çözülür (tek hücre). |
| 3 | Kısmen çözülür. Anapara Excel'den gelir. Vade ve faiz yalnız router MIXED derse belge yarısından gelir. "Ne zaman + ne kadar" çifti 1×1 sınırına takılır. |
| 2 | Çözülmez (çok satır, 1×1 sınırı). §9 S-1. |

## 4. Aynı paket mi, ayrı mı? — **Aynı paket, iki ayrı commit, ayrı ölçü**

**Gerekçe:** İkisi de aynı yolda (Excel hattı), aynı dosyalarda. Asıl önemli nokta şu: B-01 düzeltmesi Karatepe dışı soruları Excel'e açıyor. Proje ayrımı olmadan canlıya çıkarsa §1.3'teki Karatepe rakamı riskini **büyütür**. Bu yüzden sıra:
1. **Commit 1:** Proje ayrımı (§3.1). Tek başına canlıya çıkabilir; yalnız aday çıkarır.
2. **Commit 2:** B-01 (§3.2 a+b+c). Yalnız commit 1'in üstüne çıkar.

Ölçüler PR #52 §5'teki gibi ayrı raporlanır (§8).

## 5. Etkilenen dosyalar, büyüklük, şema, bağımlılık, maliyet

| Dosya | Değişiklik | Büyüklük |
|---|---|---|
| `app/services/excel_scope.py` (yeni) | daraltma (`narrow_allowed` çağrısı), veriye sahip projeler, netleştirme cümlesi | ~90 satır |
| `app/services/excel_ask.py` | `answer_data_question(… original_question)`, katalog satırına proje/durum, adsız-çok-proje kontrolü, planlayıcı promptuna 1 cümle | ~+30 / −5. Dosya bugün 629 satır; yeni mantık yeni modüle gider. |
| `app/services/ask_router.py` | `_run` kullanıcının sorusunu Excel'e de geçirir; MIXED'de iki yarı da proje soruyorsa tek soru gösterilir | ~+15 |
| `app/excel/calc.py` | başlık satırı bulma + önsöz tablosu | ~+35 |
| `app/services/router.py` | `ROUTER_SYSTEM_PROMPT` 2 cümle + 1 örnek | ~+8 |
| `docs/prompts/*` | `make prompt-doc` ile kopyalar | otomatik |
| `docs/ARCHITECTURE.md` | ADR-035 (Excel proje ayrımı + başlık satırı); ADR-010'a not | kısa |
| testler | §8 | ~+250 |

- **Şema / migrasyon: gerekmiyor.** `documents.project_id`, `project_scope` ve `status` zaten var (Ç-15/4 tetiklenmiyor).
- **Yeni bağımlılık:** Yok.
- **`excel/functions.py`:** Dokunulmaz.
- **LLM maliyeti:**
  - Yeni çağrı yok.
  - Router promptu ~+90 token; Haiku'da soru başına ~0,0001 USD.
  - Planlayıcı kataloğu daralınca kısalır: finans kullanıcısında 7 workbook yerine 2–4. Sonnet planında soru başına girdi düşer.
  - Adsız-çok-proje durumunda cevap çağrısı atlanır.
- **Doğrulama koşusu (LLM'li):** Tahmini ~0,3–0,5 USD. Ayrı onayla (§8).

## 6. Prompt değişikliği (Ç-15/8): **VAR, ayrı onay gerekir**

- `router.py::ROUTER_SYSTEM_PROMPT`: §3.2a'daki iki cümle ve bir örnek.
- `excel_ask.py::PLAN_SYSTEM_PROMPT`: §3.2c'deki tek cümle.
- Cevap promptu (`answer_prompt.py`) ve Excel cevap promptu **değişmez**.
- Katalog satırına eklenen `project` ve `status` alanları kodun ürettiği veridir, kural değildir. Yine de planlayıcının gördüğü metni değiştirdiği için bu onayın içinde sayıyorum.

Proje ayrımı (commit 1) prompt değiştirmez. Onaylanırsa B-01'den bağımsız yapılabilir.

## 7. Madde 12 (ödeme planı router ipucu) bu pakete giriyor mu? — **Evet**

§3.2a = madde 12. "Dondurmadan önce başlamayacaklar" listesindeydi (WA 16.10 v14 notu). PR #52 ve S9 ise B-01'i kapı öncesine aldı. Bu yüzden etiketten sonra, kapıdan önce bu pakette yapılır.

## 8. Riskler, test planı, geri alma

**Riskler:**

| Risk | Önlem |
|---|---|
| **Yetki sızıntısı** — görmediği projenin workbook adı veya varlığı kullanıcıya ya da prompta gider | Daraltma yetkiden sonra gelir, yalnız çıkarır. Netleştirme seçenekleri yalnız yetkili workbook'lardan çıkar. Test: enerji kullanıcısı "Yeşilova taksit" sorar → katalog boş, promptta Yeşilova adı/dosyası yok, seçeneklerde yok. |
| **Yanlış workbook** — proje adı eşleşmez ("X GES" eki, ADR-033'te açık), daraltma çalışmaz | Bugünkü davranışa düşer, yeni bir yanlış eklenmez. Adı tanınmayan proje zaten router'dan önce reddediliyor. |
| **Hesap yanlışı** — başlık bulma yanlış satırı seçer (anahtar/değer sayfaları) | Eşik 3 metin hücresi (2 ile Covenant çeyrek sayfaları bozuluyordu, §3.2b). Karatepe'nin 19 sayfası aynı kalmalı (test). Kurala uyan satır yoksa 1. satıra düşülür. Kaynak kartı hücre adresini gösterir. |
| **Eski sürüm seçilir** | Katalogda durum alanı + planlayıcı cümlesi. Kaynak kartında dosya adı görünür. |
| **Excel dışı yola etki** — router DOCUMENT sorularını DATA'ya kaydırır (ANK-OPS-003, ANK-FIN-014 sınıfı, "sözleşmedeki taksit sayısı") | Prompt cümlesi sözleşme şartlarını açıkça DOCUMENT bırakıyor. Belge yolu ölçüsü önce/sonra karşılaştırılır. DATA boş dönerse belgeye düşüş (ADR-010) korunur. |
| **Adsız sorularda çift soru** (MIXED: belge yarısı da proje sorar) | Kod tek soru gösterir (`ask_router`). |

**Testler:**
1. **Birim / servis (LLM sahte):**
   - Daraltma: finans + "Yeşilova …" → katalogda yalnız YSV dosyaları. "Karatepe …" → YSV/BOZ yok.
   - **KY testi:** "Yeşilova kalan borç" + sahte plan `outstanding_debt` → Karatepe rakamı **dönmez**, `FunctionError` → veri yok → belgeye düşüş.
   - Adsız + ödeme planı → seçenekler tam {Boztepe, Yeşilova}, rakamsız, cevap modeli çağrılmaz.
   - İki proje adı geçer + plan tek projeye dokunur → netleştirme.
   - Grup kapsamlı workbook her iki projede de aday kalır.
   - Başlık bulma: 7 seed workbook için sütun anlık görüntüsü; Karatepe'nin 19 sayfası bugünle aynı.
   - Router prompt kopyası (`make lint`).
2. **Sızıntı testi:** enerji, hukuk ve finans kullanıcılarıyla, sahte LLM'in aldığı her prompt metni yetki dışı dosya adı/başlığı için taranır.
3. **Eval, LLM'siz:** Tam `make test`, `make lint`.
4. **Eval, LLM'li (ayrı onay):**
   - (i) **Proje ayrımı ölçüsü:** 20 Excel sorusu önce/sonra, cetvel `cetvel-v2.2-v14.1` (V21 yerine onun devamı). Yabancı proje workbook'u = 0, mevcut geçenler düşmemeli.
   - (ii) **B-01 ölçüsü, ayrı:** Kontrolörün 3 B-01 sorusu ve kendi Yeşilova/Boztepe varyantlarım. Bunlar **`questions.json`'a girmez** (soru seti dondurulmuş), ayrı bir liste olarak koşulur ve raporlanır.
   - (iii) **Yan etki:** Belge yolu soruları için router kararı önce/sonra (DOCUMENT→DATA kayması sayısı).

   Kontrolörün BT-02 Yeşilova yükleme testi ayrıca ölçer.

**Geri alma:** Yalnız kod, şema değişmiyor. İki commit ayrı ayrı `git revert` edilir, sonra `make restart-backend` (N1'de ~12 sn). Canlıya alma ayrı onayla yapılır (Ç-15/6: yedek, smoke 9/9).

## 9. Tansu'ya açık sorular (3)

**S-1 (B-01 kapsamı):** Bu paket örnek 1'i çözer, örnek 3'ü kısmen çözer. Örnek 2 ("2027'de hangi ödemeler", çok satır) ile örnek 3'ün "ne zaman + ne kadar" çifti 1×1 sınırına takılır. B-01 kapı için bu hâliyle kapanmış sayılır mı? Yoksa kapıdan önce küçük bir "sonuç tablosu" planı mı isteniyor? (Kodla biçimlenen, tek kaynaklı, en fazla N satırlık tablo; Birleştirme değil.)

**S-2 (adsız soru, tek proje):** Proje adı geçmeyen Excel sorusunda veriye yalnız bir proje sahipse ne yapılsın? Önerim: bugünkü gibi o projeden cevap, cevapta proje adı ve kaynak kartı. Madde 2'deki "tek aday da sorulsun" çizgisi belge yolu içindi; Excel'de de mi geçerli olsun?

**S-3 (iki proje adı):** "Yeşilova ve Boztepe'nin sıradaki taksiti" gibi iki proje adı geçen Excel sorusunda bu pakette "hangisi?" diye sorulması (yanlış yok, eksik cevap yok) ve proje proje ayrı Excel cevabının (Ü-3) kapıdan sonraya kalması uygun mu?

## 10. Teknik görüşüm (PR #52 §6)

- **Engel görmüyorum.** Proje bilgisi workbook'larda zaten var (`project_id`). Şema gerekmiyor. Belge yolundaki daraltma fonksiyonu olduğu gibi kullanılabiliyor.
- **Daha iyi yol:** Fonksiyon imzalarını değiştirmek yerine daraltmayı **kataloğu kurarken tek noktada** yapmak. Fonksiyonların "ilk uyan dosya" davranışı, listede yalnız doğru proje kaldığında zararsız olur. Proje kuralı beş ayrı yerde değil, bir yerde durur ve test edilir.
- **B-01'i proje ayrımından önce canlıya almamak gerekir.** Router düzeltmesi tek başına Yeşilova sorularını Excel'e açar ve bugün Karatepe rakamı dönebilecek bir yol yaratır (§1.3).
- **B-01'in yarısı router değil, veri biçimi.** Başlığı 1. satırda olmayan her gerçek müşteri Excel'i aynı sorunu yaşar. Başlık satırı bulma, BT-02 yükleme testinden önce yapılmalı.
- **Kapıdan sonrası için öneri:**
  - Dalga 1'de proje anlama AI'a geçince (router JSON'unda `projects`), bu paketteki daraltma aynen kalır; yalnız girdisi değişir.
  - Router'a statik ipucu yerine kullanıcının gördüğü workbook türlerinden kısa bir dinamik katalog verilebilir.
  - 1×1 sınırı için küçük bir sonuç tablosu planı yazılabilir.

---

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (ADT-4). Okunan: Çekirdek (Ç-15, Ç-16, Ç-17), 01 Ürün (Ü-3, Ü-8), 02 Teknik (T-4, T-5, T-9)
Ürün etiketi      : Ürün 1 — T-11 (Excel yolu P2 bayrağı altında; proje ayrımı ve B-01 mevcut yolu düzeltir, yeni yetenek değil)
Kritik Geliştirme Kararı : Ç-15/3 (Excel aday kümesinin daraltılması — erişim kuralına komşu, yetki kümesinin içinden) ve Ç-15/8 (router + planlayıcı promptu, §6). Plan sunuldu, onay bekleniyor (T-9). Ç-15/4 yok (şema değişmiyor).
Gizli bilgi / yeni bağımlılık : Yok — T-14
Kapsam dışı değişiklik        : Yok — kod/prompt/ayar/şema/puanlayıcı/soru seti/canlı servis dokunulmadı; yalnız bu plan dosyası
Kendi başına verilen kararlar : (1) "21 Excel sorusu" için yazılı liste bulunamadı; S3/M1/N1'de DATA/MIXED'e giden 20 soru ölçü kümesi alındı (§2). (2) Ölçüm, eval DB'nin dışa aktarılmış audit satırlarıyla yapıldı (logs/*_audit.jsonl); eval konteyneri açılmadı. (3) Hesap motoru yerelde seed dosyalarıyla, LLM'siz ve DB'siz çalıştırıldı (§1.3). (4) Madde 12'nin özgün metni bulunamadı; atıflardan yeniden kuruldu (§3.2a). (5) B-01 için kontrolörün 3 sorusu questions.json'a eklenmeyecek, ayrı liste olarak ölçülecek (§8) — Ç-9
```
