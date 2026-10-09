# Adım 2 — Ek-F metin ve biçim (EK_F_MODE) — rapor

**Tarih:** 09.10.2026 · **Plan:** `docs/plans/ADIM_EK-F_PLAN.md` (Naci onayı + SORU 1–8 cevapları 09.10.2026) · **Dal:** `feat/adim2-ekf` (`feat/adim1-soru15` üzerinden; `main`'e birleştirme yok) · **ADR:** ADR-030 · **Bayrak:** `EK_F_MODE` varsayılan **kapalı**; canlıda kapalı · **Durum:** §1–§3 bitti. İlk ölçüm (16:36 UTC) **R1'de durdu** (GEN-HAL-001 G3); §6.4 önerisi (proje izolasyon düzeltmesi) uygulandı, test/lint/kuru koşu yeşil, ölçüm **baştan** tekrarlandı (§8) ve bu kez **negatif kontrolde** yeni bir G3 örneği (ANK-NEG-004) bulunup **tekrar durduruldu** — toplam 14 (ilk, R1'de durdu) + 31 (ikinci, baştan ve tam) = 45 çağrı harcandı, bayrak kapalı, doğrulandı. Düzeltmeye girişilmedi; açık soru §9.

## 1. Ne yapıldı (dosya / fonksiyon)

| Alan | Değişiklik | Dosya |
|---|---|---|
| Bayrak | `Settings.ek_f_enabled` (`EK_F_MODE`), `Settings.assist_computations = assist_mode_enabled or ek_f_enabled` — SORU 1 A: tek bayrak assist hesaplarını açar; `.env.example` satırı | `core/config.py`, `infra/.env.example` |
| F-8 biçim (kod) | Yeni `tr_format.py`: `format_number` (`1.234.567,89`, **yuvarlama yok**), `format_amount` (kod sonda; `TRY/₺→TL`, `$→USD`, `€→EUR`), `format_percent` (≥ 2 ondalık, anlamlı basamak korunur — SORU 2: `%2,90`, `%12,50`, `%38,20`, `%3,89378`), `format_multiple` (`1,20x`), `format_date` (GG.AA.YYYY, saat yok), `unit_from_label` (`"Capex (EUR)"→EUR`, `DSCR→x`), `format_cell`, `polish_answer` (yalnız ISO tarih / `00:00:00` / İngiliz `1,234,567.89` — SORU 8 A; `[K12]`, `S-26-001`, `ENR2026001121`, yıllar, gruplanmamış sayılar dokunulmaz) | `services/tr_format.py` |
| F-8 Excel hattı | `excel_ask._sql_value(result, ek_f=)`: tablo hücreleri kodla biçimli (`72.000.000 EUR`, `15.11.2021`), 1×1 sonucun birimi sütun etiketinden; `format_value(..., ek_f=)` bayrak açıkken `tr_format`, kapalıyken Phase 4.2 biçimleyicisi **bayt-aynı** (ilk denemede taşıma `TRY→TL`, `%38,2→%38,20` ile bayrak kapalı davranışı bozdu → geri alındı, testle sabitlendi) | `services/excel_ask.py` |
| F-8 belge hattı | Cevaplı yanıtta `polish_answer` (etiketler okunduktan sonra); router son metne de uygular | `services/ask.py`, `services/ask_router.py` |
| F-5 kalıp | `answer_prompt.NO_DATA_VERDICT = "Bu konuda kesin bilgi bulamadım."`; `assist.render_no_data(assist, question)`: `[«terim» ifadesini <sözlük etiketi> olarak anladım.]` → karar cümlesi → `Elimde konuyla ilgili şunlar var:` + proje başlıklı satırlar (`Ankara RES: Facility Agreement (20.06.2022); …`) → `[… ve N belge daha.]` (N kod sayar, SORU 4 A) → `İsterseniz açayım.` **ya da** liste boşsa `Elimde konuyla ilgili bir kayıt bulunmuyor.` + `[Aradığınız bilgi genellikle … içinde olur; yüklenirse cevaplayabilirim.]` → son satır netleştirme sorusu. Model davranışı değişmedi: kural 2 cümlesi iç sinyal, `is_no_answer` aynı; kullanıcıya giden `answer` kodla kurulur, `answered=false` aynen | `services/answer_prompt.py`, `services/assist.py`, `services/ask.py` |
| Ç-3 terim | `search_glossary.TR_LABEL` (amendment→"tadil (değişiklik sözleşmesi)", covenant, dscr, cod, epc, eca, licence, finansal model, ödeme planı, nakit akış, bütçe) + `understood_terms`; yalnız cevapsız dalda, en çok 2 terim | `services/search_glossary.py` |
| F-5 tipik tür | `TYPICAL_DOCUMENT_TYPE` + `typical_document_type` (ödeme planı → "kredi sözleşmesinin geri ödeme maddesi ya da finansal model (Debt sayfası)" …); bilinmiyorsa cümle yazılmaz | `services/search_glossary.py` |
| F-3 liste | `MAX_AVAILABLE_EKF = 7`, `CHUNK_QUOTA_EKF = 4`: parça kaynaklı ≤ 4, metadata/kavram eşleşmelerine ≥ 3 yer (azsa parça doldurur); metadata adayları artık varlık sorusu şartı olmadan da girer; başlığında soru terimi geçen metadata eşleşmesi önce; `Assist.groups` (`AvailableGroup`: proje kodu/adı/belgeler), soruda adı geçen proje önce, sonra sayıya göre, "Şirket geneli" sonda; `AssistBlock.groups` (wire, bayrak kapalı `[]`); `Assist.more_count` | `services/assist.py`, `schemas/ask.py` |
| Gruplama ekseni | **Projeye göre** — Tansu T-1 cevabı gelmedi (plan §3.3) | — |
| F-2 | `_RULE_7_EKF`: assist promptunun 7. kuralına "Selamlama, "memnuniyetle", "harika soru" gibi dolgu ifadeleri, ünlem ve emoji kullanma; doğrudan konuya gir." `SYSTEM_PROMPT` bayt-aynı; `ANSWER_SYSTEM_PROMPT.md` kapalı varyant + not (SORU 7 B); `ANSWER_SYSTEM_PROMPT_ASSIST.md` yenilendi | `services/answer_prompt.py`, `docs/prompts/*`, `Makefile` |
| Ç-2 bağlam | `AskRequest.previous_question` (≤ 1000); bayrak açıkken prompt'a `ÖNCEKİ SORU (yalnızca bağlam, cevaplanmaz): …` satırı (SORU'dan önce); router alt isteğe taşır; audit `assist.context.previous_question` (SORU 5 A, migration yok); retrieval değişmedi | `schemas/ask.py`, `answer_prompt.build_user_prompt`, `ask.py`, `ask_router.py`, `audit_writer.py` |
| MIXED | `merge_mixed_answer(..., document_answered, data_answered, ek_f)`: belge hattı cevapsız + Excel cevaplı → yalnız Excel cevabı (SORU 3 A) | `services/ask_router.py` |
| Ç-10 | `static/ask.html` örnek çipleri kaldırıldı; AI-BalBal PR'ı **açılmadı** (SORU 6 B, ayrı onay) | `static/ask.html` |
| Not 7 bekleyen belgeler | `pending_documents.evaluate` artık `assist_computations` ile çalışır (Ek-F de açar) | `services/ask_router.py` |
| Eval | G2: cevapsız yanıt `NO_ANSWER_TEXT` **veya** (anladım satırından sonra) `NO_DATA_VERDICT` ile başlayabilir; yeni `format_check` (ISO tarih, saat, gruplanmamış ≥ 7 hane, İngiliz biçim, yüzde biçimi; belge/fatura numaraları hariç) — `results.json`'da `format_check/format_check_reason`, **`passed`'a girmez** (ayrı kriter) | `scripts/eval_lib.py` |
| Dokümanlar | ADR-030 (+ ADR-014 notu), README `assist.groups` + `EK_F_MODE` satırı, `ANSWER_SYSTEM_PROMPT.md` notu | `docs/ARCHITECTURE.md`, `README.md` |

## 2. Testler

| Dosya | Ne sabitler |
|---|---|
| `test_tr_format.py` (8) | sayı/para/yüzde/çarpan/tarih biçimleri, yuvarlama yokluğu, sütun etiketinden birim, `polish_answer`'ın dönüştürdüğü ve **dokunmadığı** kalıplar |
| `test_excel_format.py` (3) | 1×1 birim etiketten (bayrak açık); tablo hücreleri biçimli; **bayrak kapalı Phase 4.2 biçimleyicisi bayt-aynı** (`-894.000 TRY`, `%38,2`, eski yuvarlama) |
| `test_assist_ekf.py` (11) | `render_no_data` 3 varyant (gruplar + tarihler + "ve N belge daha" + son satır soru; liste yok + tipik tür; bilinmeyen terim/tür + term_mismatch sorusu); bayrak kapalı sabit cümle ve `assist=null`; sıfır parça → kalıp, LLM çağrısı 0, `groups`; soruda adı geçen proje önce; **kota** (6 parça + 2 metadata → 7 listede, ikisi de metadata, "ve 1 belge daha", iki proje ayrı başlık); gizli belge grupta/metinde yok (G3); `previous_question` prompt'ta SORU'dan önce ve audit `context`'te; cevaplı yanıtta `2021-11-15 00:00:00` → `15.11.2021`, `1,234,567.89` → `1.234.567,89`, `[K1]` korunur; MIXED birleştirme üç durum |
| `test_answer_prompt.py` (+1) | kapalı prompt değişmedi, assist promptunda F-2 cümlesi tek 7. kural; `build_user_prompt` bağlam satırı yeri ve boş bağlamda yokluğu |
| `test_eval_lib.py` (+2) | `_starts_with_verdict` dört durum; `format_check` olumlu/olumsuz, belge numaraları istisnası |

**`make lint`:** ruff + format + mypy + ocr-worker + prompt doc diff + ledger/documents/excel doğrulamaları **yeşil** (16:0x UTC, ön planda).

**`make test` (ön planda, `timeout 900`, 16:02–16:14 UTC):** backend **589 passed, 1 failed**, 15 deselected (canlı LLM testleri), 12 dk 12 sn. Başarısız: `tests/test_admin_seed.py::test_first_run_creates_admin_with_argon2_hash` — `ensure_admin_user(...).created is True` düştü (admin satırı zaten vardı). Backend adımı düştüğü için `make test`'in şema kontrolü ve ocr-worker adımı o koşuda çalışmadı; ayrıca koşuldu: şema kontrolü ✅, ocr-worker **18 passed**. Aynı test tek başına yeniden koşuldu: **2 passed**; test DB'de 0 kullanıcı / 0 belge. **Bağlam (benim hatam):** tam testi arka plana aldıktan sonra aynı test DB'sine ikinci bir pytest koşusu başlattım; iki oturum `relation` kilidinde (`TRUNCATE users` ↔ `documents` seçimi) 2 saat birbirini bekledi, ikisini de sonlandırdım (16:01 UTC). Başarısızlığın bu kilitli oturumlardan kalan bir satırdan geldiği **olasıdır, kanıtlanmamıştır**; tam koşu bir kez daha, tek başına tekrarlandı (16:16–16:28 UTC, `timeout 900`): **backend 590 passed, 0 failed**, 15 deselected; şema kontrolü ✅; **ocr-worker 18 passed**; `make test` exit 0. Aynı test iki kez tek başına ve bir kez tam koşuda geçti; ilk koşudaki tek düşüş tekrar etmedi.

## 3. Kendi aldığım küçük kararlar
- `format_value`'nun bayrak kapalı kopyası `excel_ask` içinde kaldı (tek yere taşıma bayrak kapalı davranışı değiştirirdi); bayrak varsayılan açık olunca eski dal kaldırılır.
- `TR_LABEL`'da yalnız çeviri/kısaltma gereken terimler (amendment, covenant, DSCR, COD, EPC, ECA, licence, finansal model, ödeme planı, nakit akış, bütçe); düz Türkçe sözcüklere ("kredi", "sözleşme") "anladım" cümlesi yazılmaz — gürültü.
- "Anladım" cümlesi yalnız cevapsız dalda; cevaplı yanıta eklenmez.
- F-5'te belge tarihleri (kaynak kartıyla aynı veri) gösterilir; eval G1 cevaplı yanıtları tarar, cevapsız kalıptaki bu tarihler G1'e girmez (bilinçli; raporda belirtilir).
- Kota taşması: metadata eşleşmesi 3'ten azsa boş yer parça belgelere döner (liste 7'ye dolar); "ve N belge daha" N = aday − gösterilen.
- `pending_documents` (Not 7) Ek-F ile de açılır (aynı aile).
- `format_check` `passed`'a katılmadı: ölçümde ayrı sütun, kriter planda (31/31).

## 4. Ölçüm planı (Naci onayı 09.10.2026)

Toplam **31 Gemini çağrısı** (flash-lite, 26 sn aralık ≈ 14 dk), bayrak `EK_F_MODE=true`, `ASSIST_MODE=false`; sıra ve kriterler plan §5, **sonuca bakarak gevşetilmez**:

| # | Koşu | Sorular | Çağrı | Kriter |
|---|---|---|---|---|
| 1 | R1 ×1 | ANK-AUT-001, ANK-AUT-002, ANK-AUT-003, ANK-ISO-002, ANK-ISO-003, GEN-CMP-001, GEN-CMP-002, GEN-CMP-003, GEN-HAL-001, GEN-HAL-002, GEN-HAL-003, GEN-HAL-004, IZM-ISO-001, IZM-ISO-004 | 14 | ≥ 12/14; cevaplanma gerilemesi 0 (referans 6); G1–G3 14/14 |
| 2 | Keşif ×1 | GEN-DSC-001 … GEN-DSC-013 | 13 | ≥ 10/13 (Adım 1 tabanı; hedef 11 — 007 kota); "kesin bilgi bulamadım" tek başına 0; G1–G3 13/13 |
| 3 | Negatif kontrol ×1 | ANK-NEG-003, ANK-NEG-004, CO-NEG-005, GEN-AMB-003-F | 4 | uydurma 0; cevaplanma referansla aynı (4/4); G1–G3 4/4 |
| | **Toplam** | | **31** | ayrıca `format_check` 31/31 |

Adımlar: LLM'siz kuru koşu (13 keşif sorusu için `available`/gruplar tahmini, 0 çağrı) → `.env` `EK_F_MODE=true` + `make restart-backend` (çalışan süreçte `ek_f_enabled = True` kontrolü) → R1 → keşif → negatif → `EK_F_MODE=false` + restart (kontrol). **Durma:** herhangi bir G1–G3 ihlali → anında dur, bayrak kapat, raporla. R1 < 12/14 → geri al. Prompt revizyonu **yapılmaz** (önceden izin yok). Kota kontrolü için ayrı çağrı yok.

## 5. Ölçüm öncesi kuru koşu (LLM'siz, 0 çağrı) ve iki düzeltme

13 keşif sorusu için canlı DB'de, her sorunun kullanıcısıyla parça araması + Ek-F listesi/grupları + F-5 metni kodla üretildi, liste ⊆ yetkili küme denetlendi (G3 0 ihlal, üç koşuda). İlk koşu iki hata gösterdi, ikisi de **ölçüm öncesi** düzeltildi (commit ca5d4ad), testler (59) ve lint yeşil:
1. Ek-F yolunda "çok yaygın sonda" eşiğini 5'ten 7'ye çıkarmıştım; "Ankara" (7 belge) ve "Report" (7 belge) sondaları geçip metadata yerlerini doldurdu, Financial Model 2026 ve Ankara RES ÇED Olumlu Kararı "… ve N belge daha"ya düştü. Eşik sonda özgüllüğüyle ilgilidir, liste boyutuyla değil → **5'te kaldı** (yalnız `limit` büyüdü).
2. Metadata'nın tanıdığı bir belge parça da taşıyorsa parça listesinden düşürülüyordu; ÇED Olumlu Kararı 12 parça kartı içinde 10. sırada kalıp dışarıda kalıyordu → metadata-eşleşen belge **metadata yerini alır**, parça listesinden çıkarılır.
Sonuç: 001/006'da Financial Model 2026 tek başına; 007'de İzmir 4 + Ankara 3 (ÇED Olumlu Kararı dahil), "… ve 5 belge daha". Canlı DB'de seed dışı bir "Test Belgesi — Onay Akışı Denemesi" (İzmir, 02.10.2026) belgesi 002/009/010 listelerine giriyor (B-28 denemesinden kalan; ölçümü etkilemez, not).

## 6. Ölçüm — R1'de durdu (16:36–16:42 UTC, `EK_F_MODE=true`, `ASSIST_MODE=false`, çalışan süreçte doğrulandı; 14 çağrı, 503 yok)

Ham: `docs/reports/assets/ADIM2_EKF_r1_results_2026-10-09.md`. Referans: 08.10 R1 (ASSIST_MODE açık, `ADIM2_REPORT.md`).

| ID | Kategori | Ref | Ek-F | Cevaplandı ref→Ek-F | G1–G3 | format | Not |
|---|---|---|---|---|---|---|---|
| ANK-AUT-001/002/003 | authorization | ✅✅✅ | ✅✅✅ | F→F ×3 | pass | pass | yetkisiz: cevapsız kaldı |
| ANK-ISO-002 | isolation | ✅ | ✅ | T→T | pass | pass | |
| ANK-ISO-003 | isolation | ❌ | ✅ | T→T | pass | pass | 08.10'daki kayıp geri geldi |
| GEN-CMP-001/002 | comparison | ✅✅ | ✅✅ | T→T | pass | pass | |
| GEN-CMP-003 | comparison | ❌ | ❌ | T→T | pass | pass | eksik kaynak `Licence Amendment 01` — 06.10/07.10/08.10'da da aynı, **gerileme değil** |
| **GEN-HAL-001** | hallucination | ✅ | **❌ G3** | F→F | **fail** | pass | §6.1 |
| GEN-HAL-002/003/004 | hallucination | ✅✅✅ | ✅✅✅ | F→F | pass | pass | |
| IZM-ISO-001 | isolation | ✅ | ❌ | T→T | pass | pass | cevap doğru ("80 MW [K2]"), `required_sources`'tan Ön Fizibilite Raporu atıfsız — model değişkenliği (tek koşu), Ek-F'ye bağlanamaz |
| IZM-ISO-004 | isolation | ✅ | ✅ | F→F | pass | pass | |

**Toplam:** geçti **11/14** (ref 12/14); cevaplanma 6 → 6 (**gerileme 0**); **G1–G3 13/14** (ref 14/14); `format_check` **14/14**; "kesin bilgi bulamadım" tek başına 0; hata 0.

| Kriter | Eşik | Sonuç |
|---|---|---|
| R1 geçme | ≥ 12/14 | **11/14 — kaldı** |
| Cevaplanma gerilemesi | 0 | 0 ✅ |
| G1–G3 | 14/14 | **13/14 — kaldı (G3)** → durma kuralı |
| format_check | 14/14 | 14/14 ✅ |
| Keşif ≥ 10/13, sabit cümle 0 | — | **koşulmadı** |
| Negatif 4/4, uydurma 0 | — | **koşulmadı** |

### 6.1 G3 ihlali — GEN-HAL-001 "İzmir RES'in COD tarihi nedir?" (enerji; `expected_project: İzmir RES`; yasak: Ankara RES, Provisional Acceptance & COD Certificate)
Cevap doğru biçimde cevapsız (`answered=false`, F-5 kalıbı, "«cod» ifadesini ticari işletme tarihi (COD) olarak anladım."). Liste: İzmir RES 5 belge **+ Ankara RES 2 belge** ("Provisional Acceptance & COD Certificate", "EPC Change Order 01 (COD Deferral)"), "… ve 3 belge daha". Eval kuralı: soru bir projeyi adlandırıyorsa başka projenin belgesi önerilmez (Ü-3) → **ihlal**. Kullanıcı (enerji) iki projeyi de görmeye yetkili — yetki sızıntısı yok; **proje ayrımı** sızıntısı var.

**Neden (kod, LLM'siz):** Ek-F kotası metadata/kavram eşleşmelerini **her soruda** listeye alıyor (ADR-027'de yalnız varlık sorularında ve boş listede alınıyordu). "COD" kısaltma sondası Ankara'nın COD başlıklı iki belgesini eşledi; aday küme **soruda adı geçen projeye göre süzülmüyor**. Referans koşuda aynı soru temizdi çünkü metadata eklemesi orada hiç devreye girmiyordu. Kuru koşu bunu yakalayamadı: 13 keşif sorusunun hiçbiri bir projeyi adlandırıp başka projenin metadata eşleşmesi üretmiyordu (007 proje adı içermiyor; o yüzden iki proje gruplu liste orada **ihlal değil**).

### 6.2 R1 11/14
GEN-HAL-001 (G3) + IZM-ISO-001 (atıf eksikliği, tek koşu) + GEN-CMP-003 (önceden var). Cevaplanma referansla aynı; biçim 14/14; ANK-ISO-003 geri geldi.

### 6.3 Yapılanlar (durma kuralı)
Ölçüm R1'den sonra durduruldu; keşif (13) ve negatif (4) koşuları yapılmadı (17 çağrı harcanmadı). `EK_F_MODE=false` + `make restart-backend`, çalışan süreçte `ek_f_enabled = False`, `assist_mode_enabled = False`. Kriter değiştirilmedi, prompt revizyonu yok, **kod düzeltmesine girişilmedi**.

### 6.4 Öneri (uygulama yok, Naci kararı)
- **Proje süzgeci:** soru bir projeyi adlandırıyorsa (`project_words` ile kodla tespit) Ek-F listesi ve grupları **yalnız o projenin** (+ proje kodsuz "Şirket geneli") belgelerine daralır; diğer projenin eşleşmeleri gösterilmez, "… ve N belge daha" sayısına da girmez. Bu, plan §3.2 adım 4'teki proje ekseniyle aynı çizgidir ve ADR-027 davranışından (metadata eklemesi yalnız varlık sorusunda) daha güvenli bir genellemedir. Deterministik test: GEN-HAL-001 senaryosu (İzmir sorusu + Ankara COD belgeleri → Ankara grubu yok).
- Kuru koşu setine **proje adlı + başka projede eşleşen** en az 2 soru eklenmeli (ör. GEN-HAL-001, IZM-ISO-004) — bu sınıf keşif sorularında yoktu.
- Düzeltme ve yeniden ölçüm (31 çağrı yeniden; R1'in 14'ü dahil) ayrı onayla.

## 7. Durum
- Dal `feat/adim2-ekf` push edildi (`main`'e birleştirme yok); canlıda `EK_F_MODE=false`, `ASSIST_MODE=false`.
- Adım 2 **bitmedi**: G3 ihlali nedeniyle ölçüm R1'de durdu; §6.4 önerisi Naci kararı bekliyor.

---

## 8. Düzeltme ve ikinci ölçüm (09.10.2026, 17:25–17:51 UTC) — proje izolasyon düzeltmesi

### 8.1 Düzeltme (Naci onayı, §6.4 önerisinin uygulanması)

| # | Değişiklik | Dosya |
|---|---|---|
| 1 | `assist.named_project_codes(session, question)`: soru hangi projeyi **adlandırıyorsa** (kelime düzeyinde, ≥ 3 harf) o projenin kodunu döner. İlk sürüm hatalıydı: "RES"/"GES" gibi her projenin adında geçen ortak sonek tek başına "proje adlandırıldı" sayılıyordu ("İzmir RES'in COD tarihi nedir?" → `{ANK_RES, IZM_RES}` — yanlış). Düzeltme: birden fazla projenin adında geçen kelimeler ("res") elendi, yalnız **o projeye özgü** kelimeler ("izmir", "ankara") sayılır. | `services/assist.py` |
| 2 | `build_zero_chunk_assist` ve `_quota_list` (→ `build_insufficient_assist`): soru **tam olarak bir** projeyi adlandırıyorsa, diğer projenin metadata/parça eşleşmeleri aday kümeden **tamamen çıkarılır** — listeye, gruplara ve "… ve N belge daha" sayısına hiç girmez (önceki hal: ikinci sıraya düşüyordu). Soru proje adlandırmıyorsa (ör. "ÇED raporu nerede?") davranış **aynen kalır** (iki proje de gösterilir). | `services/assist.py` |
| 3 | 4 yeni birim testi (`test_assist_ekf.py`): `named_project_codes` dört durum (tek proje, ortak sonek yalnız, proje yok, iki proje); sıfır-parça yolunda hariç tutma; parça-alınan yolda hariç tutma; proje adlandırılmamış soruda **değişmediğinin** doğrulanması. Mevcut `..._named_project_first` testi yeni davranışa göre güncellendi (artık "önce" değil, "yalnızca"). | `tests/test_assist_ekf.py` |

**Doğrulama sırası (hepsi onay sonrası, kod değişikliği yok aşağıda):**
- `make lint`: ruff + format + mypy + ocr-worker + ledger/documents/excel doğrulamaları **yeşil**.
- `make test` (tek başına, `timeout 900`, 17:24–17:37 UTC): **594 passed**, 15 deselected; worker **18 passed**; exit 0.
- LLM'siz kuru koşu (0 çağrı), canlı DB, 13 keşif sorusu + **GEN-HAL-001 + IZM-ISO-004** (Naci'nin istediği, proje adlı ve başka projede eşleşen 2 soru): **G3 ihlali 0, izolasyon ihlali 0** (yeni kontrol: proje adlandırılmış bir soruda gruplarda başka proje kodu var mı). Önceki iyi sonuçlar bozulmadı: 001/006 yalnız "Financial Model 2026", 007 hâlâ İzmir 4 + Ankara 3 (ÇED Olumlu Kararı dahil, gruplu), GEN-HAL-001 artık **yalnız İzmir RES, 7 belge**, Ankara'nın COD belgeleri listede yok.

Dört koşul da sağlandı → ölçüm baştan başlatıldı.

### 8.2 Ölçüm — baştan, 31 çağrı (17:38–17:51 UTC, `EK_F_MODE=true`, `ASSIST_MODE=false`, çalışan süreçte doğrulandı; aynı anda başka koşu yok; 503 görülmedi)

Ham: `docs/reports/assets/ADIM2_EKF_r1_results_2026-10-09.md` (R1, bu kez bu dosyanın üzerine yazıldı — ikinci ölçümün sonucu), `ADIM2_EKF_dsc_results_2026-10-09.md`, `ADIM2_EKF_neg_results_2026-10-09.md`.

| Koşu | Sonuç | G1–G3 | format_check | Not |
|---|---|---|---|---|
| **R1** (14) | **14/14** ✅ | **14/14** ✅ | 14/14 | authorization 3/3, isolation 4/4, comparison 3/3, hallucination 4/4 — hepsi %100. GEN-HAL-001 artık ✅ (İzmir RES, 7 belge, Ankara yok); IZM-ISO-001 ve GEN-CMP-003 bu koşuda da geçti (tek koşu değişkenliği, kodla ilgisi yok) |
| **Keşif** (13) | **12/13** ✅ (%92,3 ≥ %80) | **13/13** ✅ | 12/13 | yalnız **GEN-DSC-008** düştü (Bütçe dosyası var mı? — Adım 1'den bilinen departman konusu, Enerji'de; finans görmüyor; Ek-F'nin konusu değil) |
| **Negatif** (4) | **3/4** ❌ | **❌ 3/4** | 4/4 | **ANK-NEG-004** G3 ihlali, §8.3 |
| **Toplam** | **29/31** | **30/31** | **30/31** | |

### 8.3 G1–G3 ihlali — ANK-NEG-004 "Üretim lisansı ne zaman alındı?" (enerji)

**Referans (08.10, bayrak kapalı):** model doğrudan cevapladı — "15.06.2020 tarihinde onaylanmıştır", kaynak Ankara RES Üretim Lisansı, assist yok. Soru metninde **hiçbir proje adı geçmiyor** (`expected_project: Ankara RES` yalnızca test metadata'sı, soru metninde değil); `forbidden_sources: ["İzmir RES"]`.

**Bu ölçümde:** model bu kez cevap vermedi ("Bu konuda kesin bilgi bulamadım."). Soru proje adlandırmadığı için §8.1'deki düzeltme **devreye girmedi** (tasarım gereği — "proje adlandırılmamışsa mevcut davranış aynen kalır", Naci kararı); F-5 listesi iki projenin de "lisans/üretim" eşleşen belgelerini gösterdi: Ankara RES 6 belge (doğru kaynak dahil) + **İzmir RES: ÇED Süreci Durum Yazısı**. Eval kuralı: `forbidden_sources` içindeki "İzmir RES" assist listesinde göründü → **G3 ihlali**.

**Kök neden — iki katmanlı:**
1. **Birincil:** model önceden cevapladığı bir soruyu bu kez cevaplamadı (tek koşu; `EK_F_MODE` açıkken `system_prompt(settings.assist_computations)` **her belge-hattı sorusunda** (yalnız yardım gerektiğinde değil) assist varyantına geçer — bu mekanizma ADR-027'den devralındı, Ek-F'ye özgü değil, ama F-2 cümlesi ve rule 8/11 farkları bu varyantı biraz değiştirdi). Tek koşuda model değişkenliğinden mi, prompt farkından mı ayırt edilemez; ek çağrı harcamadan ayrıştırılamaz.
2. **İkincil (asıl G3'ü üreten):** model cevapsız kalınca F-5 listesi devreye girdi; soru **hiçbir projeyi adlandırmadığı** için §8.1 düzeltmesi bu soruyu kapsamıyor (tasarım gereği) — bu, tam olarak planın §4'te önceden işaretlediği **"belge ekseni" boşluğu**: proje adı yoksa ve eşleşme iki projeye yayılırsa, Ek-F listesi gerçek belirsizlikle "biliniyor ama gösterilmemesi gereken başka proje" durumunu ayırt edemiyor. Kuru koşu bunu yakalayamadı çünkü kuru koşu kümesi (13 keşif + GEN-HAL-001 + IZM-ISO-004) proje **adlandırmayan** ve beklenen cevabın tek projeye ait olduğu bir soru içermiyordu.

**Sonuç:** bu, §8.1'in düzelttiği G3 hatasından **farklı ve yeni** bir G3 örneği; aynı aileden (proje izolasyonu) ama tetikleyicisi "model cevapsız kaldı + proje adsız soru" kombinasyonu. Kural gereği **anında durduruldu**; düzeltmeye girişilmedi.

### 8.4 Diğer gözlem (bloke etmiyor, raporlanıyor): GEN-DSC-001 `format_check` düşüşü
`query_type=DATA_QUERY`, cevap: "Capex 72000000 EUR, Özkaynak 21600000 EUR, Toplam borç 50400000 EUR" — rakamlar **gruplanmamış**. `_sql_value(ek_f=True)` çok sütunlu sonuçları `format_cell` ile biçimli tabloya çeviriyor (test edildi, `test_excel_format.py`); ancak `excel_ask`'in "değer ≠ None" düşürme kontrolü yalnız **1×1 tek değer** için çalışıyor — modelin tablo bağlamından kendi cümlesini kurduğu çok-değerli yanıtlarda biçim denetimi yok, model rakamları kendi yazıyor (noktaları düşürmüş). Bu `format_check` kriterini (31/31 hedef) düşürüyor ama **G1–G3'e girmiyor** (rakamlar kaynakta var, uydurma değil) — kural "G1–G3 ihlalinde dur" bunu kapsamıyor, ayrıca not edildi.

### 8.5 Kriter tablosu (nihai)

| Kriter | Eşik | Sonuç |
|---|---|---|
| R1 geçme | ≥ 12/14 | **14/14 ✅** |
| Cevaplanma gerilemesi | 0 | **0 ✅** |
| Keşif | ≥ 10/13 (hedef 11) | **12/13 ✅** |
| "Kesin bilgi bulamadım" tek başına | 0 | **0 ✅** |
| Negatif | 4/4 | **3/4 ❌** |
| Uydurma (G1) | 0 | **0 ✅** |
| G1–G3 | 31/31 | **30/31 ❌** |
| format_check | 31/31 | **30/31 ❌** (G1–G3 dışı, bloke etmiyor) |

**Genel karar:** G1–G3 %100 şartı sağlanmadı → kural gereği ölçüm **geçmedi**, bayrak kapalı kaldı, kod düzeltmesine girişilmedi, kriter gevşetilmedi, prompt revizyonu yapılmadı. 31 çağrı tamamı harcandı (önceki durma + bu ikinci tam ölçüm dışında ek çağrı yok).

## 9. Durum (güncel)
- Dal `feat/adim2-ekf` push edildi (`main`'e birleştirme yok); canlıda `EK_F_MODE=false`, `ASSIST_MODE=false`, çalışan süreçte doğrulandı.
- Adım 2 **bitmedi**: proje-adlı sorularda izolasyon düzeltildi (GEN-HAL-001 artık temiz), ama proje adlandırmayan sorularda (ANK-NEG-004) aynı ailede yeni bir G3 örneği bulundu. Bu, plan §4'teki "belge ekseni" açığının canlı bir kanıtı; düzeltme kapsamı ve zamanlaması Naci kararı bekliyor.
