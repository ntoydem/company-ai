# Naci'den Tansu'ya — Kalan Eksik Değerler + PR Ricası, 3. tur — 10.10.2026

**Kimden:** Naci (ve geliştirme tarafı) · **Kime:** Tansu (ürün sahibi) · **Konu:** PF-1 (Proje Finans) partisinin kodla üretilen belgeleri tamamlandı (Karatepe + Kızılova + Yeşilova). Kaynak: `docs/plans/ADIM5_ASAMA_B_PLAN.md` §4.1 (T-10 listesi) + `docs/reports/ADIM5_ASAMA_C_REPORT.md`'nin "Verilmeyen/pending" notları.

Bunlar demo kütüphanesi için eksik değerler. Gerçek bir şirkete ait olmak zorunda değil, tutarlı olması yeterli. Bildiğin gerçekçi bir değer yaz; boş bırakırsan varsayımla ilerleriz ve raporda açıkça işaretleriz. Değerler birbiriyle tutarlı olsun (örn. kredi toplamı <= capex − özkaynak). **Bu değerler gelene kadar Yeşilova ve Kızılova'nın Facility Agreement ile Annex F belgeleri üretilmeyecek** (bunlar LLM prose, PF-1'in bu turda kapsam dışı bırakılan kısmı).

---

## T-11. Eksik değerler

| Kod | Proje | Eksik değer | Şu anki varsayım | Cevap |
|---|---|---|---|---|
| T-11.1 | Karatepe | Lisans alırken ilk onaylanan kapasite (MW) | **AI_ASSUMPTION**: 22 MW (yalnız mevcut DOC-ANK-DEV-002 kapasite-tadili belgesinin anlatısını korumak için seçildi, Tansu'dan gelmedi; güncel 24 MW USER_FACT) | |
| T-11.2 | Karatepe | Kredi sözleşmesi imza tarihi / financial close tarihi | **AI_ASSUMPTION**: imza 20.11.2021, financial close 25.11.2021 | |
| T-11.3 | Karatepe | Capex (toplam yatırım, **USD**) | **AI_ASSUMPTION**: 20.000.000 USD — total_debt+equity'den %70/30 varsayımıyla türetildi | |
| T-11.4 | Karatepe | Özkaynak/equity (**USD**) | **AI_ASSUMPTION**: 6.400.000 USD — aynı %70/30 varsayımı | |
| T-11.5 | Kızılova | İmzalı-kullanılmamış kredinin (2026-KZ) tam imza tarihi | **Tamamen pending** — ledger'da hiç tarih alanı yok, yalnızca "2026-KZ" kodundan 2026 yılı biliniyor | |
| T-11.6 | Boztepe | Toplam kredi tutarı (anapara) | **Pending** — yalnız aylık faiz tutarı (84.300 USD) ve iki tarih var | |
| T-11.7 | Boztepe | Faiz oranı (taban endeks + marj) | **Pending** — yalnız aylık TUTAR verildi, oran verilmedi | |
| T-11.8 | Boztepe | Tenor (vade, yıl) | **Pending** | |
| T-11.9 | Boztepe | DSCR covenant eşiği | **Pending** | |
| T-11.10 | Boztepe | DSRA bakiyesi | **Pending** | |
| T-11.11 | Yeşilova | Capex (toplam yatırım, USD) | **Pending** | |
| T-11.12 | Yeşilova | Özkaynak/equity (USD) | **Pending** | |

**Not — Kızılova EPC:** T-10'un orijinal sorusu Kızılova'nın kredisi VE EPC sözleşmesinin tam tutar/taraf/tarihini soruyordu; EPC tarafı (ABC İnşaat A.Ş., 10.000.000 USD KDV hariç, imza 15.09.2026) Aşama C4'te zaten cevaplandı — yalnızca T-11.5 (kredi imza tarihi) hâlâ eksik, EPC için tekrar sormuyoruz.

**Not — Kızılova Hakediş 1:** Bu listede yok — Hakediş 1 (SÖ-26-014) tutarları Enerji/EPC partisinin konusu (onaylı karar), Proje Finans'ın kapsamı dışında.

### Düşük öncelik

| Kod | Proje | Eksik değer | Şu anki varsayım | Cevap |
|---|---|---|---|---|
| T-11.13 | Yeşilova | Türbin adedi | Model verildi (Vestas V136), adet verilmedi | |
| T-11.14 | Yeşilova | DSCR covenant'ının tarihsel test sonucu (geçti/kaldı, hangi dönem) | Yalnız eşik (1,15x) verildi, test sonucu verilmedi | |
| T-11.15 | Karatepe | Grace süresi (ay) | **AI_ASSUMPTION**: 10 ay — imza (20.06.2022) ile ilk taksit (07.04.2023) arasındaki boşluktan türetildi | |

---

## PR ricası

**PR #15** (Anayasa v2.1 taslak) ve **PR #16** (Ek-F Karakter Tanımı) hâlâ açık (OPEN). İkisi de bizim tarafta onaylanmış/kullanılmaya başlanmış durumda — mümkünse merge edebilir misiniz?

## İK (İnsan Kaynakları) sorusu

ADIM5_PF_PARTISI_PLAN'ın parti sırası PF → Hukuk → Enerji → Mali İşler → İdari İşler → **İK**; İK'nın demo kütüphanesine girişi Adım 6'da ayrıca ele alınacak şekilde not edildi. Bu doğru mu, yoksa İK'nın bir kısmı Adım 5 kapsamına şimdiden girsin mi?

---

Hiçbir rakam bu dosyayla ledger'a yazılmadı — cevaplarınız gelince işlenecek.
