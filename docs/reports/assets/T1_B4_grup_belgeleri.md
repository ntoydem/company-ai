# T1-B4 — Grup belgeleri adlı proje sorularının aday paketinde mi? (canlı DB, LLM'siz)

Yöntem: `scripts/measure_stage2.py` ile aynı yol (kullanıcı kapısı `allowed_document_ids` → `retrieve()` top-80 → `named_project_codes` → `narrow_allowed`/`narrow_chunks` → `_decide` ile olası F-3 listesi), canlı backend container'ında, yalnız SELECT. «Adlı soru» = `named_project_codes` boş olmayan soru.

| Ölçü | Değer |
|---|---|
| Adlı soru (canlı) | 67 (eval DB'de 66; fark GEN-GEN-003 → `TEST_PRJ`, bkz. B5) |
| Adlı soruda grup belgesi **kullanıcının görebildiği kümede** | 3 / 67 (yalnız `yonetim`; grup belgelerinin departmanı `idari_isler`) |
| … aday parçalarda (top-80, daraltma sonrası) grup belgesi var | 3 |
| … olası F-3 listesinde grup belgesi var | 3 |
| Adlı soruda grup belgesi aday pakette: **hayır** | 64 |

Parça/liste isabetleri: DOC-CO-ADM-001 2, DOC-CO-ADM-006 1, DOC-CO-ADM-003 1, DOC-CO-ADM-010 1 · liste: Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı 2, Grup İlişkili Taraf Hizmet Sözleşmesi 1, Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı 1, Pay Sahipleri Kararı — Kâr Dağıtım Politikası 1

Okuma: daraltma grup belgelerini tasarlandığı gibi geçiriyor (`project ∈ adlı ∪ group`); adlı soruların 64'ünde grup belgesi pakette yok, çünkü soran kullanıcının (enerji/finans/hukuk/finans_mudur) departman kapısı `idari_isler` belgelerini zaten vermiyor — daraltmadan değil, yetkiden. 3 `yonetim` sorusunda grup belgesi pakete giriyor; ANK-COR-001'de beklenen kaynak zaten bir grup belgesi (Pay Sahipleri Kararı).

## Grup belgeleri (10)

| Ref | Başlık |
|---|---|
| DOC-CO-ADM-001 | Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı |
| DOC-CO-ADM-002 | Yönetim Kurulu Kararı — Kızılova RES Geliştirme Bütçesi Onayı |
| DOC-CO-ADM-003 | Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı |
| DOC-CO-ADM-004 | Sigorta Programı Özeti (Şirketler Grubu) |
| DOC-CO-ADM-005 | Yıllık Yönetim Raporu — 2025 |
| DOC-CO-ADM-006 | Grup İlişkili Taraf Hizmet Sözleşmesi |
| DOC-CO-ADM-007 | Kurumsal Yönetim ve Uyum Politikası |
| DOC-CO-ADM-008 | Yönetim Kurulu Kararı — Denetim Komitesi Ataması |
| DOC-CO-ADM-009 | Grup Risk Raporu — 2026 |
| DOC-CO-ADM-010 | Pay Sahipleri Kararı — Kâr Dağıtım Politikası |

## Adlı sorular — tek tek

| Soru | Kullanıcı | Adlı | İzinli | Daraltılmış | Grup belgesi izinli | Parça | Grup parçası | Karar | Liste | Listede grup |
|---|---|---|---|---|---|---|---|---|---|---|
| ANK-DEV-001 | enerji | ANK_RES | 36 | 28 | 0 | 67 | 0  | named | 7 | — |
| ANK-DEV-002 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 7 | — |
| ANK-DEV-003 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 3 | — |
| ANK-DEV-004 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 2 | — |
| ANK-DEV-005 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 3 | — |
| ANK-FIN-001 | finans | ANK_RES | 37 | 18 | 0 | 44 | 0  | named | 6 | — |
| ANK-FIN-002 | finans | ANK_RES | 37 | 18 | 0 | 52 | 0  | named | 7 | — |
| ANK-FIN-003 | finans | ANK_RES | 37 | 18 | 0 | 55 | 0  | named | 6 | — |
| ANK-FIN-004 | finans | ANK_RES | 37 | 18 | 0 | 54 | 0  | named | 7 | — |
| ANK-FIN-005 | finans | ANK_RES | 37 | 18 | 0 | 52 | 0  | named | 7 | — |
| ANK-FIN-006 | finans | ANK_RES | 37 | 18 | 0 | 52 | 0  | named | 7 | — |
| ANK-FIN-007 | finans | ANK_RES | 37 | 18 | 0 | 52 | 0  | named | 7 | — |
| ANK-FIN-008 | finans | ANK_RES | 37 | 18 | 0 | 47 | 0  | named | 7 | — |
| ANK-FIN-009 | finans | ANK_RES | 37 | 18 | 0 | 51 | 0  | named | 7 | — |
| ANK-EPC-001 | enerji | ANK_RES | 36 | 28 | 0 | 70 | 0  | named | 7 | — |
| ANK-EPC-002 | enerji | ANK_RES | 36 | 28 | 0 | 70 | 0  | named | 7 | — |
| ANK-EPC-003 | enerji | ANK_RES | 36 | 28 | 0 | 65 | 0  | named | 7 | — |
| ANK-OPS-001 | enerji | ANK_RES | 36 | 28 | 0 | 70 | 0  | named | 7 | — |
| ANK-FIN-010 | finans | ANK_RES,TEST_PRJ | 37 | 18 | 0 | 51 | 0  | none | 5 | — |
| ANK-FIN-011 | finans | ANK_RES | 37 | 18 | 0 | 53 | 0  | named | 1 | — |
| ANK-FIN-012 | finans | ANK_RES | 37 | 18 | 0 | 49 | 0  | named | 7 | — |
| ANK-FIN-013 | finans | ANK_RES | 37 | 18 | 0 | 51 | 0  | named | 7 | — |
| ANK-EPC-004 | enerji | ANK_RES | 36 | 28 | 0 | 64 | 0  | named | 3 | — |
| IZM-DEV-001 | enerji | IZM_RES | 36 | 8 | 0 | 23 | 0  | named | 7 | — |
| IZM-DEV-002 | enerji | IZM_RES | 36 | 8 | 0 | 25 | 0  | named | 7 | — |
| IZM-DEV-003 | enerji | IZM_RES | 36 | 8 | 0 | 24 | 0  | named | 7 | — |
| IZM-DEV-004 | enerji | IZM_RES | 36 | 8 | 0 | 23 | 0  | named | 7 | — |
| IZM-DEV-005 | enerji | IZM_RES | 36 | 8 | 0 | 20 | 0  | named | 7 | — |
| IZM-DEV-006 | enerji | IZM_RES | 36 | 8 | 0 | 22 | 0  | named | 7 | — |
| IZM-DEV-007 | enerji | IZM_RES | 36 | 8 | 0 | 24 | 0  | named | 7 | — |
| IZM-DEV-008 | enerji | IZM_RES | 36 | 8 | 0 | 23 | 0  | named | 7 | — |
| IZM-DEV-009 | enerji | IZM_RES | 36 | 8 | 0 | 22 | 0  | named | 7 | — |
| GEN-HAL-001 | enerji | IZM_RES | 36 | 8 | 0 | 23 | 0  | named | 7 | — |
| GEN-HAL-002 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 7 | — |
| GEN-HAL-004 | finans | IZM_RES | 37 | 4 | 0 | 14 | 0  | named | 4 | — |
| IZM-ISO-001 | enerji | IZM_RES | 36 | 8 | 0 | 22 | 0  | named | 7 | — |
| IZM-ISO-004 | finans | IZM_RES | 37 | 4 | 0 | 10 | 0  | named | 4 | — |
| ANK-AUT-001 | enerji | ANK_RES | 36 | 28 | 0 | 68 | 0  | named | 0 | — |
| ANK-AUT-002 | enerji | ANK_RES | 36 | 28 | 0 | 70 | 0  | named | 0 | — |
| ANK-AUT-003 | enerji | ANK_RES,TEST_PRJ | 36 | 28 | 0 | 70 | 0  | none | 7 | — |
| ANK-DAT-001 | finans | ANK_RES | 37 | 18 | 0 | 53 | 0  | named | 4 | — |
| ANK-DAT-002 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 7 | — |
| ANK-DAT-003 | yonetim | ANK_RES | 113 | 68 | 10 | 73 | 1 ['DOC-CO-ADM-001'] | named | 7 | ['Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı'] |
| ANK-MIX-002 | enerji | ANK_RES | 36 | 28 | 0 | 69 | 0  | named | 7 | — |
| GEN-GEN-003 | yonetim | TEST_PRJ | 113 | 10 | 10 | 1 | 1 ['DOC-CO-ADM-006'] | named | 1 | ['Grup İlişkili Taraf Hizmet Sözleşmesi'] |
| ANK-MIX-003 | enerji | ANK_RES | 36 | 28 | 0 | 65 | 0  | named | 4 | — |
| ANK-FIN-014 | finans | ANK_RES | 37 | 18 | 0 | 50 | 0  | named | 7 | — |
| ANK-FIN-015 | finans | ANK_RES | 37 | 18 | 0 | 51 | 0  | named | 7 | — |
| ANK-DEV-006 | enerji | ANK_RES | 36 | 28 | 0 | 70 | 0  | named | 5 | — |
| ANK-OPS-002 | enerji | ANK_RES | 36 | 28 | 0 | 67 | 0  | named | 7 | — |
| ANK-EPC-005 | enerji | ANK_RES,TEST_PRJ | 36 | 28 | 0 | 70 | 0  | none | 7 | — |
| ANK-OPS-003 | enerji | ANK_RES | 36 | 28 | 0 | 68 | 0  | named | 7 | — |
| ANK-COR-001 | yonetim | ANK_RES | 113 | 68 | 10 | 80 | 7 ['DOC-CO-ADM-001', 'DOC-CO-ADM-003', 'DOC-CO-ADM-010'] | named | 7 | ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı', 'Pay Sahipleri Kararı — Kâr Dağıtım Politikası', 'Yönetim Kurulu Kararı — Karatepe RES Finansman Onayı'] |
| IZM-DEV-010 | enerji | IZM_RES | 36 | 8 | 0 | 21 | 0  | named | 7 | — |
| IZM-DEV-011 | hukuk | IZM_RES | 7 | 4 | 0 | 13 | 0  | named | 4 | — |
| GEN-CMP-001 | enerji | ANK_RES,IZM_RES | 36 | 36 | 0 | 80 | 0  | none | 7 | — |
| GEN-CMP-002 | enerji | ANK_RES,IZM_RES | 36 | 36 | 0 | 80 | 0  | none | 7 | — |
| GEN-CMP-003 | enerji | ANK_RES,IZM_RES | 36 | 36 | 0 | 80 | 0  | none | 7 | — |
| GEN-TRM-001 | enerji | ANK_RES | 36 | 28 | 0 | 68 | 0  | named | 2 | — |
| GEN-TRM-002 | enerji | IZM_RES | 36 | 8 | 0 | 22 | 0  | named | 7 | — |
| GEN-TRM-004 | enerji | ANK_RES | 36 | 28 | 0 | 70 | 0  | named | 7 | — |
| GEN-TRM-005 | enerji | ANK_RES | 36 | 28 | 0 | 68 | 0  | named | 0 | — |
| ANK-OPS-004 | enerji | ANK_RES | 36 | 28 | 0 | 68 | 0  | named | 2 | — |
| ANK-NEG-001 | finans | ANK_RES | 37 | 18 | 0 | 53 | 0  | named | 7 | — |
| ANK-NEG-002 | finans | ANK_RES | 37 | 18 | 0 | 54 | 0  | named | 7 | — |
| GEN-DSC-001 | finans | ANK_RES | 37 | 18 | 0 | 63 | 0  | named | 1 | — |
| GEN-DSC-001-M | finans_mudur | ANK_RES | 37 | 18 | 0 | 63 | 0  | named | 1 | — |
