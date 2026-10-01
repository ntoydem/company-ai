# Aşama D — İçerik araması `GET /api/search` (B-14) + kaynak kartında proje (B-20/6'nın ikinci yarısı) — Uygulama Planı

**Tarih:** 01.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` (NOT) §1 B-14 ve B-20/6, §4.1 "Proje (ADR-008 'proje' atfı)" satırı, §4.2 "Üst bar arama" / "Balbal cevabı, kaynak kartı"; BACKEND_GAPS (dondurulmuş `b219600`) §4.4 (B-14), §3.3 (B-20/6: "her kaynak kartında `project` alanı"). İkisinin de bağımlılığı yok: B-14'ün `people` kısmı B-05 ile (Aşama C) kapandı; `project_id` FK Phase 1.2'den beri var.

Okunanlar: `backend/app/services/{retrieval,search_query,search_glossary,ask}.py`, `repositories/{document_chunk_repo,document_repo,project_repo,user_repo}.py`, `models/{document,document_chunk,project}.py`, `schemas/{ask,document,project,directory}.py`, `api/{documents,projects,directory}.py`, `tests/test_retrieval.py`, `tests/ledger_fixtures.py`, `services/demo_documents_seed.py`; canlı Postgres 16.15'te `ts_headline` denemesi; AI-BalBal `b219600`: `SearchPanel.tsx`, `AskPanel.tsx:18-23`, `BalbalChat.tsx:5-6` (`projectOfDocument`), `SourceCardList.tsx:20,36`, `lib/strings.ts:144-154`, `api/proposed.ts` (`/api/search` **yok**).

---

## 1. Tespitler

- **T1 — FTS bacağı hazır, aramaya tek eksik `ts_headline`.** `document_chunk_repo.search_fts` (`:26-64`) `websearch_to_tsquery` ile `tsv_turkish`/`tsv_simple` üzerinde arıyor, `ts_rank_cd` + deterministik tie-break; `build_search_query` (`search_query.py:78`) Türkçe soruyu OR'lu, sözlük genişletmeli sorguya çeviriyor (ADR-020). Snippet için `ts_headline` canlı Postgres 16.15'te doğrulandı: `ts_headline('turkish'::regconfig, text, websearch_to_tsquery('turkish', q), 'MaxWords=12, MinWords=5')` → `"DSCR of 1.20x at each"`; `simple` konfigürasyonuyla Türkçe metin de çalışıyor. Uygulamada henüz kullanılmıyor.
- **T2 — `retrieve()` ve `search_fts` değişmez.** Eval (`--retrieval-only`) ve `/api/ask` bu ikisine bağlı. Arama için **yeni** bir repo fonksiyonu (`search_document_hits`) aynı WHERE/rank ifadesini paylaşır; ortak ifade özel bir yardımcıya (`_fts_predicate`) alınır — davranış değişikliği yok, mevcut `test_retrieval.py` korur.
- **T3 — Bugünkü arayüz araması istemci tarafında ve yalnızca metadata.** `SearchPanel.tsx:22-27` `/api/documents` + `/api/projects` listelerini `title/document_type/counterparty` ve `name/code` üzerinde süzüyor; içerik araması Balbal'a yönlendiriliyor; kişiler `/api/directory` (Aşama C ile dolu). Yeni uç bu üçünü **tek** istekte ve içerik dahil verir; `proposed.ts`'te `/api/search` sözleşmesi **yok** → Tansu `SearchPanel`'i yeni uca bağlar (kutu kapanması değil, davranış değişikliği).
- **T4 — Yetki.** Belge hits `allowed_document_ids(user, AuthorizationScope(), provider)` kümesinde (kural 1, P-2); metadata eşleşmesi de aynı kümede. Projeler: `GET /api/projects` zaten her kimlikli kullanıcıya açık (`projects.py:29-32`) → arama da aynı. Kişiler: `user_repo.search_directory` (aktifler, 5 alan). Arama `audit_log`'a **yazılmaz** (ADR-016 soru-cevap kaydıdır; arama bir soru değil); yalnızca yapısal log.
- **T5 — Proje bilgisi belgede var, kartta yok.** `documents.project_id` FK (`document.py:71`) ama `Document`'ta `relationship` yok; `_source_cards` (`ask.py:70-87`) `document`'ı elinde tutuyor. `Document.project` relationship + `SourceCard.project_code/project_name` yeter; ek sorgu belge başına küçük (alıntılanan belge sayısı ≤ ~5). Canlı DB: 49 ANK_RES, 15 IZM_RES, 10 projesiz belge (idari/kurumsal) → `null` meşru bir değer.
- **T6 — AI-BalBal her cevapta `/api/documents` + `/api/projects` çekip projeyi kendisi türetiyor** (`AskPanel.tsx:18-23`, `BalbalChat.tsx:35-38`, kart `SourceCardList.tsx:20,36`). Alan gelince bu iki istek ve "kullanıcının listeleyebildiği belge" varsayımı kalkar (Tansu tarafı); dondurulmuş sürüm yeni alanı görmezden gelir, kırılma yok.
- **T7 — Snippet güvenliği.** `ts_headline` varsayılan `<b>…</b>` işaretçileri kullanır; React'te bunu göstermek `dangerouslySetInnerHTML` ister. Belge metni kullanıcı yüklemesidir → snippet **düz metin** döner (`StartSel=''`, `StopSel=''`), vurguyu arayüz `q` ile kendi yapar (SORU 1).

---

## 2. Tasarım

### 2.1 `GET /api/search?q=&limit=` (B-14)

- `api/search.py`, `get_current_user`. `q`: zorunlu, 2–200 karakter (aksi 422); `limit`: 1–50, varsayılan 20 (belge başlığı için; proje/kişi listeleri zaten küçük).
- Cevap (`schemas/search.py`):
  ```python
  class SearchDocumentHit(DocumentListItem):   # id, title, document_type, …, file_kind
      snippet: str | None        # içerik eşleşmesinde en iyi chunk'tan düz metin; metadata eşleşmesinde None
      page_number: int | None    # snippet'in sayfası; metadata eşleşmesinde None
  class SearchResponse(BaseModel):
      documents: list[SearchDocumentHit]
      projects: list[ProjectResponse]
      people: list[DirectoryPerson]
  ```
- **Belgeler:** `allowed = allowed_document_ids(user, AuthorizationScope(), SqlDocumentIdsProvider)`.
  1. İçerik: `fts_query = build_search_query(q)` (sözlük genişletmeli, Balbal ile aynı — SORU 2). `document_chunk_repo.search_document_hits(session, allowed_ids, fts_query, limit)`: `DISTINCT ON (document_id)` + `ORDER BY document_id, rank DESC, chunk_index` ile belge başına **en iyi chunk**, dış sorguda `rank DESC, document_id` sırası ve `LIMIT`; `ts_headline('turkish', text, websearch_to_tsquery('turkish', q), 'MaxWords=24, MinWords=10, StartSel=, StopSel=')` yalnızca bu ≤ limit satır için hesaplanır (T1). Dönüş `(document_id, page_number, snippet, rank)`.
  2. Metadata: `document_repo.search_metadata(session, allowed_ids, q, limit)` — `title`/`document_type`/`counterparty`/`external_ref` `ILIKE %q%` (ham `q`, genişletme yok), başlık sırası. Bugünkü istemci davranışının sunucu karşılığı; işlenmemiş (`uploaded`/`ocr`) belgeler de bulunur, içerikleri henüz yok.
  3. Birleştirme: içerik hits (rank sırası) + yalnızca-metadata hits (başlık sırası), `document_id`'ye göre tekilleştirme, toplam `limit`. `DocumentListItem` alanları tek `list_by_ids` ile doldurulur.
- **Projeler:** `project_repo.search(session, q)` — `name`/`code` `ILIKE %q%`, `GET /api/projects` ile aynı görünürlük (pasifler dahil, SORU 3), `code` sırası.
- **Kişiler:** `user_repo.search_directory(session, q=q, department_slug=None)` → `DirectoryPerson` (Aşama C'deki uçla birebir).
- Boş `q` kabul edilmez (422); `nothing found` → üç boş liste, 200.
- Log: `search` satırı (`user_id`, `q[:100]`, üç sayım, süre); `audit_log` yok (T4).

### 2.2 `SourceCard.project_code` / `project_name` (B-20/6)

- `models/document.py`: `project: Mapped[Project | None] = relationship("Project")` (FK zaten var; `models/__init__` import sırası `Project`'i tanımlıyor).
- `schemas/ask.py::SourceCard`: `project_code: str | None = None`, `project_name: str | None = None` (eklemeli, varsayılan `None` → eski gövdeler geçerli).
- `ask._source_cards`: `document.project.code/name if document.project else None`.
- `audit_log.sources` JSONB `model_dump` ile otomatik taşır; `AuditLogDetail.sources: list[dict]` değişmez.
- `ExcelSourceCard`'a eklenmez (workbook kartı dosya/sheet/aralık; proje bilgisi istenmedi — SORU 4).

### 2.3 Dokunulmayanlar

`retrieve()`, `search_fts`, `build_search_query`, sözlük, `allowed_document_ids`, eval seti, `audit_log` şeması, `/api/documents`/`/api/projects`/`/api/directory` uçları, AI-BalBal, company-ai `frontend/`.

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `app/repositories/document_chunk_repo.py` | `_fts_predicate(query)` (ortak rank+where), `search_document_hits(...)` (DISTINCT ON + `ts_headline`) |
| `app/repositories/document_repo.py`, `project_repo.py` | `search_metadata(...)`, `search(...)` (ILIKE) |
| `app/schemas/search.py` (yeni), `app/api/search.py` (yeni), `app/api/router.py` | §2.1 |
| `app/models/document.py`, `app/schemas/ask.py`, `app/services/ask.py` | §2.2 |
| `tests/test_search.py` (yeni), `tests/test_document_chunk_repo.py`, `tests/test_ask.py`, `tests/test_ask_router.py` | §5 |
| `README.md` ("Arayüz"/"Soru sorma" yakınına kısa "İçerik araması" bölümü + kaynak kartı alanları), `docs/ARCHITECTURE.md` (ADR-007/ADR-020 concretization: arama aynı FTS'i paylaşır, retrieval'a dokunmaz; ADR-008/021: kart proje alanı), `docs/PHASES.md` notu, NOT (§1 B-14 + B-20/6 UYGULANDI, §4.1/§4.2 Tansu-tarafı: `SearchPanel`→`/api/search`, `projectOfDocument` kaldırılabilir), `docs/reports/ASAMA_D_REPORT.md` | docs |

Yeni uç: `GET /api/search`. Değişen (eklemeli): `POST /api/ask` (`sources[].project_code/project_name`). Migration: **yok**.

---

## 4. Uygulama sırası

1. `Document.project` + `SourceCard` alanları + `_source_cards` → `test_ask` (D-07).
2. `_fts_predicate` refactor + `search_document_hits` → `test_document_chunk_repo` (D-02/D-03); `make eval --retrieval-only` değişmedi.
3. `search_metadata`, `project_repo.search`; `schemas/search.py`, `api/search.py`, router → `test_search.py` (D-01, D-04..D-06, D-08).
4. `make test`, `make lint`, retrieval-only eval; canlı curl (§5 D-09).
5. Docs → rapor → düz commit + PHASES.md notu + push (SORU 5).

---

## 5. Kabul kriterleri ve kanıt

| # | Kriter | Test / komut |
|---|---|---|
| D-01 | Kimliksiz 401; `q` yok/1 karakter/201 karakter → 422; `limit=0`/`51` → 422 | `test_search.py` |
| D-02 | İçerik eşleşmesi: "DSCR covenant" → ilgili belge, `page_number` chunk'ın sayfası, `snippet` düz metin (işaretçi yok) ve sorgu terimini içeriyor; aynı belgede iki eşleşen sayfa → **tek** hit, en yüksek rank'li sayfa | `test_search.py` (fixture: `_document` + çok sayfalı chunk'lar), `test_document_chunk_repo.py::test_search_document_hits_one_per_document_with_headline` |
| D-03 | `search_fts` davranışı değişmedi (refactor): mevcut `test_retrieval.py`/`test_document_chunk_repo.py` yeşil, `--retrieval-only` 36/36 | komutlar |
| D-04 | Metadata eşleşmesi: başlıkta/muhatapta geçen ama içerikte geçmeyen terim → hit, `snippet`/`page_number` `None`; içerik hit'leri metadata hit'lerinden önce; `limit` uygulanır | `test_search.py` |
| D-05 | **Yetki:** `enerji` çalışanı için içerikte eşleşen `finans` belgesi sonuçta **yok**; `management` için var; projesi/kişisi her kimlikli kullanıcıya aynı | `test_search.py` |
| D-06 | Projeler `name`/`code` ILIKE ("ank" → Ankara RES, "IZM" → İzmir RES); kişiler `search_directory` ile aynı (unvan eşleşmesi dahil, 5 alan) | `test_search.py` |
| D-07 | `SourceCard.project_code/project_name`: projeli belgede dolu, projesiz belgede `None`; `audit_log.sources[0]` aynı alanları taşır | `test_ask.py` (mevcut zincir testine Project eklenir), `test_ask_router.py` |
| D-08 | Arama `audit_log`'a satır **yazmaz** | `test_search.py` (`audit_log_repo.list_filtered` boş) |
| D-09 | Canlı (`company-ai-dev`, LLM yok): `finans` ile `GET /api/search?q=DSCR` → belgelerde snippet + sayfa, `projects` Ankara RES/İzmir RES (`q=RES`), `people` boş; `GET /api/search?q=hukuk` → kişi 1; `enerji` ile `q=covenant` → `finans` belgesi yok. `/api/ask` canlı (1 soru, 2 LLM çağrısı): kart `project_code: "ANK_RES"`, `project_name: "Ankara RES"` | komut çıktıları rapora; AI-BalBal tarayıcı kontrolü Naci (henüz `/api/search`'ü çağırmıyor — bilgi) |
| D-10 | `make test`, `make lint` yeşil | komutlar |

---

## 6. SORU (Naci cevaplamalı)

1. **Snippet biçimi:** düz metin, işaretçisiz (öneri; XSS yüzeyi yok, vurguyu arayüz yapar) — mı, yoksa `ts_headline`'ın `<b>` işaretçileri mi?
2. **İçerik sorgusu:** `build_search_query(q)` (Balbal'la aynı: OR + sözlük genişletme; Türkçe "finansman" İngilizce sayfayı bulur; öneri) — mı, yoksa ham `websearch_to_tsquery(q)` (AND, genişletmesiz, daha dar) mı?
3. **Pasif projeler** aramada listelensin mi? Öneri: evet, `GET /api/projects` ile aynı görünürlük (arayüz `is_active`'i gösterir).
4. **`ExcelSourceCard`'a da `project_code/name`?** Öneri: hayır, istenmedi; workbook kartı dosya/sheet/aralık ile tanımlı.
5. **Faz birimi:** etiketsiz düz commit + PHASES.md notu (A/B/C ile aynı) — uygun mu?

---

## 7. Kendi aldığım küçük kararlar

- `limit` varsayılan 20, üst sınır 50; yalnızca belge listesine uygulanır (proje/kişi listeleri doğal olarak küçük, kişiler `search_directory`'nin 200 sınırında).
- Metadata ILIKE ham `q` ile, içerik FTS genişletilmiş sorguyla; `external_ref` de metadata eşleşmesine dahil (`DOC-ANK-FIN-004` aranabilir).
- `ts_headline` parametreleri `MaxWords=24, MinWords=10`; belge başına en iyi chunk `DISTINCT ON`.
- Arama `audit_log`'a yazılmaz; yapısal log satırı var.
- `Document.project` lazy relationship (alıntı başına bir küçük sorgu, cevapta ≤ ~5 kart); `selectinload` optimizasyonu gereksiz.
- `project_code/name` yalnızca `SourceCard`'da; `DocumentListItem`'a eklenmez (liste zaten `project_id` taşıyor, arayüzde proje listesi var).
