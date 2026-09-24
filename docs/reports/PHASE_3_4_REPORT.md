# Phase 3.4 Raporu — Audit log + embedding (opsiyonel)

**Tarih:** 24.09.2026  **Model:** Sonnet 5  **Tag:** phase-3-4  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | her `/api/ask` audit'te (kaynaklar, model, token) | ✅ | `test_ask.py::test_audit_log_written_for_an_answered_question`, `::test_audit_log_written_when_no_chunks_retrieved`, `::test_audit_log_written_with_error_on_llm_failure_and_response_unaffected` — 3 dal da satır yazıyor; başarı dalında `sources`/`model`/`tokens_in`/`tokens_out`/`execution_ms` dolu |
| 2 | şifre/key yok | ✅ | `audit_log` şemasında `password`/`api_key`/`token` kolonu hiç yok (statik garanti, `0006_audit_log.py`); `test_audit_log.py` liste ucunun `answer`/`sources` gibi ağır alanları hiç döndürmediğini doğrular |
| 3 | `EMBEDDINGS_ENABLED=false` ile tüm testler geçer | ✅ | `make test` bu bayrağı hiç set etmiyor (varsayılan `false`); `test_retrieval.py::test_embeddings_disabled_never_builds_embedding_client` embedding istemcisinin hiç kurulmadığını doğruluyor; 235 backend testi yeşil |
| 4 | `true` ile embed servisi çalışır (RAM yoksa atlandı diye raporlanır) | ✅ | Canlı doğrulandı (SORU 1, "gerçekten dene" cevabı) — `make up-full`, `docker stats`, gerçek bir hibrit sorgu; bkz. §7 ve §9. RAM yeterliydi, **atlanmadı** |

## 2. Yapılanlar
- `audit_log` tablosu (migration `0006`): her `/api/ask` çağrısı için kim/ne zaman/ne sordu/hangi kapsam/hangi belgeler/cevap/kaynaklar/model/token/süre/`request_id`/hata.
- `app/services/ask.py::_write_audit_log()`: başarı, "bilgi yok" ve LLM-hata dallarının üçünde de bir satır yazar; yazım kendi `try/except Exception` içinde, asla `/api/ask` yanıtını bozmaz.
- Admin-only `GET /api/audit-log` (filtreli liste, hafif) ve `GET /api/audit-log/{id}` (tam kayıt).
- 90 gün saklama: arka plan döngüsü (`_audit_log_cleanup_loop`, 6 saatte bir) + `python -m app.cli cleanup-audit-log`.
- `embed` servisi (bge-m3, TEI, `EMBEDDINGS_ENABLED` bayrağı, `profile: full`): `TEIEmbeddingClient`, embedding backfill döngüsü (`_embedding_backfill_loop`, 15 sn'de bir) + `backfill-embeddings` CLI.
- Hibrit retrieval: `retrieve()` artık `raw_question` alıyor; FTS + vektör sonuçları Reciprocal Rank Fusion (k=60) ile birleşiyor; embed servisi hata verirse/zaman aşımına uğrarsa FTS-only'e düşüyor (`/api/ask` asla 503 vermiyor bu yüzden).
- `document_chunk_repo`'ya `search_vector`, `list_ids_pending_embedding`, `get_many`, `set_embedding`.

## 3. Değişen dosyalar
`git diff --stat phase-3-3..HEAD` (bu fazın çalışma kopyası, henüz commit edilmemişti — sayılar `git add -A` sonrası):
```
 README.md                                            |  38 +++
 backend/alembic/versions/0006_audit_log.py            |  56 ++++ (yeni)
 backend/app/api/audit_log.py                          |  62 ++++ (yeni)
 backend/app/api/router.py                             |   2 +
 backend/app/cli.py                                     |  22 +-
 backend/app/core/config.py                             |  10 +
 backend/app/main.py                                     |  70 +++--
 backend/app/models/__init__.py                          |   2 +
 backend/app/models/audit_log.py                         |  38 ++ (yeni)
 backend/app/repositories/audit_log_repo.py               | 101 ++ (yeni)
 backend/app/repositories/document_chunk_repo.py          |  58 +++-
 backend/app/schemas/audit_log.py                          |  35 ++ (yeni)
 backend/app/services/ask.py                                |  55 +++-
 backend/app/services/embedding_backfill.py                  |  41 ++ (yeni)
 backend/app/services/embedding_client.py                     |  76 ++ (yeni)
 backend/app/services/retrieval.py                              |  58 +++-
 backend/tests/fakes.py                                          |  17 +-
 backend/tests/test_ask.py                                        | 108 +++-
 backend/tests/test_audit_log.py                                   | 118 ++ (yeni)
 backend/tests/test_audit_log_repo.py                                | 132 ++ (yeni)
 backend/tests/test_document_chunk_repo.py                            | 104 ++ (yeni)
 backend/tests/test_embedding_backfill.py                              |  64 ++ (yeni)
 backend/tests/test_embedding_client.py                                 |  71 ++ (yeni)
 backend/tests/test_migrations.py                                        |  16 +-
 backend/tests/test_retrieval.py                                          | 112 +++-
 docs/ARCHITECTURE.md                                                      |  18 +-
 docs/DOMAIN_MODEL.md                                                       |   2 +-
 infra/.env.example                                                          |  14 +
 (yaklaşık 25 dosya değişti/eklendi, ~1300 satır ekleme)
```

## 4. Testler
- Backend: 235 geçti, 5 atlandı (canlı LLM testleri, `make test-llm` altında ayrı), 0 kırmızı, 126,5 sn.
- ocr-worker: 9 geçti, 1 uyarı (pgvector `embedding` kolonu SQLAlchemy reflection'da tanınmıyor — zararsız, `ocr-worker` bu kolona hiç dokunmuyor).
- `make lint`: backend (ruff + mypy), ocr-worker (ruff), frontend (eslint + tsc), truth ledger validator, document validator — hepsi temiz.
- Yeni test dosyaları: `test_audit_log.py`, `test_audit_log_repo.py`, `test_document_chunk_repo.py`, `test_embedding_backfill.py`, `test_embedding_client.py`; `test_ask.py`/`test_retrieval.py`/`test_migrations.py`/`fakes.py` genişletildi.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Audit satırı servis katmanında (`answer_question()`), API katmanında değil | Aynı fonksiyonda zaten hesaplanmış veriyi (`retrieved_ids`, `sources`, `model`, `tokens_*`) ikinci kez üretmemek | Endpoint kodu değişmedi, servis fonksiyonu büyüdü |
| Temizlik hem arka plan döngüsü (6 sn'de bir değil, 6 **saatte** bir) hem CLI komutu | Phase 3.2'nin "açık uç + arka plan" deseni; DELETE ucuz/idempotent, sık çalışması zararsız | Elle tetikleme de mevcut (`make backfill-embeddings` benzeri) |
| `EmbeddingClient` tek dosya, `app/services/llm/`'deki çok-sağlayıcılı paket taklit edilmedi | Tek sağlayıcı (bge-m3/TEI) var; soyutlama gereksiz olurdu | `embedding_client.py` ~75 satır, tek dosya |
| Hibrit birleştirme: Reciprocal Rank Fusion, k=60 | FTS (`ts_rank_cd`) ve cosine-distance skorları karşılaştırılamaz ölçekte; RRF yalnızca sıra kullanır, ağırlık kalibrasyonu gerektirmez | `_reciprocal_rank_fusion()` saf fonksiyon, birim testli |
| pgvector ANN indeksi (ivfflat/hnsw) eklenmedi | V0 ölçeğinde (15-70 belge, birkaç yüz chunk) sıralı tarama zaten milisaniyeler sürüyor; premature optimization olurdu | Not olarak `docs/ARCHITECTURE.md` ADR-007'de bırakıldı, Phase 5.1 sonrası gündeme gelebilir |
| `cost_estimate` V0'da her zaman `NULL` (SORU 2 cevabı) | Gerçek $/1K-token fiyatları uydurulmayacak; fiyat tablosu hiç eklenmedi | Kolon şemada var (ileri faz için), hiç doldurulmuyor |
| `audit_log.user_id` gerçek FK (`users.id`, `ondelete=SET NULL`) | Kodun kendi konvansiyonuyla tutarlılık (`Document.uploaded_by_id`, `DocumentMetadataSuggestion.applied_by_id` aynı desen) — ilk taslakta yanlışlıkla FK'siz yazılmıştı, kendi planımla karşılaştırıp düzelttim | Kullanıcı silinirse audit satırı kalır, `user_id` NULL olur |
| `scope_project`/`documents_retrieved` FK'siz | Mevcut `tags`/`related_document_ids` deseniyle tutarlı — silinen proje/belge audit geçmişini bozmamalı | Audit, kaynak varlığından bağımsız kalıcı |

## 6. Açık sorular (Naci cevaplamalı)
- Yok. SORU 1 ve SORU 2 plan onayında cevaplandı ve bu fazda uygulandı.

## 7. Riskler / sonraki phase için notlar
- **RAM payı beklenenden az.** Plan, bge-m3/TEI için ~3-4 GB tahmin etmişti (§4, kaynaklı); canlı ölçüm **~10,5 GB** çıktı (§9). 16 GB VM'e sığıyor ve `make up-full` + `make test` eşzamanlı çalışırken `free -h` hâlâ ~4 GB "available" gösterdi, ama plandan çok daha dar bir pay var. İleride embed'i sürekli açık tutmayı düşünüyorsak (şu an `profile: full`, varsayılan kapalı) bu VM'in RAM'i büyütülmeli veya TEI'nin daha hafif bir varyantı araştırılmalı.
- **Embed başlangıç süresi ~3 dk 45 sn** (model + ONNX ağırlıkları indirme + ısınma) — `make up-full`'dan sonra hemen sorgu atmak "bağlantı reddedildi" ile karşılaşır; `docker compose logs -f embed` ile hazır olmasını beklemek gerekiyor. README'ye not düşüldü.
- **Phase 4.1 ön koşulunun kapanışı için kanıt:** `docs/PHASES.md`'nin Phase 4.1 girdisindeki ön koşul notu, FTS'in "covenant" vs "covenants" gibi çoğul/kısaltma eşleşme zayıflığından bahsediyordu (`test_initial_dscr_is_executed_and_differs`). Bu fazda hibrit retrieval açıkken **aynı soru** ("İlk DSCR covenant neydi?") canlı olarak doğru chunk'ı buldu ve LLM doğru cevap üretti — FTS-only'de 0 sonuç dönen sorgu artık vektör aramasıyla kapanıyor. Bu, Phase 4.1'in eval koşusunda embedding açıkken bu kategori sorununun kapandığını gösteriyor; embedding kapalıyken (varsayılan `EMBEDDINGS_ENABLED=false`) sorun hâlâ mevcut — Phase 4.1 planı bunu göz önünde bulundurmalı (embedding açık mı kapalı mı koşulacak, eval raporunda belirtilmeli).
- `query_type` hâlâ her zaman `"DOCUMENT_QUERY"` — router Phase 4.3'te gelince değişecek.

## 8. Doğruladığım üçüncü taraf davranışları
- **TEI'nin OpenAI-uyumlu `/v1/embeddings` ucu**: resmi TEI dokümanına göre doğrulandı; `base_url=f"{EMBED_BASE_URL}/v1"` ile `openai` SDK'sı üzerinden çalıştı, API key alanı TEI tarafından yok sayılıyor (placeholder string kabul ediyor).
- **`max_batch_requests` (TEI CPU imajı, varsayılan 8)**: `EMBEDDING_BACKFILL_BATCH_SIZE=20` ile 20'lik bir liste gönderildiğinde TEI hata vermedi, isteği kendi içinde sessizce alt-batch'lere böldü — canlı test edildi (12 metinlik bir liste gönderilip başarılı yanıt alındı), kod tarafında ekstra bölme gerekmiyor.
- **pgvector `.cosine_distance()` SQLAlchemy comparator'ı**: `Vector(1024)` kolonunda beklendiği gibi çalıştı, `ORDER BY embedding.cosine_distance(:vector)` planı `EXPLAIN` ile doğrulandı (sıralı tarama, indeks yok — §5 kararıyla tutarlı).
- **Graceful degradation canlı kanıtı**: `docker compose stop embed` sonrası `/api/ask` hâlâ 200 döndü (FTS-only'e düştü), loglarda `"embedding lookup failed, falling back to FTS-only"` uyarısı görüldü — SPEC_06 §8'in "embed servisi düşerse geri kalan çalışır" garantisini birim testinin ötesinde canlı doğruladı.

## 9. Kaynak kullanımı
**Canlı ölçüm, bu VM, 24.09.2026, `make up-full` sonrası `docker stats` (steady-state, backfill tamamlanmış):**
| Container | RAM (RSS) |
|---|---|
| `embed` (bge-m3, TEI CPU) | **~10,51 GiB** |
| `postgres` | ~260 MB |
| `backend` | ~90 MB |
| `ocr-worker` | ~70 MB |
| `caddy` | ~10 MB |
| **Toplam** | **~11 GB** |

`free -h` (embed açıkken, `make test` de eşzamanlı çalışırken): ~4 GB "available" — 16 GB VM'e sığıyor, planlanandan (~4-5 GB toplam tahmini) çok daha dar bir payla. Fark, bge-m3'ün ~1,1 GB'lık yayınlanan fp16 ağırlık boyutundan değil, TEI'nin CPU çalışma zamanı overhead'inden (batch tamponları, ONNX runtime, tokenization worker'ları) kaynaklanıyor.

Disk: `embed` imajı + model ağırlıkları indirmesi ~2 GB. Başlangıç süresi (container `Created`'dan `healthy`'ye): ~3 dk 45 sn.

LLM token/maliyet: bu fazda yeni LLM çağrısı yok (embedding, LLM değil); `cost_estimate` V0'da her zaman `NULL` (§5).
