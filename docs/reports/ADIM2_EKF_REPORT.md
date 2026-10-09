# Adım 2 — Ek-F metin ve biçim (EK_F_MODE) — rapor

**Tarih:** 09.10.2026 · **Plan:** `docs/plans/ADIM_EK-F_PLAN.md` (Naci onayı + SORU 1–8 cevapları 09.10.2026) · **Dal:** `feat/adim2-ekf` (`feat/adim1-soru15` üzerinden; `main`'e birleştirme yok) · **ADR:** ADR-030 · **Bayrak:** `EK_F_MODE` varsayılan **kapalı**; canlıda kapalı · **Durum:** §1–§3 bitti (kod, birim testleri, `make test`, `make lint`); **ölçüm yapılmadı, Naci onayı bekliyor** (§4).

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

## 4. Ölçüm planı — **onay bekliyor** (henüz 0 çağrı)

Toplam **31 Gemini çağrısı** (flash-lite, 26 sn aralık ≈ 14 dk), bayrak `EK_F_MODE=true`, `ASSIST_MODE=false`; sıra ve kriterler plan §5, **sonuca bakarak gevşetilmez**:

| # | Koşu | Sorular | Çağrı | Kriter |
|---|---|---|---|---|
| 1 | R1 ×1 | ANK-AUT-001, ANK-AUT-002, ANK-AUT-003, ANK-ISO-002, ANK-ISO-003, GEN-CMP-001, GEN-CMP-002, GEN-CMP-003, GEN-HAL-001, GEN-HAL-002, GEN-HAL-003, GEN-HAL-004, IZM-ISO-001, IZM-ISO-004 | 14 | ≥ 12/14; cevaplanma gerilemesi 0 (referans 6); G1–G3 14/14 |
| 2 | Keşif ×1 | GEN-DSC-001 … GEN-DSC-013 | 13 | ≥ 10/13 (Adım 1 tabanı; hedef 11 — 007 kota); "kesin bilgi bulamadım" tek başına 0; G1–G3 13/13 |
| 3 | Negatif kontrol ×1 | ANK-NEG-003, ANK-NEG-004, CO-NEG-005, GEN-AMB-003-F | 4 | uydurma 0; cevaplanma referansla aynı (4/4); G1–G3 4/4 |
| | **Toplam** | | **31** | ayrıca `format_check` 31/31 |

Adımlar: LLM'siz kuru koşu (13 keşif sorusu için `available`/gruplar tahmini, 0 çağrı) → `.env` `EK_F_MODE=true` + `make restart-backend` (çalışan süreçte `ek_f_enabled = True` kontrolü) → R1 → keşif → negatif → `EK_F_MODE=false` + restart (kontrol). **Durma:** herhangi bir G1–G3 ihlali → anında dur, bayrak kapat, raporla. R1 < 12/14 → geri al. Prompt revizyonu **yapılmaz** (önceden izin yok). Kota kontrolü için ayrı çağrı yok.

## 5. Durum
- Kod + testler + lint bitti; dal push edildi; canlı backend **yeniden başlatılmadı** (bind-mount ile dosyalar güncel ama süreç eski; ölçüm öncesi restart gerekir, bayrak kapalıyken davranış zaten bayt-aynı).
- Ölçüm için Naci onayı bekleniyor (31 çağrı, yukarıdaki sorular).
