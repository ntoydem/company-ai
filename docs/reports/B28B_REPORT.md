# B-28b Raporu — ek alanlar, etiket kataloğu, tür bazlı alan rehberi

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (düz commit + PHASES.md notu)  **Commit:** `75234e6`
**Plan:** `docs/plans/B28B_PLAN.md` · **ADR:** **ADR-025** (yeni) + ADR-024 satırı · **Migration:** `0014_extra_fields_tag_catalog_guide` · **Kapsam:** yalnızca backend (AI-BalBal PR-5 ayrı)

Naci'nin SORU cevapları (02.10.2026, hepsi planın önerisiyle): (1) etiket doğrulaması **katı**; (2) demo `parties` → `extra_fields`; (3) türe göre zorunlu alan **yok**, yalnızca vurgu; (4) retrieval sıralamasına girmez; (5) `SearchDocumentHit.matched_on` eklendi; (6) genel `admin_events` tablosu; (7) etiketsiz commit + PHASES.md + ADR-025.

## 1. Kabul kriterleri (plan §5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| X-01 | Migration `0014` ileri/geri; mevcut etiketler `identity`, 9 değişiklik etiketi `change`; `extra_fields = {}`; rehber 10 aile; seed = migration anlık görüntüsü | ✅ | `test_migrations::test_0014_seeds_change_tags_existing_tags_and_the_starter_guide`, `test_b28b::test_seed_matches_the_migration_snapshot_and_is_idempotent` |
| X-02 | `submit` ek alan yazar (`source` ai/user, `added_by_id`), `field_added` olayı; %80 kuralı `extra_fields.<key>` için 422 + `fields` listesi, `confirmed_fields` ile geçer (`field_confirmed`) | ✅ | `test_submit_stores_extra_fields_with_source_and_events`, `test_low_confidence_extra_field_needs_confirmation_and_unknown_tag_is_refused` |
| X-03 | Katalog dışı etiket → 422 `unknown_tag` (submit/PATCH); geçersiz anahtar/limit → 422 `invalid_extra_fields`; aktif etiket geçer | ✅ | aynı testler + `test_admin_patch_edits_extra_fields_and_validates_tags` (PATCH; onaylı belgede T9 onay düşer; `null` ile silme) |
| X-04 | Admin `/api/admin/tags` POST/PATCH (slug biçimi 422, çift 409, pasifleştirme), `/api/tags` herkese aktifler, employee 403, `admin_events` satırları + `/api/admin/events` | ✅ | `test_tag_catalogue_admin_crud_everyone_reads_active` |
| X-05 | Rehber admin PATCH/POST (aile 409), `/api/document-type-guide` herkese; aile eşleştirme birim testi (Facility Agreement→contract, Licence Amendment→amendment, Üretim Lisansı→licence_permit, Covenant Report→workbook, bilinmeyen→other); Türkçe `İ` katlama | ✅ | `test_match_family_picks_the_most_specific_pattern`, `test_guide_admin_edit_everyone_reads_active` |
| X-06 | Sınıflandırıcı promptu aktif etiket listesi + rehber bloğu içerir; `extra_fields` anahtar normalizasyonu + liste değer birleştirme + 20 sınırı; katalog dışı etiket düşer → `tags.dropped` | ✅ | `test_classifier_prompt_carries_catalogue_and_guide_and_sanitises_output` |
| X-07 | `/api/search` etiket ve ek alan değerinde eşleşir, `matched_on: tag / extra_field`; yetki süzgeci aynen | ✅ | `test_search_matches_tags_and_extra_fields_with_matched_on` |
| X-08 | Prompt kaynak satırı `Muhatap \| Etiketler \| Ek alanlar` yalnızca varsa; sistem promptu değişmedi (`make lint` prompt eşitliği) | ✅ | `test_prompt_source_carries_tags_and_extra_fields_only_when_present`; `describe_metadata` birim |
| X-09 | Sinyal ucu: iki `field_added` → `{contract, parties, 2}`; employee 403; salt okunur | ✅ | `test_guide_signals_count_staff_added_keys_per_family` |
| X-10 | Regresyon + canlı (LLM ≤ 2) | ✅ (§3) | §3 |
| Seed | `parties` → `extra_fields.parties` (`source=user`) belge ve workbook'ta; başka anahtar yok | ✅ | `test_demo_documents_seed::test_seed_records_ledger_parties_as_extra_field` |

## 2. Yapılanlar

- **Veri modeli (migration `0014`):** `documents.extra_fields JSONB DEFAULT '{}'`; `tag_catalog` (`tag_kind` enum); `document_type_guide`; `admin_events`; `document_review_event_kind` + `field_added`. Veri adımı: 9 değişiklik etiketi + mevcut etiketler (identity) + 10 rehber ailesi (`type_family.DEFAULT_*` tek kaynak; seed aynı satırlar).
- **Saf kurallar:** `services/type_family.py` (başlangıç rehberi, `match_family` en uzun desen, `normalize_extra_key`, `fold` Türkçe İ), `services/document_review.py` (`normalize_extra_updates`, `merge_extra_fields` → source/added/changed, `flatten_suggestion`, `EXTRA_PREFIX`).
- **Sınıflandırıcı:** prompt'a katalog + rehber bloğu, `extra_fields` çıktı; `_sanitize` etiket süzme (`dropped`), anahtar normalizasyonu, 20 sınırı.
- **API:** `submit`/`apply`/`PATCH` → `extra_fields` (null = sil) + katı etiket doğrulaması (`unknown_tag`), `invalid_extra_fields`; `field_added` olayı; yeni `api/tags.py` (`/api/tags`, `/api/admin/tags`), `api/guide.py` (`/api/document-type-guide`, `/api/admin/document-type-guide`, `/signals`, `/api/admin/events`); `/api/search` `matched_on`.
- **Prompt:** `answer_prompt.describe_metadata` + `format_source` tek satır; sistem promptu (kurallar) dokunulmadı.
- **Repo/seed:** `tag_repo`, `guide_repo`, `admin_event_repo`; `demo_catalog_seed` + CLI `seed-demo-catalog` + entrypoint; generator manifestlerine `parties`; `demo_documents_seed` → `extra_fields.parties` (mevcut kurulumda bir kez).
- **Testler:** `tests/test_b28b_catalog_guide.py` (12), `test_migrations` (+1), `test_demo_documents_seed` (+1); `conftest` her testten sonra kataloğu yeniden kurar (`company_settings` ile aynı desen); `cast` fixture'ı conftest üzerinden paylaşılıyor.
- **Dokunulmayanlar:** kapı, `review_status` makinesi, retrieval sıralaması, sistem promptu, router, Excel motoru, klasör önerisi.

## 3. Doğrulama

- `make test`: **495 geçti (480 + 15 yeni: 12 `test_b28b_catalog_guide`, 1 migration, 1 seed `parties`, 1 güncellenen), 15 deselected, 10 dk 04 sn; ocr-worker 9 geçti. İlk tam turda 102 teardown hatası (`log.info(extra={"created": …})` — `created` rezerve `LogRecord` alanı) → anahtar `created_keys` yapıldı, ikinci tur temiz**. `make lint`: **0 error(s)** (ruff + format + mypy 117 dosya; prompt dokümanı eşitliği yeşil — sistem promptu değişmedi). `--retrieval-only`: **recall@80 39/39 (%100)**, `EVAL_EXIT=0`. `validate-ledger`: 0 error(s), 0 warning(s).
- **Canlı** (Caddy üzerinden curl; LLM: **1 çağrı** (`/api/ask`)):

```text
backend logs: Running upgrade 0013 -> 0014 … seed-demo-catalog done (created_keys [], total 19 — migration zaten kurdu)
make seed-demo-documents: "demo document parties added" ×74 → documents where extra_fields ? 'parties' = 74
  DOC-ANK-FIN-001 parties = "DEF Enerji Üretim A.Ş., PQR Bank, VWX Export Credit Agency"
tag_catalog: change 9, identity 11; document_type_guide: 10 aile

GET /api/tags (finans) → 20 aktif (9 change + 11 identity); admin POST /api/admin/tags pf-kredi → 201
GET /api/document-type-guide → 10 aile
finans upload "Service Agreement" (Excel) → pending_metadata
  submit tags=["serbest"] → 422 unknown_tag ["serbest"]
  submit tags=["pf-kredi","vade-değişikliği"], extra_fields={parties, "Sözleşme Bedeli"} → pending_review;
        extra_fields: parties (user), sozlesme_bedeli (user — anahtar normalize edildi)
finans_mudur approve → approved
/api/search q=pf-kredi (yonetim) → belge, matched_on=tag; q="XYZ Servis" → matched_on=counterparty (önce muhatap eşleşti)
admin review-events: uploaded, field_added(extra_fields.parties), field_added(extra_fields.sozlesme_bedeli), submitted, approved
admin signals: [{contract, parties, 1}, {contract, sozlesme_bedeli, 1}]  — "Service Agreement" → contract ailesi
admin events: [tag_created pf-kredi]
LLM (1): "Ankara RES Facility Agreement sözleşmesinin tarafları kimler?" (finans) →
  "… tarafları DEF Enerji Üretim A.Ş., PQR Bank ve VWX Export Credit Agency'dir [K1]" — kaynak Facility Agreement Amendment 02;
  değer prompt'taki "Ek alanlar: parties=…" satırından (chunk metni tarafları bu biçimde içermiyor); product P1, uyarı yok
Temizlik: test belgesi silindi (documents = 75 = 74 seed + Naci'nin tarayıcı test belgesi); pf-kredi pasifleştirildi (emekli etiket, silinmez)
```

## 4. Kendi aldığım küçük kararlar

| Karar | Neden |
|---|---|
| Rehber eşleştirme "en uzun desen kazanır" | "Licence Amendment" hem `licence` hem `amendment` → tadil daha özgül; "Covenant Report" → `workbook` (desen `covenant report`) |
| `fold()` ile Türkçe İ katlama | `"İhale".casefold()` birleşik nokta bırakıyor; desen/tip karşılaştırması ASCII'ye indirilmiyor, yalnızca İ düzeltiliyor |
| `extra_fields` değerleri her zaman metin; liste gelirse virgülle birleştirilir | kural 3 (aritmetik yok), JSON sadeliği |
| `source=ai` yalnızca değer öneriyle **aynıysa**, güven o zaman saklanır | "personel ekledi" ayrımı (§4.7.3) net kalsın |
| Katalog dışı AI etiketi `tags.dropped`'a yazılır, `admin_events`'e değil | belgeye ait bilgi; admin öneri satırında görür |
| `admin_events` genel adıyla (tag/guide bugün, rol/üyelik sonra) | SORU 6 |
| Excel manifest yeniden üretildi, `.xlsx` ikilileri geri alındı | yalnızca `parties` alanı için manifest değişti; ikili churn commit edilmez |
| conftest her testten sonra kataloğu yeniden kurar | TRUNCATE migration'ın veri adımını siliyordu; `company_settings` ile aynı çözüm |

## 5. Açık sorular

- Yok. Tansu: etiket listesini/rehberi tamamlaması (BACKEND_GAPS §4.7.9/2) artık admin ekranından yapılabilir (PR-5 sonrası); klasör önerisi + 4.7.9/1 kararı.

## 6. Sonraki adım

- **AI-BalBal PR-5:** etiket seçici (katalog), 1. aşama panelinde ek alan satırları + "alan ekle" + rehber ipuçları, Yönetim › Etiketler / Tür rehberi sayfaları, arama sonucunda `matched_on` rozeti — T-12 onay bekleyen yeni öğeler.
- Kalan B-28: klasör önerisi (B-26 ağacı prompt'a) + yerleştirme onayı (Tansu kararı).
