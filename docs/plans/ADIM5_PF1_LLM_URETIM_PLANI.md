# Adım 5 — PF-1 LLM Belge Üretim Planı

**Tarih:** 11.10.2026 · **Durum:** plan, **üretim yok** (0 LLM çağrısı yapılmadı) · **Dayanak:** `ADIM5_PF_PARTISI_PLAN.md` §2 (LLM prose satırları), T-11 cevapları işlendikten sonraki ledger durumu (commit `3fa32ae`'ye kadar) · **Dal:** `feat/adim5-veri-kutuphanesi`.

Bu plan `ADIM5_PF_PARTISI_PLAN.md` §2'nin "LLM prose" olarak işaretlediği, bu turda henüz üretilmemiş 3 belgeyi (Yeşilova Facility Agreement, Yeşilova Annex F Raporu, Kızılova imzalı-kullanılmamış Facility Agreement) + Boztepe PF-2 için önerilen belge listesini kapsıyor.

---

## 1. Üretilecek belgeler — tür, aile, hazır olma durumu

| Belge | Tür | Aile (`DocumentSpec.family`) | Üretim | Hazır mı? |
|---|---|---|---|---|
| Yeşilova Facility Agreement (2023-YS) | Facility Agreement | `agreement` | **LLM** | **Eksik var** (bkz. §2.1) |
| Yeşilova Annex F Raporu (2025) | Covenant/Annex Report | `report` (mevcut `covenant_tests` ExtraTable yeniden kullanılabilir) | **LLM** | **Eksik var** (bkz. §2.2) |
| Kızılova İmzalı-Kullanılmamış Facility Agreement (2026-KZ) | Facility Agreement (undrawn) | `agreement` | **LLM** | **Hazır** — tüm facts ledger'da (signed_date dahil, adım 3) |

### Boztepe PF-2 (önerilen liste, T-11.6-10 artık ledger'da)

| Belge | Tür | Üretim |
|---|---|---|
| Facility Agreement (2024-BZ) | Facility Agreement | LLM |
| Ödeme Planı (interest-only dönem) | Repayment Schedule | kodla/Excel |
| Aylık Faiz Bildirimi | Bank Interest Notice | kodla |
| DSRA Hesap Ekstresi | Account Statement | kodla |

Boztepe'nin kredi imza ayı (Mayıs 2024) hâlâ yalnız `lender`'ın notunda — gerçek bir `signed_date` alanı yok (Kızılova'nınki gibi); tam gün Tansu'dan gelmeden Facility Agreement'ın `document_date`'i belirlenemez.

---

## 2. Eksikler — üretimden önce gereken ledger alanları

### 2.1 Yeşilova Facility Agreement
- **İmza tarihi yok.** NACI_CEVAP_2026-10-08.md §3.2 "Sözleşme 03.06.2023" diyor ama bu hiç ledger'a yazılmadı (`OperatingTimeline` bilerek hafif tutuldu, finansman alanı yok). Belgenin kendi `document_date`'i için bu tarih (ya da Tansu'nun onayıyla başka bir tarih) gerekiyor.

### 2.2 Yeşilova Annex F Raporu
- **2025'in toplam faiz tutarı (104.500 USD) hiç modellenmedi** — NACI_CEVAP'ta var ama ayrı bir alan açılmamıştı (peripheral olarak not edilmişti). Rapor bu tutardan bahsedecekse bir alan gerekiyor (`Finance`'e `annex_f_2025_interest_total: Money | None` gibi, şema değişikliği).
- 2025 yıl sonu bakiyesi (1.666.000 USD) **modelleme gerektirmiyor** — `repayment_schedule`'dan hesaplanabilir (2.352.000 − 7×98.000), token olarak `key_facts`'e eklenebilir.

### 2.3 Kızılova İmzalı-Kullanılmamış Facility Agreement
Eksik yok — tüm facts (lender, contract_amount, signed_date, drawdown_condition, commitment_fee, commitment_fee_date) ledger'da.

---

## 3. Token listesi — her belge için (düz rakam yok, Ç-6/G1-G3)

`generate_prose.py`'ye verilen talimat LLM'e **hiçbir gerçek sayı/tarih yazdırmaz** — yalnız `[[token]]` placeholder'ları. Üretim sonrası `validate_documents.py`'nin G1 (DEMO banner), G2 (whitelist dışı isim), G3 (proje karışması) kontrolleri + Ç-6 (kaynakta olmayan bilgi uydurulmaz) ilkesi geçerli.

**Yeşilova Facility Agreement:**
`[[spv_name]]`, `[[counterparty]]`, `[[document_no]]`, `[[document_date]]`, `[[effective_date]]`, `[[total_debt]]`, `[[margin_pct]]`, `[[repayment_profile]]`, `[[dscr_covenant]]`, `[[status_label]]`, `[[project_name]]`.

**Yeşilova Annex F Raporu (2025):**
`[[spv_name]]`, `[[counterparty]]`, `[[document_no]]`, `[[document_date]]`, `[[dscr]]` (covenant_tests[Q4_2025] üzerinden, mevcut ExtraTable kind="covenant_tests" ile), `[[covenant_result]]`, `[[annex_f_reporting_year]]`, `[[annex_f_deadline]]`. **2025 toplam faiz tutarı §2.2'deki alan yazılmadan token olarak eklenemez.**

**Kızılova İmzalı-Kullanılmamış Facility Agreement:**
`[[spv_name]]`, `[[counterparty]]`, `[[document_no]]`, `[[document_date]]` (=signed_date), `[[contract_amount]]`, `[[drawdown_condition]]`, `[[commitment_fee]]`, `[[commitment_fee_date]]`, `[[status_label]]`, `[[project_name]]`.

---

## 4. LLM çağrı sayısı, süre, kota

- `generate_prose.py::generate_one` belge başına **tam 1 LLM çağrısı** yapıyor (doğrulandı — fonksiyon içinde tek bir `client.chat.completions.create`).
- **3 belge → 3 çağrı** (Kızılova hazır; Yeşilova'nın 2 belgesi §2'deki eksikler kapatılınca).
- Kod sabitleri (`generate_prose.py:30-31`): `CALL_SPACING_S = 13` (çağrılar arası bekleme), `RATE_LIMIT_WAIT_S = 65` (hız sınırına çarpılırsa). 3 çağrı = 2 ara boşluk × 13s = **~26s** toplam bekleme + yanıt süreleri (birkaç saniye/çağrı) — toplam **1 dakikanın altında**.
- **Kota:** Gemini free-tier günlük 500 çağrı sınırının (ADIM5_PF_PARTISI_PLAN §5) çok altında — tek oturumda, aynı gün, başka bir LLM işi beklemeden biter.

---

## 5. Üretim sonrası doğrulama kapıları

1. `make validate-ledger` (0 hata).
2. `generate_prose.py` sonrası: **prose dosyasındaki her sayı/tarihin `[[token]]` olduğunun kontrolü** — `grep -nE "[0-9]{2,}" seed_data/generator/prose/<yeni-doc-id>.yaml` çalıştırılıp çıkan her eşleşmenin bir token İÇİNDE (`[[...]]`) olduğu, serbest metinde bağımsız bir rakam olmadığı teyit edilir (Ç-6).
3. `make validate-documents` (full) — G1 (banner), G2 (whitelist), G3 (proje karışması), G4 (key_facts_used metinde var mı), G5/G6 (varsa).
4. **Kasıtlı tuzakların korunduğu kontrolü:** bu 3 belgenin hiçbiri mevcut `conflict_group`/`deliberate_conflict` çiftlerine (Karatepe 14,0/13,6; Yeşilova taksit #11 18.240/18.912) dokunmuyor — ama Annex F raporu Yeşilova'nın 2025 verilerini anlatacağı için, taksit #11'in KENDİSİNİ (14.10.2026, demo_today'den sonra) hiç anmadığından emin olunmalı (2025 raporu, #11 2026'da).
5. `make lint` + `make test` (tek başına).

---

## 6. Riskler

- **Annex F raporu, taksit #11'in (2026, demo_today'den sonra) 2025 raporuna sızması riski** — LLM'e verilecek talimatta "yalnızca 2025 verilerini anlat" net olmalı, aksi halde #4-#7 (2025) ile #11 (2026) karışabilir.
- **Yeşilova Facility Agreement'ın imza tarihi onaylanmadan üretilirse** belge `document_date`'i olmadan geçersiz olur — §2.1'deki alan eksikliği gerçek bir blocker.
- **LLM'in kendi önerdiği rakam/isim üretmesi** (Ç-6 ihlali) — `generate_prose.py`'nin talimatı (zaten `generate_prose.py:47` civarında "never [[rakam yazma]]" örneği var) her 3 belge için de aynı disiplinle çalışmalı; yine de LLM'in serbest metin kısmında bir tarih/sayı icat etme riski sıfır değil — §5 madde 2'nin grep kontrolü bunu yakalar.
- **Boztepe'nin imza günü (Mayıs 2024) olmadan** Facility Agreement üretimi başlatılamaz — Kızılova'nın signed_date eksikliğiyle aynı kalıp.

---

## 7. SORU listesi

1. **Yeşilova Facility Agreement'ın imza tarihi:** NACI_CEVAP'ın "03.06.2023" değeri ledger'a yazılsın mı (ÜRÜN SAHİBİ ONAYLI olarak, bu zaten Tansu'nun kendi verdiği bir değer)? **Önerim: evet** — zaten Tansu'nun kaynağında var, yeni bir onay turu gerekmez, yalnız işlensin.
2. **Yeşilova Annex F'in 2025 toplam faiz alanı:** `Finance`'e yeni bir alan (`annex_f_2025_interest_total` gibi) eklensin mi, yoksa Annex F raporu bu tutardan hiç bahsetmesin mi (yalnız DSCR/yıl sonu bakiyesi ile mi sınırlı kalsın)? **Önerim: alan eklensin** — NACI_CEVAP'ta zaten var (104.500 USD), küçük bir Optional alan, icat değil.
3. **Boztepe'nin kredi imza günü** (Mayıs 2024, tam gün) — T-11'de sorulmadı, ayrı bir soru mu gerekiyor? **Önerim: evet, ayrı küçük bir soru** ("2024-BZ'nin tam imza günü?").
4. **Annex F raporunun hangi ExtraTable kind'ı kullanacağı** — mevcut `covenant_tests` kind'ı Karatepe'nin 4 sütunlu tablosuna göre yazılmıştı (Period/DSCR/Covenant/Result); Yeşilova'nın yıllık (Q4 ile kodlanmış) testleriyle aynı tabloyu mu paylaşsın, yoksa ayrı bir sunum mu? **Önerim: aynı tabloyu paylaşsın** — şema zaten proje-bağımsız, yeni kod gerekmez.

---

**Üretim yapılmadı.** Onay gelirse sıra: (1) SORU 1-2'nin cevapları ledger'a işlenir (0 LLM, bu turun deseniyle aynı), (2) 3 belge `generate_prose.py` ile üretilir (3 LLM çağrısı), (3) §5'teki kapılar sırayla geçilir.
