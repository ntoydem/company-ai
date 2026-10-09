# Projesiz soru + proje izolasyonu — teşhis ve seçenekler

**Tarih:** 09.10.2026 · **Durum:** plan, Naci onayı bekliyor; **kod değişikliği yok, kriter/G3 tanımı değiştirilmedi** · **Dayanak:** `docs/reports/ADIM2_EKF_REPORT.md` §8 (Adım 2 bu haliyle kapatıldı; `EK_F_MODE` canlıda kapalı, negatif kontrolde ANK-NEG-004 başarısız kayıtta kalır) · **Dal:** `feat/adim2-ekf` (`main`'e birleştirme yok) · **Tanı çağrıları:** 3/3 kullanıldı, bilgi amaçlı, resmi ölçümün yerine geçmez, kriterler değişmedi.

## 1. ANK-NEG-004 teşhisi — "Üretim lisansı ne zaman alındı?" (enerji)

### 1.1 Üç tarihsel koşu (canlı `audit_log`'dan, aynı soru metni)

| Zaman | Bayrak | Prompt | Cevap | Retrieval (parça kümesi) |
|---|---|---|---|---|
| 07.10.2026 19:31 | kapalı | `SYSTEM_PROMPT` | ✅ "Ankara RES üretim lisansı 15.06.2020 tarihinde onaylanmıştır … [K7]" | 80 parça, aynı sıralama |
| 08.10.2026 15:37 | kapalı | `SYSTEM_PROMPT` | ✅ "Üretim lisansı 15.06.2020 tarihinde onaylanmıştır [K7]." | **bayt-aynı** 80 parça |
| 09.10.2026 17:50 | `EK_F_MODE=true` | `SYSTEM_PROMPT_ASSIST` | ❌ "Bu konuda kesin bilgi bulamadım." + F-5 listesi (Ankara 6 belge + İzmir RES: ÇED Süreci Durum Yazısı) | **bayt-aynı** 80 parça |

`chunks_retrieved` üç koşuda da **birebir aynı** (aynı `document_id`/`page_number`/`rank` sırası) — retrieval'da hiçbir fark yok. Tek değişken: hangi sistem promptu (`SYSTEM_PROMPT` mi `SYSTEM_PROMPT_ASSIST` mi) kullanıldığı.

### 1.2 Üç tanı çağrısı (09.10.2026, bilgi amaçlı; resmi ölçüm sayılmaz)

| # | Bayrak | Koşu | Sonuç |
|---|---|---|---|
| 1 | `EK_F_MODE=true` | `run_eval --ids ANK-NEG-004 --repeat 2`, tekrar 1 | ❌ cevapsız, aynı liste |
| 2 | `EK_F_MODE=true` | tekrar 2 | ❌ cevapsız, aynı liste — **model kararlılığı 0/2** |
| 3 | **`ASSIST_MODE=true`, `EK_F_MODE=false`** (Ek-F'den önceki, eski yardım promptu) | `run_eval --ids ANK-NEG-004` ×1 | ❌ cevapsız: "Mevcut şirket kaynaklarında … yeterli bilgi bulamadım." + **aynı** çapraz-proje listesi (ÇED Süreci Durum Yazısı, İzmir RES yasak kaynak) |

### 1.3 Sonuç

- **Model kararlılığı 0/2** (tanı 1–2): tek koşu rastlantısı değil, **sistemli**.
- **Tanı 3 belirleyici:** Ek-F'den önceki, F-2 cümlesi olmayan, ADR-027'nin **orijinal** `SYSTEM_PROMPT_ASSIST`'i de aynı şekilde cevapsız kalıyor ve aynı çapraz-proje listesini üretiyor. Yani bu **Ek-F'ye özgü bir regresyon değil** — `ASSIST_MODE` (veya onu açan herhangi bir bayrak) açıldığında ADR-027'nin **önceden var olan** davranışı. F-2/F-3/F-5 metin katmanı sonucu **değiştirmedi**, yalnızca **açığa çıkardı**: `build_insufficient_assist`'in eski (ek_f olmayan) dalı da aynı terimle (`lisans`/`üretim`) vouch edilen parçalardan İzmir'in belgesini çekiyor.
- **Neden şimdiye kadar görülmedi:** 08.10'daki 4 negatif kontrol ölçümü (`BELIRSIZLIK_REPORT.md` §17) **bayrak kapalı** koşuldu ("4 yeni negatif kontrol ×1, bayrak KAPALI"). ANK-NEG-004, hiçbir assist-hesaplayan bayrakla (`ASSIST_MODE` ya da `EK_F_MODE`) daha önce **hiç ölçülmemiş**. Bu tur bunu ilk kez açığa çıkardı.
- **İki ayrı bulgu, iç içe:**
  1. **Birincil (model):** aynı bağlamda, flag açıkken model önceden verdiği doğru cevabı artık vermiyor. Tek değişken sistem promptu; hangi kural (7/8/11) sorumlu, ek çağrı harcamadan ayrıştırılamadı.
  2. **İkincil (liste, G3'ü tetikleyen):** model cevapsız kalınca F-4/F-5 "zayıf eşleşme → listele + sor" yoluna düşüyor; soru **hiçbir projeyi adlandırmadığı** için 09.10'daki proje-izolasyon düzeltmesi (ADR-030, `named_project_codes`) bu soruyu kapsamıyor — **tasarım gereği** ("adlandırılmamışsa aynen kalır", Naci kararı).
- **Eğer (1) olmasaydı** (model eskisi gibi doğrudan cevaplasaydı), hiçbir liste gösterilmeyecek, (2) hiç tetiklenmeyecekti. Yani bu ölçümde G3'ü **asıl** üreten (1); (2) önceden var olan ve bağımsız bir yapısal risk.

## 2. Çatışma tespiti — Ek-F F-3/F-4 ile eval G3'ü proje adsız sorularda

### 2.1 Alıntılar

**Anayasa Ü-3 (Ürün 1 / Tanıma), `anayasa/01-urun.md`:**
> "Çok projeli sohbet (Ürün 1'de): Kullanıcı tek bir Balbal AI sohbet penceresinde birden fazla proje hakkında soru sorabilir … Balbal AI her projeyle ilgili cevabı **o projenin kaynaklarıyla ayrı ayrı** verir." … "**Sınır:** Tanır, bulur, gösterir. Birleştirme (Ç-1) yapmaz: kaynaklar veya projeler arasında tablo, ortak liste, karşılaştırma üretmez."

Ü-3, **sorunun açıkça birden çok projeyi kapsadığı** durumu düzenler (karşılaştırma/birleştirme yasağı). **Projesiz, tek-cevaplı bir soruda "zayıf eşleşme" listesinin hangi projeleri içerebileceğine dair açık bir madde yok.**

**Ek-F F-3 (Cevap uzunluğu ve düzen), AI-BalBal PR #16 / `anayasa/ek-f.md`:**
> "Liste en fazla yedi maddedir … Birden fazla projeyle ilgili soruda her proje ayrı başlık altında cevaplanır."

**Ek-F F-4 (Netleştirme eşiği ve biçimi):**
> "Önce anlamaya çalışır … eşleşmenin kelime düzeyinde olmaması 'Veri Yok' gerekçesi değildir. Soru tek anlamlıysa netleştirici soru sormaz, cevaplar. Cevap, sorunun hangi proje, belge ya da döneme ait olduğuna göre değişiyorsa ve bu sohbetten anlaşılmıyorsa **tek bir** netleştirici soru sorar … **Eşleşme zayıfsa bulduklarını bağlantılarıyla listeler ve tek soruyla teyit eder.**"

F-4, zayıf eşleşmede **bulunanı listelemeyi** açıkça istiyor; listenin **proje sınırına göre süzülmesi gerektiğini söylemiyor** — ne emrediyor ne yasaklıyor.

**Eval G3 (bizim kod, `scripts/eval_lib.py`, Anayasa'nın parçası değil):**
```python
code = item.get("project_code")
if (question.expected_project is not None
    and code in _PROJECT_NAME_BY_CODE
    and _PROJECT_NAME_BY_CODE[code] != question.expected_project):
    reasons.append(f"G3: başka projenin belgesi önerildi: {item.get('title')}")
...
for name in question.forbidden_sources:
    if _source_satisfied(name, suggested, catalog):
        reasons.append(f"G3: yasak kaynak assist'te: {name}")
```
G3, **soru metnine bakmaz** — bizim test metadata'mızdaki `expected_project`/`forbidden_sources` alanlarına bakar (ANK-NEG-004'te biz `forbidden_sources: ["İzmir RES"]` yazmışız). Bu, sistemin soru metninden **bilemeyeceği** bir ölçüttür: üretimde sistem "bu sorunun cevabı kesin olarak Ankara'ya ait olmalı" bilgisine sahip değildir, bunu biz test yazarken ekliyoruz.

### 2.2 Durum tablosu

| Durum | Ü-3 | F-3 | F-4 | G3 (bizim eval) |
|---|---|---|---|---|
| Soru **açıkça** tek proje adlandırıyor (GEN-HAL-001 şekli) | konu dışı (tek proje, karşılaştırma yok) | gruplu liste, tek başlık olur | eşleşme zayıfsa listele + sor | **09.10 düzeltmesiyle** diğer proje aday kümeden çıkıyor → uyumlu |
| Soru **açıkça** birden çok proje adlandırıyor | **birleştirme yok, her proje ayrı** | her proje ayrı başlık | — | G3'te `expected_project=None` ise proje kontrolü **devreye girmez** (kod: `if question.expected_project is not None`) |
| Soru **hiçbir** projeyi adlandırmıyor, ama **bir** projeye ait olması bekleniyor (ANK-NEG-004) | **sessiz** — bu durumu düzenlemiyor | liste kuralı (≤ 7) geçerli, proje ayrımı şart değil | **zayıf eşleşmede listele + sor** → İKİ projenin eşleşmesi de "bulunan" sayılır | `expected_project` set edilmişse **her iki projeyi de** yasak sayar → F-4'ün izin verdiği davranışı **ihlal** sayar |
| Soru hiçbir projeyi adlandırmıyor ve **gerçekten** hangi projeye ait olduğu belirsiz (ör. "ÇED raporu nerede?", DSC-007) | sessiz | gruplu liste | listele + sor — **tam olarak budur** | `expected_project=None` (ya da belirsiz) ise proje kontrolü devreye girmez → **çakışma yok** |

**Çakışmanın tam yeri:** F-4'ün sanctioned ettiği "zayıf eşleşmede bulduğunu listele" davranışı, eval'in **soru-yazarının bildiği ama sistemin bilemeyeceği** `expected_project` ölçütüyle karşılaştığında — yalnız **3. satırdaki** durumda (proje adsız + tek-proje-beklenen) çatışıyor. 1., 2. ve 4. satırlarda çakışma yok.

### 2.3 Kimin kararı

- **F-4'ün metni** (zayıf eşleşmede listele) → Ek-F Karakter Tanımı, Ürün Yetkilisi (Tansu) yazdı, iki Proje Yetkilisi onayladı (ADT-2, PR #16) — **değiştirilemez** bizim tarafımızdan; yalnız Anayasa Değişiklik Talebi (S-5) ile.
- **G3'ün `expected_project` ölçütü** → bizim `scripts/eval_lib.py` kodumuz, Anayasa'nın parçası değil; biz değiştirebiliriz **ama** "G3'ü yorumlayarak değiştirme" (Naci kararı, bu plan isteğinde) — yani bu plan **önerir**, uygulamaz.
- **T-1 (Tansu'ya sorulan, AI-BalBal PR #17, cevap bekleniyor):** "Proje adı geçmeyen soruda gruplu liste + 'hangi proje?' doğru mu?" — T-1'in cevabı burayı da etkiler: T-1 "evet, projesiz sorularda da gruplu liste doğru" derse, F-4'ün bu yorumu teyit edilir ve sorun tamamen G3'ün ölçütünde kalır (§2.1). T-1 "hayır, projesiz soruda tek proje tahmin edilip gösterilmeli" derse, ürün davranışının kendisi değişir (bu plan §3 Seçenek B'ye yaklaşır).

## 3. Seçenekler (kod yok, değerlendirme)

### Seçenek A — G3'ün proje ölçütünü soru metnine bağla
G3'teki proje kontrolü, `expected_project` test metadata'sı yerine (ya da onunla birlikte) **soru metninde adlandırılan proje** (`named_project_codes`, zaten Ek-F'de var) ile çalışsın: yalnız soru açıkça bir proje adlandırıyorsa diğer proje "yasak" sayılsın.
- **Ne kapatır:** ANK-NEG-004 sınıfını (projesiz + tek-proje-beklenen) artık G3 ihlali üretmez, çünkü kontrol hiç devreye girmez.
- **Risk:** G3'ün **ölçtüğü şeyi** değiştirir — bugün "sistem gerçekten hangi projeye ait olduğunu biliyor mu" diye soran bir negatif kontrol, "sistem bunu söylemek zorunda mı" sorusuna döner. ANK-NEG-004'ün **asıl amacı** (projesiz sorularda proje karışmasın) sessizce gevşer; bu bir test-metodolojisi kararı, "G3'ü yorumlayarak değiştirme" talimatına göre **şimdi uygulanmaz**, yalnız önerilir.
- **Kod değişikliği:** `eval_lib.py` tek koşul; küçük (S). **Birleştirilebilirlik:** Adım 4 ile ilgisi yok (eval tarafı, ürün tarafı değil).

### Seçenek B — Ürün davranışını genişlet: projesiz sorularda da örtük proje tahmini
Soru metni proje adlandırmasa da, aday kümenin **büyük çoğunluğu** (ör. ≥ %80) bir projeye aitse, F-3/F-5 listesi **o projeye** daraltılsın; azınlıktaki diğer proje eşleşmeleri gösterilmesin (ya da ayrı, daha belirgin bir "başka projede de olabilir" notuna düşsün). ANK-NEG-004'te 6 Ankara belgesine karşı 2 İzmir belgesi (kota sonrası 1 görünür) — çoğunluk kuralı Ankara'yı seçerdi.
- **Ne kapatır:** ANK-NEG-004 sınıfını, **G3'ün tanımına dokunmadan**, ürün davranışını iyileştirerek kapatır.
- **Risk:** "çoğunluk" kuralı yeni bir eşik/parametre getirir (ne kadarı çoğunluk?); DSC-007 gibi **gerçekten** iki projeye eşit yayılan sorularda yanlış daraltma riski (İzmir 4 + Ankara 3 — çoğunluk olmasa da birine daraltılırsa bir proje haksız yere kaybolur). Eşik hatalı seçilirse "gerçek belirsizlik" sorularında da proje gizlenebilir — bu da bir G3/F-4 çakışması (başka türlü) üretir.
- **Birleştirilebilirlik:** **Yüksek.** `URUN1_KARARLAR_VE_SIRA.md` §4'teki Adım 4 ("gerçek belirsizlik tespiti — proje ekseni") zaten "top-N parça içinde ikinci projenin payı" ölçütünü öneriyor — bu tam olarak aynı mekanizma. Seçenek B, Adım 4'ün **kodla çözümünün bir parçası olmalı**, ayrı bir yama değil: Adım 4 zaten "ikinci grubun payı düşükse proje ekseninde netleştirme yok, cevap/liste tek projeye daralır" türünde bir kural tasarlıyor. Burada ayrı yapmak kod tekrarı ve iki farklı eşik demek olurdu.

### Seçenek C — Kök nedene (model kararı) odaklan, listeyi şimdilik değiştirme
§1.3'teki birincil bulgu — assist-promptu açıkken model önceden cevapladığı bir soruyu artık cevaplamıyor — ADR-027'nin **genel** davranışı (Ek-F'ye özgü değil); ayrı, daha kapsamlı bir tur gerektirir: `SYSTEM_PROMPT_ASSIST`'in hangi kuralı (7/8/11) modelin eşiğini kaydırıyor, kaç soruda tekrarlanıyor (şimdiki 2 tanı çağrısı tek soru içindi).
- **Ne kapatır:** düzeltilirse ANK-NEG-004 muhtemelen eskisi gibi doğrudan cevaplanır, liste hiç tetiklenmez — **kök neden çözülür**, F-3/F-4/G3 çatışması bu örnekte **ortaya çıkmaz**.
- **Risk:** büyük kapsam — tüm assist-hesaplayan yol (`ASSIST_MODE` + `EK_F_MODE`) etkilenir; Naci'nin "tek prompt revizyon hakkı" kuralına göre yeni bir round, yeniden R1 + discovery + negatif ölçümü gerekir (≥ 31 çağrı); Ek-F'nin (Adım 2) kapsamını aşar, ayrı bir plan/round olmalı.
- **Birleştirilebilirlik:** Adım 4 ile değil; Adım 2'nin kendisiyle de değil — **ayrı, cross-cutting bir araştırma** (ADR-027'nin kendisini kapsar).

### Karşılaştırma

| | Kapsadığı | G3 tanımına dokunur mu | Adım 4 ile birleşir mi | Büyüklük |
|---|---|---|---|---|
| A | yalnız bu sınıf (eval) | **evet** (gevşetir) | hayır | S |
| B | bu sınıf + benzer "çoğunluk belirgin" durumlar (ürün) | hayır | **evet, aynı mekanizma** | Adım 4'ün parçası olarak M |
| C | kök neden (model), geniş etki | hayır | hayır, ayrı round | L |

## 4. SORU (Naci)

1. **Öncelik:** A, B, C'den biri şimdi mi başlasın, yoksa Adım 4'e kadar **hiçbiri** beklesin mi (ANK-NEG-004 "bilinen kısıtlama" olarak kayıtlı kalır)? Önerim: **B, Adım 4'ün içine** — ayrı yama açmayalım, tek mekanizma iki sorunu (proje ekseni gerçek belirsizlik + bu sınıf) birden çözsün.
2. **B seçilirse:** çoğunluk eşiği Adım 4'ün kendi "ikinci grubun payı" ölçütüyle **birebir aynı parametre** mi olsun (tek eşik, tek yer), yoksa F-3 listesi için ayrı bir eşik mi? Önerim: aynı parametre — iki yerde farklı eşik tutmak kafa karıştırır ve iki kez ayarlanması gerekir.
3. **A (G3 tanımı):** bu bir eval-metodolojisi kararı olarak **bizim** karar verebileceğimiz bir şey mi, yoksa Tansu'ya T-1 ile birlikte mi sorulmalı (T-1'in cevabı zaten bunu örtük olarak belirliyor)? Önerim: T-1 cevabını bekleyelim; ayrıca sormaya gerek yok.
4. **C (kök neden):** şimdi mi (ayrı round, ≥ 31 ek çağrı) yoksa Ek-F bayrağı canlıda **varsayılan açılmadan önce** (plan §3.2 adım 3, kör test turu 1 sonrası) mı araştırılsın? Önerim: o zaman — bayrak zaten o ana kadar kapalı kalacak, aceleye gerek yok; ama kör test turu 1 öncesi **zorunlu** olsun (aksi halde canlıda aynı regresyon riskiyle açılır).
5. **ANK-NEG-004'ün kaydı:** resmi negatif kontrol setinde "başarısız" olarak mı kalsın (öneri), yoksa "flag-dependent / bilinen kısıtlama" diye ayrı bir alt not mu eklensin (`questions.json`'da yeni bir alan değil, yalnızca rapor notu)? Önerim: öneri — set ve kriter değişmez, yalnızca bu plan rapora bağlanır.
