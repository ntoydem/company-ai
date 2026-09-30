# Aşama A — "Balbal cevap döngüsü" — Uygulama Planı

**Tarih:** 30.09.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` (bundan sonra **NOT**) §1 tablosu + "Önerilen ilk somut adım — Aşama A". Hedef: AI-BalBal'ın `/api/ask` cevabı etrafında beklediği sözleşme boşluklarını backend tarafında kapatmak. company-ai `frontend/` emekli (NOT §4.4); bu fazda ona **dokunulmaz**.

Okunanlar: NOT'un tamamı; `docs/PHASES.md`; `backend/app/services/{router,ask,ask_router,audit_writer,version_chain}.py`; `schemas/{ask,auth,audit_log,excel}.py`; `api/{ask,auth,audit_log,deps}.py`; `models/audit_log.py`; `repositories/{audit_log_repo,document_repo}.py`; `core/config.py`; `alembic/versions/0008`; `scripts/eval_lib.py`; `docs/ARCHITECTURE.md` ADR-003/004/010/016/021. AI-BalBal salt okunur klon @ `b219600` (29.09.2026, dondurulmuş sürüm — NOT başlığı): `frontend/src/api/{types,ask,products,proposed}.ts`, `components/balbal/{AnswerView,BalbalChat}.tsx`, `components/SourceCardList.tsx`, `components/common/Modal.tsx` (`PendingNotice`), `auth/{useProduct,RequireProduct}.tsx`, `pages/Home.tsx`, `components/Layout.tsx`, `lib/strings.ts`, `README.md`; `docs/BACKEND_GAPS.md` §1.5.4 (B-25), §3.4 (B-04), §3.6 (B-07); `docs/BAGLANTI_YOL_HARITASI.md` §2 (B-25 adımı, T-01..T-03).

---

## 1. Tespitler (planı şekillendirenler)

- **T1 — B-04 çelişkisi, en önemli tespit.** Naci'nin listesindeki `POST /api/ask/feedback {audit_log_id, rating, comment?}` BACKEND_GAPS §3.4'ün *ilk* halidir. **Tansu #1 (30.09.2026) "beğendim / yanlış" butonlarını reddetti**; NOT bunu §0 satır 1, §1 B-04 ("geri bildirim ucu ve `rating` sütunu **yazılmaz**"), §4.1, §4.2 ve §5.3'te işledi; yerine `AskResponse.warnings` (`missing_data` / `data_conflict` / `product_limit`) geldi. AI-BalBal'ın dondurulmuş sürümü (`b219600`) Tansu #1'den **önce**; `AnswerView.tsx:61-91` `FeedbackRow` ve `proposed.ts:422-428` `sendAnswerFeedback` hâlâ orada, Tansu'nun kaldıracağı söylendi (NOT §4.1 "Geri bildirim" satırı). Bu plan iki seçeneği yazar (§3.5), **SORU 1** ile Naci'ye bırakır; önerimiz Tansu #1'e uymak.
- **T2 — `audit_log_id` bugün hiç dönmüyor, ama yazılıyor.** `audit_writer.write_audit_row` (`:41-84`) `audit_log_repo.create`'in döndürdüğü satırı atıyor (`-> None`, hata yutuluyor). `ask_router.answer_routed_question` (`:214-231`) tek yazma noktası; id'yi `RoutedAnswer`'a taşımak için yalnızca dönüş tipi değişir. `/api/ask` için **tek satır = tek id** garantisi zaten var (ADR-016 Phase 4.3).
- **T3 — `product_level` kodda, tabloda değil.** NOT §6.1: `DOCUMENT_QUERY → P1`, `DATA_QUERY`/`MIXED_QUERY → P2`; "eşleme koddadır (`ask_router.py`)". Eşleme **nihai** `query_type`'a uygulanmalı — `_run()` içindeki "DATA miss falls through to documents" (`ask_router.py:118-128`) tipi `DOCUMENT_QUERY`'ye çeviriyor; `product_level` de onunla birlikte P1'e düşmeli.
- **T4 — Versiyon id'leri yetki kontrolünü zaten taşıyor.** `ask.answer_question` (`ask.py:145-148`) `load_with_chains(..., allowed_ids=allowed)` çağırıyor (`document_repo.py:238-250`: "restricted to `allowed_ids` at every hop"); `version_chain.evaluate_version_chains` `predecessor`/`successor`'ı bu yüklenmiş `by_id`'den alıyor (`version_chain.py:98-101`). Görünmeyen komşu **hiç yüklenmez** → `predecessor is None` → id `None`. B-07'nin "yetkisi yoksa `None`" şartı ek kod olmadan sağlanır; `ChainPosition`'a iki id alanı, `SourceCard`'a iki alan. `is_initial` de aynı yerde hazır (`:104`), `SourceCard`'da yok (NOT §4.1/§4.3 önerisi) — sıfır maliyetle eklenir.
- **T5 — `enabled_products` için üç ayrı kaynak aynı şeyi istiyor:** BACKEND_GAPS §1.5.4 (karar, 28.09), BAGLANTI §2.1 (adım adım: migration `0009_company_settings`, `CurrentUserResponse.enabled_products`, `require_product`, CLI `set-enabled-products`), NOT §2 B-25 "Kabul" + Tansu #2 (müşteri admin arayüzünden değiştirebilmeli → `PATCH /api/admin/settings`). Alan adı ve değerler **birebir** `enabled_products` / `"P1"|"P2"|"P3"` olmalı (`products.ts:281-300`, `types.ts:14`). AI-BalBal bu alanı **hem `/me` hem `/login`** cevabından okur (`BAGLANTI §2.1/2`: `Login.tsx` kullanıcıyı login cevabından kuruyor) — `CurrentUserResponse` iki uçta da ortak (`auth.py:36,85`), tek yerden çözülür.
- **T6 — Denetim kaydı bu alanları taşımalı (kural 4).** NOT §1 B-04 (yeni hali): "Denetim kaydı her uyarıyı `sources`/`answer` gibi satırda saklar"; NOT §4.2: denetim detayında `warnings` ve `product_level`. `product_level` bugün `query_type`'tan türetilebilir ama eşleme ileride değişir (`ACTION → P2`, NOT §6.1); satıra yazılmazsa geçmiş kayıt yanlış okunur. İki sütun: `audit_log.product_level`, `audit_log.warnings`.
- **T7 — Ürün 2 kapalıyken davranış NOT §6.2'de tanımlı:** istek reddedilmez, ADR-010'un güvenli yönü — soru `DOCUMENT_QUERY` olarak cevaplanır, `warnings: [product_limit]`, `product_level: P1`; `POST /api/excel/ask` → `403 product_not_enabled`. Demo'da üç ürün açık → **demo davranışı değişmez**, P1 kısıtı bir test senaryosudur (NOT §6.5).
- **T8 — AI-BalBal `types.ts` elle aynalanıyor** (NOT §4.4). Bu fazın eklediği her alan **eklemeli**dir (mevcut alan kalkmaz, tip değişmez); dondurulmuş sürüm yeni alanları görmezden gelir, hiçbir şey kırılmaz. `warnings`/`product_level`/versiyon id'lerinin **görünmesi** Tansu'nun `types.ts` + bileşen güncellemesine bağlıdır (bkz. §4).
- **T9 — Faz birimi.** PHASES.md'de Adım 5 (Phase 5.4) son; bu iş AI-BalBal entegrasyonunun ilk fazı. Öneri: **ADIM 6 — AI-BalBal entegrasyonu, Phase 6.1** (tag `phase-6-1`, rapor `PHASE_6_1_REPORT.md`). Naci "Aşama A" diyor; adlandırma **SORU 5**.

---

## 2. Kapsam

**Giriyor:** (1) `AskResponse.audit_log_id`, `product_level`, `warnings`; (2) `SourceCard.supersedes_document_id`, `superseded_by_document_id`, `is_initial`; (3) `company_settings.enabled_products` + `/me`/`/login` alanı + `require_product` + `PATCH /api/admin/settings` + CLI; (4) P1-only düşürme kuralı ve `/api/excel/ask` kapısı; (5) `audit_log.product_level`/`warnings` sütunları; (6) geri bildirim ucu **yalnızca SORU 1 = B ise**.

**Girmiyor (bilinçli):** `data_conflict` uyarısı (prompt fazı, `--repeat 3` ölçümü, NOT §5.3); `SourceCard.project_code/name` (B-20/6, kendi eval uyarısı var, NOT §1); `conversation_id`/sohbet geçmişi (B-03 ertelendi); `questions.json`'a `expected_product_level` (NOT §6.3 — eval kota tüketir, `QuestionResult.query_type` zaten kaydediliyor; sonraki faz); AI-BalBal'ı Caddy'den sunma (B-27 sunma kısmı, `FRONTEND_DIR`/`make update-frontend`, ayrı iş); company-ai `frontend/` (emekli, dokunulmaz — `make lint`'in frontend adımı da bu fazda değişmez); `/api/excel/ask` cevabına `audit_log_id`/`product_level` (AI-BalBal bu ucu çağırmıyor, NOT §4.1; sözleşme büyütülmez).

---

## 3. Tasarım

### 3.1 `AskResponse.audit_log_id` — nereden geliyor

- `audit_writer.write_audit_row` → `-> UUID | None` (satır yazıldıysa `row.id`, yazma hatası yutulduysa `None`; "never raises" korunur).
- `ask_router.RoutedAnswer`'a `audit_log_id: UUID | None = None`; `answer_routed_question` (`:214`) dönüşünü alır ve `RoutedAnswer`'a koyar. LLM hatası dalında (`:178-197`) satır yazılır ama 503 döner — id istemciye gitmez, değişmez.
- `AskResponse.audit_log_id: UUID | None` (varsayılan `None` — eski test/eval gövdeleri geçerli kalır). `api/ask.py:35-46` alanı geçirir.
- Güvenlik: id kullanıcının **kendi** sorusunun kaydıdır; okuma API'si admin-only (`api/audit_log.py`, `require_admin`) — id'yi bilen `employee` satırı okuyamaz. Ek yetki yolu açılmaz (ADR-016). Yalnızca `/api/ask` döner (`/api/excel/ask` değil, §2).

### 3.2 `product_level` — nasıl hesaplanıyor

- `schemas/ask.py`: `ProductLevel = Literal["P1", "P2", "P3"]`; `AskResponse.product_level: ProductLevel = "P1"`.
- `ask_router.py`: `PRODUCT_LEVEL_BY_TYPE: dict[QueryType, ProductLevel] = {"DOCUMENT_QUERY": "P1", "DATA_QUERY": "P2", "MIXED_QUERY": "P2"}` — `NOTICE_BY_TYPE`'ın (`:48-52`) yanına, aynı desen. `_run()`'ın **sonunda**, nihai `query_type` üzerinden (DATA-miss fall-through'dan sonra) hesaplanır → `RoutedAnswer.product_level`.
- Denetim satırına yazılır (§3.7). Eşleme tablo değil kod (NOT §6.1).

### 3.3 `warnings` — Tansu #1'in yapılandırılmış hali

```python
class AskWarning(BaseModel):
    kind: Literal["missing_data", "product_limit"]   # "data_conflict" bu fazda üretilmez
    message: str                                      # sabit Türkçe metin, LLM üretmez
    action: Literal["request_data"] | None = None     # B-11 butonu için; bu fazda missing_data'da "request_data"
AskResponse.warnings: list[AskWarning] = []
```
- `missing_data`: `answered=False` olduğunda (ADR-014 sabit metin ve ADR-021 sıfır-chunk yolu; MIXED'de yalnızca iki dal da boşsa — `answered = doc.answered or data.answered`, `:132`) — `message`: `"Şirket kaynaklarında yeterli bilgi bulunamadı."`, `action: "request_data"`. Ek iş yok, yalnızca alan.
- `product_limit`: §3.6'daki düşürme kuralı tetiklendiğinde — `message`: `"Bu özellik şirketinizin paketinde yok; soru yalnızca belgelerden cevaplandı."` (BACKEND_GAPS §1.5.4'ün *"Bu özellik şirketinizin paketinde yok"* ifadesi).
- Sabitler `schemas/ask.py`'de (`NO_INTERPRETATION_NOTICE` deseni). Kural 6: uyarı metni yorum içermez.

### 3.4 `SourceCard` versiyon id'leri + `is_initial`

- `version_chain.ChainPosition`'a `supersedes_document_id: UUID | None`, `superseded_by_document_id: UUID | None` (`predecessor.id if predecessor else None`, `successor.id if successor else None` — `:106-107`'deki title mantığının aynısı).
- `SourceCard`'a `supersedes_document_id`, `superseded_by_document_id`, `is_initial: bool`; `ask._source_cards` (`ask.py:70-83`) `source.position`'dan doldurur. Mevcut `*_title` alanları **kalır** (AI-BalBal `SourceCardList.tsx:38-44` onları okuyor).
- Yetki: T4 — gizli komşu yüklenmediği için id `None`; test bunu **kanıtlar** (§6, T-08).
- `audit_log.sources` JSONB `model_dump` ile otomatik büyür (`audit_writer.py:29-31`); `AuditLogDetail.sources: list[dict]` değişmez.

### 3.5 `POST /api/ask/feedback` — iki seçenek (SORU 1)

**A — Tansu #1'e uy (önerilen):** uç **yazılmaz**, `rating` sütunu yok. Cevap kimliği (`audit_log_id`) yine döner (§3.1): destek/hata ayıklama için kullanıcı id'yi yöneticiye söyleyebilir; B-11 evrak talebinin "hangi cevaptan doğdu" referansı (NOT §1 B-11, sunucu tarafında) buna dayanır. Dondurulmuş AI-BalBal'ın `FeedbackRow`'u `POST /api/ask/feedback` → 404 → `BackendPending` → `S.balbal.feedbackPending` gösterir — **bugünkü davranışın aynısı** (`AnswerView.tsx:68-71`, `audit_log_id` yokken de aynı metin). Tansu butonları kaldırınca kutu gider.

**B — BACKEND_GAPS §3.4'ü olduğu gibi uygula:** Naci'nin listesi bunu istiyorsa:
- Tablo **ayrı**: `answer_feedback(id, audit_log_id FK → audit_log.id ON DELETE CASCADE, user_id FK SET NULL, rating text CHECK in ('up','down'), comment text NULL, created_at)`, `UNIQUE(audit_log_id)` (bir cevap bir kez; tekrar → upsert). `audit_log`'a sütun **eklenmez**: satır "yazılır ve asla güncellenmez" (`models/audit_log.py` docstring), 90 günlük temizlik (`delete_older_than`) cascade ile geri bildirimi de siler — ayrı retention kuralı gerekmez.
- Şema `proposed.ts:424-427` ile birebir: `{audit_log_id: UUID, rating: "up"|"down", comment?: str (≤ 1000)}` → `204`.
- Yetki: yalnızca `audit_log.user_id == current_user.id` olan satır; başkasının ya da olmayan id → **404** (varlık ele verilmez, `AUDIT_LOG_NOT_FOUND_MESSAGE` deseni). Admin listesi: `GET /api/audit-log?rating=down` süzgeci (`list_filtered`'a `LEFT JOIN`), `AuditLogDetail.feedback: {rating, comment, created_at} | None`.
- Kural 4/ADR-016: geri bildirim de denetim verisidir, retrieval/prompt'a girmez.

B seçilirse NOT §1 B-04 / §4.1 / §5.3 "Tansu #1 ile değişti" satırları **geri çevrilmez**; Naci'nin Tansu ile teyidi rapora yazılır.

### 3.6 `enabled_products` — `company_settings` gerekli mi?

Basit alternatif: `Settings.enabled_products` env değişkeni (`.env`'den, migration yok, CLI yok). **Reddediyoruz:** (a) Tansu #2 / NOT §5.1 — müşteri admin arayüzünden değiştirecek; env için container `--force-recreate` gerekir (PHASES.md Phase 5.4 notundaki bilinen tuzak); (b) BAGLANTI T-02 çalışırken paket değiştirmeyi bekliyor; (c) P-8 "koda/konfige gömme, veri olsun". Tek satırlık tablo küçük iş:

- **Migration `0009`:** `company_settings(id smallint PK CHECK (id = 1), enabled_products text[] NOT NULL DEFAULT '{P1,P2,P3}', updated_at timestamptz)` + tek satır `INSERT (id=1)`. Değer doğrulaması uygulamada (`Literal`), DB'de `CHECK (enabled_products <@ ARRAY['P1','P2','P3'])`. Aynı migration `audit_log` sütunlarını da ekler (§3.7).
- `models/company_settings.py`, `repositories/company_settings_repo.py`: `get(session) -> CompanySettings` (satır yok → `RuntimeError`, tahmin yok; migration garanti eder), `set_enabled_products(session, products)`.
- `schemas/auth.py::CurrentUserResponse.enabled_products: list[ProductLevel]` — `model_validate(user)` yerine `CurrentUserResponse.from_user(user, settings_row)`; `/login` (`auth.py:76`) ve `/me` (`:87`) ikisi de (T5). Sıra korunur: `P1, P2, P3`.
- `api/deps.py::require_product(level)` → dependency factory (`require_admin` deseni, `:38`): kapalıysa `HTTPException(403, detail="product_not_enabled")` — gövde `{"detail": "product_not_enabled"}` (BAGLANTI §2.1/3 birebir). İlk kullanım: `api/excel.py` `POST /api/excel/ask` → `require_product("P2")`. `inspect` **açık kalır** (NOT §6.2: P1'de Excel yüklenir/incelenir, hesap yapılmaz).
- **Düşürme kuralı** (`ask_router._run` başı): `"P2" not in enabled and routed.query_type != "DOCUMENT_QUERY"` → `routed`'ı `RoutedQuestion(query_type="DOCUMENT_QUERY", document_question=None, data_question=None)` ile değiştir (orijinal soru, ADR-010'un "DOCUMENT/DATA orijinal soruyu çalıştırır" kuralı), `warnings += product_limit`. Router çağrısı yine yapılır (sınıflandırma kaydı `query_type`… **SORU 2:** denetim satırında router'ın *ilk* kararı mı, düşürülmüş nihai tip mi yazılsın? Öneri: nihai tip + `warnings`'ta `product_limit` — DATA-miss fall-through zaten böyle davranıyor, tutarlı).
- CLI `python -m app.cli set-enabled-products P1,P2` (+ `make set-products PRODUCTS=P1`), bilinmeyen değer → exit 2, boş liste → exit 2 (en az P1). Admin ucu `PATCH /api/admin/settings {enabled_products: [...]}` → `require_admin`, aynı doğrulama, `200 {enabled_products}`; `GET /api/admin/settings` eşi. Yönetim sekmesi Tansu tarafında (NOT §4.2 son satır).
- Okuma maliyeti: `/me`, `/login`, `/api/ask`, `/api/excel/ask` başına bir `SELECT` (tek satır, PK) — cache yok, tutarlılık basit.

### 3.7 Denetim kaydı (migration `0009`, ADR-016 concretization)

- `audit_log.product_level varchar(2) NULL` (eski satırlar `NULL`, tahmin yazılmaz), `audit_log.warnings jsonb NOT NULL DEFAULT '[]'`.
- `write_audit_row` iki parametre daha alır; `AuditLogDetail`'e `product_level: str | None`, `warnings: list[dict]`. `AuditLogListItem` değişmez (hafif kalır). `GET /api/audit-log?query_type=` filtresi yeter; `product_level` filtresi eklenmez (türetilebilir).

### 3.8 Frontend

company-ai `frontend/`: **dokunulmaz** (NOT §4.4). AI-BalBal: **dokunulmaz** (Tansu'nun reposu). Sözleşme değişiklikleri yalnızca eklemeli (T8). Rapora "AI-BalBal tarafında güncellenecek dosyalar" listesi yazılır (bilgi, iş değil): `types.ts` (`SourceCard` 3 alan, `AskResponse` 3 alan, `CurrentUser.enabled_products` zaten var), `SourceCardList.tsx:38-44` (başlık → `FileLink`), `AnswerView.tsx` (`warnings` görünümü, `FeedbackRow` kaldırma — Tansu #1).

---

## 4. AI-BalBal'da bu fazla kapanan boşluklar — somut

"Backend bekleniyor" kutusu = `PendingNotice` (`Modal.tsx:43-50`) ya da `isPending()` metni. Dondurulmuş sürümde `/api/ask` etrafında bu türden **tek** kutu var: `FeedbackRow`'un `feedbackPending` metni (`AnswerView.tsx:70,77`, `strings.ts:105`). Dürüst tablo:

| Boşluk (AI-BalBal `b219600`) | Bu fazdan sonra | Kutu kapanır mı? |
|---|---|---|
| **B-25** `CurrentUser.enabled_products` yok → `products.ts:292` yalnızca P1 varsayar; ekip sohbeti launcher'ı (`Layout.tsx:27`) ve "Gündeminiz" (`Home.tsx:73`) **herkeste gizli** | Alan `/login` + `/me`'de gelir; demo `["P1","P2","P3"]` → launcher ve gündem bölümü görünür, `set-enabled-products P1` ile kaybolur (BAGLANTI bağlantı günü #4-5) | **Evet — dondurulmuş sürümde, Tansu dokunmadan.** (Ekip sohbetinin *içi* B-05/B-06 kutularını göstermeye devam eder, o ayrı.) |
| **B-07** `SourceCardList.tsx:38-44` "güncel versiyon: X" yalnızca metin (P-4 ihlali) | `superseded_by_document_id` / `supersedes_document_id` döner, yetki filtreli | Sözleşme tarafı kapanır; **link olması Tansu'nun 2 satırlık `FileLink` değişikliğine bağlı** (kutu değil, yorum satırı) |
| **B-04** `audit_log_id` yok → `feedbackPending` | `audit_log_id` döner | **SORU 1 = A:** kutu kalır (uç 404), Tansu butonları kaldırır. **SORU 1 = B:** kutu kapanır, "Teşekkürler"/"iletildi" metinleri çalışır |
| `warnings`, `product_level` | Döner | Dondurulmuş sürüm görmez; Tansu `types.ts` + `AnswerView` günceller |

Naci'nin "hangi ikisi" sorusuna cevap: **B-25 (kutusuz, hemen görünür) ve B-07 (sözleşme tarafı)**; B-04 kutusunun kapanması SORU 1'e bağlı.

---

## 5. Dosyalar / tablolar / uçlar

| Katman | Dosya | Değişiklik |
|---|---|---|
| Şema | `schemas/ask.py` | `ProductLevel`, `AskWarning`, `AskResponse.{audit_log_id, product_level, warnings}`, `SourceCard.{supersedes_document_id, superseded_by_document_id, is_initial}`, iki sabit uyarı metni |
| Şema | `schemas/auth.py` | `CurrentUserResponse.enabled_products` + `from_user()` |
| Şema | `schemas/audit_log.py`, `schemas/settings.py` (yeni) | `AuditLogDetail.{product_level, warnings}`; `CompanySettingsResponse/Update` |
| Model | `models/company_settings.py` (yeni), `models/audit_log.py`, `models/__init__.py` | tablo; iki sütun |
| Migration | `alembic/versions/0009_company_settings_and_answer_fields.py` | §3.6 + §3.7 (+ B ise `answer_feedback` tablosu) |
| Repo | `repositories/company_settings_repo.py` (yeni), `audit_log_repo.py` | `get`/`set_enabled_products`; `create` iki alan (+ B: `feedback` filtre/join) |
| Servis | `services/version_chain.py`, `ask.py`, `ask_router.py`, `audit_writer.py` | id alanları; kart doldurma; `PRODUCT_LEVEL_BY_TYPE`, düşürme kuralı, `warnings`, `RoutedAnswer.{audit_log_id, product_level, warnings}`; `write_audit_row -> UUID \| None` |
| API | `api/ask.py`, `api/auth.py`, `api/deps.py`, `api/excel.py`, `api/settings.py` (yeni), `api/router.py`, `api/audit_log.py` | alan geçişi; `enabled_products`; `require_product`; excel kapısı; `GET/PATCH /api/admin/settings`; (B: `api/feedback.py` `POST /api/ask/feedback`, audit filtre) |
| CLI / Make | `app/cli.py`, `Makefile` | `set-enabled-products`; `make set-products PRODUCTS=…` |
| Docs | `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `README.md`, `docs/notes/TANSU_…md`, `docs/reports/PHASE_6_1_REPORT.md` | §7 |

Yeni uçlar: `GET/PATCH /api/admin/settings` (admin); (B) `POST /api/ask/feedback` (kimlikli). Değişen uçlar: `POST /api/ask`, `POST /api/auth/login`, `GET /api/auth/me`, `GET /api/audit-log/{id}` (eklemeli), `POST /api/excel/ask` (P2 kapısı). Yeni tablo: `company_settings`; (B) `answer_feedback`. Yeni sütunlar: `audit_log.product_level`, `audit_log.warnings`.

---

## 6. Kabul kriterleri ve kanıt

Hepsi `make test` içinde (LLM ve router **fake**, retrieval/yetki/Excel **gerçek** — `test_ask_router.py` deseni); canlı doğrulama ayrıca.

| # | Kriter | Test / komut |
|---|---|---|
| T-01 | `POST /api/ask` cevabındaki `audit_log_id`, o çağrının **tek** `audit_log` satırının `id`'sine eşit (DOCUMENT, DATA, MIXED) | `test_ask_router.py::test_audit_log_id_matches_the_single_row` (`_audit_rows` yardımcısıyla) |
| T-02 | `product_level`: DOCUMENT→`P1`, DATA→`P2`, MIXED→`P2`; DATA-miss fall-through → `DOCUMENT_QUERY` + `P1` | `test_ask_router.py::test_product_level_by_final_query_type` |
| T-03 | `answered=false` → `warnings == [{kind: missing_data, action: request_data}]`; `answered=true` → `[]` | `test_ask_router.py`, `test_ask.py` |
| T-04 | `set-enabled-products P1` sonrası router DATA/MIXED seçse de cevap `DOCUMENT_QUERY`, `product_level: P1`, `warnings` `product_limit` içerir, Excel motoru **çağrılmaz** (fake plan çağrısı olmaz) | `test_ask_router.py::test_p1_only_degrades_to_document_with_product_limit` |
| T-05 | `/api/auth/login` **ve** `/api/auth/me` gövdesinde `enabled_products`; migration sonrası `["P1","P2","P3"]`; `set-enabled-products P1` → `["P1"]` (BAGLANTI T-01/T-02) | `test_auth.py`, `test_cli.py` |
| T-06 | `POST /api/excel/ask` P2 kapalı → `403 {"detail":"product_not_enabled"}`; açık → 200; `GET /api/excel/{id}/inspect` P1'de 200 (BAGLANTI T-03) | `test_excel_api.py` |
| T-07 | `PATCH /api/admin/settings`: admin 200, `employee` 403, `["P4"]`/`[]` 422 | `test_settings.py` (yeni) |
| T-08 | Kaynak kartı: Facility Agreement + Amendment 01 zinciri → eski belgede `superseded_by_document_id == amendment.id`, `is_initial == true`; **Amendment'i göremeyen** kullanıcıda `superseded_by_title` ve id ikisi de `None` (ADR-004/021) | `test_ask.py` (mevcut `:174` deseni + `enerji`/`finans` izolasyon fixture'ı) |
| T-09 | `audit_log` satırı `product_level` ve `warnings` taşır; `GET /api/audit-log/{id}` döner; eski satır (`NULL`) 200 | `test_audit_log.py`, `test_audit_log_repo.py` |
| T-10 | `0009` upgrade/downgrade boş DB'de; `company_settings` tek satır, `id=2` INSERT reddedilir | `test_migrations.py` |
| T-11 | (B) kendi cevabına `up`/`down` → 204 ve satır; başkasının `audit_log_id` → 404; ikinci oylama günceller; `?rating=down` süzgeci | `test_feedback.py` (yeni) |
| T-12 | `make lint` yeşil (ruff, mypy `warn_unreachable`, prompt dokümanları — prompt değişmiyor) | `make lint` |
| T-13 | Eval regresyonu yok: `make eval EVAL_ARGS="--retrieval-only"` recall@80 36/36 (Phase 5.3/5.4 ile aynı); tam eval **koşulmaz** (kota) | komut çıktısı rapora |

**Canlı doğrulama (`company-ai-dev`, gerçek Gemini, ≤ 4 çağrı — kota notu `gemini-free-tier`):**
1. `curl -c c.txt -X POST /api/auth/login` (`finans`) → gövdede `enabled_products: ["P1","P2","P3"]`; `curl -b c.txt /api/auth/me` aynı.
2. `curl -b c.txt -X POST /api/ask '{"question":"Ankara RES kredi sözleşmesindeki DSCR covenant nedir?"}'` → `audit_log_id` (UUID), `product_level: "P1"`, `sources[].superseded_by_document_id` dolu (Facility Agreement → Amendment 01), `warnings: []`; `make psql` ile `SELECT id, product_level, warnings FROM audit_log ORDER BY timestamp DESC LIMIT 1` aynı id.
3. `make set-products PRODUCTS=P1` → `/me` `["P1"]`; `/api/ask '{"question":"Ankara RES 2026 Q2 DSCR kaç?"}'` → `query_type: DOCUMENT_QUERY`, `product_level: P1`, `warnings[0].kind == product_limit`, cevap belgeden (covenant raporu PDF'i); `/api/excel/ask` → 403. Sonra `PRODUCTS=P1,P2,P3` geri.
4. **AI-BalBal'a karşı:** AI-BalBal Caddy'den sunulmuyor (B-27 sunma kısmı ayrı iş); doğrulama, AI-BalBal `frontend/`'i `npm run dev` ile backend'e proxy'leyip (Vite `server.proxy`, kendi `vite.config.ts`'i) tarayıcıda ekip sohbeti launcher'ının paket değişiminde görünüp kaybolduğunu görmektir — **tarayıcı testi, Naci elle** (Playwright kapsam dışı). Backend tarafında kanıt 1-3'tür.

---

## 7. Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: **ADR-022 — Product layer key (B-25)**: `company_settings` tek satır, `require_product`, düşürme kuralı, "demo'da üç ürün açık", alan adı sözleşmesi. Concretization satırları: ADR-016 (`audit_log_id` döner; `product_level`/`warnings` sütunları; B ise `answer_feedback`), ADR-010 (`product_level` eşlemesi nihai tipten; P1 düşürme), ADR-021 (`SourceCard` id'leri yetki filtreli, `is_initial`), ADR-003 (`enabled_products` `/me` + `/login`'de).
- `docs/PHASES.md`: yeni **ADIM 6 — AI-BalBal entegrasyonu**, **Phase 6.1 — Balbal cevap döngüsü (Aşama A)**, kabul kriterleri = §6 tablosu; durum satırı; Adım 5'in altındaki "Aşama A başlatılabilir" notuna commit referansı.
- `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md`: §1 B-07/B-04(yeni)/B-25 satırlarına "UYGULANDI (Phase 6.1)"; §4.1/§4.2 ilgili satırlar; §7.1'e satır; "Aşama A" paragrafı "başladı/bitti".
- `README.md`: ürün paketi bölümü (`make set-products`, `PATCH /api/admin/settings`), `/api/ask` cevap alanları.
- `infra/.env.example`: değişiklik **yok** (ayar DB'de).
- `docs/reports/PHASE_6_1_REPORT.md` (şablon), `git tag phase-6-1`.

---

## 8. Uygulama sırası

1. Migration `0009` + model + repo + `test_migrations` (T-10).
2. `CurrentUserResponse.enabled_products`, `/login` + `/me`, CLI, `make set-products` (T-05).
3. `require_product` + `/api/excel/ask` kapısı (T-06); `GET/PATCH /api/admin/settings` (T-07).
4. `version_chain` id alanları → `SourceCard` → `_source_cards` (T-08).
5. `AskWarning`/`ProductLevel`; `ask_router`: eşleme, düşürme kuralı, `warnings`; `write_audit_row -> UUID | None`; `RoutedAnswer`/`AskResponse` alanları; `audit_log` sütunları + `AuditLogDetail` (T-01..T-04, T-09).
6. (SORU 1 = B ise) `answer_feedback` + uç + filtre (T-11).
7. `make test`, `make lint` (T-12), `--retrieval-only` eval (T-13), canlı 1-3.
8. ADR-022 + concretization'lar, PHASES.md, NOT, README → rapor → commit + tag `phase-6-1` + push.

---

## 9. SORU (Naci cevaplamalı)

1. **B-04 / geri bildirim ucu.** Listende `POST /api/ask/feedback {audit_log_id, rating, comment?}` var; Tansu #1 (30.09) bu butonları reddetti, NOT §1/§4/§5.3 buna göre yazıldı, yerine `warnings` geldi. **A** = uca dokunma, `audit_log_id` + `warnings` dön (önerimiz). **B** = BACKEND_GAPS §3.4'ü olduğu gibi yaz (§3.5, ayrı `answer_feedback` tablosu). Hangisi? B ise Tansu ile teyit edildi mi?
2. **P1-only düşürmede denetim satırındaki `query_type`:** router'ın ilk kararı (`DATA_QUERY`) mı, düşürülmüş nihai tip (`DOCUMENT_QUERY`) mı? Öneri: nihai tip; `warnings`'taki `product_limit` düşürmeyi zaten kaydeder (DATA-miss fall-through ile aynı yaklaşım).
3. **`PATCH /api/admin/settings` bu fazda mı?** Tansu #2 (müşteri admin arayüzünden değiştirir) gerektiriyor; ~30 satır + 3 test. Öneri: evet, şimdi — Tansu'nun Yönetim sekmesi backend beklemeden yazılabilsin. Hayır dersen yalnızca CLI kalır (BAGLANTI §2.1/5 "admin arayüzü şimdilik gerekmez" — ama o not Tansu #2'den önce).
4. **`is_initial` ve `SourceCard`'daki eklemeler:** `is_initial`'ı (sıfır maliyet, NOT §4.1 önerisi) dahil ediyorum; `project_code/name` (B-20/6) dahil **etmiyorum**. Uygun mu?
5. **Faz birimi ve ad:** ADIM 6 / Phase 6.1, tag `phase-6-1`, rapor `PHASE_6_1_REPORT.md` — yoksa güvenlik yaması gibi etiketsiz "Aşama A" notu mu? (Öneri: phase — yeni tablo, yeni ADR, 5+ uç değişiyor; faz izlenebilirliği hak ediyor.)

---

## 10. Kendi aldığım küçük kararlar (raporda da listelenecek)

- `audit_log_id` yalnızca `/api/ask`'ta; `/api/excel/ask` sözleşmesi büyütülmedi (AI-BalBal çağırmıyor).
- `product_level` nihai `query_type`'tan; denetim satırına **yazılır** (türetme değil) — T6 gerekçesi.
- `warnings[].message` sabit metin, `schemas/ask.py`'de; `data_conflict` `Literal`'a **eklenmez** (üretilmeyen değer şemada durmaz; prompt fazında gelir).
- `company_settings` tek satır `id=1 CHECK`; satır migration ile gelir, kodda "yoksa oluştur" yok; `get()` satır yoksa hata verir (sessiz varsayım yok).
- `require_product` 403 gövdesi `{"detail": "product_not_enabled"}` — Türkçe mesaj değil, makine okunur kod (BAGLANTI §2.1/3 birebir; AI-BalBal `RequireProduct` zaten kendi metnini gösterir).
- `set-enabled-products` boş liste ve bilinmeyen değeri reddeder; sıra `P1,P2,P3` olarak normalize edilir.
- Router çağrısı P1-only'de de yapılır (kapalı pakette sınıflandırma atlanmaz; `product_limit` ancak router DATA/MIXED dediğinde üretilebilir).
- Eski `audit_log` satırlarında `product_level = NULL` kalır; backfill yapılmaz (tahmin yazılmaz).
- `make lint`'in frontend adımı bu fazda değişmez (NOT §4.4 önerisi ayrı Naci kararı).
