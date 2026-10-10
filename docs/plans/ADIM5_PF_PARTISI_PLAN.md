# Adım 5 — Proje Finans (PF) Partisi Planı

**Tarih:** 10.10.2026 · **Durum:** plan, kod yok, canlı Gemini çağrısı yok, canlı DB yok · **Dayanak:** `NACI_CEVAP_2026-10-08.md` §3.2/§3.3/§3.7 (AI-BalBal PR #13), `docs/SORULAR_NACIDEN_2-2026-10-09.md` T-3/T-8 (PR #17), `docs/plans/ADIM5_PLAN.md` §1.2/§1.3, Adım 5 Aşama A-C (`ADIM5_ASAMA_A/C_REPORT.md`) · **Dal:** `feat/adim5-veri-kutuphanesi` (main'e birleştirme yok, uygulama ayrı onay bekler) · **Sıra:** Tansu'nun istediği parti sırasının (PF → Hukuk → Enerji → Mali → İdari → İK) **ilki**.

## 1. Kapsam — iki alt grup

**PF-1 (verisi tam — üretilebilir): Karatepe + Yeşilova + Kızılova.**
**PF-2 (bekliyor): Boztepe.** Tansu toplam kredi tutarı, oran, tenor, DSCR, DSRA'yı **vermedi** (yalnız aylık faiz tutarı + iki tarih, bkz. `ADIM5_ASAMA_C_REPORT.md` §C3). Bu alanlar **uydurulmaz** — Boztepe'nin PF belgeleri Tansu'dan ek veri gelene kadar **üretilmez**. Boztepe'nin mevcut ledger kaydı (`boztepe_res.yaml`) zaten pending durumda; bu partide değişmez.

## 2. Belge listesi (SPV bazında)

### 2.1 Karatepe RES (mevcut 16 belge + yeni 2)

Mevcut (`DOC-ANK-FIN-001`…`016`, Adım 5 Aşama A'da yeniden hizalandı): draft/V01/V02/EXECUTED zinciri (4, kodla), AMD01/AMD02 (2, LLM prose — `hand_edited`, yeniden üretilmez), Common Terms Agreement (1), Share Pledge/Account Pledge/Insurance Assignment (3), Drawdown Notice (1), Waiver Letter Q4 2024 (1), Covenant Report Q4-2024 + Q2-2026 (2), Financial Model + Covenant Report workbook (2, kodla/Excel).

**Yeni (NACI_CEVAP §3.7'de adı geçen ama henüz belge olarak üretilmemiş):**

| Belge | Tür | Dil | Gizlilik | key_facts kaynağı | Üretim |
|---|---|---|---|---|---|
| `GarantiBBVA_Faiz_Belirleme_Bildirimi` | Bank Interest Notice | TR | normal | `project.finance.interest.margin_pct.current.value` | kodla (0 LLM) |
| Teminat Mektubu Yenileme Bildirimi (orman izni, Ocak 2027) | Guarantee Renewal Notice | TR | normal | yeni alan gerekir (bkz. §4) | kodla |

### 2.2 Yeşilova RES (yeni, ~10-12 belge)

| Belge | Tür | Dil | Gizlilik | key_facts kaynağı | Üretim |
|---|---|---|---|---|---|
| Facility Agreement (2023-YS) | Facility Agreement | EN | normal | `yesilova_res.project.finance.{lender,interest,total_debt}` | LLM prose (yeni şablon) |
| Ödeme Planı — **güncel** (01.09.2026) | Repayment Schedule | EN | normal | `...repayment_schedule` | kodla/Excel |
| Ödeme Planı — **eski** (Mart 2026) | Repayment Schedule | EN | normal | aynı liste, taksit #11 öncesi durum | kodla — **sürüm farkı tuzağı** |
| Taksit #11 Banka Faiz Bildirimi | Bank Interest Notice | TR | normal | `...bank_interest_notices[0]` | kodla — **gerçek çelişki tuzağı** |
| Annex F Talep E-postası (14.09.2026) | Reporting Request | EN | normal | — (tarih/son gün sabit metin) | kodla |
| Annex F Raporu (2025) | Covenant/Annex Report | EN | normal | `...repayment_schedule` (2025 satırları) | LLM prose |
| DSRA Hesap Ekstresi | Account Statement | TR | normal | `...dsra_balance` | kodla |
| Borç Servis Hesabı Ekstresi | Account Statement | TR | normal | `...debt_service_account_balance` | kodla |
| Sigorta Zeyilnamesi (ara dönem) | Insurance Endorsement | TR | normal | `...insurance_expiry` (dolaylı) | kodla |
| Bankaya Giden İşletme Bütçesi | Budget (bank-facing) | TR | normal | — (O&M bakım bütçesinden **ayrı**, T-3) | kodla |
| **Teminat mektubu belgesi** | — | — | — | — | **Üretilmez — kasıtlı eksik belge tuzağı (T-5 madde 4)** |

### 2.3 Kızılova RES (yeni, ~5-6 belge)

| Belge | Tür | Dil | Gizlilik | key_facts kaynağı | Üretim |
|---|---|---|---|---|---|
| İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ) | Facility Agreement (undrawn) | EN | normal | `izmir_res.project.signed_undrawn_facility` | LLM prose |
| Taahhüt Komisyonu Bildirimi (05.01.2027) | Commitment Fee Notice | TR | normal | `...commitment_fee` | kodla |
| EPC Avans Teminat Mektubu (DEF Bank/Akbank, 2.000.000 USD) | Advance Guarantee Letter | EN | normal | `...signed_unstarted_epc.advance_guarantee*` | kodla |
| Avans Faturası (ABC2026000000184) | Invoice | TR | normal | `...signed_unstarted_epc.advance_amount` (not) | kodla |

**Üretilmeyecekler (İ-1, zaten Aşama C.4'te not edildi):** kullandırım talebi, inşaat ilerleme raporu, CAR/EAR sigortası. Hakediş 1 (SÖ-26-014) tutarları "canvas'taki gibi" deniyor ama bu depoya aktarılmadı — **modellenmeden** bu belge de üretilemez (ya tutarlar gelir ya da PF-2 gibi bekler — SORU 3).

### 2.4 §1.2 matrisine katkı

PF, matrisin **`Covenant Report`** satırını tamamlıyor (Karatepe 3 + Yeşilova 2 = 5, ≥2 proje ✓) ve **`Insurance Notice`** satırına katkı veriyor (Karatepe + Yeşilova — Boztepe PF-2'de bekliyor, bu satırın "her projede ≥2" şartı Boztepe gelmeden tam sağlanmıyor, not edilsin).

## 3. Tuzaklar — tür etiketiyle

| Tuzak | Tür | Nerede | Ledger'da nasıl tutulur |
|---|---|---|---|
| Karatepe 14,0M (sözleşme) vs 13,6M (kullandırılan) | **genuine_conflict** | `DOC-ANK-FIN-004` vs `DOC-ANK-FIN-007`/ödeme planı (Aşama C.5'te belge-arası ayrıldı) | `Finance.contract_amount`/`total_debt`, `conflict_group: "karatepe-kredi-tutari"` |
| Yeşilova taksit #11 faizi: 18.240 (plan) vs 18.912 (banka) | **genuine_conflict** | Ödeme planı vs Banka Faiz Bildirimi | `Instalment.interest`/`BankInterestNotice.amount`, `conflict_group: "yesilova-taksit11-faiz"` |
| Yeşilova ödeme planının iki sürümü (01.09.2026 güncel, Mart 2026 eski) | **version_difference** (ÇELİŞKİ DEĞİL) | İki belge, aynı `repayment_schedule`'ın farklı anlık görüntüleri | **Yeni alan gerekir** — bugünkü `conflict_group` mekanizması "çelişki" ile "sürüm farkı"nı ayırmıyor (bkz. `EKF_V2_PLAN.md` (d)); öneri: `Document.version`/`supersedes` zinciri zaten bunu taşıyor — iki ödeme planı belgesi `supersedes` ile zincirlenir, `conflict_group` **kullanılmaz** (zaten çelişki değil). |
| Enercon mükerrer fatura (ENR2026001121, asıl 29.09 / kopya 30.09) | **duplicate** | Mali İşler/Muhasebe partisinin kapsamında (PF değil) — burada yalnız not | PF kapsamı dışı |
| Yeşilova'nın teminat mektubu belgesi yok | **missing_document** | — | Üretilmez; eval/belge envanterinde "beklenen ama yok" olarak **işaretlenmez bile** (gerçek demo'da da böyle: bazı belgeler gerçekten yoktur) |

**Genel kural:** `genuine_conflict` → `conflict_group`/`deliberate_conflict` (mevcut mekanizma, Adım 5 Aşama A). `version_difference` → mevcut `supersedes`/`version` zinciri (TEMPORAL TRUTH kuralı zaten bunu ayırıyor, yeni alan gerekmez). `duplicate`/`missing_document` → PF'nin kendi kapsamında yalnız bir örnek var (teminat mektubu eksikliği), yeni bir ledger mekanizması gerekmez, yalnızca belgenin **üretilmemesi** yeterli.

## 4. Yeni ledger alanı ihtiyacı

Karatepe'nin "teminat mektubu yenileme" (orman izni, Ocak 2027) için `Finance`'e yeni bir `guarantee_letters: list[GuaranteeLetter]` alanı gerekir (şu an yok). Küçük, additive — Karatepe'nin mevcut davranışını değiştirmez.

## 5. Üretim — kodla vs LLM prose, kota

| Tür | Sayı (tahmini) | LLM çağrısı |
|---|---|---|
| Kodla/şablonla (banka bildirimleri, ekstreler, komisyon bildirimi, ödeme planları) | ~14 | 0 |
| LLM prose (facility agreement'lar, Annex F raporu) | ~4 (Yeşilova FA, Kızılova FA, Annex F raporu, +1 yedek) | ~4 |

**Toplam PF-1: ~18-20 belge, ~4 LLM çağrısı** — günlük kotanın (500) çok altında, **tek kota günü gerekmez**, PF partisi tek oturumda bitebilir (Gemini 5/dk hız sınırına göre ~2 dakika sürer).

## 6. Doğrulama kapıları

1. `make validate-ledger` — yeni `guarantee_letters` alanı dahil, 0 hata.
2. `make validate-documents` — 0 hata (PF'nin yeni belgeleri dahil, prose token'ları çözülür).
3. `check_conflict_groups` — Yeşilova'nın taksit #11 çifti doğru etiketli, "version_difference" (ödeme planı sürümleri) **conflict_group kullanmadığı** için bu kuralın dışında kalır (ayrı bir kontrol gerekmez).
4. Belge türü × proje matrisi (§1.2) — `Covenant Report`/`Insurance Notice` satırları güncellenir.
5. **PF + Hukuk hazır olunca Tansu'nun ön testi başlayabilir** (T-8: "A, şartlı" — bulunan hatalar beklenmeden düzeltilir; resmi tur 1 sonucu tüm departmanlar gelince).

## 7. Riskler

- Yeşilova'nın iki ödeme planı sürümünü **çelişki olarak değil sürüm farkı olarak** doğru modellemek — yanlış etiketlenirse (conflict_group ile işaretlenirse) Tansu'nun T-5 ayrımıyla çelişir, kör testte K3 düşer.
- Kızılova'nın EPC avans faturası/teminat mektubu PF ile Enerji/EPC partisi arasında **departman sınırı belirsiz** — bu plan PF'ye yalnız banka enstrümanlarını (teminat mektubu, komisyon bildirimi) verdi, EPC sözleşmesinin kendisini Enerji/EPC partisine bıraktı; partiler arası tutarsızlık riski (aynı belgenin iki kez üretilmesi) var, Enerji partisi planlanırken bu sınır teyit edilmeli.
- Boztepe'nin verisi gelmeden PF-1 "bitti" sayılırsa, §1.2 matrisinin `Insurance Notice` satırı eksik kalır — bilinçli, flaglandı.

## 8. SORU

1. **Hakediş 1 (Kızılova, SÖ-26-014) tutarları:** "canvas'taki gibi" deniyor ama bu depoya aktarılmadı — Tansu'dan rakamlar istenip bu partiye mi eklenir, yoksa Enerji/EPC partisine mi bırakılır (hakediş inşaat/mühendislik işi, EPC'nin kapsamı)? **Önerim:** Enerji/EPC partisine bırakılsın — hakediş, PF'nin bank/kredi odaklı kapsamından çok EPC'nin ilerleme/ödeme kapsamına giriyor.
2. **Kızılova'nın EPC avans faturası/teminat mektubu PF'de mi, Enerji/EPC'de mi?** Bu plan PF'ye verdi (banka enstrümanı mantığıyla). Onaylanıyor mu? **Önerim:** evet, PF'de kalsın — banka tarafından verilen her enstrüman (teminat mektubu, komisyon bildirimi) PF'nin kapsamı, EPC sözleşmesinin kendisi ve hakediş Enerji'nin.
3. **Boztepe'nin verisi gelmeden PF partisi "tamamlandı" ilan edilsin mi** (PF-1 bitince Hukuk'a geçilsin, Boztepe PF-2 olarak ayrı, geciken bir ek mi olsun)? **Önerim:** evet — Tansu'nun T-8 cevabı zaten "PF + Hukuk hazır olunca ön test" diyor, Boztepe'nin eksikliği bu ön testi engellemez (Boztepe'nin kendi verisi geldiğinde ayrı, küçük bir ekleme olur).

---

Hiçbir belge bu planla üretilmedi — onay bekliyor.
