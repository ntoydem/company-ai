# Tarih/saat Raporu — demo takvimi vs gerçek takvim, tarih hesabının koda taşınması

**Tarih:** 05.10.2026  **Model:** Claude Sonnet 5  **Tag:** yok (düz commit + PHASES.md notu)  **Commit:** bu rapor ile aynı commit
**Plan:** `docs/plans/TARIH_SAAT_PLAN.md` · **ADR:** **ADR-026** (yeni) · **Kapsam:** backend + ledger (B-28b'den bağımsız, cross-cutting) + AI-BalBal küçük bir PR ("Bugün" rozeti)

Naci'nin SORU cevapları (05.10.2026, planın önerisiyle aynı yönde): (1) `DOC-ANK-OPS-009`'a `expiration_date` eklensin, "yenileme eksik, süresi dolmuş" kurgusu — **tarih yazılmadı**, 2-3 aday §6'da sunuluyor, onay bekliyor; (2) sistem-olgusu soruları yalnızca (a) frontend rozeti, backend kısa devresi (b) **yok**; (3) `company_timezone` varsayılanı `Europe/Istanbul`; (4) diğer üç aday (EPC-007, DEV-001, İzmir DEV-001) bu turda eklenmedi.

## 1. Kabul kriterleri (plan §7)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| T01 | `temporal.today(settings)` tek giriş noktası; `settings.demo_today`'e doğrudan erişim yalnızca orada | ✅ | `grep -rn "settings.demo_today" backend/app/` → yalnızca `app/services/temporal.py`; `ask.py`/`excel_ask.py`/`auth.py` artık `temporal.today(settings)` çağırıyor |
| T02 | `DEMO_MODE=false` + `COMPANY_TIMEZONE` gerçek saatten doğru günü döndürür; `true` (varsayılan) `demo_today`'i aynen döndürür | ✅ | `test_temporal.py::test_demo_mode_on_returns_demo_today`, `::test_demo_mode_off_returns_the_real_day_in_company_timezone` (saat sahteleştirilmiş, gerçek saat beklemedi) |
| T03 | `expiration_note()` saf fonksiyon: doğru TR cümle + gün sayısı; boşsa `None`; eski kaynak byte-identik | ✅ | `test_temporal.py::test_expiration_note_*` (3 test); `test_answer_prompt.py::test_format_source_adds_the_expiration_line_only_when_the_document_has_one` |
| T04 | Rule 8 yeni metni; `make lint` prompt-doküman eşitliği yeşil; kural 1-7/9-10 değişmedi | ✅ | `make prompt-doc` + `make lint` (bkz. §3); `docs/prompts/ANSWER_SYSTEM_PROMPT.md` diff'i yalnızca 8. satır |
| T05 | `outstanding_debt('today')`: workbook `Ledger_DemoToday` ile `temporal.today()` eşleşirse eski davranış; eşleşmezse açık uyarı, sessiz bayat değer yok | ✅ | `test_excel_engine.py::test_outstanding_debt_today_refuses_a_stale_snapshot` (bir gün kaydırılmış `today` → `FunctionError`) |
| T06 | Sistem-olgusu kısa devresi (SORU 2 cevabına göre) | N/A | SORU 2: yalnızca (a) frontend — backend kısa devresi yapılmadı, bu yüzden kriter uygulanmadı |
| T07 | `validate-ledger` 0 hata/uyarı; yeni ledger şema testi: `expiration_date` doluysa `>= effective_date` | ✅ | `make validate-ledger` → `0 error(s), 0 warning(s)`; `test_validate_ledger.py::test_expiration_date_must_be_after_effective_date` (yeni kural **C11**) |
| T08 | Canlı doğrulama (küçük, hedefli) | ⏭ ertelendi | `DOC-ANK-OPS-009`'un gerçek `expiration_date`'i yazılmadan (SORU 1 onayı bekliyor) "süresi doldu mu" sorusu canlı test edilemez; mekanizma (`expiration_note`, rule 8, Excel drift) birim testle doğrulandı. Naci tarih onaylayınca tek bir takip turu (ledger yazımı + 1-2 soruluk canlı doğrulama) yeterli |

## 2. Yapılanlar

- **`app/services/temporal.py` (yeni):** `today(settings)` — `Settings.demo_today`/`company_timezone`'ın okunduğu **tek** yer; `expiration_note(document, today)` — TR cümle + gün/ay/yıl biçimlendirme (`_tr_duration`), rule 3'ü tarihe uygulayan saf fonksiyon.
- **`app/core/config.py`:** `demo_mode_enabled: bool = True` (geri alma: `DEMO_MODE=false`), `company_timezone: str = "Europe/Istanbul"`.
- **`app/services/ask.py`, `app/services/excel_ask.py`, `app/api/auth.py`:** `settings.demo_today` yerine `temporal.today(settings)`.
- **`app/services/answer_prompt.py`:** `format_source()` artık `today` parametresi alıyor, `expiration_note` satırını (varsa) `Zincir:`'den hemen sonra ekliyor; **rule 8** yeniden yazıldı — model artık tarih farkını kendisi hesaplamıyor, hazır satırı aktarıyor.
- **`app/excel/functions.py`:** `run_function(..., today: date)` — `_today` sistem değeri olarak `params`'a enjekte edilir (LLM'in plan JSON'undan asla gelmez); `outstanding_debt('today')` workbook'un `Ledger_DemoToday`'i ile karşılaştırır, uyuşmazsa `FunctionError` (→ mevcut "veri yok" cevabı).
- **`seed_data/generator/generate_excel.py`:** `_meta()` artık `Ledger_DemoToday` adlı bir named range de yazıyor (`_meta!B4`'ü gösterir) — 4 demo workbook yeniden üretildi + LibreOffice recalc + `validate_excel.py` (0 hata).
- **Ledger şeması:** `ledger_schema.Document.expiration_date: Fact | None` (yeni alan); `generate_documents.py` metadata çıktısına eklendi; `demo_documents_seed.py`/`document_repo.create_with_job` `expiration_date` parametresi taşıyor. **74 belgenin tamamına** `expiration_date: null` eklendi (ankara_res 49, izmir_res 15, company 10) — hiçbiri gerçek bir tarih almadı.
- **`validate_ledger.py`:** yeni kural **C11** — `expiration_date` doluysa tarih/null olmalı ve `effective_date`/`document_date`'ten sonra olmalı.
- **`app/schemas/auth.py`, `app/api/auth.py`:** `CurrentUserResponse.today`/`demo_mode_enabled` — her `/api/auth/login`\|`/me` çağrısında sistemin kendi "bugün"ü (SORU 2 (a) için gereken minimum backend değişikliği).
- **`.env`/`infra/.env.example`:** `DEMO_MODE=true`, `COMPANY_TIMEZONE=Europe/Istanbul` satırları.
- **`docs/ARCHITECTURE.md`:** **ADR-026** eklendi.
- **AI-BalBal (ayrı repo, ayrı PR):** `feat/bugun-rozeti` dalı → PR **#8** (`ftansu/AI-BalBal`, merge edilmedi) — üst barda "Bugün: 15.09.2026 (demo)" rozeti, `CurrentUser.today`/`demo_mode_enabled`'ı gösteriyor; yeni CSS yok (mevcut `.topbar-dept` yeniden kullanıldı).
- **Dokunulmayanlar:** Excel'de canlı enterpolasyonlu hesap (plan §4'te büyük alternatif olarak not düşüldü, yapılmadı); backend'de sistem-olgusu kısa devresi (SORU 2); `/api/me/agenda` (B-01 henüz yok, yalnızca `temporal.py`'nin konumu ona hazırlandı).

## 3. Doğrulama

- Dokunulan/yeni test dosyaları (`test_temporal.py`, `test_config.py`, `test_answer_prompt.py`, `test_excel_engine.py`, `test_validate_ledger.py`, `test_auth.py`, `test_ask.py`) tek tek yeşil (85 test, bkz. ara kontrol).
- `make test`: **505 passed, 15 deselected, 10 dk 24 sn; ocr-worker 9 passed**.
- `make lint`: **0 error(s)** — ruff check/format, mypy 118 dosya, prompt-doküman eşitliği (`ANSWER_SYSTEM_PROMPT.md`/`EXCEL_PROMPTS.md`/`ROUTER_PROMPTS.md`), `validate_documents --prose-only`, `validate_excel` hepsi yeşil.
- `make validate-ledger`: **0 error(s), 0 warning(s)**.
- `make eval EVAL_ARGS="--retrieval-only"`: **recall@80 39/39 (%100.0)** — retrieval sıralaması (bu turda dokunulmayan kısım) değişmedi.
- `make excel`: 4 workbook yeniden üretildi (yalnızca `generated_at` zaman damgası + yeni `Ledger_DemoToday` named range değişti — diğer tüm hücreler/değerler aynı), LibreOffice recalc, `validate_excel.py` → **0 error(s)**.
- Docker imajında `zoneinfo`/`tzdata` doğrulaması: `python3 -c "from zoneinfo import ZoneInfo; ZoneInfo('Europe/Istanbul')"` → başarılı; `/usr/share/zoneinfo/Europe/Istanbul` imajda zaten mevcut (ayrı bir `tzdata` pip paketi **gerekmedi**).

## 4. Kendi aldığım küçük kararlar

| Karar | Neden |
|---|---|
| `_today` sistem değeri `run_function`'ın `params` dict'ine enjekte edilir, `FunctionSpec.run` imzası değişmez | yalnızca `outstanding_debt` okuyor; diğer 4 fonksiyonun imzasını şişirmemek |
| Excel drift kontrolü = açık ret (mevcut `FunctionError` → "veri yok"), yeni bir hata sınıfı/mesaj sözleşmesi değil | mevcut mimariyle tutarlı, kullanıcıya zaten "veri bulamadım" diyor |
| `Ledger_DemoToday` named range, var olan `_meta!B4` hücresini gösterir | yeni hücre/sayfa gerekmez, `_meta` zaten 4 workbook'un hepsinde var |
| `expiration_note` metni "GG.AA.YYYY tarihine/tarihinde" biçiminde (kesme işaretli ek yerine) | rakamdan sonra Türkçe kesme eki (`'e`/'`ye`) sayının okunuşuna göre değiştiği için belirsiz; "tarihine/tarihinde" belirsizliği tamamen ortadan kaldırıyor |
| `_tr_duration` yıl+ay birleşik biçim (örn. "1 yıl 8 ay") | tek haneli "1,7 yıl" yerine daha doğal Türkçe; ay sayısı ortalama ay uzunluğuna (30,44 gün) göre yuvarlanıyor |
| 74 belgenin tamamına `expiration_date: null` eklendi (yalnızca OPS-009'a değil) | ledger'ın "her alan her belgede açıkça yazılır" kuralıyla (CLAUDE.md, mevcut `effective_date` deseni) tutarlı; pydantic `_Strict` zaten zorunlu kılıyordu |
| Sistem-olgusu rozeti `/api/auth/me`'ye eklendi, yeni bir endpoint açılmadı | her sayfa yüklemesinde zaten çağrılıyor; `enabled_products`'ın (B-25) aynı yolu kullandığı emsal |
| AI-BalBal tarafı ayrı, küçük bir PR (#8) — B-28b PR'larına eklenmedi | konu bağımsız (katalog/rehber değil, tek rozet); gözden geçirmesi kolay kalsın |

## 5. Açık sorular / Tansu'ya

Bu turda Tansu'ya iletilecek yeni bir açık soru yok. AI-BalBal PR #8 için kısa not: NOT dosyasına düşüldü (§6).

## 6. DOC-ANK-OPS-009 — aday `expiration_date` tarihleri (Naci onayı bekliyor)

Ledger'a **hiçbir tarih yazılmadı**. "Sigorta Yenileme Bildirimi — İşletme Dönemi" belgesinin `effective_date`'i `2024-01-10`; bir yıllık yenileme mantığına uyan, `DEMO_TODAY` (15.09.2026) öncesinde biten üç aday:

| Aday | Tarih | Mantık |
|---|---|---|
| A | **09.01.2025** | Tam 1 yıllık poliçe dönemi, yıldönümünden bir gün önce biter (dönem: 10.01.2024–09.01.2025) |
| B | **10.01.2025** | Tam 1 yıl sonra, yıldönümü ile aynı gün biter |
| C | **10.04.2025** | 1 yıl + 3 aylık ek/grace süre (poliçenin fiilen kaç ay sonra "unutulduğu" senaryosu, demo'da daha uzun bir "fark edilmedi" hikâyesi isteniyorsa) |

Üçü de `validate_ledger.py`'nin yeni **C11** kuralını (`expiration_date > effective_date`) ve mevcut C8 kuralını geçer; hiçbiri `DEMO_TODAY`'e yaklaşmıyor (en yakın aday C, demo gününden ~17 ay önce bitiyor — "süre dolalı uzun zaman olmuş" okunur, "yeni dolmuş" değil; bu okunuş istenen değilse bana söyleyin, daha yakın bir tarih de önerebilirim).

Onayınızdan sonra: `seed_data/master/ankara_res.yaml`'de `DOC-ANK-OPS-009`'un `expiration_date: null` satırı seçtiğiniz tarihle değiştirilir, `make validate-ledger` + `make seed-demo-documents` (var olan kurulumda tek seferlik) + 1-2 soruluk canlı doğrulama ("Ankara RES sigorta poliçesinin süresi doldu mu?") yapılır, kısa bir takip notu + commit ile kapatılır.

## 7. Sonraki adım

- Naci'nin §6'daki tarih onayı → tek, küçük bir takip turu.
- AI-BalBal PR #8 ve (varsa bekleyen diğer PR'lar) Tansu'nun kararını bekliyor.
- B-01 (Gündeminiz) geldiğinde `temporal.py`'deki `expiration_note`/`today` fonksiyonları doğrudan yeniden kullanılabilir — ayrı bir hesap yazılmaz.
