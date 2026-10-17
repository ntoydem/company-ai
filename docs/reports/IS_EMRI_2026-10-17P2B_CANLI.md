# İş Emri 2026-10-17P2B_CANLI — P2 commit 2 (B-01, ADR-037) canlıya alma ve geri alma (Ç-15/6)

**Tarih:** 17.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` · **Ürün 1**

**Dayanak:**
- Naci 17.10.2026 açık onayı (Ç-15/6): "P2B'yi canlıya al, smoke 9/9 ile".
- Tansu PR #61 madde 7: commit 2, commit 1 canlıdayken çıkabilir.
- Ç-15/8 onay kanıtı: PR #61 madde 7.
- Kapsam: kod `da3dd08` + rapor `4c44c95`. Yalnız backend yeniden başlatması; veri, şema ve ayar değişikliği yok. Router ve planlayıcı promptları değişiyor.
- Komutlar: `IS_EMRI_2026-10-17P2B.md` §8, aynen uygulandı.

## 1. Sonuç

**Canlıya alındı. Smoke iki koşuda 8/9 ve 7/9 çıktı. Dur koşulu tetiklendi, Naci'ye bildirildi. Naci'nin kararıyla geri alındı. Geri almadan sonra smoke 9/9.**
- Ek kontrol soruları (emir adım 4) **koşulmadı**. Smoke düştüğü için durdum.
- Smoke'un dokuz cevabının hiçbirinde **başka projenin rakamı dönmedi**. Düşen üç satırın kaynakları ve Excel dosyaları yalnız Karatepe'ye (`ANK_RES`) aitti.
- Kod düzeltmesi **yapılmadı** (emir). P2B kodu dalda geri alındı (`faedc84`). ADR-037 ve P2B raporu tarih olarak kalıyor.

| Zaman (UTC) | Olay |
|---|---|
| 14:47:29 | Önce-durum (yalnız SELECT) |
| 14:47:33–45 | `make restart-backend` (P2B kodu), `/health` ok |
| 14:47 | smoke 1. koşu: **8/9** (g düştü) |
| 14:49 | smoke 2. koşu: **7/9** (a, b düştü) → DUR, bildirildi |
| 15:01 | Naci: geri al. `git revert da3dd08` → `faedc84` |
| 15:02:05 | `make restart-backend` (P2A kodu), `/health` ok |
| 15:02 | smoke: **9/9** |

## 2. Başlangıç

| | |
|---|---|
| Dal / HEAD | `4c44c95` (üstünde `da3dd08`). `git status --short` yalnız `?? logs/` |
| Canlı backend, önce | imaj `sha256:9ac73489e7d3…`, StartedAt `2026-10-17T12:53:08Z` (P2A_CANLI), healthy |
| Canlı DB, önce (14:47:29Z) | documents **113**, document_chunks 461, audit_log **1680**, alembic **0016** |

audit_log P2A_CANLI sonunda 1676'ydı. Aradaki +4 başka kullanımdan geliyor.

Yeniden başlatma: 14:47:33 → 14:47:45 (12 sn). Aynı imaj (`--build` yok), StartedAt `14:47:34Z`, `/health` → `{"status":"ok","version":"0.1.0","database":"ok"}`. `Running upgrade` satırı ve gerçek hata satırı yok; yalnız `uvicorn.error` logger adlı INFO satırları var.

## 3. Smoke koşuları (P2B kodu)

| # | user | 1. koşu (14:47) | 2. koşu (14:49) |
|---|---|---|---|
| a | finans | MIXED ✅ | MIXED ❌ `value '13.600.000' not in Excel part` |
| b | finans_mudur | MIXED ✅ | MIXED ❌ `value '13.600.000 USD' not in Excel part` |
| c | admin | DOCUMENT ✅ | DOCUMENT ✅ |
| d | enerji | DOCUMENT ✅ | DOCUMENT ✅ |
| e | finans | DOCUMENT ✅ | DOCUMENT ✅ |
| f | yonetim | DOCUMENT ✅ | DOCUMENT ✅ |
| g | finans | MIXED ❌ `value '11.671.800' not in Excel part` | MIXED ✅ |
| h | finans | DOCUMENT ✅ | DOCUMENT ✅ |
| i | enerji | DOCUMENT ✅ | DOCUMENT ✅ |
| | | **8/9** | **7/9** |

Ham çıktı: `logs/smoke_20261017-1447_*.json`, `logs/smoke_20261017-1449_*.json` (`logs/` izlenmiyor).

**b'nin router kararı:** b ("Karatepe RES kredi sözleşmesine göre fiilen kullandırılan toplam kredi tutarı kaç USD?") P2B kodunda iki koşuda da MIXED'e gitti. P2A_CANLI'da (12:53) ve geri almadan sonra (15:02) DOCUMENT_QUERY idi. Bu bir gözlem; tek bir soruda dört koşudur, ölçü değildir.

### 3.1 g — 1. koşu: "Karatepe için bankaya hâlâ ne kadar borcumuz var?" (beklenen Excel değeri 11.671.800)

**Router çıktısı** (backend logu, `request_id 313d95a0…`, 14:48:38Z):
- `query_type`: **MIXED_QUERY**
- `reason`: *"Outstanding balance depends on the agreed loan amount stated in the agreement plus the **repayment schedule rows** (paid vs remaining principal) in the workbook"*
- `document_question`: "Karatepe RES finansman sözle…" (kayıt burada kesik, bkz. not)
- `data_question`: kesik. Planlayıcının çıktısına bakılırsa "ödenmiş ve kalan anapara" diye yeniden yazılmış. Bu çıkarımdır, metnin kendisi kayıtta yok.

**Planlayıcı** (`excel sql result not scalar`, attempt 1, rows 1, columns `["paid_principal_usd", "remaining_principal_usd"]`):
```
SELECT (SELECT SUM(principal_usd) FROM financial_model_2026__debt WHERE end_date <= DATE '2026-10-06') AS paid_principal_usd, (SELECT closin…
```
- Sonuç 1 satır × **2 sütun**, yani tek değer değil (ADR-011). Yeniden plan yapıldı.
- İkinci planın sonucu 1×1 idi: **1.928.200**. Cevap modeli bu değeri "ödenmiş mi kalan mı belirsiz" diye yazdı.
- Değer Karatepe'nin kendi Debt sayfasından (`Financial_Model_2026.xlsx Debt!A2:H26`) geliyor, ama **yanlış sütundan**: kalan bakiye değil, ödenmiş anapara toplamına benziyor. 13.600.000 − 11.671.800 = 1.928.200.

**Not:** Router ve planlayıcı satırları, durma anında aldığım log çıktısından. O çıktı 420 karakterde kesilmişti. Backend container'ı geri almada yeniden yaratıldığı için logun tamamı artık yok. audit_log router alanlarını tutmuyor. Yukarıdaki kesik kısımlar bu yüzden tamamlanamadı.

Cevap metni (tam):
> Belgelere göre:
> Güncel belge olan Facility Agreement Amendment 02 [K32] kredi tutarı ve geri ödeme koşullarını içermiyor. Aşağıdaki değerler zincirdeki önceki belgelerden alınmıştır.
>
> Toplam finansman tutarı 14.000.000 USD'dir ve tamamı Garanti BBVA tarafından yerel banka olarak sağlanmıştır; yapıda ayrı bir ihracat kredi kuruluşu (ECA) tranşı yoktur [K44].
>
> Cari kapsam raporunda kullanılan (utilised) toplam kredi tutarı 13.600.000 USD, kredi kapsamındaki güncel bakiye ise 11.671.800 USD olarak ayrı ayrı belirtilmiştir [K25].
>
> Geri ödeme planı, 10 ayın sona ermesinin ardından başlar [K48]. Kredinin toplam vadesi 13 yıl olarak tanımlanmıştır [K48]. Erken geri ödeme, Garanti BBVA'ya önceden bildirilmek kaydıyla Karatepe RES Enerji Üretim A.Ş. için mümkündür; isteğe bağlı erken ödemede standart idari inceleme uygulanır [K48].
>
> Excel verisine göre:
> Soruda hem ödenmiş hem kalan anapara bakiyesi istenmiş, ancak verilen sonuç tek bir değer (1.928.200) olduğu için hangisine karşılık geldiği belirtilemiyor; bu nedenle her iki bakiyeyi ayrı ayrı yazamıyorum. Hesaplanan değer 1.928.200 olarak kaydedilmiştir, ancak bunun ödenmiş mi yoksa kalan anapara mı olduğu kaynaktan teyit edilmelidir.

Kaynaklar: Facility Agreement Amendment 02, Facility Agreement, Covenant Compliance Report Q2 2026 (hepsi `ANK_RES`). Excel: `Financial_Model_2026.xlsx Debt!A2:H26`.

### 3.2 a — 2. koşu: "Karatepe RES kredisinde fiilen kullandırılan toplam tutar nedir?" (beklenen Excel değeri 13.600.000)

Router: MIXED (gerekçe: *"contractual facility amount from the agreement vs. actually drawn amount from workbook records"*). Excel kaynağı yok, Excel yarısı "bulamadım". 1. koşuda aynı soru Excel'den 13.600.000 vermişti (`Debt!A2:H26`). Belge yarısında 13.600.000 var; smoke değeri Excel yarısında arıyor.

> Belgelere göre:
> Kaynaklarda kredinin toplam tutarı **14.000.000 USD** olarak yazılmıştır [K48]. Bu tutar, "Facility Agreement" belgesinin (DOC-ANK-FIN-004, 20.06.2022) 2. maddesinde "total financial accommodation" olarak geçer. Bu belge güncel değildir (Superseded); güncel Facility Agreement Amendment 02 belgesinde (K32, K33) tutar yer almadığından değer, zincirdeki önceki belgeden alınmıştır.
>
> Güncel Covenant Compliance Report Q2 2026 belgesinde kullanılan (utilised) toplam tutar 13.600.000 USD olarak yazılmıştır [K27]. Bu rakam kullanılan tutardır ve belgede taahhüt edilen tutar olarak belirtilmemiştir.
>
> Excel verisine göre:
> Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.

### 3.3 b — 2. koşu: "Karatepe RES kredi sözleşmesine göre fiilen kullandırılan toplam kredi tutarı kaç USD?" (beklenen Excel değeri 13.600.000 USD)

Router: MIXED (gerekçe: *"contractual facility amount in the agreement vs. actual drawn amount in the workbook"*). Excel kaynağı yok, Excel yarısı "bulamadım". 1. koşuda Excel'den 13.600.000 USD vermişti.

> Belgelere göre:
> Kredi tutarı: Toplam finansman tutarı 14.000.000 USD olarak yapılandırılmıştır. Tüm finansman Garanti BBVA tarafından yerel banka olarak sağlanmaktadır ve ayrı bir ihracat kredi kuruluşu (ECA) dilimi yoktur [K48]. Amendment 02 bu tutarı değiştirmemekte, orijinal koşulların yürürlükte kaldığını belirtmektedir [K31][K32].
>
> Kredi kapsamında kullandırılan tutar: Covenant Compliance Report Q2 2026'da toplam kullandırılan (utilised) tutar 13.600.000 USD, güncel bakiye 11.671.800 USD olarak yazılmıştır [K24].
>
> Kullandırım koşulları:
> Kullanım, koşulların (conditions precedent) yerine getirilmesine bağlıdır; yasal görüşler ve kurumsal yetkilendirmeler 20.06.2022 tarihinden önce teslim edilmelidir ve finansal kapanış 08.07.2022 için planlanmıştır [K53]. Her kullandırım tarihinde yapılan beyanlar tekrarlanmış sayılır [K49].
>
> Birinci dilim (Tranche 1): Kullandırım talep belgesinde, tüm koşulların 15.07.2022 itibarıyla yerine getirildiği teyit edilmiş ve 8.000.000 USD tutarındaki dilimin 15.07.2022'de kullandırılması talep edilmiştir [K11]. Bu tutar Karatepe RES Enerji Üretim A.Ş.'nin belirlenmiş banka hesabına doğrudan transfer edilecek ve transfer 15.07.2022 tarihinde iş bitimine kadar tamamlanacaktır [K29].
>
> Excel verisine göre:
> Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.

Kaynaklar: Facility Agreement, Facility Agreement Amendment 02, Covenant Compliance Report Q2 2026, Karatepe RES Drawdown Notice — Tranche 1 (hepsi `ANK_RES`).

## 4. Geri alma

Naci'nin kararı ("geri al + rapor", 17.10.2026 oturum içi). Ayrı bir revert commit'i atıldı:

```bash
git revert --no-edit da3dd08        # → faedc84 (12 dosya, P2B kod/test/ADR/prompt kopyası/results/p2b geri)
make restart-backend                # 15:02:05Z, aynı imaj, migrasyon yok
curl -fsS http://localhost:8080/health   # {"status":"ok","version":"0.1.0","database":"ok"}
python3 scripts/smoke_live.py       # 9/9
```

Geri almadan sonra smoke (15:02, ilk koşu, exit 0):

| # | user | http | type | answered | s | sonuç |
|---|---|---|---|---|---|---|
| a | finans | 200 | MIXED_QUERY | True | 17.6 | ✅ |
| b | finans_mudur | 200 | DOCUMENT_QUERY | True | 6.2 | ✅ |
| c | admin | 200 | DOCUMENT_QUERY | True | 3.8 | ✅ |
| d | enerji | 200 | DOCUMENT_QUERY | False | 1.0 | ✅ |
| e | finans | 200 | DOCUMENT_QUERY | False | 0.0 | ✅ |
| f | yonetim | 200 | DOCUMENT_QUERY | False | 0.1 | ✅ |
| g | finans | 200 | MIXED_QUERY | True | 24.6 | ✅ |
| h | finans | 200 | DOCUMENT_QUERY | True | 2.3 | ✅ |
| i | enerji | 200 | DOCUMENT_QUERY | False | 0.0 | ✅ |

**9/9 geçti.** Ham çıktı `logs/smoke_20261017-1502_*.json`.

Canlı kod şimdi P2A (`1f9ac13`, ADR-036) durumunda. Dal HEAD'i bu rapor commit'i; altında `faedc84` (revert).

## 5. Şüpheliler — KANIT DEĞİL, HİPOTEZ

P2B'de canlı LLM yoluna üç değişiklik girdi. Hangisinin (ya da model dalgalanmasının) sebep olduğu **ölçülmeden belli değil**:

1. **Yeni ROUTER cümlesi** (Excel tanımındaki "loan repayment schedules" ve DATA_QUERY'deki "a value read from a repayment schedule row …").
   - Lehine: g'nin router gerekçesi doğrudan "repayment schedule rows (paid vs remaining principal)" diyor. Veri sorusu "ödenmiş + kalan" diye bölünmüş, bu da iki sütunlu plana yol açmış.
   - Lehine: b P2B'de iki kez MIXED, öncesinde ve sonrasında DOCUMENT.
   - Karatepe'nin ödeme planı workbook'u yok. Model Debt sayfasını "ödeme planı" gibi okumuş olabilir.
2. **PLAN cümlesi** ("Use the current version of a workbook; use a superseded one only when …"). a/b'nin 2. koşusunda Excel yarısı "bulamadım" dedi. Planlayıcı `none` döndürmüş olabilir; plan logu tam elde yok.
3. **Katalog satırına eklenen `project` / `status` alanları.** Planlayıcının gördüğü metni değiştirdi; Karatepe satırları artık `project: Karatepe RES, status: …` taşıyor.

Başlık satırı değişikliği (`calc.py`) bu listede değil: Karatepe'nin 19 tablosu testle ve eval DB'de birebir aynıydı (P2B raporu §4.1 test 1, §5.1). Yine de canlıda ayrıca ölçülmedi.

Ayırt etmek için gereken ölçü (bu emirde yok, ayrı emir ve onay ister): aynı smoke soruları (a, b, g), her biri birkaç kez, eval ortamında (1) yalnız router cümlesi, (2) yalnız PLAN cümlesi, (3) yalnız katalog alanları açıkken. Router kararı ve plan logu tam kaydedilir.

## 6. Proje karışması

**Başka projenin rakamı dönmedi.**
- Üç smoke koşusunun 27 satırında Excel kaynağı yalnız `Financial_Model_2026.xlsx` (Karatepe), o da yalnız Karatepe sorularında.
- Düşen satırların (g, a, b) belge kaynaklarının hepsi `ANK_RES`.
- Ek kontrol soruları (P2A tekrarı, B-01 örnekleri, router yan etki) koşulmadı. Bu yüzden Yeşilova/Boztepe Excel soruları canlıda ölçülmedi.

## 7. audit_log

| | audit_log | documents | chunks | alembic |
|---|---|---|---|---|
| Önce (14:47:29Z) | 1680 | 113 | 461 | 0016 |
| Durma anı (14:50:37Z) | 1698 (+18 = iki smoke koşusu) | 113 | 461 | 0016 |
| Geri almadan sonra (15:03:31Z) | **1707** (+27 toplam = üç smoke koşusu) | 113 | 461 | 0016 |

Veri, migrasyon ve `.env` değişmedi.

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (+ ADT-4). Okunan: Çekirdek (Ç-15/6, Ç-15/8, Ç-16); P2B raporu §8; P2A_CANLI yöntemi
Ürün etiketi      : Ürün 1 — T-11 (mevcut Excel yolunun düzeltilmesi; projeler ayrı)
Ç-15/6 onay kanıtı: Naci 17.10.2026 "P2B'yi canlıya al, smoke 9/9 ile" (da3dd08 + 4c44c95, yalnız
  backend yeniden başlatması); Tansu PR #61 madde 7. Ç-15/8 onay kanıtı: PR #61 madde 7
Şartlar           : geri alma planı hazırdı ✓; smoke 9/9 ✗ (8/9, 7/9) → emir gereği DUR ve bildirildi,
  kendi başıma geri alınmadı; geri alma Naci'nin açık kararıyla yapıldı (oturum içi, 17.10.2026),
  sonra smoke 9/9 ✓; migrasyon yok ✓
Gizli bilgi / yeni bağımlılık : Yok — .env okunup değiştirilmedi; parolalar smoke_live içinde,
  yazdırılmadı; yeni paket yok; imaj yeniden kurulmadı
Kapsam dışı değişiklik : Yok — canlıda yalnız backend container'ı iki kez yeniden yaratıldı. DB'ye
  yazan tek şey üç smoke koşusunun 27 audit satırı. Kod DÜZELTİLMEDİ (emir); yalnız Naci onaylı
  revert commit'i (faedc84) ve bu rapor. Ek kontrol soruları (emir adım 4) dur koşulu yüzünden
  koşulmadı. Ham çıktılar logs/ altında, izlenmiyor
Dur koşulları     : TETİKLENDİ — smoke 2. koşuda da 9/9 değil (7/9); başka projenin rakamı dönmedi
Kendi başına verilen kararlar :
  1. Naci'nin "geri alma tamam ise" mesajı koşula bağlıydı ve geri alma henüz yapılmamıştı; geri alma
     canlıyı etkilediği için önce soruldu, "Evet, geri al + rapor" cevabıyla yapıldı
  2. Revert ayrı commit (faedc84); emirdeki "yalnız raporu commit et" bu raporun commit'i için
  3. Router/planlayıcı ayrıntıları durma anında alınan kesik log çıktısından; logun tamamı container
     yeniden yaratılınca kayboldu (§3.1 not)
  4. Şüpheliler hipotez olarak yazıldı; sebep ölçülmedi (§5)
```
