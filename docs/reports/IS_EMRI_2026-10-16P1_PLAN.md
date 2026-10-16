# İş Emri 2026-10-16P1 — Netleştirme seçenekleri yalnız veriye sahip projeler: PLAN

**Tarih:** 16.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `c0c0984`) · **Ürün 1** · **Ç-15/3 → T-9: kod öncesi plan, onay bekleniyor**

**Dayanak:** Tansu 16.10 (`ftansu/AI-BalBal` ana dal, `gh api` ile salt okundu):
- `docs/yazismalar/2026-10-16_naciye-acik-kararlar.md` madde 1 ve 2
- `docs/yazismalar/2026-10-16_naciye-karar-excel-proje-ayrimi.md` §3/2
- ADR-034 (N1)
- `docs/reports/IS_EMRI_2026-10-16V141.md` §2, §3

**Okunan anayasa:** `anayasa/00-cekirdek.md` (Ç-15, Ç-16, Ç-17), `01-urun.md`, `02-teknik.md` (T-5, T-9 + ADT-4).

**Durum:** yalnız plan. Kod, ayar, şema, puanlayıcı ve canlı servis değişmedi. Ölçüm, eval DB'de (`company-ai-eval`, `./data-eval`) yalnız `SELECT` ile yapıldı. Konteyner ölçümden sonra kapatıldı.

## 1. Bugün seçenekler neye dayanıyor (kod okuması)

Akış (N1, ADR-034):
1. `ask_router.answer_routed_question` → `route_without_llm` → `is_unnamed_value_question`. Yalnız metin ve `projects` tablosuna bakar.
2. `ask.project_question_for`:
   - `allowed_document_ids` (ADR-004)
   - `retrieve()` (top-k parça)
   - `project_narrowing.unnamed_value_clarification(session, allowed, chunks)`
3. `unnamed_value_clarification`:
   - Görünür proje yoksa → `None`.
   - En üst parça grup belgesiyse → `None` (şirket sorusu).
   - Aksi halde `unnamed_project_question(visible_project_names(session, allowed))` döner.
4. `visible_project_names`: `allowed` içinde **en az bir belgesi olan tüm aktif projeler**, ada göre sıralı.

**Sonuç:** seçenek listesi ne sıralamaya ne de parça skoruna dayanıyor. Dayandığı tek şey yetki kümesi. Getirim (`chunks`) yalnız "şirket sorusu mu" kararında ve audit satırında kullanılıyor. Sorunun **konusu** listeye hiç girmiyor. Bu yüzden kullanıcı neyi görüyorsa sayılıyor (yonetim için 6 proje).

Ayrı bir yol daha var: Adım 4 proje ekseni (`assist.classify_project_axis` → `build_disambiguate_assist`, "Hangi projeyi kastediyorsunuz: X mi, Y mi?"). Bu yol getirilen parçaların proje dağılımına, yani sıralamaya dayanıyor. N1 ön-yönlendirmesinin yakalamadığı sorularda (router'ın sınıfladığı, belge yolunda parça dönen sorular) çalışıyor. Madde 1 "adsız değer sorusu" dediği için bu plan o yola **dokunmaz** (Ç-16). Bkz. §7 S-4 notu.

## 2. Sorun ve ölçülmüş örnekler

N1 koşusu (`results/n1_final_2026-10-16`) ve v2.1+v14+v14.1 puanı:

| Soru | Kullanıcı | N1 seçenekleri | Veriye sahip (V141 §3) | Sonuç |
|---|---|---|---|---|
| GEN-DSC-003 "Sigorta ne zaman bitiyor?" | enerji | Karatepe, **Kızılova** | Karatepe | ❌ (`forbidden: Kızılova`) |
| ANK-MIX-001 "Güncel DSCR kaç?" | finans | Boztepe, Karatepe, **Kızılova**, Yeşilova | Boztepe, Karatepe, Yeşilova | ❌ (`forbidden: Kızılova`) |
| GEN-DSC-004 "Lisans durumu ne?" | enerji | Karatepe, Kızılova | Karatepe, Kızılova | ✅ (enerji iki projeyi görüyor; doğruluğu tesadüf) |

N1'de proje sorusu alan 15 sorunun tamamı §5'teki tabloda.

## 3. Önerilen yöntem (kod; LLM yok)

**İlke:** Seçenek = yetki kümesindeki proje belgelerinden, sorunun konu terimini metninde (OCR parçaları) ya da künyesinde (başlık/tür/karşı taraf/etiket/ek alan) taşıyan en az bir belgesi olan projeler. Karar belge düzeyinde verilir. Top-k, sıra ve parça skoru kullanılmaz.

Adımlar (`project_question_for` içinde, getirimden sonra, mevcut "en üst parça grup belgesi" kuralından sonra):

1. **Terimler.** `question_terms(question)` kullanılır: soru kelimeleri ve durak kelimeler atılmış hali; `build_search_query` ile aynı ilk yarı.
2. **Her terim için kanıt kümesi (belge düzeyi).** Terim ve sözlük karşılıkları (`expand_terms` / `metadata_terms`; ör. sigorta → Insurance, DSCR → "debt service coverage") birlikte aranır.
   - Kapsam: yalnız `allowed` içindeki, `project_scope = project` olan ve projesi aktif belgeler.
   - Metin eşleşmesi: `_fts_predicate`, yani getirimle aynı FTS tanımı. Belge kimlikleri `DISTINCT` alınır, `LIMIT` yok.
   - Künye eşleşmesi: `search_metadata` (mevcut). Parçası olmayan belgeler (ör. workbook) künyeden yakalanır.
3. **Ayırt etmeyen terimleri at.**
   - Kanıtı 0 belge olan terim atılır ("zaman", "doluyor"). Hiçbir belgede geçmiyor, konu ayırt etmez.
   - **Genel** terim atılır: kullanıcının görünür proje belgelerinin **%50'sinden fazlasında** geçen terim (ör. enerji için "Üretim" %100, "durumu" %61). Oran **yalnız yetki kümesi içinden** hesaplanır. Böylece gizli belgeler hangi terimin "genel" sayılacağını da etkileyemez (dolaylı sızıntı yok).
4. **Konu terimi (kavram çapası).** Kalan terimlerden sözlükte kavramı olanlar (`GLOSSARY` / `CONCEPT_GLOSSARY` anahtarı: sigorta, lisans, DSCR, vade, tadil, kredi, sözleşme, rapor, ÇED …) varsa yalnız onlar konu sayılır. Kavram yoksa kalan terimlerin hepsi konu sayılır.

   Gerekçe: "güncel", "son", "ilk", "kadar" gibi niteleyiciler başka projenin alakasız belgesini listeye sokuyor. Ölçüm §5'te: "Son tadil" sorusunda "Son" kelimesi Yeşilova'yı ekliyor.
5. **Projeler konu terimlerinin BİRLEŞİMİ ile seçilir** (kesişimi değil). Gerekçe: "veriye sahip projeyi düşürmek geçmez".
   - Ölçülmüş örnek: Yeşilova Facility Agreement (2023-YS) metninde "tenor/maturity/vade" hiç geçmiyor.
   - Kesişim kullanılsaydı, "Kredi sözleşmesinin vadesi" sorusunda kredi sözleşmesi olan Yeşilova düşerdi.
6. **Sonuç.** Bugünkü cümle kalıbı ve sıralaması (ada göre) aynen korunur.

| Durum | Davranış |
|---|---|
| ≥ 2 proje | "Hangi proje için sormak istiyorsunuz (A, B)?" — yalnız bu projeler |
| **1 proje** | **Yine sorulur** (madde 2): "Hangi proje için sormak istiyorsunuz (Karatepe RES)?". Bugünkü tek-görünür-proje davranışıyla aynı; doğrudan cevap **bu pakette yok** (S-3). |
| 0 proje, ama konu terimi vardı | Konu yalnız grup belgelerinde var ya da hiç yok. `None` döner: ön-yönlendirme düşer, soru bugünkü normal yola gider (router → belge yolu). Sonuç ya grup belgesinden cevap ya da mevcut "veri yok" kalıbı olur (madde 1: "veri yok demek doğru davranış"). Yeni metin yazılmaz. |
| Ayırt eden terim kalmadı (hepsi 0 ya da hepsi genel) | Konu belirlenemedi. **Bugünkü liste** (tüm görünür projeler) kullanılır. Bu güvenli geri düşüştür: veri sahibi düşmez, eksik seçenek sunulmaz (S-1). |

Kapsam sınırları:
- Proje adı geçen sorular (ADR-031 daraltması), bilinmeyen proje (ADR-031/032) ve keşif soruları (F-3 listesi) **değişmez**.
- `visible_project_names` "bilinmeyen proje" sorusunda aynen kalır. Orada konu yoktur; kullanıcıya görebildiği projeler sunulur.

## 4. Etkilenen dosyalar, büyüklük, şema/bağımlılık

| Dosya | Değişiklik | Tahmini |
|---|---|---|
| `backend/app/repositories/document_chunk_repo.py` | `document_ids_matching(session, *, allowed_ids, query) -> set[UUID]` (mevcut `_fts_predicate`, `DISTINCT document_id`) | +15 satır |
| `backend/app/services/project_narrowing.py` | `projects_with_data(session, allowed, question) -> list[str] \| None` (§3 adım 1–5); `unnamed_value_clarification(…, question)` parametresi; `GENERIC_SHARE = 0.5` sabiti | +70 satır (238 → ~310, < 400) |
| `backend/app/services/ask.py` | `project_question_for` → `request.question` iletilir | 1–2 satır |
| `backend/tests/test_project_options.py` (yeni) | §6 birim testleri | ~160 satır |
| `backend/tests/test_unnamed_value_question.py` | Fikstür belgelerinin metnine soru konusu eklenir (bugün "kredi vade"; soru metni de buna uyuyor, büyük ölçüde değişmeyecek) | küçük |
| `scripts/measure_stage2.py` | `getattr(…, "unnamed_value_clarification")` imzası kontrol edilir; gerekiyorsa çağrı güncellenir | küçük |
| `docs/ARCHITECTURE.md` | ADR-035 "Proje seçenekleri belge düzeyinde konu kanıtıyla" | kısa |
| `docs/reports/IS_EMRI_2026-10-16P1.md` | rapor | — |

- **Şema/migrasyon: gerekmez** (Ç-15/4 tetiklenmez). Yeni tablo, kolon ve indeks yok. Var olan `tsv_turkish`/`tsv_simple` ve `documents` kolonları okunur.
- **Yeni bağımlılık: yok.**
- **LLM: yok.** Kod üretimli, ADR-034 ile aynı model (0 çağrı, token 0).
- **Prompt/davranış kuralı: değişmez** (Ç-15/8 tetiklenmez).
- **Ayar/bayrak: yok.** ADR-034 gibi bayraktan bağımsız. Geri alma kod düzeyinde (§6).
- **Yetki kuralı değişmez.** `allowed_document_ids` aynen çağrılır; yeni filtre onun **içinden** daraltır (T-5; madde 1 usulü). Plan, Ç-15/3 "erişim kuralına değen davranış" ihtiyatıyla sunuldu.

## 5. Ölçüm: önerilen yöntemin N1'deki 15 soruya etkisi (eval DB, SELECT-only, LLM'siz)

Bu 15 cevap kod üretimli. Tablodaki "önerilen" sütunu, aynı DB'de §3 kuralları terim-belge sorgularına elle uygulanarak çıkarıldı. Uygulama sonrası aynı ölçüm kodla tekrarlanacak.

Kısaltmalar: B = Boztepe, K = Karatepe, Kz = Kızılova, Y = Yeşilova, A = Akyar, D = Demirci.

| Soru (kullanıcı) | Bugün (N1) | Konu terimleri → belge kanıtı | Önerilen | Not |
|---|---|---|---|---|
| **GEN-DSC-003** Sigorta ne zaman bitiyor? (enerji) | K, Kz | sigorta → K (2 belge) | **K** (tek, yine sorulur) | ❌ → ✅ beklenir |
| **GEN-DSC-004** Lisans durumu ne? (enerji) | K, Kz | lisans → K, Kz ("durumu" %61 genel) | **K, Kz** | ✅ kalır |
| **ANK-MIX-001** Güncel DSCR kaç? (finans) | B, K, Kz, Y | DSCR → B, K, Y ("Güncel" kavram değil) | **B, K, Y** | ❌ → ✅ beklenir |
| GEN-AMB-002 Raporda belirtilen DSCR değeri kaç? (finans) | B, K, Kz, Y | rapor, DSCR → B, K, Y | B, K, Y | Kz düşer |
| ANK-NEG-003 Kredi sözleşmesinin vadesi kaç yıl? (finans) | B, K, Kz, Y | sözleşme → B, K, Kz, Y; vade → B, K, Kz ("Kredi" %73 genel) | B, K, Kz, Y | aynı; birleşim Y'yi tutar |
| GEN-AMB-001 Sözleşmenin vadesi ne zaman doluyor? (yonetim) | A, B, D, K, Kz, Y | sözleşme, vade → B, K, Kz, Y | B, K, Kz, Y | A, D düşer |
| GEN-AMB-003 Son tadil neyi değiştirdi? (yonetim) | 6 proje | tadil → K | K (tek, sorulur) | sözcük sınırı: §8 R-3 |
| GEN-AMB-003-F aynı (finans) | B, K, Kz, Y | tadil → K | K (tek, sorulur) | kavram çapası olmasa "Son" Y'yi eklerdi |
| GEN-AMB-004 Lisans ne zaman alındı? (enerji) | K, Kz | lisans → K, Kz | K, Kz | aynı |
| ANK-NEG-004 Üretim lisansı ne zaman alındı? (enerji) | K, Kz | lisans → K, Kz ("Üretim" %100 genel) | K, Kz | aynı; bilinen kayıp sürer (madde 2) |
| GEN-AMB-006 Hukuki inceleme notunda ne tespit edildi? (hukuk, 7 belge) | K, Kz | tüm terimler %57–86 → ayırt eden yok | K, Kz (geri düşüş) | aynı |
| GEN-GEN-002 ÇED süreci nedir? (yonetim) | 6 proje | ÇED → K, Kz | K, Kz | GEN-GEN kararı ayrı (V14 §3) |
| GEN-GEN-003 Covenant testi ne işe yarar? (yonetim) | 6 proje | kredi, sözleşme, covenant → B, K, Kz, Y | B, K, Kz, Y | aynı |
| GEN-DSC-011 / 011-K karatepenin ilk kredi ödemesi … (yonetim) | 6 proje | kredi → B, K, Kz, Y | B, K, Kz, Y | "karatepenin" ad sayılmıyor (madde 5, takma ad, kapı sonrası) |

**Beklenen puan etkisi** (v2.1 + v14 + v14.1, N1 referansı 70/99):
- GEN-DSC-003 ve ANK-MIX-001 ❌ → ✅ beklenir; ANK-MIX-001'in diğer kontrolleri V141'de zaten geçmişti. Tahmin: **72/99**.
- Diğer 13 soru: geçme durumu değişmez. Bunların `required/forbidden_phrases` alanı yok, netleştirme ölçütü aynı.
- Kesin sayı canlı kodla tek koşuda ölçülür.

**Performans:** belge düzeyi tek FTS sorgusu eval DB'de **0,7 ms** sürdü (`EXPLAIN ANALYZE`, 113 belge). Soru başına 2–6 terim × (1 FTS + ≤ 3 künye ILIKE) → beklenen **< 30 ms**. Yalnız N1 yolunda çalışır (eval'de 15/99 soru). LLM çağrısı olmadığından toplam süre bugünkünden belirgin değişmez. Raporda p50/p95 verilecek.

## 6. Test planı ve geri alma

**Birim/entegrasyon** (`test_project_options.py`; mevcut DB fikstürleri, sahte LLM — tümünde `fake_llm.requests == []`):
1. Konu iki projede var, üçüncüde yok → yalnız ikisi sayılır.
2. **Sızıntı (T-5):** enerji kullanıcısı; Karatepe sigorta belgesi enerji'de, Yeşilova Sigorta Zeyilnamesi finans'ta. "Sigorta ne zaman bitiyor?" → cevap tam olarak "(Karatepe RES)"; "Yeşilova" geçmez; gizli belge kimliği `retrieved_document_ids` içinde yok.
3. **Sızıntı, dolaylı:** gizli belgelerin çokluğu bir terimi "genel" yapmaz. Oran yalnız `allowed` içinden hesaplanır: aynı soru, gizli belge sayısı artırılınca aynı sonucu verir.
4. Tek aday → yine soru, tek ad (madde 2; doğrudan cevap yok).
5. Konu yalnız grup belgesinde → `None` → router yolu (sahte router çağrılır).
6. Konu hiçbir belgede yok → `None` → router yolu.
7. Ayırt eden terim yok (hepsi genel) → bugünkü tüm görünür proje listesi.
8. Künye eşleşmesi: parçası olmayan belge (workbook benzeri), başlığında "DSCR" → projesi sayılır.
9. Kavram çapası: "Son tadil …" — "son" başka projede geçiyor, "tadil" yalnız birinde → yalnız o.
10. Pasif proje (`is_active=false`) seçenek olmaz (T1 emsali).
11. Mevcut N1 testleri (`test_unnamed_value_question.py`, 13 test) yeşil kalır.

**Eval (LLM'siz ön ölçüm + tek canlı koşu):**
- Kod sonrası, eval DB'de 15 sorunun `project_question_for` çıktısı betikle alınır ve §5 tablosuyla birebir karşılaştırılır. Fark varsa rapora yazılır; DUR.
- GEN-DSC-003, GEN-DSC-004 ve ANK-MIX-001 `required/forbidden_phrases` ile otomatik ölçülür.
- Canlı koda tek M1-tarzı koşu, v2.1+v14+v14.1 ile. Karşılaştırma N1 70/99'a karşı; KY ve güvenlik G1–G3 ayrıca raporlanır.

**Doğrulama:** `make test` (bayraksız) + `make lint` yeşil. Canlıya alma: `make restart-backend` + `scripts/smoke_live.py`. Smoke satırı (f) "Sözleşmenin vadesi …" (yonetim) 6 → 4 proje göstermeli (B, K, Kz, Y); beklenti rapora yazılır.

**Geri alma:** yalnız kod.
- `git checkout c0c0984 -- backend/app` (ya da P1 commit'inin `git revert`'ü) + `make restart-backend`.
- Migrasyon yok, `.env` değişmez, veri değişmez. Geri alma süresi ≈ yeniden başlatma (~12 s, N1 ölçümü).

## 7. Riskler

| # | Risk | Önlem / kalan |
|---|---|---|
| R-1 | **Yetki sızıntısı** | Tüm sorgular `Document.id IN allowed`. Genel-terim oranı da yalnız `allowed`'dan. Seçenek yalnız `allowed` içindeki proje belgesinden doğar. Test 2–3. Yetki fonksiyonu değişmez. |
| R-2 | **Performans** | Belge düzeyi `DISTINCT`, GIN'li `tsv_*` kolonları; ölçülen 0,7 ms/sorgu. Yalnız N1 yolunda. Raporda süre. |
| R-3 | **Yanlış daraltma: veri sahibi düşer (geçmez)** | Kanıt **sözcük** düzeyinde: "belgede konu terimi ya da sözlük karşılığı geçiyor". Anlamsal değil, embedding kapalı. Örnek: "tadil" yalnız Karatepe'de bulunuyor (Amendment 01). Yeşilova Sigorta **Zeyilnamesi** de bir tadildir ama kelime geçmez. Önlemler: kavramlar arası birleşim (kesişim yok); ayırt eden terim yoksa bugünkü tam listeye geri düşüş; tek aday doğrudan cevaba çevrilmez (madde 2). Kalan risk: sözlükte olmayan eş anlam. Çözüm kod değil sözlük verisi (`GLOSSARY` / `CONCEPT_GLOSSARY` genişletme, "tek sorudan değil gerçek belge teriminden" kuralıyla). |
| R-4 | **Yanlış genişleme: verisi olmayan girer** | Örnek: Kızılova "Avans Faturası" metninde "vade" (fatura vadesi) geçer → vade sorusunda Kızılova kanıtlı sayılır. Bugünkü 15 soruda sonucu değiştirmiyor (Kızılova'nın imzalı kredi sözleşmesi "sözleşme" teriminden zaten giriyor). Kalan risk raporda örnekleriyle listelenecek. |
| R-5 | **Excel** | Workbook'ların parçası yok; yalnız künyeden (başlık/etiket) kanıt olur. Bugün DSCR verisi taşıyan projeler PDF'lerden de bulunuyor. Excel yolu (hesap motoru proje ayrımı, Excel notu §3) bu paketin **dışında**; aynı fonksiyon orada "seçenekler yalnız veriye sahip projeler" (§3/2) için yeniden kullanılabilir. B-01 ayrı. |
| R-6 | **Grup belgeleri / şirket-geneli sorular** | Grup belgesi hiçbir zaman proje seçeneği olmaz. Mevcut "en üst parça grup belgesi → şirket sorusu" kuralı önce çalışır. Konu yalnız grup belgelerindeyse 0 proje → `None` → normal yol (şirket cevabı ya da "veri yok"). "Her proje / tüm projeler / şirket" soruları `asks_across_projects` ile zaten bu yola girmez. |
| R-7 | **Eşik (%50) ayarı** | Sabit, kodda tek yer. Küçük yetki kümelerinde (hukuk 7 belge) tüm terimler genel çıkabilir → geri düşüş (bugünkü liste). Eşik veriyle değişirse ADR-035'e yazılır. |

**Bilinen kayıp sürer:** ANK-NEG-004 (madde 2: "doğrudan Karatepe cevabı" beklentisi, bugün K, Kz soruluyor; önerilen yöntemde de K, Kz).

## 8. Tansu'ya açık sorular

**S-1 (konu belirlenemezse):** Sorunun bütün kelimeleri belgelerin çoğunda geçiyorsa (ör. hukuk "Hukuki inceleme notunda ne tespit edildi?") yöntem konuyu ayırt edemiyor. Bu durumda bugünkü gibi tüm görünür projeleri saymayı öneriyorum, çünkü eksik seçenek sunmaktan iyi. Onaylıyor musun?

**S-2 (hiçbir projede veri yoksa):** Konu terimi hiçbir proje belgesinde geçmiyorsa proje sorusu sorulmaz; soru N1 öncesindeki normal yoldan gider. Sonuç grup belgesinden cevap ya da mevcut "veri yok" kalıbıdır; yeni metin yazılmaz. Bu, madde 1'deki "veri yok demek doğru davranış" cümlesinin uygulaması olarak doğru mu?

**S-3 (madde 2 "sonra" seçeneği):** Daraltmada tek proje kalınca "Karatepe RES için: …" diye doğrudan cevap verme seçeneğini **bu pakete almamayı**, P1 canlıda ölçüldükten sonra ayrı bir pakete bırakmayı öneriyorum. Gerekçe: kanıt sözcük düzeyinde ve "tek aday" bazen sözcük eksikliğinden doğuyor. Örnek R-3: "Son tadil …" sorusunda yalnız Karatepe çıkıyor, Yeşilova zeyilnamesi kelime olarak yakalanmıyor. Doğrudan cevap bu durumda madde 2'nin uyardığı "eksik cevabı tam gibi sunma" (KY) riskini geri getirir. Ayrı paket mi, bu paket mi?

*(Not, soru değil: Adım 4 proje ekseni yolu — `classify_project_axis`, parça dağılımına dayanır — madde 1'in kapsamında sayılmadı, dokunulmuyor. Tansu bu yolu da belge düzeyine çekmek isterse ayrı plan.)*

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (+ ADT-4). Okunan: Çekirdek (Ç-9, Ç-15, Ç-16, Ç-17), 01 Ürün, 02 Teknik (T-5, T-9);
  Tansu 16.10 açık kararlar (madde 1, 2) + Excel proje ayrımı notu (gh api, salt okuma)
Ürün etiketi      : Ürün 1 — T-11 (netleştirme sorusunun seçenekleri; proje-proje tam cevap Ürün 2'de kalır)
Kritik Geliştirme Kararı : Ç-15/3 — yetki/erişim kuralına değen davranış (filtre yetki kümesinin içinden);
  plan sunuldu, ONAY BEKLENİYOR. Ç-15/4 (şema) tetiklenmez — migrasyon yok. Ç-15/8 (prompt) tetiklenmez — LLM yok.
Gizli bilgi / yeni bağımlılık : Yok — kod yazılmadı; .env/.env.eval değişmedi; yeni paket yok; LLM çağrısı 0
Kapsam dışı değişiklik        : Yok — yalnız bu plan dosyası. Eval DB yalnız SELECT (konteyner sonra kapatıldı);
  canlı servis, ayar, şema, puanlayıcı, soru seti dokunulmadı
Kendi başına verilen kararlar : §3 ayrıntıları (kavram çapası, birleşim, %50 genel-terim eşiği, 0 aday → None,
  ayırt eden terim yok → bugünkü liste), ADR-035 numarası, Adım 4 yolunun kapsam dışı tutulması — onayla birlikte kesinleşir
```
