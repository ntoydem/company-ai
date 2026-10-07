# Kuru koşu — kodla belirsizlik tespiti, 80 soru (07.10.2026, LLM'siz, kota 0)

Komut: `docker compose … run --rm -T backend python -m scripts.dry_run_ambiguity` — `app/services/ambiguity.py` (TOP_N=15, CLOSE=0.5; eşikler yalnızca 5 belirsiz soruya göre ayarlandı, yeniden ayarlanmadı). "(i) kapsamsız" sütunu yalnızca sınıf-kelime/proje/liste testini gösterir; belge türü/başlık adlandırma istisnası (b) ayrıca uygulanır (ANK-NEG-003/004 ve GEN-AMB-003-F bu yüzden ✓ görünse de ateşlenmez). Rapor: `docs/reports/BELIRSIZLIK_REPORT.md` §8.

dry-run-ambiguity — TOP_N=15 CLOSE=0.5: 80 soru, ateşlendi 6, yanlış pozitif 0, yanlış negatif 0, router (MIXED/DATA) tarafından yolda dışlanan 1

| Soru | Kategori | Kullanıcı | Beklenen | Ateşlendi | (i) kapsamsız | (ii) grup | parça | Sorulacak |
|---|---|---|---|---|---|---|---|---|
| ANK-DEV-001 | document | enerji | – | – | – | 11 | 80 |  |
| ANK-DEV-002 | document | enerji | – | – | – | 11 | 80 |  |
| ANK-DEV-003 | document | enerji | – | – | – | 10 | 80 |  |
| ANK-DEV-004 | temporal | enerji | – | – | – | 10 | 80 |  |
| ANK-DEV-005 | temporal | enerji | – | – | – | 9 | 80 |  |
| ANK-FIN-001 | document | finans | – | – | – | 8 | 45 |  |
| ANK-FIN-002 | document | finans | – | – | – | 5 | 50 |  |
| ANK-FIN-003 | document | finans | – | – | – | 5 | 64 |  |
| ANK-FIN-004 | document | finans | – | – | – | 5 | 52 |  |
| ANK-FIN-005 | document | finans | – | – | – | 5 | 49 |  |
| ANK-FIN-006 | temporal | finans | – | – | – | 7 | 46 |  |
| ANK-FIN-007 | temporal | finans | – | – | – | 7 | 46 |  |
| ANK-FIN-008 | temporal | finans | – | – | – | 6 | 50 |  |
| ANK-FIN-009 | document | finans | – | – | – | 6 | 51 |  |
| ANK-EPC-001 | document | enerji | – | – | – | 9 | 80 |  |
| ANK-EPC-002 | document | enerji | – | – | – | 8 | 80 |  |
| ANK-EPC-003 | document | enerji | – | – | – | 10 | 80 |  |
| ANK-OPS-001 | temporal | enerji | – | – | – | 9 | 80 |  |
| ANK-FIN-010 | data | finans | – | – | – | 7 | 46 |  |
| ANK-FIN-011 | document | finans | – | – | – | 7 | 41 |  |
| ANK-FIN-012 | temporal | finans | – | – | – | 7 | 47 |  |
| ANK-FIN-013 | temporal | finans | – | – | – | 5 | 63 |  |
| ANK-EPC-004 | temporal | enerji | – | – | – | 12 | 80 |  |
| IZM-DEV-001 | document | enerji | – | – | – | 8 | 80 |  |
| IZM-DEV-002 | document | enerji | – | – | – | 7 | 80 |  |
| IZM-DEV-003 | document | enerji | – | – | – | 10 | 80 |  |
| IZM-DEV-004 | document | enerji | – | – | – | 8 | 80 |  |
| IZM-DEV-005 | document | enerji | – | – | – | 14 | 80 |  |
| IZM-DEV-006 | document | enerji | – | – | – | 9 | 80 |  |
| IZM-DEV-007 | document | enerji | – | – | – | 9 | 80 |  |
| IZM-DEV-008 | document | enerji | – | – | – | 7 | 80 |  |
| IZM-DEV-009 | document | enerji | – | – | – | 9 | 80 |  |
| GEN-HAL-001 | hallucination | enerji | – | – | – | 7 | 80 |  |
| GEN-HAL-002 | hallucination | enerji | – | – | – | 11 | 80 |  |
| GEN-HAL-003 | hallucination | enerji | – | – | – | 10 | 80 |  |
| GEN-HAL-004 | hallucination | finans | – | – | – | 4 | 49 |  |
| IZM-ISO-001 | isolation | enerji | – | – | – | 9 | 80 |  |
| ANK-ISO-002 | isolation | enerji | – | – | – | 12 | 80 |  |
| ANK-ISO-003 | isolation | finans | – | – | – | 2 | 26 |  |
| IZM-ISO-004 | isolation | finans | – | – | – | 5 | 52 |  |
| ANK-AUT-001 | authorization | enerji | – | – | – | 10 | 80 |  |
| ANK-AUT-002 | authorization | enerji | – | – | – | 9 | 80 |  |
| ANK-AUT-003 | authorization | enerji | – | – | – | 10 | 80 |  |
| ANK-DAT-001 | data | finans | – | – | – | 7 | 54 |  |
| ANK-DAT-002 | data | enerji | – | – | – | 11 | 80 |  |
| ANK-DAT-003 | data | yonetim | – | – | – | 7 | 80 |  |
| ANK-MIX-001 | mixed | finans | – | 🔥 | ✓ | 2 | 7 | Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Covenant Compliance Report — Q4 2024? |
| ANK-MIX-002 | mixed | enerji | – | – | – | 11 | 80 |  |
| GEN-GEN-001 | document | yonetim | – | – | – | 5 | 13 |  |
| GEN-GEN-002 | document | yonetim | – | – | – | 11 | 65 |  |
| GEN-GEN-003 | document | yonetim | – | – | – | 4 | 80 |  |
| ANK-MIX-003 | mixed | enerji | – | – | – | 9 | 80 |  |
| ANK-FIN-014 | document | finans | – | – | – | 7 | 47 |  |
| ANK-FIN-015 | document | finans | – | – | – | 5 | 50 |  |
| ANK-DEV-006 | document | enerji | – | – | – | 9 | 80 |  |
| ANK-OPS-002 | document | enerji | – | – | – | 11 | 80 |  |
| ANK-EPC-005 | document | enerji | – | – | – | 11 | 80 |  |
| ANK-OPS-003 | document | enerji | – | – | – | 9 | 80 |  |
| ANK-COR-001 | document | yonetim | – | – | – | 7 | 80 |  |
| IZM-DEV-010 | document | enerji | – | – | – | 7 | 80 |  |
| IZM-DEV-011 | temporal | hukuk | – | – | – | 4 | 22 |  |
| GEN-CMP-001 | comparison | enerji | – | – | – | 13 | 80 |  |
| GEN-CMP-002 | comparison | enerji | – | – | – | 13 | 80 |  |
| GEN-CMP-003 | comparison | enerji | – | – | – | 10 | 80 |  |
| GEN-AMB-001 | ambiguous | yonetim | 🔶 belirsiz | 🔥 | ✓ | 8 | 68 | Hangi belgeyi kastediyorsunuz: Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri; Facility Agreement Amendment 01; Ankara RES Security Agreement (Share Pledge)? |
| GEN-AMB-002 | ambiguous | finans | 🔶 belirsiz | 🔥 | ✓ | 2 | 11 | Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Covenant Compliance Report — Q4 2024? |
| GEN-AMB-003 | ambiguous | yonetim | 🔶 belirsiz | 🔥 | ✓ | 7 | 25 | Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi? |
| GEN-AMB-004 | ambiguous | enerji | 🔶 belirsiz | 🔥 | ✓ | 11 | 18 | Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi? |
| GEN-AMB-005 | ambiguous | yonetim | 🔶 belirsiz | 🔥 | ✓ | 5 | 46 | Hangi belgeyi kastediyorsunuz: Yönetim Kurulu Kararı — Denetim Komitesi Ataması; Ankara RES ÇED Olumlu Kararı; Pay Sahipleri Kararı — Kâr Dağıtım Politikası? |
| GEN-TRM-001 | term_mismatch | enerji | – | – | – | 9 | 80 |  |
| GEN-TRM-002 | term_mismatch | enerji | – | – | – | 8 | 80 |  |
| GEN-TRM-004 | term_mismatch | enerji | – | – | – | 9 | 80 |  |
| GEN-TRM-005 | term_mismatch | enerji | – | – | – | 9 | 80 |  |
| ANK-OPS-004 | temporal | enerji | – | – | – | 9 | 80 |  |
| ANK-NEG-001 | document | finans | – | – | – | 5 | 49 |  |
| ANK-NEG-002 | document | finans | – | – | – | 5 | 52 |  |
| ANK-NEG-003 | document | finans | – | – | ✓ | 2 | 42 |  |
| ANK-NEG-004 | document | enerji | – | – | ✓ | 11 | 80 |  |
| CO-NEG-005 | document | yonetim | – | – | – | 8 | 80 |  |
| GEN-AMB-003-F | document | finans | – | – | ✓ | 1 | 9 |  |

Ateşlenen sorular ve gerekçe:
- ANK-MIX-001 (mixed, finans) — "Güncel DSCR kaç?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 2 grup → Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Covenant Compliance Report — Q4 2024?
- GEN-AMB-001 (ambiguous, yonetim) — "Sözleşmenin vadesi ne zaman doluyor?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 8 grup → Hangi belgeyi kastediyorsunuz: Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri; Facility Agreement Amendment 01; Ankara RES Security Agreement (Share Pledge)?
- GEN-AMB-002 (ambiguous, finans) — "Raporda belirtilen DSCR değeri kaç?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 2 grup → Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Covenant Compliance Report — Q4 2024?
- GEN-AMB-003 (ambiguous, yonetim) — "Son tadil neyi değiştirdi?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 7 grup → Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi?
- GEN-AMB-004 (ambiguous, enerji) — "Lisans ne zaman alındı?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 11 grup → Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi?
- GEN-AMB-005 (ambiguous, yonetim) — "Toplantıda ne karar alındı?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 5 grup → Hangi belgeyi kastediyorsunuz: Yönetim Kurulu Kararı — Denetim Komitesi Ataması; Ankara RES ÇED Olumlu Kararı; Pay Sahipleri Kararı — Kâr Dağıtım Politikası?

Yanlış pozitif: []
Yanlış negatif: []
Yolda dışlanan (MIXED/DATA): ['ANK-MIX-001']
