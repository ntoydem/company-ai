# Adım 5, Aşama C Raporu — demo_today, şema genelleştirmesi, 5 yeni SPV, Kızılova finans/EPC, tutarsızlık taraması

**Tarih:** 10.10.2026  **Model:** Sonnet 5  **Dal:** `feat/adim5-veri-kutuphanesi`  **Commit'ler:** `814f755` (C1), `342e664` (C2), `d1a8236` (C3), `2bc9f59` (C4)

Bu rapor, onaylanmış `docs/plans/ADIM5_ASAMA_B_PLAN.md`'nin uygulanmasıdır (Aşama C). Her adım (C1–C4) ayrı commit'lendi; her commit'ten önce `make lint` + `make validate-ledger` + `make test` (tek başına, test DB'de, 900s timeout) yeşil oldu. **Canlı DB'ye dokunulmadı, canlı Gemini çağrısı yapılmadı, main'e birleştirme yok.**

## C1 — demo_today: 15.09.2026 → 06.10.2026

Plan §1.2'deki doğrulama listesi uygulandı:
- `Settings.demo_today`, `.env`, `infra/.env.example`, 4 master ledger dosyasının `meta.demo_today`'i, `questions.json`'un `demo_today`'i güncellendi.
- `debt_math.outstanding_on`/`operating_year` **gerçek kodla** tekrar çalıştırıldı: outstanding (11.671.800 USD) ve işletme yılı (3) her iki tarihte de (15.09.2026 ve 06.10.2026, 07.10.2026 dahil) **değişmiyor** — plandaki "şans eseri" tahmini doğrulandı (8. taksit 07.10.2026'da, demo_today'den sonra; aynı yarı yıl içinde atomik kapanış).
- `covenant_tests`'e yeni bir çeyrek **eklenmedi** (Aşama B SORU 1: Q2_2026 son rapor kalıyor).
- Excel workbook'ları + 70 belge yeniden üretildi; `validate-ledger`/`documents`/`excel` 0 hata.
- Test düzeltmeleri: ADR-026 stale-snapshot testi artık 07.10.2026'yı reddediyor; `outstanding_debt`/`dscr`/`production`/`capacity_factor` testlerinin `today=` parametreleri taşındı; `Settings.demo_today`/`temporal.today()`'i doğrudan test eden iki test; `test_ask.py`'deki "BUGÜN: 15.09.2026" prompt assertion'ı güncellendi. Saf fonksiyon testleri (arbitrary `today` parametresi alan, gerçek config'e bağımlı olmayanlar — `test_answer_prompt.py`, `test_periods.py`, `test_version_chain.py`, `test_eval_lib.py`'nin rapor-render testleri, `test_temporal.py`'nin `expiration_note` testleri) **bilerek dokunulmadı**.

## C2 — Üç ek ledger şekli (eklemeli, Ankara/İzmir'e dokunmadan)

`AnkaraLedger`/`AnkaraProject` ve `IzmirLedger`/`IzmirProject` **hiç değişmedi**. Eklenenler:

- **`OperatingCapacity`/`OperatingTimeline`** (yeni, hafif): tek kapasite değeri, Tansu'nun verdiği az sayıda işletme-aşaması tarihi için.
- **`OperatingProject`** (Yeşilova RES, Boztepe RES, Güneşalan GES): işletmede, `construction=None` (EPC geçmişi bu round'da verilmedi).
- **`GenericDevelopmentProject`** (Akyar GES, Demirci RES): `IzmirProject`'in ta kendisi — `IzmirTimeline`/`Development`/`TargetCapacity` zaten proje-bağımsızdı, yalnız `code`/`name` artık Literal değil pattern-kontrollü `str`.
- **Karatepe'nin talebi üzerine (Naci'nin düzeltmesi) `Finance`/`Operations`/`Turbines`/`Interest` yeniden kullanıldı**: birçok alan Optional/default-boş yapıldı (capex, equity, local_debt, eca_debt, lenders, tenor_years, grace_months, drawdowns, covenant_tests, base_rate_pct_by_year, repayment_schedule, cfads_by_quarter, outstanding_debt_as_of_demo_today, dscr_covenant — hepsi `| None`/`Field(default_factory=list)`). Karatepe'nin kendi `ankara_res.yaml`'ı her alanı doldurduğu için bu gevşetme **onun davranışını değiştirmedi** (`make validate-ledger` aynı 7 uyarıyı verdi, `make test` 615 testin hepsini yeşil tuttu).
- Yeni küçük alanlar: `Instalment.interest`, `BankInterestNotice` (Yeşilova'nın #11 taksit kasıtlı faiz çelişkisi için), `Finance.debt_service_account_balance`, `Operations.om_contractor`/`om_contract_price`/`insurance_expiry`, `SingleLenderInterest` (tek bankalı, marj değişmemiş kredi — Karatepe'nin `ChangedFact` marjına zorlamadan).
- `check_cross_project_refs`: ikili `("ankara_res","izmir_res")` tuple'ından, `PROJECT_PREFIX`'teki **her** projeyi gezen N-yönlü bir döngüye genelleştirildi.
- `check_documents`/`check_version_links`/`check_document_distribution`: artık paylaşılan `LedgerModel` union'ını kabul ediyor.
- `validate()`'e, `project.stage`'e göre dispatch eden eklemeli bir döngü kondu.

## C3 — 5 yeni SPV ledger dosyası (yalnız Tansu'nun verdiği değerler)

`seed_data/master/{yesilova_res,boztepe_res,gunesalan_ges,akyar_ges,demirci_res}.yaml` yazıldı. `LEDGER_FILES`/`PROJECT_PREFIX` elle 9 girdiye genişletildi (Aşama B SORU 3); yeni `PROJECT_CODE_TO_RAW_KEY` + `company.yaml`'ın `spvs` kaydıyla senkronu denetleyen `test_project_prefix_matches_company_spv_registry` testi eklendi.

**C2'nin gerekli bir devamı:** Akyar/Demirci'nin gerçek verisiyle denerken `IzmirTimeline`'ın (`development_start`, `pre_licence_application`, `land_acquisition_start`, `ced_application`) ve `GenericDevelopmentProject.development`'ın **required** olduğu ortaya çıktı — Tansu bunların hiçbirini vermedi. İkisi de Optional'a gevşetildi (Kızılova'nın kendi verisi hâlâ hepsini doldurduğu için davranışı değişmedi).

### Yeşilova RES (22 MW, Commerzbank/LMN Bank — kurgusal, Ç-12 bekliyor)
Verilen: toplam kredi 2.352.000 USD (24×98.000 eşit anapara, 3 aylık), faiz Term SOFR 3,89378%+1,50 (değişmemiş), DSCR≥1,15x (tek eşik), DSRA 702.000 USD, borç servis hesabı 84.500 USD, 2 taksit/çapa noktası.

**Mekanik türetme (icat değil):** 24 taksitin tam tarih listesi (14.04.2024→14.01.2030, 3 aylık) Tansu'nun verdiği eşit-anapara/başlangıç-bitiş deseninden hesaplandı. 3 çapa noktası **tam** eşleşti: taksit #11 öncesi bakiye 1.372.000 = 2.352.000−10×98.000; 2025 yıl sonu 1.666.000 = 2.352.000−7×98.000; 2026'da ödenen #8/#9/#10, #12 vadesi 14.01.2027 — hepsi mekanik hesaba uyuyor (`debt_math.py` ile değil, elle aritmetik olarak doğrulandı; bu alan `Finance`'in `build_schedule`'ı kullanmıyor çünkü Yeşilova'nın faiz hesabı Karatepe'ninkiyle aynı yarı-yıl modeline uymuyor — 3 aylık, tek sabit oran).
**Kasıtlı tuzak:** taksit #11'in faizi — ödeme planı 18.240 USD, banka bildirimi 18.912 USD (`conflict_group: "yesilova-taksit11-faiz"`).
**Verilmeyen/pending:** capex, equity, grace_months, covenant_tests (periyodik test sonuçları yok, yalnız eşik), monthly_production, 2025'in toplam 104.500 USD'lik faiz tutarı (Annex F'ten, ayrı bir alan açılmadı — peripheral, modellenmedi), Annex F e-posta/son gün tarihleri (döküman metadata'sı, ledger alanı yok).

### Boztepe RES (30 MW, Garanti BBVA/PQR Bank)
Verilen: yalnız aylık faiz tutarı (84.300 USD) ve iki tarih (son ödenen 01.10.2026, sıradaki 02.11.2026).
**Verilmeyen/pending:** total_debt, DSCR, DSRA, tenor, faiz oranı (yalnız tutar verildi, oran yok) — **hiçbiri icat edilmedi**. KGF kefaleti Tansu'nun kendi notunda "USD proje kredisiyle tam uyuşmuyor" diye flaglanmış bir çelişki — modellenmedi (kendi kararı bekliyor).

### Güneşalan GES (18 MWp, kredisiz/özkaynak)
`finance: null`. O&M: Solaris GES İşletme Hizmetleri (3.240.000 TRY/yıl). Dava yok.

### Akyar GES (60 MWp, geliştirme) / Demirci RES (80 MW, geliştirme)
Yalnız önlisans tarihi/bitişi verildi (Akyar: 03.03.2026→03.03.2028; Demirci: 10.10.2024→10.10.2027, "36 aya uzatıldı" — mekanik hesap: 10.10.2024+36 ay=10.10.2027, icat değil). `development_start`, ÇED süreci, arazi edinimi — **verilmedi, unset kaldı**. Demirci'nin TEA olumsuz görüşüne itirazı (hukuki süreç) — belge/ledger alanı açılmadı, Hukuk partisinin işi.

### Hiçbirinde modellenmeyen (bilinçli, Hukuk partisine bırakıldı)
Boztepe imar iptali davası, Yeşilova tazminat davası, Demirci TEA itirazı — üçü de **ledger'a hiç işlenmedi** (ne bir alan ne bir not); bu round'un kapsamı "5 SPV'nin ledger gerçekleri", dava dosyaları değil.

## C4 — Kızılova'nın imzalı-kullanılmamış kredisi + imzalı-başlamamış EPC'si

`IzmirProject`'e iki yeni Optional alan (**yalnız Kızılova'ya özel** — Naci'nin düzeltmesiyle Akyar/Demirci'nin `GenericDevelopmentProject`'iyle paylaşılmıyor):

- **`SignedUndrawnFacility`** (2026-KZ): 30.000.000 USD, imzalı ama kullandırılmadı; kullandırım koşulu üretim lisansı. İmza tarihi **verilmedi** (yalnız "2026-KZ" kodundan yıl biliniyor — tam tarih icat edilmedi, unset). 05.01.2027 taahhüt komisyonu 61.333 USD = 30.000.000×%0,80×92/360 — mekanik hesap, icat değil.
- **`SignedUnstartedEpc`** (S-26-001): ABC İnşaat A.Ş. (NACI_CEVAP'ta zaten kurgusal), anahtar teslim, 10.000.000 USD (KDV hariç), imza 15.09.2026, LNTP verildi. %20 avans = 2.400.000 USD (KDV dahil); DEF Bank'tan (Akbank'ın kurgusal karşılığı) 2.000.000 USD avans teminat mektubu, vade 15.03.2028.
- **Verilmeyen/modellenmeyen:** Hakediş 1 (SÖ-26-014) tutarları — "canvas'taki gibi" deniyor ama bu depoya aktarılmadı.
- **Tansu'nun İ-1 kararı açıkça uygulandı:** Kızılova için inşaat sigortası (CAR/EAR), kullandırım talebi ve inşaat ilerleme raporu **üretilmeyecek** — ne bir belge ne bir ledger alanı eklendi.

## C5 — ECA/EUR/yerli banka/tenor tutarsızlık taraması + eval soru tablosu

### Belge/prose taraması (gerçek şablonlar grep'lendi, PDF yeniden üretilmedi — içerik `[[token]]` ile aynı kalıyor)

| Bulgu | Konum | Sorun | Önerilen düzeltme (uygulanmadı) |
|---|---|---|---|
| **Aritmetik tutmuyor** | `DOC-ANK-FIN-004` ("The total financial accommodation... is structured as [[total_debt]]. This structure comprises a local bank facility of [[local_debt]]... and an ECA facility of [[eca_debt]]...") | `total_debt` key_fact `contract_amount`'a (14,0M) işaret ediyor; `local_debt`(13,6M)+`eca_debt`(0) = 13,6M ≠ 14,0M. Okuyucu "toplam = yerli+ECA" diye okur ama tutmaz. | Bu cümleyi ikiye böl: "azami taahhüt [[contract_amount]]" (ayrı cümle) + "kullandırılan tutar, yerli banka [[local_debt]] ve ECA [[eca_debt]]'den oluşuyor" (toplamı `total_debt`'e eşit olan ayrı bir cümle). Prose dosyası `hand_edited` değil, düzenlenebilir — ama bu round'da **uygulanmadı**, Naci kararı bekliyor. |
| **"Uzatıldı" ama değişmedi** | `DOC-ANK-FIN-006` ("the maturity schedule is extended, such that the tenor of the facility is adjusted to [[tenor_years]]") | `tenor_years.current` = 13 = `tenor_years.initial` — gerçekte değişmedi, ama cümle "extended" diyor. | Cümleyi kaldır veya "the tenor of the facility remains at [[tenor_years]], unchanged by this amendment" şeklinde yeniden yaz. |
| Kozmetik (düzeltme önerisi zayıf) | `DOC-ANK-FIN-004` ("an export credit agency (ECA) facility of [[eca_debt]]=0 USD provided by the export credit agency party") | Belge-temelli, YANLIŞ değil ama "0 USD'lik bir ECA tesisi" tuhaf okunuyor. | Düşük öncelik; isteğe bağlı yeniden ifade. |

**Taranan ama bulgu çıkmayan alanlar:** literal (token olmayan) "EUR" hiçbir Karatepe prose/doküman şablonunda yok (hepsi `[[token]]` üzerinden, doğru şekilde USD'ye çözülüyor); "4 dilim"/"dört taksit" gibi sabit bir sayı hiçbir yerde hardcode değil (drawdown sayısı her zaman gerçek listeden geliyor, 4→2 geçişi otomatik düzeldi).

### Eval soru tablosu (Aşama B §5'ten taşındı, bu ledger durumuna göre yeniden doğrulandı)

| ID | Soru | Eski dayanak | Yeni durum | Önerilen sınıf |
|---|---|---|---|---|
| ANK-FIN-004, ANK-NEG-002 | "...ECA kredisi ne kadar?" | ECA gerçek bir kredi ortağıydı (30M EUR) | `eca_debt=0 USD`, belge bunu doğrudan anlatıyor | (a) olduğu gibi kalsın **veya** (b) "ECA katılımı var mı?" biçimine çevir — **Naci kararı bekliyor, değiştirilmedi** |
| ANK-FIN-013, ANK-NEG-001, ANK-NEG-003 | "...tenor'u ilk ne kadardı, şimdi ne kadar?" / "...vadesi kaç yıl?" | Tenor 12→14 gerçekten değişiyordu | Tenor 13→13 (değişmiyor); notlar güncel değil | ANK-FIN-013: DSCR'a çevrilmesi önerilir (test_eval_lib.py'da zaten bu değişiklik yapıldı — ama **soru dosyasının kendisi değiştirilmedi**); ANK-NEG-001/003: not metni güncellensin, soru/beklenti aynı kalabilir |
| ANK-FIN-015 | "...ilk kredi çekim bildirimi tutarı?" | Not: "2021-12-15, 15.000.000 EUR" (sabit metin) | Yol otomatik 2022-07-15/8.000.000 USD'ye çözülüyor (sorun yok); not metni yanlış | Not metni güncellensin (kozmetik) |
| ANK-FIN-007 | "...ilk DSCR covenant'ı neydi?" | Değişmedi (1,25) | Değişmedi, kaynak belge değişti | Değişiklik gerekmiyor |

**Hiçbiri bu round'da değiştirilmedi** — "sessizce 0 beklentisine çevirme" talimatına uyarak, hepsi Naci'nin kararına bırakıldı.

## Testler ve doğrulama

Her C-adımından sonra ayrı: `make lint` (0 hata) + `make validate-ledger` (0 hata, Karatepe'nin aynı 7 uyarısı) + `make test` (tek başına, test DB'de, 900s timeout) — **4 ayrı yeşil koşu**, 615 backend + 18 ocr-worker test, hiçbiri birden fazla tur kırılmadı (her adımda en fazla bir düzeltme turu gerekti: C1'de "BUGÜN" prompt assertion'ı).

`EK_F_MODE`/`ASSIST_MODE`: `.env`'de ve çalışan canlı backend sürecinde (`get_settings()` ile sorgulandı) **ikisi de `false`** — doğrulandı.

## Kapsam dışı bırakılanlar (bilinçli, bu round'un parçası değil)

- Karatepe'nin O&M sözleşmesi (NACI_CEVAP §3.7: Enercon Servis Türkiye, 38.500 EUR/ay, Boztepe ile aynı) — **Karatepe'nin kendi ledger'ına işlenmedi**; C5'in tutarsızlık taramasında not edildi ama Karatepe'nin kendi dosyasını değiştirmek bu round'un kapsamı dışı.
- Boztepe/Yeşilova/Demirci'nin dava dosyaları — Hukuk partisinin işi.
- SPEC_05 §6/§8/§9 — Aşama B'de "Adım 5 bitene kadar beklesin" kararı, bu round'da da geçerli.
- PF partisinin LLM belge üretimi — **bu Aşama C'nin parçası değil, ayrı onay bekliyor.**

---

**Sonraki adım:** bu rapor Naci'nin onayını bekliyor. Onaylanırsa bir sonraki round, C5'teki bulguların (prose düzeltmeleri, eval soru sınıflandırması) uygulanması veya Mali/Enerji/Hukuk partilerinden biriyle devam olabilir — karar Naci'nin.
