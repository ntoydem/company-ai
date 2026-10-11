# Adım 5 — Tansu'nun PR #21 (6. tur) cevaplarını işleme planı

**Tarih:** 11.10.2026 · **Durum:** yalnızca plan — **hiçbir ledger/kod/belge değiştirilmedi**
**Kaynak:** `ftansu/AI-BalBal`, PR #21 (`docs/naci-cevap-6-2026-10-11`, dosya `docs/NACI_CEVAP_2026-10-11.md`),
PR #19 (`docs/naci-sorular-4-2026-10-11`, Cevap sütunu), PR #20 (`docs/naci-sorular-5-2026-10-11`, Cevap sütunu),
`docs/NACI_CEVAP_2026-10-08.md` (branch `docs/naci-notlari`) — tümü `gh api`/`git clone` ile okundu (GraphQL yok).

---

## 1. Ön koşul — PR #15 / #16 birleşme durumu

```
gh api repos/ftansu/ai-balbal/pulls/15 --jq '{merged, merged_at, state}' → {"merged": false, "merged_at": null, "state": "open"}
gh api repos/ftansu/ai-balbal/pulls/16 --jq '{merged, merged_at, state}' → {"merged": false, "merged_at": null, "state": "open"}
```

**İkisi de birleşmedi.** PR #21 §6 de bunu doğruluyor: *"Birleştirme ürün sahibinin tek tıkına kaldı. Birleşince güncel Anayasayı company-ai'ye ekle."*

**Sonuç:** Anayasa v2.1 Ç-12 (gerçek banka adlarına izin) henüz **resmi değil**. Banka adı değişiklikleri (§3 aşağıda) PR #15 birleşene kadar **BEKLE** olarak işaretlendi — bu planın hiçbir adımı banka adı değişikliğini şimdi uygulamaz.

---

## 2. Fark tablosu (PR #21 §1-§3 ↔ mevcut ledger)

| Proje | Alan | Mevcut (ledger) | Yeni (PR #21) | Etkilenen doc_id (ledger/spec/prose) | Tür | Maliyet |
|---|---|---|---|---|---|---|
| Boztepe | `finance.signed_date` | `2024-05-02` (AI_ASSUMPTION) | **2024-02-20** | `boztepe_res.yaml` (ledger). Henüz belge yok. | 0 LLM | — |
| Boztepe | `repayment_profile` (metin) | "ilk 3 yıl yalnız faiz... anapara Mayıs 2027'den" | "ilk 3 yıl faiz, anapara **01.03.2027**'den **84 eşit taksit** (178.571,43 USD, son taksit **01.02.2034**)" | `boztepe_res.yaml` + `repayment_schedule` (84 satır yeniden hesaplanır) | 0 LLM (ledger + DuckDB/Python hesap) | — |
| Boztepe | `lender` | `PQR Bank` | **PQR Bank kalır** (Ç-12 BEKLE) | `boztepe_res.yaml` | 0 LLM | — |
| Boztepe | `timeline` | `{}` (boş) | COD **28.12.2020**, YEKDEM 01.01.2021–31.12.2030, 85 USD/MWh; 2024-BZ inşaat-dönemi sponsor fonu refinansmanı | `boztepe_res.yaml` | 0 LLM | — |
| Karatepe | `lenders.eca` / `eca_debt` | VWX ECA, 0 USD | **Kaldır** (ECA tarafı yok) | `ankara_res.yaml` + facility-chain belgeleri (`DOC-ANK-FIN-001..005`, zaten üretilmiş — yeniden üretim gerekir) | Claude prose (5 belge) | ~5 × $0,02 ≈ $0,10 |
| Karatepe | `lenders.local_bank` | `PQR Bank` | **PQR Bank kalır** (Ç-12 BEKLE) | `ankara_res.yaml` | 0 LLM | — |
| Karatepe | `turbines.model_generic` | "3,0 MW sınıfı kara tipi türbin" | **Enercon E-82 3,0 MW** (T-9, gerçek ad onaylı — Ç-12'ye bağlı DEĞİL, üretici adı ayrı karar) | `ankara_res.yaml` + türbin adı geçen belgeler (DOC-ANK-DEV-001, muhtemelen DOC-ANK-OPS-*) | Claude prose (≤3 belge) | ~3 × $0,02 ≈ $0,06 |
| Karatepe | YEKDEM | yok | 24 MW tamamı, 2021-sonrası mekanizma, 15.10.2023–14.10.2033, 51 USD/MWh | `ankara_res.yaml` (yeni alan) + ilgili belge varsa | 0 LLM (yeni alan) + olası 1 Claude | ~$0,02 |
| Karatepe | `guarantee_letters[0]` | yalnız amaç + "Ocak 2027" | Vade **15.01.2027**, lehtar orman idaresi, banka **Garanti BBVA** (Ç-12 BEKLE → şimdilik PQR Bank), tutar **1.150.000 TL** | `ankara_res.yaml` + DOC-ANK-FIN-0xx (guarantee key_facts kullanan belge) | 0 LLM (key_facts), belge metni değişmiyorsa | — |
| Kızılova | `development_start` | 2023-02-01 | **2022-06-01** | `izmir_res.yaml` + DOC-IZM-DEV-001..003 | Claude prose (≤3) | ~$0,06 |
| Kızılova | `pre_licence_application` | 2023-05-10 | **04–18.10.2023** (başvuru 04.10.2023) | aynı | Claude prose | dahil |
| Kızılova | `pre_licence` | 2024-01-18 | **2025-01-15** (ÖL/13085-3, bitiş 15.01.2027 — **ledger'daki `pre_licence_expiry: 2027-01-15` ZATEN bu değerle tutarlı**, sadece grant tarihi değişiyor) | aynı | Claude prose | dahil |
| Kızılova | `land_acquisition` | 2024-04-02 / 2024-09-30 | satış vaadi **20.01.2025**, tapu **15.02.2025** + ENH kira (şerh bekliyor) | `izmir_res.yaml` + DOC-IZM-DEV-002 | Claude prose | ~$0,02 |
| Kızılova | `ced_application` | 2025-03-05 | **2025-04-10** | `izmir_res.yaml` + DOC-IZM-DEV-003 | Claude prose | dahil |
| Kızılova | ÇED son olay | İDK 27.08.2026 | ek bilgi talebi 18.07.2026 · görüş yazısı 12.09.2026 · İDK **bekleniyor** (ÇED-2026-057) | `izmir_res.yaml` + DOC-IZM-DEV-003/004 | Claude prose | dahil |
| Kızılova | `pending_steps` | Askeri yazı + TEA bekliyor (2 madde) | **Askeri tamamlandı (30.08.2025)**, **TEA olumlu (25.10.2025, TEA-2025-301)**, jeoteknik/kurum görüşü/bağlantı çağrısı tamamlandı; orman ön izni + mera devam | `izmir_res.yaml` (pending_steps tablosu yeniden yazılır) + ilgili belge | 0 LLM (yapılandırılmış veri) | — |
| Kızılova | `signed_undrawn_facility.lender` | PQR Bank | **PQR Bank kalır** (Ç-12 BEKLE) | `izmir_res.yaml` | 0 LLM | — |
| Kızılova | `advance_guarantee` | DEF Bank | **DEF Bank kalır** (Ç-12 BEKLE) | `izmir_res.yaml` | 0 LLM | — |
| Yeşilova | `lender` | LMN Bank | **LMN Bank kalır** (Ç-12 BEKLE) | `yesilova_res.yaml` + DOC-YSV-FIN-009/010 | 0 LLM | — |
| Yeşilova | `timeline` (yeni) | yok | Faz 1: 3×V136→12 MWe, COD 28.12.2016, YEKDEM 01.01.2017–31.12.2026, 73 USD/MWh. Faz 2: +2 türbin→22 MWe, COD 15.11.2022, YEKDEM dışı (PTF) | `yesilova_res.yaml` (yeni alan) | 0 LLM (yeni alan) | — |
| Yeşilova | `capex`/`equity` etiketleri | `note` metni var ama ayrı/etiketli alan yok | `equity` = "net sponsor katkısı (kredi sonrası)"; yeni alan "inşaat dönemi sponsor fonu" = 26.400.000 | `yesilova_res.yaml` (şema: yeni Optional alan) + DOC-YSV-FIN-009 prose (equity artık YAZILABİLİR — bkz. §6 not) | 0 LLM (şema+ledger) + 1 Claude (DOC-YSV-FIN-009 equity cümlesi geri eklenir) | ~$0,02 |
| Yeşilova | DSRA / borç servis hesabı notu | 702.000 / 84.500 (düz rakam) | Aynı rakamlar + **açıklayıcı not** ("6 dönem borç servisi karşılığı"; "vade öncesi işletme hesabından aktarıldı") | `yesilova_res.yaml` (yalnız `note` alanı) | 0 LLM | — |
| Yeşilova | Annex F eksik belge listesi | yok | "Yeşilova TEİAŞ bağlantı anlaşması teminat mektubu" **kasıtlı eksik** olarak listede geçsin (belge üretilmez) | DOC-YSV-FIN-010 prose (bir madde eklenir) | 1 Claude (zaten mevcut belgenin küçük bir eki) | ~$0,02 |
| Tüm SPV'ler | Banka adları | PQR/LMN/DEF Bank | Garanti BBVA / Commerzbank AG / Akbank | `company.yaml` name_whitelist + TÜM finansman belgeleri (facility chain'lerin tamamı) | **BEKLE (PR #15)** | — |
| Boztepe | KGF | Hiçbir ledger/belge/eval sorusunda referans yok (`grep -rln KGF` → yalnızca 2 rapor dosyası, kendi narratifim) | **Zaten temiz — yapılacak iş yok.** | — | — | $0 |
| fx_rates | 2026-09-15 spot | EUR/TRY 47,35 · USD/TRY 43,60 | **EUR/TRY 55,30 · USD/TRY 48,30** (öneri; canvas'ın 22/23.09 TCMB değerlerinden ayrı) | `fx_rates.yaml` (yeni/değişen satırlar) | 0 LLM | — |
| fx_rates | 2026 yıllık ortalama | EUR/TRY 46,80 · USD/TRY 43,10 | **EUR/TRY 52,40 · USD/TRY 45,90** | `fx_rates.yaml` | 0 LLM | — |
| fx_rates | 22.09/23.09.2026 TCMB | yok | EUR/TRY 55,8513 (22.09) · USD/TRY 48,7499 (23.09) — **yeni, ayrı satırlar** | `fx_rates.yaml` (yeni period'lar) | 0 LLM | — |
| Güneşalan | `timeline` | boş | COD 01.07.2017, YEKDEM 01.07.2017–30.06.2027, 133 USD/MWh, kredisiz | `gunesalan_ges.yaml` | 0 LLM (henüz belge yok) | — |
| Akyar/Demirci | — | kanonikle uyumlu | değişiklik yok | — | — | $0 |

**Toplam tahmini Claude maliyeti (bu bölüm):** ~$0,10 (Karatepe ECA) + ~$0,06 (türbin adı) + ~$0,02 (YEKDEM) + ~$0,06 (Kızılova 3 belge) + ~$0,02 (Yeşilova equity) + ~$0,02 (Annex F eki) ≈ **~$0,28**, 1 çağrı/belge varsayımıyla (ölçülmüş ortalama $0,01–0,02/çağrı, bu oturumdaki 7 gerçek denemenin ortalaması).

---

## 3. Bağımsız aritmetik doğrulama (PR #21 §4)

Python ile tek tek yeniden hesaplandı — **tüm 11 kontrol doğrulandı (✅)**:

| Kontrol | Hesap | Sonuç |
|---|---|---|
| Karatepe 13,6M+6,4M=20M | `13_600_000+6_400_000` | ✅ 20.000.000 |
| Karatepe 8M+5,6M=13,6M | `8_000_000+5_600_000` | ✅ 13.600.000 |
| Karatepe EPC 14,5M EUR×1,1783≤20M | `14_500_000*1.1783` | ✅ 17.085.350 |
| Yeşilova 24×98.000=2.352.000 | | ✅ |
| Yeşilova 2.352.000−10×98.000=1.372.000 | | ✅ |
| Yeşilova 2.352.000−7×98.000=1.666.000 | | ✅ |
| Yeşilova 24.048.000+2.352.000=26.400.000 | | ✅ |
| Yeşilova #11 faizi 1.372.000×(3,89378%+1,50%)×92/360 | `18911.79` | ✅ ≈18.912 (ödeme planındaki 18.240 farkı KASITLI, dokunulmadı) |
| Boztepe 15M×6,744%/12=84.300; DSRA 6×84.300=505.800; Mart'27–Şub'34=84 ay | | ✅ hepsi |
| Kızılova 30M×0,80%×92/360=61.333; 05.10→05.01=92 gün | | ✅ |
| Kızılova avans 10M×20%=2M; ×KDV%20=2,4M; önlisans 15.01.25+24ay=15.01.27 | | ✅ |
| Bordro Eylül/Ekim toplamları | | ✅ |
| Kur EUR/USD=55,8513/48,7499=1,1457 | | ✅ |

### Ek kontrol — Yeşilova türbin/MW aritmetiği (SORU'da istenen)

**ÇELİŞKİ BULUNDU.** PR #21 §2'nin faz tablosu:
- Faz 1: **3 × Vestas V136 → 12 MWe** → 12/3 = **4,0 MW/türbin**
- Faz 2: **+2 türbin → 22 MWe toplam** → ek kapasite (22−12)=10 MW / 2 türbin = **5,0 MW/türbin**

T-11.13'ün (bu oturumda zaten ledger'a işlenmiş) gerekçesi: **"5 × 4,4 MW = 22 MW"** — tek tip 4,4 MW modu varsayıyor.

- 3×4,4 = **13,2 MW** ≠ 12 MW (Faz 1 ile çelişiyor)
- 2×4,4 = **8,8 MW** ≠ 10 MW (Faz 2 artışıyla çelişiyor)
- Yalnız TOPLAM (5×4,4=22) tesadüfen PR #21'in toplamıyla (12+10=22) eşleşiyor — faz bazında **tutarsız**.

Bu, §5'teki "Bilinçli gerçekçilik sapmaları #4" (*"Yeşilova Faz 1'de (2016) V136 4,4 MW modu"*) ile **aynı şey değil** — o not V136'nın 4,4 MW modda çalışmasının gerçekçi olmadığını (demo için kabul edilebilir) söylüyor, faz-bazlı türbin SAYISI aritmetiğini çözmüyor. **Bu yüzden T-14'e taşındı (aşağıda).**

### Diğer gözlemler (yalnız bulgu, düzeltme önerilmedi)

- Kızılova "bağlantı çağrısı" (14.07.2025) TEA onayından (25.10.2025) **önce** — sıra olarak mümkün (çağrıya katılım TEA onayından önce olabilir) ama domain bilgisi kesin değil, hafif bir gözlem.
- Karatepe "ilk taksit COD'den önce" — **YENİ DEĞİL**, §5'in kendi "Bilinçli gerçekçilik sapmaları #1" listesinde zaten var.
- Kalan tüm tarih sıraları (lisans→COD, imza→ilk kullanım, vb.) kontrol edildi, çelişki bulunamadı.

---

## 4. §5 "bilinçli bırakılanlar" ile çakışma kontrolü

Bu planın **hiçbir adımı** §5'in iki listesinden birini (kasıtlı tuzaklar / kabul edilen sapmalar) istemeden düzeltmiyor:

| Bu planın adımı | §5 kalemiyle ilişkisi | Risk |
|---|---|---|
| Karatepe ECA kaldırma, banka/türbin adı | Kasıtlı tuzak "14,0/13,6 mn USD farkı" **tutara dokunmuyor**, yalnız ECA tarafı/isimler | Yok |
| Boztepe `repayment_profile`/tarih düzeltmesi | Kabul edilen sapma #3 ("3 yıl yalnız faiz") — bu plan AYNI yapıyı **uyguluyor**, bozmuyor | Yok |
| Yeşilova equity etiketleme | Kasıtlı tuzak "#11 faizi 18.912/18.240" **dokunulmuyor**; "ödeme planının iki sürümü" **dokunulmuyor** | Yok |
| Annex F "eksik belge" listesine teminat mektubu eklenmesi | §5 zaten bunu kasıtlı eksik sayıyor — bu adım listelemeyi **doğru yapmayı** sağlıyor, belgeyi ÜRETMİYOR | Yok |
| Kızılova timeline/pending_steps düzeltmesi | §5'te Kızılova'ya dair madde yok | Yok |
| fx_rates güncellemesi | §5'te kur'a dair madde yok | Yok |

**Sonuç: çakışma yok.** Dikkat edilecek tek nokta: Karatepe facility-chain belgeleri (DOC-ANK-FIN-001..005) yeniden üretilirken **ECA satırı çıkarılırken tutar (14,0/13,6 mn) rakamına dokunulmamalı** — prose_guidance'a bu açıkça yazılacak.

---

## 5. Hukuk partisi belge listesi önerisi

**Kural kontrolü (hepsi uygulandı):** Kızılova ihtarnamesi "ceza hakkı saklı, tutar talep edilmez" seviyesinde (PR #21 §1 T-12.4 zaten böyle diyor — mevcut ledger notu DA bu seviyede, değişiklik gerekmiyor). Mera (T-12.4b) ve TEA (T-12.5) için **sonuç belgesi YOK**. Akyar (T-12.5b)/Güneşalan'a **dava belgesi YOK**. T-13.2 ile DOC-ANK-DEV-006/DOC-IZM-LEG-002 karşı tarafları bu round'da henüz cevaplanmadı (PR #20'de bekliyor) — bu Hukuk partisi listesi onlara dokunmuyor, ayrı.

| Süreç | Önerilen belgeler (doc_id) | Departman | Gizlilik | Dil | Tür | Tarih |
|---|---|---|---|---|---|---|
| T-12.1 Karatepe kamulaştırma | `DOC-ANK-LEG-001` dava dilekçesi · `DOC-ANK-LEG-002` idare savunması · `DOC-ANK-LEG-003` bilirkişi raporu · `DOC-ANK-LEG-004` duruşma tutanağı (10.01.2026) | hukuk | restricted | tr | Claude (4) | 12.02.2025 → 10.01.2026 |
| T-12.1b Elektrik direği ihlali | `DOC-ANK-LEG-005` dava dilekçesi (davacı: komşu malik) | hukuk | restricted | tr | Claude (1) | 18.06.2026 |
| T-12.2 Yeşilova tazminat | `DOC-YSV-LEG-001` dava dilekçesi · `DOC-YSV-LEG-002` hukuk danışmanı yazışması (`.msg` → PDF) | hukuk | restricted | tr | Claude (2) | 11.06.2025, 14.09.2026 |
| T-12.2b Sınır ihlali | `DOC-YSV-LEG-003` dava dilekçesi | hukuk | restricted | tr | Claude (1) | 02.09.2026 |
| T-12.3 Boztepe imar iptali | `DOC-BOZ-LEG-001` dava dilekçesi · `DOC-BOZ-LEG-002` belediye savunması · `DOC-BOZ-LEG-003` YD reddi kararı (10.07.2026) · `DOC-BOZ-LEG-004` bilirkişi keşif tutanağı (26.09.2026) | hukuk | restricted | tr | Claude (4) | 22.05.2026 → 26.09.2026 |
| T-12.4 Kızılova ihtarname | `DOC-IZM-LEG-005` noter ihtarnamesi (ABC İnşaat'a) | hukuk | restricted | tr | Claude (1) | 29.09.2026 |
| T-12.4b Mera | **Belge yok** (kural) | — | — | — | — | — |
| T-12.5 Demirci TEA itirazı | `DOC-DMR-LEG-001` itiraz dilekçesi (ETKB/TEİAŞ'a) | hukuk | restricted | tr | Claude (1) | 22.09.2026 |
| T-12.5b Akyar | **Dava belgesi yok** (kural); yalnız `DOC-AKY-LEG-001` kamulaştırma ön değerlendirme notu (dava değil) | hukuk | normal | tr | Claude (1) | 05.09.2026 |
| T-12.6 Boztepe kredi | belge değil, yalnız ledger tarihi düzeltmesi (zaten §2'de) | — | — | — | 0 LLM | — |

**Toplam yeni belge: 15** (4+1+2+1+4+1+0+1+1+0). **450 üst sınırına etkisi:** company-ai'nin kendi planı `docs/plans/ADIM5_PLAN.md:60-61`'de Hukuk partisini zaten **~55 belgelik** bir bütçeyle öngörmüştü ("ara toplam İK hariç ~380"); bu 15 belge o bütçenin içinde kalıyor, ek bir aşım yaratmıyor. "450" sayısının kaynağı company-ai'nin kendi planlama dosyalarında **bulunamadı** (muhtemelen AI-BalBal canvas/ürün tarafı bir sayı) — doğrulanamadı, bu yüzden yalnız company-ai'nin kendi ~380/~55 referansıyla kıyaslandı.

**Yapısal ön koşul (blocker):** `generate_documents.py:41` — `_PROJECT_CODE = {"ANK": ..., "IZM": ..., "CO": None, "YSV": ...}` — **Boztepe/Demirci/Akyar için kod YOK**. Bu üç projenin İLK belgesi üretilmeden önce (Hukuk dahil) `_PROJECT_CODE`'a `"BOZ": "BOZ_RES"`, `"DMR": "DMR_RES"`, `"AKY": "AKY_GES"` eklenmesi **zorunlu** (küçük, 0-LLM bir kod değişikliği — bu planın kapsamı dışında, yalnız not edildi).

---

## 6. Kategori B (20 belge) ↔ Tansu'nun kanonik karşı taraf tablosu

`NACI_CEVAP_2026-10-08 §D.1.3` **bulunamadı** — dosya `docs/naci-notlari` dalında `docs/NACI_CEVAP_2026-10-08.md` (249 satır) olarak mevcut, ama bölüm numaralandırması `1, 2, 3.1–3.9, 4, 5, 6` biçiminde; bir "§D" şeması yok. En yakın ilgili içerik:
- **§3.1 Şirketler** — her SPV'nin unvanı/durumu, ama bilateral bir "karşı taraf" eşlemesi değil.
- **§3.2 Krediler** — kredi bazlı lender eşlemesi (2022-KT→Garanti BBVA, 2023-YS→Commerzbank AG, 2024-BZ→Garanti BBVA, 2026-KZ→Garanti BBVA) var, ama bu **finansman belgelerine** ait; Kategori B'nin 20 belgesi (ADM/DEV/OPS mektup ve raporları) finansman değil — EPDK, belediye, toplantı katılımcıları gibi **farklı türde** karşı taraflar gerektiriyor.

**Sonuç: eşleştirme tablosu çıkarılamadı — 20 belgenin TAMAMI açık kalıyor.** Bu, T-14'e taşınmadı (20 ayrı soru olurdu, orantısız); bunun yerine ayrı bir, daha küçük bir round'da (bu planın kapsamı dışında) tek tek sorulmalı veya kök-neden düzeltmesiyle (§4'teki önceki bulgu) birlikte ele alınmalı.

---

## 7. Uygulama sırası ve maliyet

1. **0 LLM — ledger düzeltmeleri (Boztepe tarih/repayment_profile, Karatepe ECA kaldırma öncesi alan temizliği, Kızılova timeline/pending_steps, Yeşilova yeni timeline+capex/equity şema alanı, fx_rates, Güneşalan timeline).** Her SPV ayrı commit, her commit sonunda `validate-ledger` yeşil. ~8 commit.
2. **0 LLM — `generate_documents.py::_PROJECT_CODE`'a BOZ/DMR/AKY ekle** (Hukuk partisi için ön koşul). 1 commit.
3. **Claude prose — Karatepe facility-chain (5 belge, ECA+banka+türbin adı), Kızılova DEV 1-3 (3 belge), Yeşilova FIN-009 equity cümlesi geri ekleme, Yeşilova FIN-010 Annex F eksik-belge eki.** Her belge ayrı `--only` çağrısı, 1 çağrı/belge hedefi, bütçe $0,5 toplam güvenlik payı. ~10 çağrı, ~10 commit.
4. **Her adımda:** `make lint` + `validate-ledger` + `validate-documents` (full) + token-grep yeşil; tek bir solo `make test` yalnız bu round'un SONUNDA.
5. **Hukuk partisi (§5) — AYRI bir round'da** (bu plan onayından sonra, yeni bir görev mesajıyla): 15 yeni belge, ~15 Claude çağrısı.

**Toplam tahmini maliyet:** ~$0,28 (§2) + ~15×$0,02 ≈ $0,30 (Hukuk) ≈ **~$0,58 toplam**, bütçenin çok altında.
**Tahmini commit sayısı:** ~8 (ledger) + 1 (kod) + 10 (prose, bu round) + 15 (Hukuk, ayrı round) ≈ **19 commit bu round için, +15 Hukuk round'unda**.
**Tahmini test sayısı:** yeni Python testi gerekmiyor (yalnız veri/prose değişiklikleri) — mevcut test paketinin tamamı (çevrede ~650) her round sonunda bir kez koşulur.

---

## 8. Tansu'ya soru listesi — T-14 (yalnızca gerçek çelişki/eksiklik)

| Kod | Soru | Seçenekler |
|---|---|---|
| T-14.1 | Yeşilova türbin/MW aritmetiği çelişkisi (§3'teki bulgu): Faz 1 (3 türbin/12 MWe) ve Faz 2 (+2 türbin/+10 MWe) hangi MW/türbin değerini kullanıyor? | **(A)** Faz 1 türbinleri 4,0 MW modda (3×4=12), Faz 2 türbinleri 5,0 MW modda (2×5=10) — modlar fazlar arası farklı. **(B)** T-11.13'ün "5×4,4=22" varsayımı YANLIŞ, iptal edilsin; gerçek dağılım (A)'daki gibi faz-bazlı olsun. **(C)** Başka bir kombinasyon (belirtiniz). |
| T-14.2 | Kategori B'nin 20 belgesinin (ADM/DEV/OPS mektup/rapor) gerçek karşı tarafları (EPDK, belediye, toplantı katılımcıları vb.) — kanonik bir kaynakta var mı, yoksa tek tek mi sorulmalı? | **(A)** Kanonik kaynak var, paylaşılsın. **(B)** Yok, ayrı bir round'da tek tek sorulsun (20 soru, küçük parçalar halinde). |
| T-14.3 | Karatepe YEKDEM'in canvas'taki eski hâli (16 MW/73 USD/2028) ile PR #21'in yeni hâli (24 MW/51 USD/2033) arasındaki fark — canvas güncellenene kadar hangi değer kullanılsın? | **(A)** PR #21'deki yeni değer (51 USD/2033) — zaten §3.9'da "canvas yayınlanana kadar bu dosya geçerli" deniyor. **(B)** Canvas güncellenene kadar hiç YEKDEM alanı eklenmesin. |

---

## Özet (10 satır)

1. PR #15/#16 **birleşmedi** — banka adı değişiklikleri (Ç-12) **BEKLE**, bu round'da uygulanmıyor.
2. Fark tablosu 20+ alan kapsıyor (Boztepe tarih/ödeme, Karatepe ECA/türbin/YEKDEM, Kızılova takvim, Yeşilova faz/equity, fx_rates) — toplam ~$0,28 Claude maliyeti.
3. PR #21 §4'ün 11 aritmetik kontrolü **birebir doğrulandı** (hepsi ✅).
4. **Yeni bulgu:** Yeşilova faz-bazlı türbin MW'ı (12+10=22) ile T-11.13'ün "5×4,4" varsayımı **çelişiyor** — T-14.1'e taşındı.
5. §5 "bilinçli bırakılanlar" listesiyle **hiçbir çakışma yok** — plan onlara dokunmuyor.
6. Hukuk partisi için **15 yeni belge** önerildi (6 süreç, dava belgesi olmayan 2 süreç hariç tutuldu); mevcut ~380/~55 bütçesinin içinde.
7. **Yapısal blocker bulundu:** `_PROJECT_CODE` dict'inde Boztepe/Demirci/Akyar kodu yok — Hukuk partisinden önce eklenmesi gerekiyor (0 LLM, küçük kod değişikliği).
8. Kategori B'nin 20 belgesi için Tansu'nun "kanonik karşı taraf tablosu" **bulunamadı** (`§D.1.3` yok) — hepsi açık kaldı, T-14.2'ye taşındı.
9. Önerilen sıra: 0-LLM ledger/kod adımları önce, Claude prose adımları sonra, Hukuk partisi AYRI bir round'da; toplam ~19 commit bu round + 15 Hukuk round'unda.
10. **3 soru T-14 olarak hazırlandı** (türbin MW, Kategori B karşı taraf kaynağı, YEKDEM geçiş kuralı) — cevap bekleniyor, bu round'da hiçbir ledger/kod/belge değiştirilmedi.
