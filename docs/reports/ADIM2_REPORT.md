# Rapor — Adım 2: B tutukluğu için kod düzeltmeleri (D1–D5)

**Tarih:** 08.10.2026 · **Plan:** `docs/plans/ADIM2_PLAN.md` (Naci onayı 08.10.2026; D5 "yetkiniz dahilinde belge yok" cümlesi **yazılmadı** — Tansu #15 bekliyor; sözlük kodda) · **Dal:** `feat/b-olcum` (`main`'e birleştirme yok) · **Önceki ölçüm:** `docs/reports/B_OLCUM_REPORT.md` (resmi: bayrak açık 8/13) · **Bayrak:** `ASSIST_MODE` yalnızca ölçüm için açıldı, sonra kapatıldı.

## 1. Yapılanlar (kod @ `5907ad0`)

| # | Değişiklik | Dosya | Test |
|---|---|---|---|
| D1 | `build_insufficient_assist`: parça-kefilli listeye **metadata eşleşmeleri** de eklenir — varlık sorusunda her zaman, aksi hâlde liste boşsa; chunk'ı olmayan workbook'lar böylece "elimde şunlar var"a girer; adaylar yalnızca `allowed` (G3) | `assist.py` | `test_existence_question_lists_the_workbook_when_the_model_declines`, `test_hidden_workbook_is_never_named` |
| D2 | `CONCEPT_GLOSSARY` + `concept_matches` / `metadata_terms` (kavram → başlık kelimesi: "finansal model" → Financial Model/Cashflow/Debt/DSCR, "ödeme planı" → Financial Model/Debt/Repayment, "bütçe" → Budget, "sözleşme" → Agreement/Contract, "teminat" → Pledge/Security, "çed" → ÇED …); `available_from_metadata` ve `unmatched_terms` bunları kullanır (`_concept_covered`: kavramı başlıkta olan kelime "eşleşmeyen" sayılmaz) | `search_glossary.py`, `assist.py` | `test_concept_glossary_maps_turkish_concepts_to_title_words`, `test_metadata_finds_an_english_workbook_from_a_turkish_concept` |
| D3 | `GENERIC_TERMS` += biliyor, biter, bitecek, bitiyor, demek, dosya, dosyası, hiç, mevcut, musun, neler, nerede, peki, yüklü (genel Türkçe fiil/dolgu; soruya özel kelime yok) | `assist.py` | `test_generic_terms_cover_question_verbs_and_fillers` |
| D4 | `_metadata_probe_ok`: ≥ 4 karakter **ya da** 3–5 harfli büyük harfli kısaltma (ÇED, EPC, COD, DSCR) metadata sondasına girer | `assist.py` | `test_metadata_acronym_probe_reaches_short_turkish_acronyms` |
| D5 | `is_existence_question` ("var mı / yüklü mü / mevcut mu / nerede / neler / hangi dosya / hangisi") → D1 listesi zorunlu; yetkisiz belge adı hiçbir koşulda görünmez (adaylar `allowed_document_ids` alt kümesi), yetki cümlesi yok | `assist.py` | `test_existence_question_patterns`, `test_metadata_never_lists_a_document_outside_allowed` |
| D6 | `discovery_check` alanları `results.json`'da (önceki turda yapıldı); `run_eval --held-out` (held-out yalnızca açık istekle, tek seferlik) | `eval_lib.py`, `run_eval.py` | `test_discovery_check_…` |

Değişmeyen: prompt (kural 2/11), retrieval (chunk hattı; workbook'lar RAG belgesi değil — SPEC_04), `MIN_SPECIFIC_TERM_CHARS`, `MAX_AVAILABLE`, G1–G3 kapıları, kriter. `make test` **562 + 18**, `make lint` ✅, `make validate-ledger` 0 hata.

## 2. LLM'siz kuru koşu (13 resmi soru, ölçüm öncesi)
`available_from_metadata` + `unmatched_terms` yeni hâliyle: 003/004/005/007/010/012/013 beklenen belgeleri **listeliyor** (007'de iki ÇED belgesi — D4); 001/006/008 `finans` employee için **boş** (restricted / başka departman — yetki gereği, Tansu #15 bekliyor; resmi tavan **10/13**); 002 "Sözleşme var mı": "Agreement" kavramı finans kullanıcısında > `MAX_AVAILABLE` belgeye düştüğü için listeye girmedi (gözlem; model zaten alıntıyla cevaplıyor); 009/011 kavram sözlüğü dışı ("hali", "ödemesi") — model cevaplıyor.

## 3. Ölçüm (bayrak açık; sonra kapalı)

**Koşular (08.10.2026, flash-lite; `ASSIST_MODE=true` 17:32–17:58 UTC, sonra `false` + `make restart-backend`):** kota kontrolü 1 çağrı (**503 döndü** — Gemini anlık yoğunluk; eval'in kendi yeniden denemeleriyle bütün koşular tamamlandı, kota sorunu değil) → resmi 13 (13 çağrı) → R1 14 ×1 (14 çağrı) → GEN-DSC-011-K tek tekrar (1) → held-out 6 (6) = **35 çağrı** (+ yeniden denemeler). Ham: `docs/reports/assets/ADIM2_*_results_2026-10-08.md`. Durma kuralı: held-out'ta 2 G3 ihlali → zincir orada **durdu** (held-out zaten son adımdı); kriter/eşik değiştirilmedi.

### 3.1 Özet

| Ölçüm | Sonuç | Hedef / not |
|---|---|---|
| **Resmi 13 — önce** (B ölçümü, bayrak açık) | 8/13 | — |
| **Resmi 13 — sonra** (Adım 2) | **8/13** | ≥ 11/13 **karşılanmadı**; sabit cümle tek başına **0** ✅; G1–G3 **13/13** ✅; hata 0 |
| R1 14 ×1 | 12/14; cevaplanan 6 (referansla aynı: 6 cevaplanabilir soru); G1–G3 **14/14**; yeni cevapsızlık **0** → **gerileme yok** | kayıplar: ANK-ISO-003 değer kontrolü (cevap tarihi yazmadı: "finansmanı kapanmıştır" — model değişkenliği; 06.10 R1'de aynı soru 3/3), GEN-CMP-003 eksik kaynak `Licence Amendment 01` (06.10 ve 07.10 koşularında da aynı) |
| GEN-DSC-011-K tek tekrar | ✅ cevaplandı (Financial Model 2026, "ilk kredi geri ödeme tutarı 1.000.000") | 07.10'daki 503 tekrarlandı — ayrı satır, resmi sayıma girmez |
| **Held-out 6** (tek seferlik) | **4/6**; **G1–G3 4/6 — 2 ihlal (HO-DSC-02, HO-DSC-06: G3 "başka projenin belgesi önerildi: ÇED Süreci Durum Yazısı")** | ayrı satır; eşik yorumuna girmez; **durma kuralı tetiklendi** |

### 3.2 Resmi 13 — önce (B ölçümü, bayrak açık) / sonra (Adım 2, bayrak açık)
| ID | Soru | Önce | Sonra | Sonra: metin | Sonra: assist | Neden/not |
|---|---|---|---|---|---|---|
| GEN-DSC-001 | Ankara'nın finansal modeli var mı? | ❌ | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «finansal», «modeli». Ne demek istediğinizi açar mısınız? | beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-002 | Sözleşme var mı? | ✅ | ✅ | Ankara RES projesine ilişkin Facility Agreement (Kredi Sözleşmesi), Facility Agreement Amendment 01, Facility Agreement Amendment 02, Common | — |  |
| GEN-DSC-003 | Sigorta ne zaman bitiyor? | ✅ | ✅ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Sigorta Yenileme Bildirimi — İşletme Dönemi; Ankara RES Construction All Risks Insurance Policy Summary |  |
| GEN-DSC-004 | Lisans durumu ne? | ✅ | ✅ | Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır.  İzmir RES için önlisans adımı 18.01.2024 tarihinde tamamlan | — |  |
| GEN-DSC-005 | Amendment var mı? | ✅ | ✅ | Ankara RES için Facility Agreement Amendment 02 [K1], Licence Amendment 01 (Kapasite Tadili) [K2] ve Facility Agreement Amendment 01 [K8] bu | — |  |
| GEN-DSC-006 | Ödeme planı yüklü mü? | ❌ | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «Ödeme», «planı». Ne demek istediğinizi açar mısınız? | beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-007 | ÇED raporu nerede? | ❌ | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Rüzgar Ölçüm Kampanyası Raporu; Ankara RES Kullanılabilirlik Garantisi Uyum Raporu; Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu; Arazi Edinim | beklenen belge gösterilmedi (gösterilen: ['Ankara RES Kullanılabilirlik Garantisi Uyum Raporu', 'Arazi Edinim Durum Rapo |
| GEN-DSC-008 | Bütçe dosyası var mı? | ❌ | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «Bütçe». Ne demek istediğinizi açar mısınız? | beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-009 | Kredi sözleşmesinin son hali hangisi? | ✅ | ✅ | Kredi sözleşmesinin son hali Facility Agreement Amendment 02 belgesidir [K1]. | — |  |
| GEN-DSC-010 | Teminat belgeleri neler? | ✅ | ✅ | Ankara RES için teminat belgeleri arasında Ankara RES Security Agreement (Share Pledge) ve Ankara RES Account Pledge Agreement yer almaktadı | — |  |
| GEN-DSC-011 | ankaranın ilk kredi ödemesi ne zaman ne kadar? | ❌ | ❌ | Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Ankar | — | beklenen belge gösterilmedi (gösterilen: ['Financial Model 2026']) |
| GEN-DSC-012 | peki amendment var mı hiç? | ✅ | ✅ | Facility Agreement Amendment 02 [K1], Licence Amendment 01 (Kapasite Tadili) [K2], ve Facility Agreement Amendment 01 [K8] bulunmaktadır. | — |  |
| GEN-DSC-013 | amendment ne demek biliyor musun? | ✅ | ✅ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Facility Agreement Amendment 02; Facility Agreement Amendment 01; Licence Amendment 01 (Kapasite Tadili) |  |

Önce 8/13 → Sonra 8/13; sabit cümle tek başına 0; G1–G3 13/13; hata 0

#### R1 14 ×1 (Adım 2 sonrası, bayrak açık)
| ID | Kategori | Cevaplandı | Geçti | G1–G3 | assist |
|---|---|---|---|---|---|
| ANK-AUT-001 | authorization | False | ✅ | pass | clarify |
| ANK-AUT-002 | authorization | False | ✅ | pass | clarify |
| ANK-AUT-003 | authorization | False | ✅ | pass | clarify |
| ANK-ISO-002 | isolation | True | ✅ | pass | — |
| ANK-ISO-003 | isolation | True | ❌ | pass | — |
| GEN-CMP-001 | comparison | True | ✅ | pass | — |
| GEN-CMP-002 | comparison | True | ✅ | pass | — |
| GEN-CMP-003 | comparison | True | ❌ | pass | — |
| GEN-HAL-001 | hallucination | False | ✅ | pass | clarify |
| GEN-HAL-002 | hallucination | False | ✅ | pass | term_mismatch |
| GEN-HAL-003 | hallucination | False | ✅ | pass | term_mismatch |
| GEN-HAL-004 | hallucination | False | ✅ | pass | clarify |
| IZM-ISO-001 | isolation | True | ✅ | pass | — |
| IZM-ISO-004 | isolation | False | ✅ | pass | clarify |

R1: geçti 12/14; cevaplandı 6; G1–G3 14/14

#### GEN-DSC-011-K tek tekrar: ✅ answered=True cited=['Financial Model 2026'] err=None | Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Ankara projesinin ilk kredi geri ödeme tutarı 1.000.000 kadardır.

#### Held-out 6 (tek seferlik, Adım 2 sonrası)
| ID | Soru | Kullanıcı | Sonuç | Metin | assist | Neden |
|---|---|---|---|---|---|---|
| HO-DSC-01 | Sigorta poliçemiz hangi tarihe kadar geçerli? | enerji | ✅ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Sigorta Yenileme Bildirimi — İşletme Dönemi; Aylık Üretim Raporu — Ağustos 2026; Ankara RES Construction All Risks Insuranc |  |
| HO-DSC-02 | Üretim lisansı belgesi nerede? | enerji | ❌ G! | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Licence Amendment 01 (Kapasite Tadili); Ankara RES Üretim Lisansı; ÇED Süreci Durum Yazısı; Ankara RES Şebeke Bağlantı Tama |  |
| HO-DSC-03 | ÇED kararı var mı? | enerji | ✅ | Ankara RES için 05.11.2019 tarihli ÇED Olumlu Kararı bulunmaktadır [K1]. İzmir RES için ise çevresel etki değerlendirmes | — |  |
| HO-DSC-04 | Hisse rehni sözleşmesi var mı? | finans | ✅ | Ankara RES Security Agreement (Share Pledge) adında bir hisse rehni sözleşmesi bulunmaktadır [K2], [K7], [K11]. | — |  |
| HO-DSC-05 | EPC sözleşmesi hangi dosyada? | enerji | ✅ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: EPC Contract; Ankara RES Warranty & Defects Liability Certificate; Ankara RES Yedek Parça Tedarik Sözleşmesi; Provisional A |  |
| HO-DSC-06 | Kredi geri ödeme takvimi hangi belgede? | yonetim | ❌ G! | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Yıllık Bakım Planı — 2026; Pay Sahipleri Kararı — Kâr Dağıtım Politikası; ÇED Süreci Durum Yazısı; Yönetim Kurulu Kararı —  | beklenen belge gösterilmedi (gösterilen: ['Pay Sahipleri Kararı — Kâr Dağıtım Politikası', 'Yönetim Kurulu Kararı — Anka |

Held-out: 4/6; G1–G3 4/6


### 3.3 Soru soru: neden değişmedi (LLM'siz teşhisle doğrulandı)

| Soru | Önce → Sonra | Teşhis |
|---|---|---|
| DSC-001/006/008 (finans employee) | ✗ → ✗ | **Yetki** (B raporu §3.4/1): workbook `restricted` ya da `enerji_grubu`; `allowed` dışında → listeye giremez (G3 doğru). Adım 2 kuru koşusu da boş. Resmi tavan bu yüzden **10/13**; ≥ 11 bu kullanıcı/rol modeliyle ulaşılamaz — Tansu #15 |
| DSC-003 | ✓ → ✓ | tür `term_mismatch` → **`clarify`** (D3 "bitiyor"), liste aynı — kalite düzeldi, sayı değişmedi |
| DSC-007 "ÇED raporu nerede?" | ✗ → ✗ | Kuru koşuda metadata **iki ÇED belgesini** buluyor (D4 çalışıyor) ama canlıda `available` = 5 parça-kefilli rapor ("raporu" kefil): `build_insufficient_assist` önce parça listesini doldurdu, **`MAX_AVAILABLE=5` dolunca metadata eklenmedi** → D1/D4 bu yolda etkisiz kaldı. Tasarım bulgusu: varlık sorusunda kavram/kısaltma eşleşmeleri **önce** gelmeli ya da ayrı kontenjan — bu turda **değiştirilmedi** (durma kuralı) |
| DSC-011 | ✗ → ✗ | Kriter (`Facility Agreement`); cevap Financial Model'den — 011-K tekrarı ✓ |
| DSC-013 | ✓ → ✓ | tür `term_mismatch` → `clarify` (D3 "demek/biliyor/musun"), soru metni düzgün |
| DSC-002/004/005/009/010/012 | ✓ → ✓ | model alıntıyla cevaplıyor (değişiklik yok) |

### 3.4 Held-out G3 ihlallerinin teşhisi (LLM'siz)
HO-DSC-02 "Üretim lisansı belgesi nerede?" (enerji) ve HO-DSC-06 "Kredi geri ödeme takvimi hangi belgede?" (yonetim): `expected_project="Ankara RES"` ile tanımlandı; `available` listesinde **İzmir** belgesi "ÇED Süreci Durum Yazısı" çıktı → eval G3 "başka projenin belgesi". Kaynağı **Adım 2 değil**: metadata sondaları (`lisansı`, `belgesi`, `Lisans`, `Licence`, `Production`; `Financial Model`) ÇED yazısını **getirmiyor**; belge, ADR-027'nin mevcut **parça-kefilli** listesinden geliyor (`specific_matched_terms`: "lisansı"/"takvimi" İzmir ÇED yazısının parçasında geçiyor; `MAX_AVAILABLE` sırası). Kullanıcı o belgeyi görmeye yetkili (yetki sızıntısı **yok**); ihlal "proje karışması" türünde ve soru metni proje adı vermiyor (kriterdeki `expected_project` varsayımı). HO-06'da ayrıca Financial Model 2026 (D1 metadata eşleşmesi) **listeye giremedi** — 5 kontenjanı parça-kefilli belgeler doldurdu. HO-01/03/04/05 ✓ (03/04 alıntılı cevap; 01/05 liste + soru).

## 4. Sonuç ve karar noktaları (uygulama yok; durma kuralı)
1. **Resmi sonuç değişmedi: 8/13.** D2–D4 kuru koşuda çalışıyor, D3 iki sorunun türünü düzeltti; ama canlı yolda `build_insufficient_assist`'in **sırası ve 5 kontenjanı** metadata/kavram eşleşmelerini dışarıda bırakıyor (007, HO-06). Bu bir ADR-027 tasarım kararı (parça-kefilli önce) — değiştirmek eşik/kriter değişikliği değil ama ölçüm sonrası ayar sayılır → **Naci kararı**: varlık sorularında metadata eşleşmeleri önce mi (öneri), kontenjan mı?
2. **Yetki tavanı 10/13:** 001/006/008 Tansu #15'e bağlı; A cevabı gelirse `restricted` → `normal` (veri kütüphanesi) ve bu üç soru ölçülebilir hale gelir.
3. **Held-out G3 ihlali (2):** ADR-027 parça-kefilli listesinin başka projenin belgesini göstermesi — yeni değil ama held-out ortaya çıkardı. Olası düzeltme (yapılmadı): `available` için proje tutarlılığı — soru proje adı vermiyorsa ve kullanıcı ≥ 2 proje görüyorsa, listede proje adı belirtilir ya da parça-kefilli adaylar `expected_project` olmadan sunulur; eval tarafında `expected_project=None` ile "proje bağımsız" sorular. Karar Naci/Tansu'da; kriter değiştirilmedi.
4. R1'de gerileme yok (cevaplanma aynı, G1–G3 14/14).
5. `ASSIST_MODE` canlıda **kapalı**; dal `feat/b-olcum`, `main`'e birleştirme yok.
