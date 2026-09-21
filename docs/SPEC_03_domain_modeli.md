# SPEC 03 — Yenilenebilir enerji / finans domain modeli

Core mimari RES'e bağımlı değildir; V0 demo dataset'i RES senaryosunu modeller. Bu dosyada **rakam yoktur**; tüm rakamlar `seed_data/master/*.yaml` ledger'da, Naci onayıyla.

## 1. Demo projeler
- **Ankara RES** — tamamlanmış, `DEMO_TODAY` (15.09.2026) itibarıyla 3. işletme yılında (COD 2023). Development'tan operation'a tam tarihçe: lisans, finansman, financial close, construction, commissioning, COD, operasyon. Arşiv yalnızca operasyon belgelerinden oluşmaz.
- **İzmir RES** — Development aşaması. ÇED süreci devam ediyor; final ÇED kararı, yapı ruhsatı, üretim lisansı, construction, COD, operasyon **yok** (ledger'da `null`).
Sistem bu ikisini hiçbir şekilde karıştırmaz (izolasyon testleri SPEC_05).

## 2. Proje yaşam döngüsü
Lisans öncesi süreç adımları (bilgi amaçlı, demo belgelerinde kullanılır): Önlisans, Süre Uzatımı Başvurusu, Arazi Edinimi, İmar Kesinleşme, Kat'i Proje Onayı, Bağlantı Anlaşması, Askeri Yasak Yazısı, TEA Yazısı, ÇED, Yapı Ruhsatı, Üretim Lisansı.
Sonra: Lisans → Finansman → Financial Close → EPC / Construction → Commissioning → COD → Operation.

**Karar — validator yalnızca kaba sırayı kontrol eder:**
`Development < Licence < Financing < Financial Close < Construction < Commissioning < COD < Operation`
Lisans öncesi alt adımların mevzuat sırası validator'a girmez (teyit edilmediği için); ledger'da tarihleri tutarlı yazılır, ama kural olarak zorlanmaz.

Örnek kurallar (validator): EPC contract construction bitiminden sonra imzalanamaz; financial close financing belgelerinden önce olamaz; COD commissioning'den önce olamaz; operating year = `DEMO_TODAY` − COD ile uyumlu; İzmir'de lisans sonrası alanlar boş.

## 3. Finans domain (Ankara RES)
Belge tipleri (asgari): Term Sheet, Mandate Letter, Facility Agreement, Common Terms Agreement, ECA Facility Agreement, Intercreditor Agreement, Security Agreement, Share Pledge, Account Pledge, Assignment Agreement, Mortgage, Direct Agreement, Sponsor Support Agreement, Legal Opinion, Conditions Precedent Checklist, Financial Close Documentation, Drawdown Notice, Repayment Schedule, Covenant Report, Financial Model, Debt Schedule.
Tutarlı olması gereken değerler: total debt, ECA debt, local debt, interest rate, margin, tenor, grace period, repayment profile, DSCR covenant, drawdowns, outstanding debt, capex, debt/equity.
AI'nın cevaplayabilmesi gereken sorular: financial close tarihi, ilk drawdown, toplam finansman, yerli banka / ECA finansmanı, faiz, tenor, grace, repayment profile, güncel outstanding debt, minimum DSCR covenant, son covenant test sonucu, amendment'lar, güncel Facility Agreement.

## 4. Para birimleri (karar)
Kredi EUR; tarife/gelir USD (YEKDEM); OPEX/bütçe/fatura TL. Ledger'da her tutarın yanında birim. Excel testleri ledger'daki sabit `fx_rates` ile; gerçek kur yok.

## 5. EPC / Construction (Ankara RES)
EPC Contract, Turbine Supply Agreement, Civil Works, Electrical Works, Equipment Supply, Transformer Procurement, Construction Schedule, Progress Reports, Payment Certificates, Change Orders, Claims, Technical Reports, Site Meeting Minutes, HSE Reports, Commissioning Documents, Acceptance Tests, Provisional/Final Acceptance, COD Documentation.

## 6. Operation (Ankara RES)
Aylık/yıllık üretim, SCADA özetleri, availability, capacity factor, rüzgar verisi, preventive/corrective maintenance, spare parts, türbin arızaları, warranty claims, O&M invoices, grid correspondence, insurance, annual technical reports, budgets, KPI reports. Dataset şişirilmez; önemli lifecycle olayları kapsanır.

## 7. Hukuk
ÇED süreçleri, arazi/edinim, sözleşme ihtilafları, supplier disputes, idari başvurular, legal opinions, claims, dava takip tabloları. Dramatik dava hikâyeleri yok.

## 8. Mali İşler / İdari İşler
Bütçe, cash flow, invoice, payment, procurement, supplier, accounting, tax, audit, insurance, board/shareholder resolutions, SPV corporate documents, management reports.

## 9. Kurumsal yapı (ledger'da tanımlanır)
Holding/ana şirket, her proje için SPV, hissedarlar ve paylar, banka(lar), ECA, EPC yüklenicisi, türbin tedarikçisi, teknik danışman, sigorta. Tüm isimler kurgusal ve jenerik (ABC Enerji A.Ş., PQR Bank, …). Gerçek kişi, imza, belge no, QR/barkod, kimlik verisi yok. Gerçek kamu kurumu adları (EPDK, TEİAŞ, ÇŞB vb.) süreç bağlamında kullanılabilir; kurum kimliği taklit edilmez.

## 10. Değişiklik örnekleri (controlled changes — değerler ledger'da)
Kapasite artışı (Licence Amendment), DSCR covenant gevşetme + tenor uzatma (Facility Amendment), COD ertelemesi (Change Order / Amendment). Değişiklik rastgele değildir; sonraki tüm belgeler yeni değeri kullanır.
