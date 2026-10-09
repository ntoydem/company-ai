# Adım 1 — Soru 15: Financial Model `restricted → normal` (kısa rapor)

**Tarih:** 09.10.2026 · **Plan:** `docs/plans/URUN1_KARARLAR_VE_SIRA.md` §3.2 adım 1 (Naci onayı 09.10.2026) · **Karar:** Tansu Soru 15 → **A** (`NACI_CEVAP_2026-10-08.md` §1: finansal model, ödeme planı ve bütçe workbook'u `normal`; bordro/dava `restricted` kalır; P-2 aynen) · **Dal:** `feat/adim1-soru15` (`feat/b-olcum` üzerinden; `main`'e birleştirme yok) · **Önceki ölçüm:** `ADIM2_REPORT.md` resmi 13 → **8/13** · **Tavan beklentisi:** 10/13 (yalnızca DSC-001 ve DSC-006 yetki kaynaklıydı) · **Bayrak:** `ASSIST_MODE` yalnızca ölçüm için açıldı (13:09–13:16 UTC), sonra kapatıldı ve `make restart-backend` ile doğrulandı (`assist_mode_enabled = False`).

## 1. Ne değişti

| # | Değişiklik | Dosya | Not |
|---|---|---|---|
| 1 | `DOC-ANK-FIN-008` (Financial Model 2026) `confidentiality: restricted → normal` | `seed_data/master/ankara_res.yaml` | Ledger'daki **tek** `restricted` satırdı; artık demo sette `restricted` belge yok (`board` var: DOC-CO-ADM-001). |
| 2 | Excel üreticisi gizliliği **ledger'dan** okur | `seed_data/generator/generate_excel.py` | Bulgu: `WorkbookSpec` içinde `"restricted"` sabit yazılıydı (ikinci kaynak). Alan spec'ten kaldırıldı, `_ledger_confidentiality(raws, doc_id)` eklendi. |
| 3 | Excel manifest yeniden üretildi, yalnızca manifest alındı | `seed_data/excel/manifest.json` | Üretici geçici klasöre koşturuldu; `generated_at` dışında tek fark `confidentiality`. Commit'li `.xlsx` dosyalarına dokunulmadı (LibreOffice recalc gerekmedi); `make validate-excel` 0 hata. |
| 4 | Tek belge yeniden seed: `seed-demo-documents --refresh REF[,REF]` | `demo_documents_seed.py` (`refresh_demo_document_metadata`), `cli.py` | Seed create-if-missing olduğu için mevcut satırı değiştirmiyordu. Yeni opt-in yol yalnızca **kapı alanlarını** (department, subdepartment, confidentiality, project) manifest'e eşitler; başlık/etiket/personel düzenlemelerine dokunmaz; önce/sonra değerleri loglanır. Elle SQL yok; prod'da aynı komut. |
| 5 | Testler | `test_demo_documents_seed.py` (+2), `test_authorization.py` (+1) | (a) seed sonrası FIN-008 `normal`, sette `restricted` yok; (b) refresh: eski duruma getirilen satır manifest'e döner, adlandırılmayan FIN-009 ve personel düzenlemesi (başlık) korunur, bilinmeyen ref `found=False`, ikinci koşu değişiklik 0; (c) **uçtan uca SQL sağlayıcıyla**: `finans` (employee) FIN-008'i görür, aynı departmanın `restricted` belgesi ve `board` belge hâlâ dışarıda. |

**Aynı aileden listelenen, değiştirilmeyen belgeler (T-3 Tansu cevabı bekliyor):**

| Ref | Başlık | Departman | Gizlilik | Not |
|---|---|---|---|---|
| DOC-ANK-FIN-009 | Covenant Report (workbook) | finans | normal | zaten görünür |
| DOC-ANK-OPS-002 | Budget vs Actual 2026 | **enerji_grubu** / enerji_bakim | normal | finans göremez — sebep departman, gizlilik değil (T-3) |
| DOC-ANK-OPS-003 | Monthly Production 2026 | enerji_grubu / enerji_bakim | normal | — |
| DOC-ANK-ADM-001 | Budget Approval | mali_isler | normal | bütçe onayı (PDF), finans göremez |

Ayrı "ödeme planı" belgesi yok; ödeme planı Financial Model'in `Debt` sayfası.

## 2. Doğrulama

| Kontrol | Sonuç |
|---|---|
| `make test` | backend **565 passed** (15 deselected = canlı LLM testleri), ocr-worker 18 passed |
| `make lint` | ruff + format + mypy + prompt dokümanı ✅ (bir format düzeltmesi sonrası) |
| `make validate-ledger` | 0 hata, 0 uyarı (USER_FACT 269, AI_ASSUMPTION 278) |
| `make validate-excel`, `validate-documents --prose-only` | 0 hata |
| Canlı DB | `seed-demo-documents --refresh DOC-ANK-FIN-008` → `changed: {confidentiality: [restricted, normal]}`; sorgu: 76 belgede `restricted` 0 |

## 3. Ölçüm — resmi 13 keşif sorusu ×1, bayrak açık, 13 çağrı (flash-lite, 26 sn aralık, 13:10–13:15 UTC)

Ham: `docs/reports/assets/ADIM1_dsc_results_2026-10-09.md`. Kriterler `B_OLCUM_REPORT.md` §1'deki gibi, **değiştirilmedi**.

| ID | Soru | Kullanıcı | Önce (08.10) | Sonra (09.10) | Sonra ne oldu |
|---|---|---|---|---|---|
| GEN-DSC-001 | Ankara'nın finansal modeli var mı? | finans | ❌ | ✅ | DATA_QUERY: Excel'den "Evet, … mevcuttur; Capex 72000000 EUR, Özkaynak 21600000 EUR … 2021-11-15 00:00:00" — kaynak Financial Model 2026 |
| GEN-DSC-002 | Sözleşme var mı? | finans | ✅ | ✅ | 7 sözleşme listelendi |
| GEN-DSC-003 | Sigorta ne zaman bitiyor? | enerji | ✅ | ✅ | clarify + Sigorta Yenileme Bildirimi, CAR poliçe özeti |
| GEN-DSC-004 | Lisans durumu ne? | enerji | ✅ | ✅ | iki proje ayrı ayrı |
| GEN-DSC-005 | Amendment var mı? | yonetim | ✅ | ✅ | 3 amendment |
| GEN-DSC-006 | Ödeme planı yüklü mü? | finans | ❌ | ✅ | clarify + **Financial Model 2026** listede (kavram sözlüğü "ödeme planı" → Financial Model, Adım 2 D2) |
| GEN-DSC-007 | ÇED raporu nerede? | enerji | ❌ | ❌ | clarify + 5 belge, ama **Ankara RES ÇED Olumlu Kararı yok** (bkz. §4) |
| GEN-DSC-008 | Bütçe dosyası var mı? | finans | ❌ | ❌ | `term_mismatch` «Bütçe», liste boş (bkz. §4) |
| GEN-DSC-009 | Kredi sözleşmesinin son hali hangisi? | finans | ✅ | ✅ | Amendment 02 |
| GEN-DSC-010 | Teminat belgeleri neler? | finans | ✅ | ✅ | Share Pledge + Account Pledge |
| GEN-DSC-011 | ankaranın ilk kredi ödemesi ne zaman ne kadar? | yonetim | ❌ | ❌ | MIXED: Excel'den "ilk kredi geri ödeme tutarı 1.000.000 kadardır"; `required_sources` Facility Agreement atıfsız (bkz. §4) |
| GEN-DSC-012 | peki amendment var mı hiç? | yonetim | ✅ | ✅ | 3 amendment |
| GEN-DSC-013 | amendment ne demek biliyor musun? | yonetim | ✅ | ✅ | clarify + 3 amendment |

**Toplam: 8/13 → 10/13** (%76,9; kategori eşiği %80 hâlâ altında) · "yeterli bilgi yok" **tek başına 0** · **G1–G3 13/13** (uydurma yok, kaynaksız şirket bilgisi yok, yetkisiz belge adı yok) · hata/503 0 · sonuç tavan beklentisiyle (10/13) **aynı**.

## 4. Kalan 3 başarısızlığın nedeni (LLM'siz teşhis, ham çıktıdan)

| ID | Neden | Adım 1'in konusu mu | Nerede çözülür |
|---|---|---|---|
| **GEN-DSC-007** | Liste `MAX_AVAILABLE=5` ile dolu; önce **parçadan gelen** 5 belge giriyor (4'ü İzmir: Rüzgar Ölçüm, Ön Fizibilite, Arazi Edinim, ÇED Süreci Durum Yazısı + Ankara Kullanılabilirlik Raporu). Kısaltma sondası (ÇED) Ankara ÇED Olumlu Kararı'nı bulur ama yer kalmaz — Adım 2 raporundaki aynı bulgu (metadata/kavram eşleşmeleri sona ekleniyor). Liste ayrıca iki projeyi karışık veriyor (soru #4 / Ek-F F-3 gruplu liste). | Hayır | Ek-F adımı (a1): proje başlıklı gruplu liste + metadata/kavram eşleşmesine ayrı kota (ADIM2 §4 karar noktası) |
| **GEN-DSC-008** | Budget vs Actual 2026 **enerji_grubu** klasöründe; finans uzmanı yetkili değil → P-2 gereği adı dönmez, «Bütçe» eşleşmedi sayılır. Davranış doğru; veri yerleşimi sorusu. | Hayır (Soru 15 gizliliği çözer, departmanı değil) | Tansu T-3 cevabı (bütçe dosyasının departmanı) → kütüphane |
| **GEN-DSC-011** | Geri ödeme bilgisi yalnızca Excel `Debt` sayfasında; belge hattı cevapsız, Excel hattı "1.000.000" veriyor (para birimi ve tarih yok). `required_sources: Facility Agreement` atıfı imkânsız (B raporu §3.6'da kaydedilen kriter hatası; **değiştirilmedi**). | Hayır | Kütüphane: ilk taksit hem kredi sözleşmesi geri ödeme maddesinde hem ödeme planında (Tansu §1 notu); eval beklentisi o zaman yenilenir |

**Yan gözlem (geçti ama Ek-F için not):** GEN-DSC-001 "var mı?" sorusuna Excel'den rakam döküyor; biçim F-8'e aykırı ("72000000 EUR", "2021-11-15 00:00:00") ve "Evet, mevcuttur" + kaynak kartı yeterdi. GEN-DSC-011'de tutar para birimsiz. İkisi de bir sonraki adımın (Ek-F metin/biçim, F-8 `format_check`) girdisi; bu adımda dokunulmadı.

## 5. Kendi aldığım küçük kararlar
- Gizlilik tek kaynak ledger: Excel spec'inden alan kaldırıldı (küçük refactor; alternatif olan "spec'te de normal yaz" iki kaynağı sürdürürdü).
- Manifest yalnızca `confidentiality` + `generated_at` değişti; `.xlsx` baytları korunarak LibreOffice adımı atlandı (ADR-029'daki "içerik aynı, bayt üretme" yaklaşımı).
- Refresh yalnızca kapı alanlarını eşitler; title/type/tags bilerek dışarıda (B-28b: personel düzenlemeleri seed tarafından ezilmez).
- Kota kontrolü için ayrı çağrı yapılmadı (13 çağrı sınırı); eval'in kendi yeniden denemesi yetti, 503 görülmedi.
- Dal `feat/b-olcum` üzerinden açıldı: ölçüm karşılaştırması Adım 2 koduyla aynı tabanda olsun diye.

## 6. Durum
- `ASSIST_MODE` canlıda **kapalı**, backend yeniden başlatılmış ve doğrulanmış.
- Dal `feat/adim1-soru15` push edildi; `main`'e birleştirme yok (birleştirme sırası: `feat/b-olcum` → bu dal, Naci kararıyla).
- Bir sonraki adım (plan §3.2 adım 2, Ek-F F-3/F-5/F-8 metin ve biçim) **onay bekliyor**.
