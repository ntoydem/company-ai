# Adım 4 — Proje ekseni belirsizlik tespiti + projesiz soruda proje çıkarımı — rapor

**Tarih:** 09.10.2026 · **Plan:** `docs/plans/ADIM4_PLAN.md` (Naci onayı + SORU 1–5 cevapları 09.10.2026) · **Dal:** `feat/adim4-proje-ekseni` (`feat/adim2-ekf` üzerinden; `main`'e birleştirme yok) · **ADR:** ADR-030'un devamı (Ek-F rendering layer) · **Bayrak:** `EK_F_MODE` (ayrı bayrak yok); canlıda kapalı · **Ölçüm:** retrieval-only, **0 Gemini çağrısı** · **Durum:** kod + testler + lint bitti; ölçüm koşuldu; **orijinal 5 soruluk kriter tam karşılanmadı** (AMB 3/5 < hedef 4/5), **sonuca bakarak gevşetilmedi**; belge-varlığı kriteriyle eklenen 1 yeni soru (GEN-AMB-006) **ayrı** sayıldı (1/1) — §3.1, §4. Held-out ölçümü ve eşik kilidi Adım 5'e ertelendi — §6.

## 1. Ne yapıldı (dosya / fonksiyon)

| Alan | Değişiklik | Dosya |
|---|---|---|
| Ayarlar | `Settings.project_axis_disambig_spread` (env `PROJECT_AXIS_DISAMBIG_SPREAD`, varsayılan 0.5), `Settings.project_axis_dominant_share` (env `PROJECT_AXIS_DOMINANT_SHARE`, varsayılan 0.75) — tek bayrak `EK_F_MODE`, yeni bayrak yok | `core/config.py`, `infra/.env.example` |
| Saf çekirdek | `ProjectAxisDecision` (`kind: named\|disambiguate\|dominant\|none`, `project_code`, `codes`); `project_distribution(cards)`; `classify_project_axis(distribution, named, *, disambig_spread, dominant_share)` — DB'siz, saf fonksiyon. `named` ≥ 2 proje → her zaman `none` (Ü-3'ün çoklu-proje yolu, disambiguate değil). Şirket geneli (`project_code=None`) adaylar hiçbir eşiğe girmez | `services/assist.py` |
| Disambiguate render | `disambiguate_question(session, codes)` ("Hangi projeyi kastediyorsunuz: A mi, B mi?", proje adları kapıdan); `build_disambiguate_assist` — liste yok, "anladım"/"elimde var" çerçevesi yok (F-4: "içerik sıralamaz"); `render_no_data`'da `kind=="disambiguate"` → yalnız soru satırı | `services/assist.py` |
| Dominant render | `Assist.inferred_project` set edilince `render_no_data` karar cümlesinden sonra **"{Proje} projesine ait olduğu varsayıldı."** satırı ekler — sessiz tahmin yok (Naci 09.10.2026) | `services/assist.py` |
| LLM'den önce kesme | `ask.py::answer_question`: parçalar + `by_id` yüklendikten **hemen sonra, prompt kurulmadan önce** `classify_project_axis` çağrılır; `disambiguate` ise LLM **hiç çağrılmaz**, sonuç doğrudan döner. `named`/`dominant`/`none` kesmez; karar `build_insufficient_assist`'e taşınır (model cevapsız kalırsa yeniden hesaplanmaz) | `services/ask.py` |
| Varlık sorusu düzeltmesi | **Regresyon bulundu ve düzeltildi (bu round içinde):** `downgrade_existence_disambiguate(decision, question)` — bir varlık sorusunda ("… nerede?", "… var mı?") `disambiguate` **asla** devreye girmez, F-4 (2)'nin "zayıf eşleşmede listele + teyit et" yolu korunur. Bulgu: ilk sürümde "ÇED raporu nerede?" (DSC-007 şekli) 1:1 ya da 4:3 bölünmede `disambiguate`'e düşüyordu — mevcut `test_unnamed_project_question_still_shows_every_matching_project` testi bunu yakaladı | `services/assist.py`, `services/ask.py` |
| Şema | `AssistBlock.kind` Literal'i `disambiguate` değerini alır; yeni `AssistBlock.axis: Literal["project"] \| None` alanı | `schemas/ask.py` |
| Eval | `ledger_schema.AssistKind` → `disambiguate` eklendi; `assist_check` zaten jenerik, değişmedi | `seed_data/generator/ledger_schema.py` |
| Ölçüm aracı | `scripts/dry_run_project_axis.py` (yeni, `dry_run_ambiguity.py` ile aynı desen): 14 soru için gerçek retrieval + gerçek `classify_project_axis`, 0 LLM | `scripts/dry_run_project_axis.py` |

## 2. Testler

| Dosya | Ne sabitler |
|---|---|
| `test_project_axis.py` (10, yeni) | `classify_project_axis` saf: named önceliği, ≥2 adlandırma → none, yakın dağılım → disambiguate (+ 3 projeli close-code listesi), net çoğunluk → dominant, aradaki boşluk → none, tek proje/0 aday → none, şirket geneli adaylar sayılmaz, eşikler çağırandan okunur; `project_distribution` sayımı |
| `test_assist_ekf.py` (+4) | disambiguate LLM'den önce keser (`fake_llm.requests == []`), cevap yalnız sabit soru; iki proje adlandırılmış soru hiçbir zaman disambiguate olmaz (LLM çağrılır); sıfır-parça dominant → daraltma + "varsayıldı" cümlesi + azınlık hiç görünmez; parçalı dominant (ANK-NEG-004 şekli) uçtan uca → aynı |
| `test_assist_ekf.py` (regresyon düzeltmesi) | `..._named_project_first` testi yeniden adlandırıldı/güncellendi (proje izolasyon düzeltmesi, önceki round); `test_unnamed_project_question_still_shows_every_matching_project` **bu round'da kırıldı, düzeltmeyle (existence downgrade) geri geldi** |
| `test_eval_lib.py` (+1) | `expect_assist="disambiguate"` eşleşmesi; disambiguate sorusu `format_check` geçer (rakam yok) |

**`make lint`:** ruff + format + mypy (bare, proje genelinde) **yeşil**. **`make test`** (tek başına, `timeout 900`, 19:54–20:07 UTC): backend **609 passed**, 15 deselected; şema kontrolü ✅; ocr-worker **18 passed**; exit 0.

## 3. Ölçüm — retrieval-only, 0 LLM çağrısı (09.10.2026)

Ham çıktı: `docs/reports/assets/DRY_RUN_PROJECT_AXIS_2026-10-09.txt`. Eşikler (dev setinde tutulan, ölçüm boyunca değiştirilmeyen): `PROJECT_AXIS_DISAMBIG_SPREAD=0.5`, `PROJECT_AXIS_DOMINANT_SHARE=0.75`.

### 3.1 Dev AMB (5) — hedef ≥ 4/5

| ID | Soru | Dağılım (gerçek retrieval) | Sonuç | İsabet |
|---|---|---|---|---|
| GEN-AMB-001 | Sözleşmenin vadesi ne zaman doluyor? | Ankara 26 / İzmir 2 / genel 1 (68 parça) | `dominant` ANK_RES | ❌ |
| GEN-AMB-002 | Raporda belirtilen DSCR değeri kaç? | Ankara 6 / İzmir **0** (11 parça) | `none` | ❌ |
| GEN-AMB-003 | Son tadil neyi değiştirdi? | yakın bölünme | `disambiguate` (ANK_RES, IZM_RES) | ✅ |
| GEN-AMB-004 | Lisans ne zaman alındı? | yakın bölünme | `disambiguate` (ANK_RES, IZM_RES) | ✅ |
| GEN-AMB-005 | Toplantıda ne karar alındı? | yakın bölünme | `disambiguate` (ANK_RES, IZM_RES) | ✅ |

**İsabet: 3/5 (%60) — hedef ≥ 4/5 karşılanmadı.**

### 3.2 Dev NEG (9) — hedef yanlış alarm 0/9

| ID | Soru | Sonuç |
|---|---|---|
| ANK-NEG-001 | Ankara RES kredisinin vadesi kaç yıl? | `named` ANK_RES |
| ANK-NEG-002 | Ankara RES finansmanında ihracat kredi kurumu kredisi ne kadar? | `named` ANK_RES |
| ANK-NEG-003 | Kredi sözleşmesinin vadesi kaç yıl? | `none` |
| **ANK-NEG-004** | Üretim lisansı ne zaman alındı? | **`dominant` ANK_RES** ✅ (bu round'un somut kapanış kriteri) |
| CO-NEG-005 | Denetim komitesi üyeleri hangi kararla atandı? | `dominant` ANK_RES |
| GEN-AMB-003-F | Son tadil neyi değiştirdi? (finans) | `none` |
| GEN-CMP-001 | Ankara RES üretim lisansı ne zaman alındı, İzmir RES önlisansı ne zaman alındı? | `none` |
| GEN-CMP-002 | Ankara RES üretim lisansı ile İzmir RES önlisansı — hangisi daha önce alındı? | `none` |
| GEN-CMP-003 | Ankara RES ile İzmir RES'in kurulu gücü hangisi daha büyük? | `none` |

**Yanlış alarm: 0/9 (%0) — hedef karşılandı. ✅**
**ANK-NEG-004 == `dominant`/`ANK_RES` — hedef karşılandı. ✅**

### 3.3 Kriter tablosu

| Kriter | Eşik | Sonuç |
|---|---|---|
| Dev AMB isabet (orijinal 5) | ≥ 4/5 | **3/5 — karşılanmadı** |
| Dev AMB isabet (yeni, GEN-AMB-006) | — (bilgi amaçlı, ayrı) | **1/1** |
| Dev NEG yanlış alarm | 0/9 | **0/9 ✅** |
| ANK-NEG-004 | `dominant`/`ANK_RES` | **✅** |

**Genel karar: orijinal 5 sorunun kriteri tam karşılanmadı.** Kurala göre eşik **oynatılmadı**, GEN-AMB-001/002 dev setten **çıkarılmadı**, sayım değiştirilmedi. GEN-AMB-006'nın sonucu (1/1) **ayrı** sayılır; "hedef karşılandı" iddiası yapılmaz — bu tek bir ek örnek, istatistiksel bir düzeltme değil.

## 4. Kök neden ve ek kanıt — belge varlığı (eşik sorunu değil)

### 4.1 GEN-AMB-001/002: "korpus-gereği-belirsiz-değil" — kanıt belge varlığından, dedektör çıktısından değil

Aşağıdaki sayılar **dedektörden değil**, `documents` tablosunun kendisinden: her iki proje için, sorunun konusuyla ilgili belge **türünün** kaç kez geçtiği.

| Soru | İlgili belge türü | Ankara | İzmir | Kaynak |
|---|---|---|---|---|
| GEN-AMB-001 "Sözleşmenin vadesi ne zaman doluyor?" | `Facility Agreement` | **6** | **0** | `documents` tablosu, `document_type`/`project_id` grupla |
| GEN-AMB-002 "Raporda belirtilen DSCR değeri kaç?" | `Covenant Report` | **3** | **0** | aynı |

İzmir RES'in bu iki belge türünden **hiç** kaydı yok (henüz imzalı bir finansman sözleşmesi yok, dolayısıyla kredi taahhüdü/DSCR raporu da yok — `NACI_CEVAP_2026-10-08.md` §3.1 ile uyumlu). Bu, sorunun kendisinin değil, **bu korpusta bu konunun** iki projeye eşit dağılmadığının doğrudan kanıtı; dedektörün 3.1'de ürettiği `dominant`/`none` çıktısı bu belge-varlığı gerçeğinin bir **sonucu**, nedeni değil.

**Not (sayıma/kritere etkisi yok):** GEN-AMB-001 ve GEN-AMB-002 bu bulguyla **"korpus-gereği-belirsiz-değil"** olarak işaretlenir (bilgi notu); dev AMB setinden çıkarılmadı, kriter (≥4/5, 5 soru üzerinden) ve sonuç (3/5) **aynen** kalır.

### 4.2 Yeni soru — belge varlığı kriteriyle seçildi (GEN-AMB-006)

Seçim kriteri yalnızca belge varlığı: `documents` tablosunda **iki projede de aynı belge türünden ≥ 2 kayıt** olan konular arandı (dedektör çıktısına bakılmadan). Tüm proje-belge türü kombinasyonları tarandığında bu koşulu sağlayan **tek** tür bulundu:

| Belge türü | Ankara | İzmir |
|---|---|---|
| `Legal Review Memo` | **2** | **2** |

(Diğer tüm türlerde en az bir proje 0 veya 1 kayıt taşıyor; `Teknik Rapor` İzmir'de 2 ama Ankara'da 0; `Budget Approval` her ikisinde 1.) Bu yüzden **en fazla 3** değil, **1** yeni soru eklendi — kriter başka bir seçeneğe izin vermedi, zorlanmadı.

**GEN-AMB-006** ("Hukuki inceleme notunda ne tespit edildi?", `ask_as_user: hukuk`) önce yazıldı ve commit edildi (bcc71fe), **sonra** kuru koşu çalıştırıldı. Sonuç: `disambiguate`, `codes=('ANK_RES','IZM_RES')` — **1/1**, soruya göre değiştirilmedi.

**Genel sonuç:** iki ayrı sayı — orijinal 5 sorunun 3/5'i (hedef ≥4/5 karşılanmadı) ve yeni 1 sorunun 1/1'i (bilgi amaçlı). Birleştirilip "4/6 ≥ 4/5" gibi bir iddia yapılmaz.

## 5. Durum
- Dal `feat/adim4-proje-ekseni` push edildi (`main`'e birleştirme yok); canlıda `EK_F_MODE=false`, `ASSIST_MODE=false` — bu ölçüm hiç dokunmadı (0 LLM, 0 bayrak değişimi).
- Adım 4 kodu ve testleri tamamlandı; dev ölçüm: NEG ve ANK-NEG-004 ✅, orijinal AMB 3/5 ❌ (gevşetilmedi), yeni AMB 1/1 (ayrı, bilgi amaçlı).

## 6. Held-out ve eşik kilidi — Adım 5'e ertelendi (Naci kararı, 09.10.2026)

Held-out ölçümü (5 yeni AMB + 5 yeni NEG, Naci/danışman yazacak) ve nihai eşik kilidi **şimdi yapılmaz**; Adım 5 (veri kütüphanesi, Ç-9 B yeniden adlandırma + yeni belgeler) **sonrasına** ertelendi. Gerekçe: §4'teki bulgu zaten korpusun kendisinin eksik olduğunu gösteriyor (İzmir'de bazı belge türleri hiç yok); Adım 5 bu korpusu kökten değiştirecek, bugünkü `0.5`/`0.75` eşikleri o zaman **yeniden doğrulanacak**. Bu rapordaki ölçüm bir **ara doğrulamadır**, nihai kilit değildir — `docs/plans/ADIM4_PLAN.md` §3'teki sıra notuna işlendi.
