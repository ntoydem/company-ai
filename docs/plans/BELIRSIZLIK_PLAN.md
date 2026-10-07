# Belirsiz sorularda netleştirme — Uygulama Planı (Tansu kararı (a), 07.10.2026)

**Tarih:** 07.10.2026 · **Durum:** Naci onayı bekliyor; **kod yazılmadı, canlı ölçüm yapılmadı** · **Karar:** Tansu — belirsiz soruda Balbal kısa bir netleştirme sorusu sorsun, belgeleri sıralayıp cevaplamasın (`docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §0, 07.10.2026) · **Bayrak:** `ASSIST_MODE` (ADR-027; canlıda kapalı) · **Dal önerisi:** `feat/belirsizlik` (`main` @ `67e09a3` üzerinden)

Kaynaklar: ADR-014 (sabit metin = hüküm), ADR-021 (sıfır parça → LLM yok), ADR-027 (assist bloğu, kod mülkiyeti, `validate_question`), `docs/reports/ASSIST_KARSILASTIRMA_2026-10-06.md` (belirsiz 5 soru × 2 tekrar), `docs/reports/DAVRANIS_MANTALITESI_REPORT.md` §8–§10, `seed_data/evaluation/questions.json` v5.

---

## 0. Tespitler (bugünkü kod ve ölçüm)

- **T1 — Assist yalnızca `answered=false` yolunda tetikleniyor.** `app/services/ask.py`: model cevabı `is_no_answer()` ile sabit cümleyse `build_insufficient_assist` (modelin `SORU:` satırı `validate_question`'dan geçerse korunur); sıfır parçada `build_zero_chunk_assist` (LLM yok). Model cevap verdiyse `SORU:` satırı **yok sayılır** (`"assist question ignored on an answered reply"`). Yani netleştirme ancak model önce "cevap veremedim" derse mümkün.
- **T2 — Prompt belirsizliği ele almıyor.** `SYSTEM_PROMPT_ASSIST` = kural 1–7, 8 (Süre:), 9–10, **11** ("cevap veremediğinde tek kısa soru"). Hiçbir kural "soru birden çok belgeye/projeye eşit uyuyorsa seçme, sor" demiyor; kural 2–4 kaynak varsa aktarmayı söylüyor. Modelin varsayılan eğilimi "yardımcı ol" → kaynakları sıralayarak cevap.
- **T3 — Ölçüm (06.10.2026, bayrak açık, 5 soru × 2):** 2 netleştirme (GEN-AMB-001 ×2 — retrieval'ın getirdiği parçalar soruyu karşılamadı, model sabit cümle + `SORU:` yazdı), 8 sıralayarak cevap:
  | Soru | Model ne yaptı | Neden belirsiz |
  |---|---|---|
  | GEN-AMB-002 "Raporda belirtilen DSCR değeri kaç?" (finans) | Q4 2024, Q2 2026, Q3–Q1 dönemlerini listeledi | hangi rapor/dönem yok |
  | GEN-AMB-003 "Son tadil neyi değiştirdi?" (yonetim) | Facility Agreement Amendment 02'yi anlattı | iki tadil zinciri var (kredi, lisans); model "son"u kredi zincirinde seçti — savunulabilir ama Tansu kararı: sor |
  | GEN-AMB-004 "Lisans ne zaman alındı?" (enerji) | yalnızca Ankara üretim lisansı 15.06.2020 | kullanıcı İzmir önlisansını da görüyor; proje adı yok → model sessizce birini seçti |
  | GEN-AMB-005 "Toplantıda ne karar alındı?" (yonetim) | 3 ayrı kararı art arda sıraladı (biri bozuk "9020" → "yüzde 90"; 07.10'da kaynak düzeltildi) | 7 karar/toplantı belgesi görünür |
- **T4 — Belirsizliğin ortak biçimi:** soruda **ayırt edici isim yok** (`specific_matched_terms` boş: "sözleşme", "rapor", "lisans", "toplantı", "tadil" hepsi genel/glossary-bilinen); retrieval'ın getirdiği parçalar **birden çok projeye ya da birden çok belge türüne/döneme** yayılıyor; kullanıcı kapsam (proje, belge, dönem) vermemiş.
- **T5 — Eval tarafı hazır:** kategori `ambiguous` = `expect_no_answer=true` + `expect_assist=clarify`, eşik ≥%80 (`DEFAULT_THRESHOLD_PCT`), `assist_check` türü ölçer; negatif kontroller ANK-NEG-001/002 (`document`, cevap bekleniyor, assist beklenmiyor); karşılaştırma soruları GEN-CMP-001…003 (**iki projeyi sıralayarak cevaplamak zorunlu** — Ü-3) %100 kategorisinde. Aşırı tetiklenmenin doğal ölçüsü: bu soruların cevaplanma oranı R0/R1'e göre düşmemeli.
- **T6 — ADR-014 uyumu her seçenekte korunabilir:** `answer` sabit cümle; netleştirme `assist.question` (kod şablonu ya da `validate_question`'dan geçmiş model satırı); yeni sabit cümle gerekiyorsa ADR-014 listesine kodla eklenir, LLM üretmez.

## 1. Seçeneklerin karşılaştırması

| | **(1) Cevap prompt'una kural** | **(2) Kodla belirsizlik tespiti** | **(3) Router'da sınıflandırma** |
|---|---|---|---|
| **Ne** | `SYSTEM_PROMPT_ASSIST`'e kural 12: "Soru hangi belgeyi/projeyi/dönemi kastettiğini söylemiyorsa ve kaynaklar birden fazla belgeye, projeye ya da döneme ait farklı değerler içeriyorsa **birini seçme, hepsini sıralama**: 2. kuraldaki cümleyi yaz ve kural 11'e göre tek bir `SORU:` sor. Soru proje adı, belge adı ya da dönem veriyorsa bu kural uygulanmaz; iki projeyi karşılaştırma isteği (Ü-3) de belirsizlik değildir." | Retrieval'dan sonra, LLM'den **önce** kod: (i) soru terimlerinde ayırt edici terim yok (`specific_matched_terms` boş, proje kelimesi yok) **ve** (ii) getirilen parçalar ≥2 projeye **veya** ≥2 belge türüne/sürüm-dışı belgeye yayılıyor ve en iyi iki parçanın FTS skoru yakın (ör. `rank` farkı < %15) → LLM çağrılmaz, `answer` = sabit cümle, `assist.kind=clarify`, `question` = kod şablonu eksenle ("Hangi proje: Ankara RES mi, İzmir RES mi?" / "Hangi belge: A, B, C?" — adlar yalnızca kapıdan). | Router çıktısına `clarify_needed: bool` (+ `clarify_axis`): yalnızca soru metnine bakarak "belirsiz" deme; `ask_router` o zaman belge hattını atlayıp sabit cümle + şablon soru döndürür. |
| **Aşırı tetiklenme riski** | **Orta.** Model "birden fazla kaynak" görünce açık sorularda da sorabilir: facility zinciri 6 sürümdür (ANK-NEG-001 "vadesi kaç yıl?" 4 parça, aynı değer); Ü-3 karşılaştırmaları iki projeden parça getirir. Kuralın istisnaları (proje/belge/dönem verilmişse; karşılaştırma isteği) bunu azaltır; kalan risk ölçümle görülür. Tek prompt revizyonu hakkı (Not 2 politikası). | **Yüksek, ama deterministik.** (ii)'nin "≥2 proje" sinyali tam da Ü-3 karşılaştırmalarında ateşlenir (soru iki projeyi adıyla verir → (i) proje kelimesi var → düşer, iyi); "≥2 belge türü" sinyali "Güncel DSCR kaç?" (MIXED, covenant + rapor) gibi meşru sorularda ateşlenir; eşikler elle ayarlanır, her ayar yeni yanlış pozitif üretebilir. Avantaj: **LLM'siz kuru koşu** ile 76 sorunun tamamında kaç kez ateşlendiği sıfır kotayla görülür. | **En yüksek.** Router belgeleri görmez: "Sözleşmenin vadesi?" korpusta tek sözleşme varken de belirsiz sayılır; ya da tam tersi, ad verilmemiş ama tek aday olan soru gereksiz soruya döner. Kapı bilgisi olmadığından aday adı yazamaz (G3). |
| **Ölçüm planı** | A: 5 belirsiz × 3 (hedef `clarify` ≥ %80 → ≥ 12/15). B (aşırı tetiklenme): ANK-NEG-001/002 + 3 yeni negatif kontrol (§3) + 14 %100-kategorisi (GEN-CMP dahil) × 1 → cevaplanma R1 ile aynı, G1–G3 %100. C (yalnızca A+B temizse): R0'da cevaplanmış `document`/`temporal`/`version` sorularının tamamı × 1 → yeni "cevapsız" sıfır. | Önce **kuru koşu** (LLM yok, `scripts/dry_run.py` benzeri): 76 soru için sinyal (i)+(ii) → beklenen: 5 belirsizde ateşlenir, diğer 71'de ateşlenmez; yanlış pozitif listesi plana eklenir. Sonra A/B/C aynı. | Router prompt revizyonu + aynı A/B/C; ayrıca router'ın mevcut 76 sınıflandırması değişmemeli (`test_router` fake'leri + canlı 76 × router çağrısı). |
| **Kota (flash-lite, 26 sn aralık)** | A 15 + B 19 = **34 çağrı** (~15 dk); C ~40 çağrı (~18 dk), yalnızca gerekirse. Prompt revizyonu olursa A tekrar (+15). | Kuru koşu **0**; sonra 34 (+40). Belirsiz tespit edilen sorularda LLM hiç çağrılmaz → çalışma maliyeti düşer. | 34 (+40) + router'ın 76 sorusu = **+76** (router çağrısı ucuz ama kota sayar). |
| **`ASSIST_MODE` uyumu** | Kural yalnızca `SYSTEM_PROMPT_ASSIST`'te (`system_prompt(assist)`); kapalıyken bayt-identik. | Dal `settings.assist_mode_enabled` ile sarılır; kapalıyken retrieval → LLM aynen. | Router prompt'u iki bayrağa göre ikiye ayrılmalı (bugün tek prompt) — bayrak kapalı yolu da değişme riski taşır. |
| **ADR-014 (sabit metin)** | ✅ `answer` sabit cümle; `SORU:` satırı `validate_question` (rakam/tarih/para yok, yetkisiz başlık yok, yankı filtresi) → düşerse `CLARIFY_TEMPLATE`. | ✅✅ Tüm metin kod şablonu; eksen adları (proje/belge) kapıdan. Yeni şablonlar ADR-014 listesine eklenir. | ✅ metin kod şablonu; ama aday adı veremez (router kapıyı bilmez) → yalnızca "Hangi projeyi kastediyorsunuz?" genel soru. |
| **G3 / yetki** | Değişmez (kapı önce, model yalnızca yetkili parçaları görür; `validate_question` yetkisiz başlığı düşürür). | Değişmez (adaylar `allowed`'dan). | Router kapıdan önce çalışır; aday adı yazarsa ihlal → yazamaz. |
| **Kod değişikliği** | 1 sabit (`_RULE_12_ASSIST`), prompt dokümanı (`make prompt-doc` assist sürümü), 1–2 test (prompt içeriği; fake LLM ile "sabit cümle + SORU:" → `clarify`). ADR-027'ye madde. | `app/services/assist.py`'ye `ambiguity_axes(session, allowed, chunks, terms)` + `CLARIFY_AXIS_TEMPLATES`; `ask.py`'ye LLM öncesi dal; `assist.kind` aynı (`clarify`), yeni alan `assist.axis: project\|document\|period` (additive); testler; dry-run scripti. | Router şeması + prompt + `RoutedQuestion` alanı + `ask_router` dalı + fake router; en geniş yüzey. |
| **Geri alma** | bayrak / tek sabiti kaldır | bayrak / tek `if` | bayrak + router prompt geri alma |

## 2. Öneri — ilk adım en az riskli: **(1) prompt kuralı**, (2) kuru koşu ile **ölçülmüş yedek**, (3) **şimdi değil**

- **Adım 1 — (1):** kural 12'yi `SYSTEM_PROMPT_ASSIST`'e ekle (yalnızca bayrak açıkken), istisnalarıyla (proje/belge/dönem verilmişse uygulanmaz; karşılaştırma isteği belirsizlik değil). Mevcut hat zaten "sabit cümle + `SORU:` → `clarify`" üretiyor (T1), yani model doğru davranırsa **başka kod gerekmez**. Ölçüm A+B (34 çağrı); A'da `clarify` < 12/15 ya da B'de tek bir yeni cevapsız/G1–G3 ihlali → **dur, raporla**; en fazla **bir** prompt revizyonu, sonra karar Naci'de.
- **Adım 2 — (2) kuru koşu (kota 0):** (1)'den bağımsız olarak sinyal (i)+(ii)'yi 76 soru üzerinde LLM'siz çalıştırıp yanlış pozitif listesini çıkar. (1) yetersiz kalırsa (model yine sıralıyorsa) ya da aşırı tetikleniyorsa, kod tespiti **yalnızca kuru koşuda temiz olan sinyalle** devreye alınır (LLM'siz, deterministik, ADR-014'e en uygun). Kuru koşu temiz çıkarsa (2) tek başına da aday olur — karar ölçüm sonrası.
- **(3) router:** belgeleri görmediği için belirsizliği bilemez; iki bayrağa bölünmesi gerekir; **bu turda yok**.
- Her adımda `answer` = sabit cümle (ADR-014), `assist.kind=clarify`; Ç-7 durumları ve uyarı türleri değişmez; prompt'a örnek eklenmez (Not 2 kuralı).

## 3. Yeni eval soruları — TASLAK (onay olmadan `questions.json`'a yazılmaz, canlı ölçüm yapılmaz)

Amaç: belirsiz **görünen** ama korpusta tek adayı olan sorular → cevap **verilmeli** (aşırı tetiklenme kontrolü). Kategori `document`, `expect_no_answer=false`, `expect_assist` yok; `expected_answer` ledger yolu (yol adları `validate-ledger` F8 ile doğrulanacak):

| ID (taslak) | Soru | Kullanıcı | Beklenen | Neden negatif kontrol |
|---|---|---|---|---|
| ANK-NEG-003 | "Kredi sözleşmesinin vadesi kaç yıl?" | finans | `ledger:ankara_res.project.finance.tenor_years` (facility zinciri tek, 6 sürüm aynı değer) | "sözleşme" adı yok ama finans kullanıcısının tek kredi sözleşmesi zinciri var; sürüm çokluğu belirsizlik değil (TEMPORAL TRUTH) |
| ANK-NEG-004 | "Üretim lisansı ne zaman alındı?" | enerji | `ledger:ankara_res.project.development.licence_date` (15.06.2020) | GEN-AMB-004'ün karşıtı: "üretim lisansı" yalnızca Ankara'da var (İzmir'de önlisans) → proje adı olmadan da tek aday |
| CO-NEG-005 | "Denetim komitesi üyeleri hangi kararla atandı?" | yonetim | kaynak `DOC-CO-ADM-008` (`required_sources`), değer kontrolü yok | GEN-AMB-005'in karşıtı: "toplantı" yerine konu verildi → tek karar belgesi |

Ayrıca mevcut belirsiz 5 soru olduğu gibi kalır (`notes` "TASLAK" ibaresi Naci onayıyla kaldırılır, 06.10.2026 onayı var). Kota taslak soru sayısı `CATEGORY_QUOTAS` (`document` zaten dolu) ile çelişmez; `validate-ledger` Q-kuralları koşulur.

## 4. Kabul kriterleri (Adım 1)

| # | Kriter | Kanıt |
|---|---|---|
| 1 | Bayrak kapalı: prompt ve yanıt bayt-identik | `test_assist.py::test_flag_off_keeps_todays_contract` + `SYSTEM_PROMPT` değişmedi testi |
| 2 | Bayrak açık, fake LLM "sabit cümle + SORU: Hangi projeyi kastediyorsunuz?" → `answered=false`, `assist.kind=clarify`, `question` korunur | yeni test (mevcut `test_insufficient_keeps_a_valid_model_question…` deseni) |
| 3 | Prompt dokümanı güncel | `make lint` (`print-answer-prompt-assist`) |
| 4 | Ölçüm A: belirsiz 5 × 3 → `clarify` ≥ 12/15, G1–G3 15/15 | `make eval EVAL_ARGS="--ids GEN-AMB-001,…,005 --repeat 3"` |
| 5 | Ölçüm B: ANK-NEG-001/002 + 3 yeni + 14 %100 × 1 → cevaplanma R1 ile aynı (hiç yeni cevapsız yok), G1–G3 19/19 | tek koşu; tablo raporda |
| 6 | Ölçüm C (A+B temizse): R0'da cevaplanmış soruların tamamı × 1 → yeni cevapsız 0 | tek koşu |
| 7 | Tansu için yan yana tablo (06.10 ile aynı 5 soru: önce/sonra metinleri) | `scripts/compare_assist_runs.py` |

## 5. Dosyalar (Adım 1) · (2) için ek
`backend/app/services/answer_prompt.py` (`_RULE_12_ASSIST`), `docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md`, `backend/tests/test_assist.py`, `backend/tests/test_answer_prompt.py`, `seed_data/evaluation/questions.json` (+3 negatif kontrol, onay sonrası), `docs/ARCHITECTURE.md` (ADR-027'ye "belirsizlik" maddesi), rapor `docs/reports/BELIRSIZLIK_REPORT.md`. (2) için: `backend/app/services/assist.py` (`ambiguity_axes`, şablonlar), `backend/app/services/ask.py` (LLM öncesi dal), `scripts/dry_run_ambiguity.py`, `backend/tests/test_assist.py`.

---

## SORU (Naci cevaplamalı)

1. **Sıra onayı:** Adım 1 = prompt kuralı (1); Adım 2 = (2)'nin LLM'siz kuru koşusu hemen (kota 0) ve gerekirse devreye alma; (3) yok — uygun mu?
2. **Kural 12 metni** (§1 tablosundaki) ve istisnaları (proje/belge/dönem verilmişse uygulanmaz; Ü-3 karşılaştırmaları belirsizlik değil) — onaylıyor musun, değişiklik var mı?
3. **3 negatif kontrol taslağı** (§3) `questions.json`'a eklensin mi; ledger yolları doğrulandıktan sonra?
4. **Ölçüm C** (R0'da cevaplanmış ~40 soru × 1, ~18 dk) Adım 1'in parçası mı, yoksa yalnızca A+B temizse ayrı seansta mı?
5. **GEN-AMB-003 "Son tadil neyi değiştirdi?"** için beklenti kesin `clarify` mi (model bugün "en güncel tadil"i seçiyor — TEMPORAL TRUTH'a göre savunulabilir)? Tansu kararı (a) "sor" diyor; onayla ya da bu soruyu `document` kategorisine çevir.
6. **"Sorulamaz" durumu:** belirsizlik tespit edilip de netleştirme sorusu yazılamazsa (model satırı düşer) bugünkü `CLARIFY_TEMPLATE` ("Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?") yeterli mi?
