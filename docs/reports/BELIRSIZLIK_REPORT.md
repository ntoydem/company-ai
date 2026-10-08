# Rapor — Belirsiz sorularda netleştirme (Tansu kararı (a); kural 12 + kodla tespitin kuru koşusu)

**Tarih:** 07.10.2026 (ikinci tur aynı gün: Adım 2 uygulandı, §8–§10)  **Model:** Fable 5.1  **Plan:** `docs/plans/BELIRSIZLIK_PLAN.md` (onay + 6 SORU cevabı, 07.10.2026)  **Dal:** `feat/belirsizlik` (`main` @ `eab24d0` üzerinden)  **Bayrak:** `ASSIST_MODE` — ölçüm sonrası canlıda **kapalı**.

## 1. Adım 2 — kodla belirsizlik tespiti, LLM'siz kuru koşu (kota 0)

Script (scratchpad, repoya alınmadı): 80 sorunun her biri için `ask_as_user`'ın yetkili kümesinde `question_terms` → `unmatched_terms` → `specific_matched_terms`; FTS ile `retrieval_top_k` parça; sinyal **(i) kapsamsız soru**, sinyal **(ii) yayılma** (ilk N parçada ≥2 *grup*; grup = proje + belge türü, sürüm zinciri tek grup; ikinci grubun en iyi parçası birincinin ≥ `CLOSE` katı). Ateşlenme = (i) ∧ (ii). Beklenen: yalnızca `ambiguous` kategorisinde.

| Varyant | (i) tanımı | N / CLOSE | Ateşlendi | Doğru (5 belirsiz) | Yanlış pozitif | Yanlış negatif |
|---|---|---|---|---|---|---|
| V1 | `specific_matched_terms` **boş** ∧ proje kelimesi yok ∧ liste kelimesi yok | 10 / 0.85 | 0 | 0 | 0 | 5 — "Sözleşmenin", "DSCR", "tadil", "Lisans", "Toplantıda/karar" ADR-027'nin "ayırt edici" ölçütünü geçiyor (≤ limit belgede geçiyorlar) |
| V2 | ayırt edici terimlerin **hepsi belge-sınıfı kelimesi** (sözleşme, rapor, lisans, toplantı, tadil, karar, belge, poliçe, tutanak, mektup, dscr, değer) ∧ proje/liste kelimesi yok | 10 / 0.85 | 2 | GEN-AMB-001, GEN-AMB-004 | 0 | 3 — AMB-002/003/005: parçalar 2–3 gruba yayılıyor ama ikinci grup ilkinin %85'ine ulaşmıyor |
| V3 | V2 ile aynı | 15 / 0.5 | 6 | **5/5** | **1** — ANK-MIX-001 (`mixed`: "güncel DSCR" sözleşme eşiği + gerçekleşen) | 0 |

Okuma: (i) tek başına 76 sorunun 6'sında ✓ (5 belirsiz + ANK-MIX-001); belirsizliği ayıran asıl sinyal **belge-sınıfı kelimesi dışında ayırt edici terim olmaması**. (ii) eşiği gevşetilince tek yanlış pozitif bir MIXED soru — router onu zaten MIXED sayıyor (sözleşme eşiği + gerçekleşen değer), yani kod tespiti **yalnızca DOCUMENT_QUERY yolunda** çalıştırılırsa V3 bu kümede 5/5 doğru, 0 yanlış pozitif olur. Sınır: 80 soruluk küme; belge-sınıfı listesi elle. **Uygulanmadı** (Naci cevap 6: eksen adlı soru fikri Adım 2 raporunda değerlendirilir, şimdi uygulanmaz) — §6'da değerlendirme.

## 2. Adım 1 — kural 12 (yalnızca `SYSTEM_PROMPT_ASSIST`)

Son metin (`backend/app/services/answer_prompt.py::_RULE_12_ASSIST`, `docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md`):

> 12. Soru hangi belgeyi, projeyi ya da raporu kastettiğini söylemiyorsa ve kaynaklar birbirinden FARKLI belgelere, projelere ya da rapor dönemlerine ait farklı değerler içeriyorsa, bunlardan birini seçme ve hepsini sıralama: 2. kuraldaki cümleyi yaz ve 11. kurala göre tek bir SORU: satırıyla hangisinin kastedildiğini sor. Birden fazla aday olduğunu fark ettiysen bunu açıklayıp adayları listeleme; yalnızca sabit cümle ve SORU: satırı. Kaynakların farklı projelere ait olması, soru projeleri adıyla saymıyorsa, belirsizliktir ve soru sorulur. Bu kural şu durumlarda UYGULANMAZ: (a) aynı belgenin sürüm zinciri (Zincir: satırı aynı belge ailesini gösteriyorsa) belirsizlik değildir — 5. kural geçerlidir ve "güncel", "ilk", "son", "orijinal" gibi kelimeler o zincir içinde kapsamı belirler; kaynaklarda birden fazla ayrı belge ailesi (örneğin farklı türde iki tadil zinciri) varsa "son" tek başına kapsam vermez ve soru sorulur; (b) soru proje adı, belge adı veya dönem veriyorsa; (c) kullanıcı "tüm", "hepsi", "listele" gibi bir ifadeyle hepsini istiyorsa; (d) soru 10. kuraldaki gibi birden fazla projeyi ADIYLA sayıyorsa. 9. kural (aynı terimin farklı tanımları) bu kuraldan etkilenmez.

Naci'nin eklemeleri: (a) sürüm zinciri + güncel/ilk/son kapsam verir ✓; (b) tüm/hepsi/listele ✓ (madde c); (c) "farklı dönemler" → **"rapor dönemleri"**ne daraltıldı (sürüm zincirini kapsamaz; madde a bunu ayrıca dışlar). Metin, A ölçümünden sonra bir kez revize edildi (§4). Bayrak kapalı `SYSTEM_PROMPT` **değişmedi** (`test_rule_12_asks_one_question_on_ambiguity_only_in_the_assist_prompt`: `"\n12. " not in SYSTEM_PROMPT`). Kod değişikliği yok: model sabit cümle + `SORU:` yazınca mevcut hat (`is_no_answer` → `build_insufficient_assist` → `validate_question`) `clarify` üretiyor.

## 3. Eval seti (v6, 80 soru)

| ID | Soru | Kullanıcı | Beklenen | Değer kontrolü |
|---|---|---|---|---|
| ANK-NEG-003 | Kredi sözleşmesinin vadesi kaç yıl? | finans | cevap (`tenor_years.current` = 14 yıl), assist yok | `14 yıl` (ANK-NEG-001 deseni) |
| ANK-NEG-004 | Üretim lisansı ne zaman alındı? | enerji | cevap 15.06.2020, assist yok | `15.06.2020` |
| CO-NEG-005 | Denetim komitesi üyeleri hangi kararla atandı? | yonetim | cevap, kaynak DOC-CO-ADM-008 | `01.03.2022` (`company.documents[7].effective_date` — belgenin key_facts'ı yok; liste sırası değişirse yol güncellenmeli). **Referans koşusunda** model kararı doğru belgeyle aktardı ama tarihi yazmadı → değer kontrolü düştü; öneri: `expected_answer` yerine kaynak + cevap ölçütü (skip) — Naci onayı bekliyor |
| GEN-AMB-003-F | Son tadil neyi değiştirdi? | finans | cevap (tek tadil zinciri), kaynak Facility Agreement Amendment 02 | atlanır (`facility_chain` listesi → skip), ölçüt kaynak + cevap |

`ledger_schema.Question.id` deseni `CO-` önekine ve `-X` son ekine açıldı; `validate-ledger` 0 hata; `test_eval_lib` 80/v6.

## 4. Ölçüm (flash-lite, 26 sn aralık)

Kota kontrolü: tek `/api/ask` 200 (2,0 s). **Referans (bayrak KAPALI, 73 soru × 1 = ambiguous 5 + cevap beklenen 60 + %100-kategorisi cevapsız 8):** `results/gemini-3.5-flash-lite_2026-10-07/` — G1–G3 **73/73**; belirsiz 5'in **5'i cevaplandı** (0 netleştirme — bugünkü davranış); cevaplanma/kaynak kayıpları bu turdan bağımsız model değişkenliği (temporal 7/11, document 30/36, data 3/4, comparison 2/3 — ör. ANK-DEV-004/FIN-005/IZM-DEV-005/006/011/OPS-004 cevapsız kaldı, GEN-CMP-003 eksik kaynak), B/C karşılaştırmasında satır satır referans.

**A — kural 12 ilk metin (bayrak AÇIK, 5 × 3):** `consistency_193918` — **clarify 8/15**, G1–G3 15/15 → eşik (≥ 12) altında, zincir otomatik durdu.

| Soru | r1 | r2 | r3 | Not |
|---|---|---|---|---|
| GEN-AMB-001 | clarify | clarify | clarify | 3/3 netleştirme (2× şablon, 1× model sorusu "Hangi sözleşmenin vadesinin ne zaman dolduğu sorulmaktadır?") |
| GEN-AMB-002 | clarify | clarify | clarify | 3/3 netleştirme (model soruları: "Hangi döneme ait rapordaki DSCR…", "Hangi raporu kastediyorsunuz?") |
| GEN-AMB-003 | cevap | cevap | cevap | 0/3 — model "son tadil"i kural 12-a ile kredi zincirinin son tadili (Amendment 02) saydı; lisans tadili zinciri ikinci aile olduğu hâlde sormadı |
| GEN-AMB-004 | cevap | cevap | cevap | 0/3 — kaynaklar iki projeden gelince kural 12-d'yi (çok projeli soru) uyguladı ve iki projeyi sıraladı (soru proje adı vermiyor) |
| GEN-AMB-005 | clarify | clarify | cevap | 2/3 netleştirme; r3'te "birden fazla karara ilişkin farklı belgeler bulunmaktadır" deyip yine listeledi |

**Tek prompt revizyonu (hak kullanıldı):** (d) "birden fazla projeyi **ADIYLA** sayıyorsa" + "kaynakların farklı projelere ait olması, soru projeleri adıyla saymıyorsa belirsizliktir"; (a)'ya "birden fazla ayrı belge ailesi (örneğin farklı türde iki tadil zinciri) varsa 'son' tek başına kapsam vermez"; "aday çokluğunu fark ettiysen açıklayıp listeleme". Son metin §2'de.

**A2 — revize kural 12 (bayrak AÇIK, 5 × 3):** `consistency_194821` — **clarify 10/15**, G1–G3 **15/15** → eşik (≥ 12/15) hâlâ altında; zincir **durdu**, B/C koşulmadı (Naci: "clarify < 12/15 ise dur ve raporla; tek prompt revizyonu hakkı" — hak kullanıldı, ikinci revizyon yapılmadı).

| Soru | A (ilk metin) | A2 (revize) | A2 model soruları / davranış |
|---|---|---|---|
| GEN-AMB-001 | 3/3 | **3/3** | 3× `CLARIFY_TEMPLATE` (model satırı düştü ya da yazılmadı) |
| GEN-AMB-002 | 3/3 | **3/3** | "Hangi rapordaki/raporun DSCR değerini öğrenmek istiyorsunuz?" |
| GEN-AMB-003 | 0/3 | **0/3** | 3× "Son tadil (Facility Agreement Amendment 02) …" — model "son"u kredi zincirinin son halkası okudu; lisans tadili ailesini rakip aday saymadı |
| GEN-AMB-004 | 0/3 | **1/3** | r3 "Hangi projenin lisansının ne zaman alındığı sorulmaktadır?" ✓; r1 iki projeyi sıraladı, r2 yalnızca Ankara'yı verdi |
| GEN-AMB-005 | 2/3 | **3/3** | "Hangi toplantıda alınan karar(ları) öğrenmek istiyorsunuz?" |

Okuma: revizyon AMB-005'i tamamladı ve AMB-004'te ilk netleştirmeyi getirdi; kalan iki boşluk yapısal: **AMB-003** kural 12-a (sürüm zinciri + "son" kapsam verir — Naci eklemesi) ile beklenti 5 ("yonetim için clarify") arasındaki gerilimdir — model "son tadil"i her seferinde tek zincir içinde çözüyor (TEMPORAL TRUTH'a göre savunulabilir), ikinci aileyi (lisans tadili) belirsizlik olarak görmüyor; **AMB-004** ise kaynaklar iki projeden gelince modelin kural 10 refleksinin (projeleri ayrı cümlelerde ver) kural 12'ye baskın çıkması — prompt kelimesiyle ancak kısmen kırıldı. AMB-003 dışında kalan 4 soruda **10/12 = %83** (eşik üstü). Kuru koşu V3 (§1) tam da bu iki soruda kodla ateşleniyor (AMB-003: 2 grup, AMB-004: 8 grup) → §6.

**Referans (bayrak kapalı) ile fark:** aynı 5 soru bayrak kapalıyken 5/5 cevaplandı (0 netleştirme); bayrak açıkken 10/15 netleştirme, G1–G3 her iki durumda %100. B/C koşulmadığı için aşırı tetiklenme (gerileme) ölçümü **yapılmadı**; negatif kontroller ANK-NEG-003/004, CO-NEG-005, GEN-AMB-003-F yalnızca bayrak kapalı referansta koştu (CO-NEG-005 cevaplandı ama değer "01.03.2022" metinde yok → değer kontrolü kaynak ölçütüne bırakılmalı, aşağıda).

**Durum:** `ASSIST_MODE` canlıda **kapalı**, backend yeniden başlatıldı. Toplam kota: 73 (ref) + 15 (A) + 15 (A2) + 1 (kontrol) = **104 `/api/ask`** (her biri router + cevap).

**Karar Naci'de (Tansu'ya da gidebilir):** (1) GEN-AMB-003'ü `document` (cevap beklenir) saymak — o zaman A2 = 10/12 ≥ %80 ve B/C koşulabilir; ya da (2) kural 12'ye dokunmadan Adım 2 kod tespitini (V3, yalnızca DOCUMENT_QUERY) ikinci katman olarak uygulamak — AMB-003/004'te LLM çağrılmadan şablon soru üretir, ölçüm kuru koşuda 5/5; ya da (3) ikinci bir prompt revizyonu (yeni hak gerektirir). Öneri: (2) — deterministik, kota 0, ADR-014'e en uygun; (1) ile birlikte de yapılabilir.

## 5. Testler
`make test`: backend **552 passed** (15 deselected live_llm; +1 `test_rule_12_asks_one_question_on_ambiguity_only_in_the_assist_prompt`), şema doğrulaması OK, ocr-worker **18 passed**; `make lint` ✅ (ruff + mypy strict + prompt dokümanları güncel — `ANSWER_SYSTEM_PROMPT_ASSIST.md` kural 12 ile yeniden üretildi); `make validate-ledger` 0 hata (v6, 80 soru).

## 6. Adım 2 değerlendirmesi — eksen adlı netleştirme sorusu (uygulanmadı)
Kuru koşu V3, DOCUMENT_QUERY yoluna sınırlanırsa, belirsiz 5 soruda LLM çağrılmadan "Hangi belge: A, B, C?" / "Hangi proje: Ankara RES mi, İzmir RES mi?" şablonları kapıdan gelen adlarla üretilebilir (ADR-014: tüm metin kod; G3: adlar `allowed`'dan). Artı: deterministik, kota 0, modelin "yardım etme" eğiliminden bağımsız. Eksi: belge-sınıfı kelime listesi ve eşikler (N=15, CLOSE=0.5) elle; yeni belge türleri geldiğinde liste bakımı; 80 soruluk kümede 1 MIXED yanlış pozitif (router'la dışlanabilir). Öneri: kural 12 ölçümü yeterli çıkarsa **kodla tespit ikinci katman olarak beklesin**; model kural 12'yi atladığı sorularda (A'da `clarify` olmayan tekrarlar) kod tespitinin ateşlenip ateşlenmediği §4'te karşılaştırılır — ateşleniyorsa iki katman birbirini tamamlar, ayrı plan.

## 7. Kendi aldığım küçük kararlar
| Karar | Neden |
|---|---|
| "farklı dönemler" → "rapor dönemleri" | Naci (c): sürüm zinciri kapsanmasın; covenant raporları dönem bazlı, zincir değil |
| Kural 12'ye (d) "10. kuraldaki gibi birden fazla proje" istisnası | Ü-3 karşılaştırmaları (GEN-CMP) iki projeden parça getirir; sıralama orada zorunlu |
| `Question.id` deseni genişletildi | Naci'nin verdiği id'ler (`CO-NEG-005`, `GEN-AMB-003-F`) eski desene uymuyordu |
| CO-NEG-005 değer kontrolü belge yürürlük tarihi | ADM-008'in key_facts'ı yok; asıl ölçüt kaynak + cevap |
| Kuru koşu scripti repoya alınmadı | Adım 2 uygulanmadı; rapor §1 sonuçları taşıyor |

---

## 8. Adım 2 uygulandı — kodla belirsizlik tespiti (Naci, 07.10.2026 ikinci tur)

Naci kararları: kural 12 **dalda kalır, `main`'e alınmaz** (B/C ölçülmedi); GEN-AMB-003 beklentisi `clarify` kalır; yeni prompt revizyonu yok; Adım 2 (V3) uygulanır.

- **Kod:** `app/services/ambiguity.py` — `detect(session, allowed, question, chunks, documents)`: sinyal (i) kapsamsız soru (ayırt edici terimlerin hepsi belge-sınıfı kelimesi; proje kelimesi yok; "tüm/hepsi/listele" yok; **istisna (b): soru bir adayın belge türünü ya da başlığını adıyla içeriyorsa kapsam verilmiştir**), sinyal (ii) yayılma (ilk 15 parçada ≥ 2 grup = proje + belge türü, ikinci grubun en iyi parçası ≥ 0,5 × birinci). İkisi de tutarsa LLM **çağrılmaz**: `answer` sabit cümle, `assist.kind=clarify`, `assist.axis=project|document`, `question` sabit şablon — `PROJECT_TEMPLATE` "Hangi projeyi kastediyorsunuz: A mi, B mi?" (proje adları yalnızca getirilen belgelerin projeleri) / `DOCUMENT_TEMPLATE` "Hangi belgeyi kastediyorsunuz: X; Y; Z?" (≤ 3 başlık, yalnızca getirilen = yetkili belgeler); `available` = grup temsilcileri (en iyi sayfa). Tüm metin kod (ADR-014); adlar `allowed_document_ids` kümesinin alt kümesinden (G3).
- **Yol kısıtı:** `ask_router._run` → `answer_question(..., check_ambiguity=query_type == "DOCUMENT_QUERY")`; MIXED/DATA ve DATA→DOCUMENT geri düşüşünde kontrol yok. `ASSIST_MODE` kapalıyken `check_ambiguity` okunmaz → bayt-identik (`test_flag_off_is_byte_identical`).
- **Audit:** mevcut `audit_log.assist` JSON'u (`kind`, `question`, `axis`, `available`); `model=None`, `tokens 0` (yalnızca router çağrısı yapılmış olur).
- **Eşik notu (Naci 2):** `TOP_N=15`, `CLOSE=0.5` ve belge-sınıfı kelime listesi **tek kümeye** (`questions.json` v6'nın 5 `ambiguous` sorusu) göre ayarlandı; bu turda değiştirilmedi. Tek ekleme eşik değil, planın (b) istisnasının belge-türü yarısı: kuru koşuda ANK-NEG-004 ("Üretim lisansı ne zaman alındı?") ateşlendi çünkü "lisansı" sınıf kelimesi — soru adayın türünü ("Üretim Lisansı") adıyla söylüyor → `_names_a_candidate` ile dışlandı (test: `test_naming_the_document_type_is_scope`). Held-out seti gelince eşikler yeniden değerlendirilmez, yalnızca ölçülür.
- **Testler:** `backend/tests/test_ambiguity.py` 9 test — iki projeli kapsamsız soru → LLM 0 çağrı + proje şablonu + audit; proje adı verilen → ateşlenmez; "tüm" → ateşlenmez; tek grup (sürüm zinciri) → ateşlenmez; iki belge ailesi tek projede → belge şablonu; MIXED → kontrol yok; bayrak kapalı → bayt-identik; adlar yalnızca getirilen belgelerden (G3); belge türünü adlandıran soru → ateşlenmez.

## 9. Kuru koşu — 80 soru (Naci 3) → `docs/reports/DRY_RUN_AMBIGUITY_2026-10-07.md`

**Sonuç: ateşlenen 6 = 5 belirsiz (5/5) + ANK-MIX-001 (router MIXED → yolda dışlanır); yanlış pozitif 0, yanlış negatif 0.** Özellikle kontrol edilenler (hepsi **ateşlenmedi**):

| Soru | Not |
|---|---|
| GEN-AMB-003-F (finans) | tek grup (yalnızca kredi tadili zinciri görünür) → ateşlenmez; aynı soru `yonetim` ile 7 grup → "Hangi projeyi…" |
| ANK-NEG-001, ANK-NEG-002 | "Ankara RES" proje kelimesi → kapsam var |
| ANK-NEG-003 "Kredi sözleşmesinin vadesi kaç yıl?" | kapsamsız ✓ ama 2 grup ve ikinci grup < 0,5 × birinci → yayılma yok |
| ANK-NEG-004 "Üretim lisansı ne zaman alındı?" | 11 grup, sınıf kelimesi ✓ → **(b) istisnası**: "üretim lisansı" bir adayın belge türü |
| CO-NEG-005 | "denetim komitesi" ayırt edici (sınıf dışı) terim → kapsam var |
| GEN-CMP-001…003 | "Ankara RES"/"İzmir RES" proje kelimeleri → kapsam var |
| ANK-FIN-001…015 (tümü), temporal kategori (ANK-DEV-004/005, ANK-FIN-006/007/008/012/013, ANK-OPS-001/004, ANK-EPC-004, IZM-DEV-011) | proje adı ya da ayırt edici terim var → ateşlenmez |

Ateşlenenlerin gerekçesi (tam tablo ekte): GEN-AMB-001 8 grup → belge şablonu; GEN-AMB-002 2 grup (Facility Agreement; Covenant Report Q4 2024) → belge şablonu; GEN-AMB-003 7 grup, iki proje → **proje şablonu** ("kredi tadili mi lisans tadili mi" yerine proje ekseni seçildi — eksen seçimi "≥ 2 proje → proje" kuralıyla; Tansu'ya gösterilecek nokta); GEN-AMB-004 11 grup → proje şablonu; GEN-AMB-005 5 grup → belge şablonu (Denetim Komitesi Ataması; ÇED Olumlu Kararı; …).

## 10. Held-out hazırlığı (Naci 4), canlı doğrulama (Naci 5), CO-NEG-005 (Naci 6)

- **Held-out:** `questions.json`'a üst düzey `"held_out": []` bloğu eklendi; `ledger_schema.QuestionSet.held_out: list[Question] = []` (aynı doğrulama kuralları), `run_eval` bu bloğu **hiç okumaz** (canlı ölçüm yok), `scripts/dry_run_ambiguity.py --held-out` kuru koşuya dahil eder. Tansu'nun 10 sorusu gelince: bloğa yaz → `make validate-ledger` → `--held-out` kuru koşu → sonuç raporda; Naci onayıyla `questions` bloğuna taşınır.
- **Canlı doğrulama (bayrak açık, ×1, 2 çağrı):** `make eval EVAL_ARGS="--ids GEN-AMB-003,GEN-AMB-004"` → ikisi de `answered=false`, `assist.kind=clarify`, `question="Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi?"`, `model=gemini-3.5-flash-lite` ile `tokens_in≈774` = **yalnızca router çağrısı** (cevap modeli çağrılmadı), G1–G3 2/2 ✅; `results/gemini-3.5-flash-lite_2026-10-07/`. Ardından `ASSIST_MODE=false` + `make restart-backend`. B/C tam ölçümü yapılmadı (Naci 5: tespit LLM'den önce, yanlış pozitifler kuru koşuda görülür).
- **CO-NEG-005 değer kontrolü kaldırıldı (gerekçe):** soru "hangi kararla atandı?" — bir **karar adı** sorar, tarih değil; referans koşusunda model doğru belgeyle (DOC-CO-ADM-008) cevapladı ama "01.03.2022"yi yazmadı → tarih ölçütü soruyla uyumsuz bir ret üretirdi. `expected_answer` artık `ledger:company.documents[7].id` (DOC-* referansı → `ExpectedValue.skip=True`, eval_lib'in belgelenmiş deseni: "a DOC-* document reference already covered by required_sources"); ölçüt = `required_sources` ("Yönetim Kurulu Kararı — Denetim Komitesi Ataması") + `answered`. Not: `documents[7]` liste indeksidir; belge sırası değişirse yol güncellenmeli (notes'ta).

## 11. Durum (ikinci tur sonu; §13 ile güncellendi — kural 12 sonra daldan çıkarıldı)
Dal `feat/belirsizlik`: kural 12 (ölçülmemiş, dalda) + Adım 2 kod tespiti (kuru koşu 5/5, 0 yanlış pozitif; canlı 2/2). `main`'e **alınmadı**. `ASSIST_MODE` canlıda **kapalı**, backend yeniden başlatıldı. Testler §12.

## 12. Testler (ikinci tur)
`make test`: backend **561 passed** (15 deselected live_llm; +9 `test_ambiguity.py`), şema doğrulaması OK, ocr-worker **18 passed**; `make lint` ✅ (ruff + mypy strict + prompt dokümanları); `make validate-ledger` 0 hata (v6 + `held_out`).

---

## 13. Üçüncü tur (07.10.2026, Naci: netleştir ve göster, birleştirme yok)

**1. Held-out 10 soru (HO-AMB-01..05, HO-NEG-01..05):** kuru koşu **çalıştırılmadı — sorular elimde yok.** Repoda (`questions.json` `held_out: []`), uzak dalda, `docs/` altında ve bu oturumun bağlamında bu id'lerle bir taslak bulunmuyor; bu oturumda böyle bir taslak üretilmedi ya da onaylanmadı. Uydurmadım. Sorular (metin, `ask_as_user`, niyet: belirsiz / net) verilir ya da `held_out` bloğuna yazılırsa: `make validate-ledger` → `scripts/dry_run_ambiguity.py --held-out` → tablo (kullanıcının görebildiği belge sayısı, grup/parça dağılımı, niyet tuttu mu, V3 ateşledi mi; HO-NEG'de ateşlenen varsa ayrıca liste). Eşikler bu sonuçlara göre değiştirilmeyecek.

**2. GEN-AMB-003 — "Ankara RES" cevabı belirsizliği çözmüyor (bilinen sınırlama, düzeltme yapılmadı).** LLM'siz kontrol (`yonetim`, aynı kapı): "Son tadil neyi değiştirdi?" → 7 grup, Ankara'da iki tadil ailesi (Licence Amendment 01 rank 0,4; Facility Agreement Amendment 02 rank 0,2) + İzmir → V3 **proje** eksenini seçiyor ("Ankara RES mi, İzmir RES mi?"). Kullanıcı "Ankara RES" deyip "Ankara RES son tadil neyi değiştirdi?" diye sorarsa: 8 grup, iki Ankara tadil ailesi hâlâ yan yana (0,8 / 0,4, yani CLOSE eşiğini geçiyor) ama **proje kelimesi kapsam sayıldığı için detektör ateşlenmez** → soru modele gider, model bugünkü gibi birini (kredi tadili) seçer. Nedenleri: (a) eksen seçimi "≥ 2 proje → proje" kuralı; belge ekseni ikinci sırada kalıyor; (b) proje kelimesi varsa (i) sinyali kapanıyor — proje içi belge-türü belirsizliği görülmüyor; (c) çok turlu hafıza yok (T9), ikinci soru bağımsız değerlendiriliyor. Sonuç: tek proje içinde birden fazla belge ailesi varken proje ekseni **yetersiz** bir netleştirme olabilir. Olası düzeltmeler (yapılmadı, karar Naci/Tansu'da): proje verilmişken de belge-türü yayılmasını kontrol etmek (eşik değil, (i) sinyalinin kapsamı) ya da eksen seçiminde belge ekseninin önceliği. GEN-AMB-003'ün diğer dört belirsiz sorudan farkı budur: AMB-004'te proje cevabı yeterli (projede tek lisans belgesi), AMB-001/002/005'te belge ekseni zaten seçiliyor.

**3. Kural 12 daldan çıkarıldı** (gerekçe: V3 ile aynı işi yapan, aşırı tetiklenmesi ölçülmemiş ikinci mekanizma): `answer_prompt.py` kural 12 öncesi hâline döndü (`git diff 406251e~1 -- backend/app/services/answer_prompt.py` boş), `SYSTEM_PROMPT_ASSIST` = kural 1–7, 8', 9–10, 11; `docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md` yeniden üretildi (12 yok), `test_rule_12_…` silindi, Makefile başlığı "11 yenidir"e döndü. Kural 12'nin metni ve ölçümü (A 8/15, A2 10/15) git geçmişinde (`406251e`) ve bu raporun §2/§4'ünde kalır. Testler §14.

**4. Dalın durumu (birleştirme Naci onayı bekliyor):** `feat/belirsizlik` = Adım 2 kod tespiti (bayrak arkasında, DOCUMENT_QUERY) + eval v6 (80 soru, 4 negatif kontrol, `held_out` bloğu) + `dry_run_ambiguity.py` + dokümanlar. Kural 12 yok. `ASSIST_MODE` canlıda kapalı.

## 14. Testler (üçüncü tur)
`make test`: backend **560 passed** (15 deselected live_llm; kural 12 testi silindi), şema doğrulaması OK, ocr-worker **18 passed**; `make lint` ✅ (prompt dokümanları güncel, 12 yok).

---

## 15. Held-out kuru koşu — Tansu'nun 10 sorusu (08.10.2026; LLM'siz, canlı çağrı yok, eşikler değiştirilmedi)

Sorular `questions.json` → `held_out` bloğuna yazıldı (`Question.id` deseni `HO-`/2 hane için açıldı; `run_eval` bu bloğu okumaz; `make validate-ledger` 0 hata). Tam tablo (görülebilen belge, top-15 parça dağılımı, grup, niyet, V3): `docs/reports/DRY_RUN_HELD_OUT_2026-10-08.md`. Özet: **ateşlenen 3 — HO-AMB-01 ✓, HO-AMB-04 ✓, HO-NEG-02 ✗ (yanlış pozitif)**; ateşlenmeyen 7 — HO-AMB-02/03/05 ✗ (yanlış negatif), HO-NEG-01/03/04/05 ✓. Belirsizlerde isabet **2/5**, netlerde **4/5**. 80 soruluk kümeye (5/5, 0 YP) göre belirgin düşüş → eşik ve sınıf-kelime listesi tek kümeye göre ayarlanmıştı (§8 notu doğrulandı).

| Soru | Kullanıcı | Niyet | Görebildiği belge | Grup (top-15) | Niyet tuttu mu | V3 | Neden / öneri (yazılmadı) |
|---|---|---|---|---|---|---|---|
| HO-AMB-01 "Üretim rakamı ne kadar?" | enerji | belirsiz | 36 | 10 (Production Report ×6 0,50; ÇED, Saha, Yapı Ruhsatı, O&M… ×1 0,30) | ✅ (≥2 aday: aylık üretim raporları) | 🔥 belge: "Aylık Üretim Raporu — Aralık 2023; ÇED Olumlu Kararı; Saha Kullanım Hakkı Sözleşmesi" | ateşlendi ama şablon adayları gürültülü: asıl belirsizlik **hangi ay/rapor** (aynı türün dönemleri) — grup = proje+tür olduğundan dönem ekseni yok; öneri: aynı tür içinde ≥2 belge varsa "dönem/belge" ekseni ve aday listesi aynı türün belgeleri |
| HO-AMB-02 "Kapasite kaç MW?" | enerji | belirsiz | 36 | 8 (Licence Amendment 0,30; Teknik Rapor İzmir 0,20; …) | ✅ (Ankara 48→60 MW, İzmir 80 MW) | – | **YN**: "Kapasite" sınıf kelimesi değil (glossary'de capacity) → (i) kapalı. Öneri: büyüklük/ölçü adları ("kapasite", "üretim", "tutar") için ayrı bir "olgu-sınıfı" listesi ya da glossary-bilinen genel isimleri ayırt edici saymamak |
| HO-AMB-03 "Teknik rapora göre sonuç ne?" | enerji | belirsiz | 36 | 7 (Teknik Rapor İzmir ×6 0,60; Üretim Lisansı 0,50; …) | ✅ (iki İzmir teknik raporu: 06.2024, 01.2025) | – | **YN**: soru belge türünü adıyla veriyor ("Teknik Rapor") → istisna (b) kapsam sayıyor; ama belirsizlik **aynı türün iki belgesi** arasında — tür-içi belirsizlik modelde yok. Öneri: tür adlandırıldığında o türde ≥2 belge varsa belge ekseniyle sor |
| HO-AMB-04 "Karar ne zaman alındı?" | yonetim | belirsiz | 75 | 5 (Board Resolution ×6 0,50; ÇED Kararı 0,40; Shareholder Resolution ×5 0,40) | ✅ | 🔥 belge: "Denetim Komitesi Ataması; ÇED Olumlu Kararı; Kâr Dağıtım Politikası" | isabetli (GEN-AMB-005 ile aynı aile) |
| HO-AMB-05 "Son değişiklik neydi?" | yonetim | belirsiz | 75 | 8 (Facility Agreement ×6 0,20; Change Order ×3 0,20; …) | ✅ (kredi tadilleri, change order, lisans tadili) | – | **YN**: "değişiklik" ayırt edici sayılıyor (Change Order belgeleri) → (i) kapalı. Öneri: "değişiklik/tadil/revizyon" sınıf kelimesi; ayrıca "son" tek başına kapsam vermemeli (GEN-AMB-003 sınırlamasıyla aynı) |
| HO-NEG-01 "Önlisans ne zaman alındı?" | enerji | net | 36 | 12 (Önlisans İzmir ×3 0,30; gürültü ×1 0,10–0,20) | ✅ (tek önlisans belgesi: İzmir; Ankara'nın önlisansı ledger'da tarih ama belge yok) | – | doğru: "Önlisans" belge türü adlandırılmış → (b). Ledger: `izmir_res.project.timeline.pre_licence.date` = **18.01.2024** |
| HO-NEG-02 "Banka hangi DSCR seviyesini şart koşuyor?" | finans | net | 16 | 5 (Facility Agreement ×7 0,50; Drawdown 0,30; Covenant Report 0,30; Waiver 0,30; Account Pledge 0,30) | ⚠️ | 🔥 **yanlış pozitif** — belge: "Facility Agreement; Drawdown Notice; Covenant Report Q2 2026" | "dscr" ve "değer" V2'de sınıf kelimesi sayıldı (GEN-AMB-002'yi ateşlemek için) — "banka/şart/seviye" ayırt edici değil → (i) açık; Covenant Report ve Drawdown 0,30 ≥ 0,25 → (ii) açık. Öneri: "dscr" bir belge sınıfı değil, olgu terimi — listeden çıkarılmalı (GEN-AMB-002 o zaman "rapor" ile yine ateşlenir, doğrulanmalı). Ledger: `ankara_res.project.finance.dscr_covenant` = **1,25x → 1,20x** (Amendment 01) |
| HO-NEG-03 "Anahtar teslim müteahhit kim?" | enerji | net | 36 | **0 parça** | ✅ (tespit değil; retrieval boş) | – | Retrieval hiçbir parça getirmedi: "anahtar teslim" / "müteahhit" korpusta yok (belgeler İngilizce "EPC Contractor"). Canlıda cevap: sıfır parça → sabit cümle (+ bayrak açıksa `term_mismatch`). Öneri: glossary "anahtar teslim → EPC/turnkey", "müteahhit → contractor" (ADR-020 yolu), tespitle ilgisiz. Ledger: `ankara_res.project.construction.epc_contractor.value` = **JKL İnşaat A.Ş.** (eval değer kontrolü metin türü → skip) |
| HO-NEG-04 "Hisse devri hangi oranda?" | yonetim | net | 75 | 2 (Shareholder Resolution 0,20; Maintenance Report 0,10) | ✅ (tek aday: Pay Sahipleri Kararı — GHI) | – | "Hisse" ayırt edici → (i) kapalı. Ledger: `company.spvs[0].shareholders[1].share_pct.value` = **20** (%20; belgede "yüzde 20"; eval değer kontrolü int → skip, ANK-COR-001 gibi) |
| HO-NEG-05 "ÇED süreci hangi aşamada?" | enerji | net | 36 | 10 (Bağlantı Görüşü 0,50; ÇED Durum Yazısı ×3 0,50; Arazi Edinim 0,40; …) | ✅ | – | "ÇED" ayırt edici → (i) kapalı. Ledger: `izmir_res.project.development.ced_status.value` = **ongoing → "devam ediyor"** |

**Okuma:** V3'ün iki zayıf noktası held-out'ta ortaya çıktı: (1) **sınıf-kelime listesi elle ve dar** — "kapasite", "değişiklik" yokken "dscr/değer" var (AMB-02/05 kaçtı, NEG-02 yanlış ateşlendi); (2) **grup = proje + belge türü**: aynı türün dönem/sürüm belgeleri arasındaki belirsizlik (AMB-01 asıl ekseni, AMB-03) görülmüyor, tür adlandırılınca (b) istisnası tamamen kapatıyor. HO-NEG-03 tespitle değil retrieval/glossary ile ilgili. Hiçbir eşik, liste ya da kod değiştirilmedi; öneriler yukarıda, karar Naci/Tansu'da. Canlı çağrı yapılmadı.

---

## 16. Birleştirme kararı (Naci, 08.10.2026)
- V3 kodla tespit `main`'e **girmedi**: held-out'ta belirsizlerde 2/5, netlerde 1 yanlış alarm (HO-NEG-02); dal `feat/belirsizlik` @ `7a6eaf5` etiketlendi (`ambiguity-v3-unmerged`), silinmedi.
- Kriterler gevşetilmedi: eşikler, sınıf-kelime listesi ve `clarify ≥ 12/15` kapısı değiştirilmedi.
- Belirsiz soru davranışı şimdilik şu kadarıyla sınırlı: prompt kuralı 12 denemesi (ölçüm 10/15, yalnızca git geçmişinde) + Tansu'nun (a) kararı (netleştirme sor) + `main`'deki ADR-027 hattı (cevap verilemeyince `clarify`). `chore/eval-v6-heldout` dalı yalnızca eval v6 + `held_out` + kuru koşu scripti (main'de `ambiguity.py` olmadığı için mesajla çıkar) + raporlar + glossary ("anahtar teslim", "müteahhit") taşır.
