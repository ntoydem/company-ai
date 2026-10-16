# Huni tablosu — M1 koşusu (2026-10-16, canlı kod A2L3 `64c8966`, puanlayıcı v2.0) kalan kayıplar

Her kayıp tek aşamaya atanır. Aşama 1–2 kanıtı LLM'siz: M1 audit `chunks_retrieved` (hedef sayfa top-80'de mi?) + getirilen belgelerin proje dağılımı; `assist.kind`/`axis` M1 cevabından. Tablo `scripts/build_huni.py` ile üretildi (betik değiştirilmedi); betiğin S3'e göre yazılmış `OVERRIDES` sözlüğü ve otomatik kuralı bu koşuda **dört satırda** yanlış aşama verdi, bunlar elle düzeltildi ve "Not" sütununda **[elle]** ile işaretlendi (gerekçe: İş Emri 2026-10-16M1 raporu §3). S3 yeniden puanlama tablosu: `s3_rescored_huni.md`.

| Soru | Kat. | Aşama | Hedef sayfa top-80 | Beklenen belge top-80 | Proje dağılımı (getirilen) | Adlı | assist | Yabancı listede | Puanlayıcı sebebi | Not |
|---|---|---|---|---|---|---|---|---|---|---|
| ANK-FIN-004 | document | **5 Puanlama-kaynak** | — | ✅ | ANK_RES:16 | ANK_RES | — | ❌ | değer | değer doğru, «ECA katılımı olmadığı» kalıp dışı |
| ANK-FIN-005 | document | **3a Israrlı red** | ✅ | ✅ | ANK_RES:16 | ANK_RES | term_mismatch/project | ❌ | answered=False; kaynak; değer | YENİ kayıp: FA + Amd 02 + Faiz Bildirimi promptta (52 parça), model "bulamadım" dedi; assist «bazı» (faiz bazı) sözcüğünü eşleşmeyen terim saydı |
| ANK-OPS-001 | temporal | **3a Israrlı red** | ✅ | ✅ | ANK_RES:26 | ANK_RES | — | ❌ | kaynak; değer | Ağustos 2026 raporu promptta, «3. işletme yılı» aktarılmadı |
| ANK-FIN-010 | data | **4 Excel** | — | ❌ | ANK_RES:16 | ANK_RES | — | ❌ | kaynak | [elle] MIXED; Excel planı Covenant Report workbook yerine Financial Model `dscr` tablosunu seçti (1×7 → 2. deneme 1,37x), beklenen "Covenant Report (workbook)" gösterilmedi; belge kısmı doğru. S3'te Covenant workbook ile geçmişti (betik "1 Arama" dedi: workbook parça taşımaz) |
| IZM-DEV-004 | document | **3a Israrlı red** | — | ✅ | IZM_RES:8 | IZM_RES | clarify/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| IZM-DEV-005 | document | **3a Israrlı red** | — | ✅ | IZM_RES:8 | IZM_RES | clarify/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| IZM-DEV-006 | document | **3a Israrlı red** | — | ✅ | IZM_RES:8 | IZM_RES | term_mismatch/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| ANK-ISO-002 | isolation | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | — | — | ✅ | yasak kaynak | listede/cevapta yabancı proje |
| ANK-ISO-003 | isolation | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:11, YSV_RES:7, IZM_RES:4, BOZ_RES:3 | — | disambiguate/project | — | answered=False; kaynak; değer | proje adı yok → eksen disambiguate, liste yok |
| ANK-MIX-001 | mixed | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:14, YSV_RES:6, BOZ_RES:4, IZM_RES:3 | — | — | ❌ | kaynak; değer | [elle] adsız soru (daraltma yok, 4 projenin parçaları promptta): belge alt-sorusu modelce cevapsız (`ask completed answered=False`), EK_F yalnız Excel kısmını gösterdi (1,37x, Financial Model); Amd 01 + Covenant workbook gösterilmedi (betik "elle bak" dedi) |
| GEN-GEN-003 | document | **3b Kural** | — | — | ANK_RES:26, IZM_RES:4, BOZ_RES:2, YSV_RES:2, grup:1 | — | — | — | answered=True | genel bilgi sorusu cevaplandı (GEN-001/002 reddedildi) |
| ANK-FIN-014 | document | **2b Router** | ❌ | ❌ |  | ANK_RES | — | ❌ | kaynak | [elle] router DATA (S3'te MIXED) → yalnız workbook kartı; soru adıyla Q4 2024 raporunu soruyor (A5 strict), değer 1,24x doğru (betik "1 Arama" dedi: DATA sorgusunda parça yok) |
| ANK-OPS-003 | document | **2b Router** | ❌ | ❌ |  | ANK_RES | — | ❌ | kaynak | router DATA → workbook; adıyla sorulan Aralık 2023 raporu belge |
| ANK-COR-001 | document | **3a Israrlı red** | ✅ | ✅ | ANK_RES:44, grup:3 | ANK_RES | clarify/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| GEN-CMP-003 | comparison | **3b Kural** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | ANK_RES,IZM_RES | — | — | ifade | değerler doğru, karşılaştırma sabit cümlesi yok |
| ANK-NEG-002 | document | **5 Puanlama-kaynak** | — | ✅ | ANK_RES:16 | ANK_RES | — | ❌ | değer | değer doğru, «ECA katılımı görünmüyor» kalıp dışı |
| ANK-NEG-004 | document | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | — | clarify/project | ❌ | answered=False; kaynak; değer | proje adı yok → eksen netleştirmesi, belge erişimde |
| GEN-DSC-002 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:10, BOZ_RES:2, IZM_RES:2, YSV_RES:1 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-004 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:14, IZM_RES:8 | — | disambiguate/project | — | discovery | proje adı yok → eksen disambiguate, liste yok |
| GEN-DSC-006 | discovery | **2 Proje ekseni** | — | ❌ | ANK_RES:1, IZM_RES:1, YSV_RES:1, BOZ_RES:1 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-007 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:11, IZM_RES:4 | — | clarify | — | discovery | proje adı yok → eksen netleştirmesi, belge erişimde |
| GEN-DSC-008 | discovery | **1 Arama** | — | ❌ | YSV_RES:1 | — | clarify | ✅ | discovery | xlsx (Budget vs Actual) parça taşımaz, keşfe giremez |
| GEN-DSC-009 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:14, YSV_RES:7, BOZ_RES:4, IZM_RES:3 | — | term_mismatch | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-010 | discovery | **2 Proje ekseni** | — | ✅ | YSV_RES:7, ANK_RES:6, IZM_RES:3, BOZ_RES:2 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-011 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:21, IZM_RES:12, YSV_RES:7, BOZ_RES:5, grup:2, AKY_GES:1 | — | disambiguate/project | — | discovery | [elle] adsız soru → disambiguate (Karatepe/Kızılova), liste yok, Excel plan none; S3'teki "4 Excel" override bu koşuda geçersiz |
| GEN-DSC-006-M | discovery | **2 Proje ekseni** | — | ❌ | ANK_RES:1, IZM_RES:1, YSV_RES:1, BOZ_RES:1 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-008-M | discovery | **1 Arama** | — | ❌ | YSV_RES:1 | — | clarify | ✅ | discovery | xlsx (Budget vs Actual) parça taşımaz, keşfe giremez; bu koşuda DOCUMENT (S3'te DATA→düşüş) [elle: not güncellendi] |
| GEN-DSC-007-K | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:11, IZM_RES:4 | — | clarify | — | discovery | proje adı yok → eksen netleştirmesi, belge erişimde |

## Özet — aşama başına kayıp

| Aşama | M1 | S3r |
|---|---|---|
| 1 Arama | 2 | 2 |
| 2 Proje ekseni | 13 | 14 |
| 2b Router | 2 | 1 |
| 3a Israrlı red | 6 | 5 |
| 3b Kural | 2 | 2 |
| 4 Excel | 1 | 1 |
| 5 Puanlama-kaynak | 2 | 4 |
| **Toplam** | **28** | **29** |
