# Kuru koşu — held-out 10 soru (08.10.2026, LLM'siz, kota 0, canlı çağrı yok)

Komut: `docker compose … run --rm -T backend python -m scripts.dry_run_ambiguity --only-held-out --detail` — `app/services/ambiguity.py` V3 (TOP_N=15, CLOSE=0.5, eşikler DEĞİŞTİRİLMEDİ). Sorular: Tansu taslağı, Naci onayı 08.10.2026, `questions.json` → `held_out` (`run_eval` okumaz). Yorum: `docs/reports/BELIRSIZLIK_REPORT.md` §15.

dry-run-ambiguity — TOP_N=15 CLOSE=0.5: 10 soru, ateşlendi 3, yanlış pozitif 1, yanlış negatif 3, router (MIXED/DATA) tarafından yolda dışlanan 0

| Soru | Kategori | Kullanıcı | Beklenen | Ateşlendi | (i) kapsamsız | (ii) grup | parça | Sorulacak |
|---|---|---|---|---|---|---|---|---|
| HO-AMB-01 (held-out) | ambiguous | enerji | 🔶 belirsiz | 🔥 | ✓ | 10 | 78 | Hangi belgeyi kastediyorsunuz: Aylık Üretim Raporu — Aralık 2023; Ankara RES ÇED Olumlu Kararı; Ankara RES Saha Kullanım Hakkı Sözleşmesi? |
| HO-AMB-02 (held-out) | ambiguous | enerji | 🔶 belirsiz | – | – | 8 | 13 |  |
| HO-AMB-03 (held-out) | ambiguous | enerji | 🔶 belirsiz | – | ✓ | 7 | 51 |  |
| HO-AMB-04 (held-out) | ambiguous | yonetim | 🔶 belirsiz | 🔥 | ✓ | 5 | 46 | Hangi belgeyi kastediyorsunuz: Yönetim Kurulu Kararı — Denetim Komitesi Ataması; Ankara RES ÇED Olumlu Kararı; Pay Sahipleri Kararı — Kâr Dağıtım Politikası? |
| HO-AMB-05 (held-out) | ambiguous | yonetim | 🔶 belirsiz | – | – | 8 | 26 |  |
| HO-NEG-01 (held-out) | document | enerji | – | – | – | 12 | 17 |  |
| HO-NEG-02 (held-out) | document | finans | – | 🔥 | ✓ | 5 | 62 | Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Drawdown Notice — Tranche 1; Covenant Compliance Report Q2 2026? |
| HO-NEG-03 (held-out) | document | enerji | – | – | – | 0 | 0 |  |
| HO-NEG-04 (held-out) | document | yonetim | – | – | – | 2 | 2 |  |
| HO-NEG-05 (held-out) | document | enerji | – | – | – | 10 | 37 |  |

Ateşlenen sorular ve gerekçe:
- HO-AMB-01 (ambiguous, enerji) — "Üretim rakamı ne kadar?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 10 grup → Hangi belgeyi kastediyorsunuz: Aylık Üretim Raporu — Aralık 2023; Ankara RES ÇED Olumlu Kararı; Ankara RES Saha Kullanım Hakkı Sözleşmesi?
- HO-AMB-04 (ambiguous, yonetim) — "Karar ne zaman alındı?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 5 grup → Hangi belgeyi kastediyorsunuz: Yönetim Kurulu Kararı — Denetim Komitesi Ataması; Ankara RES ÇED Olumlu Kararı; Pay Sahipleri Kararı — Kâr Dağıtım Politikası?
- HO-NEG-02 (document, finans) — "Banka hangi DSCR seviyesini şart koşuyor?": kapsamsız (yalnızca belge-sınıfı terim, proje/liste kelimesi yok) + 5 grup → Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Drawdown Notice — Tranche 1; Covenant Compliance Report Q2 2026?

Yanlış pozitif: ['HO-NEG-02']
Yanlış negatif: ['HO-AMB-02', 'HO-AMB-03', 'HO-AMB-05']
Yolda dışlanan (MIXED/DATA): []

| Soru | Kullanıcı | Niyet | Görebildiği belge | Parça (top-N dağılımı: proje/tür ×n (en iyi rank)) | Grup | Niyet tuttu mu | V3 | Eksen / soru |
|---|---|---|---|---|---|---|---|---|
| HO-AMB-01 | enerji | belirsiz | 36 | ANK_RES/Production Report ×6 (0.50); ANK_RES/ÇED Olumlu Kararı ×1 (0.30); ANK_RES/Saha Kullanım Hakkı Sözleşmesi ×1 (0.30); ANK_RES/Yapı Ruhsatı ×1 (0.30); ANK_RES/O&M Agreement ×1 (0.30); ANK_RES/Performance Test Report ×1 (0.30); ANK_RES/Licence Amendment ×1 (0.30); ANK_RES/Maintenance Report ×1 (0.30); ANK_RES/Üretim Lisansı ×1 (0.30); ANK_RES/Performance Review ×1 (0.30) | 10 | ✅ | 🔥 | belge: Hangi belgeyi kastediyorsunuz: Aylık Üretim Raporu — Aralık 2023; Ankara RES ÇED Olumlu Kararı; Ankara RES Saha Kullanım Hakkı Sözleşmesi? |
| HO-AMB-02 | enerji | belirsiz | 36 | ANK_RES/Licence Amendment ×3 (0.30); ANK_RES/COD Documentation ×1 (0.20); IZM_RES/Teknik Rapor ×3 (0.20); ANK_RES/Üretim Lisansı ×1 (0.20); ANK_RES/ÇED Olumlu Kararı ×1 (0.10); IZM_RES/Önlisans ×1 (0.10); ANK_RES/Performance Test Report ×2 (0.10); ANK_RES/Production Report ×1 (0.10) | 8 | ✅ | – |  |
| HO-AMB-03 | enerji | belirsiz | 36 | IZM_RES/Teknik Rapor ×6 (0.60); ANK_RES/Üretim Lisansı ×1 (0.50); ANK_RES/Bağlantı Anlaşması ×1 (0.40); ANK_RES/Licence Amendment ×1 (0.40); ANK_RES/Completion Report ×3 (0.30); ANK_RES/Performance Test Report ×1 (0.30); ANK_RES/Production Report ×2 (0.30) | 7 | ✅ | – |  |
| HO-AMB-04 | yonetim | belirsiz | 75 | CO/Board Resolution ×6 (0.50); ANK_RES/ÇED Olumlu Kararı ×2 (0.40); CO/Shareholder Resolution ×5 (0.40); ANK_RES/Maintenance Plan ×1 (0.20); ANK_RES/Grid Connection Certificate ×1 (0.20) | 5 | ✅ | 🔥 | belge: Hangi belgeyi kastediyorsunuz: Yönetim Kurulu Kararı — Denetim Komitesi Ataması; Ankara RES ÇED Olumlu Kararı; Pay Sahipleri Kararı — Kâr Dağıtım Politikası? |
| HO-AMB-05 | yonetim | belirsiz | 75 | ANK_RES/Facility Agreement ×6 (0.20); ANK_RES/Change Order ×3 (0.20); ANK_RES/Licence Amendment ×1 (0.20); ANK_RES/Bağlantı Anlaşması ×1 (0.10); IZM_RES/Legal Review Memo ×1 (0.10); IZM_RES/Önlisans ×1 (0.10); IZM_RES/Teknik Rapor ×1 (0.10); IZM_RES/Bağlantı Görüşü Başvurusu ×1 (0.10) | 8 | ✅ | – |  |
| HO-NEG-01 | enerji | net | 36 | IZM_RES/Önlisans ×3 (0.30); ANK_RES/Maintenance Plan ×1 (0.20); ANK_RES/Grid Connection Certificate ×2 (0.20); IZM_RES/Ön Görüş Talebi ×1 (0.10); IZM_RES/Toplantı Tutanağı ×1 (0.10); ANK_RES/ÇED Olumlu Kararı ×1 (0.10); IZM_RES/Teknik Rapor ×1 (0.10); IZM_RES/Arazi Edinim Raporu ×1 (0.10); IZM_RES/ÇED Durum Yazısı ×1 (0.10); ANK_RES/Production Report ×1 (0.10); ANK_RES/Licence Amendment ×1 (0.10); ANK_RES/Performance Review ×1 (0.10) | 12 | ✅ | – |  |
| HO-NEG-02 | finans | net | 16 | ANK_RES/Facility Agreement ×7 (0.50); ANK_RES/Drawdown Notice ×2 (0.30); ANK_RES/Covenant Report ×3 (0.30); ANK_RES/Waiver Letter ×1 (0.30); ANK_RES/Account Pledge ×2 (0.30) | 5 | ⚠️ | 🔥 | belge: Hangi belgeyi kastediyorsunuz: Facility Agreement; Ankara RES Drawdown Notice — Tranche 1; Covenant Compliance Report Q2 2026? |
| HO-NEG-03 | enerji | net | 36 | — | 0 | ✅ | – |  |
| HO-NEG-04 | yonetim | net | 75 | CO/Shareholder Resolution ×1 (0.20); ANK_RES/Maintenance Report ×1 (0.10) | 2 | ✅ | – |  |
| HO-NEG-05 | enerji | net | 36 | IZM_RES/Bağlantı Görüşü Başvurusu ×1 (0.50); IZM_RES/ÇED Durum Yazısı ×3 (0.50); IZM_RES/Arazi Edinim Raporu ×2 (0.40); IZM_RES/Ön Görüş Talebi ×1 (0.30); ANK_RES/Production Report ×1 (0.30); IZM_RES/Teknik Rapor ×3 (0.20); IZM_RES/Önlisans ×1 (0.20); ANK_RES/Maintenance Plan ×1 (0.20); ANK_RES/Insurance Notice ×1 (0.20); ANK_RES/Üretim Lisansı ×1 (0.20) | 10 | ✅ | – |  |

