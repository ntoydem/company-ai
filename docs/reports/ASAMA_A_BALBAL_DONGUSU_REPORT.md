# Aşama A Raporu — "Balbal cevap döngüsü" (AI-BalBal `/api/ask` sözleşmesi)

**Tarih:** 30.09.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit, `docs/PHASES.md` çapraz referans notu)  **Commit:** `1199d88`
**Plan:** `docs/plans/ASAMA_A_BALBAL_DONGUSU_PLAN.md` · **ADR:** ADR-022 (yeni), ADR-003/010/016/021 concretization · **Migration:** `0009`

Naci'nin SORU cevapları: (1) **A** — `POST /api/ask/feedback` yazılmadı, `audit_log_id` + `warnings` yeterli (Tansu #1); (2) `company_settings` tablosu (env değil); (3–4) `PATCH /api/admin/settings` dahil, `is_initial` dahil, `project_code/name` hariç; (5) faz etiketi yok. Plan SORU 2'ye (P1 düşürmede denetim satırındaki `query_type`) açık cevap gelmedi → plandaki öneri uygulandı: **nihai tip** (`DOCUMENT_QUERY`) + `warnings`'ta `product_limit` (DATA-miss fall-through ile aynı yaklaşım, bkz. §5).

## 1. Kabul kriterleri (plan §6)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| T-01 | `/api/ask` cevabındaki `audit_log_id` = o çağrının tek `audit_log` satırının id'si | ✅ | `test_ask_router.py::test_answer_returns_the_id_of_its_single_audit_row_with_product_level`; canlı: `fb3fc7bb-…` cevapta ve `SELECT … FROM audit_log WHERE id=…` aynı satır |
| T-02 | `product_level`: DOCUMENT→P1, DATA→P2, MIXED→P2; DATA-miss fall-through → DOCUMENT + P1 | ✅ | `test_product_level_follows_the_final_query_type`, `test_answer_returns_the_id…` (DATA → P2) |
| T-03 | `answered=false` → `warnings == [missing_data, action: request_data]`; `answered=true` → `[]` | ✅ | `test_no_answer_carries_a_missing_data_warning_with_the_request_data_action`, `test_p1_only_leaves_a_document_routing_untouched` |
| T-04 | P1-only: router DATA/MIXED dese de `DOCUMENT_QUERY`, `product_level: P1`, `product_limit` uyarısı, Excel motoru çağrılmaz, router yine çalışır | ✅ | `test_p1_only_degrades_a_data_routing_to_documents_with_a_product_limit_warning`; canlı §7 adım 3 |
| T-05 | `/login` **ve** `/me` gövdesinde `enabled_products`; varsayılan `[P1,P2,P3]`; `set-enabled-products P1` → `[P1]` (BAGLANTI T-01/T-02) | ✅ | `test_settings.py::test_login_and_me_carry_enabled_products_default_all_open`, `test_me_reflects_a_package_change_without_relogin`, `test_cli_set_enabled_products`; canlı adım 1 ve 3 |
| T-06 | `POST /api/excel/ask` P2 kapalı → `403 {"detail":"product_not_enabled"}`; açık → 200; `/inspect` P1'de 200 (BAGLANTI T-03) | ✅ | `test_excel_ask_is_closed_in_p1_but_inspect_stays_open`, `test_product_gate_answers_401_before_403`; canlı adım 3 |
| T-07 | `PATCH /api/admin/settings`: admin 200 (kanonik sıra), `employee` 403, `[]`/`["P4"]` 422 | ✅ | `test_admin_reads_and_updates_enabled_products_in_canonical_order`, `test_admin_update_rejects_empty_and_unknown_products`, `test_settings_endpoints_require_admin` |
| T-08 | Kaynak kartı: zincirde `superseded_by_document_id` / `supersedes_document_id` / `is_initial` dolu; **görünmeyen** komşuda başlık ve id ikisi de `None`, halka güncel sayılmaz | ✅ | `test_ask.py::test_sources_come_from_citations_with_page_and_chain` (genişletildi), `test_hidden_successor_yields_no_id_and_no_title` (`restricted` Amendment 01 + `finans` employee) |
| T-09 | `audit_log` satırı `product_level` ve `warnings` taşır; `GET /api/audit-log/{id}` döner; eski satır `NULL`/`[]` ile 200 | ✅ | `test_audit_log.py::test_detail_carries_product_level_and_warnings`; canlı: her iki satır `psql` ile okundu |
| T-10 | `0009` upgrade/downgrade boş DB'de; `company_settings` tek satır `{P1,P2,P3}`, `id=2` INSERT reddedilir | ✅ | `test_migrations.py::test_downgrade_to_empty_then_upgrade_head` (`IntegrityError` beklenir) |
| T-11 | (yalnızca SORU 1 = B) geri bildirim ucu | ⏭ atlandı — SORU 1 = A, uç yazılmadı | — |
| T-12 | `make lint` yeşil | ✅ | ruff/format/mypy (92 dosya) backend, ruff ocr-worker, eslint+tsc frontend (dokunulmadı), 3 prompt dokümanı eşit, ledger/documents/excel doğrulayıcıları 0 hata |
| T-13 | `make eval EVAL_ARGS="--retrieval-only"` regresyonsuz | ✅ | recall@80 **36/36 (%100)**, Phase 5.3/5.4 ile aynı; tam eval koşulmadı (kota) |

## 2. Yapılanlar

- **Migration `0009`:** `company_settings(id=1 CHECK, enabled_products text[] ⊆ {P1,P2,P3}, updated_at)` + tek satır INSERT; `audit_log.product_level` (varchar(2), NULL), `audit_log.warnings` (JSONB, `[]`).
- **`AskResponse`:** `audit_log_id` (`audit_writer.write_audit_row` artık satır id'sini döndürüyor; yazma hatası → `None`, cevap yine döner), `product_level` (`ask_router.PRODUCT_LEVEL_BY_TYPE`, nihai `query_type`'tan), `warnings[]` (`AskWarning{kind, message, action?}`; `missing_data` `answered=false`'ta, `product_limit` düşürmede; sabit Türkçe metinler `schemas/ask.py`'de).
- **`SourceCard`:** `supersedes_document_id`, `superseded_by_document_id`, `is_initial` — `version_chain.ChainPosition`'a iki id alanı; yeni yetki kodu yok (zincir zaten `allowed_document_ids` ile yükleniyor).
- **B-25:** `CurrentUserResponse.enabled_products` (`from_user()`, `/login` + `/me`), `deps.require_product(level)` (401 önce 403; `{"detail":"product_not_enabled"}`), `POST /api/excel/ask` P2 kapısı, `ask_router.degrade_for_products` (P2 kapalı + DATA/MIXED → DOCUMENT, orijinal soru, `product_limit`), `GET/PATCH /api/admin/settings` (`require_admin`), `python -m app.cli set-enabled-products P1,P2`, `make set-products PRODUCTS=…`.
- **Denetim:** `audit_log_repo.create` + `write_audit_row` iki yeni alan; `AuditLogDetail.product_level/warnings`.
- **Test altyapısı:** `conftest._clean_tables` truncate sonrası `company_settings` satırını migration'daki gibi geri koyar (P1'e geçen test sızmaz).
- **Docs:** ADR-022 + 4 concretization; README (router bölümündeki bayat `GENERAL_QUERY` satırları da temizlendi — GENERAL kaldırma turunda README'de kalmıştı; yeni "Ürün paketi ve cevap alanları" bölümü; `make set-products`); `docs/PHASES.md` Adım 5 altına not; `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §1 B-04/B-07, §2 B-25, §4.1/§4.2, §7.1, "Aşama A" paragrafı → UYGULANDI.

## 3. Değişen dosyalar

`git diff --stat 36f06d6..1199d88`: 27 dosya (+~560 / −42). Yeni: `alembic/versions/0009_company_settings_answer_fields.py`, `app/models/company_settings.py`, `app/repositories/company_settings_repo.py`, `app/schemas/settings.py`, `app/api/settings.py`, `tests/test_settings.py`, bu rapor. Değişen: `api/{ask,auth,deps,excel,router}.py`, `cli.py`, `models/{__init__,audit_log}.py`, `repositories/audit_log_repo.py`, `schemas/{ask,audit_log,auth}.py`, `services/{ask,ask_router,audit_writer,version_chain}.py`, `tests/{conftest,test_ask,test_ask_router,test_audit_log,test_migrations}.py`, `Makefile`, `README.md`, `docs/{ARCHITECTURE,PHASES}.md`, `docs/notes/TANSU_…md`. **company-ai `frontend/`: dokunulmadı** (emekli, NOT §4.4). **AI-BalBal: dokunulmadı.**

## 4. Testler

- Backend: **397 geçti** (383 + 14 yeni), 15 deselected (`live` işaretli canlı LLM testleri, `make test` dışında), 0 atlanan, 3 dk 40 sn. `make test`'in ocr-worker adımı bu değişiklikten bağımsız (ocr-worker'a dokunulmadı; `make lint` ocr-worker ruff yeşil).
- `make lint`: yeşil (bkz. T-12).
- `make eval EVAL_ARGS="--retrieval-only"`: 36/36.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| P1 düşürmede denetim satırına **nihai** `query_type` (`DOCUMENT_QUERY`) yazılır, router'ın ilk kararı `warnings[].kind=product_limit` ve `RoutedQuestion.reason`'da kalır | Plan SORU 2 cevapsız kaldı; DATA-miss fall-through zaten böyle davranıyor, tutarlılık | Naci tersini isterse `ask_router.answer_routed_question`'da tek satır |
| `degrade_for_products` orijinal soruyu `document_question` olarak taşır | İlk denemede `None` bırakınca belge hattı hiç koşmadı (test yakaladı, `assert data is not None`) | Davranış planla aynı |
| `audit_log_id` yalnızca `/api/ask`'ta | AI-BalBal `/api/excel/ask` çağırmıyor; sözleşme büyütülmedi | `ExcelAskResponse` değişmedi |
| `product_level` denetim satırına **yazılır**, türetilmez | Eşleme ileride değişir (`ACTION → P2`); geçmiş kayıt yeniden yorumlanmamalı | `0009` sütunu; eski satırlar `NULL`, backfill yok |
| `data_conflict` `AskWarning.kind` `Literal`'ında **yok** | Üretilmeyen değer şemada durmaz; prompt fazı + eval kategorisi gerekir (NOT §5.3) | Tansu'nun `types.ts`'inde de bu turda iki tür |
| `company_settings` satırı yalnızca migration'dan; `get()` satır yoksa `CompanySettingsMissingError` | Sessiz varsayım yok; eksik satır kurulum hatasıdır | Testlerde `conftest` truncate sonrası satırı geri koyar |
| `require_product` 403 gövdesi Türkçe cümle değil `product_not_enabled` | BAGLANTI §2.1/3 birebir; AI-BalBal `RequireProduct` kendi metnini gösterir | Diğer 403'ler (`NOT_AUTHORIZED_MESSAGE`) değişmedi |
| Router P1-only'de de çalışır | `product_limit` ancak router DATA/MIXED dediğinde üretilebilir; sınıflandırma maliyeti (flash-lite) küçük | P1 müşteride soru başına 1 ek ucuz çağrı |
| README'deki bayat `GENERAL_QUERY` satırları bu turda düzeltildi | Aynı bölüm düzenleniyordu; yanlış doküman bırakılmadı | GENERAL kaldırma raporunun kapsam notuna ek |
| `expected_product_level` eval alanı eklenmedi | Plan §2; `QuestionResult.query_type` zaten kaydediliyor; kota | Sonraki faz adayı |
| `make lint`'in frontend adımı değişmedi | NOT §4.4 önerisi ayrı Naci kararı | company-ai `frontend/` hâlâ lint'te (yeşil) |

## 6. Açık sorular (Naci cevaplamalı)

- `SORU:` §5 ilk satır — P1 düşürmede denetim satırındaki `query_type` nihai tip olarak kaldı; onaylıyor musun, yoksa router'ın ilk kararı mı yazılsın?
- `SORU:` company-ai `frontend/`'in `make lint` kapsamından çıkarılması (NOT §4.4 önerisi) — ayrı, tek satırlık Makefile değişikliği; bu turda dokunulmadı.

## 7. Canlı doğrulama (`company-ai-dev`, gerçek Gemini, 4 çağrı) ve riskler

1. `finans` ile `POST /api/auth/login` → `enabled_products: ["P1","P2","P3"]`, `department_slugs: ["finans","mali_isler"]`; `GET /api/auth/me` aynı.
2. `POST /api/ask "Ankara RES kredi sözleşmesindeki minimum DSCR covenant'ı nedir?"` → `DOCUMENT_QUERY`, `P1`, `answered`, cevap 1,20x (Amendment 01, ledger ile uyumlu), `warnings: []`, `audit_log_id: fb3fc7bb-…`; kartlarda `supersedes_document_id`/`superseded_by_document_id` dolu (Amendment 01 → önceki Facility Agreement; Facility Agreement'ın kendisinin de bir öncülü var, 70 belgelik korpusun zinciri); `psql`: aynı id, `product_level=P1`, `warnings=[]`.
3. `make set-products PRODUCTS=P1` → `/me` `["P1"]`; `POST /api/excel/ask` → **403 `product_not_enabled`**; `POST /api/ask "Ankara RES 2026 Q2 DSCR kaç?"` → `DOCUMENT_QUERY`, `P1`, `warnings: [product_limit]`, `excel_sources: []`, cevap 1,37x **Covenant Compliance Report Q2 2026 PDF'inden** (s.3, s.5) — Excel hesabı yapılmadı; `psql`: `DOCUMENT_QUERY | P1 | [{"kind":"product_limit",…}]`. Sonra `PRODUCTS=P1,P2,P3` geri alındı, `/me` doğrulandı.
4. AI-BalBal'a karşı tarayıcı testi (ekip sohbeti launcher'ının paket değişiminde görünüp kaybolması) **yapılmadı** — AI-BalBal Caddy'den sunulmuyor (B-27 sunma kısmı ayrı iş), Playwright kapsam dışı; Naci elle yapabilir (`npm run dev` + Vite proxy).

Riskler / sonraki adım notları:
- Dondurulmuş AI-BalBal (`b219600`) `warnings`/`product_level`/versiyon id'lerini **görmez** (`types.ts` elle aynalanıyor); B-25 kapısı ise hemen etkili (launcher/gündem). `FeedbackRow` → `feedbackPending` metni Tansu butonları kaldırana kadar görünür; beklenen davranış.
- `company_settings` her istekte bir PK okuması; cache yok, bilinçli.
- Sonraki aday: B-09/B-13/B-17/B-05 (küçük şema eklemeleri, NOT §1), B-27 "AI-BalBal'ı Caddy'den sun" (`FRONTEND_DIR` + `make update-frontend`).

## 8. Doğruladığım üçüncü taraf davranışları

- FastAPI: dependency factory (`require_product("P2")` → iç `dependency(session, _user)`) `Annotated[None, Depends(...)]` ile çalışır; iç bağımlılık `get_current_user` olduğu için 401, 403'ten önce gelir (`test_product_gate_answers_401_before_403`).
- Postgres: `enabled_products <@ ARRAY['P1','P2','P3']::varchar[]` CHECK'i `varchar(2)[]` sütunla eşleşir; `CHECK (id = 1)` ikinci satırı `IntegrityError` ile reddeder (test_migrations).
- SQLAlchemy `ARRAY(String(2))` + `server_default="{P1,P2,P3}"` migration INSERT'inde beklendiği gibi dolar (`psql`: `{P1,P2,P3}`).

## 9. Kaynak kullanımı

- `docker stats`: backend 113 MiB, postgres 166 MiB, ocr-worker 56 MiB, caddy 11 MiB (16 GB VM).
- LLM: canlı doğrulama 4 istek (2 flash-lite router + 2 flash cevap); test ve retrieval-only eval sıfır LLM.
