# Adım 5 — Veri kütüphanesi (D/E) + C.4 etiketleri (Ç-9) — uygulama planı

**Tarih:** 09.10.2026 · **Durum:** plan, Naci onayı bekliyor; **kod yok, canlı Gemini çağrısı yok** · **Dayanak:** `URUN1_KARARLAR_VE_SIRA.md` §3.2 Adım 5 (c); `docs/plans/URUN1_NOT_PLAN.md` §3–§4 (kütüphane maliyeti); `docs/plans/ADIM4_PLAN.md` §3 (erteleme notu: eşik yeniden doğrulaması bu adım sonrası); `NACI_CEVAP_2026-10-08.md` (AI-BalBal PR #13) §3 (tek değer listesi); `docs/plans/PROJESIZ_SORU_PLAN.md`/`ADIM4_REPORT.md` §4.1 (bu adımın nedenlerinden biri: İzmir'in bazı belge türlerinden hiç kaydı yok) · **Dal:** `feat/adim5-veri-kutuphanesi` (`feat/adim4-proje-ekseni` üzerinden; `main`'e birleştirme yok) · **Kapsam dışı:** C.1 (36 kullanıcı/departman üyeliği — Adım 6), C.3 (yükleme önerisi), C.6 (önlisans süreç modeli), ekip sohbeti, sözlük tablosu, held-out ölçümü (bu adımdan **sonra**, `ADIM4_PLAN.md` §3).

## 0. Önce — AI-BalBal PR #17 durumu (09.10.2026, okuma, aynı gün)

**Tansu T-1…T-9'un hiçbirine cevap vermedi.** PR #17: `OPEN`, **0 yorum**, dosya (`docs/SORULAR_NACIDEN_2-2026-10-09.md`) hiç düzenlenmedi. Repoda 09.10 12:45 UTC'den (son push'um) sonra hiçbir yeni commit/branch/PR/yorum yok; PR #15 (Anayasa v2.1) ve #16 (Ek-F) de Naci onayladığı halde Tansu tarafından **henüz birleştirilmedi**.

**Adım 5'i bloke eden 4 soru, cevapsız — her biri için varsayımla ilerleniyor (işaretli, SORU'da tekrar sorulacak):**

| # | Soru | Adım 5'i nasıl bloke ediyor | Bu planın varsayımı |
|---|---|---|---|
| T-3 | Bütçe/gerçekleşen workbook'u hangi departmanda (Enerji O&M mi, Proje Finans mi)? | Her SPV için bu tür belgenin **klasörü** belirlenemiyor | **Enerji O&M'de kalır** (bugünkü yer), Proje Finans'a görme yetkisi Ürün 2'nin görüş-talebi modeliyle sonra eklenir (T-3 cevabı "A" gelirse) |
| T-7 | Demo "bugün" tarihi 06.10.2026 sabit mi? | `demo_today`'e göre hesaplanan **her** USER_FACT (kalan borç, işletme yılı, sigorta gün sayısı…) bu tarihe bağlı; yanlış tarihle üretilen belge yeniden üretilir | **Sabit 06.10.2026** varsayılıyor (Tansu'nun önerisiydi, T-7 bunu teyit istiyor) |
| T-8 | "Klasörler tamamlandı" = PF+Hukuk mu, tüm departmanlar mı? Parti parti test başlar mı? | Parti sırası ve Tansu'ya "haber ver" noktaları değişir | **Parti parti** varsayılıyor (§4), her partiden sonra haber verilir |
| T-9 | Enercon/Vestas (üretici) adları ne zaman kararlaşır? | O&M belgelerinde üretici adı yazılır yazılmaz | **Mevcut adlarla** (Enercon, Vestas) üretilir, tek tablodan yönetilir (§5), karar gelince toplu değişir |

Bu dört varsayım **plan onayına dahil**; Naci onaylarsa bu şekilde ilerlenir, Tansu cevap verirse yalnız o maddenin değer(ler)i değişir (yapı değişmez — her biri zaten "tek tablo/değişken" ile izole edilmiş).

## 1. Kapsam — 7 SPV + holding, belge türü × proje matrisi

### 1.1 Şirketler (Tansu §3.1, isimler/rakamlar tek kaynak — SPV şeması `company.yaml`'a eklenir)

| Kısa ad | Kod (öneri) | Durum | Kurulu güç | Not |
|---|---|---|---|---|
| XYZ Enerji A.Ş. (holding) | `XYZ` (proje değil, şirket) | — | — | tüm personel burada |
| Karatepe RES | `ANK_RES` (**değişmez**, §2) | İşletmede | 24 MW | Garanti BBVA 2022-KT |
| Yeşilova RES | `YSV_RES` (yeni) | İşletmede | 22 MW | Commerzbank 2023-YS |
| Boztepe RES | `BOZ_RES` (yeni) | İşletmede | 30 MW | Garanti BBVA 2024-BZ |
| Güneşalan GES | `GNS_GES` (yeni) | İşletmede | 18 MWp | kredisiz (özkaynak) |
| Kızılova RES | `IZM_RES` (**değişmez**, §2) | Geliştirme (önlisans) | 42 MW | Garanti BBVA 2026-KZ, kullandırılmadı |
| Akyar GES | `AKY_GES` (yeni) | Geliştirme | 60 MWp | kredisiz |
| Demirci RES | `DMR_RES` (yeni) | Geliştirme | 80 MW | kredisiz, TEA olumsuz |

**Kod kararı (SORU 1):** `ANK_RES`/`IZM_RES` **iç kodları ve `DOC-ANK-*`/`DOC-IZM-*` önekleri değişmez** (§2'nin 0-LLM yeniden kullanımı için); yalnız **görünen ad** (`project.name`, SPV unvanı, başlık metinleri) "Karatepe RES"/"Kızılova RES" olur. 5 yeni SPV'ye yeni kod/önek: `YSV`/`BOZ`/`GNS`/`AKY`/`DMR`.

### 1.2 Belge türü × proje matrisi — belirsizlik testi şartı

**Zorunlu tasarım kuralı (Adım 4'ün bulgusundan, `ADIM4_REPORT.md` §4.1):** en az **3 belge türü** (sürüm/tadil hariç) **en az 2 projede** **her projede ≥ 2 belge** olacak şekilde planlanır — bugünkü korpusta bu şart yalnız 1 türde (`Legal Review Memo`) sağlanıyordu, Adım 4'ün dev AMB setinin 2/5'i bu yüzden "korpus-gereği-belirsiz-değil" çıktı. Aday türler (işletmedeki 4 SPV'nin hepsinde doğal olarak tekrarlayan):

| Belge türü | Hangi projelerde ≥ 2 | Not |
|---|---|---|
| `Legal Review Memo` | Karatepe (zaten 2), Yeşilova, Boztepe (kamulaştırma/imar davaları → her birinde ≥ 2 hukuki not) | mevcut tür, genişletilir |
| `Insurance Notice` / poliçe yenileme bildirimi | Karatepe, Yeşilova, Boztepe (üçünün de poliçesi var, §3.7) | yeni tekrar |
| `Maintenance Report` / bakım raporu | Karatepe, Yeşilova, Boztepe, Güneşalan (hepsinin O&M'i var) | yeni tekrar |
| `Covenant Report` | Karatepe (3, mevcut), Yeşilova (yeni, Annex E/F raporlaması) | Kızılova'da **hiç yok** (kullandırılmadı) — bilinçli, D5 |

Bu dördü belge üretim planında (§3) **işaretli** üretilir; her partinin sonunda matris güncellenir (§4 doğrulama kapısı).

### 1.3 Belge sayısı (güncellenmiş tahmin, Adım 1 İ-1 kararıyla düşürülmüş)

| Departman | Belge (yaklaşık) | Not |
|---|---|---|
| Proje Finans | ~85 | 4 kredi (Karatepe 3 halka + Yeşilova + Boztepe + Kızılova kullandırılmamış, 1 belge), Annex E/F raporlama, DSRA/hesap belgeleri, **Kızılova'da kullandırım talebi/inşaat ilerleme raporu üretilmez** (İ-1) |
| Hukuk | ~55 | Karatepe kamulaştırma, Yeşilova tazminat, Boztepe imar iptali (duruşma 28.10), Kızılova yüklenici ihtilafı (ihtarname), Demirci TEA itirazı — 5 dava × ~4, sözleşme kopyaları |
| Enerji (Proje Geliştirme + O&M + EPC + Üretim/Piyasa) | ~120 | işletmedeki 4 SPV'nin O&M/üretim raporları, Kızılova geliştirme (LNTP, mühendislik/tasarım, türbin rezervasyonu — **inşaat/kullandırım belgesi yok**), Akyar/Demirci geliştirme belgeleri (ÇED, askeri görüş, TEA) |
| Mali İşler (+ Muhasebe, Finansal Muhasebe) | ~75 | 8 şirket (holding + 7 SPV) × sicil/vergi/imza sirküleri, bordro (BR-26-009/010), e-faturalar (ABC avans, Enercon mükerrer), beyannameler, muavin Excel |
| İdari İşler | ~20 | zimmet, araç, kira, PO dosyaları, acil ödemeler (AÖ-26-002/003) |
| E eklemeleri (Yeşilova/Boztepe/Güneşalan özel) | ~25 | banka yazışmaları, Annex F, sigorta zeyilnamesi |
| **Ara toplam (İK hariç)** | **~380** | bugün 70 (+ yeniden adlandırılacak) |
| İK | ~36 × 12 ≈ 432, ya da ofis-bazlı ~180 | **kapsam dışı bırakılabilir** (SORU 7) — kişi dosyaları şablonla, LLM'siz |

Not: "~345" (URUN1_NOT_PLAN'ın ilk tahmini) yerine **~380** — 5 yeni SPV'nin işletme/geliştirme belgeleri eklendi, Kızılova'nın inşaat belgeleri (İ-1 kararıyla) çıkarıldı.

## 2. Mevcut 70 belge — `[[token]]` yeniden adlandırma + Tansu §3 hizalaması (0 LLM)

**Neden 0 LLM:** `seed_data/generator/prose/*.yaml` dosyalarında ad/rakam **hiç literal değil** — hepsi `[[project_name]]` (90), `[[spv_name]]` (114), `[[counterparty]]` (116), `[[capacity_mw]]`, `[[dscr_covenant]]`, `[[total_debt]]` gibi token'lar; LLM yazdığı anlatıyı bu token'ların **etrafında** kurmuş, değerlerini hiç görmemiş. Üretici (`generate_documents.py`) token'ları ledger'dan doldurur. Bu yüzden:

1. **Değişen:** `seed_data/master/ankara_res.yaml` (ve `izmir_res.yaml`) içindeki `project.name`, `spv.name`, `finance.*`, `timeline.*` **değerleri** → Tansu §3'teki rakamlara (Karatepe 24 MW/USD/Garanti 2022-KT/DSCR 1,20x; Kızılova 42 MW/önlisans/Garanti 2026-KZ/kullandırılmadı). `company.yaml`'daki `parties`/`name_whitelist` → yeni isimler (banka adı Ç-12 istisnasıyla "Garanti BBVA" gerçek ad olabilir — §5'teki karar bekleniyor, şimdilik kurgusal "PQR Bank" kalır, SORU 3).
2. **Değişmeyen:** `seed_data/documents/manifest.json`, `seed_data/generator/prose/*.yaml` (prose dosyalarının kendisi — token'lar aynı), `document_specs/ankara_*.py`/`izmir.py`'daki İngilizce **başlık şablonları** değişmeyebilir (örn. "Facility Agreement" türü aynı kalır; yalnız içindeki `[[spv_name]]` doldurma değeri değişir) — **tek istisna:** başlıklarda literal "Ankara"/"İzmir" geçen 70 dosyanın dosya adı/manifest başlığı (örn. `2019-...-ANK_RES_...pdf`) — bu dosya adları **değişmez** (iç kod `ANK_RES` sabit kaldığı için, §1.1 kararı).
3. **Yeniden üretim adımı:** `make seed` (ya da `generate_documents.py` doğrudan) ledger'daki yeni değerlerle 70 PDF'i **aynı dosya adlarıyla** yeniden üretir (WeasyPrint, bayt-aynı değil ama **içerik aynı doğrulama** yöntemi — ADR-029'daki yöntemle, metin+görsel karşılaştırma); `make excel` 4 workbook'u yeniden üretir (LibreOffice recalc).
4. **Doğrulama:** `make validate-ledger` + `make validate-documents` + `make validate-excel` — **0 hata** şartı; eski 80 soruluk eval'in **mekanik** olarak çoğu geçerli kalır (ad/rakam eşlemesi değişti, soru metni ve kaynak başlıkları aynı kaldığı sürece) — §6'da detay.

**LLM çağrısı: 0.** Yalnız YAML değer değişikliği + `make seed`/`make excel` (template/kod, LLM yok) + doğrulama.

## 3. Yeni belgeler — üretim yolu ve kota planı

### 3.1 Kodla/şablonla (0 LLM) — sayısal/yapısal belgeler

| Tür | Yöntem | Neden LLM değil |
|---|---|---|
| Financial Model, Covenant Report, Budget vs Actual, Monthly Production (5 yeni SPV için) | `generate_excel.py` (openpyxl + LibreOffice recalc) | CLAUDE.md: "LLM matematik yapmaz"; rakamlar formülle, ledger'dan |
| Bordro özeti (BR-26-0xx), muavin Excel, e-fatura XML özeti | yeni küçük şablon fonksiyonu (openpyxl/jinja benzeri düz metin) | sayısal, deterministik |
| İmza sirküleri, ticaret sicil gazetesi, vergi levhası (8 şirket) | şablon (Markdown/HTML → WeasyPrint, mevcut `generate_documents.py` deseni) | sabit form, LLM'siz doldurma |
| Kişi dosyaları (İK, kapsam dışı bırakılırsa atlanır) | şablon | form niteliğinde |

**Tahmini: ~120–150 belge, 0 LLM.**

### 3.2 LLM düzyazı (anlatı belgeleri) — mevcut yöntemle (`generate_prose.py`)

Hukuki notlar, dava dilekçeleri, teknik raporlar, toplantı tutanakları, yazışmalar, ihtarnameler — bugünküyle aynı mekanizma: Markdown şablon + token + LLM 1 çağrı/belge (`MAX_ATTEMPTS=3`, gözlenen ret oranı düşük → ~1,2 çağrı/belge ortalama).

**Hesap:** ~380 (ara toplam, İK hariç) − ~130 (şablon/Excel, §3.1) ≈ **~250 anlatı belgesi** → **~300 LLM çağrısı** (1,2 çarpanıyla).

### 3.3 Kota planı (Gemini ücretsiz: günde 500, dakikada 5 → 26 sn aralık)

| Gün | İş | Çağrı | Not |
|---|---|---|---|
| 1 | PF (85) + Hukuk (55) anlatı belgeleri | ~140 × 1,2 ≈ 170 | tek günde sığar (< 500) |
| 2 | Enerji (120) anlatı belgeleri | ~120 × 1,2 ≈ 145 | |
| 3 | Mali İşler (75) + İdari (20) + E (25) anlatı belgeleri | ~120 × 1,2 ≈ 145 | |
| — | Excel/şablon üretimi (0 LLM) | 0 | herhangi bir gün, paralel |
| 4. gün (ayrı) | Eval yeniden yazımı ölçümü (R0 kapalı + R1 açık, ~yeni soru sayısı × 2) | ~150–250 | §6 |

**Toplam ~3 kota günü** (üretim) **+ 1 kota günü** (ölçüm) = **~4 gün**; her gün 5/dk sınırıyla ~1–1,5 saat sürer (26 sn aralık). Parti biterse o günün kotası bitmeden bir sonraki partiye geçilmez (günlük 500 sınırına karşı tampon).

## 4. Sıra — PF → Hukuk → Enerji → Mali İşler → İdari → İK, her partide doğrulama kapısı

| Parti | İçerik | Doğrulama kapısı (parti bitince, hepsi geçmeden sıradaki parti başlamaz) |
|---|---|---|
| **1. Proje Finans** | 4 kredi ailesi (Karatepe 3 halka, Yeşilova, Boztepe, Kızılova kullandırılmamış), Excel'ler (Financial Model/Covenant/Budget/Production × 4 işletmedeki SPV), DSRA/hesap belgeleri | `make validate-ledger` (G1 taranmış, D2 önek, F-kuralları SPV başına); `make validate-excel`; rakam çapraz kontrolü (Karatepe 14,0/13,6 mn **bilinçli** fark hâlâ var mı — §5); gizlilik etiketi kontrolü (Financial Model `normal`, Adım 1 kararı korunuyor) |
| **2. Hukuk** | 5 dava (Karatepe kamulaştırma, Yeşilova tazminat, Boztepe imar iptali, Kızılova ihtilaf, Demirci TEA itirazı), Legal Review Memo'lar (§1.2 matrisi) | `make validate-documents`; proje izolasyonu (D2); belge türü × proje matrisinin §1.2 şartını karşıladığı kontrol edilir (en az 3 tür, ≥2 proje, her projede ≥2) |
| **3. Enerji** | Geliştirme (Kızılova LNTP, Akyar/Demirci ÇED/TEA), O&M (Enercon/Vestas/Solaris sözleşmeleri + bakım raporları), EPC (Kızılova mühendislik/avans/teminat), Üretim/Piyasa | aynı + C.4 etiketleri (proje + tür etiketi her belgede ≥ 1) — bu partide etiket kataloğu da güncellenir (5 yeni proje etiketi) |
| **4. Mali İşler** | 8 şirket sicil/vergi/imza, bordro, e-fatura, beyanname, muavin Excel | gizlilik/yetki testleri (K5 provası: finans/mali_isler ayrımı); mükerrer fatura/mükerrer talep gibi **bilinçli** tuzakların işaretlenmesi (§5) |
| **5. İdari İşler** | zimmet, araç, kira, PO, acil ödeme | retrieval-only kontrol (0 LLM): yeni belgelerin FTS'te bulunabilirliği |
| **6. İK** (opsiyonel, SORU 7) | kişi dosyaları (şablon) | — |

**Her parti sonunda:** Tansu'ya haber (T-8 cevabına göre parti parti test başlayabilir ya da tüm partiler bitmeden başlamaz — varsayım: parti parti, §0).

## 5. Tutarlılık — tek ledger kaynağı, bilinçli vs kazara çelişki

- **Tek kaynak:** her SPV'nin tüm rakamları (MW, tarih, tutar) `seed_data/master/<spv>.yaml`'da; belge şablonları bu değerleri **token'la** okur, asla literal yazmaz (§2'deki mevcut disiplin aynen sürer).
- **Bilinçli çelişkiler (K3 "Çelişkili Veri" testi için, Adım 2 §3.2 adım 7'nin girdisi) — ayrı işaretlenir:** ledger'da yeni bir alan, `deliberate_conflict: true` + `conflict_group` (örn. `karatepe-kredi-tutari`) — Tansu'nun listesi (§3.7): Karatepe 14,0/13,6 mn USD, Yeşilova 18.912/18.240 faiz, Yeşilova'nın iki ödeme planı sürümü, Enercon mükerrer fatura, mükerrer yemek fişi, PO-26-039 sipariş/fatura farkı. `validate_ledger.py` bu alanı görünce **D2 (proje izolasyonu)** ve **F (rakam tutarlılığı)** kurallarını o grup için **atlar**, başka hiçbir yerde atlamaz.
- **Kazara çelişki — kapıda yakalanır:** `deliberate_conflict` işaretlenmemiş her rakam/tarih, aynı `conflict_group`'ta olmayan iki belgede farklıysa `validate_ledger.py` **hata** verir (mevcut F-kuralları mantığı; yeni olan yalnız "bilinçli mi" ayrımı). Bu, §4'teki her partinin doğrulama kapısının parçası.
- **Üretici/banka adları (Ç-12, Ek-E 8):** Tansu'nun kararı bekleniyor (T-9; Anayasa'da banka adları serbest, OEM/kamu adları açık). Bu adamlar `company.yaml`'da **tek tabloda** (`name_whitelist` + yeni bir `pending_real_names` alanı) tutulur; karar gelince **tek yerden** toplu değişir, belge yeniden üretimi gerekmez (adlar zaten token'la giriyor).

## 6. Etki — eval, eşikler, bayt-aynı kuralı, canlı DB

- **`questions.json`:** `expected_project` Literal'i 2'den 7'ye çıkar (`ledger_schema.py`); `ask_as_user` eşlemesi (eski 5 demo hesap, C.1'e kadar **değişmez** — Adım 5 yalnızca belge üretir, kullanıcı seti Adım 6'da değişir); `required_sources`/ledger yolları yeni dosya adlarına (SPV koduna) göre güncellenir; `GEN-DSC-*`/`GEN-AMB-*`/`ANK-NEG-*` gibi mevcut sorular **ad değişmeden** (§1.1 kod kararı) çoğunlukla aynen kalır — yalnız **rakamları** değişenler (`value_check`) güncellenir.
- **`PROJECT_AXIS_DISAMBIG_SPREAD`/`DOMINANT_SHARE`:** `ADIM4_PLAN.md`'nin erteleme notuyla uyumlu — bu adım biterken **yeniden doğrulanır** (dry run, 0 LLM, `ADIM4_PLAN.md` §3'teki aynı 9+5(+1) soruyla, yeni korpus üzerinde). GEN-AMB-001/002'nin bu kez gerçekten `disambiguate` çıkıp çıkmadığı (Yeşilova/Boztepe'nin kendi Facility Agreement/Covenant Report'u olduğu için) **ilk kontrol edilecek şey**.
- **Held-out ölçümü (Adım 4'ün ertelenen kısmı):** bu adım bittikten **sonra** istenir (Naci/danışman yazar, geliştirici AI görmez — mevcut kural).
- **Bayt-aynı kuralı:** bu adım hiçbir davranış kodu değiştirmiyor (yalnız veri); `EK_F_MODE=false` davranışı etkilenmez, ama **flag açıkken** davranış (F-3/F-5/F-8/Adım 4) yeni korpusla **yeniden ölçülmeli** (R1 + keşif + negatif, ~31 çağrı, zaten planlıydı).
- **Canlı DB'ye yükleme:** `make backup` (önce) → `make reset-demo` (TRUNCATE, mevcut hafıza notuyla uyumlu — `rm -rf data/` değil) → `make seed` (admin+departman+proje+belge) → `make up-full`'a gerek yok (embeddings kapalı) → `make validate-ocr`. Geri dönüş: `make restore` (yedekten).

## 7. Risk, süre, SORU

### 7.1 Risk

| Risk | Etki | Azaltma |
|---|---|---|
| Tansu'nun 4 sorusu (T-3/7/8/9) yanıtsız kalırsa varsayımla üretilen belgeler yeniden üretilir | orta — yalnız o alanlar, tüm set değil | her varsayım izole bir ledger alanında (§0) |
| 5 yeni SPV için İ-2/İ-3 (Akyar/Demirci tarih/MW) tekrar çelişebilir | düşük — Tansu §3'te netleşmiş görünüyor | §1.1 tablosu Tansu §3'ten alındı, çift kontrol edildi |
| ~300 LLM çağrısı 3 güne yayılırken bir gün 503/kota sorunu çıkarsa | orta — parti geç kalır | her partinin kendi günü var, taşarsa ertesi güne kayar (sabit sıra bozulmaz) |
| Belge türü × proje matrisi (§1.2) hukuk/enerji partisi bitene kadar doğrulanamaz | düşük — geç fark edilirse ek belge gerekir | §1.2 matrisi üretim **öncesi** planlanıyor (bu plan), parti 2/3 sonunda ayrıca kontrol ediliyor |
| WeasyPrint/LibreOffice bayt-aynı değil (ADR-029 bilinen sınır) | düşük | içerik karşılaştırma yöntemi zaten var |

### 7.2 Süre
**L, 2–3 hafta** geliştirme (şablon aileleri, generator genişletmesi, ledger, validator) **+ ~4 kota günü** (üretim + ölçüm) — Tansu'nun "frontend ile aynı anda biter" beklentisi bu süreyle karşılaştırılmalı (URUN1_NOT_PLAN SORU 9'da zaten not edildi, 2–3 hafta kabul edilmişti).

### 7.3 SORU (Naci)

1. **Kod/önek kararı (§1.1):** `ANK_RES`/`IZM_RES` iç kodları ve `DOC-ANK-*`/`DOC-IZM-*` önekleri **değişmesin** mi (önerim, düşük risk, 0 ek kod) yoksa yeni adlara göre **yeniden kodlansın** mı (yüksek risk, ~70 dosya adı + tüm referans zinciri)?
2. **İK kapsamı (§1.3, §4):** bu adıma **dahil** mi (36×12 ≈ 432 belge, büyük ek iş) yoksa **Adım 6'ya** (C.1, kullanıcı seti) mı bırakılsın? Önerim: Adım 6'ya — kişi dosyaları kullanıcı kimlikleriyle birlikte anlamlı.
3. **Banka adı istisnası (Ç-12, §2/§5):** bu adımda gerçek "Garanti BBVA"/"Commerzbank" adları mı kullanılsın (Anayasa v2.1 ADT-1 zaten onaylı — Naci onayladı, Tansu da onayladı, birleştirme bekliyor) yoksa Tansu'nun birleştirmesine kadar kurgusal adlarla mı (§2'deki varsayım) devam edilsin? Önerim: **birleştirmeyi bekle** — PR #15 henüz merge değil.
4. **Varsayımlar (§0, T-3/7/8/9):** onaylanıyor mu, yoksa Tansu'dan cevap gelene kadar **bu adım başlamasın** mı? Önerim: onayla, başla — her biri izole, geç cevap gelirse yalnız o alan değişir.
5. **Belge türü × proje matrisi (§1.2):** önerilen 4 tür (Legal Review Memo, Insurance Notice, Maintenance Report, Covenant Report) onaylanıyor mu, yoksa başka türler mi eklensin?
6. **Eski 80 soruluk eval'in akıbeti (§6):** kod değişmeden (§1.1 kararı A ise) mekanik olarak büyük ölçüde korunacağı varsayılıyor — bu varsayım kabul mü, yoksa eval tamamen mi yeniden yazılsın?
7. **Sıra içi paralellik:** Excel/şablon üretimi (0 LLM) PF partisiyle **aynı günde paralel** mi başlasın (önerim, zarar yok) yoksa partiler tamamen **ardışık** mı (her şey dahil) kalsın?
