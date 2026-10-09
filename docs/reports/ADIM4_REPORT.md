# Adım 4 — Proje ekseni belirsizlik tespiti + projesiz soruda proje çıkarımı — rapor

**Tarih:** 09.10.2026 · **Plan:** `docs/plans/ADIM4_PLAN.md` (Naci onayı + SORU 1–5 cevapları 09.10.2026) · **Dal:** `feat/adim4-proje-ekseni` (`feat/adim2-ekf` üzerinden; `main`'e birleştirme yok) · **ADR:** ADR-030'un devamı (Ek-F rendering layer) · **Bayrak:** `EK_F_MODE` (ayrı bayrak yok); canlıda kapalı · **Ölçüm:** retrieval-only, **0 Gemini çağrısı** · **Durum:** kod + testler + lint bitti; ölçüm koşuldu; **kriter tam karşılanmadı** (AMB 3/5 < hedef 4/5), **sonuca bakarak gevşetilmedi** — §4.

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
| Dev AMB isabet | ≥ 4/5 | **3/5 — karşılanmadı** |
| Dev NEG yanlış alarm | 0/9 | **0/9 ✅** |
| ANK-NEG-004 | `dominant`/`ANK_RES` | **✅** |

**Genel karar: kriter tam karşılanmadı.** Kurala göre eşik **oynatılmadı**; aşağıda tanım/kök neden incelendi, sonuca bakarak gevşetme yapılmadı.

## 4. İki AMB kaçağının kök nedeni (eşik sorunu değil, korpus gerçeği)

**GEN-AMB-001 (Ankara 26 / İzmir 2, pay ≈ %93):** İzmir RES henüz geliştirme aşamasında; imzalı bir kredi/finansman sözleşmesi yok (bu, cevaplarda tekrar eden bir gerçek — bkz. `NACI_CEVAP_2026-10-08.md` §3.1). "Sözleşme" terimi bu yüzden gerçek belgelerde **doğası gereği** Ankara'ya ağırlıklı; dağılım objektif olarak çoğunluklu, yakın değil. Eski V3 detektörü bu soruyu kelime kalıbıyla ("belge-sınıfı kelimesi, proje adı yok") ateşliyordu — gerçek belge dağılımına bakmıyordu. Adım 4'ün sayıya dayalı tanımı burada **daha dürüst**: soru metni belirsiz görünse de, bu demo korpusunda gerçekten %93 Ankara'ya ait.

**GEN-AMB-002 (Ankara 6 / İzmir 0):** DSCR bir kredi taahhüdü ölçütüdür; İzmir'in henüz kredisi yok → İzmir'de **hiç** DSCR belgesi/parçası yok. Dağılımda ikinci proje **hiç görünmüyor** (`len(by_project) < 2`) → `none` otomatik, eşikten bağımsız. Hiçbir eşik değeri bu soruyu `disambiguate`'e taşıyamaz çünkü karşılaştırılacak ikinci bir aday hiç yok.

**Sonuç:** bu iki soru, dev `ambiguous` kategorisine eski (sözcük kalıbı tabanlı) V3 detektörüyle yazılmış; gerçek korpusta **cevaplar zaten tek projeye ait** (biri ağırlıklı, biri münhasıran). Adım 4'ün tanımı değil, bu iki sorunun **kategorisi** gözden geçirilmeli — ya held-out/dev AMB setinden çıkarılmalı ya da İzmir'e de "sözleşme"/"DSCR" içeren bir belge eklenerek gerçekten ambiguous hale getirilmeli (kütüphane adımı, Adım 5). Eşik **değiştirilmedi**.

## 5. Durum
- Dal `feat/adim4-proje-ekseni` push edilecek (`main`'e birleştirme yok); canlıda `EK_F_MODE=false`, `ASSIST_MODE=false` — bu ölçüm hiç dokunmadı (0 LLM, 0 bayrak değişimi).
- Adım 4 kodu ve testleri tamamlandı; dev ölçüm kriteri **kısmen** karşılandı (NEG ve ANK-NEG-004 ✅, AMB 3/5 ❌). Held-out henüz istenmedi (Naci kararı: kod bitince istenecek — bu rapor o eşiği karşılıyor, ama AMB sonucu nedeniyle held-out istemeden önce Naci'nin §4'teki bulguyu değerlendirmesi gerekiyor).
