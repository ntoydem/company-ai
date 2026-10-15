# T1-A — «Fazla cömert mi?» kontrolü: 70 geçen soru tek tek

Yöntem: `results/s3_rescored/results.json` alanları (value/source/safety/assist/discovery) + `questions.json` + ledger ham değeri; LLM yok, puanlayıcı değiştirilmedi. Bir soru birden çok sınıfa girebilir. «Kontrolör bakmalı» = kod alanlarından karar verilemeyen satır.

## Sınıf özeti

| Sınıf | Soru sayısı | Sorular |
|---|---|---|
| (a) yalnız değer eşleşmesiyle geçti, kaynak/proje yanlış olabilir | 3 | ANK-FIN-001, ANK-FIN-007, ANK-FIN-011 |
| (b) «küme» kuralıyla geçti ama tam belge beklenebilirdi | 3 | ANK-FIN-001, ANK-FIN-007, ANK-FIN-009 |
| (c) netleştirme/disambiguate metniyle geçti ama değer sorulmuştu | 10 | ANK-AUT-001, ANK-AUT-002, ANK-NEG-003, GEN-AMB-003-F, GEN-DSC-001-M, GEN-DSC-005, GEN-GEN-001, GEN-GEN-002, GEN-HAL-001, GEN-HAL-004 |
| (d) bir kuralın gevşemesi KY'yi (kendinden emin yanlış) gizleyebilir | 30 | ANK-AUT-003, ANK-DAT-001, ANK-DAT-002, ANK-DAT-003, ANK-DEV-003, ANK-EPC-002, ANK-EPC-004, ANK-FIN-008, ANK-FIN-009, ANK-FIN-010, ANK-FIN-011, ANK-FIN-012, ANK-FIN-014, ANK-FIN-015, ANK-MIX-002, ANK-MIX-003, ANK-OPS-002, CO-NEG-005, GEN-DSC-001, GEN-DSC-003, GEN-DSC-012, GEN-DSC-013, GEN-GEN-001, GEN-HAL-001, GEN-HAL-004, GEN-TRM-001, GEN-TRM-002, GEN-TRM-004, IZM-DEV-001, IZM-DEV-008 |
| temiz (hiçbir bayrak yok) | 31 | ANK-DEV-001, ANK-DEV-002, ANK-DEV-004, ANK-DEV-005, ANK-FIN-002, ANK-FIN-003, ANK-FIN-005, ANK-FIN-006, ANK-EPC-001, ANK-EPC-003, IZM-DEV-002, IZM-DEV-003, IZM-DEV-009, GEN-HAL-002, IZM-ISO-001, IZM-ISO-004, ANK-DEV-006, ANK-EPC-005, IZM-DEV-010, IZM-DEV-011, GEN-CMP-001, GEN-CMP-002, GEN-AMB-001, GEN-AMB-002, GEN-AMB-003, GEN-AMB-004, GEN-AMB-005, GEN-AMB-006, GEN-TRM-005, ANK-OPS-004, ANK-NEG-001 |

### (d) alt kırılımı

| Alt sınıf | n | Sorular |
|---|---|---|
| cevap var, değer doğrulanmadı | 17 | ANK-FIN-008, ANK-FIN-009, ANK-EPC-002, ANK-FIN-010, ANK-FIN-012, ANK-EPC-004, IZM-DEV-001, IZM-DEV-008, ANK-MIX-002, ANK-MIX-003, ANK-FIN-015, ANK-OPS-002, CO-NEG-005, GEN-DSC-001, GEN-DSC-003, GEN-DSC-012, GEN-DSC-013 |
| G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY | 9 | ANK-DEV-003, ANK-FIN-010, ANK-FIN-011, ANK-EPC-004, ANK-DAT-001, ANK-DAT-003, ANK-MIX-002, ANK-MIX-003, ANK-FIN-014 |
| cevapsız yanıt metninde rakam/tarih var | 7 | GEN-HAL-001, GEN-HAL-004, ANK-AUT-003, GEN-GEN-001, GEN-TRM-001, GEN-TRM-002, GEN-TRM-004 |
| G1 yalnız DOCUMENT_QUERY'de; bu DATA_QUERY | 2 | ANK-DAT-002, GEN-DSC-001 |
| F-8 biçim hatası puana girmiyor | 1 | GEN-DSC-001 |

## Şüpheli satırlar (benim okumam)

| Soru | Sınıf | Okuma | Kontrolör? |
|---|---|---|---|
| ANK-FIN-001 | a,b | değer doğru (08.07.2022); kaynak Amendment 02 — FA zincirinin güncel halkası, aynı olgu; v1'de de tür okumasıyla geçerdi | — |
| ANK-FIN-007 | a,b | değer doğru (1,25x); Draft'ı da gösteriyor (tolere edildi); 'ilk' soruya Draft'tan cevap vermesi tarihsel okuma — kontrolör bakmalı | kontrolör bakmalı |
| ANK-FIN-009 | b,d | 'Facility Agreement'ında' kalıbı 14 işaret dışında; tam belge gösterildiği için sonuç değişmez; değer (2 amendment) doğrulanmadı ama metinde doğru | — |
| ANK-FIN-011 | a,d | değer doğru (11.671.800); 7 kaynak, uzun cevap, %3,25 / 14.000.000 USD gibi ek rakamlar MIXED olduğu için G1 denetimi dışı — kontrolör bakmalı | kontrolör bakmalı |
| ANK-NEG-003 | c | vade sorulmuş, netleştirme döndü (Karatepe mi Yeşilova mı); altın küme bunu bekliyor (expect_assist) — puan tasarım gereği, 'cömert' değil | — |
| GEN-AMB-003-F | c | 'son tadil' → proje netleştirmesi; beklenen clarify, gelen disambiguate (eşdeğer sayılıyor, B2a) | — |
| GEN-GEN-002 | c | genel bilgi sorusuna 'Hangi projeyi kastediyorsunuz' döndü; cevapsız olması doğru, netleştirmenin anlamlılığı tartışılır — kontrolör bakmalı | kontrolör bakmalı |
| GEN-HAL-004 | c,d | cevap yok + yalnız Kızılova listesi; Karatepe FA zinciri gösterilmedi — v13 beklentisiyle tutarlı | — |
| GEN-DSC-001-M | c | liste + soru (discovery ölçütü); A2 ile finans_mudur görünürlüğü düzeldi | — |
| GEN-DSC-005 | c | liste + soru; beklenen Amendment 01 listede | — |
| ANK-FIN-010 | d | değer kontrolü atlandı ('pass' biçimlenemez); cevap 1,37x veriyor ama test sonucunu (geçti) açıkça söylemiyor — sınır, kontrolör bakmalı | kontrolör bakmalı |
| ANK-FIN-012 | d | değer kontrolü atlandı (belge kimliği); metin Amendment 02 / 15.03.2025 diyor — doğru | — |
| ANK-EPC-004 | d | değer kontrolü atlandı; 'şebeke bağlantı işleri' sebebi metinde var; MIXED → G1 dışı | — |
| IZM-DEV-001 | d | değer kontrolü atlandı ('development'); cevap aşamayı adıyla söylemiyor, ÇED/önlisans durumunu aktarıyor — sınır, kontrolör bakmalı | kontrolör bakmalı |
| IZM-DEV-008 | d | değer kontrolü atlandı (liste); ÇED, TEİAŞ, MSB adımları doğru; ledger'daki imar/kat'i proje/yapı ruhsatı eksik — kısmi | — |
| ANK-MIX-002 | d | değer kontrolü atlandı (dict); Excel sapması −894.000 TL aritmetik doğru; belge kısmındaki 12553 MWh / %91,4 MIXED olduğu için G1 dışı — kontrolör bakmalı | kontrolör bakmalı |
| ANK-MIX-003 | d | değer kontrolü atlandı (dict); 371.000 TL aritmetik doğru (34.871.000 − 34.500.000) | — |
| GEN-DSC-001 | d | discovery; DATA yolu '13600000' gruplanmamış (F-8 ❌, puana girmiyor); 'var mı' sorusuna hesap döndürdü | — |
| GEN-DSC-003 | d | discovery; 'sona erdi' cevabı — beklenen belge gösterildi; değer doğrulanmadı | — |
| GEN-DSC-012 | d | discovery; üç tadil sayıyor (Licence Amendment dahil) — beklenen belge gösterildi | — |

## 70 soru — tam tablo

| Soru | Kat. | Kullanıcı | Cevap | Değer | Kaynak kuralı | Assist | Önce→Sonra | Bayraklar |
|---|---|---|---|---|---|---|---|---|
| ANK-DEV-001 | document | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-DEV-002 | document | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-DEV-003 | document | enerji | var | pass | set | — | ✅→✅ | d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-DEV-004 | temporal | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-DEV-005 | temporal | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-FIN-001 | document | finans | var | pass | set | — | ✅→✅ | a:beklenen belge değil, küme üyesi gösterildi; b:set kuralıyla geçti, required_sources tam gösterilmedi |
| ANK-FIN-002 | document | finans | var | pass | set | — | ✅→✅ | — |
| ANK-FIN-003 | document | finans | var | pass | set | — | ✅→✅ | — |
| ANK-FIN-005 | document | finans | var | pass | set | — | ✅→✅ | — |
| ANK-FIN-006 | temporal | finans | var | pass | set | — | ✅→✅ | — |
| ANK-FIN-007 | temporal | finans | var | pass | set | — | ✅→✅ | a:beklenen belge değil, küme üyesi gösterildi; b:set kuralıyla geçti, required_sources tam gösterilmedi |
| ANK-FIN-008 | temporal | finans | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str) |
| ANK-FIN-009 | document | finans | var | skipped | set | — | ✅→✅ | b:soru belgeyi adıyla anıyor olabilir (14 işaret dışı kalıp); d:cevap var, değer doğrulanmadı (unformattable expected_answer type: list) |
| ANK-EPC-001 | document | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-EPC-002 | document | enerji | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str) |
| ANK-EPC-003 | document | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-FIN-010 | data | finans | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str); d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-FIN-011 | document | finans | var | pass | set | — | ✅→✅ | a:çok kaynak (7); d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-FIN-012 | temporal | finans | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str) |
| ANK-EPC-004 | temporal | enerji | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str); d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| IZM-DEV-001 | document | enerji | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str) |
| IZM-DEV-002 | document | enerji | var | pass | set | — | ✅→✅ | — |
| IZM-DEV-003 | document | enerji | var | pass | set | — | ✅→✅ | — |
| IZM-DEV-008 | document | enerji | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: list) |
| IZM-DEV-009 | document | enerji | var | pass | set | — | ✅→✅ | — |
| GEN-HAL-001 | hallucination | enerji | yok | skipped | n/a | clarify | ✅→✅ | c:netleştirmeyle geçti (kategori hallucination, ledger yolu yok); d:cevapsız yanıt metninde rakam/tarih var |
| GEN-HAL-002 | hallucination | enerji | yok | skipped | n/a | term_mismatch | ✅→✅ | — |
| GEN-HAL-004 | hallucination | finans | yok | skipped | n/a | clarify | ❌→✅ | c:netleştirmeyle geçti (kategori hallucination, ledger yolu yok); d:cevapsız yanıt metninde rakam/tarih var |
| IZM-ISO-001 | isolation | enerji | var | pass | set | — | ✅→✅ | — |
| IZM-ISO-004 | isolation | finans | var | pass | set | — | ❌→✅ | — |
| ANK-AUT-001 | authorization | enerji | yok | skipped | n/a | clarify | ✅→✅ | c:netleştirmeyle geçti (kategori authorization, ledger yolu yok) |
| ANK-AUT-002 | authorization | enerji | yok | skipped | n/a | clarify | ✅→✅ | c:netleştirmeyle geçti (kategori authorization, ledger yolu yok) |
| ANK-AUT-003 | authorization | enerji | yok | skipped | n/a | term_mismatch | ✅→✅ | d:cevapsız yanıt metninde rakam/tarih var |
| ANK-DAT-001 | data | finans | var | pass | set | — | ✅→✅ | d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-DAT-002 | data | enerji | var | pass | set | — | ✅→✅ | d:G1 yalnız DOCUMENT_QUERY'de; bu DATA_QUERY |
| ANK-DAT-003 | data | yonetim | var | pass | set | — | ✅→✅ | d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-MIX-002 | mixed | enerji | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: dict); d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| GEN-GEN-001 | document | yonetim | yok | skipped | n/a | clarify | ✅→✅ | c:netleştirmeyle geçti (kategori document, ledger yolu yok); d:cevapsız yanıt metninde rakam/tarih var |
| GEN-GEN-002 | document | yonetim | yok | skipped | n/a | disambiguate | ❌→✅ | c:netleştirmeyle geçti (kategori document, ledger yolu yok) |
| ANK-MIX-003 | mixed | enerji | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: dict); d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-FIN-014 | document | finans | var | pass | strict | — | ✅→✅ | d:G1 yalnız DOCUMENT_QUERY'de; bu MIXED_QUERY |
| ANK-FIN-015 | document | finans | var | skipped | strict | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: int) |
| ANK-DEV-006 | document | enerji | var | pass | strict | — | ✅→✅ | — |
| ANK-OPS-002 | document | enerji | var | skipped | strict | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str) |
| ANK-EPC-005 | document | enerji | var | pass | strict | — | ✅→✅ | — |
| IZM-DEV-010 | document | enerji | var | pass | strict | — | ✅→✅ | — |
| IZM-DEV-011 | temporal | hukuk | var | pass | strict | — | ✅→✅ | — |
| GEN-CMP-001 | comparison | enerji | var | pass | set | — | ✅→✅ | — |
| GEN-CMP-002 | comparison | enerji | var | pass | set | — | ✅→✅ | — |
| GEN-AMB-001 | ambiguous | yonetim | yok | skipped | n/a | clarify | ✅→✅ | — |
| GEN-AMB-002 | ambiguous | finans | yok | skipped | n/a | disambiguate | ❌→✅ | — |
| GEN-AMB-003 | ambiguous | yonetim | yok | skipped | n/a | disambiguate | ❌→✅ | — |
| GEN-AMB-004 | ambiguous | enerji | yok | skipped | n/a | disambiguate | ❌→✅ | — |
| GEN-AMB-005 | ambiguous | yonetim | yok | skipped | n/a | disambiguate | ❌→✅ | — |
| GEN-AMB-006 | ambiguous | hukuk | yok | skipped | n/a | disambiguate | ❌→✅ | — |
| GEN-TRM-001 | term_mismatch | enerji | yok | skipped | n/a | term_mismatch | ✅→✅ | d:cevapsız yanıt metninde rakam/tarih var |
| GEN-TRM-002 | term_mismatch | enerji | yok | skipped | n/a | term_mismatch | ✅→✅ | d:cevapsız yanıt metninde rakam/tarih var |
| GEN-TRM-004 | term_mismatch | enerji | yok | skipped | n/a | term_mismatch | ✅→✅ | d:cevapsız yanıt metninde rakam/tarih var |
| GEN-TRM-005 | term_mismatch | enerji | yok | skipped | n/a | term_mismatch | ✅→✅ | — |
| ANK-OPS-004 | temporal | enerji | var | pass | set | — | ✅→✅ | — |
| ANK-NEG-001 | document | finans | var | pass | set | — | ✅→✅ | — |
| ANK-NEG-003 | document | finans | yok | skipped | n/a | disambiguate | ❌→✅ | c:netleştirmeyle geçti (kategori document, ledger yolu var) |
| CO-NEG-005 | document | yonetim | var | skipped | set | — | ✅→✅ | d:cevap var, değer doğrulanmadı (unformattable expected_answer type: str) |
| GEN-AMB-003-F | document | finans | yok | skipped | n/a | disambiguate | ❌→✅ | c:netleştirmeyle geçti (kategori document, ledger yolu var) |
| GEN-DSC-001 | discovery | finans | var | skipped | n/a | — | ✅→✅ | d:cevap var, değer doğrulanmadı (expect_no_answer); d:G1 yalnız DOCUMENT_QUERY'de; bu DATA_QUERY; d:F-8 biçim hatası puana girmiyor (gruplanmamış sayı) |
| GEN-DSC-003 | discovery | enerji | var | skipped | n/a | — | ✅→✅ | d:cevap var, değer doğrulanmadı (expect_no_answer) |
| GEN-DSC-005 | discovery | yonetim | yok | skipped | n/a | clarify | ✅→✅ | c:netleştirmeyle geçti (kategori discovery, ledger yolu yok) |
| GEN-DSC-012 | discovery | yonetim | var | skipped | n/a | — | ✅→✅ | d:cevap var, değer doğrulanmadı (expect_no_answer) |
| GEN-DSC-013 | discovery | yonetim | var | skipped | n/a | — | ✅→✅ | d:cevap var, değer doğrulanmadı (expect_no_answer) |
| GEN-DSC-001-M | discovery | finans_mudur | yok | skipped | n/a | clarify | ❌→✅ | c:netleştirmeyle geçti (kategori discovery, ledger yolu yok) |
