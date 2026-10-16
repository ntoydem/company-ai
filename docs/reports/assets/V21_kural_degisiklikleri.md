# V21 — 9 kuralın madde başına önce/sonra ve tek-başına etkisi

Yöntem: `scripts/rescore.py --ablation` — M1 (`results/m1_final_2026-10-16`, v2.0 71/99) ve S3r
(`results/s3_rescored`, v2.0 70/99) aynı ham cevaplarla, LLM çağrısı yok, eval postgres'i
(`company-ai-eval`, SELECT-only). v2.1 (hepsi açık): **M1 69/99, S3r 69/99**. Resmi v2.0 skorları
değişmedi (`results/m1_final_2026-10-16/`, `results/s3_rescored/` dokunulmadı); v2.1 ayrı çıktı
(`results/v21/m1/`, `results/v21/s3r/`).

## Madde başına tek-başına etki (ablasyon — her satır yalnız O kural kapalı, diğer 8'i açık)

| Kural | M1 delta | M1'de değişen | S3r delta | S3r'de değişen |
|---|---|---|---|---|
| R1 çelişen rakam | **−1** | ANK-FIN-013 | 0 | — |
| R2 F-8 düşürür | **−1** | ANK-FIN-011 | **−1** | GEN-DSC-001 |
| R3 atlama etiketi | 0 | — | 0 | — |
| R4 MIXED tamlık | 0 (doğru teşhis, puan değişmedi) | — | 0 (aynı) | — |
| R5 netleştirme konusu | 0 (ölçülemez, opt-in) | — | 0 | — |
| R6 liste kapsamı | 0 (ölçülemez, opt-in) | — | 0 | — |
| R7 G3 tüm projeler | 0 (doğru teşhis, puan değişmedi) | — | 0 (aynı) | — |
| R8 G1 MIXED/DATA | 0 (yeni yakalama yok, regresyon yok) | — | 0 | — |
| R9 ledger biçimlendirici | 0 (2 soru yeni doğrulandı, ikisi de doğru) | — | 0 | — |

**Toplam etki, hepsi birlikte:** M1 71→69 (−2: R1 + R2); S3r 70→69 (−1: R2). R4/R7'nin M1'deki
görünür satırları ("Değişen sorular" tablosunda) puanı değiştirmiyor — zaten başka sebeple
düşen bir soruya doğru teşhis ekliyorlar (ANK-MIX-001: kaynak eksik + T-1; GEN-DSC-008/-M:
discovery eksik + G3).

## Madde madde — ne değişti, hangi soru, hangi yön

1. **R1 (ANK-FIN-013 sınıfı, çelişen rakam):** Eski davranış — beklenen yüzde grupları
   (ör. marj ilk/şimdi) metinde bulununca `value_check=pass`, başka bir çelişen yüzde varsa
   bakılmıyordu. Yeni davranış — beklenen alanın kavram anahtar sözcüğüyle (`margin_pct` →
   "marj", `generate_excel.py:541` ile doğrulandı) aynı cümledeki HER yüzde kontrol edilir;
   kabul edilenler dışında biri varsa fail. **Etkilenen:** ANK-FIN-013 (M1, ✅→❌, −1) — Excel
   yarısının "marj %6,5" (Debt sayfası all-in oranı) cümlesi artık yakalanıyor; kontrolörün
   KY#1'i birebir. S3r'de aynı soru zaten başka sebeple düşüyordu (0 net etki, ama kural
   doğru çalışıyor — rescore_diff'te R1 etiketi yok çünkü `value_check` zaten fail'di, ama
   ablasyon M1'de −1 net gösteriyor). **Yön: ↓ (sıkılaştırıyor, kasıtlı).** Doğrulama: M1 ve
   S3r'de R1 yüzünden ANK-FIN-013 DIŞINDA yeni fail olan **0 soru** — dar (aynı cümle) sürüm
   yanlış pozitif üretmedi, genişletmeye gerek kalmadı.
2. **R2 (F-8 biçim hatası düşürsün):** Eski davranış — `format_check` hesaplanıyor, raporda
   gösteriliyor, `passed`'a girmiyordu. Yeni davranış — `format_check=fail` artık `passed=False`
   yapar. **Etkilenen:** ANK-FIN-011 (M1, ✅→❌, −1 — kontrolörün KY#2'si: "%3,25"/"%2,9"
   İngilizce yüzde biçimi), GEN-DSC-001 (S3r, ✅→❌, −1 — T1 raporunun kendi bulgusu:
   gruplanmamış "13600000"). **Yön: ↓ (sıkılaştırıyor, kasıtlı).**
3. **R3 (GEN-DSC-011-K atlama etiketi):** Eski davranış — `expected_answer is None` dalı
   `skip_reason="expect_no_answer"` döndürüyordu (gerçek A3 kuralıyla aynı etiket, soru
   `expect_no_answer=false` olsa da). Yeni davranış — `"no_literal_expected_answer"` (doğru
   etiket) + docstring'de tüm atlama koşulları numaralı. **Kök neden bulgusu** (etiket
   düzeltmesinin ötesinde): `ankara_res.yaml:143-151`'de `repayment_schedule[0] = {date:
   2023-04-07, principal: {value: 172700, USD}}` LİTERAL olarak var; soru setinin
   `expected_answer`'ı buna hiç işaret etmiyor. Kontrolörün gördüğü "480.700" toplamı
   anapara+faiz — faiz kısmı `debt_math.build_schedule` ile HESAPLANAN bir değer, ledger'da
   literal alan yok, bu puanlayıcı tasarımıyla asla doğrulanamaz. **Öneri (v14, uygulanmadı):**
   `expected_answer: ["ledger:ankara_res.project.finance.repayment_schedule[0].date",
   "ledger:ankara_res.project.finance.repayment_schedule[0].principal.value"]`. **Yön: etki
   yok (0/0)** — saf teşhis.
4. **R4 (T-1, MIXED tamlık):** Eski davranış — MIXED cevabın bir yarısı sessizce boş/atlanmış
   olsa da `passed` buna bakmıyordu. Yeni davranış — `required_sources` hem belge hem workbook
   adı taşıyorsa (ya da opt-in `parts` öyle diyorsa), cevap HER İKİ başlığı da göstermeli; hiç
   başlık yoksa (düz tek cümleye inmiş — ANK-MIX-001'in gerçek M1 cevabı) ya da bir başlık
   içi boşsa fail. **Etkilenen:** ANK-MIX-001 (M1+S3r, ❌→❌, net 0 — zaten kaynak eksikliğiyle
   düşüyordu, R4 doğru teşhisi ekliyor: "cevap iki ayrı bölüm göstermeden tek cümleye indi").
   **ANK-MIX-003 hâlâ yakalanamıyor** — `required_sources` tek kaynak (yalnız workbook), soru
   metninin kendisi ikili ("...neydi VE ...yazıyor mu?") ama bu mevcut alanlardan çıkarılamıyor.
   **Öneri (v14):** ANK-MIX-003'e `parts: ["document","excel"]` eklensin. **Yön: ↓ (doğru
   teşhis, net puan etkisi yok).**
5. **R5 (T-2, netleştirme konusu):** Eski davranış — her çıplak netleştirme sorusu geçiyordu
   (G2 cömertliği). Yeni davranış — yalnız opt-in `clarify_kind` set edilmişse kontrol edilir;
   **kalıcı tasarım kararı:** metin tabanlı bir sezgisel yöntem denenmedi, çünkü gerçek v13
   sorularına bakınca GEN-AMB-001/002/003/004 (meşru proje netleştirmesi) de soru metninde HİÇ
   proje adı taşımıyor — "proje adı yok → netleştirme yanlış" kuralı bunları da (yanlışlıkla)
   düşürürdü. **Etkilenen:** 0/99 (clarify_kind hiçbir soruda set değil). **Öneri (v14):**
   GEN-AMB-005'e `clarify_kind: "other"` eklensin (ambiguity toplantı/karar ekseninde, proje
   ekseninde değil). **Yön: etki yok (0/0)** — mekanizma hazır, veri eksik.
6. **R6 (liste kapsamı):** Eski davranış — liste beklentili sorularda (IZM-DEV-008) kapsam
   hiç ölçülmüyordu. Yeni davranış — opt-in `expected_items` sayacı (A6 deseniyle aynı,
   `passed`'ı etkilemiyor). **Etkilenen:** 0/99 ölçülebilir. **Öneri (v14):** IZM-DEV-008'e
   `expected_items` eklensin (mera tahsis değişikliği, İDK toplantısı, imar, kat'i proje —
   kontrolörün eksik bulduğu 4 öğe). **Yön: etki yok (0/0)** — mekanizma hazır, veri eksik.
7. **R7 (G3 tüm projeler):** Eski davranış — "başka projenin belgesi" yalnız Karatepe/Kızılova
   kodlarını tanıyordı (`_PROJECT_NAME_BY_CODE`, 2 proje); Yeşilova/Boztepe/Güneşalan/
   Akyar/Demirci'den bir belge önerilse hiç bayrak almazdı. Yeni davranış — 7 projenin hepsi
   (`_ALL_PROJECT_NAME_BY_CODE`); kapı aynı (yalnız adlı sorular). **Etkilenen:** GEN-DSC-008,
   GEN-DSC-008-M (M1, ❌→❌, net 0 — zaten discovery eksikliğiyle düşüyordu, şimdi G3 bayrağı
   da ekleniyor: "Bankaya Giden İşletme Bütçesi" başka projeden); ANK-MIX-001 (S3r, aynı
   desen, Boztepe/Yeşilova belgeleri). **Yön: ↓ (doğru teşhis, net puan etkisi yok).**
8. **R8 (G1 MIXED/DATA'ya genişler):** Eski davranış — G1 "uydurma sayı" denetimi yalnız
   DOCUMENT_QUERY'de çalışıyordu; MIXED'in belge yarısı ve DATA_QUERY hiç taranmıyordu. Yeni
   davranış — MIXED'in belge yarısı (gerçekten iki başlıklıysa) ve DATA_QUERY (çözülebilir bir
   `expected` değeri varsa) da taranır; DuckDB'nin kendi doğru değeri her zaman serbest.
   **Uygulama sırasında bulunup düzeltilen 2 tuzak** (ölçmeden önce): (a) düz tek cümleye
   inmiş bir MIXED cevapta ("Belgelere göre:" hiç yok) belge yarısını ayıramayız — taramak
   Excel/DuckDB rakamının kendisini "uydurma" sayardı (ANK-MIX-003, GEN-DSC-011-K'de ilk
   ölçümde tam da bu oldu); (b) çözülebilir `expected` değeri olmayan çıplak bir DATA_QUERY
   cevabında rakamın kendisi için çapa yok. İkisi de "taranamaz" sayılıp atlanıyor, "uydurma"
   sayılmıyor. **Etkilenen:** M1/S3r'de 0 yeni bayrak, 0 regresyon (ablasyonla doğrulandı).
   **Yön: etki yok (0/0)** — bu iki runda yakalanan ekstra bir uydurma rakam yok, ama
   mekanizma artık güvenli şekilde genişletilmiş durumda.
9. **R9 (ledger biçimlendirici):** Eski davranış — 13 "belge var ama değer doğrulanamadı"
   kaydının tamamı `skip` (her zaman geçer). Yeni davranış — iki yapısal fallback (para: ebeveyn
   dict'te `currency` kardeşi varsa; literal Türkçe metin: Türkçe harf içeren, kod-olmayan
   serbest metin, virgülle bağımsız yan tümcelere bölünür) önceden `None` dönen 2 alanı
   formatlıyor: ANK-FIN-015 (8.000.000 USD), ANK-OPS-002 (Türbin arızası + 11 gün duruş).
   **İkisi de M1 VE S3r'de hem yeni doğrulandı HEM geçti** — hiçbir soru yeni formatlanıp
   düşmedi. Diğer 11 kayıt ayrıntılı tablo: `V21_item9_ledger_formatter.md` (6'sı belge kimliği/
   MIXED-dict, tasarım gereği hiç gap değil; 2'si — ANK-FIN-010 "pass"/"fail", IZM-DEV-001
   "development" — hiçbir üretilen belgede Türkçe karşılığı olmadığı için bilerek
   doğrulanamıyor bırakıldı, alias UYDURULMADI). **Yön: ↑ (gevşetme değil, yalnız genişletme;
   0 yeni fail).**

## Kontrolör #42 uyuşması

**13/20 (%65) → 15/20 (%75)** (`V21_kontrolor_karsilastirma.md` / `results/v21/m1/
kontrolor_42_karsilastirma.md`). İki gerçek düzeltme (ANK-FIN-013 R1, ANK-FIN-011 R2) uyuşmayı
+2 artırdı. Kalan 5 ayrılık: ANK-ISO-002 (test beklentisi eskimiş, puanlayıcı değil), ANK-MIX-003
+ GEN-DSC-011-K + IZM-DEV-008 + GEN-AMB-005 (dördü de mekanizma hazır, v14 opt-in alan/veri
bekliyor — §3/4/5/6'da ayrı ayrı not edildi).
