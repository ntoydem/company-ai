# T1-B5 — Proje adı tanıma / olmayan proje reddi: LLM'siz test vektörü

Alan: `projects` tablosunda ad/alias alanı **yok** — yalnız `name`, `code`, `stage`, `is_active`. Eşleme mantığı: `assist.named_project_codes` (adın ≥3 harfli, yalnız o projeye özgü kelimeleri; **alt dize** eşleşmesi; `is_active` süzgeci yok) ve `project_narrowing.unknown_project_names` (regex `[Büyük harf]\w* (RES|GES)`; kelime `projects` ad/kod kelimelerinde yoksa «olmayan proje»). Canlı `projects` tablosuna karşı (SELECT), 45 satır.

**Sonuç: 36/45 beklendiği gibi; 9 sapma.**

| # | Soru | Beklenen (adlı) | Beklenen (olmayan) | Gerçek (adlı) | Gerçek (olmayan) | Sonuç |
|---|---|---|---|---|---|---|
| 1 | Karatepe RES'in kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 2 | Karatepe RES kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 3 | Karatepe A.Ş.'nin kurulu gücü nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 4 | KARATEPE RES kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 5 | KARATEPE res kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 6 | karatepe kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 7 | Karatepe'nin kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 8 | Karatepe GES kapasitesi nedir? | ANK_RES | — | AKY_GES,ANK_RES | — | ❌ |
| 9 | Karatepe Res. kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 10 | Karatepe  RES  kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 11 | Karatepe-RES kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 12 | Karatepe RES'in, kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 13 | Kızılova RES'in COD tarihi nedir? | IZM_RES | — | IZM_RES | — | ✅ |
| 14 | Kizilova RES'in COD tarihi nedir? | IZM_RES | — | — | Kizilova RES | ❌ |
| 15 | KIZILOVA RES COD tarihi nedir? | IZM_RES | — | IZM_RES | — | ✅ |
| 16 | kızılova COD tarihi nedir? | IZM_RES | — | IZM_RES | — | ✅ |
| 17 | Kızılova GES COD tarihi nedir? | IZM_RES | — | AKY_GES,IZM_RES | — | ❌ |
| 18 | Yeşilova RES'in kredi bakiyesi nedir? | YSV_RES | — | YSV_RES | — | ✅ |
| 19 | Yesilova RES'in kredi bakiyesi nedir? | YSV_RES | — | — | Yesilova RES | ❌ |
| 20 | YEŞİLOVA RES kredi bakiyesi nedir? | YSV_RES | — | YSV_RES | — | ✅ |
| 21 | yeşilova kredi bakiyesi nedir? | YSV_RES | — | YSV_RES | — | ✅ |
| 22 | Boztepe RES'in DSRA bakiyesi nedir? | BOZ_RES | — | BOZ_RES | — | ✅ |
| 23 | boztepe DSRA bakiyesi nedir? | BOZ_RES | — | BOZ_RES | — | ✅ |
| 24 | Boztepe GES DSRA bakiyesi nedir? | BOZ_RES | — | AKY_GES,BOZ_RES | — | ❌ |
| 25 | Akyar GES kamulaştırma notu nerede? | AKY_GES | — | AKY_GES | — | ✅ |
| 26 | Demirci RES TEA itirazı nerede? | DMR_RES | — | DMR_RES | — | ✅ |
| 27 | Güneşalan GES'in belgeleri var mı? | — | — | AKY_GES | Güneşalan GES | ❌ |
| 28 | Bursa RES'in kapasitesi nedir? | — | Bursa RES | — | Bursa RES | ✅ |
| 29 | Bursa GES'in kapasitesi nedir? | — | Bursa GES | AKY_GES | Bursa GES | ❌ |
| 30 | bursa RES'in kapasitesi nedir? | — | bursa RES | — | — | ❌ |
| 31 | BURSA RES kapasitesi nedir? | — | BURSA RES | — | BURSA RES | ✅ |
| 32 | Bursa Res kapasitesi nedir? | — | Bursa Res | — | — | ❌ |
| 33 | Bursa'nın kapasitesi nedir? | — | — | — | — | ✅ |
| 34 | Karatepe RES ile Bursa RES'in kapasitesi nedir? | ANK_RES | Bursa RES | ANK_RES | Bursa RES | ✅ |
| 35 | Karatepe RES ile Kızılova RES'in kapasitesi nedir? | ANK_RES,IZM_RES | — | ANK_RES,IZM_RES | — | ✅ |
| 36 | Hangi RES projesinde ÇED tamamlandı? | — | — | — | — | ✅ |
| 37 | Bu RES'in kapasitesi nedir? | — | — | — | — | ✅ |
| 38 | Tüm RES projelerinin kapasitesi nedir? | — | — | — | — | ✅ |
| 39 | Test Project belgeleri nerede? | TEST_PRJ | — | TEST_PRJ | — | ✅ |
| 40 | Ankara RES'in kapasitesi nedir? | — | Ankara RES | — | Ankara RES | ✅ |
| 41 | İzmir RES'in kapasitesi nedir? | — | İzmir RES | — | İzmir RES | ✅ |
| 42 | Kara tepe RES kapasitesi nedir? | — | — | — | — | ✅ |
| 43 | Karatepe Rüzgar Enerji Santrali'nin kapasitesi nedir? | ANK_RES | — | ANK_RES | — | ✅ |
| 44 | ANK_RES kapasitesi nedir? | — | — | — | — | ✅ |
| 45 | Karatepe RES Enerji Üretim A.Ş. unvanı nedir? | ANK_RES | — | ANK_RES | — | ✅ |

## Sapmalar (düzeltme yapılmadı — öneri)

| Sapma | Satırlar | Sebep (kod) | Etki | Öneri |
|---|---|---|---|---|
| «X GES» her zaman Akyar GES'i de adlandırıyor | 8, 17, 24, 27, 29 | `named_project_codes`: «ges» kelimesi yalnız bir proje adında (Akyar GES) geçtiği için «özgü» sayılıyor; «res» 5 projede geçtiği için düşüyor | «Karatepe GES» → iki proje adlı → eksen kararı `none`, daraltma Karatepe ∪ Akyar; «Güneşalan GES» → hem olmayan proje hem Akyar adlı (olmayan proje önce geldiği için ret doğru çıkıyor) | RES/GES/SPP gibi ekleri sabit son-ek listesi olarak sayımdan düş (bir projede geçse bile) |
| ASCII yazım yanlış «proje yok» reddi | 14, 19 | `unknown_project_names`: «kizilova» ≠ «kızılova», «yesilova» ≠ «yeşilova» | Kullanıcı ı/ş yazmazsa «Bu adda bir proje kayıtlı değil» — yanlış ret | ASCII-katlama (ı→i, ş→s, ğ→g, ü→u, ö→o, ç→c) ile karşılaştır ya da `projects.aliases` alanı |
| Küçük harfli / karışık yazım olmayan proje yakalanmıyor | 30, 32 | `_PROJECT_MENTION` büyük harfle başlayan ad + büyük harf `RES|GES` istiyor | «bursa RES», «Bursa Res» → ret yok → router + Adım 4 `dominant` tahmini (GEN-HAL-003 sınıfı geri gelir) | Ek eşleşmesini büyük/küçük harf duyarsız yap; ad kelimesini `projects` ile karşılaştır, baş harfe güvenme |
| Alt dize eşleşmesi: «test» ⊂ «testi» | — (canlı 99 soru ölçümünde) | `named_project_codes`: `w in lowered_question` alt dize; canlı `projects`'te `TEST_PRJ / Test Project` satırı var (23.09.2026, eval DB'de yok) | Canlıda ANK-FIN-010, ANK-AUT-003, ANK-EPC-005 (`covenant testi`, `performans testi`) → {ANK_RES, TEST_PRJ} → eksen `none`; GEN-GEN-003 → yalnız TEST_PRJ → aday küme 10 grup belgesine iniyor (eval'da `dominant`, 80 parça) | Kelime sınırı eşleşmesi + `is_active=false` projeleri sayma; `TEST_PRJ` satırı için Tansu/Naci kararı (silme veya pasif) |

Doğru çalışanlar: büyük/küçük harf (KARATEPE, karatepe), kesme/virgül/çift boşluk/tire, «Res.» yazımı, «A.Ş.» ve «Rüzgar Enerji Santrali» uzun adı (kelime eşleşmesi sayesinde), iki proje birlikte, determiner'lı «Hangi/Bu/Tüm RES», «Ankara RES»/«İzmir RES» eski adları → olmayan proje (tablo tek kaynak), «Bursa RES» (3 yazım), «Kara tepe» → ne adlı ne olmayan (router'a düşer).
