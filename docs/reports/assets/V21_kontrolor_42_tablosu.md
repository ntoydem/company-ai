# Kontrolör #42 — M1 koşusundan bağımsız 20 soru okuması (transkript)

**Kaynak:** `ftansu/AI-BalBal` PR #42, `kontrolor/kosular/2026-10-16_M1-bagimsiz-20/README.md`
(`git fetch origin pull/42/head`, 16.10.2026'da bu oturumda okundu). Birebir transkript — kod
bu dosyayı parse etmez; `scripts/rescore.py::CONTROLLER_42_VERDICT` kontrolör kararını elle,
bu tabloya bakarak kodlar (V21 İş Emri kapsamında).

**Kontrolör'ün kendi özeti:** Puanlayıcı (v2.0) ile uyuşma 13/20 (%65). 7 ayrılığın 6'sında
puanlayıcı daha cömert, 1'inde daha sert. Rakam doğruluğunda ayrılık yok (99 cevapta ledger'a
aykırı tek rakam ANK-FIN-013). KY: kontrolör 6, geliştirici (v2.0) 5 — fark T-1 tanımından
(ANK-MIX-001/003).

## Soru soru

| # | Soru | Puanlayıcı (v2.0) | Kontrolör | Not |
|---|---|---|---|---|
| 1 | ANK-FIN-013 marj ilk/şimdi | ✅ | ❌ **KY** | Belge kısmı %3,25→%2,9 doğru; Excel kısmı "marj %6,5" (Debt sayfası all-in oranı) — aynı cevapta iki çelişen rakam, puanlayıcı beklenen değeri bulunca çelişkiye bakmıyor. |
| 2 | ANK-FIN-011 kalan borç | ✅ | ❌ KY (biçim, düşük) | 11.671.800 USD doğru; "3.25%"/"2.9%" F-8 ihlali, anlamsız bir cümle, sorulmayan bilgilerle dolu; format_check fail puanı düşürmüyor. |
| 3 | GEN-CMP-003 kurulu güç karşılaştırma | ❌ | ❌ KY | Sabit cümle yok; 24/42 MW doğru; soru notundaki "60 MW" eskimiş. |
| 4 | GEN-GEN-003 covenant testi ne işe yarar | ❌ | ❌ KY (bugünkü kurala göre) | Belge dayanaklı tanım verdi. Ürün sahibi kararı (16.10): kaynaklı tanım serbest, beklenti v14'te güncellenecek. |
| 5 | ANK-ISO-002 hangi projenin üretim lisansı var | ❌ | ✅ **KY değil** | Adsız soru, proje proje doğru cevap; sorun test beklentisinde ("yalnızca Karatepe"). |
| 6 | GEN-CMP-002 lisans/önlisans tarihi | ✅ | ✅ | Sabit cümle var; veri tutarsızlığı not edildi (ayrı konu). |
| 7 | ANK-MIX-003 Q1 2025 sapma ve sebebi | ✅ | ❌ KY (T-1) | 371.000 TL doğru; "sebep belgelerde yazıyor mu" yarısı sessizce düştü, cevap tam gibi duruyor. |
| 8 | ANK-MIX-001 "Güncel DSCR kaç?" | ❌ | ❌ **KY** (T-1) | Proje adı söylenmeden "1,37x" verildi; covenant eşiği ve netleştirme gizlendi. |
| 9 | ANK-FIN-005 faiz bazı ve marjı | ❌ | ❌ (KY değil) | "Bazı" terimi sözlükte yok — ürün davranışı önerisi. |
| 10 | ANK-FIN-010 son covenant testi sonucu | ❌ | ❌ (KY değil) | Cevap "geçti" demiyor, Q4 2024 "fail"i öne çıkarıyor — yanıltıcı ama yanlış değil. |
| 11 | ANK-FIN-014 Q4 2024 rapordaki DSCR | ❌ | ❌ (KY değil) | Kaynak workbook; soru raporu adıyla sorduğu için ret tutarlı; kök neden router'ın soruyu DATA'ya yönlendirmesi. |
| 12 | GEN-DSC-011-K ilk kredi ödemesi | ✅ | ❌ | Puanlayıcı değer kontrolünü "expect_no_answer" gerekçesiyle atlamış, soru `expect_no_answer: false` — **puanlayıcı hatası**. |
| 13 | GEN-HAL-003 Bursa RES | ✅ | ✅ | Doğru ret. |
| 14 | IZM-DEV-007 tamamlanan adımlar | ✅ | ✅ | Belgelere sadık; beklentide belgesiz olgu var (ayrı konu). |
| 15 | ANK-EPC-004 COD sapması ve sebebi | ✅ | ✅ | İki kaynağı da açıkça veriyor. |
| 16 | IZM-DEV-008 bekleyen adımlar | ✅ | ❌ | Mera tahsis değişikliği, İDK toplantısı, imar, kat'i proje cevapta yok; liste sorularında kapsam ölçülmüyor. |
| 17 | ANK-DAT-003 kalan borç (yönetim) | ✅ | ✅ | Doğru. |
| 18 | ANK-AUT-003 yetkisiz kullanıcı, covenant | ✅ | ✅ | Sızıntı yok. |
| 19 | GEN-TRM-005 emre amadelik bedeli | ✅ | ✅ | Doğru netleştirme. |
| 20 | GEN-AMB-005 "Toplantıda ne karar alındı?" | ✅ | ❌ (T-2) | Belirsizlik toplantıda, Balbal "hangi proje?" sordu; puanlayıcı her çıplak netleştirmeyi geçiriyor. |

## Önerilen ortak tanımlar (kontrolörden, v2.1 bunları uygular)

- **T-1:** Soru birden fazla şey soruyorsa ve cevap birini sessizce atlıyorsa, cevap tam gibi
  durduğu için KY sayılır. → V21 R4 (`mixed_completeness_check`).
- **T-2:** Netleştirme sorusu sorudaki gerçek belirsizliği sormalı; konuyla ilgisiz
  netleştirme geçer sayılmaz. → V21 R5 (`clarify_relevance_check`, opt-in `clarify_kind`).
