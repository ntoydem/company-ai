# Adım 5 — T-11 Etki Raporu (Tansu'nun cevapları, henüz işlenmedi)

**Tarih:** 11.10.2026 · **Durum:** yalnızca araştırma/etki raporu — **hiçbir ledger/kod/belge değiştirilmedi** · **Kaynak:** `ftansu/AI-BalBal`, branch `docs/naci-sorular-3-2026-10-10`, dosya `docs/SORULAR_NACIDEN_3-2026-10-10.md` (son commit `85d93ee`; Tansu'nun cevapları `2a4e48f`) · **Canlı DB/Gemini çağrısı yok, main'e merge yok, bayraklar (EK_F_MODE/ASSIST_MODE) kapalı.**

Bu rapor **uygulama değil** — Tansu'nun T-11 cevaplarını ledger'a işlemeden önce etkiyi, çelişkileri ve açık kararları ortaya çıkarmak için yazıldı. Her bulgu gerçek bir `grep`/dosya taramasıyla doğrulandı; tahmin edilen hiçbir sayı yok — bulunamayan yerler açıkça "bulunamadı" diye işaretlendi.

---

## 1. Tansu'nun 6 sorusuna cevap

### (1) Karatepe EPC 41.500.000 EUR → 14.500.000 EUR

- **Etkilenen ledger alanı:** tek bir alan — `project.construction.epc_contract_price.value` (`seed_data/master/ankara_res.yaml:181`). Hakediş, taksit, fatura gibi EPC'ye bağlı ayrı bir ödeme/tahsilat alanı Karatepe'nin ledger'ında **hiç yok** (`grep -in "hakediş|progress payment|epc.*invoice|epc.*payment|epc.*instalment"` → 0 sonuç). Hakediş kavramı bu depoda yalnız Kızılova'da var, Karatepe'de modellenmedi.
- **Etkilenen belgeler:** tek belge — **`DOC-ANK-EPC-001`** (EPC Contract). `key_facts: {epc_contract_price: ...}` bu değeri `[[epc_contract_price]]` token'ı ile çözüyor. Belge **LLM prose** (model: gemini-3.5-flash-lite) ama **`hand_edited` DEĞİL** — token otomatik güncellenir, elle prose düzenlemesi gerekmez, LLM çağrısı da gerekmez (token zaten donmuş metne `generate_documents.py` tarafından enjekte ediliyor).
- **Etkilenen eval sorusu:** tek soru — **`ANK-EPC-001`** ("Karatepe RES EPC sözleşme bedeli nedir?"). `resolve_expected` ledger'dan canlı okuduğu için otomatik çözülür, soru dosyasında değişiklik gerekmez.
- **Validator etkisi:** `epc_contract_price` hiçbir F-kuralıyla `capex`'e bağlı değil (M2 yalnız *currency*'yi — EUR'da kalmasını — kontrol ediyor, `validate_ledger.py:632`); değer değişikliği tek başına hiçbir hata/uyarı üretmiyor.

### (2) Karatepe kredi tarihleri 2021 → 2022 (imza 20.06.2022, FC 08.07.2022)

**Tüm tarih alanları (`ankara_res.yaml:37-40`):**
| Alan | Şu an | Tansu'nun yeni değeri |
|---|---|---|
| `financing_signed` | 2021-11-20 (AI_ASSUMPTION) | 20.06.2022 |
| `financial_close` | 2021-11-25 (AI_ASSUMPTION) | 08.07.2022 |

**Bulunan gerçek çelişkiler (satır/belge koduyla):**

1. **KIRILACAK validator kuralı — `validate_ledger.py:303-316`, kod `C1`.** Karatepe timeline'ı şu **kesin sıra**yı zorunlu kılıyor: `development_start < licence < financing_signed < financial_close < construction_start < commissioning < cod_actual`. `construction_start` şu an **2022-01-10** (`ankara_res.yaml:40`, USER_FACT, değişmiyor). Yeni `financial_close` (08.07.2022) bundan **6 ay sonra** — sıra bozuluyor. Ledger'ın kendi yorumu (satır 34-35) bunu zaten önceden flagliyor: *"construction_start (2022-01-10) ile tutarlı olması için signed/close tarihleri construction_start'tan ÖNCEye alındı (C1 kuralı)"* — yani 2021 tarihleri **bilerek** bu kuralı geçmek için seçilmişti. Tansu'nun yeni tarihleri bu kuralı **doğrudan kırıyor** — `construction_start` da birlikte ileri alınmadan `make validate-ledger` hata verir: `C1: must be after financial_close`.
2. **Zaten bilinen, şimdi doğrulanan iç çelişki — `ankara_res.yaml:82` (`grace_months`).** Not metni zaten *"imza (2022-06-20) ve ilk taksit (2023-04-07) arasındaki boşluktan türetildi"* diyor — yani bu not, `timeline.financing_signed`'ın GERÇEK değerinden (2021-11-20) bağımsız olarak, kodun imza yılını (2022-KT) kullanmıştı. Tansu'nun cevabı bu notu şimdi **tutarlı** kılıyor (T-11.2 cevabının kendisi de bunu söylüyor: *"2021 varsayımı... T-11.15 notuyla çelişiyor"*).
3. **Facility chain belge tarihleri — `DOC-ANK-FIN-001..004` (`ankara_res.yaml:275,297,319,341` civarı).** Bu 4 belgenin kendi `document_date`/`effective_date` alanları (sırasıyla 2021-06-15, 2021-07-20, 2021-08-25, 2021-11-20) **hardcoded** — `financing_signed`'dan otomatik türemiyor. Tarihler 2022'ye kaymazsa belge tarihleriyle ledger tarihi arasında uyumsuzluk kalır.
4. **Sıra çelişkisi YOK (doğrulandı):** ilk kullanım (drawdown #1, `ankara_res.yaml:91`) = **2022-07-15**, Tansu'nun *"ilk kullanım 15.07.2022"* notuyla **birebir eşleşiyor** — bu alan hiç değişmedi, zaten uyumlu. Tadil (AMD01 `DOC-ANK-FIN-005`, 2024-01-12) ve Waiver (`DOC-ANK-FIN-015`, 2025-01-20) ikisi de hem eski hem yeni finansman tarihinden **çok sonra** — çelişki yok.
5. **Faiz hesabı / ödeme planı / DSRA — çelişki YOK.** `debt_math.build_schedule`'ın girdileri (`drawdowns`, `repayment_schedule`, `base_rate_pct_by_year`, `margin_pct`) hiçbiri `financing_signed`/`financial_close`'a bağlı değil — kendi sabit tarihleriyle çalışıyor. DSRA (1.240.000 USD) statik bir bakiye, tarihe bağlı değil. **Hiçbiri etkilenmiyor.**
6. **"Canvas" ile çelişki:** AI-BalBal'ın kendi tasarım canvas'ı bu depoda yok — **bulunamadı**, kontrol edilemedi.

### (3) Boztepe KGF kefaletini çıkarmak

`grep -rln "KGF" .` (tüm repo) → **tek sonuç: `docs/reports/ADIM5_ASAMA_C_REPORT.md:44`** (kendi anlatı notum). Ledger'da (`boztepe_res.yaml`), hiçbir belgede, hiçbir eval sorusunda, hiçbir testte KGF'e dair **tek bir satır yok** — Aşama C'de bilerek modellenmemişti ("kendi kararı bekliyor" diye not edilmişti). **Çıkarınca teminat yapısında boşluk kalmıyor** çünkü zaten hiçbir teminat yapısı (KGF dahil) modellenmemişti — Boztepe'nin `finance` bloğu T-11.6-10'dan önce tamamen `pending`.

### (4) Yeşilova capex 26.400.000 / özkaynak 24.048.000 USD + 2023-YS kredisi + 22 MW + 5×4,4 MW

- **Aritmetik:** 26.400.000 − 2.352.000 = **24.048.000** — birebir (bkz. §2.4).
- **`check_finance` (F1/F2) Yeşilova'ya uygulanmıyor** — `validate_ledger.py:1085-1088`, bu fonksiyon yalnız `isinstance(ankara, ls.AnkaraLedger)` koşuluyla çağrılıyor; Yeşilova `OperatingLedger` kullanıyor, bu kurala hiç tabi değil. Yani "toplam = kredi + özkaynak" zorunluluğu kodda yok, ama Tansu'nun seçtiği sayılar **zaten tam uyuyor**.
- **Kapasite:** `capacity_mw.current = 22` (`yesilova_res.yaml`, zaten mevcut) — 5×4,4=22 ile **tutarlı**. Türbin adedi şu an ledger'da hiç yok (T-11.13 pending idi); 5 olarak yazılacak, çelişki yaratmıyor.
- **Taksitler:** Tansu "Canvas ve taksitler değişmez" diyor; 2023-YS kredisi (2.352.000 USD, 24×98.000) zaten ayrı ve küçük bir kredi olarak modellenmiş — capex/equity ile hiçbir alan paylaşmıyor. **Çelişki bulunamadı.**

### (5) İK asgari seti — Tur 1 öncesi takvim etkisi

- **ADIM5_PLAN'daki İK satırı (`docs/plans/ADIM5_PLAN.md:60-61,107,116,153`):** plan İK'yı parti sırasında **6. (son)** parti olarak koymuş ve miktarını "~36×12≈432 belge, büyük ek iş" olarak tahmin etmiş; §153'teki SORU 7 bunun Adım 5'e mi yoksa **Adım 6'ya** mı bırakılacağını soruyor, öneri Adım 6. Tansu'nun bu turdaki cevabı **asgari bir alt-küme** istiyor (432 değil) — SORU 7'nin kapsamını daraltıyor, iptal etmiyor.
- **Önerilen adım numarası:** parti sırası **değişmiyor** — İK zaten 6. (son) parti. Tansu da "Sıra aynı kalsın (İK sonda)" diyor. Tek fark: resmi Tur 1, tüm partiler (İK dahil) bitmeden başlamıyor (T-8 kararı) — bu zaten planın kendi mantığı, yeniden numaralandırma gerekmiyor.
- **Yapısal ön koşul (blocker, plan dışı bulgu):** `DepartmentSlug` Literal'ında (`ledger_schema.py:56-65`) **"İK" yok** — yalnız `enerji_grubu/enerji_gelistirme/enerji_epc_insaat/enerji_bakim/finans/hukuk/mali_isler/idari_isler`. Backend'in kendi departman seed listesinde de (`backend/app/services/demo_departments_seed.py:37-40`) **İK yok**. Herhangi bir İK belgesi üretilmeden önce bu iki yere İK departmanı eklenmesi **zorunlu** (küçük ama atlanabilecek bir ön koşul).
- **Kaç belge / kodla-LLM oranı:** asgari set — 36 kişilik liste (1), bordro özeti/restricted (1), izin belgeleri ("belgeler", temsili ~3), birkaç iş sözleşmesi örneği ("birkaç", ~3) ≈ **~8 belge** (kesin sayı "belgeler"/"birkaç" ifadeleri yorum payı bıraktığı için yaklaşık). ADIM5_PLAN'ın kendi tasarım kararı (§satır 61: *"kişi dosyaları şablonla, LLM'siz"*) zaten bunu **tamamı kodla** olarak öneriyor → **0 LLM çağrısı, kota etkisi sıfır**.
- **Kısıtlı belge/yetki etkisi:** bordro özeti `confidentiality: restricted` olacak (zaten mevcut bir seviye, şema değişikliği gerekmiyor); İK departmanına ait bir **demo kullanıcı** da gerekiyor (yetki sızıntısı testi İK kullanıcısı olmadan yapılamaz, Tansu'nun kendi gerekçesi).
- **Tahmini süre:** yeni departman + yeni belge türleri (Personnel List, Payroll Summary, Leave Document, Employment Contract) + 36 kişilik liste veri modeli tasarımı gerektiriyor — PF-1'in kodla kısmıyla kıyaslanabilir ölçekte yeni mühendislik işi. **Kaba tahmin: yarım gün–1 gün** (asıl değişken: 36 kişilik liste nerede/nasıl tutulacağı — yeni bir dosya mı, `company.yaml`'a mı eklenecek — bu rapor bu kararı almıyor, §4'te SORU olarak bırakıldı).

### (6) Boztepe faiz yapısı (%3,894 + %2,85 = %6,744) — mevcut başka bir oranla çakışıyor mu?

Boztepe'nin ledger'ında (`boztepe_res.yaml`) şu ana kadar **hiçbir oran alanı yoktu** — yalnız aylık faiz TUTARI (84.300 USD) ve 2 tarih vardı (T-11.7 "pending"). Boztepe'nin `documents: []` — **hiç belge üretilmedi** (PF-2 hâlâ bloke). Dolayısıyla çakışabilecek ne bir ledger alanı ne bir belge var — **çelişki bulunamadı**, yapı sıfırdan ekleniyor.

---

## 2. Aritmetik doğrulama (komut çıktısı)

```
$ python3 -c "
boztepe_interest = 15_000_000 * 0.06744 / 12
dsra = 6 * 84300
commitment = 30_000_000 * 0.0080 * 92 / 360
yesilova_equity = 26_400_000 - 2_352_000
karatepe_total = 13_600_000 + 6_400_000
print(round(boztepe_interest,2), dsra, round(commitment,4), yesilova_equity, karatepe_total)
"
84300.0 505800 61333.3333 24048000 20000000
```

1. **15.000.000 × %6,744 / 12 = 84.300,00** — ledger'daki aylık tutarla **birebir** eşleşiyor.
2. **DSRA 6 × 84.300 = 505.800** — Tansu'nun cevabıyla **birebir**.
3. **Kızılova taahhüt komisyonu:** ledger'daki not oranı **%0,80** diyor (`izmir_res.yaml:72`, serbest metin, ayrı bir yapılandırılmış alan yok — oran uydurulmadı, notta yazan kullanıldı). 30.000.000 × %0,80 × 92/360 = **61.333,33**; ledger'daki değer **61.333** (tam sayıya yuvarlanmış) — fark 0,33 USD, yuvarlama farkı, **tutarlı**.
   - Ek doğrulama: yeni imza tarihi (05.10.2026) → komisyon tarihi (05.01.2027) arası gün sayısı **tam 92 gün** (`date(2027,1,5)-date(2026,10,5)).days == 92`) — Tansu'nun *"92 gün üzerinden birebir çıkıyor"* iddiası **doğrulandı**.
4. **Yeşilova özkaynak = 26.400.000 − 2.352.000 = 24.048.000** — ledger'a yazılacak değerle **birebir**.
5. **Karatepe 13.600.000 + 6.400.000 = 20.000.000** — capex onayıyla **birebir**.
6. **Karatepe EPC 14.500.000 EUR için USD kuru:** **ledger'da VAR** — `seed_data/master/fx_rates.yaml` (uydurulmadı). EPC imza yılı (2021) ortalama kuru **EUR/USD = 1,1783**: 14.500.000 × 1,1783 = **17.085.350 USD** — Tansu'nun kendi *"~17 mn USD"* tahminiyle **birebir örtüşüyor** (muhtemelen aynı 2021 kurunu kullanmış). Karşılaştırma için 2026 kurlarıyla: yıllık ortalama (1,0858) → 15.744.100 USD; demo_today spot (1,0860, 15.09.2026) → 15.747.000 USD. **Üç kurun hiçbirinde** 20.000.000 USD'lik toplam yatırımı aşmıyor (kalan 2,9–4,3 mn USD aralığında, "geliştirme/şebeke/finansman maliyeti" için yeterli alan var).

---

## 3. İşaretleme önerisi — "ürün sahibi onaylı"

Mevcut sistem: `Tag = Literal["USER_FACT", "AI_ASSUMPTION"]` (`ledger_schema.py:15`). Tansu'nun istediği, Claude'un seçtiği ama Tansu'nun yazılı onayladığı değerleri (T-11.2 tarihleri, T-11.6-10 Boztepe yapısı, T-11.14 test sonuçları) ayırt edecek bir işaret.

**Seçenek A — yeni bir üçüncü tag değeri** (örn. `"PRODUCT_OWNER_APPROVED"`):
- Dokunulacak yerler (kesin, taranmış): `ledger_schema.py:15` (Literal'a ekleme), `validate_ledger.py:180` (`count_tags`) ve `validate_ledger.py:1127` (`--summary` CLI'nin kendi sayacı) — ikisi de şu an `{"USER_FACT": 0, "AI_ASSUMPTION": 0}` sözlüğü kullanıyor, üçüncü anahtar eklenmezse yeni tag **sessizce sayılmaz** (hata vermez, sadece `--summary` çıktısında görünmez). `validate_documents.py:109-110`'daki `AI_ASSUMPTION` kontrolü **ayrı bir kavram** (prose dosyasının kendi tag'i, LLM-mi-yazdı sorusu) — bundan etkilenmiyor.
- Artı: sorgulanabilir, raporda/arayüzde ayrı rozet olarak gösterilebilir.
- Eksi: şemanın çekirdeğine (her `Fact`/`Money`'e) yeni bir değer ekliyor; 3 yerde kod değişikliği.

**Seçenek B — `USER_FACT` + açıklayıcı not:**
- Değer artık Tansu'nun yazılı onayı olduğu için `tag: USER_FACT` kullanılır, `note:` alanına *"Ürün sahibi onaylı varsayım (Tansu, 11.10.2026) — Claude'un önerisi, Tansu'nun yazılı onayıyla işlendi."* yazılır.
- Artı: **sıfır** şema/validator değişikliği (bu oturumda zaten defalarca kullanılan desen — not alanı her zaman serbest).
- Eksi: tag seviyesinde ayrıştırılamaz (yalnız not metninden okunur, programatik sayılamaz).

Hiçbiri uygulanmadı — karar Naci'nin (bkz. §5 SORU 1).

---

## 4. Uygulama planı (sıralama, henüz yapılmadı)

Her adım kendi doğrulama kapısıyla, önceki adımın commit'i push edildikten sonra başlar (bu oturumun yerleşik deseni).

1. **Boztepe (izole, en düşük risk).** `total_debt=15.000.000 USD`, `interest={base: "Swap sabit %3,894", margin_pct: 2,85}` (mevcut `SingleLenderInterest` şekli, şema değişikliği yok), `tenor_years=10`, `dscr_covenant=1,20`, `dsra_balance=505.800 USD`, `repayment_profile` serbest metinle ("ilk 3 yıl yalnız faiz, Mayıs 2027'den itibaren eşit aylık anapara"). İmza ayı (Mayıs 2024) için `OperatingTimeline`'da alan yok — not olarak `lender`'ın notuna eklenebilir (şema değişikliği gerekmez). **Kapı:** `make validate-ledger` (0 hata; `check_finance`/F1-F2 Boztepe'ye uygulanmıyor, yeni bir hata beklenmiyor), `make test`.
2. **Yeşilova (izole).** `finance.capex=26.400.000 USD`, `finance.equity=24.048.000 USD` (ikisi de zaten Optional alan, şema değişikliği yok), `turbines.count=5`, `covenant_tests` listesine `Q4_2024` (dscr 3,9, pass) ve `Q4_2025` (dscr 3,6, pass) eklenir (yıllık test, mevcut `CovenantTest.period` deseni `Q[1-4]_YYYY` yıl-sonu testi Q4 olarak kodlamaya uyuyor, yeni alan gerekmiyor). **Kapı:** aynı.
3. **Kızılova (izole, TEK şema değişikliği).** `SignedUndrawnFacility`'ye yeni bir `signed_date: date` alanı eklenmesi gerekiyor (şu an hiç yok) → `2026-10-05`. **Kapı:** `make lint` (yeni alan mypy/ruff'tan geçmeli), `make validate-ledger`, `make test`.
4. **Karatepe EPC fiyatı.** `epc_contract_price.value: 41500000 → 14500000`. **Kapı:** `make validate-ledger`, `generate_documents` + önce/sonra fark (yalnız `DOC-ANK-EPC-001`'in `epc_contract_price` token'ı değişmeli), `make test`.
5. **Karatepe tarihleri (en riskli adım).** `financing_signed→2022-06-20`, `financial_close→2022-07-08`; **zorunlu eş-değişiklik:** `construction_start`'ı `financial_close`'dan sonraya almak (C1 kuralı, §1(2) bulgusu — tam tarih henüz seçilmedi, bkz. §5 SORU 3); `DOC-ANK-FIN-001..004`'ün `document_date`/`effective_date` alanlarını yeni 2022 aralığına kaydırmak (göreli sıralama korunarak, C8 kuralı). **Kapı:** `make lint`, `make validate-ledger` (C1/C8 özellikle), `generate_documents` + fark, `make test`.
6. **Boztepe KGF çıkarma.** Dosya değişikliği yok (hiç modellenmemişti) — yalnız bir açıklayıcı yorum satırı eklenebilir (opsiyonel, kozmetik).

**Hangi belgeler yeniden üretilecek:** `DOC-ANK-EPC-001` (adım 4), `DOC-ANK-FIN-001/002/003/004` (adım 5) — hepsi **token-otomatik**, elle prose düzenlemesi gerekmiyor. **Hand_edited olup elle düzeltme gerektirecek hiçbir belge bulunamadı** — ne EPC fiyatı ne Karatepe tarihleri hand_edited bir prose dosyasının METNİNDE (token dışında) geçiyor.

---

## 5. SORU listesi

1. **Tag seçeneği (§3):** Seçenek A (yeni tag) mı, Seçenek B (USER_FACT+not) mı? **Önerim: B** — sıfır validator/şema riski, bu oturumda zaten kullanılan desen.
2. **İK kapsamı:** Tansu'nun asgari seti (≈8 belge) mi Adım 5'e giriyor, yoksa ADIM5_PLAN'ın SORU 7'sindeki tam 432-belge seti de mi? **Önerim: yalnız asgari set** — Tansu'nun kendi yazdığı kapsam bu, tam set Adım 6'da (kullanıcı kimlikleriyle birlikte) kalsın.
3. **Karatepe'nin yeni `construction_start` tarihi ve facility-chain (001-003) belge tarihleri** Tansu tarafından verilmedi, C1/C8 kurallarını geçecek şekilde seçilmesi gerekiyor. **Önerim:** ben seçeyim (hiçbir belge/eval bu tarihlere bağlı değil, düşük risk) — uygulama turunda raporlanır.
4. **36 kişilik İK listesi nerede tutulsun** (yeni bir dosya mı, `company.yaml`'a mı eklensin)? Bu rapor bu kararı almadı. **Önerim:** yeni, ayrı bir `seed_data/master/personnel.yaml` — 36 kişi Karatepe/Kızılova/Yeşilova gibi "proje" değil, şirket-geneli bir kaynak.

---

**Doğrulama:** Bu rapor hiçbir ledger/kod dosyasını değiştirmedi. `make validate-ledger` çıktısı rapor öncesiyle **aynı** (0 hata, 1 uyarı — T1, Karatepe türbin/kapasite aritmetiği, ilgisiz):

```
WARNING ankara_res.yaml project.turbines.count.value: T1: 8 türbin × ~5 MW ≈ 40 MW, declared capacity_mw.current is 24 MW
0 error(s), 1 warning(s)
```
