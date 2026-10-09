# Ürün 1 — Kararlar ve revize iş sırası (Tansu cevapları, Anayasa v2.1, Ek-F)

**Tarih:** 09.10.2026 · **Durum:** plan **onaylı** (Naci 09.10.2026, §2 ve §7.1); uygulama adım adım ayrı onayla başlar (ilk: adım 1, Soru 15); **kod değişikliği ve canlı çağrı yok** · **Dayanak:** Tansu `docs/NACI_CEVAP_2026-10-08.md` (AI-BalBal PR #13, commit 7615b85), Anayasa v2.1 taslağı (PR #15, ADT-1), Ek-F Karakter Tanımı (PR #16, ADT-2), `NACI_NOTU_URUN1.md` §G (yeniden test), `NACI_NOTU_URUN2.md` §F (yükümlülük bağı) · **Önceki planlar:** `URUN1_NOT_PLAN.md` (§1 boşluklar A–F, §3 sıra, §4 kütüphane maliyeti), `ADIM2_PLAN.md`, `BELIRSIZLIK_PLAN.md` · **Ölçümler:** `B_OLCUM_REPORT.md` (resmi 8/13), `ADIM2_REPORT.md` (8/13, R1 12/14, held-out 4/6), `DRY_RUN_HELD_OUT_2026-10-08.md` (V3 2/5, 1 yanlış alarm).

Kısaltmalar: ADT = Anayasa Değişiklik Talebi; K1–K6 = Tansu'nun yeniden test kategorileri (§G.3); R1 = eval'in 14 soruluk %100 kategorisi (regresyon seti); G1–G3 = güvenlik kontrolleri (uydurma yok, kaynaksız yok, yetkisiz ad yok).

---

## 1. Karar tablosu — PR #14'teki 17 soru

| # | Soru (kod) | Tansu | Bizde ne değişiyor | Nerede |
|---|---|---|---|---|
| 1 | Belirsiz soru (İ-8) | **İki durum.** (1) Gerçek belirsizlik → liste yok, **tek** netleştirme sorusu; seçenekler belge/proje adıyla, linkli olabilir. (2) Zayıf eşleşme / veri yok → linkli liste + "bunu mu kastettiniz?" | Bugünkü assist her zaman "liste + soru" verir → (1) için ayrı yol gerekir (§4). Ek-F F-4 ile aynı. | `assist.py`, `ask_router.py`, `schemas/ask.py` (`assist.kind` yeni değer: `disambiguate`) |
| 2 | Sözlük yeri (İ-7) | **A** admin/parametre tablosu; "belgeden terim" testi tablo verisi üzerinde koşar | Adım 2'deki `CONCEPT_GLOSSARY` + `search_glossary` koddan tabloya taşınır (tablo + admin API + cache; kod sözlüğü seed olur). Sıraya girer (§3 adım 5). | yeni `glossary_terms` tablosu, migration, `/api/admin/glossary` |
| 3 | "Amendment ne demek?" (Ç-3) | **A** | Model cevapsızsa ve soru terimi sözlükte varsa assist metnine "«amendment»'ı tadil olarak anlıyorum" cümlesi (kodla, LLM'siz); kaynaksız tanım yine yok. | `assist.py` (`CLARIFY_TEMPLATE` öncesi tek cümle) |
| 4 | Proje adı geçmeyen soru (yeni) | Doğrudan cevap yok → **Ek-F F-3 cevap sayılır:** projeler ayrı başlık, gruplu liste | `available` listesi proje grubuyla döner (`assist.available[].project`), soru "hangi proje?"; eval'deki "proje karışması" uyarısı gruplu listede **ihlal sayılmaz** (`expected_project=None` kuralı) | `assist.py`, `eval_lib.py` |
| 5 | Finans uzmanı finansal model (Soru 15) | **A** normal sınıf; bordro/dava restricted; P-2 aynen | `DOC-ANK-FIN-008` `restricted → normal` (ledger + reseed yalnızca o satır). Dikkat: "Bütçe dosyası" (`DOC-ANK-OPS-002`) zaten `normal`, ama **departmanı enerji_grubu** → finans göremez; bu Soru 15'in değil klasör/departman kararının konusu (Tansu'ya soru T-3). | `ankara_res.yaml:1227` |
| 6 | Kızılova aşaması (İ-1) | **A** önlisans, 42 MW, EPC yalnız LNTP, kredi imzalı kullandırılmadı | Kütüphane: kullandırım talebi, inşaat ilerleme raporu, CAR/EAR **üretilmez**; §4.1 belge sayısı düşer (~−10) | kütüphane D/E |
| 7 | Akyar (İ-2) | **A** 60 MWp, 03.03.2028 | ledger | D/E |
| 8 | Demirci (İ-3) | **A** 80 MW, 10.10.2027 | ledger | D/E |
| 9 | Personel (İ-4) | **A** §C.1, 36 kişi, 7 unvan düzeltmesi | C.1 hesaplar bu listeden; `DemoUser` Literal | C.1 |
| 10 | İmza (İ-5) | **A** 500.000 TL tek A, üstü A+B | imza sirküleri + ödeme talimatı şablonları | D/E |
| 11 | Demo bugün (İ-6) | **A** 06.10.2026 | `company.yaml demo_today`, `Settings.demo_today`, "bugüne göre" ledger alanları (`outstanding_debt_as_of_demo_today`, `operating_year`), validator F9/F11 — **kütüphaneyle birlikte** | D/E |
| 12 | Eski Ankara/İzmir (Ç-9) | **B** yeniden adlandır; **ledger değerleri §3'e** (Karatepe 24 MW, USD, Garanti 2022-KT; Kızılova önlisans) | Prose'da ad ve **rakamlar token** (`[[project_name]]` 90, `[[capacity_mw]]`, `[[dscr_covenant]]`, `[[total_debt]]`…; düz rakam 0) → mevcut 70 belge **0 LLM** ile yeniden üretilir; değişen: ledger değerleri, para birimi EUR→USD, `document_specs` başlıkları, eval beklentileri (§4.4) | D/E |
| 13 | .eml/.docx/MT940 (Ç-7) | **A** PDF kopya + orijinal ek | yükleme hattı değişmez; generator'a "ek dosya" alanı | D/E |
| 14 | Mevzuat değerleri (Ç-8) | **B** biz webden araştırır öneri listesi sunarız, onlar onaylar | Yeni küçük iş: `docs/notes/MEVZUAT_ONERI.md` (ÇED 90 gün, TEA 180 gün, teminat bedelleri; kaynak linkli); onay gelmeden ledger'a yazılmaz | D/E öncesi, S |
| 15 | Sohbet bağlamı (Ç-2) | **A** istemci tarafı | `AskRequest.previous_question: str \| None` (opsiyonel, audit'e yazılır, prompt'a "önceki soru" olarak girer); sunucu hafızası yok | `schemas/ask.py`, `answer_prompt.py` — prompt değişir → R1 |
| 16 | Ekip sohbeti (Ç-5) | **A** şimdi, Ürün 1; Balbal girmez | kapsam Ürün 1 (Tansu), **sıra bizde** (§2) | `URUN1_NOT_PLAN §5` |
| 17 | Önlisans süreç modeli (Ç-6) | **A** şimdi, Ürün 1 backend; "yetişir mi" Ürün 3 | kapsam Ürün 1 (Tansu), **sıra bizde** (§2) | C.6 |

Ek cevaplar: SORU 8 → §3.1'in 10 sorusu `discovery` olarak eval'e (dev seti, §5); SORU 9 → 2–3 hafta + 2 kota günü kabul, **önce Proje Finans ve Hukuk**, hazır olunca haber; §7.2 açık 2–5 cevaplandı (B-22/3 yönetici izin belgesini görmez; yazışma departman belgesi; bildirim onaycı + yükleyen + klasör müdürü; görüş talebi Ürün 2). Ek-C 1.14: ADT-1 onayı v1.1/v2.0'ı da onaylar.

## 2. Naci kararları (09.10.2026)

| Konu | Karar | Sonuç |
|---|---|---|
| Ç-5 ekip sohbeti, Ç-6 süreç modeli | Kapsam **Ürün 1** (Tansu A; Anayasa v2.1 Ü-3 genişlemesiyle uyumlu). **Sıra bizde.** | §3'te (f) ve (g); ilk kör test turundan sonra (SORU 7) |
| Ç-8 | **B** | Mevzuat öneri notu, onaydan sonra ledger |
| İ-7 | **A** sözlük admin tablosu, **sıraya koy** | §3 adım (e); Adım 2 kod sözlüğü seed verisi olur |
| Ç-9 | **B**, ama ledger değerleri `NACI_CEVAP §3`'e göre | Yeniden adlandırma + değer güncellemesi tek iş; eval beklentileri değerle birlikte yenilenir |

**§7.1 cevapları (Naci, 09.10.2026):**

| SORU | Karar | Sonuç |
|---|---|---|
| 1 Sıra | **A** | §3.2 revize sıra geçerli |
| 2 Ölçüm seti | **A** | Adım 1–4 eski Ankara/İzmir setinde "geçiş değeri"; tam ölçüm kütüphane sonrası |
| 3 ASSIST_MODE | **A** (adım 2 yeşilse) | Canlıda varsayılan açık, bayrak bir tur daha kalır, kör test turu 1 sonrası kaldırılır |
| 4 Belirsizlik | **A** | Yalnız proje ekseni, kodla; LLM sınıflandırması şimdi yok |
| 5 Held-out | **A** | Held-out sorularını Naci/danışman yazar; geliştirici AI ölçüm gününe kadar görmez; kullanılan set yanar |
| 6 K3 Çelişkili Veri | **A** | Adım 7 kör testten önce zorunlu |
| 7 (f)/(g) | **A** | Ekip sohbeti ve süreç modeli kör test turu 1 sonrası |
| 8 Ölçüm kaydı | **A** | İki yeni tablo + reask sezgisi; **yalnız toplu admin görünümü, kişi bazında rapor yok** |
| 9 ADT-1/ADT-2 | **A** | Naci PR #15 ve #16'yı GitHub'da onayladı (09.10.2026); Anayasa v2.1 ve Ek-F yürürlük Tansu'nun birleştirmesiyle |

## 3. Revize sıra

### 3.1 Naci'nin önerisi ve eleştiri

Naci: (a) Ek-F davranışı → (b) Soru 15 → (c) kütüphane D/E → (d) C.4/C.3/C.1 → (e) sözlük tablosu → (f) ekip sohbeti → (g) süreç modeli.

**Eski sette mi, yeni sette mi ölçmek?** Bugünkü eval (98 soru + 16 held-out, G1–G3 kontrolleri, R1 regresyon) **yalnızca eski sette** çalışır; (c) bittiğinde `expected_project`, `ask_as_user`, `required_sources`, ledger yolları yeniden yazılır (§4.4) ve her şey **bir kez daha** ölçülür (~1 kota günü, zaten planlı). Buna rağmen (a) ve (b)'yi eski sette ölçmek doğru:
- (a) tutukluğun kaynağı (Tansu) ve S–M büyüklükte; (c) L (2–3 hafta). Davranışı 3 hafta ölçmeden bırakmak, (c) bitince iki bilinmeyeni (yeni veri + yeni davranış) aynı anda ölçmek demek; regresyon ayrıştırılamaz.
- Eski set için kontrol altyapısı hazır: G1–G3, R1 14, discovery 13, 4 negatif kontrol. Yeni sette bunlar yok.
- Maliyet: ~31 çağrı (R1 14 + discovery 13 + 4 negatif) — bir kota saatinden az.
- **Sınır:** eski sette ölçülen rakam (örn. discovery 8/13 → ?) yeni sette aynı kalmaz; rapor "eski set, geçiş değeri" der; **resmi** Ürün 1 kabulü Tansu'nun kör testidir (§5).

**Sıra eleştirisi:**
1. **(b) (a)'dan önce** ve ayrı ölçülmeli: tek satırlık ledger değişikliği, 0 LLM, discovery DSC-001/006'nın ölçülebilir olmasını sağlar. (a) ile birleştirilirse (a)'nın etkisi karışır. ("Bütçe" DSC-008 Soru 15'le düzelmez, departman konusu — T-3.)
2. **(a) iki parça:** (a1) Ek-F F-3/F-5/F-8 metin/biçim (prompt + sabit cümle + liste) ve (a2) F-4 "gerçek belirsizlik" ayrımı. (a2) V3'ün çöktüğü yer; (a1)'i bekletmemeli. (a2) §4'teki daraltılmış tanımla ayrı adım.
3. **(d)'nin içi sıralı değil, bağımlı:** C.4 etiketler proje adlarına bağlı → **(c) ile aynı anda** (yeniden adlandırma sırasında katalog değişir; ayrı yapılırsa iki reseed). C.3 yükleme önerisi veri setinden bağımsız → (c) sürerken **paralel**. C.1 hesaplar §C.1 listesine bağlı, kör testin K5'i ve ekip sohbeti için ön koşul → (c)'nin son parçası.
4. **(e) sözlük tablosu kör testten önce** olmalı: Tansu "belgeden terim testi tablo verisi üzerinde koşar" dedi; ve tablo boş gelmemeli (kod sözlüğü seed).
5. **Eksik adım — K3 "Çelişkili Veri":** kör testin K3'ü 5/5 ister (Çelişkili Veri'de sessiz seçim = kritik bulgu). Bugün bu davranış **yok** (ADR-014 sabit metin listesinde yok; Karatepe 14,0/13,6, Yeşilova 18.912/18.240, iki ödeme planı sürümü tuzakları kütüphaneyle geliyor). Kütüphane bitince ama kör test öncesi **(c')** olarak girer, Ek-F F-6 kalıbıyla. Bu adım yoksa test ilk turda düşer.
6. **Ç-2 istemci bağlamı** (15) ve **Ç-3 terim cümlesi** (3) küçük; (a1) ile aynı prompt revizyonuna girer ki R1 bir kez koşsun.
7. **(f), (g) kör test turu 1'den sonra:** K1–K6 ikisini ölçmüyor; Ürün 1 testi geçilmeden finalize yok (T-13). Tansu testte isterse öne alınır (T-4).
8. **Ön koşul:** (a1)/(a2) Ek-F'ye dayanır → Ç-15/8 gereği ADT-2 onayı (PR #16, Naci) ve O-13/8 ölçüm kaydı için ADT-1 (PR #15). İkisi de Naci'nin tek tıkı.

### 3.2 Önerilen sıra

| Adım | İçerik | Bağımlılık | Büyüklük | Ölçülebilir bitiş kriteri | Durma noktası |
|---|---|---|---|---|---|
| **0** | Naci: PR #15/#16 onayı; bu plan; Tansu sorularının (§7.2) gönderimi | — | — | ADT-1/ADT-2 "onaylıyorum" | — |
| **1 (b)** Soru 15 | `DOC-ANK-FIN-008` normal; reseed tek belge; `test_authorization` beklentisi | 0 | S, 0 LLM | finans kullanıcısı `/api/documents`'ta görür; retrieval-only 44/44; discovery 13 ×1 bayrak açık: DSC-001/006 liste/soru verir (≤ 13 çağrı) | G3 ihlali → dur |
| **2 (a1)** Ek-F metin/biçim | F-5 kalıbı sabit cümle + assist yerine ("… olarak anladım. … kesin bilgi bulamadım. Elimde … var. İsterseniz açayım. … yüklenirse cevaplayabilirim." — yükleme cümlesi sona, cevap soru/seçenekle biter); F-3 liste ≤ 7, projeler ayrı başlık (soru 4); F-8 biçim (GG.AA.YYYY, 1.234.567,89 USD, %2,90, 1,20x) prompt + `format_check`; F-2 dolgu yasağı; Ç-3 terim cümlesi; Ç-2 `previous_question`; arayüz: `assist.question` ana metin, çipler kalkar (Ç-10) | 0, 1 | M | Bayrak açık: R1 14 ×1 cevaplanma/G1–G3 gerilemesi 0; discovery 13 ×1 ≥ 10/13, sabit cümle tek başına 0; 4 negatif kontrol ×1 uydurma 0; biçim denetimi (`format_check`) 100%; ≤ 31 çağrı; **tek prompt revizyon hakkı** | G1–G3 ihlali → dur; R1 < 12/14 → geri al |
| **3** ASSIST_MODE kararı | Adım 2 yeşilse: `.env.example` ve canlı `ASSIST_MODE=true`; bayrak **bir tur daha** kalır (geri dönüş), kör test turu 1 sonra kaldırılır | 2 | S | bayrak kapalı davranışın hâlâ derlendiği/test edildiği testler yeşil | — |
| **4 (a2)** gerçek belirsizlik | §4: yalnız proje ekseni + sürüm ekseni, kodla; `assist.kind=disambiguate`, liste yok, tek soru | 2 | M | §4.5 ölçüm: dev AMB ≥ 4/5, NEG yanlış alarm 0/9, held-out (yakılır) ≥ 3/5 ve yanlış alarm ≤ 1/5; retrieval-only, 0 LLM | yanlış alarm > 1 → eşik değil **tanım** gözden geçirilir, rapor |
| **5 (c)** kütüphane D/E | Ç-9 B + §3 değerleri (0 LLM 70 belge); demo bugün 06.10; 6 yeni SPV; Ç-7 ekler; Ç-8 mevzuat öneri notu önce; **C.4 etiketler aynı reseed'de**; sıra Tansu: PF → Hukuk → Enerji → Mali → İdari → İK | 0, mevzuat onayı | L (2–3 hafta, ~350 çağrı prose, 1 kota günü) | `make validate-ledger/documents/ocr` 0 hata; departman partisi bitince Tansu'ya haber; eval yeniden yazımı (§4.4) ve **tam ölçüm** (~1 kota günü): G1–G3 100%, R1-yeni ≥ eski | P1/P2 validator hatası partide → parti durur |
| **5′ (C.3)** yükleme önerisi | (c) ile paralel | — | M+M | boş formla yüklenen PDF'te ≥ 6/8 alan; SPV belirsizse `null` + soru | SPV yanlış atama 1 → dur |
| **6 (C.1)** hesaplar | 36 kullanıcı, departman/müdür, eski 5 pasif; eval `ask_as_user` eşlemesi | 5 | M | her kullanıcı giriş + kendi klasörü; `approver_not_configured` 0; yetki testi (K5 provası) 4/4 | yetki sızıntısı → dur |
| **7 (c′)** Çelişkili Veri | Aynı olgunun iki kaynakta farklı değeri (ledger tuzakları) → F-6 kalıbı, sessiz seçim yok; ADR-014 sabit metin + eval `conflict` kategorisi | 5 | M | `conflict` 5/5 dev sorusu; G1–G3 100% | — |
| **8 (e)** sözlük tablosu | tablo + admin API + Adım 2 sözlüğü seed; Tansu girdi ekler | 2 | M | tablo boşken sistem çalışır; tablodaki terimle `metadata_terms` eşleşir; test | — |
| **9** ölçüm kaydı (§6) | O-13/8, G.4 | 0 (ADT-1) | M | §6 kriterleri | — |
| **10** Kör test turu 1 (Tansu) | §5 | 5–9 | Tansu | K1–K6 eşikleri | kritik bulgu → tur düşer |
| **11 (f)** ekip sohbeti | `URUN1_NOT_PLAN §5` | 6, 10 | M | yetki testi; Balbal mesaj üretmez | — |
| **12 (g)** süreç modeli | C.6 ağaç + durum türetme + API | 5, 10 | L | "Kızılova lisans başvurusunu ne engelliyor?" kaynaklı tespit | — |

## 4. "Gerçek belirsizlik" tespiti — dürüst yaklaşım (uygulama yok)

**Ne oldu:** V3 (`ambiguity.py`, yalnız `ambiguity-v3-unmerged` etiketinde) "kapsamsız soru ∧ parça dağılımı" sinyaliyle 80 soruda 5/5 + 1 MIXED yanlış alarm, held-out'ta **2/5 ve 1 yanlış alarm** (HO-NEG-02 "Banka hangi DSCR seviyesini şart koşuyor?" → aynı projenin 5 finans belgesine dağıldı diye "hangi belge?" sordu). Kaçırdığı üçü (HO-AMB-02/03/05) düşük skorlu, iki projeye yayılan sorulardı. Sonuç: **belge ekseninde** dağılım belirsizlik sinyali değil; **proje ekseninde** sinyal zayıf skorlarda kayboldu.

**Tanım (İ-8 (1) + Ek-F F-4):** cevap *proje*, *belge* ya da *dönem*e göre değişiyorsa ve sohbetten anlaşılmıyorsa. Üç eksenin tespit edilebilirliği eşit değil:

| Eksen | Kodla tespit | Yanlış alarmın maliyeti | Kaçırmanın maliyeti |
|---|---|---|---|
| **Proje** (Ankara mı İzmir mi) | Yüksek: proje kelimesi yok ∧ parçalar ≥ 2 projeye dağılmış (**skor eşiği yok**, yalnızca grup sayısı ve ikinci grubun parça payı ≥ %25) | Net bir soruya "hangi proje?" → kullanıcı yeniden sorar (G.4 yeniden sorma göstergesi yakalar) | Model iki projeyi karıştırır → **K4/Ü-3 kritik bulgu** → asimetri: kaçırma daha pahalı |
| **Sürüm/dönem** (ilk sözleşme mi 2. tadil mi; hangi ay) | Orta: aynı tür ≥ 2 sürüm/dönem parça verdi ∧ soruda "güncel/ilk/son/tarih" ipucu yok | Düşük: zaten TEMPORAL TRUTH kuralı "güncel" ile "tarihsel"i ayırır; çoğu zaman model güncelini söyler, kaynakta sürüm görünür | Orta |
| **Belge** (hangi belgeyi kastetti) | **Düşük** — V3'ün çöktüğü yer: aynı projede birden çok belge parça vermesi normaldir (sözleşme + rapor + bildirim) | Yüksek: HO-NEG-02 tipi net sorulara soru dönülür → tutukluk geri gelir | Düşük: zayıf eşleşme yolu (liste + teyit, F-4 (2)) zaten var |

**Öneri:**
1. Tespit **yalnız proje ekseni** (+ isteğe bağlı sürüm ekseni ikinci turda). Belge ekseni **bilerek dışarıda**; o durumlar F-4 (2) "liste + mı kastettiniz?" yoluyla karşılanır — Ek-F'ye uygundur ve yanlış alarm maliyeti düşüktür.
2. Proje ekseni için eşik **skor değil pay**: top-N parça içinde ikinci projenin payı; V3'teki "ikinci ≥ 0,5×birinci skor" düşük skorlu dağılımları kaçırdı (AMB-02/03/05).
3. Sohbet bağlamı (Ç-2 A, `previous_question`) proje kelimesi içeriyorsa tespit **kapanır** (F-4: "aynı sohbette yeniden sormaz").
4. Çıktı: `assist.kind=disambiguate`, `assist.axis=project`, `question="Hangi projeyi kastediyorsunuz: Ankara RES mi, İzmir RES mi?"`, `available=[]` (liste yok); LLM çağrılmaz (ADR-021 ile uyumlu; kota 0).
5. **Dürüst sınır:** "Üretim rakamı ne kadar?" (hangi ay?) ya da "Karar ne zaman alındı?" (hangi karar?) gibi anlam belirsizliklerini kodla güvenilir yakalamanın yolu yok; bunlar F-4 (2) listesine düşer. Bunu da yakalamak için tek yol LLM sınıflandırması (soru başına +1 çağrı ya da cevap modelinden yapısal `ambiguity` alanı — Ç-1 "cevap eşiği aynı" ile uyumlu olmalı). **Şimdi önermiyorum**; kör test K6 (≥ 2/3) sonucuna göre karar (SORU 4).

**Ölçüm (§5 held-out kuralıyla):** dev: `questions.json` ambiguous (6) + negatif (9) + MIXED; held-out: Naci'nin yazdığı **yeni** 5 AMB + 5 NEG (eskiler 08.10'da yakıldı). Hedef: proje ekseni AMB recall ≥ 4/5 dev, ≥ 3/5 held-out; NEG yanlış alarm 0 dev, ≤ 1 held-out; F-4 "tek soru, liste yok" uyumu 100%; G1–G3 100%; LLM 0 (retrieval-only). Yanlış alarm > 1 → eşik oynatılmaz, **tanım** rapora yazılır ve durulur (eski kural).

## 5. Tansu'nun kör testi (§G) ile geliştirici seti

- **İki set, iki amaç.** `questions.json` (98 + held_out) **geliştirici seti**dir: herkese açık, regresyon ve G1–G3 için. Tansu'nun K1–K6 soruları **repoya girmez** (§G.2); sonuçlar `TEST_DEFTERI.md`'ye, bulgular `urun-testi` issue olarak gelir, soru metni tur bitince açıklanır → açıklanan soru **dev setine** eklenir.
- **Yeni held-out kuralı:** bir ölçümde kullanılan held-out seti **yanar** (dev setine taşınır, `held_out: false`); bir sonraki ölçüm için **Naci** yeni soruları yazar, ben ölçümden önce okumam; raporda "held-out (yakıldı: tarih)" damgası. §3.1'in 10 sorusu ve HO-DSC-01…06 artık dev setidir (açık yayımlandı). SORU 8 cevabı buna uygun: 10 soru `discovery` kategorisine dev olarak girer.
- **Eşleme:**

| Tansu | Bizim dev karşılığı | Boşluk |
|---|---|---|
| K1 Anlama ≥ 9/10 | `discovery` (eş anlamlı, kavram sözlüğü) | sözlük tablosu (adım 8), F-4 (2) |
| K2 Kesin bilgi + kaynak ≥ 7/8 | `document`, `excel`, `temporal` kategorileri, `required_sources` | yeni ledger yolları (§4.4) |
| K3 Çelişki/eksik/sürüm 5/5 | `versions`; **`conflict`, `missing_known` yok** | adım 7 (c′) zorunlu |
| K4 Ürün 1 sınırı 3/3 | MIXED hesap yapmama, `expected_project` ayrımı | proje gruplu liste (soru 4) |
| K5 Yetki 4/4 | G3 + başlık sızıntı testi | 36 hesapla yeniden (adım 6) |
| K6 Belirsiz/kapsam dışı ≥ 2/3 | `ambiguous`, `out_of_scope` | adım 4; F-7 kalıbı |
| Belge yükleme SPV 0 hata | — | adım 5′ (C.3) |

- Kör testten önce "geçiş provası": aynı kategorilerle bizim dev setimizden K-haritalı bir koşu (G1–G3, R1-yeni) yapılır; sonuç Tansu'ya **sayı** olarak değil "hazır" olarak bildirilir (sorularını etkilememek için).

## 6. Audit / ölçüm kaydı (O-13/8, G.4, F.5) — kısa taslak

- **İlke:** toplu değerlendirme; kişi bazında rapor **yok**; mevcut audit kuralları (yalnız admin, 90 gün) aynen; yeni kayıt kurumsal hafızaya girmez.
- **Soru tarafı (`audit_log`, mevcut `assist` JSON'a ek alanlar, migration yok):** `answer_state` (answered / no_answer / clarify / disambiguate / conflict / out_of_scope), `assist_kind`, `question_asked` (bool), `sources_shown` (int), `previous_question_given` (bool).
- **Olay tarafı (yeni tablo `answer_events`, migration):** `audit_id`, `event` ∈ {source_opened, reask}, `created_at`; `source_opened` istemciden `POST /api/ask/{audit_id}/events`; `reask` sunucuda hesaplanır: aynı kullanıcı, ≤ 10 dk, önceki soruyla terim benzerliği ≥ 0,6 → `reask_of=<audit_id>` (G.4 "tutukluk göstergesi").
- **Yükleme tarafı (yeni tablo `upload_field_log`):** `document_id`, `field`, `suggested_value`, `confidence`, `final_value`, `changed`, `form_opened_at`, `approved_at` — C.3 (adım 5′) ile birlikte.
- **Okuma:** yalnız toplu uç `GET /api/admin/metrics/summary` (dönem, alan bazlı düzeltme oranı, durum dağılımı, yeniden sorma oranı, ortalama onay süresi); kullanıcı kırılımı **yok**. 90 gün temizliği mevcut audit işine eklenir.
- ADR-030 "Measurement log is not memory"; büyüklük M; kör testten önce açık olmalı (sonradan toplanamaz).

## 7. Sorular

### 7.1 Naci'ye SORU (A/B) — **cevaplandı 09.10.2026: 1 A, 2 A, 3 A (adım 2 yeşilse), 4 A, 5 A, 6 A, 7 A, 8 A, 9 A** (ayrıntı §2)

1. **Sıra:** §3.2 revize sıra (A) mı, kendi sıran a→g (B) mi?
2. **Ölçüm seti:** adım 1–4 eski Ankara/İzmir setinde "geçiş değeri" olarak ölçülsün (A) mı, kütüphane bitince tek ölçüm (B) mi?
3. **ASSIST_MODE:** adım 2 yeşilse canlıda varsayılan açık + bayrak bir tur daha (A) mı, kör test turu 1'e kadar kapalı (B) mi?
4. **Belirsizlik:** yalnız proje ekseni kodla (A) mı, LLM sınıflandırma çağrısı da planlansın (B, soru başına +1 çağrı) mı?
5. **Held-out:** her ölçüm öncesi 10 yeni soruyu sen yazarsın, ben görmem (A) mı; Tansu'dan istenir (B) mi?
6. **K3 Çelişkili Veri (adım 7):** kör test öncesi zorunlu (A) mı, tur 1 sonrası (B) mi? (B seçilirse K3 ilk turda düşer; bilinçli kabul.)
7. **(f)/(g) zamanı:** kör test turu 1 sonrası (A) mı, kütüphaneyle paralel (B) mi?
8. **Ölçüm kaydı:** iki yeni tablo + reask sezgisi (A) mı, yalnız audit JSON genişletme, istemci olayı yok (B) mi?
9. **ADT-1/ADT-2:** olduğu gibi onay (A) mı, madde itirazı var (B — madde no) mı?

### 7.2 Tansu'ya sorulacaklar — AI-BalBal `docs/SORULAR_NACIDEN_2-2026-10-09.md` olarak gönderildi (dal `docs/naci-sorular-2-2026-10-09`, 09.10.2026)

- **T-1 (#4):** Proje adı geçmeyen soruda F-3 gereği projeler ayrı başlıkta gruplu liste + "hangi proje?" — doğru anladık mı? Bu, İ-8 (1) "liste yok" kuralının istisnası mı (seçenekler proje adı olduğu için)?
- **T-2 (SORU 8 ↔ §G.2):** §3.1'in 10 sorusu `questions.json`'a girerse herkese açık olur; bunlar geliştirici seti sayılıp kör testte **kullanılmayacak** varsayıyoruz — uygun mu?
- **T-3 (bütçe):** Yeni kütüphanede bütçe/gerçekleşen workbook'u hangi departmanın klasöründe (Enerji O&M mi, Proje Finans mi)? Bugün Enerji'de; finans uzmanı göremiyor.
- **T-4 (f/g):** Ekip sohbeti ve önlisans süreç modeli kör test turu 1'de ölçülecek mi? Değilse tur 1'den sonra yapmayı öneriyoruz.
- **T-5 (K3):** Çelişkili Veri için Ek-F F-6 kalıbı sabit metin olarak kullanılabilir mi ("Kaynaklar farklı söylüyor: … Fark: … Hangisinin geçerli olduğunu teyit edebilir misiniz?")? K3'te "eksik belge" (Annex F teminat mektubu) için beklenen davranış F-5 mi?
- **T-6 (K6):** 3 sorunun kaçı gerçek belirsizlik, kaçı kapsam dışı? (Metin değil, sayı.)
- **T-7 (demo bugün):** 06.10.2026 sabit kalır mı, kör test tarihine göre kayar mı? Sabit kalmasını öneriyoruz (ledger "bugüne göre" alanları).
- **T-8 (teslim):** "Klasörler tamamlandı" = Proje Finans + Hukuk partisi mi, tüm departmanlar mı? Parti parti test başlayabilir mi?
- **T-9 (Ç-12):** Enercon/Vestas adları için karar ne zaman? Kütüphane başlarken tek tablodan yöneteceğiz; karar gelince toplu değişir.
