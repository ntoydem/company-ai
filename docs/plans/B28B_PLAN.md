# B-28b — `extra_fields`, etiket kataloğu, tür bazlı alan rehberi — Uygulama Planı

**Tarih:** 02.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.** · **Kapsam:** company-ai backend (+ AI-BalBal için ayrı PR-5 notu) · **Ürün:** Ürün 1 — Tanıma (Ek-B: "belgeleri sınıflandırır, indeksler, belgeler arasında bağlantı kurar"; Ek-D S-6 belge girişi)

Kaynak: NOT §2 B-28 "Kalan çekirdek" (B-28b tanımı: `extra_fields JSONB`, `tag_catalog`, tür bazlı rehber, klasör önerisi); BACKEND_GAPS (dondurulmuş `b219600`) §4.7.1 ("can alıcı olanı eksiksiz, gerisini hiç"), §4.7.2 (tür/içeriğe göre değişen alan seti; **sabit form yok**, rehber var, P-8), §4.7.3 (personelin eklediği alan, "personel ekledi" ayrımı, rehber iyileşme sinyali), §4.7.4 (az ve tutarlı etiket; kimlik + değişiklik etiketleri; **sabit listeden**, liste insan kararıyla büyür; 9 başlangıç değişiklik etiketi), §4.7.5 (%80 kuralı), §4.7.6 (kayıt defteri), §4.7.9 (açık noktalar: rehber ve etiket listesi ürün sahibi tamamlayacak); Tansu'nun ilkesi (NOT §5.1/§8.1): yapı taşlarını **müşteri admin'i** yönetir, kural motoru kodda kalır; ADR-004/007/024; backend `metadata_suggestion.py` (9 sabit alan, beyaz liste), `document_repo.search_metadata` (title/type/counterparty/external_ref ILIKE), `answer_prompt.format_source` (prompt başlığı: başlık, tarih, yürürlük, versiyon, durum, sayfa), `document_chunks.tsv_*` (yalnızca chunk metni), ledger (`type`, `parties`, `key_facts`).

---

## 0. Tespitler

- **T1 — Bugün ne var:** `documents.tags` serbest `ARRAY(String)`; upload hiç yazmıyor (`tags=[]`), yalnızca seed ve `apply`/`submit`/`PATCH` yazıyor; demo'da 71 belgede 11 farklı etiket (`ANK_RES, IZM_RES, COMPANY, DRAFT, EXECUTED, AMD01, AMD02, V01, V02, onay akışı, test`) — hepsi "kimlik" türü, çoğu proje/durum/versiyon tekrarı. Ek alan yok. AI önerisi 9 sabit alan + `tags` serbest liste. Prompt kaynağa yalnızca başlık/tarih/yürürlük/versiyon/durum/sayfa yazıyor — **etiketler ve muhatap bile prompt'a girmiyor**; FTS yalnızca chunk metninde; `/api/search` metadata eşleşmesi title/type/counterparty/external_ref.
- **T2 — Ledger zaten "ek alan" modelini taşıyor:** her belgede `parties` (taraflar) ve `key_facts` (örn. `dscr_covenant`, `tenor_years`, `capacity_mw`, `licence_date`, `ced_status`). Yani B-28b'nin `extra_fields`'ı yeni bir fikir değil; ledger'daki anahtarlar başlangıç rehberinin **gerçek** örnekleridir (uydurma değil). `type` değerleri 50+ serbest ad ("Facility Agreement", "Üretim Lisansı", "Covenant Report", "ÇED Durum Yazısı"…) → rehber **aile** bazlı olmalı, tek tek tür adına değil.
- **T3 — Etiket kataloğu müşteri admin'inin işi.** §4.7.4 "sabit liste, insan kararıyla büyür" + Tansu "yapıyı müşteri yönetir" → `tag_catalog` tablosu, admin CRUD; kural motoru (doğrulama) kodda. Başlangıç içeriği: §4.7.4'teki 9 değişiklik etiketi + mevcut verideki 11 kimlik etiketi (yoksa 71 belge geçersiz olur). Sabit kod listesi **değil**.
- **T4 — Rehber de müşteri admin'inin işi, zorunlu form değil.** §4.7.2: "sabit form yok… Balbal'ın yargısına yön veren bir rehber"; P-8 şirket bazında. → `document_type_guide` tablosu (aile → önerilen ek alanlar + önerilen etiketler + prompt ipucu), admin CRUD; **zorunluluk üretmez** (yüklemenin zaten zorunlu 4 alanı var: başlık, tür, tarih, muhatap). "Zorunlu/önerilen gösterimi": zorunlu = mevcut çekirdek alanlar; önerilen = rehberden. Türe göre ek **zorunlu** alan → SORU 3.
- **T5 — B-28 entegrasyonu hazır zemin:** `submit` gövdesi + `confirmed_fields` + `document_review_events` (`field_edited/field_confirmed`) var; `extra_fields` aynı mekanizmaya anahtar bazında girer; "personel ekledi" = `field_added` olayı (§4.7.3). `apply`/`PATCH` T9 kuralına tabi kalır.
- **T6 — Aranabilirlik üç katmanda:** (a) `/api/search` metadata eşleşmesi → `tags` ve `extra_fields` değerleri ILIKE'a girer (ucuz); (b) `/api/ask` prompt kaynak başlığı → `Muhatap`, `Etiketler`, `Ek alanlar: k=v;…` satırı eklenir (Balbal "aynı bilgiyle" cevaplar — §4.7.3); (c) retrieval sıralaması (chunk FTS) **değişmez** — belge metadata'sı için ayrı tsvector/boost ADR-007 değişikliğidir, bu turda yok (SORU 4). Prompt değişikliği `make prompt-doc`/`--repeat` ölçümü ister → yalnızca **kaynak başlığı** değişir, sistem promptu (kurallar 1–10) değişmez; eval `--retrieval-only` + 2–3 soruluk küçük canlı kontrol yeter.
- **T7 — Klasör önerisi (§4.7.2 son paragraf, §4.7.9/1)** bu turda **yok**: Balbal'ın klasör önermesi B-26 ağacını prompt'a koymayı ve "yazma yetkisi olmayan klasöre yerleştirme onayı" kararını (Tansu'da) ister; ayrı tur.
- **T8 — Anayasa:** Ç-15/4 veri modeli değişikliği → plan onayı (bu belge). Ç-11/T-5: `extra_fields` prompt'a yalnızca **yetkili belgenin** kaynak bloğunda girer (gate değişmez). O-7 Kurumsal Hafıza: personelin eklediği alan belgenin metadata'sıdır, "bilinçli eklenen not" sınıfında (CLAUDE.md) — soru-cevap değil.

## 1. `extra_fields` — nedir, hangi türde ne

**Model:** `documents.extra_fields JSONB NOT NULL DEFAULT '{}'` — `{ "<key>": {"value": str, "source": "ai"|"user", "confidence": float|null, "added_by_id": uuid|null, "added_at": iso} }`. Anahtar: `snake_case`, 1–48 karakter; değer: metin (tarih/sayı da metin; aritmetik yok — kural 3). Belge başına en fazla 20 anahtar (gürültü sınırı, §4.7.1). Anahtar isimleri **serbest** (personel açar), rehber yalnızca önerir.

**Başlangıç rehberi — aileler ve önerilen ek alanlar (BACKEND_GAPS §4.7.2 + ledger `parties`/`key_facts`'tan; rakam yok, yalnızca anahtar adları):**

| Aile (`family`) | Eşleşen tür adları (ledger'dan örnek) | Önerilen ek alanlar (`suggested_extra_fields`) | Önerilen etiketler |
|---|---|---|---|
| `contract` | Facility Agreement, Common Terms Agreement, EPC Contract, O&M Agreement, Service Agreement, Spare Parts Agreement, Lease Agreement, Share/Account Pledge, Assignment Agreement, Bağlantı Anlaşması, Saha Kullanım Hakkı Sözleşmesi | `parties` (taraflar), `contract_value` + `currency`, `effective_date`* , `expiry_or_tenor`, `governing_law` | kimlik: proje/konu/`sozlesme` |
| `amendment` | Licence Amendment, Change Order, Waiver Letter, "Amendment …" | `amends` (hangi sözleşme — zaten `supersedes_document_id`, rehber bunu **ister**), `changed_items` (yalnızca işaret, özet değil — §4.7.2) | **değişiklik etiketleri** (§4.7.4 listesi) |
| `licence_permit` | Üretim Lisansı, Önlisans, Yapı Ruhsatı, ÇED Olumlu Kararı, Grid Connection Certificate, Bağlantı Görüşü Başvurusu | `authority` (kurum), `licence_no`, `capacity_mw`, `valid_until` | kimlik |
| `report` | Technical/Teknik Rapor, Covenant/Production/Maintenance/Availability/Completion/Performance Test Report, Legal Review Memo, Risk Report, Management Report | `period` (dönem), `prepared_by`, `subject_asset` | kimlik |
| `resolution_minutes` | Board Resolution, Shareholder Resolution, Toplantı Tutanağı, Budget Approval | `meeting_date`*, `resolution_no`, `decision_subject` | kimlik |
| `insurance` | Insurance Policy/Summary/Notice/Review Memo | `insurer`, `policy_no`, `coverage_period`, `insured_asset` | kimlik |
| `correspondence` | Drawdown Notice, Insurance Notice, ÇED Durum Yazısı, Ön Görüş Talebi, Legal Opinion | `sender`, `recipient`, `reference_no`, `reply_due` | kimlik |
| `invoice` (GAPS örneği; demo'da yok) | Fatura | `vendor` (zaten `counterparty`), `work_description`, `invoice_no`, `amount` + `currency` | kimlik |
| `workbook` | Financial Model, Covenant Report (xlsx), Budget vs Actual, Monthly Production | `period`, `data_scope` (hangi proje/dönem), `source_system`; **formül özeti değil** — yapı `inspect` ile zaten veriliyor, formül içeriği yapılandırılmaz (kural 3: hesabı DuckDB yapar, LLM/metadata değil) | kimlik |
| `other` | eşleşmeyen | yok | — |

\* zaten standart alan (`effective_date`) — rehber "bu türde doldur" der, yeni alan açmaz. Eşleştirme: `document_type_guide.type_patterns` (küçük harf alt-dize listesi, örn. `["agreement","sözleşme","contract","pledge","anlaşma"]`); eşleşme yoksa `other`. Rehber **config'tir, veri değil** → ledger'a girmez, seed ile başlangıç satırları yazılır, admin düzenler.

## 2. Etiket kataloğu

- **Tablo `tag_catalog`:** `slug` (PK, `kebab-case`, Türkçe karakterli serbest; örn. `faiz-değişikliği`), `label`, `kind: identity|change`, `is_active`, `created_by_id`, `created_at`. **Admin CRUD** `GET/POST/PATCH /api/admin/tags` (+ `is_active=false` ile emeklilik; silme yok — geçmiş belgeler referans verir), herkes için `GET /api/tags` (aktifler; yükleme/1. aşama seçici). Değişiklikler `tag_catalog_events` yerine mevcut desen: `document_review_events` **değil** (belgeye bağlı değil) → küçük `catalog_events(kind: tag|guide, actor, before, after)` tablosu (ADR-023 `folder_grant_events` deseni). Tansu ilkesi: **yapıyı admin yönetir, kuralı kod** — kural = "etiket katalogdan gelir".
- **Başlangıç (seed + migration veri adımı):** §4.7.4'ün 9 değişiklik etiketi (`faiz-değişikliği`, `teminat-yapısı-değişikliği`, `vade-değişikliği`, `kredi-tutarı-değişikliği`, `ödeme-planı-değişikliği`, `finansal-taahhüt-değişikliği`, `taraf-değişikliği`, `temettü-dağıtım-koşulu-değişikliği`, `sigorta-şartı-değişikliği`) `kind=change` + mevcut verideki 11 etiket `kind=identity` (migration `SELECT DISTINCT unnest(tags)` ile; boş DB'de no-op, seed aynı listeyi kurar — Aşama C/E deseni). `test`/`onay akışı` gibi test kalıntıları Naci isterse sonradan pasifleştirir (admin).
- **Doğrulama (kural):** `submit`, `apply`, `PATCH`, upload (`tags` form alanı eklenirse) → her etiket **aktif** katalogda olmalı, aksi 422 `unknown_tag` + `{fields: ["tags"], unknown: [...]}`; AI önerisindeki katalog dışı etiket `_sanitize`'da düşürülür ve `document_review_events` değil, öneri satırında `fields.tags.dropped: [...]` olarak saklanır (defterde "Balbal şunu önerdi, katalogda yok" görünür — §4.7.3'ün "rehber iyileşme sinyali" mantığı etikete de uygulanır). Katalog dışı etiket **otomatik eklenmez** (büyüme insan kararı).
- **Prompt:** sınıflandırıcıya aktif etiket listesi verilir ("tags: yalnızca şu listeden"), `kind=change` etiketleri yalnızca `amendment` ailesine önerilir.

## 3. Tür bazlı alan rehberi

- **Tablo `document_type_guide`:** `family` (PK), `label`, `type_patterns: text[]`, `suggested_extra_fields: jsonb [{key, label, hint}]`, `suggested_tags: text[]` (katalog slug'ları), `standard_fields_emphasis: text[]` (bu türde özellikle doldurulması beklenen standart alanlar, örn. `effective_date`, `supersedes_document_id`), `prompt_hint: text`, `is_active`. **Admin CRUD** `GET/PATCH /api/admin/document-type-guide` (aile satırları düzenlenir; yeni aile eklenebilir), herkes `GET /api/document-type-guide` (aktifler).
- **Kullanım:** (a) **Sınıflandırıcı** — prompt'a rehber özeti girer (aile → önerilen anahtarlar + ipucu); model `extra_fields` için `{key: {value, confidence}}` döndürür, yalnızca rehberdeki anahtarlar + metinde açıkça geçenler, uydurma yok; `_sanitize` anahtar adını normalize eder, 20 sınırı uygular. (b) **Arayüz** — 1. aşama paneli ve yükleme formu seçilen türün ailesini `type_patterns` ile bulur, "Bu türde genellikle…" satırıyla önerilen ek alanları boş satır olarak gösterir, "+ alan ekle" ile serbest anahtar (AI-BalBal PR-5). (c) **Zorunluluk yok** (T4); `standard_fields_emphasis` yalnızca vurgu. **Sinyal (§4.7.3):** `GET /api/admin/document-type-guide/signals` → `document_review_events` `field_added` olaylarının (aile, anahtar) bazında sayımı — "personel şu türde şu alanı sık ekliyor"; karar insanın (rehbere ekleme admin işi, otomatik değil).

## 4. B-28 akışıyla entegrasyon

| Nokta | Değişiklik |
|---|---|
| AI önerisi (`document_metadata_suggestions.fields`) | + `extra_fields: {key: {value, confidence}}` (rehberli), `tags` yalnızca katalog, `tags.dropped` |
| `POST /submit` | gövde + `extra_fields: {key: value \| null}` (null = kaldır), `tags` katalog doğrulaması; %80 kuralı ek alanlara **anahtar bazında** (`confirmed_fields` içinde `extra_fields.<key>`); olaylar: `field_added` (personelin açtığı anahtar — "personel ekledi", §4.7.3), `field_edited`/`field_confirmed` (öneriden farklı/onaylı), `source: user` damgası |
| `apply` / `PATCH` (admin) | aynı alanlar, aynı doğrulama; onaylı belgede T9 (onay düşer) aynen |
| `review` | değişmez (müdür karar verir; alanları düzenlemez — ayrı karar) |
| `review_status` | değişmez; yayın yalnızca `approved` |
| Kapı | değişmez (ADR-004) |
| `/api/search` | metadata eşleşmesi `tags` ve `extra_fields` değerlerinde de (ILIKE); `SearchDocumentHit`'e `matched_on: title\|tag\|extra_field` (küçük, isteğe bağlı — SORU 5) |
| `/api/ask` prompt | `format_source` başlığına `Muhatap`, `Etiketler`, `Ek alanlar` (yalnızca varsa) — sistem promptu (kurallar) **değişmez**; `make prompt-doc` ANSWER_SYSTEM_PROMPT etkilenmez |
| Şemalar | `DocumentListItem.tags` (zaten detayda), `DocumentDetailResponse.extra_fields`, `MetadataSuggestionApplyRequest.extra_fields`, `DocumentSubmitRequest.extra_fields`, `TagResponse`, `DocumentTypeGuideResponse` |
| Migration `0014` | `extra_fields`, `tag_catalog`, `document_type_guide`, `catalog_events`; veri adımı: katalog ← mevcut etiketler + 9 değişiklik etiketi; rehber başlangıç satırları (10 aile) |
| Seed | `demo_catalog_seed.py` (aynı başlangıç, "varsa dokunma"); ledger belgelerinin `parties`/`key_facts`'ını `extra_fields`'a **yazma** → SORU 2 |

Dokunulmayanlar: kapı, `review_status` makinesi, retrieval sıralaması, sistem promptu kuralları, router, Excel motoru, klasör önerisi.

## 5. Kabul kriterleri

| # | Kriter |
|---|---|
| X-01 | Migration `0014` boş DB'den head'e ve geri; mevcut 74 belge geçerli: 11 etiket katalogda `identity`, 9 değişiklik etiketi `change`; `extra_fields = {}`; rehber 10 aile |
| X-02 | `submit` ile `extra_fields: {"parties": "…", "licence_no": "…"}` yazılır; `GET /{id}` döner; defterde `field_added` (personel), öneriden gelen anahtar için `field_edited`/`field_confirmed`; %80 kuralı `extra_fields.<key>` için 422 `low_confidence_not_confirmed` |
| X-03 | Katalog dışı etiket → 422 `unknown_tag` (submit/apply/PATCH); pasif etiket de reddedilir; aktif etiket geçer |
| X-04 | Admin `/api/admin/tags` POST/PATCH (slug biçimi, çift kayıt 409, pasifleştirme), `/api/tags` herkese aktifler; `catalog_events` satırı; employee 403 |
| X-05 | Admin rehber PATCH (önerilen alan ekleme/çıkarma, pattern), `/api/document-type-guide` herkese; aile eşleştirme birim testi ("Facility Agreement"→contract, "Licence Amendment"→amendment, "Üretim Lisansı"→licence_permit, "Covenant Report"→report, bilinmeyen→other) |
| X-06 | Sınıflandırıcı (FakeLLM): prompt aktif etiket listesini ve seçilen ailenin önerilen anahtarlarını içerir; dönen `extra_fields` 20 sınırı + anahtar normalizasyonu; katalog dışı etiket düşer, `tags.dropped`'a yazılır |
| X-07 | `/api/search?q=<etiket veya ek alan değeri>` belgeyi metadata eşleşmesiyle bulur; yetkisiz belge yine görünmez |
| X-08 | `/api/ask` prompt kaynak başlığında `Etiketler:` / `Ek alanlar:` yalnızca dolu olduğunda; `test_ask` prompt yakalama testi; sistem promptu eşitlik kontrolü (`make lint`) değişmeden yeşil |
| X-09 | Sinyal ucu: iki personelin `contract` ailesinde `parties` eklemesi → `{family: contract, key: parties, count: 2}` |
| X-10 | Regresyon: `make test`, `make lint`, `--retrieval-only` 39/39, `validate-ledger` 0; canlı: `finans` belge yükler → ek alan + katalog etiketi ile submit → `finans_mudur` onaylar → `/api/search` etiketle bulur; **LLM ≤ 2** (bir sınıflandırma, bir `/api/ask` ek alanlı kaynak) |

## 6. SORU (Naci cevaplamalı)

1. **Etiket doğrulaması katı mı?** Önerim **katı** (§4.7.4: "şirketin sabit listesinden"): katalog dışı etiket 422; AI'nın önerdiği katalog dışı etiket düşer ve defterde görünür, admin isterse kataloga ekler. Alternatif: yumuşak (uyarı + kaydet) — listeyi zamanla kirletir.
2. **Demo belgelerinin ledger `parties`/`key_facts`'ı `extra_fields`'a seed'lensin mi?** Önerim **evet, yalnızca `parties`** (gerçek metadata; `key_facts` ledger'ın eval için tuttuğu yol referansıdır, kullanıcıya gösterilecek değer değil). Böylece arama ve prompt'ta "taraflar" hemen çalışır; `make seed` idempotent kalır.
3. **Türe göre zorunlu alan var mı?** Önerim **hayır** (GAPS §4.7.2 "sabit form yok"); yalnızca vurgu (`standard_fields_emphasis`). Evet dersen `submit` 422 `required_field_missing`.
4. **Metadata/ek alanlar retrieval sıralamasına girsin mi?** Önerim **bu turda hayır** — yalnızca `/api/search` ve prompt başlığı; chunk FTS'e metadata eklemek ADR-007 değişikliği, eval ölçümü ister (ayrı tur).
5. **`SearchDocumentHit.matched_on`** küçük alanı eklensin mi (UI "etiketle eşleşti" gösterebilsin)? Önerim evet (tek alan).
6. **Katalog/rehber olayları** için ayrı `catalog_events` tablosu mu, yoksa şimdilik yalnızca log? Önerim tablo (B-08 SORU 2'de "rol/üyelik olayları" için de aynı tablo kullanılabilir → `admin_events(kind, actor, target, before, after)` genel adıyla; iki ihtiyacı tek tabloda kapatır).
7. Etiketsiz düz commit + PHASES.md notu + **ADR-025** (ek alanlar, katalog, rehber — "yapıyı admin yönetir, kuralı kod") — teyit. AI-BalBal tarafı ayrı PR-5 (etiket seçici, ek alan satırları, admin katalog/rehber sayfaları, T-12 onay bekliyor).

## 7. Dosyalar (company-ai)

`alembic/versions/0014_extra_fields_tag_catalog_guide.py` · `models/document.py` (+`extra_fields`) · **yeni** `models/tag_catalog.py`, `models/document_type_guide.py`, `models/admin_event.py` · `repositories/{tag_repo,guide_repo,admin_event_repo}.py` · `services/document_review.py` (ek alan anahtar bazlı %80, `field_added`) · `services/metadata_suggestion.py` (rehber + katalog promptu, `extra_fields`, `tags.dropped`) · `services/type_family.py` (saf eşleştirme) · `services/answer_prompt.py::format_source` (+3 satır; sistem promptu değişmez) · `repositories/document_repo.py::search_metadata` (+tags/extra_fields) · `api/{documents,admin_tags,admin_guide,tags,guide}.py` · `schemas/{document,tag,guide}.py` · `services/demo_catalog_seed.py` + `cli.py` + `entrypoint.sh` · testler (`test_tag_catalog`, `test_type_guide`, `test_extra_fields_review`, `test_metadata_suggestion`, `test_search`, `test_ask`, `test_migrations`) · docs: ADR-025 + ADR-004/024 satırları, DOMAIN_MODEL, SPEC_02 §2/§4, README, NOT (§2 B-28 "kalan çekirdek" → UYGULANDI, Tansu'ya PR-5 to-do), PHASES.md, rapor.

## 8. Uygulama sırası

1. Migration + modeller + seed (katalog, rehber) → `test_migrations`, `test_demo_*`.
2. `type_family` + rehber/katalog repo + admin uçları + herkese okuma uçları → testler (X-04, X-05).
3. `submit`/`apply`/`PATCH`: `extra_fields` + katalog doğrulaması + olaylar + %80 anahtar bazlı → `test_document_review` (X-02, X-03).
4. Sınıflandırıcı: rehber + katalog promptu, `extra_fields`, `tags.dropped` → `test_metadata_suggestion` (X-06).
5. `/api/search` metadata + prompt başlığı → `test_search`, `test_ask` (X-07, X-08); sinyal ucu (X-09).
6. `make test`, `make lint`, `--retrieval-only`, `validate-ledger`; canlı akış (X-10, LLM ≤ 2).
7. Docs + ADR-025 → rapor → commit → çapraz referans → push → dur. AI-BalBal PR-5 ayrı plan.
