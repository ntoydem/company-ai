# Rapor — Belirsiz sorularda netleştirme (Tansu kararı (a); kural 12 + kodla tespitin kuru koşusu)

**Tarih:** 07.10.2026  **Model:** Fable 5.1  **Plan:** `docs/plans/BELIRSIZLIK_PLAN.md` (onay + 6 SORU cevabı, 07.10.2026)  **Dal:** `feat/belirsizlik` (`main` @ `eab24d0` üzerinden)  **Bayrak:** `ASSIST_MODE` — ölçüm sonrası canlıda **kapalı**.

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
