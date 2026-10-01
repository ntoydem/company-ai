# Aşama D Raporu — `GET /api/search` (B-14) + kaynak kartında proje (B-20/6)

**Tarih:** 01.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `<commit>`
**Plan:** `docs/plans/ASAMA_D_PLAN.md` · **ADR:** ADR-020 ve ADR-021 concretization; yeni ADR yok · **Migration:** yok

Naci'nin SORU cevapları (hepsi planın önerisi yönünde): (1) düz metin snippet, işaretçisiz; (2) `build_search_query` (sözlük genişletmeli, Balbal ile aynı); (3) pasif projeler listelenir; (4) `ExcelSourceCard`'a proje alanı yok; (5) etiketsiz düz commit. D-09 canlı doğrulamayı backend yaptı; Tansu'nun arayüzü henüz `/api/search`'ü çağırmadığı için tarayıcı adımı yok.

## 1. Kabul kriterleri (plan §5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| D-01 | Kimliksiz 401; `q` yok/1/201 karakter → 422; `limit` 0/51 → 422; eşleşme yok → üç boş liste, 200 | ✅ | `test_search.py::test_search_requires_login_and_validates_params` |
| D-02 | İçerik eşleşmesi: `page_number` = en iyi chunk'ın sayfası, `snippet` düz metin (`<b>` yok) ve terimi içerir; aynı belgede birden çok eşleşen sayfa → tek hit, en yüksek rank'li sayfa | ✅ | `test_document_chunk_repo.py::test_search_document_hits_one_per_document_best_page_with_plain_headline` (covenant maddesi s.5, tanım s.6 ve kapak s.1'i geçer); `test_search.py::test_content_hits_carry_snippet_and_page_and_come_before_metadata_hits` |
| D-03 | `search_fts` davranışı değişmedi (ortak predicate refactor'ı) | ✅ | `test_retrieval.py` + `test_document_chunk_repo.py` yeşil; `make eval EVAL_ARGS="--retrieval-only"` recall@80 **36/36** |
| D-04 | Metadata eşleşmesi (`snippet`/`page_number` `None`) içerik hit'lerinden sonra; `limit` uygulanır | ✅ | aynı test + `test_limit_caps_documents` |
| D-05 | Yetki: `enerji` için içerikte **ve** başlıkta eşleşen `finans` belgesi sonuçta yok | ✅ | `test_search_respects_allowed_document_ids`; canlı: `enerji` `q=covenant` → yalnızca `enerji_grubu` (1 hit), `finans` 0 |
| D-06 | Projeler `name`/`code` ILIKE (`ank` → ANK_RES; `RES` → ANK_RES, IZM_RES); kişiler `search_directory` ile aynı, 5 alan | ✅ | `test_projects_and_people_match_name_code_and_title`; canlı: `q=RES` → iki proje (`is_active` dahil), `q=hukuk` → Hukuk Müşaviri |
| D-07 | `SourceCard.project_code/project_name`: projeli belgede dolu, projesizde `None`; `audit_log.sources[0]` aynı alanları taşır | ✅ | `test_ask.py::test_sources_come_from_citations_with_page_and_chain` (Amendment 01 → `ANK_RES`/"Ankara RES", projesiz Facility Agreement → `None`); canlı: iki kartta `ANK_RES Ankara RES`, son audit satırı `sources->0->>project_code = ANK_RES` |
| D-08 | Arama `audit_log`'a yazmaz | ✅ | `test_content_hits_…` (`list_filtered == []`); canlı: aramalardan sonra 725, yalnızca `/api/ask` 726 yaptı |
| D-09 | Canlı (`company-ai-dev`, seed'li) | ✅ | `finans` `q=DSCR&limit=5` → 5 içerik hit'i (Facility Agreement s.7 "…DSCR) of 1.25x. Compliance with this DSCR covenant…", Amendment 01 s.4 "…to 1.20x with effect from March 15, 2025…", Covenant Compliance Report'lar s.3), `projects []`, `people []`; `/api/ask` 1 soru (2 LLM çağrısı) → kartlarda proje alanları |
| D-10 | `make test`, `make lint` yeşil | ✅ | **438 geçti** (432 + 6 yeni), 15 deselected (`live`), 5 dk 10 sn; lint yeşil (ruff/format/mypy 96 dosya, prompt dokümanları, ledger/documents/excel doğrulayıcıları) |

## 2. Yapılanlar

- **`document_chunk_repo`:** `_fts_predicate(query)` — `search_fts`'in rank + where ifadesi tek yere alındı (davranış aynı, D-03); yeni `search_document_hits(allowed_ids, query, limit)` — `DISTINCT ON (document_id)` ile belge başına en iyi chunk, dış sorguda rank sırası + `LIMIT`, `ts_headline('turkish', text, websearch_to_tsquery, 'MaxWords=24, MinWords=10, StartSel="", StopSel=""')` yalnızca son satırlar için; `DocumentHit(document_id, page_number, snippet, rank)`.
- **`document_repo.search_metadata`** (title/type/counterparty/`external_ref` ILIKE, allowed küme içinde), **`project_repo.search`** (name/code ILIKE, pasifler dahil).
- **`GET /api/search?q=&limit=`** (`api/search.py`, `schemas/search.py`): `allowed_document_ids` → içerik hit'leri (`build_search_query(q)`) → yalnızca-metadata hit'leri (ham `q`) → `SearchDocumentHit` (= `DocumentListItem` + `snippet` + `page_number`), `projects: ProjectResponse[]`, `people: DirectoryPerson[]`; yapısal log, `audit_log` yok.
- **`DirectoryPerson.from_user`** — `/api/directory` ve `/api/search` aynı dönüşümü paylaşır (Aşama C'deki kopya kaldırıldı).
- **B-20/6:** `Document.project` relationship; `SourceCard.project_code/project_name`; `ask._source_cards` doldurur; audit `sources` JSONB otomatik taşır.
- **Docs:** README "İçerik araması — Aşama D" bölümü (+ kaynak kartı proje alanı), ADR-020/ADR-021 satırları, PHASES.md notu, NOT §1 B-14 + B-20/6 UYGULANDI, §4.1 "Proje" satırı, §4.2 "Üst bar arama"/"kaynak kartı" satırları (Tansu tarafı: `proposed.ts`'e `/api/search` sözleşmesi + `SearchPanel` bağlama; `projectOfDocument` kaldırılabilir).
- **Dokunulmayanlar:** `retrieve()`, `search_fts`, `build_search_query`, sözlük, `allowed_document_ids`, eval seti, `audit_log` şeması, `/api/documents`/`/api/projects`/`/api/directory`, `ExcelSourceCard`, AI-BalBal, company-ai `frontend/`.

## 3. Değişen dosyalar

Uygulama commit'i: kod `app/repositories/{document_chunk_repo,document_repo,project_repo}.py`, `app/schemas/{search (yeni),directory,ask}.py`, `app/api/{search (yeni),directory,router}.py`, `app/models/document.py`, `app/services/ask.py`; testler `tests/test_search.py` (yeni), `tests/{test_document_chunk_repo,test_ask}.py`; docs `README.md`, `docs/{ARCHITECTURE,PHASES}.md`, `docs/notes/TANSU_…md`, bu rapor.

## 4. Testler

- Backend: **438 geçti** (6 yeni: 5 `test_search.py`, 1 chunk-repo; `test_ask` zincir testi proje assert'leriyle genişletildi), 15 deselected, 5 dk 10 sn.
- Geçici kırmızılar (ikisi de testlerle yakalandı, canlıya gitmedi): (a) `ts_headline(VARCHAR, text, tsquery, VARCHAR)` — Postgres yalnızca `(regconfig, text, tsquery, text)` imzasını çözer; SQLAlchemy literal'leri `VARCHAR` bağladığı için `cast(…, REGCONFIG)`/`cast(…, Text)` eklendi. (b) `StartSel=, StopSel=` boş değerler `invalid parameter list format` — doğru biçim `StartSel="", StopSel=""` (DB'de doğrulandı: `[minimum DSCR covenant of 1.20x at each test date.]`). Ayrıca ilk test taslağı mevcut `_chunk` yardımcısının imzasına uymuyordu, teste yerel `page()` yardımcısı yazıldı.
- `make lint` yeşil; `--retrieval-only` 36/36.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| `ts_headline` argümanlarına açık `REGCONFIG`/`Text` cast'ı; seçiciler `""` | §4 (a)/(b) | Snippet düz metin |
| `_fts_predicate` refactor'ı `search_fts`'in içine de uygulandı | Tek tanım; ikisinin ayrışması "aramada var, Balbal bulamadı" tutarsızlığı yaratırdı | `test_retrieval` + eval değişmedi |
| Metadata hit'leri yalnızca içerik hit'lerinin doldurmadığı yere, başlık sırasıyla | Plan §2.1/3 | — |
| `DirectoryPerson.from_user` ortak | İki uçta aynı 5 alan kopyalanmasın | `/api/directory` davranışı aynı |
| Snippet'lerde "DEMO DEMO…" banner'ı görünebilir (Covenant Compliance Report s.3 örneği) | `ts_headline` pencereyi eşleşen terime göre seçiyor; demo belgelerin her sayfasında banner var (SPEC_05) | Kozmetik, demo verisine özgü; gerçek belgede yok. İstenirse `MaxWords`/`MinWords` ayarı ya da banner satırının chunk'tan düşürülmesi ayrı iş |
| Arama `limit` yalnızca belge listesine | Plan §7 | Proje/kişi listeleri doğal olarak küçük |

## 6. Açık sorular (Naci cevaplamalı)

- Yok. Tansu tarafı: `proposed.ts`'e `GET /api/search` sözleşmesi, `SearchPanel`'in bu uca bağlanması (snippet düz metin, vurguyu arayüz `q` ile yapar), `projectOfDocument` türetmesinin kaldırılması (NOT §4.1/§4.2).

## 7. Riskler / sonraki adım için notlar

- AI-BalBal `b219600` `/api/search`'ü çağırmıyor; üst bar araması Tansu bağlayana kadar istemci-tarafı süzme ile çalışır (bugünkü davranış, kırılma yok).
- İçerik sorgusu sözlük genişletmeli (SORU 2): kısa Türkçe sorgular İngilizce sayfaları da bulur; aynı zamanda "geniş" eşleşme üretebilir — Balbal retrieval'ıyla tutarlı, bilinçli.
- Sonraki aday (NOT): B-26 klasörler (bir SORU: klasör ağacı müşteri mi platform mu), `data_conflict` prompt turu, B-01/B-11 (ledger'a `expiration_date` gelince).

## 8. Doğruladığım üçüncü taraf davranışları

- Postgres 16.15 `ts_headline`: imza `(regconfig, text, tsquery, text)`; `StartSel`/`StopSel` boş bırakılamaz ama `""` kabul edilir ve işaretçisiz çıktı verir; `MaxWords=24, MinWords=10` ile covenant cümlesi pencereye giriyor.
- SQLAlchemy 2.x: `func.websearch_to_tsquery` bilinen fonksiyon (config'i `REGCONFIG` bağlar), `func.ts_headline` bilinmiyor → `cast(literal(...), REGCONFIG)` gerekli; `select(...).distinct(col)` Postgres `DISTINCT ON` üretir.
- Pydantic v2: `SearchDocumentHit(**DocumentListItem.model_validate(doc).model_dump(), snippet=…, page_number=…)` türetilmiş şemayı doldurur; `file_kind` property'si `from_attributes` ile taşınır.

## 9. Kaynak kullanımı

- Değişiklik yok; LLM: canlı doğrulamada 1 soru (2 çağrı), aramalar LLM'siz.
