# Huni tablosu — S3 yeniden puanlama (v2.0) kalan kayıplar

Her kayıp tek aşamaya atanır. Aşama 1–2 kanıtı LLM'siz: S3 audit `chunks_retrieved` (hedef sayfa top-80'de mi?) + getirilen belgelerin proje dağılımı; `assist.kind`/`axis` S3 cevabından; diğerleri `OVERRIDES` (S3 raporu §3.4 okuması, betikte gerekçeli).

| Soru | Kat. | Aşama | Hedef sayfa top-80 | Beklenen belge top-80 | Proje dağılımı (getirilen) | Adlı | assist | Yabancı listede | Puanlayıcı sebebi | Not |
|---|---|---|---|---|---|---|---|---|---|---|
| ANK-FIN-004 | document | **5 Puanlama-kaynak** | — | ✅ | ANK_RES:16, YSV_RES:8, BOZ_RES:4, IZM_RES:4 | ANK_RES | — | ❌ | değer | değer doğru, «ECA katılımı olmadığı» kalıp dışı |
| ANK-OPS-001 | temporal | **3a Israrlı red** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | ANK_RES | — | ❌ | kaynak; değer | Ağustos 2026 raporu promptta, «3. işletme yılı» aktarılmadı |
| ANK-FIN-013 | temporal | **5 Puanlama-kaynak** | ✅ | ✅ | ANK_RES:16, YSV_RES:6, BOZ_RES:3, IZM_RES:3 | ANK_RES | — | ❌ | değer | değerler doğru, `3.25%` yazımı (F-8/kalıp) |
| IZM-DEV-004 | document | **3a Israrlı red** | — | ✅ | ANK_RES:26, IZM_RES:8 | IZM_RES | clarify/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| IZM-DEV-005 | document | **3a Israrlı red** | — | ✅ | ANK_RES:25, IZM_RES:8 | IZM_RES | clarify/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| IZM-DEV-006 | document | **3a Israrlı red** | — | ✅ | ANK_RES:26, IZM_RES:8 | IZM_RES | term_mismatch/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| IZM-DEV-007 | document | **5 Puanlama-kaynak** | — | ✅ | ANK_RES:26, IZM_RES:8 | IZM_RES | — | ❌ | kaynak | adımlar doğru, ÇED yazısı yetkili kümede değil (ledger taşıyıcı yok) |
| GEN-HAL-003 | hallucination | **2 Proje ekseni** | — | — | ANK_RES:26, IZM_RES:8 | — | term_mismatch/project | — | G: G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| ANK-ISO-002 | isolation | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | — | — | ✅ | yasak kaynak | listede/cevapta yabancı proje |
| ANK-ISO-003 | isolation | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:11, YSV_RES:7, IZM_RES:4, BOZ_RES:3 | — | disambiguate/project | — | answered=False; kaynak; değer | proje adı yok → eksen disambiguate, liste yok |
| ANK-MIX-001 | mixed | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:14, YSV_RES:6, BOZ_RES:4, IZM_RES:3 | — | clarify | ✅ | answered=False; kaynak; değer | listede/cevapta yabancı proje |
| GEN-GEN-003 | document | **3b Kural** | — | — | ANK_RES:26, IZM_RES:4, BOZ_RES:2, YSV_RES:2, grup:1 | — | — | — | answered=True | genel bilgi sorusu cevaplandı (GEN-001/002 reddedildi) |
| ANK-OPS-003 | document | **2b Router** | ❌ | ❌ |  | ANK_RES | — | ❌ | kaynak | router DATA → workbook; adıyla sorulan Aralık 2023 raporu belge |
| ANK-COR-001 | document | **3a Israrlı red** | ✅ | ✅ | ANK_RES:44, grup:3 | ANK_RES | clarify/project | ❌ | answered=False; kaynak | beklenen belge promptta, cevap yok |
| GEN-CMP-003 | comparison | **3b Kural** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | ANK_RES,IZM_RES | — | — | ifade | değerler doğru, karşılaştırma sabit cümlesi yok |
| ANK-NEG-002 | document | **5 Puanlama-kaynak** | — | ✅ | ANK_RES:16, YSV_RES:8, BOZ_RES:4, IZM_RES:4 | ANK_RES | — | ❌ | değer | değer doğru, «ECA katılımı görünmüyor» kalıp dışı |
| ANK-NEG-004 | document | **2 Proje ekseni** | ✅ | ✅ | ANK_RES:26, IZM_RES:8 | — | clarify/project | ❌ | answered=False; kaynak; değer | proje adı yok → eksen netleştirmesi, belge erişimde |
| GEN-DSC-002 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:10, BOZ_RES:2, IZM_RES:2, YSV_RES:1 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-004 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:14, IZM_RES:8 | — | disambiguate/project | — | discovery | proje adı yok → eksen disambiguate, liste yok |
| GEN-DSC-006 | discovery | **2 Proje ekseni** | — | ❌ | ANK_RES:1, IZM_RES:1, YSV_RES:1, BOZ_RES:1 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-007 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:11, IZM_RES:4 | — | clarify | — | discovery | proje adı yok → eksen netleştirmesi, belge erişimde |
| GEN-DSC-008 | discovery | **1 Arama** | — | ❌ | YSV_RES:1 | — | — | ✅ | discovery | xlsx (Budget vs Actual) parça taşımaz, keşfe giremez |
| GEN-DSC-009 | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:14, YSV_RES:7, BOZ_RES:4, IZM_RES:3 | — | term_mismatch | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-010 | discovery | **2 Proje ekseni** | — | ✅ | YSV_RES:7, ANK_RES:6, IZM_RES:3, BOZ_RES:2 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-011 | discovery | **4 Excel** | — | ✅ | ANK_RES:21, IZM_RES:12, YSV_RES:7, BOZ_RES:5, grup:2, AKY_GES:1 | — | — | ❌ | discovery | MIXED: Excel tek hücre (tutar), tarih düştü; FA belgesi gösterilmedi |
| GEN-DSC-006-M | discovery | **2 Proje ekseni** | — | ❌ | ANK_RES:1, IZM_RES:1, YSV_RES:1, BOZ_RES:1 | — | clarify | ✅ | G: G3: başka projenin belgesi önerildi; G3: yasak kaynak assist'te | listede/cevapta yabancı proje |
| GEN-DSC-008-M | discovery | **1 Arama** | — | ❌ | YSV_RES:1 | — | — | ✅ | discovery | router DATA → plan none → belge düşüşü; xlsx keşfe giremez |
| GEN-DSC-007-K | discovery | **2 Proje ekseni** | — | ✅ | ANK_RES:11, IZM_RES:4 | — | clarify | — | discovery | proje adı yok → eksen netleştirmesi, belge erişimde |
| GEN-DSC-011-K | discovery | **2 Proje ekseni** | — | ❌ | ANK_RES:21, IZM_RES:12, YSV_RES:7, BOZ_RES:5, grup:2, AKY_GES:1 | — | disambiguate/project | — | discovery | proje adı yok → eksen disambiguate, liste yok |

## Özet — aşama başına kayıp

| Aşama | Sayı |
|---|---|
| 1 Arama | 2 |
| 2 Proje ekseni | 14 |
| 2b Router | 1 |
| 3a Israrlı red | 5 |
| 3b Kural | 2 |
| 4 Excel | 1 |
| 5 Puanlama-kaynak | 4 |
| **Toplam** | **29** |
