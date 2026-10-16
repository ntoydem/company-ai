# İş Emri 2026-10-16P3 — Madde 3: ❗ Çelişkili veri davranışı: PLAN

**Tarih:** 16.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `bdbe0e1`) · **Ürün 1** · **Ç-15/8 (cevap promptu + davranış kuralı) → T-9: kod öncesi plan, onay bekleniyor**

**Dayanak** (`ftansu/AI-BalBal` ana dal, `gh api` ile salt okundu):
- `docs/yazismalar/2026-10-16_naciye-acik-kararlar.md` Madde 3 (ve Madde 1–2'nin bağlamı)
- `anayasa/00-cekirdek.md`: Ç-6 ("çelişkili veriyi gizleyemez"), Ç-7 + 7.1 (durum tablosu, zorunlu sıra), Ç-15/8
- `anayasa/01-urun.md` (Ek-F'nin düzenleyemeyeceği şeyler: Ç-7 etiketleri), `anayasa/02-teknik.md` (T-9 + ADT-4)
- `anayasa/ek-f.md` F-1 ("emoji ve ünlem kullanmaz"), F-6 (Çelişkili Veri kalıbı); `ek-d.md` S-10 adım 5
- company-ai: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §5.3 (`data_conflict` ilk tasarımı), `docs/plans/EKF_V2_PLAN.md` (d) (Tansu'nun T-5 dört durumu), `docs/plans/ADIM5_PF_PARTISI_PLAN.md` §3 (kasıtlı çelişki grupları)

**Durum:** Yalnız plan. Kod, prompt, ayar, şema, puanlayıcı, soru seti ve canlı servis değişmedi. Ölçüm yalnız `results/v22/{m1,n1}/results.json` (scorer v2.2, LLM'siz yeniden puanlama) ve ledger'dan yapıldı. Yeni LLM çağrısı yapılmadı.

---

## 1. Tansu'nun tarifi (Madde 3, tam)

> **Karar (16.10):** İki **güncel** kaynak aynı olgu için farklı değer veriyorsa:
> - Cevapta **"❗ Çelişkili veri"** uyarısı ünlem işaretiyle görünür.
> - İki değer de **kaynağıyla** verilir.
> - Balbal birini seçmez, birini "doğru" diye sunmaz.
>
> Sürüm farkı çelişki değildir (10.10 kararı aynen): güncel + "tarihsel" eski. Yalnız iki güncel kaynak farklıysa çelişki.
>
> V22 listesine yalnız puanlayıcı tarafı girmişti; bu madde **Balbal'ın davranışıdır** ve kapıdan önce kodda olmalı. Kapı ölçümünde bu davranış aranacak. Prompt değişikliği gerekiyorsa Ç-15/8 gereği önce kısa plan.

Bağlayıcı üst metinler:
- **Ç-7:** Balbal bir kaynağı sessizce seçmez, diğerini gizlemez, ortalama almaz, tahminle tek doğru üretmez. Çelişen kaynakları ve farkı gösterir.
- **Ç-7.1 / S-10:** Çelişkili Veri bir cevap başlangıcıdır. Önce durum adıyla bildirilir, sonra çelişen kaynaklar ve fark gösterilir, cevap bir soru/seçenekle biter.
- **Ek-F F-6 kalıbı:** "Kaynaklar farklı söylüyor: … (belge, sürüm/tarih) ve … (belge, sürüm/tarih). Fark: … Hangisinin geçerli olduğunu teyit edebilir misiniz?" Fark sayıyla ve kaynakla söylenir.
- **Ek-F F-1** modele ünlem/emoji yasaklar. Bu yüzden ❗ **modelden değil koddan** gelmelidir (§3).

### 1.1 Çelişki sayılan / sayılmayan durumlar

| Durum | Tansu'ya göre | Dayanak |
|---|---|---|
| Aynı olgu, iki ayrı belge ailesi, ikisi de güncel, değer farklı | **❗ çelişki** | Madde 3, T-5 durum 1 |
| Aynı belge zincirinde eski ↔ güncel (tadil, sürüm) | Çelişki değil: güncel + "tarihsel" | Madde 3, 10.10 kararı, ADR-012 |
| Superseded belgedeki değer, tadil o maddeyi değiştirmemişse | Değer hâlâ güncel (kural 5). Başka bir aileyle farklıysa çelişkiye girer | kural 5 + Madde 3 (yorumum, **S-1**) |
| Farklı projelerin değerleri | Çelişki değil. Netleştirme (kural 12) ya da proje proje ayrı değer (kural 10, Ü-3) | Ü-3, Madde 1–2 |
| Aynı olgunun farklı dönem/tarihteki ölçümü (Q1 ↔ Q2 raporu) | Çelişki değil: zamansal fark | TEMPORAL TRUTH (yorumum) |
| Mükerrer kayıt | Ayrı durum (T-5 durum 3). Bu pakette yok | EKF_V2_PLAN (d) |
| Eksik belge | F-5 "Veri Yok" | T-5 durum 4 |
| Kullanıcının göremediği bir belgeyle fark | **Asla** söylenmez | Değişmez kural 1, Ç-6 |
| Excel ↔ belge farkı (MIXED) | Tarifte yok | **S-2** |

**Belirsiz kalanlar:** (1) "güncel kaynak" tanımı, kural 5'in "tadil değiştirmediyse eski halkadaki değer hâlâ geçerli" ilkesiyle nasıl birleşir? (**S-1**) (2) Excel ↔ belge farkı (**S-2**). (3) Belge künyesi (metadata tarihi) ile başka belgenin metni arasındaki fark (**S-3**).

## 2. Bugünkü davranış (okundu, değiştirilmedi)

### 2.1 Kod ve prompt

- **Çelişki tespiti yok. Ne kod yapıyor ne prompt.** `answer_prompt.py`'de çelişki için tek dayanak **kural 9**. O da yalnız "aynı terim veya kavram için farklı tanım/açıklama" diyor; **değer, tarih ve tutar kapsamda değil**. Ayrıca bir işaret istemiyor.
- **Kural 5**, zincir içindeki farkı "Bu değer <belge> ile önceki <eski değer> seviyesinden değiştirilmiştir" cümlesiyle anlatır. Hangi kaynakların aynı zincirde olduğunu kod hesaplar (`version_chain.py`, `Zincir:` satırı). Model yalnız okur.
- **Kural 12** (assist): Soru proje/belge belirtmiyorsa ve kaynaklar farklı belgelere/projelere ait farklı değerler içeriyorsa model sormalıdır. Soru proje adı veriyorsa uygulanmaz (b). Aynı projenin iki ayrı belgesinin farklı değer verdiği durumu (gerçek çelişki) hiçbir kural karşılamıyor.
- **Durum etiketi:** `AskWarning.kind` = `missing_data | insufficient_data | product_limit | document_processing | document_unreadable | router_fallback`. `schemas/ask.py:26` açıkça şunu söylüyor: "`data_conflict` is deliberately absent: it needs a prompt change and its own eval category". ADR listesinde de aynı not var (`ARCHITECTURE.md:225`).
- **Kaynak kartı (`SourceCard`):** `is_current`, `is_initial`, `supersedes_*`, `superseded_by_*`, `project_code` taşıyor. Çelişki alanı yok.
- **Excel yolu:** Tek değer üretir (`excel_ask.py`). Cevap promptunda çelişki kavramı yok. Workbook kataloğu sürüm filtrelemiyor (`list_excel_by_ids` yalnız `ready`). Bu P2'nin konusu, burada not olarak kalıyor. MIXED'de iki kısım yalnız art arda yazılıyor (`merge_mixed_answer`). Belge kısmının modeli Excel sonucunu görmüyor.
- **Ön yüz (AI-BalBal):** `AnswerView.tsx` `warnings[]`'i rozet + mesaj olarak gösteriyor. `types.ts:405` yalnız 3 türü tanıyor. Yeni tür eklenirse rozet etiketi boş kalır ama mesaj görünür.
- **EK_F:** Kural 7'ye "ünlem ve emoji kullanma" eklenmiş durumda. `polish_answer` yalnız tarih ve sayı biçimine dokunuyor; ❗'i silmez.

### 2.2 Ledger'daki kasıtlı çelişkiler (`conflict_kind: genuine_conflict`)

| Grup | Değerler | Kaynaklar | Eval sorusu |
|---|---|---|---|
| `karatepe-kredi-tutari` | 14.000.000 USD (sözleşme tesis tutarı) ↔ 13.600.000 USD (kullandırılan) | Facility Agreement (DOC-ANK-FIN-004, zincirde İLK HALKA, maddesi tadille değişmedi) ↔ Covenant Compliance Report Q2 2026 / ödeme planı | ANK-FIN-002 (beklenen yalnız `total_debt` 13,6M); dolaylı: FIN-003, FIN-011, DAT-003 |
| `yesilova-taksit11-faiz` | 18.240 USD (ödeme planı) ↔ 18.912 USD (banka faiz bildirimi) | **Excel** ödeme planı ↔ **belge** Banka Faiz Bildirimi | Yok |
| (sürüm farkı, çelişki değil) | Yeşilova ödeme planı Mart 2026 ↔ 01.09.2026 | `supersedes` zinciri | Yok |

Kasıtsız bir çelişki de var: **Kızılova önlisans tarihi.** Önlisans Belgesi'nin künyesinde `document_date` 18.01.2024, ÇED Süreci Durum Yazısı'nın metninde 15.01.2025. Bu veri hatası K2 ile repoda düzeltildi (`3026264`), canlıya henüz geçmedi.

### 2.3 Eval: çelişki beklenen sorular ve bugünkü durum (`results/v22`, yeni çağrı yok)

Soru setinde `conflict` kategorisi yok (11 kategori). Puanlayıcı ❗ aramıyor.

| Soru | M1 (70/99) | N1 (68/99) | Davranış |
|---|---|---|---|
| ANK-FIN-002 toplam kredi tutarı | ✅ | ✅ | M1 iki değeri verdi, "toplam finansman olarak ayrıca verilmiştir" dedi, etiket yok. **N1 kendinden emin yanlış:** "Bu değer Covenant Compliance Report Q2 2026 ile önceki 14.000.000 USD seviyesinden değiştirilmiştir". Kural 5'in sürüm cümlesini zincir dışı iki belgeye uyguladı. Çelişkiyi sürüm farkı gibi gizledi (Ç-7 ihlali), puanlayıcı geçirdi. |
| ANK-FIN-003 / FIN-011 | ✅ / ❌ | — | M1 iki değeri verdi; 14,0M'yi "güncel değildir" ya da "geçerli değer olarak alınmıştır" diye seçti. |
| ANK-DAT-003 (MIXED) | ✅ | ✅ | Belge kısmı yalnız 14,0M'yi verdi, 13,6M yok. Sessiz seçim. |
| IZM-DEV-001 | ✅ | ✅ | İki önlisans tarihini kaynağıyla verdi, etiket yok. |
| IZM-DEV-007 | ✅ | ✅ | M1: "hangisinin doğru olduğuna karar verilmemiştir" (doğru davranış, ❗ yok). N1: iki tarihi ayrı satırlarda verdi, fark söylenmedi. |
| ANK-FIN-013 (MIXED) | ❌ | ❌ | **Yanlış çelişki riski.** Excel kısmı "marj %6,5" verdi (`all_in_rate`, B-01/V21 R1). Belge kısmı %2,9 diyor. Bu çelişki değil, Excel eşleme hatası. |

**Özet ölçü (bugün):** 99 sorunun hiçbirinde "Çelişkili veri" etiketi yok. Kasıtlı Karatepe çelişkisi M1'de 3, N1'de 1 cevapta görünüyor; biri (N1 FIN-002) sürüm farkı gibi sunulmuş. Yeşilova faiz çelişkisini ölçen soru yok.

## 3. Önerilen yöntem: "AI anlar, kod uygular"

**Tespit AI'da (prompt), işaret ve biçim kodda.** Gerekçe: Belgelerde yapılandırılmış olgu yok. "Aynı olgu" kararını yalnız model verebilir. Kod ise modelin işaretini mevcut zincir ve proje bilgisiyle **doğrular** ve uyarıyı **sabit metinle** basar. Bu, `SORU:` satırının bugünkü düzeninin aynısıdır (ADR-027: model satırı yazar, kod ayırır ve doğrular).

1. **Prompt (kural 13, §4):** Model çelişki gördüğünde her değeri kendi `[Kn]` etiketiyle ayrı cümlede yazar ve farkı söyler (F-6). Cevabın sonuna `ÇELİŞKİ: [Ka] [Kb]` satırı ekler. Modele ❗ yazdırılmaz (F-1).
2. **Kod: ayırma.** Yeni `services/conflict.py` içinde `split_conflict_line(text)` (`split_question_line`'ın eşi) satırı cevaptan çıkarır.
3. **Kod: doğrulama.** Hepsi deterministik, LLM yok. İşaret kabul edilmezse satır atılır, cevap aynen kalır, `conflict marker rejected` + sebep loglanır:
   - En az iki farklı ve bilinen etiket olmalı. Etiketler **en az iki farklı belgeye** ait olmalı ve her etiket cevap gövdesinde de geçmeli (fark kaynağıyla verilmiş olmalı).
   - **Aynı zincir → ret** (sürüm farkıdır, kural 5). Bunun için `ChainPosition`'a koddan hesaplanan `chain_id` alanı eklenir (zincirin kök belge id'si; şema yok).
   - **Farklı proje → ret.** İki kaynağın da `project_code`'u var ve bunlar farklıysa çelişki sayılmaz (kural 10/12). Grup belgesi (`project_scope=group`) bir projeyle çelişebilir.
   - **Yürürlükte olmayan kaynak → ret** (`in_force=False`: süresi dolmuş ya da henüz başlamamış). Bu zamansal farktır.
   - Yetki filtresi zaten önce çalışır. Etiketler yalnız prompta giren, yani izinli kaynaklardan gelebilir. Kod ayrıca hiçbir şey eklemez (kural 1).
4. **Kod: gösterim.** Kabul edilirse:
   - Cevabın **ilk satırı** sabit `❗ Çelişkili veri: Kaynaklar bu bilgi için farklı değer veriyor; Balbal birini seçmez.` olur.
   - Ardından modelin cevabı aynen gelir (iki değer, kaynak etiketleriyle).
   - **Son satıra** sabit F-6 kapanışı eklenir: `Hangisinin geçerli olduğunu teyit edebilir misiniz?` (Ç-7.1 adım 4).
   - `warnings[]`'e `AskWarning(kind="data_conflict", message=<sabit metin>, action="request_data", source_refs=[Ka, Kb])` eklenir. `source_refs` yeni ve isteğe bağlı bir alan; ön yüz bu kartları ❗ ile işaretleyebilir.
   - Audit satırı mevcut `warnings` JSONB sütununda saklanır. **Migration yok.**
5. **MIXED:** Belge kısmının ❗'i kendi başlığı altında kalır, Excel kısmına dokunulmaz. Excel ↔ belge farkının tespiti bu pakette **yok** (**S-2**).
6. **Yasaklar kodla da korunur:**
   - Kod hiçbir zaman değer seçmez, ortalama almaz, sıralamaz.
   - Cevapta işaret olup doğrulama düşerse modelin yazdığı iki değer yine görünür (gizleme yok). Yalnız ❗ etiketi basılmaz.
   - **Kendinden emin yanlış riski:** Asıl risk, modelin çelişkiyi sürüm farkı gibi sunması (N1 FIN-002). Kural 13'ün (c) cümlesi bunu yasaklar: "Değiştirilmiştir" cümlesi yalnız aynı `Zincir:` ailesi için kurulur. Kod ayrıca bunu ölçmek için loglar (aşağıda): Cevapta "seviyesinden değiştirilmiştir" geçiyor ama atıf yapılan iki kaynak farklı zincirdeyse, satır `version_sentence_cross_chain` olarak işaretlenir. Bu bir gösterim değil, ölçüdür.

**Alternatifleri reddettim:**
- *Yalnız kod (sayı karşılaştırma):* "Aynı olgu" bilinmeden yapılırsa FIN-013 gibi Excel eşleme hatalarını ❗ yapar, tarihleri ve dönemleri karıştırır.
- *Yalnız prompt (model ❗ yazar):* F-1 ile çelişir, doğrulanamaz ve sürüm farkında yanlış alarm verir.

## 4. Prompt değişikliği (Ç-15/8, ayrı onay)

**Kapsam:** Yalnız `SYSTEM_PROMPT_ASSIST` (canlı yol; EK_F/ASSIST açık). `SYSTEM_PROMPT` byte byte aynı kalır (ADR-027'den beri bu düzen). Kural 1–12 değişmez. Prompta örnek konmaz, örnekler eval setinde durur.

**Önerilen tam metin (kural 13, `_RULES_ASSIST`'in sonuna):**

> 13. Aynı projenin aynı bilgisi (bir değer, tutar, oran, tarih ya da durum) için iki veya daha fazla kaynak birbirinden FARKLI şey söylüyorsa ve bu kaynaklar aynı belge zincirinin eski ve yeni halkası değilse, bu çelişkili veridir. Bu durumda: kaynaklardan birini seçme, birini doğru ya da geçerli diye sunma, ortalama alma, değerleri birleştirme. Her değeri kendi kaynak etiketiyle ayrı bir cümlede yaz, belge adını ve tarihini belirt; farkı kaynaklarda yazdığı biçimiyle söyle, fark hesabı yapma. Cevabın sonuna yeni bir satırda "ÇELİŞKİ:" ile başla ve yalnızca çelişen kaynakların etiketlerini yaz. Şunlar çelişki DEĞİLDİR, bu satırı yazma: (a) aynı zincirde eski ve güncel değer — 5. kural geçerlidir; (b) farklı projelerin değerleri — 10. ve 12. kural geçerlidir; (c) aynı bilginin farklı dönemlere ya da tarihlere ait değerleri. 5. kuraldaki "… seviyesinden değiştirilmiştir" cümlesini yalnızca aynı Zincir: ailesindeki belgeler için kur; farklı belge ailelerinin farkını değişiklik gibi anlatma. Çelişki varken 2. kuraldaki cümleyi yazma.

**Etki:**
- Girdi ≈ +230 token/cevap çağrısı. M1'de cevaplanan sorularda `tokens_in` medyanı 31.968 (aralık 3.610–47.874); ek yük ≈ %1.
- Çıktı yalnız çelişkide ≈ +10 token. **Ek LLM çağrısı yok.**
- Kural 9 (tanım farkı) dokunulmadan kalır. Kural 13 değer, tarih ve durum içindir.
- Kural 12 ile sıra: Soru proje vermiyorsa ve değerler farklı projelere aitse kural 12 (sor) geçerlidir. Aynı projenin iki ailesi farklıysa kural 13 geçerlidir.
- `docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md` aynalanır (eşlik testi zaten var).
- **S-1 cevabı "sözleşme tutarı ile kullandırılan farklı olgulardır" olursa** kural 13'e (d) eklenir: "kaynak değerleri açıkça farklı adlarla yazıyorsa (üst sınır/kullanılan gibi) ikisini adıyla yaz; bu çelişki değildir". Bu durumda Karatepe çifti ❗ almaz.

## 5. Etkilenen dosyalar, büyüklük, şema/bağımlılık/maliyet

| Dosya | Değişiklik | Tahmini |
|---|---|---|
| `backend/app/services/answer_prompt.py` | `_RULE_13_ASSIST` + listeye ekleme | +15 |
| `docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md` | ayna | +1 paragraf |
| `backend/app/services/conflict.py` (yeni) | `split_conflict_line`, `validate_conflict`, `render_conflict` | ~90 |
| `backend/app/services/version_chain.py` | `ChainPosition.chain_id` (kod içi) | +6 |
| `backend/app/services/ask.py` | çağrı noktası, `AskResult.conflict` (dosya zaten 515 satır; mantık `conflict.py`'de) | +12 |
| `backend/app/services/ask_router.py` | `data_conflict` uyarısını `warnings`'e ekleme | +6 |
| `backend/app/schemas/ask.py` | `kind` += `data_conflict`, sabit metin, fabrika, `AskWarning.source_refs: list[str] = []` (eklemeli, API geriye uyumlu) | +15 |
| `backend/tests/test_conflict.py` (yeni) + `test_answer_prompt.py`, `test_ask.py`, `test_ask_router.py` | §7 | ~200 |
| `docs/ARCHITECTURE.md` | ADR-035 (çelişki: AI işaretler, kod doğrular/basar) + `:225` notunun güncellenmesi | +10 |
| AI-BalBal `frontend/src/api/types.ts`, `lib/strings.ts`, `AnswerView.tsx` | `data_conflict` rozeti "Çelişkili veri" + kart işareti. **Tansu'nun deposu, ayrı PR, isteğe bağlı:** ❗ cevap metninde zaten görünür | ~15 |

- **DB şeması / migration:** yok (audit `warnings` JSONB). Ç-15/4 yok.
- **Yeni bağımlılık / dış servis:** yok (T-14).
- **Ayar:** Yeni bayrak önermiyorum. Davranış mevcut ASSIST/EK_F prompt yolunda; geri alma git revert ile (§7).
- **LLM maliyeti:** Ek çağrı yok. Ölçüm koşusu (§7) normal bir eval koşusunun maliyetinde.

## 6. Riskler

1. **Yanlış çelişki alarmı (gürültü):** Tadil zinciri, dönem raporları (Q1/Q2 DSCR) ve proje proje değerler ❗ alabilir. Önlem: kod aynı zincir, farklı proje ve yürürlükte olmama durumlarını reddeder; kural 13 (c) dönemleri dışarıda tutar. Ölçü: §7.3'teki yanlış alarm kümesi; kabul ölçütü 0.
2. **Gerçek çelişkiyi kaçırma:** Model satırı yazmazsa ❗ çıkmaz. Kod, satır olmadan çelişki bulamaz. Önlem: kural 13 + eval'de kasıtlı çiftler. Kaçırma "sessiz seçim" olur (Ç-7). Ölçülür, kod tarafında telafisi yok. Bu yöntemin bilinen sınırı.
3. **Kendinden emin yanlış:** Çelişkiyi sürüm farkı gibi anlatmak (N1 FIN-002). Önlem: kural 13'ün son cümleleri + `version_sentence_cross_chain` logu (ölçü).
4. **Excel/belge karışımı:** MIXED'de Excel'in yanlış eşlemesi (FIN-013 %6,5) çelişki gibi görünebilir. Önlem: bu pakette Excel ↔ belge tespiti yok, yalnız belge ↔ belge (**S-2**). Yeşilova faiz çifti bu yüzden kapsam dışı kalır.
5. **Sürüm kuralıyla çakışma:** Kural 5'e göre "eski halkadaki değişmemiş değer hâlâ güncel". Zincir dışı bir belgeyle farklıysa bu çelişkidir (Karatepe FA ↔ Covenant). Kod bunu `is_current` ile değil `chain_id` ile ayırır; `is_current` kullanılsaydı Karatepe çifti yanlışlıkla reddedilirdi. **S-1** onayı gerekiyor.
6. **Kapı skoruna etkisi:**
   - Puanlayıcı ❗ aramıyor. Sabit ilk ve son satır `value_check`/`phrase_check`'i bozmaz (rakam eklemiyor).
   - Etkilenebilecek yerler: `format_check` (cevap uzunluğu/yapısı) ve `answer_policy` (FIN-002 bugün tek değer bekliyor; iki değer zaten veriliyor). Bu, kapı öncesi koşuda ölçülür.
   - **IZM-DEV-001/007:** K2 canlıya geçince önlisans çelişkisi kalkar. ❗ çıkarsa yanlış alarmdır. Geçmezse ❗ beklenir (**S-3**).
7. **Ön yüz:** Tansu'nun PR'ı gelene kadar rozet etiketi boş görünür. ❗ satırı metinde olduğu için davranış kaybolmaz.
8. **Prompt uzunluğu / Haiku uyumu:** Kural 12 ölçümlü bir metindi. Kural 13 onun ayrımlarını tekrar ediyor. Haiku'da kural 12 davranışı bozulabilir. Önlem: önce/sonra kural 12 soruları (ambiguous 9 soru) ayrıca karşılaştırılır.

## 7. Test planı ve geri alma

### 7.1 Birim (LLM'siz, sahte istemci)
- `split_conflict_line`: satır yok / tek etiket / `[K1, K2]` / bilinmeyen etiket / gövdede geçmeyen etiket.
- `validate_conflict`: aynı zincir → ret; farklı proje → ret; grup belgesi + proje → kabul; `in_force=False` → ret; aynı belgenin iki sayfası → ret; Karatepe FA (İLK HALKA, `is_current=False`) + Covenant (GÜNCEL, farklı zincir) → **kabul**.
- `render`: ilk satır ve son satır sabit, model metni bayt bayt korunur, `polish_answer` ❗'e dokunmaz.
- `ask.py` / `ask_router.py`: `warnings`'te `data_conflict`, audit satırında saklanma, MIXED'de belge başlığı altında kalma, cevaplanmayan cevapta (`is_no_answer`) işaret yok sayılır.
- Prompt aynası + `SYSTEM_PROMPT` değişmezlik testi.

### 7.2 Eval soruları (soru seti kontrolörün; **öneri, eklenmedi**)
- **Çelişki beklenen:** ANK-FIN-002 (❗, iki değer: FA 14,0M + Covenant 13,6M). Yeni ölçü sorusu C-1 "Karatepe RES kredisinin tutarı nedir?" (finans).
- **Yeşilova #11 faiz** yalnız S-2 "evet" ise.
- **Kızılova önlisans tarihi:** K2 öncesi ❗ beklenir mi, S-3'e bağlı.

### 7.3 Yanlış alarm testi
Tam 100 soruluk koşuda ❗ alan her soru listelenir. İzinli küme = `karatepe-kredi-tutari`'na dokunan sorular (FIN-002, FIN-003, FIN-011, DAT-003). Kümenin dışındaki her ❗ yanlış alarmdır. Özellikle bakılacaklar:
- temporal (11; ANK-FIN-013 zincir farkı dahil)
- comparison (3)
- ambiguous (9)
- Yeşilova ödeme planı sürümleri

**Kabul:** izinli küme dışında 0 ❗.

### 7.4 Önce/sonra ölçüsü
- **Önce:** `results/v22/{m1,n1}` (bu planın §2.3'ü; 0 etiket).
- **Sonra:** aynı model/ayarla tek canlı koşu. Rapor edilecekler:
  - ❗ alan sorular
  - izinli kümede yakalama oranı
  - yanlış alarm sayısı
  - kural 12 sorularının değişimi
  - toplam skor (v2.2)
  - `conflict marker rejected` ve `version_sentence_cross_chain` log sayıları
- Gürültü için kasıtlı çiftlerde `--repeat 3` (TANSU_GERI_BILDIRIM §5.3 önerisi).

### 7.5 Geri alma
- Tek commit; `git revert` + backend yeniden başlatma (`docs/OPERATIONS.md` runbook'u).
- Migration ve ayar olmadığı için veri tarafında geri alınacak bir şey yok.
- Yeni tür API'de eklemeli; eski istemci etkilenmez.

## 8. Tansu'ya açık sorular (en fazla 3)

**S-1 ("güncel kaynak" ve Karatepe çifti):** Bir tadil maddeyi değiştirmediyse, eski halkadaki değer kural 5'e göre hâlâ güncel. Bu değer başka bir belge ailesindeki değerden farklıysa ❗ sayalım mı? Somut örnek: Facility Agreement 14.000.000 USD ↔ Covenant Report "kullandırılan" 13.600.000 USD. Ledger bu çifti `genuine_conflict` diye işaretliyor, ama iki değer farklı adlarla yazılmış (tesis tutarı / kullandırılan). Önerim: **evet, ❗** (ledger kararınızla aynı). "Farklı olgu" derseniz kural 13'e (d) eklenir, çift ❗ almaz.

**S-2 (Excel ↔ belge):** MIXED cevapta Excel değeri ile belge değeri farklıysa (Yeşilova 11. taksit faizi: ödeme planı 18.240 ↔ banka bildirimi 18.912 USD) ❗ kapı öncesi kapsamda mı? Önerim: **hayır, kapıdan sonra, P2'den (Excel proje ayrımı) sonra.** Bugün Excel'in eşleme hatası (FIN-013 "marj %6,5") yanlış ❗ üretir. Bu pakette yalnız belge ↔ belge yapılır.

**S-3 (künye ↔ metin):** Bir belgenin künye tarihi (`document_date`) ile başka bir belgenin metnindeki tarih farklıysa ❗ sayılsın mı? Örnek: Kızılova önlisans, künyede 18.01.2024, ÇED yazısında 15.01.2025. Demo veride bu bir hataydı, K2 ile düzeliyor. Gerçek müşteri verisinde aynı durum çıkacak. Önerim: **evet.** İki kaynak da kullanıcının gördüğü yetkili kaynaktır (Ç-7 "yetkili kaynakların farklı bilgi vermesi"). K2 canlıya geçince IZM-DEV-001/007 yanlış alarm testine girer.

## 9. Teknik görüşüm

- **Engel görmüyorum. Paket küçük:** bir prompt kuralı, bir yeni modül, şema ve bağımlılık yok, ek LLM çağrısı yok.
- **İş bölümü doğru yerde:** "Bu iki cümle aynı olguyu mu anlatıyor?" yargısı ancak AI'da yapılabilir. "Aynı zincir mi, aynı proje mi, yürürlükte mi, kullanıcı görüyor mu?" soruları ise zaten kodda hesaplanıyor. Bunları modele bırakmamak gerekir. ❗'i koddan basmak hem F-1 ile uyumlu hem de etiketin tek biçimde çıkmasını garanti ediyor.
- **En büyük kazanç ❗ değil, kural 13'ün son cümlesi olabilir.** Bugünkü en tehlikeli davranış, çelişkiyi sürüm farkı gibi anlatan kendinden emin cevap (N1 FIN-002). Puanlayıcı onu geçiriyor.
- **Yöntemin sınırı açık:** Model işaret koymazsa kod yakalayamaz. Kaçırma oranı eval'de ölçülecek. Kapıda "aranan davranış" için soru setine en az 2–3 kasıtlı çelişki sorusu (+ yanlış alarm kontrolü) girmesini öneririm. Bugün yalnız ANK-FIN-002 var, o da tek değer bekliyor.
- **Sıra önerisi:** Madde 1 (P1) → bu paket → P2. Paketler birbirine dokunmuyor (P1 netleştirme, P3 cevaplanan yol). P3'ün ölçüsü P2'den önce alınırsa FIN-013'ün Excel gürültüsü yanlış alarm testinde ayrıca not edilmeli.

---

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (ADT-4). Okunan: Çekirdek (Ç-6, Ç-7, 7.1, Ç-15, Ç-16, Ç-17), 01 Ürün (Ek-F sınırları), 02 Teknik (T-9 + ADT-4), Ek-F (F-1, F-6), Ek-D (S-10)
Ürün etiketi      : Ürün 1 — T-11 (Ç-7 durum etiketi; yeni yetenek değil, mevcut cevap yolunun davranışı)
Kritik Geliştirme Kararı : Ç-15/8 (Balbal AI cevap promptu: kural 13 + davranış kuralı). Plan sunuldu, onay bekleniyor (T-9). Ç-15/3 yok (yetki filtresi önce çalışır, değişmez); Ç-15/4 yok (DB şeması değişmiyor; API'ye eklemeli enum değeri ve isteğe bağlı alan)
Gizli bilgi / yeni bağımlılık : Yok — T-14
Kapsam dışı değişiklik        : Yok — kod/prompt/ayar/şema/puanlayıcı/soru seti/canlı servis dokunulmadı; yalnız bu plan dosyası
Kendi başına verilen kararlar : (1) Ölçüm results/v22 (scorer v2.2) dosyalarından; yeni LLM çağrısı yok. (2) "Güncel" ayrımı is_current değil chain_id ile önerildi (§6/5). (3) Excel↔belge tespiti kapsam dışı önerildi, S-2'ye bağlı. (4) Yeni ayar bayrağı önerilmedi; geri alma git revert. (5) Ön yüz değişikliği Tansu'nun deposunda, isteğe bağlı — Ç-9
```
