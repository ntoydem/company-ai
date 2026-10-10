# Naci'den Tansu'ya — Kalan Eksik Değerler + PR Ricası, 3. tur — 10.10.2026

**Kimden:** Naci (ve geliştirme tarafı) · **Kime:** Tansu (ürün sahibi) · **Konu:** PF-1 (Proje Finans) partisi kodla üretilen belgeleri tamamlandı (Karatepe + Kızılova + Yeşilova). Bu turda **yeni bir tasarım sorusu yok** — yalnızca ledger'da hâlâ `pending`/varsayım olarak duran, Tansu'dan gelmesi gereken rakamlar; her satıra gerçek değer yazmanız ya da "bilmiyorum/öncelik değil" demeniz yeterli.

**Not (düzeltme, bilgi için):** Önceki round'da Karatepe'nin kredi alanlarını (capex/equity/total_debt/local_debt/eca_debt/outstanding_debt_as_of_demo_today) yanlışlıkla EUR'a çevirmiştik — M2 kararı ("loan amounts are EUR by decision") Adım 5'ten önceki eski rakamlar içindi; sizin NACI_CEVAP §3.1-3.2 ile verdiğiniz yeni rakamlar USD ve eskilerin yerine geçti. Bu turda **USD'ye geri alındı**, aşağıdaki Karatepe satırı da USD üzerinden soruluyor.

---

## T-11. Eksik değerler (SPV bazında)

Her satırdaki rakam şu an ledger'da **yok** (icat edilmedi, `pending`/varsayım olarak işaretli). Cevap sütununa gerçek değeri yazmanız yeterli; bilmiyorsanız "bilmiyorum" veya "öncelik değil, beklesin" deyin.

### T-11.1 — Boztepe RES (2024-BZ, Garanti BBVA USD)
Şu an yalnızca **aylık faiz tutarı** (84.300 USD) ve iki tarih (son ödenen 01.10.2026, sıradaki 02.11.2026) var. PF-2 bu veriler gelene kadar üretilemiyor.

| # | Alan | Mevcut durum | Cevap |
|---|---|---|---|
| T-11.1.a | Toplam kredi tutarı (anapara) | pending | |
| T-11.1.b | Faiz oranı (taban endeks + marj, ör. "Term SOFR 6M + %X") | pending — yalnız aylık tutar (84.300 USD) var | |
| T-11.1.c | Tenor (vade, yıl) | pending | |
| T-11.1.d | DSCR covenant eşiği | pending | |
| T-11.1.e | DSRA bakiyesi | pending | |

### T-11.2 — Yeşilova RES (2023-YS, Commerzbank AG/LMN Bank)
| # | Alan | Mevcut durum | Cevap |
|---|---|---|---|
| T-11.2.a | Türbin adedi | Model verildi (Vestas V136), adet verilmedi | |
| T-11.2.b | DSCR covenant'ının tarihsel test sonucu (geçti/kaldı, hangi dönem) | Yalnız eşik (1,15x) verildi, test sonucu verilmedi | |

### T-11.3 — Karatepe RES (2022-KT, Garanti BBVA/PQR Bank — **USD**)
Bu iki alan Tansu tarafından hiç verilmedi; şu anki ledger değerleri bizim **türetmemiz** (varsayım), onay/düzeltme bekliyor.

| # | Alan | Mevcut durum (varsayım) | Cevap |
|---|---|---|---|
| T-11.3.a | Capex (toplam yatırım, USD) | 20.000.000 USD — total_debt + equity'den %70/%30 varsayımıyla türetildi, Tansu'nun verdiği bir rakam değil | |
| T-11.3.b | Özkaynak/equity (USD) | 6.400.000 USD — aynı %70/%30 varsayımı | |
| T-11.3.c | Grace süresi (ay) | 10 ay — imza (20.06.2022) ile ilk taksit (07.04.2023) arasındaki boşluktan türetildi, doğrudan verilmedi | |

### T-11.4 — Kızılova RES (S-26-001, ABC İnşaat A.Ş.)
| # | Alan | Mevcut durum | Cevap |
|---|---|---|---|
| T-11.4.a | Hakediş 1 (SÖ-26-014, Eylül 2026 mühendislik/tasarım) tutarları | "Canvas'taki gibi" deniyor ama depoya aktarılmadı; ADIM5_PF_PARTISI_PLAN §8 SORU 1'de de flaglanmıştı — Enerji/EPC partisine mi bırakılsın yoksa şimdi mi verilsin? | |

---

## PR ricası

**PR #15** (Anayasa v2.1 taslak) ve **PR #16** (Ek-F Karakter Tanımı) hâlâ açık (OPEN). İkisi de bizim tarafta onaylanmış/kullanılmaya başlanmış durumda (Ek-F davranışı zaten kod tarafında ilk adım oldu) — mümkünse bu PR'ları **merge** edebilir misiniz? Bekliyor olmaları, bu dosyaların "taslak" statüsünde görünmesine neden oluyor.

## İK (İnsan Kaynakları) sorusu

ADIM5_PF_PARTISI_PLAN'ın parti sırası PF → Hukuk → Enerji → Mali İşler → İdari İşler → **İK**; İK'nın demo kütüphanesine girişi Adım 6'da ayrıca ele alınacak şekilde not edildi (toplam ~380 belge hedefi İK **hariç**). Bu doğru mu, yoksa İK'nın bir kısmı (ör. bordro şablonu, iş sözleşmesi örneği, SGK bildirgesi) Adım 5 kapsamına şimdiden girsin mi?

---

Hiçbir rakam bu dosyayla ledger'a yazılmadı — cevaplarınız gelince işlenecek.
