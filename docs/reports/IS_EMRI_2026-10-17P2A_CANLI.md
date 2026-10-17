# İş Emri 2026-10-17P2A_CANLI — P2 commit 1 (Excel proje ayrımı, ADR-036) canlıya alma (Ç-15/6)

**Tarih:** 17.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `b73b750`) · **Ürün 1**

**Dayanak:** Naci 17.10.2026 açık onayı (Ç-15/6); Tansu PR #61 madde 7 (commit 1 tek başına canlıya
çıkabilir). Kapsam:
- kod commit'i `1f9ac13` ve rapor `b73b750`;
- yalnız backend yeniden başlatması;
- veri, şema, ayar ve prompt değişikliği yok.
- Commit 2 (B-01) bu emirde **yok**; canlıya alınmadı.

Komutlar: `docs/reports/IS_EMRI_2026-10-17P2A.md` §8 ve P1K_CANLI yöntemi, aynen uygulandı.

**Sonuç:** başarılı.
- Smoke **9/9** ilk koşuda geçti; yeniden koşu gerekmedi.
- Üç kontrol sorusu **3/3**: Yeşilova ve Boztepe cevabında Karatepe rakamı yok, Karatepe aynı kaldı.
- Geri alma gerekmedi.

## 1. Başlangıç (adım 1–2)

| | |
|---|---|
| Dal / HEAD | `feat/adim5-veri-kutuphanesi`, `b73b750` (üstünde `1f9ac13`). `git status --short` yalnız `?? logs/` |
| Canlı backend, önce | imaj `company-ai-backend` `sha256:9ac73489e7d3…`, **StartedAt 2026-10-17T11:22:02Z** (P1K_CANLI), healthy. Kod `./backend` bind-mount'tan, `--reload` yok; yani P2A kodu bu süreçte henüz yüklü değildi |
| Canlı DB, önce (yalnız SELECT, 12:53:04Z) | `company_ai`: documents **113**, document_chunks 461, audit_log **1664**, alembic **0016** |

audit_log 1664, P1K_CANLI sonundaki değerle aynı; aradan başka kullanım geçmemiş.

## 2. Yeniden başlatma (adım 3)

```
make restart-backend        # 12:53:07 → 12:53:19 UTC (12 s)
hazır: http://localhost:8080/health -> {"status":"ok","version":"0.1.0","database":"ok"}
```

- **Sonra:** aynı imaj (`sha256:9ac73489e7d3…`, `--build` yok), **StartedAt 2026-10-17T12:53:08Z**.
- `Running upgrade` ve ERROR satırı 0; migrasyon 0016'da kaldı.
- `.env` değişmedi.

## 3. smoke_live (adım 4)

`python3 scripts/smoke_live.py`, ilk koşu (12:53 UTC), exit 0:

| # | user | http | type | answered | s | sonuç |
|---|---|---|---|---|---|---|
| a | finans | 200 | MIXED_QUERY | True | 16.3 | ✅ |
| b | finans_mudur | 200 | DOCUMENT_QUERY | True | 6.3 | ✅ |
| c | admin | 200 | DOCUMENT_QUERY | True | 2.6 | ✅ |
| d | enerji | 200 | DOCUMENT_QUERY | False | 0.9 | ✅ |
| e | finans | 200 | DOCUMENT_QUERY | False | 0.0 | ✅ |
| f | yonetim | 200 | DOCUMENT_QUERY | False | 0.1 | ✅ |
| g | finans | 200 | MIXED_QUERY | True | 25.4 | ✅ |
| h | finans | 200 | DOCUMENT_QUERY | True | 2.8 | ✅ |
| i | enerji | 200 | DOCUMENT_QUERY | False | 0.0 | ✅ |

**9/9 geçti.** Ham çıktı `logs/smoke_20261017-1253_*.json` (`logs/` izlenmiyor).

## 4. Kontrol soruları (adım 5)

Yöntem P1K_CANLI ile aynı: `smoke_live.py --spec` ile üç soruluk geçici bir dosya (scratchpad, repoya
girmedi), kullanıcı `finans`, gerçek planlayıcı. Beklentiler:
- j, k: `response_excludes` (`11.671.800`, `1,37`);
- l: `contains` (`11.671.800`).

Sonuç **3/3**, exit 0. Ham çıktı `logs/smoke_20261017-1254_{j,k,l}.json`. Üçü de `MIXED_QUERY`,
`answered=true`, model `claude-haiku-5-5`.

### a) "Yeşilova RES'in kalan kredi borcu ne kadar?" → 11.671.800 geçmemeli: ✅

Kaynaklar: Yeşilova RES Facility Agreement (2023-YS) s.3, s.4; Taksit #11 Banka Faiz Bildirimi s.2, s.3
(hepsi `YSV_RES`).

> Belgelere göre:
> Kredi tutarı 2.352.000 USD'dir ve 03.06.2023 tarihli sözleşmeyle kullandırılmıştır [K3]. Uygulanacak marj %1,5'tir [K3].
>
> Geri ödeme takvimi eşit anapara esasına göre belirlenmiştir: üç aylık dönemlerle 24 taksit halinde, her taksit 98.000 USD anapara olarak ödenir [K14].
>
> Faiz tutarı her taksit için ayrıca bildirilir. 14.10.2026 vadeli taksit için uygulanacak faiz tutarı Commerzbank AG tarafından 18.912 USD olarak bildirilmiştir [K4]. Bu tutar Commerzbank AG'nin kendi hesaplamasına dayanmaktadır; ödeme planındaki tutarla karşılaştırılması Yeşilova RES Enerji Üretim A.Ş.'in sorumluluğundadır [K15].
>
> Borçlu her geri ödemeyi, yürürlükteki sözleşmede öngörülen tarihlerde ve biçimde yapar [K14]. Ödeme tarihlerinin ve biçiminin kendisi kaynaklarda yer almamaktadır. Yukarıda belirtilen profilin kapsamadığı geri ödeme konuları genel hükümlere tabidir [K14]; bu genel hükümler kaynaklarda yer almamaktadır.
>
> Borç Servis Rezerv Hesabı (DSRA) bakiyesi sabit 702.000 USD olup altı dönemlik borç servisine eşittir [K3].
>
> Excel verisine göre:
> Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.

Excel yarısı artık Karatepe'nin 11.671.800 USD'sini vermiyor; Yeşilova'ya ait Excel olmadığı için
"bulamadım" diyor. Belge yarısı yalnız Yeşilova kaynaklarından.

### b) "Boztepe RES'in güncel DSCR değeri kaç?" → 1,37 geçmemeli: ✅

Kaynaklar: Boztepe RES Facility Agreement (2024-BZ) s.5; Boztepe RES — Covenant Compliance Report
Q3 2026 s.3 (ikisi de `BOZ_RES`).

> Belgelere göre:
> Kredi sözleşmesinde minimum borç servis karşılama oranı (DSCR) 1,20x olarak belirtilmiştir [K6]. Covenant Compliance Report Q3 2026 da uygulanabilir minimum gereksinimi 1,20x olarak kaydetmektedir [K11].
>
> Excel verisine göre:
> Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.

Karatepe'nin 1,37x değeri dönmedi.

### c) "Karatepe RES'in kalan kredi borcu ne kadar?" → 11.671.800 geçmeli: ✅

Kaynaklar: Facility Agreement s.4, s.6; Covenant Compliance Report Q2 2026 s.4; Facility Agreement
Amendment 01 s.4; Facility Agreement Amendment 02 s.4 (hepsi `ANK_RES`).

> Belgelere göre:
> **Kredi tutarı:** Facility Agreement (20.06.2022) belgesinde toplam finansman tutarı 14.000.000 USD olarak yazılıyor ve tamamının Garanti BBVA tarafından yerel banka olarak sağlandığı belirtiliyor [K47]. Bu tutar güncel Facility Agreement Amendment 02 belgesinde geçmediği için geçerli değer olarak aktarılmıştır.
>
> Covenant Compliance Report Q2 2026 belgesinde ise kullandırılan (utilised) toplam tutar 13.600.000 USD ve raporlama tarihi itibarıyla kalan bakiye 11.671.800 USD olarak ayrı ayrı yazılmıştır [K26].
>
> **Geri ödeme koşulları:**
> - Vade 13 yıl olarak kesin biçimde tanımlanmıştır [K48].
> - Geri ödeme planı, 10 aylık sürenin sonunda başlar [K48].
> - Taksit yapısı, Facility Agreement Amendment 01 (12.01.2024) belgesinde "Sculpted (variable), semi-annual instalments after grace" olarak yazılmıştır [K51]. Bu değer güncel Amendment 02 belgesinde değiştirilmediği için geçerlidir; ancak Amendment 01 belgesinin durumu "superseded"dir.
> - Erken geri ödeme, Garanti BBVA'ya önceden bildirimle Karatepe RES Enerji Üretim A.Ş. tarafından yapılabilir. İsteğe bağlı erken ödemede standart idari inceleme uygulanır [K48].
>
> **Faiz marjı:** Facility Agreement (20.06.2022) belgesinde faiz, baz endeks üzerine %3.25 olarak yazılmıştır [K47]. Bu değer Facility Agreement Amendment 02 ile önceki %3.25 seviyesinden değiştirilmiş ve marj %2.9 olarak belirlenmiştir [K32].
>
> Excel verisine göre:
> Karatepe RES için kalan kredi borcu (anapara bakiyesi), 06.10.2026 tarihli çalışma kitabı görüntüsü itibarıyla 11.671.800 USD'dir.

Karatepe Excel yarısı değişmedi: 11.671.800 USD.

**Not (bu emrin kapsamı dışı, dokunulmadı):** c'nin belge yarısında `%3.25` / `%2.9` ondalık
noktayla yazılmış (F-8'e aykırı). Bu LLM metni; P2A Excel yolunu değiştirdi, belge yarısına
dokunmadı.

## 5. audit_log

| | audit_log | documents | alembic |
|---|---|---|---|
| Önce (12:53:04Z) | 1664 | 113 | 0016 |
| Sonra (12:55:20Z) | **1676** (+12) | 113 | 0016 |

- **+12 satır:** smoke 9 + kontrol 3; hepsi `error` NULL.
- Model alanı: 9 satırda `claude-haiku-5-5` (a, b, c, d, g, h, j, k, l); 3 satırda NULL (e, f, i, yani kod yolları).
- Backend logunda 12:53'ten sonra WARNING/ERROR 0.

## 6. Geri alma (gerekmedi; yazılı)

Yalnız kod geri alınır. Veri, migrasyon ve `.env` değişmedi.

```bash
cd ~/company-ai
git revert --no-edit 1f9ac13               # rapor commit'leri kalabilir
make restart-backend                       # ~12 s
curl -fsS http://localhost:8080/health
python3 scripts/smoke_live.py              # 9/9
```

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (+ ADT-4). Okunan: Çekirdek (Ç-15/6, Ç-16); P2A raporu §8; P1K_CANLI yöntemi;
  Tansu PR #61 madde 7 (emirdeki metin)
Ürün etiketi      : Ürün 1 — T-11 (mevcut Excel yolunun düzeltilmesi; projeler ayrı)
Ç-15/6 onay kanıtı: Naci 17.10.2026 açık canlıya alma onayı (1f9ac13 + b73b750; yalnız backend
  yeniden başlatması). Şartlar: geri alma planı (§6) ✓, smoke 9/9 ✓ (ilk koşu), migrasyon yok ✓
Gizli bilgi / yeni bağımlılık : Yok — .env okunup değiştirilmedi (parolalar smoke_live içinde,
  yazdırılmadı; psql kullanıcı adı .env'den); yeni paket yok; imaj yeniden kurulmadı
Kapsam dışı değişiklik : Yok — canlıda yalnız backend container'ı yeniden yaratıldı. DB'ye yazan tek
  şey smoke + kontrol sorularının kendi 12 audit satırı. Kod, şema, ayar, prompt, veri, eval ortamı
  dokunulmadı. Commit 2 (B-01) canlıya alınmadı. Git'te yalnız bu rapor (ham çıktılar logs/ altında,
  izlenmiyor)
Dur koşulları     : tetiklenmedi — /health ok, smoke 9/9 ilk koşuda, a/b'de Karatepe rakamı yok,
  c'de 11.671.800 var
Kendi başına verilen kararlar :
  1. Kontrol soruları smoke_live.py --spec ile soruldu (finans, aynı giriş yöntemi); spec scratchpad'de,
     repoya girmedi
  2. "Geçmemeli" response_excludes ile (tüm yanıt gövdesi), "geçmeli" contains ile kontrol edildi;
     cevap metinleri ayrıca ham JSON'dan okunup bu rapora aynen kondu
  3. c'deki %3.25 / %2.9 (F-8) gözlemi yalnız not edildi; kapsam dışı
```
