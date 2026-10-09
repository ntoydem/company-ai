# Adım 5, Aşama A Raporu — Veri Kütüphanesi: Ledger/Şema + Yeniden Adlandırma + Kuru Koşu

**Tarih:** 09.10.2026  **Model:** Sonnet 5  **Dal:** `feat/adim5-veri-kutuphanesi`  **Tag:** yok (Aşama A ara adım; Adım 5 tamamlanınca etiketlenecek)

Bu rapor, Naci'nin "AŞAMA A'yı uygula (LLM çağrısı YOK)" talimatının a–d maddelerini kapsar: ledger/şema genişletmesi, mevcut 70 belgenin 0-LLM yeniden adlandırma + Tansu §3 verileriyle yeniden üretimi, test DB'de retrieval-only kuru koşu, ve güncellenen eval sorularının listesi. **Canlı DB'ye dokunulmadı, canlı Gemini çağrısı yapılmadı.**

## 0. PR #17 durumu (ADIM5_PLAN.md'den taşındı)

Tansu, T-1..T-9'un blocking olanlarına (T-3 bütçe departmanı, T-7 demo "bugün" tarihi, T-8 klasör partisi, T-9 firma isimleri) henüz cevap vermedi. Naci'nin 4 varsayımı (T-3, T-7, T-8, T-9 — hepsi onaylı) bu round'da aynen uygulandı; T-7 (demo_today değişikliği) **uygulanmadı**, bkz. §1.

## 1. Kapsam daraltma kararları (raporda şeffaf, henüz Naci onayı beklemiyor — bilgilendirme)

Aşama A'nın "ledger/şema" maddesi, mevcut `ledger_schema.py`/`validate_ledger.py`'nin **tam olarak 2 bespoke proje şekline** (Ankara/Karatepe, İzmir/Kızılova) hardcode edilmiş olduğunu ortaya çıkardı — plan metninin ima ettiğinden çok daha rijit. Üç bilinçli kapsam daraltması yapıldı:

1. **`demo_today` değiştirilmedi** (hâlâ `2026-09-15`). Değiştirmenin etki alanı çok geniş (her temporal eval sorusu, `Settings.demo_today`, `.env`, tüm covenant/DSCR/outstanding hesapları); bu round'un kapsamı dışına alındı.
2. **5 yeni SPV (Yeşilova RES, Boztepe RES, Güneşalan GES, Akyar GES, Demirci RES) yalnızca `company.yaml`'da hafif bir `CompanySpv` kayıt girişi aldı** (ad, %100 XYZ Enerji A.Ş. hissedarlığı) — kendi `seed_data/master/*.yaml` ledger dosyaları, belgeleri veya `CompanySpv`'den daha derin bir ledger şekli **yok**. Şemanın tam genelleştirilmesi (N-proje) Aşama A'nın kapsamından çok daha büyük bir iş; sonraki partiler (Enerji/Hukuk/Mali) için bir ön koşul olarak not edilir.
3. **Kızılova RES'in `finance`/`construction` alanları `None` kaldı** (şema tasarımı zaten böyle zorluyor — `IzmirProject.finance: None`). Tansu'nun Kızılova için verdiği LNTP/EPC-imzalandı/30M USD-imzalı-kullanılmamış gibi finans/EPC gerçekleri **bu round'da modellenmedi**. Bu, Hukuk/Enerji/Mali partilerinden önce çözülmesi gereken bir blocker olarak işaretlendi.

## 2. (a) Ledger/şema değişiklikleri

`seed_data/generator/ledger_schema.py`:
- `Fact`/`Money`: `deliberate_conflict: bool = False`, `conflict_group: str | None = None` eklendi.
- `Interest.margin_pct: Fact` → `ChangedFact` (Karatepe'nin marjı değişti: 3,25% → 2,90%).
- `Finance.contract_amount: Money | None = None` eklendi — **kasıtlı tuzak** için (bkz. §3): sözleşmede yazan tutar (14.000.000 USD) artık fiilen kullandırılan/ödenecek tutardan (`total_debt`, 13.600.000 USD) ayrı bir alan.
- `Finance.dsra_balance: Money | None = None` eklendi (Tansu §3.2: DSRA bakiyesi).
- `AnkaraProject.name` → `Literal["Karatepe RES"]`; `IzmirProject.name` → `Literal["Kızılova RES"]`.
- `IzmirTimeline.pre_licence_expiry: Event` eklendi (Tansu §3.1: önlisans bitişi 15.01.2027).
- `CompanySpv.project_code` Literal'ı 7 koda genişletildi; `Question.expected_project` Literal'ı 7 yeni Türkçe gösterim adına genişletildi.
- `SPEC_FICTIONAL_NAMES`: `"ABC Enerji A.Ş."` → `"XYZ Enerji A.Ş."`; eski tek-paylaşılan `"DEF Enerji Üretim A.Ş."` kaldırıldı (artık 7 SPV'nin her biri kendi adını taşıyor, hepsi `company.yaml`'ın `name_whitelist`'inde). **`docs/SPEC_05_*.md` §4'ün aynı güncellemeyi alması gerekiyor — bu round'da yapılmadı, flaglanıyor.**

`seed_data/generator/validate_ledger.py`:
- Yeni `find_conflict_groups`/`check_conflict_groups` — ham YAML ağacında herhangi bir `conflict_group` etiketi bulup (a) grubun ≥2 üyesi olmasını, (b) her üyenin `deliberate_conflict: true` taşımasını zorunlu kılar (işaretsiz çelişki = hata, Naci'nin kuralı). Şemadan bağımsız, genel bir yürüyücü (mevcut `count_tags` deseniyle aynı tarzda).
- `check_debt_schedule`: `margin_pct.value` → `margin_pct.current.value` (ChangedFact'e geçiş).
- `QUOTAS` (`{"Ankara RES": 35, "İzmir RES": 12}`) → yeni adlarla güncellendi.

**Kabul:** `make validate-ledger` → **0 hata**, 7 kabul edilen uyarı (§6).

## 3. (b) 70 belgenin 0-LLM yeniden adlandırma + Tansu §3 verileriyle yeniden üretimi

### 3.1 Kod/kimlik değişmezliği (SORU 1)

`ANK_RES`/`IZM_RES` kodları ve `DOC-ANK-*`/`DOC-IZM-*` ID önekleri **hiç değişmedi**. Değişen yalnızca görünen ad: proje adı, SPV tüzel kişilik adı, holding adı, belge başlıkları, prose metni, Excel etiketleri. Bu, her çapraz referansı (belge ID'leri, `PROJECT_PREFIX`, manifest dosya adları) sıfır risk ile sağlam tuttu.

Doğrulandı: `grep` ile prose şablonlarında (`seed_data/generator/prose/*.yaml`) **hiçbir literal taraf/proje adı yok** — tüm literal adlar üç master YAML'da yaşıyor; bu, 70 belge yeniden adlandırmasının gerçekten 0-LLM (saf veri ikamesi) olduğunun kanıtı.

### 3.2 İsim değişiklikleri

| Eski | Yeni |
|---|---|
| ABC Enerji A.Ş. (holding) | XYZ Enerji A.Ş. |
| Ankara RES | Karatepe RES |
| İzmir RES | Kızılova RES |
| DEF Enerji Üretim A.Ş. (Karatepe SPV) | Karatepe RES Enerji Üretim A.Ş. |
| DEF İzmir Rüzgar Enerji A.Ş. (Kızılova SPV) | Kızılova RES Enerji Üretim A.Ş. |
| XYZ Wind Turbines GmbH | RST Turbines GmbH (kendi kararım — SORU 3'ün banka-adı mantığı OEM isimlerine de uygulandı, yeni holding adıyla karışmasın) |
| GHI Yatırım A.Ş. (%20 Karatepe ortağı) | Kaldırıldı (bought out); yalnızca tarihsel belgelerde (`DOC-CO-ADM-003`) kalır |

Karatepe ve Kızılova'nın SPV hissedarlığı artık tek satır: **XYZ Enerji A.Ş. — %100**.

### 3.3 Karatepe RES — Tansu §3.2 finansal verisi

| Alan | Eski | Yeni | Not |
|---|---|---|---|
| Kapasite | 48→60 MW (EUR dönemi) | **22→24 MW** | `initial`=22 AI_ASSUMPTION (Tansu yalnız güncel 24'ü verdi; mevcut DOC-ANK-DEV-002 "Licence Amendment 01" belgesinin anlatısı bozulmasın diye küçük bir gerçek değişiklik korundu) |
| Türbin | 12× 5,0 MW sınıfı | **8× 3,0 MW sınıfı** (marka adı yok) | 8×3,0=24 ✓ |
| Finansman imza/close | 2021-09-30 / 2021-11-15 | **2021-11-20 / 2021-11-25** (AI_ASSUMPTION) | Tansu bir tarih vermedi; `construction_start` (2022-01-10, değişmedi) ile kronolojik tutarlılık (C1) için seçildi |
| Faiz bazı | EURIBOR 6M | **Term SOFR 6M** | |
| Faiz marjı | 3,25% (sabit) | **3,25% → 2,90%** (ChangedFact, AMD02 ile) | |
| Tenor | 12→14 yıl | **13→13 yıl** (değişmedi) | Tansu bir tenor değişikliği belirtmedi; `changed_by` F4 kuralı için nominal olarak AMD01'e (konsolidasyon) işaret ediyor |
| DSCR covenant | 1,25→1,20 | **1,25→1,20** (değişmedi, zaten eşleşiyordu) | Şans/kasıt — doğrulandı, düzenleme gerekmedi |
| **Sözleşme tutarı** (`contract_amount`, yeni alan) | — | **14.000.000 USD** | Kasıtlı tuzak — bkz. aşağı |
| **Fiilen kullandırılan/ödenecek** (`total_debt`) | 50.400.000 EUR | **13.600.000 USD** | Kasıtlı tuzak — bkz. aşağı |
| Drawdown'lar | 4 dilim, 50,4M EUR | **2 dilim: 2022-07-15 8,0M + 2023-01-15 5,6M USD = 13,6M** | |
| Outstanding (15.09.2026) | 44.100.000 EUR | **11.671.800 USD** | `debt_math.py` ile doğrulandı (§3.4) |
| DSRA bakiyesi | — | **1.240.000 USD** (yeni alan) | |
| Capex / Equity | 72M / 21,6M EUR | **20.000.000 / 6.400.000 USD** (AI_ASSUMPTION) | `total_debt + equity = capex` (F2): 13,6M+6,4M=20M ✓ |

**Kasıtlı tuzak (Tansu'nun "14,0M vs 13,6M" senaryosu):** `contract_amount` (sözleşmede yazan tesis büyüklüğü, 14,0M) ile `total_debt` (fiilen kullandırılan/ödeme planındaki toplam, 13,6M — `drawdowns` ve `repayment_schedule` toplamıyla aynı) bilinçli olarak farklı. Her ikisi `deliberate_conflict: true, conflict_group: "karatepe-kredi-tutari"` ile etiketli; yeni `check_conflict_groups` kuralı bunu doğruluyor. `DOC-ANK-FIN-004` (orijinal sözleşme) ve `DOC-ANK-FIN-010` (Common Terms Agreement) `contract_amount`'a işaret ediyor (14,0M anlatıyor); `DOC-ANK-FIN-007` (Covenant Report) `total_debt`'e işaret ediyor (13,6M anlatıyor) — bu, "kredi tutarı ne kadar?" sorusunun belgeye göre farklı cevap vereceği, kasıtlı bir demo tuzağı.

**Tadil zinciri** (ID sırası = kronolojik sıra korunuyor, dondurulmuş prose içerikle tutarlı):
`DOC-ANK-FIN-004` (orijinal, 2021-11-20) → `DOC-ANK-FIN-005` ("Amendment 01", **2024-01-12**, konsolide metin, sayısal değişiklik yok) → `DOC-ANK-FIN-006` ("Amendment 02", **2025-03-15**, DSCR 1,25x→1,20x + marj 3,25%→2,90%, Q4_2024 ihlaline yanıt).

### 3.4 Debt math doğrulaması (gerçek kod ile, el hesabıyla değil)

`debt_math.build_schedule`/`outstanding_on`/`quarterly_debt_service` doğrudan çalıştırılarak doğrulandı:
- `sum(drawdowns) == sum(repayment_schedule.principal) == 13.600.000` (F11)
- 8. taksit = **412.500 USD**, tarih **2026-10-07** (Tansu'nun verdiği anchor, tam eşleşiyor)
- 9. taksit tarihi **2027-04-07** (Tansu'nun verdiği ikinci anchor; tutarı o vermedi, AI_ASSUMPTION)
- Son taksit **2034-10-07** ≤ finansal close (2021-11-25) + tenor (13 yıl) = 2034-11-25 (F11)
- `outstanding_on(..., 2026-09-15) = 11.671.800` — ledger'daki `outstanding_debt_as_of_demo_today` ile **tam** eşleşiyor (F9)
- 11 çeyreklik CFADS/debt-service oranı, `covenant_tests.dscr`'nin 11 değerine (1,42 → 1,37) **≤0,01 tolerans** içinde eşleşiyor (F10) — hesaplama CURRENT (2,90%) marjla, `check_debt_schedule`'ın kendi mantığıyla birebir

### 3.5 Kızılova RES — Tansu §3.1 verisi

- Kapasite hedefi: 80 → **42 MW**
- Yeni `pre_licence_expiry`: **15.01.2027**
- SPV hissedarlığı: ABC Enerji A.Ş. %100 → **XYZ Enerji A.Ş. %100**
- `finance`/`construction`: **None kaldı** (§1 madde 3)

### 3.6 Diğer kodda yeniden adlandırma sweep'i

Ledger/belge dışında, LIVE koda ve araçlara sızmış literal "Ankara RES"/"İzmir RES" string'leri bulundu ve düzeltildi (hepsi görünen-ad, 0 davranış değişikliği):
- `backend/app/services/demo_projects_seed.py` — **kritik**: test/live DB'ye proje adı seed eden tuple; düzeltilmeseydi test DB'deki kuru koşu, yeniden adlandırılmış belge içeriğiyle eşleşmeyen eski proje adlarına karşı çalışacaktı. Mevcut satırlar değiştirilmez (`DemoSeedResult`, idempotent create-if-missing) — canlıya hiçbir etkisi yok, yalnızca **yeni** bir reseed'de etkili olur.
- `scripts/eval_lib.py::_PROJECT_NAME_BY_CODE` — eval/dry-run makinesinin proje-adı haritası.
- `backend/app/services/router.py`, `answer_prompt.py` — LLM prompt'larındaki örnek cümlelerde proje adı; `make prompt-doc` ile `docs/prompts/*.md` yeniden senkronize edildi.
- `seed_data/generator/document_specs/*.py` (7 dosya) — her belgenin kapak sayfası/alt başlığı (`subtitle_tr`/`subtitle_en`/`subject_label_tr`) literal proje adı taşıyor (token değil); hepsi yeniden adlandırıldı.
- `seed_data/generator/facts.py::_project_name` — `[[project_name]]` token'ının çözdüğü harita.
- `backend/app/api/documents.py` — docstring örneği (kozmetik).

## 4. (c) Test DB'de retrieval-only kuru koşu

**Canlı DB'ye dokunulmadı.** `DATABASE_URL`, hem `backend` hem `ocr-worker` için tek seferlik `docker compose run` çağrılarında `TEST_DATABASE_URL`'e yönlendirildi (ayrı, boş `company_ai_test` veritabanı — canlı servislerin kendisi hiç durdurulmadı/yönlendirilmedi). `ocr-worker` detached başlatıldı, 74 belge "ready" olana kadar beklendi, sonra durduruldu/kaldırıldı. Kuru koşu bitince test DB tekrar `TRUNCATE ... CASCADE` ile temizlendi (pytest'in kendi `autouse` fixture'ının zaten yaptığı şey, elle tekrarlandı ki sıradaki `make test` kirli veriyle başlamasın).

`scripts/dry_run_project_axis.py` (0-LLM, gerçek retrieval + gerçek `classify_project_axis`) Adım 4'ün 9+5+1 soru setiyle yeni korpusta çalıştırıldı. **Eşikler (`PROJECT_AXIS_DISAMBIG_SPREAD=0.5`, `PROJECT_AXIS_DOMINANT_SHARE=0.75`) değiştirilmedi.**

| Ölçüm | Eski korpus (Adım 4) | Yeni korpus (Adım 5, bu round) |
|---|---|---|
| Dev AMB (orijinal 5, hedef ≥4/5) | **3/5** (GEN-AMB-001 ❌ dominant, GEN-AMB-002 ❌ none) | **3/5** (aynı iki soru, aynı sınıflandırma) |
| Dev AMB (yeni, GEN-AMB-006) | 1/1 ✅ | 1/1 ✅ |
| Dev NEG yanlış alarm (9, hedef 0/9) | **0/9** | **0/9** |
| ANK-NEG-004 == dominant/ANK_RES | ✅ | ✅ |

**Sonuç: ❌ kaldı (3/5 < 4/5, hedef karşılanmadı) — Adım 4'teki durumun aynısı.** Yeniden adlandırma/finansal realignment, GEN-AMB-001/002'nin kök nedenini (korpus-gereği gerçekten belirsiz olmaması — İzmir/Kızılova'da hâlâ ilgili belge türü yok) değiştirmedi; beklenen ve doğrulandı. Kriter gevşetilmedi, sonuca bakarak hiçbir eşik değiştirilmedi.

## 5. (d) Güncellenen eval soruları

### 5.1 Blanket yeniden adlandırma (yalnız görünen ad; kod/beklenti davranışı değişmedi)

`seed_data/evaluation/questions.json`'daki **tüm** soru metni, `expected_project` değeri, `required_sources`/`forbidden_sources` ve `notes` alanlarında "Ankara RES"→"Karatepe RES", "İzmir RES"→"Kızılova RES" (ve bağlı Türkçe iyelik ekleri) uygulandı — 90+ girdi. Bu salt kozmetik; `version`/soru sayısı değişmedi (99 soru + held-out, v9).

### 5.2 Değer gerçekten değişti (ledger yolu aynı kaldı, çözülen değer değişti — SORU 6 kuralı: yalnız veri değiştiği için güncellendi, beklenti zayıflatılmadı)

| ID | Soru | Değişen alan |
|---|---|---|
| ANK-DEV-003, ANK-DEV-004, ANK-DEV-006, ANK-EPC-005, GEN-CMP-003 | kapasite | `capacity_mw.initial/current` (48/60→22/24) |
| ANK-DEV-005 | lisans tadili tarihi | `timeline.licence_amendment.date` (not metni güncellendi) |
| ANK-FIN-001, ANK-ISO-003 | financial close tarihi | `timeline.financial_close.date` |
| ANK-FIN-002 | toplam kredi | `finance.total_debt.value` (50,4M EUR→13,6M USD) |
| ANK-FIN-003 | yerli banka kredisi | `finance.local_debt.value` |
| ANK-FIN-004, ANK-NEG-002 | ECA kredisi | `finance.eca_debt.value` (30M EUR→0 USD) |
| ANK-FIN-005 | faiz bazı/marjı | `finance.interest.margin_pct` (**yapısal**: Fact→ChangedFact, yol `.current.value` oldu) |
| ANK-FIN-006, ANK-MIX-001 | güncel DSCR | `finance.dscr_covenant.current.value` |
| ANK-FIN-007 | ilk DSCR | `finance.dscr_covenant.initial.value` (değişmedi ama kaynak belge/tarih değişti) |
| ANK-FIN-008, ANK-FIN-009, GEN-AMB-003-F | facility_chain / amendment sayısı | `finance.facility_chain` |
| ANK-FIN-010 | son covenant testi sonucu | `finance.covenant_tests[-1]` |
| ANK-FIN-011 | outstanding borç | `finance.outstanding_debt_as_of_demo_today.value` (44,1M EUR→11,67M USD) |
| ANK-FIN-012 | DSCR değişikliği belgesi/tarihi | `finance.dscr_covenant.changed_by` |
| ANK-FIN-013 | tenor ilk/güncel | `finance.tenor_years` (14→12'den 13→13'e; artık **değişmiyor**) |
| ANK-FIN-014 | Q4 2024 DSCR | `finance.covenant_tests[4].dscr` |
| ANK-FIN-015 | ilk drawdown tutarı | `finance.drawdowns[0].amount.value` |
| ANK-DAT-001, ANK-DAT-003 | 2026 Q2 DSCR / kalan borç | aynı alanlar |
| ANK-EPC-001, ANK-EPC-002, ANK-EPC-004 | EPC fiyatı/dokümanı/sapma nedeni | değişmedi ama çapraz referans güncellendi |
| IZM-DEV-005, IZM-DEV-006, IZM-ISO-004, HO-NEG-01, GEN-CMP-001, GEN-CMP-002 | önlisans/inşaat/finansman tarihleri | Kızılova timeline (değişmedi, ama proje adı/çapraz ref güncellendi) |
| IZM-ISO-001, IZM-DEV-010 | hedef kapasite | `capacity_mw.target.value` (80→42) |
| IZM-DEV-011 | önlisans tarihi referansı | `timeline.pre_licence.date` (değişmedi) |
| ANK-NEG-001, ANK-NEG-003 | kredi tenor'u | `finance.tenor_years.current.value` |
| HO-NEG-02, HO-NEG-03 | DSCR / EPC müteahhit | değişmedi, format/kaynak kontrolü |

(44 soru toplam; tam liste yukarıdaki satırlarda — bazı ID'ler birden fazla alanı kapsadığı için grup halinde gösterildi.)

### 5.3 Yapısal/mekanizma düzeltmeleri

- **ANK-FIN-005**: `expected_answer` yolu `project.finance.interest.margin_pct.value` → `.current.value` (şema değişikliği, ChangedFact).
- **ANK-COR-001** (GHI'nin tarihsel %20'si) ve **HO-NEG-04** (aynı yol, held-out): `expected_answer`, artık var olmayan `company.spvs[0].shareholders[1].share_pct.value` yolundan **literal `"20"`**'ye çevrildi (GHI artık ortaklık yapısında bir satır değil; gerçek **%20**, DOC-CO-ADM-003'ün statik metninde sabit kaldı). Bu, `scripts/eval_lib.py::_resolve_one`'da genel bir eksikliği ortaya çıkardı: `ledger:` öneki olmayan bir `expected_answer` daha önce hiç desteklenmiyordu (validator onu zaten "kontrol gerektirmez" sayıyordu ama scoring tarafı patlıyordu). **Düzeltme**: `_resolve_one`, `ledger:` önekiyle başlamayan bir string'i artık doğrudan literal bir gereksinim olarak kabul ediyor — validator'ın zaten var olan niyetini tamamlıyor, yeni bir ürün kararı değil.

## 6. Kabul edilen uyarılar (düzeltilmedi, bilinçli)

- **M2** (6 uyarı): "loan amounts are EUR by decision" — SPEC'in varsayılan kararı (kredi tutarları EUR) Karatepe için artık geçerli değil; Tansu §3.2 açıkça USD veriyor. Bilinçli, kayıtlı sapma.
- **T1** (1 uyarı): "8 türbin × ~5 MW ≈ 40 MW, declared capacity_mw.current is 24 MW" — validator'ın hardcoded 5 MW/türbin varsayımı, Karatepe'nin seçilen 3,0 MW'lık türbin modeliyle uyuşmuyor. 8×3,0=24 MW matematiksel olarak doğru; validator'ın heuristiği genel/varsayılan bir türbin boyutu için yazılmış.

## 7. Testler

- `make lint`: **temiz** (ruff + mypy + validate-ledger/documents/excel, 0 hata).
- `make test` (tek başına, 900s timeout, test DB'de): **609 backend + 18 ocr-worker test, tümü yeşil**. İlk tam koşuda 39, sonra 6 test kırıldı (sırasıyla: proje adı Literal'ına artık uymayan test fixture'ları, Karatepe'nin eski EUR rakamlarını hardcode eden `test_excel_engine.py`, FIN-005/006'nın rol değişimiyle tutarsızlaşan `test_ask.py`/`test_generate_prose_guard.py`, ve §5.3'teki `eval_lib.py` eksikliği) — hepsi kök nedenine kadar izlendi ve düzeltildi, hiçbiri `skip`/`xfail` ile atlanmadı.
- `EK_F_MODE`/`ASSIST_MODE`: `.env`'de ve çalışan canlı backend sürecinde (`get_settings()` ile sorgulandı) **ikisi de `false`** — doğrulandı.

## 8. Kendi aldığım küçük kararlar (raporda listelendi, raporda da listelenecek)

- Karatepe'nin türbin markası verilmedi (SORU 3'ün banka-adı mantığı OEM isimlerine de uygulandı): "3,0 MW sınıfı kara tipi türbin" — jenerik, marka adı yok.
- Karatepe'nin kapasite tadili belgesinin (DOC-ANK-DEV-002) anlatısı korunsun diye küçük bir gerçek kapasite değişikliği (22→24 MW) icat edildi — Tansu bunu söylemedi ama reddetmedi de; AI_ASSUMPTION olarak etiketli.
- Capex/equity (20M/6,4M USD) standart %70/30 borç/özkaynak oranından türetildi — Tansu bu ikisini vermedi.
- Grace süresi (~10 ay) imza-ilk taksit boşluğundan türetildi.
- FIN-005/FIN-006'nın hangisinin AMD01 (konsolidasyon) / AMD02 (DSCR değişikliği) olduğu, belge ID sırası = kronolojik sıra korunacak şekilde seçildi; dondurulmuş (hand-edited) prose içeriği buna uyacak şekilde iki dosya arasında taşındı (LLM çağrısı yok — yalnızca metin elle taşındı).

## 9. Açık sorular / sonraki adımlar

- `docs/SPEC_05_*.md` §4'ün yeni isim listesiyle güncellenmesi gerekiyor (bu round'da yapılmadı).
- Kızılova'nın finans/EPC gerçekleri (LNTP, 30M USD imzalı-kullanılmamış kredi) şemanın `IzmirProject.finance: None` kısıtı kaldırılmadan modellenemiyor — Hukuk/Enerji/Mali partilerinden önce çözülmesi gerekiyor.
- 5 yeni SPV'nin tam ledger dosyaları (yalnızca `company.yaml` kaydı var) — plan sırasında hangi partinin bunları dolduracağı netleşmeli.
- `demo_today` değişikliği (Tansu'nun önerdiği 06.10.2026) hâlâ beklemede, geniş etki alanı nedeniyle bu round'a dahil edilmedi.

---

**PF partisinin LLM belge üretimi bu Aşama A'nın parçası DEĞİL — ayrı onay bekleniyor.**
