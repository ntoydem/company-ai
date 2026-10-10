# Ek-F v2 Planı — Tansu'nun T-1..T-9 cevaplarıyla kod çelişkileri

**Tarih:** 10.10.2026 · **Durum:** plan, kod yok, canlı Gemini çağrısı yok · **Dayanak:** `docs/SORULAR_NACIDEN_2-2026-10-09.md` (AI-BalBal PR #17, commit 763f8a7) T-1/T-5/T-6; `docs/plans/URUN1_KARARLAR_VE_SIRA.md` §7.3 · **Dal:** `feat/adim5-veri-kutuphanesi` (main'e birleştirme yok)

Bu plan **uygulama değil** — Tansu'nun 2. tur cevaplarının mevcut Ek-F (ADR-030) ve Adım 4 (proje ekseni) koduyla nerede çeliştiğini, hangi dosya/fonksiyonun değişmesi gerektiğini ve nasıl ölçüleceğini anlatır. Her madde için SORU + öneri var; onay gelmeden kod değişmez.

## (a) F-5: "arşivde yok" ifadesi var mı?

**Bulgu:** Kodda **literal "arşivde yok" ifadesi yok** — tarandı (`assist.py`, `answer_prompt.py`), bulunamadı. `NO_ANSWER_TEXT` (`answer_prompt.py:21`) zaten "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için **yeterli bilgi bulamadım**." diyor — Tansu'nun istediği "**erişebildiğim kaynaklarda bulamadım**" ile kavramsal olarak aynı yönde (yetkisiz belgeyi "yok" diye işaretlemiyor) ama **birebir aynı cümle değil**.

**Çelişki yok, ama netleştirme eksik:** `render_no_data` (F-5) içinde eksik belge durumuna özel bir cümle yok — yalnızca genel `NO_ANSWER_TEXT` + F-3 listesi var. Tansu'nun T-5 cevabı "eksik belge" için özel bir sıra istiyor: (1) F-5 "Veri Yok" (ama "arşivde yok" DENMEZ, "erişebildiğim kaynaklarda bulamadım" denir), (2) sonra erişilebilir belgeler söylenir, (3) yükleme önerisi **en sonda**. Bugünkü `render_no_data` zaten bu sırayı büyük ölçüde izliyor (`CLARIFY_TEMPLATE`/upload cümlesi en son ekleniyor — SORU 4 yorumuna bakılırsa) ama **cümlenin kendisi** "erişebildiğim kaynaklarda bulamadım" değil, `NO_ANSWER_TEXT`'in kendisi kullanılıyor.

**Dosya/fonksiyon:** `backend/app/services/answer_prompt.py::NO_ANSWER_TEXT` (sabit metin — değişirse R1/G2 testleri etkilenir, dikkatli); `backend/app/services/assist.py::render_no_data`.

**SORU 1:** `NO_ANSWER_TEXT`'in kendisi Tansu'nun tam cümlesine mi çekilsin ("erişebildiğim kaynaklarda bulamadım"), yoksa mevcut cümle kalsın, yalnızca **eksik belge özel durumunda** (F-5'in "bu belge adıyla yok" alt durumu — ör. Annex F teminat mektubu sorulduğunda) ek bir cümle mi eklensin? **Önerim:** ikinci — `NO_ANSWER_TEXT` genel/her durumda kullanılan bir sabit, değiştirmek G2/R1'i geniş çapta etkiler; eksik-belge-özel cümle daha dar bir ekleme.

## (b) Adım 4 "dominant → varsayıldı" mantığı T-1 ile çelişiyor

**Bugünkü kod:** `classify_project_axis` üç proje-ekseni çıktısı üretir: `named` (proje adı geçiyor → doğrudan cevap, **Tansu'nun 3. durumuyla zaten uyumlu**), `disambiguate` (yakın bölünme → `downgrade_existence_disambiguate` ile varlık sorularında F-3 listesine düşer, diğerlerinde **liste yok, tek soru** — **Tansu'nun belge-arama/değer ayrımına kısmen uyumlu**), `dominant` (açık çoğunluk → **her soru türünde** aynı davranış: `inferred_project` set edilir, F-3 listesi o projeye daralır, "… projesine ait olduğu varsayıldı" cümlesi eklenir — `render_no_data:889-894`).

**Çelişki — tam burada:** T-1, "değer veya bilgi soruyorsa… projelerin değerleri alt alta sıralanmaz; yalnız tek netleştirici soru" diyor, **çoğunluk olup olmamasına bakmadan**. Bugünkü `dominant` davranışı ise tam tersini yapıyor: listeyi daraltıp "varsayıldı" diyerek **cevap üretiyor**, soru sormuyor. Bu, Adım 4'ün kendi onaylı tasarımıyla (`ADIM4_PLAN.md`, Naci SORU 1-2: "sessiz tahmin yasak, varsayım açıkça yazılır") doğrudan çelişmiyor (`varsayıldı` cümlesi sessiz değil) — ama **Tansu'nun yeni kuralıyla** çelişiyor: o, varsayımı açıkça yazmayı bile istemiyor, **soru sorulmasını** istiyor.

**İkinci boyut — soru TÜRÜ ayrımı hiç yok:** `downgrade_existence_disambiguate` yalnız `disambiguate` durumunu `is_existence_question`'a göre ayırıyor; `dominant` durumunda **hiçbir soru-türü ayrımı yok** — değer sorusu da belge-arama sorusu da aynı şekilde (liste + varsayıldı) işleniyor. Tansu'nun istediği: belge-arama sorusunda liste **kalsın** (F-3 gruplu, linkli), değer sorusunda liste **gitsin**, tek soru gelsin.

**Dosya/fonksiyon:**
- `backend/app/services/assist.py::ProjectAxisDecision`/`classify_project_axis` — davranış değişmiyor (sınıflandırma doğru), ama çağıran taraf artık soru türünü de bilmeli.
- `backend/app/services/assist.py::downgrade_existence_disambiguate` — adı/kapsamı genişlemeli: `dominant` durumunu da `is_existence_question`'a göre ayırmalı (belge-arama ise liste+varsayıldı kalsın, değer sorusuysa `none`'a düşüp F-4'ün tek sorusuna gitsin — `disambiguate`'in zaten yaptığı gibi).
- `backend/app/services/assist.py::render_no_data` — `dominant` + değer-sorusu kombinasyonunda artık `assist.question` (tek soru) döndürmeli, F-3 listesi/varsayıldı cümlesi değil.
- `backend/app/services/ask.py::answer_question` — pre-LLM short-circuit'in `dominant` dalı aynı ayrımı yapmalı.

**Ölçüm:** `scripts/dry_run_project_axis.py`'nin dev AMB/NEG setine, en az 2 "dominant + değer sorusu" örneği eklenmeli (şu an yok — mevcut set `disambiguate`/`none` ağırlıklı); hedef: bu örneklerde çıktı `question` (liste yok), belge-arama örneklerinde çıktı liste (var).

**SORU 2:** Bu, Adım 4'ün "çoğunluk belirgin değilse tahmin yok, belirginse varsayıldı" tasarımının **değer soruları için tamamen terk edilmesi** demek (belge-arama sorularında `dominant` davranışı aynı kalabilir). Onaylanıyor mu? **Önerim:** evet — Tansu'nun cevabı net ve ürün sahibinin kararı; "varsayıldı" cümlesi değer sorularında kalksın, yalnız belge-arama/varlık sorularında (zaten `is_existence_question` ile ayrılan yol) kalsın.

## (c) Belirsizlik tespiti yalnız proje ekseni değil

**Bugünkü kod:** `ProjectAxisKind`/`classify_project_axis` **tamamen ve yalnızca** proje eksenine kurulu — kredi, sözleşme, belge, dönem gibi başka eksenlerde hiçbir tespit mekanizması yok. Bu, Adım 4'ün KENDİ kapsamıydı (bilinçli, `URUN1_KARARLAR_VE_SIRA.md` §4 madde 5: "dürüst sınır… şimdi önermiyorum").

**Çelişki:** Tansu'nun T-6 cevabı — "belirsizlik tespitini yalnız proje eksenine kurmayın; F-4 genel bir kuraldır… ne olursa davranış aynıdır" — bu sınırı **ürün sahibi düzeyinde** reddediyor; Adım 4'ün "şimdilik proje ekseni" kapsam kararı artık yalnızca "henüz kodlanmadı" değil, "Tansu bunu yetersiz buluyor" oluyor.

**Dosya/fonksiyon:** Yeni bir eksen eklemek (`ProjectAxisKind`'a paralel `CreditAxisKind`/`ContractAxisKind` gibi) **büyük bir iş** — her eksen için "aday kümesi nasıl çıkarılır" (proje ekseninde zaten var olan `project_distribution`'ın muadili) ayrı ayrı tasarlanmalı. Bu plan kapsamında **tasarlanmadı**, yalnız boşluk olarak işaretlendi.

**SORU 3:** Kör test turu 1'in K6 sonucuna (≥2/3) göre karar vereceğimiz "dürüst sınır" (§4 madde 5) hâlâ geçerli mi, yoksa Tansu'nun T-6 cevabı bu kararı **öne mi** alıyor (kör testten önce en az bir ek eksen — örn. sözleşme/kredi — tasarlansın mı)? **Önerim:** sınır geçerli kalsın — Tansu'nun cevabı "genel kural olsun" diyor ama **kör testin K6 sonucunu** bekleme kararını (Naci, SORU 4, §2) geçersiz kılmıyor; kör test K6<2/3 çıkarsa bu madde önceliklenir.

## (d) Çelişki kalıbı dört durumlu

**Bugünkü kod:** Çalışan sistemde (ask/assist pipeline) **hiçbir çelişki-tespiti/F-6 şablonu yok** — tarandı (`assist.py`, `answer_prompt.py`, `ask.py`), "Kaynaklar farklı söylüyor" tarzı bir cümle **hiçbir yerde bulunamadı**. Yalnızca `seed_data/generator/validate_ledger.py::check_conflict_groups` var — ama o bir **build-time ledger doğrulayıcısı** (kasıtlı tuzakların işaretli olmasını zorluyor), **runtime cevap davranışı değil**. Bu, `URUN1_KARARLAR_VE_SIRA.md`'nin kendi tespitiyle uyumlu (§3.2 adım 7: "Bugün bu davranış YOK").

**Tansu'nun dört durumu (T-5):**
1. **Gerçek çelişki** (iki güncel kaynak farklı değer) → F-6 kalıbı: "Kaynaklar farklı söylüyor: … (belge, tarih) ve … (belge, tarih). Fark: … Hangisinin geçerli olduğunu teyit edebilir misiniz?"
2. **Sürüm farkı** (ödeme planı/tadil sürümleri) → **çelişki değil**; güncel söylenir, eski "tarihsel" etiketiyle yanında. (Bu zaten TEMPORAL TRUTH kuralının/`version_chain.py`'nin kapsamında — F-6'ya girmemeli.)
3. **Mükerrer kayıt** (aynı belgenin iki kaydı) → ikisi gösterilir, mükerrer olabileceği (aynı no/tutar/tarih) belirtilir, biri sessizce seçilmez.
4. **Eksik belge** → F-5 (madde a).

**Ledger'da tür alanı nasıl tutulur (soru soruyor, uygulanmadı):** Mevcut `deliberate_conflict`/`conflict_group` (Adım 5 Aşama A/C) yalnızca "bu bir kasıtlı çift" diyor, HANGİ TÜRDEN olduğunu ayırmıyor — Karatepe'nin 14,0/13,6'sı (gerçek çelişki) ile Yeşilova'nın iki ödeme planı sürümü (sürüm farkı, ÇELİŞKİ DEĞİL) şu an **aynı mekanizmayla** işaretli. `docs/plans/ADIM5_PF_PARTISI_PLAN.md`'de bu ayrım TÜR ETİKETİYLE öneriliyor (`conflict_kind: genuine_conflict | version_difference | duplicate | missing_document`).

**Dosya/fonksiyon (uygulama ileride):**
- `seed_data/generator/ledger_schema.py::Fact`/`Money` — yeni `conflict_kind: Literal[...] | None` alanı (`conflict_group`'un yanında).
- `seed_data/generator/validate_ledger.py::check_conflict_groups` — `conflict_kind` tutarlılığını da kontrol eder (bir grubun tüm üyeleri aynı `conflict_kind`'i taşımalı).
- **Tamamen yeni:** runtime'da F-6 şablonunu üreten bir fonksiyon (`backend/app/services/assist.py` içine, örn. `render_conflict(...)`) — retrieval'ın aynı konuda birden fazla, birbiriyle **uyuşmayan, her ikisi de güncel** kaynak döndürdüğünü tespit etmesi gerekir. Bu tespit mekanizması (b)/(c)'den bağımsız, **ayrı ve büyük bir iş** — bu plan onu TASARLAMIYOR, yalnız varlığını ve dört durumunu not ediyor.

**SORU 4:** F-6'nın runtime tespiti (retrieval'dan "bu iki kaynak aynı konuda farklı diyor" çıkarımı) ayrı bir plan/round mu olsun (`ADIM5_PF_PARTISI_PLAN.md`'nin kütüphanesi bitmeden tasarlanamaz — tuzaklar henüz üretilmedi), yoksa bu planın devamı mı olsun? **Önerim:** ayrı round — `URUN1_KARARLAR_VE_SIRA.md`'nin kendi sırası da bunu "adım 7 (c′)" olarak kütüphaneden (adım 5) SONRA, kör testten ÖNCE koyuyor; bu plan yalnız boşluğu belgeledi, tasarım o round'da yapılır.

---

## Özet — SORU listesi

1. `NO_ANSWER_TEXT` mi değişsin, yoksa eksik-belge-özel bir ek cümle mi? **Önerim: ek cümle.**
2. `dominant` + değer sorusu kombinasyonunda "varsayıldı" cevabı değer sorularında tamamen terk edilsin mi (belge-arama sorularında kalsın)? **Önerim: evet.**
3. Proje-dışı eksen (kredi/sözleşme/belge) tasarımı kör test K6 sonucuna mı bağlı kalsın? **Önerim: evet, sınır geçerli.**
4. F-6 runtime tespiti ayrı bir round'a (kütüphane sonrası, kör test öncesi) mı bırakılsın? **Önerim: evet.**

Hiçbiri uygulanmadı — bu dosya yalnız plan.
