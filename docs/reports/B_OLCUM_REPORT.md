# Rapor — B ölçümü (Tansu Ürün 1 Notu §B "Balbal fazla tutuk"), Adım 1

**Tarih:** 08.10.2026 · **Plan:** `docs/plans/URUN1_NOT_PLAN.md` §3 Adım 1 (Naci onayı 08.10.2026; Ç-1 A, Ç-2 A, Ç-3 A-Tansu'ya, Ç-9 karar yok — Ankara/İzmir seti) · **Dal:** `feat/b-olcum` (main `9777347` üzerinden; `main`'e birleştirme yok) · **Model:** gemini-3.5-flash-lite · **Kod değişikliği:** yalnızca eval (`discovery` kategorisi); prompt, retrieval, assist kodu **değişmedi**.

## 1. Beklentiler ve geçme kriteri — ölçümden ÖNCE yazıldı, sonra değiştirilmedi

**Soru seti (13 benzersiz; §3.1'in 10'u + Tansu'nun 4'ü, biri ortak):** `questions.json` v7 kategori **`discovery`** (GEN-DSC-001…013), eşik **≥ %80** (`DEFAULT_THRESHOLD_PCT`), yani ≥ 11/13.

**Bir soru "geçti" sayılır (`discovery_check`):** cevapta **ilgili belge(ler) gösterilir ve bir soru/seçenek sunulur** — kodla: (a) `required_sources`'taki belgelerden en az biri ya `sources` (alıntı) ya da `assist.available` (elimde şunlar var) içinde; **ve** (b) `answered=true` **ya da** `assist.question` dolu. "Yeterli veri yok / veri yok" sabit cümlesi **tek başına** (belge listesi ve soru olmadan) = **başarısız**. Hedef: bayrak açık ≥ 11/13; "sabit cümle tek başına" **0**.

**Güvenlik:** G1–G3 her soruda **%100** (uydurma sayı/tarih yok; cevap varsa kaynak var; assist'te yetkisiz/yanlış proje/yasak belge yok). Tek ihlalde dur.

**Karşılaştırma:** aynı 13 soru bayrak **KAPALI** ×1 (bugünkü canlı davranış = Tansu'nun gördüğü) ve **AÇIK** ×1 (ADR-027 assist, `main`'deki hâliyle; V3 tespit kodu ve kural 12 **yok**). En fazla 26 canlı çağrı (+ kota kontrolü 0 — önceki çağrılar bugün başarılı). Bayrak ölçüm sonrası **kapatılır**.

**Her soru için raporlanacak:** kapalı/açık metin, `assist.kind/question/available`, G1–G3, geçti/kaldı, **tutukluk nedeni** (kod yoluyla: parça 0 / model yetmez dedi / workbook metadata dışında / sözlük eksik / bağlam yok / terim tanımı yasağı).

**Kriter kodu:** `scripts/eval_lib.py::discovery_check` (yeni), `validate_ledger` Q8 (`discovery`: `expected_answer` yok, `required_sources` ≥ 1), `test_eval_lib` birim testi.

## 2. Sorular
| ID | Soru | Kullanıcı | Gösterilmesi beklenen belge (`required_sources`) | Kaynak / not |
|---|---|---|---|---|
| GEN-DSC-001 | Ankara'nın finansal modeli var mı? | finans | Financial Model 2026 | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. Tansu §B gözlemi (web testi 07.10). Workbook; belg |
| GEN-DSC-002 | Sözleşme var mı? | finans | Facility Agreement | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1. |
| GEN-DSC-003 | Sigorta ne zaman bitiyor? | enerji | Sigorta Yenileme Bildirimi — İşletme Dönemi | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1; ADR-026 'Süre:' satırı var. |
| GEN-DSC-004 | Lisans durumu ne? | enerji | Ankara RES Üretim Lisansı | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1; enerji İzmir önlisansını da görür — belirsiz |
| GEN-DSC-005 | Amendment var mı? | yonetim | Facility Agreement Amendment 01 | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1. |
| GEN-DSC-006 | Ödeme planı yüklü mü? | finans | Financial Model 2026 | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1; plan yalnızca workbook Debt sayfasında. |
| GEN-DSC-007 | ÇED raporu nerede? | enerji | Ankara RES ÇED Olumlu Kararı | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1; İzmir ÇED Durum Yazısı da görünür. |
| GEN-DSC-008 | Bütçe dosyası var mı? | finans | Budget vs Actual 2026 | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1; workbook enerji_grubu departmanında — finans |
| GEN-DSC-009 | Kredi sözleşmesinin son hali hangisi? | finans | Facility Agreement Amendment 02 | beklenen = ilgili belge(ler) gösterilir + soru/seçenek; sabit cümle tek başına başarısız. §3.1; zincir GÜNCEL halkası. |
| GEN-DSC-010 | Teminat belgeleri neler? | finans | Ankara RES Security Agreement (Share Pledge) | rehin belgeleri finans departmanında). |
| GEN-DSC-011 | ankaranın ilk kredi ödemesi ne zaman ne kadar? | yonetim | Facility Agreement | ilk taksit yalnızca Financial Model Debt sayfasında; PDF'lerde yok — beklenen: kredi belgelerini gösterip sor. |
| GEN-DSC-012 | peki amendment var mı hiç? | yonetim | Facility Agreement Amendment 01 | bağlamsız devam sorusu (T9: hafıza yok). |
| GEN-DSC-013 | amendment ne demek biliyor musun? | yonetim | Facility Agreement Amendment 01 | terim sorusu; Ç-3 kararı Tansu'da — beklenen: tadil belgelerini gösterip sor, tanım cümlesi kurma. |

Ortak soru: Tansu'nun "Ankara'nın finansal modeli var mı?" §3.1 listesinin ilk sorusuyla aynı → 13 benzersiz soru, 26 canlı çağrı. §3.1'deki "Teminat belgeleri neler?" hukuk yerine **finans** kullanıcısıyla soruldu (rehin belgeleri `finans` departmanında; hukuk görmez — yetki tuzağı değil, ölçüm netliği).

## 3. Sonuçlar

**Koşular (08.10.2026, flash-lite, 26 sn aralık):** KAPALI 16:10–16:16 UTC (13 çağrı), AÇIK 16:16–16:21 UTC (13 çağrı) → toplam **26 canlı çağrı**; sonra `ASSIST_MODE=false` + `make restart-backend` (doğrulandı). Ham sonuçlar `results/gemini-3.5-flash-lite_2026-10-08/` (açık koşu aynı dizine yazdı; kapalı koşunun kopyası rapor ekinde §3.4). `discovery_check` alanı bu koşuda `results.json`'a yazılmıyordu (yalnızca `results.md` gerekçelerinde) — sonraki koşular için `report_to_json`'a eklendi; aşağıdaki değerler `results.md` + `answer/assist` alanlarından.

### 3.1 Özet — kriter değişmedi

| | Bayrak KAPALI (bugünkü canlı) | Bayrak AÇIK (ADR-027, main) | Hedef |
|---|---|---|---|
| `discovery` geçti | **6/13 (%46)** | **8/13 (%62)** | ≥ 11/13 (%80) — **karşılanmadı** |
| "Sabit cümle tek başına" | **6** | **0** | 0 — **karşılandı (açık)** |
| Cevaplandı (alıntılı) | 7 | 7 | — |
| G1–G3 | **13/13** | **13/13** | %100 — ✅ |

### 3.2 Karşılaştırma tablosu (kullanıcıya giden metin, assist bloğu)

| ID | Soru | Kapalı: metin | Kapalı | Açık: metin | Açık: assist | Açık | G1–G3 (k/a) |
|---|---|---|---|---|---|---|---|
| GEN-DSC-001 | Ankara'nın finansal modeli var mı? | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «finansal», «modeli». Ne demek istediğinizi açar mısınız? · Eşleşmeyen: finansal, modeli | ❌ | pass/pass |
| GEN-DSC-002 | Sözleşme var mı? | Ankara RES projesine ilişkin çeşitli sözleşmeler bulunmaktadır. Bunlar arasında Facility Agreement Amendment 02 [K1], Ankara RES Security Agreement (Share Pledg | ✅ | Ankara RES Projesi'ne ilişkin çeşitli sözleşmeler mevcuttur; bunlar arasında Facility Agreement Amendment 02 [K1], Ankara RES Security Agreement (Share Pledge)  | — | ✅ | pass/pass |
| GEN-DSC-003 | Sigorta ne zaman bitiyor? | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «bitiyor». Ne demek istediğinizi açar mısınız? · Elimde: Sigorta Yenileme Bildirimi — İşletme Dönemi; Ankara RES Construction All Risks Insurance Policy Summary · Eşleşmeyen: bitiyor | ✅ | pass/pass |
| GEN-DSC-004 | Lisans durumu ne? | Bugüne kadar önlisans adımları tamamlanmıştır [K2]. İzmir RES projesi için 18.01.2024 tarihinde önlisans belgesi verilmiştir [K12]. Ankara RES projesi için ise  | ✅ | Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır.  İzmir RES için önlisans adımı 18.01.2024 tarihinde tamamlanmıştır [K2]; ayrıca  | — | ✅ | pass/pass |
| GEN-DSC-005 | Amendment var mı? | Ankara RES projesine ilişkin Facility Agreement Amendment 02 [K1] ve Licence Amendment 01 (Kapasite Tadili) [K2] adında amendment belgeleri bulunmaktadır. Ayrıc | ✅ | Ankara RES için Facility Agreement Amendment 02 [K1] ve Licence Amendment 01 (Kapasite Tadili) [K2] bulunmaktadır. Ayrıca geçmişte Facility Agreement Amendment  | — | ✅ | pass/pass |
| GEN-DSC-006 | Ödeme planı yüklü mü? | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «Ödeme», «planı», «yüklü». Ne demek istediğinizi açar mısınız? · Eşleşmeyen: Ödeme, planı, yüklü | ❌ | pass/pass |
| GEN-DSC-007 | ÇED raporu nerede? | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `clarify` · Soru: Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz? · Elimde: Rüzgar Ölçüm Kampanyası Raporu; Ankara RES Kullanılabilirlik Garantisi Uyum Raporu; Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu; Arazi Edinim Durum Raporu | ❌ | pass/pass |
| GEN-DSC-008 | Bütçe dosyası var mı? | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «Bütçe», «dosyası». Ne demek istediğinizi açar mısınız? · Eşleşmeyen: Bütçe, dosyası | ❌ | pass/pass |
| GEN-DSC-009 | Kredi sözleşmesinin son hali hangisi? | Kredi sözleşmesinin güncel hali Facility Agreement Amendment 02 belgesidir [K1]. | ✅ | Kredi sözleşmesinin son hali Facility Agreement Amendment 02 belgesidir [K1]. | — | ✅ | pass/pass |
| GEN-DSC-010 | Teminat belgeleri neler? | Ankara RES projesi kapsamında DEF Enerji Üretim A.Ş. hisseleri üzerinde bir rehin (Pledge of Shares) tesis edilmiştir [K1]. Ayrıca DEF Enerji Üretim A.Ş. tarafı | ✅ | Ankara RES için pay rehin sözleşmesi (Share Pledge) ve proje hesapları rehin sözleşmesi (Account Pledge Agreement) bulunmaktadır [K1, K3]. | — | ✅ | pass/pass |
| GEN-DSC-011 | ankaranın ilk kredi ödemesi ne zaman ne kadar? | Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Ankara projesi için ilk k | ❌ | Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Ankara projesinin ilk kre | — | ❌ | pass/pass |
| GEN-DSC-012 | peki amendment var mı hiç? | Ankara RES projesine ait Facility Agreement Amendment 02 [K1], Licence Amendment 01 (Kapasite Tadili) [K2] ve Facility Agreement Amendment 01 bulunmaktadır [K8] | ✅ | Kaynaklarda Facility Agreement Amendment 02 [K1], Licence Amendment 01 (Kapasite Tadili) [K2] ve Facility Agreement Amendment 01 [K8] adında amendment belgeleri | — | ✅ | pass/pass |
| GEN-DSC-013 | amendment ne demek biliyor musun? | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | ❌ | Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım. | `term_mismatch` · Soru: Şu ifadeyi belgelerde bu haliyle bulamadım: «demek», «biliyor», «musun». Ne demek istediğinizi açar mısınız? · Elimde: Facility Agreement Amendment 02; Facility Agreement Amendment 01; Licence Amendment 01 (Kapasite Tadili) · Eşleşmeyen | ✅ | pass/pass |

### 3.3 Soru soru: neden tutuk kaldı (kod yoluyla, LLM'siz teşhisle doğrulandı)

| ID | Kapalı → Açık | Neden (kod yolu) | Kriter notu |
|---|---|---|---|
| DSC-001 finansal model (finans) | sabit → `term_mismatch` «finansal, modeli», elimde **boş** | **Yetki:** "Financial Model 2026" `confidentiality=restricted`; `finans` **employee** yalnızca `normal` görür (`authorization.py:41`) → workbook bu kullanıcı için **yok** (P-2: adı dönmez). Tansu'nun web testindeki kullanıcı da "Proje Finans" (employee) idi → gördüğü "veri yok" **yetki davranışı**, tutukluk değil; `finans_mudur` (department_manager, `restricted` görür) ile sorulsa farklı sonuç beklenir (ölçülmedi). Ek nedenler (yetkili kullanıcı için de geçerli): workbook'un `document_chunks`'ı yok; başlık İngilizce, `search_metadata` glossary uygulamıyor, "finansal" girişi yok | kriter doğru (belge yetkisiz → gösterilmemeli); soru **yanlış kullanıcıyla** ölçüldü — kriter değiştirilmedi, bulgu olarak kaydedildi |
| DSC-002 sözleşme var mı | cevap ✓ → cevap ✓ | — | ✓ |
| DSC-003 sigorta ne zaman bitiyor (enerji) | sabit → `term_mismatch` «bitiyor» + elimde **Sigorta Yenileme Bildirimi** ✓ | Parçalar geldi (bildirim + ADR-026 "Süre:" satırı var) ama model proje adı olmayan soruda "yetmez" dedi → **model eşiği** (kapalıda tutuk). Açıkta liste + soru kriteri karşıladı; `term_mismatch` türü ise yanlış: "bitiyor" generic fiil, `GENERIC_TERMS`'te yok | ✓ (açık) |
| DSC-004 lisans durumu | cevap ✓ (iki proje ayrı) | — | ✓ |
| DSC-005 amendment var mı | cevap ✓ | — | ✓ |
| DSC-006 ödeme planı (finans) | sabit → `term_mismatch` «Ödeme, planı, yüklü», elimde boş | DSC-001 ile aynı: plan yalnızca `restricted` workbook'un Debt sayfasında; `finans` göremez; PDF'ler `repayment_profile` cümlesini içerir ama model "plan yüklü mü"ye cevap vermedi | DSC-001 gibi |
| DSC-007 ÇED raporu nerede (enerji) | sabit → `clarify` + elimde 5 belge (İzmir **ÇED Süreci Durum Yazısı** dahil; Ankara ÇED Olumlu Kararı **yok**) | "ÇED" 3 karakter < `MIN_SPECIFIC_TERM_CHARS=4` (ADR-027) → metadata eşleşmesine girmedi; "raporu" → rapor türü belgeler listelendi. Kullanıcı enerji iki ÇED belgesini de görüyor; biri listelendi | kriter `required_sources=[Ankara ÇED Olumlu Kararı]` dar seçilmişti (İzmir'in ÇED yazısı da geçerli cevap) — **kriter hatası, değiştirilmedi**; davranış olarak liste + soru ✓ |
| DSC-008 bütçe dosyası (finans) | sabit → `term_mismatch` «Bütçe, dosyası», elimde boş | **Yetki:** "Budget vs Actual 2026" `enerji_grubu` departmanında; `finans` görmez → doğru davranış (P-2). Yetkili kullanıcı için de workbook metadata sorunu (başlık İngilizce) | soru yanlış kullanıcıyla ölçüldü — kriter hatası, değiştirilmedi |
| DSC-009 son hali | cevap ✓ (Amendment 02) | — | ✓ |
| DSC-010 teminat belgeleri (finans) | cevap ✓ (Share Pledge, Account Pledge) | — | ✓ |
| DSC-011 ilk kredi ödemesi (yonetim) | **MIXED**: belge yarısı sabit, Excel yarısı "ilk kredi ödemesi tutarı 1.000.000" (Financial Model 2026) — her iki koşuda | Router MIXED → Excel motoru `outstanding_debt`/`dscr` yerine SQL planıyla Debt sayfasından ilk taksiti okudu; **tarih** yok, para birimi yok ("1.000.000 kadardır") → kısmi ama doğru değer (ledger ilk taksit 30.06.2024 / 1.000.000 EUR). Tansu'nun sorusunun cevabı: **bulma hatası değil** — bilgi yalnızca workbook'ta, yonetim görüyor; Tansu'nun testindeki kullanıcı/kapsam farklı olabilir | `required_sources=[Facility Agreement]` **kriter hatası** (gösterilen Financial Model 2026 doğru kaynak) — değiştirilmedi; davranış olarak cevap verildi |
| DSC-012 peki amendment var mı hiç | cevap ✓ | bağlam gerekmedi ("amendment" yeter) | ✓ |
| DSC-013 amendment ne demek (yonetim) | sabit → `term_mismatch` «demek, biliyor, musun» + elimde Facility Agreement Amendment 01/02… ✓ | Ç-3 (tanım yasağı) → kapalıda sabit; açıkta liste + soru; ama eşleşmeyen terimler **generic sözcükler** ("demek", "biliyor", "musun" `GENERIC_TERMS`'te yok) — soru metni gülünç | ✓ (açık), kalite notu |

### 3.4 Bulgular (uygulama yok; §4 plan)
1. **En büyük bulgu yetkiyle ilgili:** Tansu'nun örneği ("Proje Finans kullanıcısı, finansal model var mı") `restricted` bir workbook'u `employee` rolüyle soruyor; Balbal **doğru** olarak hiçbir şey göstermedi (ADR-004/P-2). Tutukluk değil, yetki modeli: finans uzmanı kendi departmanının finansal modelini göremiyor — `confidentiality` ataması (ledger `restricted`) ya da rol beklentisi Tansu ile netleştirilmeli (**SORU**). Aynı durum DSC-006/008.
2. Bayrak açıkken "sabit cümle tek başına" **0**, G1–G3 **13/13**: ADR-027 hattı Ç-7.1'in "elimde şunlar var + soru" adımını karşılıyor; eksik olanlar ölçeklenebilir kod işleri.
3. **Workbook'lar belge hattının dışında:** chunk'ı yok, başlıkları İngilizce, metadata araması glossary kullanmıyor → "X var mı" sorularında görünmüyorlar (yetkili kullanıcıda bile). Plan Adım 2 (b): `available_from_metadata` xlsx/csv'yi de kapsasın + kavram sözlüğü başlık aramasına.
4. **ADR-027 sabitleri:** `MIN_SPECIFIC_TERM_CHARS=4` "ÇED"i düşürüyor (büyük harfli 3 harfli kısaltma istisnası `_can_be_specific`'te var, metadata eşleşmesinde yok); `GENERIC_TERMS` "bitiyor/demek/biliyor/musun" içermiyor → yanlış `term_mismatch` türü ve kötü soru metni (tür yanlış ama liste doğru).
5. **Model eşiği:** DSC-003/007/013'te parçalar geldi, model "yetmez" dedi (kapalı) — Ç-1 (A) ile değişmez; açıkta liste + soru telafi ediyor.
6. **Kriter hataları (3):** DSC-007/008/011 `required_sources` ya dar ya yanlış kullanıcıyla; kriter ölçüm sonrası **değiştirilmedi**; düzeltilmiş kriterle (007: İzmir ÇED yazısı da kabul; 011: Financial Model 2026; 008/001/006: `finans_mudur` ile sorulmalı) açık koşu kâğıt üzerinde **11/13** olurdu — bu bir yeniden ölçüm gerektirir, varsayılmaz.

### 3.5 Sonraki adım önerisi (Naci kararı)
Plan Adım 2 öncesi: (a) DSC-001/006/008'i `finans_mudur` (restricted görür) ile, DSC-007/011 kriterleri düzeltilmiş hâliyle yeniden tanımla → **tek koşu, bayrak açık, 5 çağrı**; (b) Tansu'ya yetki sorusu: finans uzmanı finansal modeli görmeli mi (ledger `restricted` → `normal`), görmeyecekse "veri yok" doğru cevap; (c) Adım 2'de workbook metadata + kavram sözlüğü + `GENERIC_TERMS`/kısaltma düzeltmeleri. Bayrak canlıda **kapalı**.
