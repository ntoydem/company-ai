# T1-B3 — Belge etiketleri (canlı DB, 113 belge, LLM'siz)

Kaynak: `documents ⋈ projects` (yalnız okuma) + `document_pages.page_number=1` ilk 900 karakter. Anahtar kelime: Karatepe/Kızılova/Yeşilova/Boztepe/Akyar/Demirci/Güneşalan (ı/i ve ş/s ASCII varyantlarıyla). 7 Excel belgesinin sayfa metni yok (dosya adı + başlık + metadata ile bakıldı).

## Özet

| Kapsam | n | ✓ tutarlı | ⚠ şüpheli | ✗ tutarsız | ? ad yok |
|---|---|---|---|---|---|
| project | 103 | 103 | 0 | 0 | 0 |
| group | 10 | 7 | 3 | 0 | 0 |

Proje belgelerinde atanan projenin adı nerede bulundu:

| Yer | n |
|---|---|
| sayfa1 | 65 |
| başlık | 31 |
| yalnız metadata (karşı taraf/extra) | 4 |
| dosya | 3 |

«Yalnız metadata» 4 belge = Karatepe'nin 4 Excel çalışma kitabı (Financial Model 2026, Covenant Report (workbook), Budget vs Actual 2026, Monthly Production 2026): sayfa metni yok, başlık/dosya adı proje adı taşımıyor; proje adı yalnız `counterparty`/`extra_fields.parties` alanında (Karatepe RES Enerji Üretim A.Ş.). Tutarsızlık değil, metin kanıtı yok.

## Grup belgeleri (10)

| Ref | Başlık | Tür | Departman | Bulunan proje adları | Karar |
|---|---|---|---|---|---|
| DOC-CO-ADM-001 | Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı | Board Resolution | idari_isler | {'ANK_RES': ['başlık', 'extra', 'karşı taraf', 'sayfa1']} | ⚠ grup işaretli, metin tek projeyi anıyor: ANK_RES |
| DOC-CO-ADM-002 | Yönetim Kurulu Kararı — Kızılova RES Geliştirme Bütçesi Onayı | Board Resolution | idari_isler | {'IZM_RES': ['başlık', 'extra', 'karşı taraf', 'sayfa1']} | ⚠ grup işaretli, metin tek projeyi anıyor: IZM_RES |
| DOC-CO-ADM-003 | Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı | Shareholder Resolution | idari_isler | {'ANK_RES': ['extra']} | ⚠ grup işaretli, metin tek projeyi anıyor: ANK_RES |
| DOC-CO-ADM-004 | Sigorta Programı Özeti (Şirketler Grubu) | Insurance Summary | idari_isler | — | ✓ grup; proje adı yok |
| DOC-CO-ADM-005 | Yıllık Yönetim Raporu — 2025 | Management Report | idari_isler | — | ✓ grup; proje adı yok |
| DOC-CO-ADM-006 | Grup İlişkili Taraf Hizmet Sözleşmesi | Service Agreement | idari_isler | {'ANK_RES': ['extra', 'karşı taraf', 'sayfa1'], 'IZM_RES': ['extra', 'sayfa1']} | ✓ grup; birden çok proje anılıyor ['ANK_RES', 'IZM_RES'] |
| DOC-CO-ADM-007 | Kurumsal Yönetim ve Uyum Politikası | Governance Policy | idari_isler | — | ✓ grup; proje adı yok |
| DOC-CO-ADM-008 | Yönetim Kurulu Kararı — Denetim Komitesi Ataması | Board Resolution | idari_isler | — | ✓ grup; proje adı yok |
| DOC-CO-ADM-009 | Grup Risk Raporu — 2026 | Risk Report | idari_isler | — | ✓ grup; proje adı yok |
| DOC-CO-ADM-010 | Pay Sahipleri Kararı — Kâr Dağıtım Politikası | Shareholder Resolution | idari_isler | — | ✓ grup; proje adı yok |

## Proje belgeleri (103)

| Ref | Başlık | Dosya | Tür | Proje | Departman | Durum | Bulunan | Karar |
|---|---|---|---|---|---|---|---|---|
| DOC-AKY-LEG-001 | Kamulaştırma Ön Değerlendirme Notu | — | Assessment Memo | AKY_GES | hukuk | active | {'AKY_GES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-ADM-001 | Yıllık İşletme Bütçesi Onayı — 2026 | — | Budget Approval | ANK_RES | mali_isler | executed | {'ANK_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-ADM-002 | Sigorta Programı Yıllık Gözden Geçirme Notu | — | Insurance Review Memo | ANK_RES | idari_isler | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-DEV-001 | Karatepe RES Üretim Lisansı | — | Üretim Lisansı | ANK_RES | enerji_grubu | amended | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-DEV-002 | Licence Amendment 01 (Kapasite Tadili) | — | Licence Amendment | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-DEV-003 | Karatepe RES Bağlantı Anlaşması | — | Bağlantı Anlaşması | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-DEV-004 | Karatepe RES Yapı Ruhsatı | — | Yapı Ruhsatı | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-DEV-005 | Karatepe RES ÇED Olumlu Kararı | — | ÇED Olumlu Kararı | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-DEV-006 | Karatepe RES Saha Kullanım Hakkı Sözleşmesi | — | Saha Kullanım Hakkı Sözleşmesi | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-001 | EPC Contract | — | EPC Contract | ANK_RES | enerji_grubu | amended | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-002 | Provisional Acceptance & COD Certificate | — | COD Documentation | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-003 | EPC Change Order 01 (COD Deferral) | — | Change Order | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-004 | Karatepe RES Mechanical Completion Certificate | — | Completion Certificate | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-005 | Karatepe RES Independent Engineer's Completion Report | — | Completion Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-006 | Karatepe RES Punch List Closure Confirmation | — | Punch List Closure | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-007 | Karatepe RES Construction All Risks Insurance Policy Summary | — | Insurance Policy | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-008 | Karatepe RES Performance Test Results Report | — | Performance Test Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-009 | Karatepe RES Warranty & Defects Liability Certificate | — | Warranty Certificate | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-EPC-010 | Karatepe RES Şebeke Bağlantı Tamamlama Belgesi | — | Grid Connection Certificate | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-001 | Facility Agreement — Draft | — | Facility Agreement | ANK_RES | finans | draft | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-002 | Facility Agreement — V01 | — | Facility Agreement | ANK_RES | finans | superseded | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-003 | Facility Agreement — V02 | — | Facility Agreement | ANK_RES | finans | superseded | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-004 | Facility Agreement | — | Facility Agreement | ANK_RES | finans | superseded | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-005 | Facility Agreement Amendment 01 | — | Facility Agreement | ANK_RES | finans | superseded | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-006 | Facility Agreement Amendment 02 | — | Facility Agreement | ANK_RES | finans | executed | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-007 | Covenant Compliance Report Q2 2026 | — | Covenant Report | ANK_RES | finans | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-008 | Financial Model 2026 | Financial_Model_2026.xlsx | Financial Model | ANK_RES | finans | active | {'ANK_RES': ['extra', 'karşı taraf']} | ✓  |
| DOC-ANK-FIN-009 | Covenant Report (workbook) | Covenant_Report.xlsx | Covenant Report | ANK_RES | finans | active | {'ANK_RES': ['extra', 'karşı taraf']} | ✓  |
| DOC-ANK-FIN-010 | Karatepe RES Common Terms Agreement | — | Common Terms Agreement | ANK_RES | finans | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-011 | Karatepe RES Security Agreement (Share Pledge) | — | Share Pledge | ANK_RES | finans | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-012 | Karatepe RES Account Pledge Agreement | — | Account Pledge | ANK_RES | finans | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-013 | Karatepe RES Insurance Assignment Agreement | — | Assignment Agreement | ANK_RES | finans | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-014 | Karatepe RES Drawdown Notice — Tranche 1 | — | Drawdown Notice | ANK_RES | finans | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-015 | Karatepe RES Waiver Letter — Q4 2024 Covenant Test | — | Waiver Letter | ANK_RES | finans | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-016 | Karatepe RES Covenant Compliance Report — Q4 2024 | — | Covenant Report | ANK_RES | finans | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-017 | Garanti BBVA Faiz Belirleme Bildirimi | — | Bank Interest Notice | ANK_RES | finans | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-FIN-018 | Teminat Mektubu Yenileme Bildirimi — Orman İzni | — | Guarantee Renewal Notice | ANK_RES | finans | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-001 | Hukuki Görüş — Finansman Ön Koşulları | — | Legal Opinion | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-002 | Arazi Kullanım Hakkı Hukuki İnceleme Notu | — | Legal Review Memo | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-003 | Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri | — | Legal Review Memo | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-004 | Kamulaştırma ve İrtifak Bedeli Tespiti Davası — Dava Dilekçesi | — | Lawsuit Petition | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-005 | Kamulaştırma ve İrtifak Bedeli Tespiti Davası — İdare Savunması | — | Defense Brief | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-006 | Kamulaştırma ve İrtifak Bedeli Tespiti Davası — Bilirkişi Raporu | — | Expert Report | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-007 | Kamulaştırma ve İrtifak Bedeli Tespiti Davası — Duruşma Tutanağı | — | Hearing Record | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-008 | Mahkeme Kalemi E-postası — Dava Süreci Güncellemesi | — | Court Clerk Email | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-009 | Karşı Taraf Vekili E-postası — Dava Dosyası Güncellemesi | — | Opposing Counsel Email | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-LEG-010 | Elektrik Direği İhlali Davası — Dava Dilekçesi | — | Lawsuit Petition | ANK_RES | hukuk | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-001 | Aylık Üretim Raporu — Ağustos 2026 | — | Production Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-002 | Budget vs Actual 2026 | Budget_vs_Actual_2026.xlsx | Budget vs Actual | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'karşı taraf']} | ✓  |
| DOC-ANK-OPS-003 | Monthly Production 2026 | Monthly_Production_2026.xlsx | Monthly Production | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'karşı taraf']} | ✓  |
| DOC-ANK-OPS-004 | Karatepe RES O&M Agreement | — | O&M Agreement | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-005 | Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası) | — | Maintenance Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-006 | Aylık Üretim Raporu — Aralık 2023 | — | Production Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-007 | Aylık Üretim Raporu — Haziran 2025 | — | Production Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-008 | Yıllık Performans Değerlendirme Notu — 2024-2025 Dönemi | — | Performance Review | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-009 | Sigorta Yenileme Bildirimi — İşletme Dönemi | — | Insurance Notice | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-010 | Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu | — | Availability Report | ANK_RES | enerji_grubu | active | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-011 | Karatepe RES Yedek Parça Tedarik Sözleşmesi | — | Spare Parts Agreement | ANK_RES | enerji_grubu | executed | {'ANK_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-ANK-OPS-012 | Yıllık Bakım Planı — 2026 | — | Maintenance Plan | ANK_RES | enerji_grubu | active | {'ANK_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-BOZ-FIN-001 | Boztepe RES Facility Agreement (2024-BZ) | — | Facility Agreement | BOZ_RES | finans | executed | {'BOZ_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-BOZ-FIN-002 | Aylık Faiz Bildirimi — Ekim 2026 Taksidi | — | Bank Interest Notice | BOZ_RES | finans | active | {'BOZ_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-BOZ-FIN-003 | DSRA Hesap Ekstresi — Ekim 2026 | — | DSRA Account Statement | BOZ_RES | finans | active | {'BOZ_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-BOZ-FIN-004 | Anapara Geri Ödeme Planı (84 Taksit) | Boztepe_Repayment_Schedule_84_Instalments.xlsx | Repayment Schedule | BOZ_RES | finans | active | {'BOZ_RES': ['dosya', 'extra', 'karşı taraf']} | ✓  |
| DOC-BOZ-FIN-005 | Boztepe RES — Covenant Compliance Report Q3 2026 | — | Covenant Report | BOZ_RES | finans | active | {'BOZ_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-BOZ-LEG-001 | İmar Planı Değişikliği İptali Davası — Dava Dilekçesi | — | Lawsuit Petition | BOZ_RES | hukuk | active | {'BOZ_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-BOZ-LEG-002 | İmar Planı Değişikliği İptali Davası — Belediye Savunması | — | Defense Brief | BOZ_RES | hukuk | active | {'BOZ_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-BOZ-LEG-003 | İmar Planı Değişikliği İptali Davası — Yürütmeyi Durdurma Talebinin Reddi | — | Interim Decision | BOZ_RES | hukuk | active | {'BOZ_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-BOZ-LEG-004 | İmar Planı Değişikliği İptali Davası — Bilirkişi Keşif Tutanağı | — | Site Visit Record | BOZ_RES | hukuk | active | {'BOZ_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-DMR-LEG-001 | TEA Olumsuz Görüşüne İtiraz Dilekçesi | — | Regulatory Objection Letter | DMR_RES | hukuk | active | {'DMR_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-ADM-001 | Kızılova RES Geliştirme Bütçesi Onayı | — | Budget Approval | IZM_RES | mali_isler | executed | {'IZM_RES': ['başlık', 'extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-IZM-ADM-002 | Saha Güvenliği ve İdari Düzenlemeler Notu | — | Site Security Memo | IZM_RES | idari_isler | active | {'IZM_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-IZM-ADM-003 | Proje Maliyet Takip Notu — Geliştirme Aşaması | — | Cost Tracking Memo | IZM_RES | mali_isler | active | {'IZM_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-001 | Kızılova RES Önlisans Belgesi | — | Önlisans | IZM_RES | enerji_grubu | active | {'IZM_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-002 | Arazi Edinim Durum Raporu | — | Arazi Edinim Raporu | IZM_RES | enerji_grubu | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-003 | ÇED Süreci Durum Yazısı | — | ÇED Durum Yazısı | IZM_RES | enerji_grubu | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-004 | Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu | — | Teknik Rapor | IZM_RES | enerji_grubu | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-005 | Kızılova RES Bağlantı Görüşü Başvurusu | — | Bağlantı Görüşü Başvurusu | IZM_RES | enerji_grubu | active | {'IZM_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-006 | Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı | — | Toplantı Tutanağı | IZM_RES | enerji_grubu | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-007 | Rüzgar Ölçüm Kampanyası Raporu | — | Teknik Rapor | IZM_RES | enerji_grubu | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-DEV-008 | Askeri Yasak Bölgeler Ön Görüş Talebi | — | Ön Görüş Talebi | IZM_RES | enerji_grubu | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-FIN-001 | Taahhüt Komisyonu Bildirimi | — | Commitment Fee Notice | IZM_RES | finans | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-FIN-002 | EPC Avans Teminat Mektubu | — | Advance Guarantee Letter | IZM_RES | finans | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-FIN-003 | Avans Faturası — ABC2026000000184 | — | Invoice | IZM_RES | finans | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-FIN-004 | Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ) | — | Facility Agreement | IZM_RES | finans | executed | {'IZM_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-IZM-LEG-001 | Arazi Mülkiyeti Hukuki İnceleme Notu | — | Legal Review Memo | IZM_RES | hukuk | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-LEG-002 | Kira/İrtifak Hakkı Sözleşmesi Taslağı | — | Lease Agreement Draft | IZM_RES | hukuk | draft | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-LEG-003 | Şirket Yapısı Hukuki Görüşü — Kızılova SPV | — | Legal Opinion | IZM_RES | hukuk | active | {'IZM_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-IZM-LEG-004 | Önlisans Süre Uzatımı Hukuki Değerlendirmesi | — | Legal Review Memo | IZM_RES | hukuk | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-LEG-005 | Yüklenici İhtilafı — Noter İhtarnamesi | — | Notary Notice | IZM_RES | hukuk | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-IZM-LEG-006 | Mera Tahsis Değişikliği Talebi | — | Request Letter | IZM_RES | hukuk | active | {'IZM_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-001 | Taksit #11 Banka Faiz Bildirimi | — | Bank Interest Notice | YSV_RES | finans | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-002 | Annex F Talep E-postası | — | Reporting Request | YSV_RES | finans | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-003 | DSRA Hesap Ekstresi | — | Account Statement | YSV_RES | finans | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-004 | Borç Servis Hesabı Ekstresi | — | Account Statement | YSV_RES | finans | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-005 | Sigorta Zeyilnamesi — Ara Dönem | — | Insurance Notice | YSV_RES | finans | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-006 | Bankaya Giden İşletme Bütçesi | — | Budget | YSV_RES | finans | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-007 | Ödeme Planı — Güncel | Yesilova_Repayment_Schedule_2026-09.xlsx | Repayment Schedule | YSV_RES | finans | active | {'YSV_RES': ['dosya', 'extra', 'karşı taraf']} | ✓  |
| DOC-YSV-FIN-008 | Ödeme Planı — Mart 2026 | Yesilova_Repayment_Schedule_2026-03.xlsx | Repayment Schedule | YSV_RES | finans | superseded | {'YSV_RES': ['dosya', 'extra', 'karşı taraf']} | ✓  |
| DOC-YSV-FIN-009 | Yeşilova RES Facility Agreement (2023-YS) | — | Facility Agreement | YSV_RES | finans | executed | {'YSV_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-YSV-FIN-010 | Yeşilova RES Annex F Raporu (2025) | — | Covenant Report | YSV_RES | finans | draft | {'YSV_RES': ['başlık', 'extra', 'sayfa1']} | ✓  |
| DOC-YSV-LEG-001 | Arazi Tahsisi Tazminat Davası — Hukuk Danışmanı Yazışması | — | Legal Counsel Correspondence | YSV_RES | hukuk | active | {'YSV_RES': ['extra', 'karşı taraf', 'sayfa1']} | ✓  |
| DOC-YSV-LEG-002 | Arazi Tahsisi Tazminat Davası — Dava Dilekçesi | — | Lawsuit Petition | YSV_RES | hukuk | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
| DOC-YSV-LEG-003 | Sınır İhlali Davası — Dava Dilekçesi | — | Lawsuit Petition | YSV_RES | hukuk | active | {'YSV_RES': ['extra', 'sayfa1']} | ✓  |
