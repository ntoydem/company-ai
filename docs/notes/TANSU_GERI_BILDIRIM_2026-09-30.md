# AI-BalBal taleplerine backend geri bildirimi — 30.09.2026

**Kime:** Ürün sahibi tarafı (`ftansu/AI-BalBal`) ve onun yapay zekası
**Hazırlayan:** Backend tarafı (`ntoydem/company-ai`, Claude Code ile), Naci'nin talebiyle
**İncelenen:** `ftansu/AI-BalBal` @ `b219600` (29.09.2026; `docs/BACKEND_GAPS.md` v7.9, `docs/BAGLANTI_YOL_HARITASI.md` 28.09.2026, `frontend/src/**`) ↔ `ntoydem/company-ai` @ `4301968` (Phase 5.4b)
**İncelenen sürüm donduruldu (30.09.2026, Naci'nin kararı):** `BACKEND_GAPS.md` v7.9, commit `b219600`, 29.09.2026 tarihli — bu nottaki tüm B-N/P-N/§N atıfları bu sürümedir. Bundan sonraki `BACKEND_GAPS.md` güncellemeleri bu notta **otomatik takip edilmeyecek**; ayrı bir inceleme turunda ele alınır (bkz. §7.1).
**Esas alınan çerçeve:** `CLAUDE.md` altı değişmez kural (1 SECURITY, 2 SOURCE GROUNDING, 3 CALCULATION, 4 AUDITABILITY, 5 TEMPORAL TRUTH, 6 NO OPINION), `docs/ARCHITECTURE.md` ADR-001…ADR-021, `docs/SPEC_06` §6 ağ kuralı, backend'in bugünkü uçları (28 uç, aşağıda §4.3).

Bu not karar gerekçeli bir sınıflandırmadır; kod içermez. Backend'de değişiklik yapılmadı. AI-BalBal çalıştırılmadı; "çalışıyor" ifadeleri kod okumasına dayanır, çalıştırma kanıtı değildir. Backend tarafı, ürün sahibinin BACKEND_GAPS §1.7.1 soru kuralını kabul eder: aşağıdaki her "karar gerekiyor" satırı bir sorudur, tahminle uygulanmayacaktır.

Kısaltmalar: **kural N** = `CLAUDE.md`'deki N numaralı değişmez kural. **ADR-N** = `docs/ARCHITECTURE.md`. **B-N / P-N / §N** = `BACKEND_GAPS.md`. Satır numaraları o dosyanın 29.09.2026 halidir.

---

## 0. Güncelleme — Tansu'nun cevapları (30.09.2026, Word yorumları, özet)

Tansu notun sade özetine on cevap verdi. Aşağıdaki tablo her cevabın bu nottaki karşılığını ve yeni durumunu gösterir; ayrıntı ilgili bölümde **Durum (30.09)** satırlarındadır. Cevaplar özet halinde alındı; tam metin gerekirse Naci'den istenir.

| # | Tansu'nun cevabı (özet) | Etkilenen madde | Durum |
|---|---|---|---|
| 1 | "Beğendim / yanlış" geri bildirim butonları **reddedildi**. Yerine üç bildirim türü: **veri eksikliği**, **veri uyuşmazlığı** (departmanlar arası çelişki → "diğer departmandan veri/bilgi talep et" butonu), **yetkilendirme uyarısı** (talep ürün sınırını aşıyorsa). | B-04, B-11, B-25 | **DEĞİŞTİ** — §1 B-04 satırı yeniden yazıldı; §5.3 |
| 2 | "Şirketteki tüm yetkilendirmeleri müşteri kendi yönetim arayüzünden belirler; Balbal yalnızca gerekli araçları sağlar." | B-08, B-20, B-26, B-28, ADR-004 Phase 1.2 notu | **YENİ TASARIM KARARI** — §5.1 |
| 3 | Sohbet geçmişi ertelemesi onaylandı ("şimdilik gerek yok"). | B-03 | **ERTELENDİ** — §2 B-03 |
| 4 | İzin/yazışma belgelerinde bireysel erişim: "kendisi görecek, İK herkesi görecek." | B-22/3, B-23/2 | **NETLEŞTİ** — §2 B-22, §5.1 |
| 5 | Belge onayı: "Yönetici kendi belgesini eklerse onay gerekmez; personel eklerse kendi onayı + departman yetkilisinden 2. onay." | B-28, Phase 3.2 SORU 2 | **YENİ TASARIM KARARI** — §5.2; §3.3 güncellendi |
| 6 | Yükleme yetki açığı "öncelikli giderilmeli". | §2 B-26/3 ara düzeltme | **KAPANDI** — bağımsız güvenlik yaması olarak uygulandı, `docs/PHASES.md` Adım 5 notuna bakınız |
| 7 | "Şimdilik Ürün 2'den başlayacak. Ürün 1 yalnızca veri yükleyecek, yüklenen veriyi bulup bilgilendirecek." DuckDB/Excel hesabı Ürün 2. | B-25, §3.1, eval seti, örnek sorular | **NETLEŞTİ** — §6 |
| 8 | İnternet/HTTPS: "Şimdilik web'de görüntülenecek, detaylar ileride şekillenecek." | B-27, §3.2 | **KAPANDI (30.09.2026)** — VPN/Tailscale; Tansu'ya Tailscale ile erişim verildi, bkz. §6.6 |
| 9 | Kural 3'ün ("LLM hesap yapmaz") BACKEND_GAPS'a P-11 olarak eklenmesi onaylandı ("Ürün 1 için uygun"). | §3.9 | **KABUL** — ekleme ürün sahibi tarafının reposunda yapılır; backend dokunmaz |
| 10 | Çelişki önceliği: "Anayasaya (`CLAUDE.md`/kurallar) eklenecek, GitHub üzerinden çözüm aranacak, çözülmezse Tansu ve Naci karar verir. Frontend'in talebi backend'in kabiliyetlerini karşılamalı ve anayasa içinde olmalı." | Eski karar listesi #11 | **NETLEŞTİ** — öncelik `CLAUDE.md` ve ADR'lerde; BACKEND_GAPS §1.6'nın "bağlayıcı çerçeve" ifadesi buna göre okunur |
| — | **company-ai `frontend/`'in kaderi** (§4.4'te "Naci'nin kararı, notun dışında" denilen açık soru). Naci: AI-BalBal, Naci ve Tansu'nun projesinin tek, asıl frontend'i olacak; `company-ai/frontend/` **emekli edilir**. | §4.4, B-19 | **KAPANDI (30.09.2026, Naci)** — company-ai `frontend/` **silinmez**, repoda kalır, yalnızca artık geliştirilmez; AI-BalBal asıl arayüz. Backend (FastAPI, yetki, retrieval, Excel motoru, router) değişmeden AI-BalBal'ın istemci katmanı olmaya devam eder. Ayrıntı §4.4 (güncellendi). |

---

## 1. Benimseyeceğimiz talepler ve yöntemi

Bu maddeler mevcut kurallarla ve ADR'lerle çelişmiyor; her biri var olan bir deseni genişletir. Sıra, `BACKEND_GAPS` §12 ile uyumludur; bağımlılığı olanlar belirtilmiştir.

| Kod | Talep | Yöntem (hangi mevcut kod / desen genişletilir) | Bağımlılık |
|---|---|---|---|
| **B-04** — **DEĞİŞTİ (Tansu #1)** | ~~`audit_log_id` + `POST /api/ask/feedback` (beğendim/yanlış)~~ → cevaba bağlı **üç bildirim türü**: `missing_data`, `data_conflict`, `product_limit` | Geri bildirim ucu ve `rating` sütunu **yazılmaz**; `audit_log_id` alanına da ihtiyaç kalmadı. Yerine `AskResponse.warnings: [{kind, message, action?}]` alanı: (a) **`missing_data`** = bugünkü `answered=false` sabit metninin (ADR-014) yapılandırılmış hali, ek iş yok; (b) **`data_conflict`** = kullanıcının **görebildiği** kaynaklar arasında aynı olgu için farklı değer bulunduğunda; cevap iki değeri de kaynağıyla aktarır, hangisinin doğru olduğunu **söylemez** (kural 6), `action: request_data` ile B-11 evrak/bilgi talebi butonuna bağlanır; (c) **`product_limit`** = router'ın seçtiği dal kapalı üründeyse (§6). Uygulama notları §5.3'te. Denetim kaydı (ADR-016) her uyarıyı `sources`/`answer` gibi satırda saklar; retrieval'a girmez. | (b) için prompt fazı, (c) için B-25 |
| **B-07** | `SourceCard`'a `supersedes_document_id` / `superseded_by_document_id` | `services/ask.py` kaynak kartını `load_with_chains` ile yüklenen zincirden kuruyor; ADR-021'e göre zincir **her halkada** `allowed_document_ids` ile kısıtlı yüklenir, görünmeyen komşu hiç yüklenmez. Dolayısıyla id'yi eklemek yetki kontrolünü kendiliğinden taşır: yüklenmemiş komşu → `None`. `schemas/ask.py:31-46`'ya iki alan; `SourceCardList.tsx:38-43`'teki uyarı linke dönüşür. | Yok |
| **B-09** | `users.primary_department_id`, `/me` ve `/login`'de `primary_department_slug` | Migration: sütun + mevcut kullanıcılar için ilk üyelikten backfill. `schemas/auth.py::CurrentUserResponse`'a alan. `api/users.py` create/update'te "ana departman üyeliklerden biri olmalı, management/admin için boş olabilir" doğrulaması. ADR-003 concretization notu. Frontend `Home.tsx:33`, `BalbalChat.tsx:32`, `ShellContext.tsx:19`'daki `department_slugs[0]` varsayımı kalkar. | Yok |
| **B-13** | `file_kind` alanı | `documents.file_name` (migration 0008, ADR-011) ve `storage_path` uzantısı zaten var; `DocumentListItem`/`DocumentDetailResponse`'a türetilmiş `file_kind: pdf\|image\|xlsx\|xlsm\|csv` eklenir, migration gerekmez. `WorkbookInspectCard.tsx:7`'nin her belge için attığı 422 çağrısı kalkar. | Yok |
| **B-17** | İndirme adı belge başlığı + uzantı; `?inline=1` | `api/documents.py:253` `FileResponse(path, filename=path.name)` → `filename=f"{title}.{ext}"`, Starlette `FileResponse`'un `content_disposition_type` parametresiyle `inline`/`attachment` seçimi. Başlıktaki dosya-sistemi-güvensiz karakterler temizlenir. | Yok |
| **B-05** | `users.title`; `GET /api/directory?q=&department=` | Migration: `users.title` (nullable). Yeni uç `api/departments.py` deseniyle (her kimlikli kullanıcı, `get_current_user`), dar şema: `id, display_name, title, department_slug, department_name`. `password_hash`, rol, aktiflik dönmez. `users.manager_id` (§2.3) aynı migration'da eklenebilir, kullanımı B-22'ye kalır. | Yok |
| **B-14** | `GET /api/search?q=` içerik araması | `services/search_query.build_search_query` (ADR-020, sözlük genişletmeli OR sorgusu) + `retrieval.py`'nin FTS bacağı zaten var; `allowed_document_ids` önce (ADR-004). Dönüş: belge + `snippet` + `page_number` (chunk'tan), proje eşleşmesi. `people` kısmı B-05'e bağlı. `SearchPanel.tsx:22-24`'teki istemci tarafı başlık süzmesi yerini alır. | B-05 (people için) |
| **B-20/6** | Tek sohbette çok proje; `project_id` zorunlu değil | Backend'de `AskRequest.project_id` zaten opsiyonel (`schemas/ask.py:28`); değişiklik gerekmez. Ek olarak `SourceCard`'a `project_code`/`project_name` eklenir ki arayüz projeyi `/api/documents` listesinden türetmek zorunda kalmasın (`AskPanel.tsx:21-24`, `BalbalChat.tsx:35-38`). **Uyarı:** proje ayrımı bugün retrieval'da `project_id` filtresi + prompt disipliniyle sağlanıyor (ADR-020/021); filtre kaldırılınca `isolation` eval kategorisi (bugün %75, bilinen sınırlama) daha da zorlanır. Kaldırma kararı eval ile birlikte alınır. Frontend'in kendi içinde tutarsızlık: `AskPanel.tsx:16,31,46-58` hâlâ proje çipi gösterip `project_id` gönderiyor, yalnızca `BalbalChat` göndermiyor. | Yok |
| **B-11** — **kapsamı büyüdü (Tansu #1)** | Evrak/bilgi talebi, varlık ele vermeden; artık `data_conflict` ve `missing_data` uyarılarının "diğer departmandan veri/bilgi talep et" butonunun hedefi | Bugünkü "bilgi bulamadım" sabit metni (ADR-014, ADR-021: chunk yoksa LLM çağrılmadan döner) zaten belge varlığını ele vermez; bu kısım yapılmış durumda. Yeni: `document_requests(id, from_user_id, to_department_id, description, status, source_audit_log_id?)` tablosu + `POST /api/document-requests`; departmanı kullanıcı seçer (Balbal önermez, P-2). Talebin hangi cevaptan doğduğu, denetim kaydı satırına referansla saklanabilir (kural 4); bu, reddedilen `audit_log_id`'nin tek meşru kullanımı olur ve yalnızca sunucu tarafında kalır. Hedef departmanın görmesi B-01 gündemine bağlı. | B-01 |
| **B-01** (ilk kısım) | Gündem: süresi dolacak belgeler | Deterministik SQL: `documents.expiration_date` 60 gün içinde ve `allowed_document_ids` içinde. LLM yok. `GET /api/me/agenda` döner `kind: deadline`. "Onay bekleyen öneri" kalemi B-28 kararına, diğer kalemler B-06a/B-11/B-22/B-23'e bağlı. Ürün 2 kapısı B-25'e bağlı. | B-25 (kapı için) |
| **B-19** | Arayüz incelemesi + tersine liste | Bu not. Tersine liste §4.3'te. | — |
| **B-27** (yalnızca "AI-BalBal'ı sun" kısmı) | Caddy'nin `ftansu/AI-BalBal/frontend` build'ini sunması, tek komutla güncelleme | `infra/caddy/Dockerfile` bugün `./frontend` bağlamından build alıyor (ADR-018). Build bağlamını bir `FRONTEND_DIR` değişkeniyle seçilebilir yapmak ve `make update-frontend` (git pull + build + `up -d caddy`) eklemek küçük iş. Bu kısım LAN'da düz HTTP ile bugün yapılabilir. Erişim yolu artık netleşti (§3.2, §6.6): VPN/Tailscale, internete açık HTTPS değil — Tansu'ya Tailscale ile erişim verildi. | Yok |
| **B-18** (yöntem olarak) | Demo veri seti genişletme, 15 kişilik personel, kurgu şirket | Mevcut üretim hattı genişletilir: ledger (`seed_data/master/*.yaml`) → `make prose` (LLM bir kez, `[[token]]` ile, rakam görmez) → `generate_documents.py` (deterministik) → `validate_documents.py` → `manifest.json` → `make seed` (ADR-013). Personel listesi ledger'a `personnel` bölümü olarak girer; `demo_users_seed.py` ve `demo_departments_seed.py` ledger'dan okur. Excel seti `generate_excel.py` + LibreOffice recalc hattıyla (ADR-011). **Şirket adı:** ledger'daki "ABC Enerji A.Ş." `USER_FACT` olarak onaylı (Phase 2.1, 23.09.2026); canvas'taki "NATA" ledger'a uydurulur, tersi değil. Her yeni rakam/tarih/isim `AI_ASSUMPTION` etiketiyle girer ve Naci onayı bekler; bu kural ürün sahibinin de kabul ettiği P-9 ile aynı yöndedir. | B-20 (İK belgeleri için) |

Bu tablodaki maddeler için ADR gerekmez; B-07, B-09, B-13, B-17, B-05 ve B-04'ün `missing_data`/`product_limit` kısımları tek bir küçük phase'e sığar ("Balbal cevap döngüsü"; B-25'in `product_level` eşlemesi §6 ile artık yazılabilir). Yükleme yetki açığının ara düzeltmesi (§2 B-26/3, Tansu #6 "öncelikli") **30.09.2026'da bağımsız bir güvenlik yaması olarak zaten uygulandı** (`docs/PHASES.md` Adım 5 notu) — ayrı bir faza gerek kalmadı. Naci'nin faz planı onayı gerekir; bu not onun yerine geçmez.

---

## 2. Uyarlayarak benimseyeceklerimiz

Talebin özü kabul; şu noktalar değişmeden uygulanamaz.

### B-25 mekanizması — ürün anahtarı — **NETLEŞTİ (Tansu #7, ayrıntı §6)**
- **Kabul:** `company_settings.enabled_products` (tek satır, `text[]`, değerler `P1|P2|P3`), `require_product("P2")` FastAPI bağımlılığı (`require_admin` deseni, `api/deps.py:38`), `enabled_products` hem `/me` hem `/login` cevabında, `set-enabled-products` CLI komutu. Alan adı ve değerler `frontend/src/api/products.ts` ile birebir.
- **Durum (30.09):** "Bugün her cevap P1" varsayımı düştü; eşleme §6'da: `DOCUMENT_QUERY → P1`, `DATA_QUERY`/`MIXED_QUERY → P2`. `product_level` artık yazılabilir. **Tansu #2** gereği `enabled_products`'ı müşteri kendi yönetim arayüzünden değiştirebilmeli → CLI'ya ek olarak admin ucu (`PATCH /api/admin/settings`) ve Yönetim panelinde bir sekme; bu, BAGLANTI §2.1/5'in "admin arayüzü şimdilik gerekmez" notunu geçersiz kılar.

### B-20 (1–5) — departman yapısı — **etkilendi (Tansu #2, bkz. §5.1)**
- **Kabul:** Görünen ad değişiklikleri, İK ve Üretim/Piyasa, Mali İşler alt birimleri, `finans` üyelik düzeltmesi. Slug'lar sabit (BAGLANTI §3.1 önerisi doğru).
- **Durum (30.09):** Tansu #2 ("yetkilendirmeyi müşteri arayüzden belirler") departman ağacını **veri** yapar: demo yapısı seed/migration ile gelir. **Düzeltildi (30.09.2026, Naci):** departmanı ekleyip düzenleyen **müşteri değil**, platform yöneticileridir (Platform Yetkilendirmesi, §5.1, §8). Phase 1.2'nin "departmanlar seed-only, CRUD yok" kararı büyük ölçüde korunur; backend tarafı platform-içi bir CRUD mekanizması kurabilir (proje CRUD deseni, `require_admin`) ama bunu müşteri admin arayüzüne açmaz. Bunun Anayasa v1.1 O-10 ile çelişkisi §8'de, karar Tansu'nun/Proje Yetkililerinin.
- **Değişmesi gereken:** Üç yer birlikte değişmek zorunda: Alembic **veri** migration'ı (seed "varsa dokunma" davranışlı, `demo_departments_seed.py:49`), seed dosyası ve ledger (`seed_data/master/company.yaml` departmanları slug olarak taşır, ADR-013; `validate_ledger` slug'ları denetler). BAGLANTI ilk ikisini görmüş, ledger'ı görmemiş. Ayrıca `search_glossary.py`'de departman adı geçen bir sözlük satırı yok, o tarafta iş çıkmaz. `README.md`'deki demo hesap tablosu güncellenir.

### B-08 — departman yöneticisi rolü — **önceliği yükseldi (Tansu #2 ve #5, bkz. §5)**
- **Kabul:** Kural yalnızca `allowed_document_ids` içinde (P-2 = ADR-004). Önerilen iki seçenekten **rol** (`UserRole.department_manager`) tercih edilir: `user_departments.max_confidentiality` alternatifi, gizlilik kararını üyelik satırına dağıtır ve `SingleDocumentIdsProvider` (`authorization.py:84-110`) ile "kim görebilir" ucunu ikinci bir kural kaynağına bağlar.
- **Değişmesi gereken:** `user_role` Postgres enum'una değer eklemek migration ister; `ROLE_LABELS`/`ROLE_VALUES` (frontend `lib/format.ts`) ve `UserForm` ürün sahibi tarafında güncellenir. ADR-004'e concretization satırı. "Departman müdürü kendi departmanının `restricted` belgelerini görür, `board` görmez" varsayımı ürün sahibince teyit edilmeli; §2.4 yalnızca `restricted` diyor.
- **Durum (30.09):** İki yeni karar bu rolü ön koşul yapıyor: iki aşamalı belge onayında "departman yetkilisi" ikinci onaycıdır (§5.2) ve rolün kime verileceğini müşteri admin arayüzünden belirler (§5.1; `PATCH /api/users/{id}` zaten `role` alıyor, yalnızca enum genişler). Sıra: B-08, B-28'den **önce** gelir. **KAPANDI (30.09.2026, Naci):** İkinci onaycı (ve onaysız yükleyici) hedef **departmanın kendi `department_manager`'ı**'dır — genel `management` rolü ya da sistem `admin`'i değil (bkz. §5.2). Naci: "Finans departmanına yüklenen bir belgeyi Finans departmanının yetkilisi onaylar, sistem admin'i değil."

### B-26 — klasörler ve departman erişim yetkileri
- **Kabul:** `folders`, `folder_grants`, `documents.folder_id`; yetki yalnızca gate içinde; her belge tek klasörde ve belgenin `department`'ı klasörün sahibi departmanı (ADR-004'ün "yetki departmandan gelir" ilkesi korunur); yetki kaldırılınca anında geçerli (gate her istekte hesaplanır, ek iş yok); `SingleDocumentIdsProvider` aynı kuralı taşıdığı için "kim görebilir" ucu tutarlı kalır.
- **Değişmesi gereken:**
  1. `DocumentIdsProvider` protokolüne Phase 1.2'deki gibi bir metot eklenir (`list_document_ids_for_folder_grants(department_slugs, confidentiality_levels)`); `allowed_document_ids`'in `employee` dalı üyelik ∪ klasör-grant birleşimini alır. Bu bir **ADR** ister (ADR-004'ün superseding değil, concretization'ı; imza değişmez).
  2. Yetki değişikliği geçmişi (`§2.6.1/8`) `audit_log`'a **yazılmaz**; o tablo soru-cevap kaydıdır (ADR-016, satır başına bir `/api/ask`). Ayrı `folder_grant_events` tablosu; `GET /api/admin/folders/audit` oradan okur.
  3. `POST /api/documents/upload` `folder_id` alır ve `write` yetkisi yoksa 403 döner. Bu, bugün her iki repoda da bulunan **yazma tarafı yetki boşluğunu** kapatır: `api/documents.py:113` yüklemeyi her kimlikli kullanıcıya açıyor, `:137-138` departman slug'ını yalnızca "var mı" diye kontrol ediyor; Enerji çalışanı `department=finans` ile belge yükleyebilir ve o belge Finans kullanıcılarının Balbal cevaplarına kaynak olur. Kural 1 okumayı korur, yazmayı korumaz. B-26 gelene kadar ara düzeltme olarak "yüklenen belgenin departmanı ⊆ yükleyenin üyelikleri (management/admin hariç)" kuralı önerilir; kararı Naci verir.
  4. `documents.department` FK'sız serbest string (ADR-004 Phase 1.2 notu) klasör sahibiyle çift kaynak olur; ADR'de "klasörün `owner_department`'ı belirleyici, `documents.department` ondan türetilir" yazılmalı.
- **Durum (30.09):** Tansu #6 ile 3. madde (yükleme yetki açığı) **öncelikli**: B-26 beklenmeden ara düzeltme yapıldı, **kapandı** (bkz. §7.1 satır 4). Tansu #2 ile klasör yetkilerinin admin arayüzünden yönetilmesi (zaten B-26'nın tasarımı) teyit edildi; §5.1.

### B-03 — sohbet geçmişi ve çok turlu soru — **ERTELENDİ (Tansu #3)**
- **Durum (30.09):** "Şimdilik gerek yok." Backend'de iş yok; frontend'in bellek-içi geçmişi (`components/balbal/sessions.tsx`) kalır. Aşağıdaki notlar ileride açıldığında geçerlidir.
- **Kabul (ileride):** `ask_conversations` / `ask_turns` ayrı tablolar, kullanıcıya özel, 90 gün, retrieval'a girmez (ADR-016 ile aynı disiplin; temizlik döngüsü paylaşılır). Her turda retrieval yeniden `allowed_document_ids` üzerinden.
- **Değişmesi gereken (ileride):** "Önceki turun sorusu sınıflandırıcıya bağlam olarak verilir" (§3.2) router prompt'unu değiştirir (`services/router.py`, kopyası `docs/prompts/ROUTER_PROMPTS.md`, `make lint` eşitliğini denetler). Phase 5.1b'de Naci prompt ayarını bilinçli olarak dondurdu (isolation/temporal bilinen sınırlama kararı, 26.09.2026); bu değişiklik ayrı bir prompt fazında, `--repeat 3` ölçümüyle yapılır. B-22'nin sohbet içi eksik-bilgi sorma akışı (§8.1.1/2) bu altyapıya bağlıdır; B-03 ertelenince B-22'nin o kısmı da ertelenmiş olur.

### B-02 — bildirimler
- **Kabul:** `notifications` tablosu, 60 sn polling, push yok.
- **Değişmesi gereken:** Olay kaynaklarının çoğu henüz var olmayan modüllere bağlı (görüş talebi, işlem, yazışma). Bugün üretilebilen iki olay: "departmanıma belge yüklendi" ve "belgenin yeni versiyonu geldi" (`document_repo.mark_superseded`). "Departmana yüklendi" olayında alıcı kümesi tanımsız: departmanın tüm üyeleri mi, yalnızca yöneticisi mi (B-08)? Karar gerekiyor. Bildirim satırı `document_id` taşıyorsa okunurken de `allowed_document_ids` süzgecinden geçmeli (P-2); yazma anındaki yetki yeterli değil, yetki sonradan kalkabilir.

### B-06a — departmanlar arası görüş talebi
- **Kabul:** Ürün 2; talep + cevap kurumsal hafızaya girer (CLAUDE.md "bilinçli eklenen notlar" tanımıyla uyumlu); Balbal yalnızca cevap taslağı önerir, gönderen insandır (P-1, kural 6).
- **Değişmesi gereken:** "Hafızaya girer" tek bir yolla olabilir: talep+cevap çifti bir **belge** olarak ingestion hattına girer (`document_repo.create_with_job` veya metin için doğrudan `document_pages`), böylece `allowed_document_ids`, sayfa bazlı kaynak (ADR-008) ve versiyon alanları otomatik uygulanır. İkinci bir hafıza tablosu açılmaz. Belgenin `department`'ı (isteyen mi, cevaplayan mı) ve gizliliği karar ister. Sohbet uçlarıyla (`/api/chats`, `kind: opinion_request`) birleştirilmesi B-06b'nin ertelenmesiyle çelişir; görüş talebi için ayrı, dar `opinion_requests` uçları önerilir.

### B-22 — işlem talebi iskeleti ve izin formu (ADR ÖNCE)
- **Kabul:** Durum makinesi kodda, LLM hiçbir geçişi tetiklemez (kural 3 ve 6 ile uyumlu); iş günü ve dönüş tarihi backend'de (§8.1.2 satır 837, kural 3 ile uyumlu); talepler retrieval'a girmez (ADR-016 disiplini); P-1'in dört testi.
- **Değişmesi gereken:**
  1. Niyet ayrımı (§3.5) router'a yeni bir tür ekler (`ACTION`); ADR-010'un "her hata DOCUMENT'a düşer" güvenli yönü korunmalı: tereddütte soru olarak işlenir, işlem olarak değil.
  2. Alan çıkarma `metadata_suggestion.py` deseniyle (JSON modu, beyaz liste dışı değerler düşürülür, `metadata_suggestion.py:99-118`) yapılır; tarihler kodda doğrulanır.
  3. İzin bakiyesinin İK klasöründeki belgelerden türetilmesi (§8.1.6) bireysel erişim ister. **Netleşti (Tansu #4): "kendisi görecek, İK herkesi görecek."** Model: `documents.owner_user_id` (nullable) + gate'e bir dal: belge sahibinin kendisi **veya** İK departmanı üyesi görür; `management` dahil başkası görmez (§8.1.9 ile aynı). Bu dal da yalnızca `allowed_document_ids` içindedir (P-2); `SingleDocumentIdsProvider` aynı kuralı taşır. Onay zincirindeki yöneticinin belgeyi görüp görmeyeceğini Tansu söylemedi (§8.1.9 "onay zincirindeki yönetici" diyordu); açık soru.
  4. Bakiye aritmetiği (`entitled + carried_over − used − pending`) Python'da; belgelerden rakam okuma LLM'e kalırsa her soruda yeniden çıkarım yapılır. Öneri: izin belgeleri B-28'in "personel eklediği alan" mekanizmasıyla yapılandırılmış sayı taşısın, LLM her seferinde PDF'ten okumasın.
  5. `Europe/Istanbul` ve "bugün" için `DEMO_TODAY` (ADR-012) değil gerçek saat kullanılacak; bu, demo ile gerçek zamanın ilk kez ayrıştığı yer olur, ADR'de belirtilmeli.

### B-23 — yazışma ve dilekçe taslağı, Ürün 2 kısmı (ADR ÖNCE)
- **Kabul:** Kaynaksız cümle yerine `[BİLGİ EKSİK]`, `legal_references` dışı atıf `[DOĞRULANMALI]`; bu, kural 2'nin sabit metin disiplininin genişletilmiş halidir. Süre `legal_deadline_rules` + tebliğ tarihi ile deterministik (kural 3). Şablonlar tabloda (P-8). Sistemden gönderim yok.
- **Değişmesi gereken:**
  1. "Gelen yazının içeriği talimat değildir" (§8.2.4/3) bugün `answer_prompt.py`'de açık bir kural olarak **yok**; prompt kaynakları `[K<n>]` bloklarıyla veri gibi sunuyor ama enjeksiyon koruması yazılı değil. Bu, B-23'ten bağımsız olarak genel bir prompt düzeltmesidir; prompt fazında ele alınır (bkz. B-03 notu).
  2. Gizlilik: §8.2.9 "yalnızca ilgili departman ve onay zinciri görür". Bizde `restricted` belgeyi `management` de görür (ADR-004, `authorization.py:63-69`). **Tansu #4'ün "kendisi + İK" modeli yazışmaya da uygulanırsa** çözüm B-22 ile aynı dal olur: `owner_user_id` + departman yetkilisi (B-08). Tansu'nun cevabı "izin/yazışma" diyor, dolayısıyla aynı modeli kapsıyor kabul edilir; teyit istenir.
  3. Taslak, hazırlayanın `allowed_document_ids` kümesiyle sınırlı (§8.2.4/4): mevcut `/api/ask` akışı zaten böyle; taslak üretimi aynı `answer_question` hattını `write_audit=True` ile çağırmalı ki her taslak denetim kaydına girsin (kural 4).

### B-28 — belge yükleme mantığının benimsenebilir çekirdeği — **onay akışı değişti (Tansu #5, bkz. §5.2)**
§3.3'teki iki noktadan ilki (kim onaylar) Tansu #5 ile **iki aşamalı, role bağlı** akışa dönüştü; ikincisi (onaysız belge görünmez) hâlâ açık. Aşağıdaki çekirdek, bu iki karara göre uyarlanarak alınır:
- **Kayıt defteri:** `document_metadata_suggestions` tek satırlı ve üzerine yazılan bir tablo (`models/document_metadata_suggestion.py:21-23`, ADR-006 "V0'da öneri geçmişi yok"). B-28 §4.7.6 değiştirilemez, çok satırlı kayıt ister. Mevcut tablo korunur (öneri durumu), yanına yalnızca ekleme yapılan `document_intake_events(document_id, actor, kind: suggested|edited|added|approved, field, before, after, confidence, created_at)` tablosu gelir. `audit_log`'a yazılmaz (ADR-016).
- **%80 eşiği sunucuda:** `metadata_suggestion.py` güveni zaten 0–1 aralığında üretiyor (`:58`); `apply` ucu, `confidence < threshold` olan alanı gövdede açık `confirmed: true` olmadan reddeder. Eşik `Settings` parametresi (P-8; `.env.example`'a girer).
- **Belge türüne göre değişen alan seti:** Bugün sabit 9 alan (`metadata_suggestion.py:43`). Tür bazlı "hangi alanlar önemli" rehberi bir tablo olur (P-8), prompt rehberi okur; dönen JSON şeması genişler ama beyaz liste doğrulaması korunur.
- **Personelin eklediği alan:** `documents.tags` (ARRAY) ve yeni bir `documents.extra_fields JSONB` (ad → değer, `added_by`). Retrieval FTS'e bu alanlar eklenirse aranabilir olur (ADR-007); prompt'a metadata olarak girer.
- **Değişiklik etiketleri sabit listeden:** `tags` serbest string; sabit liste `tag_catalog` tablosu + doğrulama. Liste büyümesi admin işlemi.
- **Klasör önerisi:** B-26'ya bağlı.

### B-20/7 — Enerji izin/ruhsat adımları (Ürün 3 veri modeli)
- **Kabul (ileride):** `permit_steps`, `project_permit_status`, `GET /api/projects/{id}/permits`; yasal süreler parametre tablosunda (P-8). LLM yok, deterministik; kural 6 ile çelişmez.
- **Değişmesi gereken:** Adım verisi ledger'dan gelmeli (ADR-013: her tarih ledger'da); `izmir_res.yaml` zaten başvuru/karar olaylarını `Event{date, doc, tag}` olarak taşıyor, tablo bunlardan seed edilir. Kurum yazısının adıma bağlanması B-23'e bağlı. Şimdilik ADR taslağı, kod yok (§12 sıra 7).

### B-06b — Balbal'ın grup sohbetine katılması (Ürün 2 sonrası)
- **Kabul (ileride):** "Sohbetteki tüm üyelerin ortak görebildiği belgeler" kuralı ADR-004 ile uyumludur ve yeni bir yetki yolu açmadan uygulanabilir: her üye için `allowed_document_ids` çağrılır, kümelerin kesişimi alınır, retrieval o kümeyle çalışır. Tek gate korunur.
- **Değişmesi gereken:** Kesişim boşsa Balbal sabit "bulamadım" der (ADR-014); "kimin yetkisi dar" bilgisi hiçbir üyeye söylenmez (P-2). Bunların testi B-06b ADR'sine girer. Sıra: Ürün 2 tamamlandıktan sonra (ürün sahibinin kararı).

---

## 3. Benimsemeyeceğimiz talepler ve nedeni

"Benimsemiyoruz" = **mevcut haliyle**. Her maddede hangi kural/ADR'nin engellediği ve hangi kararla açılabileceği yazılıdır. Bunlar ürün sahibine sorudur, ret değildir.

### 3.1 B-25 katman sınıflandırması: "bugünkü her cevap Ürün 1" — **NETLEŞTİ (Tansu #7), artık §2/§6'da**
- **Durum (30.09):** Tansu: "Ürün 1 yalnızca veri yükleyecek, yüklenen veriyi bulup bilgilendirecek; DuckDB/Excel hesabı Ürün 2." Çelişki kalktı; sonuçları §6'da. Aşağıdaki metin kararın gerekçesi olarak korunuyor.
- **Talep:** BAGLANTI §2.1/4: `AskResponse.product_level` bugün hep `"P1"` döner; BACKEND_GAPS §1.5.1: Ürün 1'de "Hesaplama: **Yok**", Ürün 2'de "yalnızca aritmetik, yalnızca gerçekleşmiş veriyle".
- **Çelişki:** Backend'in `DATA_QUERY` ve `MIXED_QUERY` cevapları DuckDB ile hesap yapar (ADR-010, ADR-011; `services/excel_ask.py`, `dscr`, `outstanding_debt`, `budget_variance`, `capacity_factor`, `production` fonksiyonları). Ürün sahibinin tablosuna göre bu Ürün 2 yeteneğidir. İkisi aynı anda doğru olamaz: ya bu cevaplar `P2` etiketlenir ve yalnızca-P1 müşteride `require_product("P2")` ile kapanır, ya da §1.5.1 tablosu "Ürün 1: kesin veriyle aritmetik dahil" diye düzeltilir. Arayüzdeki örnek sorular (`strings.ts:49` "Ankara RES 2026 Q2 DSCR kaç?") ve eval setinin `data`/`mixed` kategorileri (`questions.json`) bu karara bağlı.
- **Ek belirsizlik (30.09.2026'da tamamen kapandı):** ~~`GENERAL_QUERY` ("DSCR ne demek?", şirket verisi kullanmaz, ADR-010) hiçbir katmana atanmamış.~~ `GENERAL_QUERY` tipi kendisi kaldırıldı (§6.6) — artık bir katman ataması sorusu bile yok.
- **Açılma koşulu:** ~~Ürün sahibinin tek cümlelik kararı.~~ Verildi (Tansu #7). `GENERAL_QUERY` katmanı sorusu da kendiliğinden kapandı — o tip hiç yok, §6.6.

### 3.2 B-27 internet'e açık HTTPS test ortamı — **KAPANDI (30.09.2026): (b) VPN/Tailscale seçildi**
- **Durum (30.09, güncellendi):** Tansu #8'in "şimdilik web'de görüntülenecek" ifadesi netleşti — aşağıdaki üç seçenekten **(b)** seçildi: Tansu'ya **Tailscale ile erişim verildi**. **(c) internete açık HTTPS uygulanmadı**; `CLAUDE.md`/ADR-015/SPEC_06 §6'nın "V0 internete açık değil" kararı **değişmedi, dokunulmadı** — yalnızca VPN üzerinden LAN gibi erişim açıldı, bu zaten CLAUDE.md'nin "V0 sonrası" olarak öngördüğü Tailscale yolu. Aşağıdaki (a)/(b)/(c) analizi, hangi seçeneğin neden uygun olduğunu gösteren gerekçe olarak korunuyor.
- **Talep:** §1.8.1/1 "sabit web adresi ve HTTPS", §1.8.1/4 "ortam internete açık".
- **Çelişki:** `CLAUDE.md` stack kararı "V0'da LAN üzerinde düz HTTP", kapsam dışı listesi "HTTPS/Tailscale (V0 sonrası)"; ADR-015 "Network: LAN only, plain HTTP … V0"; `docs/SPEC_06` §6 "V0 internete açık değildir … Public WAN exposure yok". Üç belge aynı şeyi söylüyor; bu bir V0 kapsam kararıdır, teknik zorluk değildir.
- **Uygulandı:** Öneri (b) — Tailscale ile ürün sahibinin VM'e LAN gibi ulaşması — kabul edildi ve Tansu'ya erişim verildi. TLS'siz cookie riski (ADR-003 `secure=false`) yalnızca VPN içinde kalıyor, WAN'a açılmadı. "AI-BalBal'ı Caddy'den sunma" kısmı (§1) hâlâ backend tarafının bağımsız bir işi — Tailscale erişimi tek başına AI-BalBal'ı Caddy'nin sunmasını sağlamaz, `make update-frontend` gibi bir mekanizma hâlâ gerekli.

### 3.3 B-28'in iki kararı: onay yetkisi ve onaysız belgenin görünmezliği — **ikisi de KAPANDI (1. Tansu #5 + Naci 30.09; 2. Naci 30.09)**
- **Talep 1 (§4.7.5, §4.2 güncellemesi):** ~~Etiket önerisini yükleyen personel onaylar.~~ **Tansu #5:** "Yönetici kendi belgesini eklerse onay gerekmez; personel eklerse kendi onayı + departman yetkilisinden 2. onay." Bu, B-28'in tek onaylı akışını da, Phase 3.2'nin admin-onayı kararını da değiştirir; tasarımı ve etkileri §5.2'de.
- **Çelişki (hâlâ geçerli olan kısım):** Phase 3.2 planında SORU 2 (`docs/plans/PHASE_3_2_PLAN.md:207-209`) tam bu soruyu sordu: "yalnızca admin mi, yükleyen de mi?" Naci "admin" dedi; `api/documents.py:337` ve `:380` buna göre `require_admin`. Yeni akış bu kararın yerine geçer; Naci'nin açık kararı ve `docs/PHASES.md`'ye "Phase 3.2 SORU 2 kararı, Tansu'nun 30.09.2026 iki aşamalı onay kararıyla değiştirildi" notu gerekir; sessiz değişiklik olmaz. Yazma boşluğunun (Tansu #6 "öncelikli") **önce** kapatılması gerektiği değişmedi: ikinci onay, yanlış departmana yüklenmiş belgeyi durdurur ama hedef departmanın kendi `department_manager`'ının onaysız akışını durdurmaz (§5.2 KAPANDI notuyla güncellendi: bu onaysız yol artık yalnızca o departmanın kendi yetkilisine özgüdür, genel `admin`/`management`'a değil).
- **Talep 2 (§4.7.5 son madde):** "Onaylanmamış belge ne aramada ne Balbal'ın cevaplarında yer alır."
- **Çelişki:** Bugün belge `ready` olduğu anda `allowed_document_ids` içindedir ve retrieval'a girer (ADR-006, ADR-021); metadata önerisi belgenin görünürlüğünü etkilemez (SPEC_02 §4: "kullanıcı kabul/düzenleyene kadar belge metadata'sı değişmez", görünürlük değil). B-28 bir **yayın durumu** ekler. Bu yalnızca `allowed_document_ids` içinde uygulanabilir (P-2 = ADR-004), yani gate'e `documents.published` benzeri bir koşul girer ve `SingleDocumentIdsProvider`, eval seed'i (`make seed` sonrası 74 belgenin hepsi yayınlanmış olmalı) ve mevcut testler etkilenir. Yapılabilir; ama "ürün kararı" olduğu için Naci onayı ve ADR-004 concretization ister. Kendi başımıza uygulamayız.
- **Durum (30.09):** Tansu #5 bu ikinci noktaya değinmedi. İki aşamalı onay (§5.2) bir "onay bekliyor" durumu **zaten üretir**; sorunun yeni hali: "ikinci onay gelene kadar personelin yüklediği belge aramada/Balbal'da görünsün mü?" Backend önerisi: görünmesin (yayın durumu = onay durumu, tek kaynak); yöneticinin kendi yüklediği belge onay gerektirmediği için hemen görünür.
- **KAPANDI (30.09.2026, Naci):** Backend önerisi onaylandı — **onay bekleyen belge, ikinci onay gelene kadar ne aramada ne Balbal'ın cevaplarında görünür.** `allowed_document_ids` (ADR-004, P-2) gate'ine `documents.review_status = approved` koşulu girer; `SingleDocumentIdsProvider` de aynı koşulu taşır (görünürlük burada da tutarlı kalır). Eval seed'inin 74 belgesinin hepsi `approved` olmalı (aksi halde retrieval'dan düşerler) — bu, uygulama fazının kabul kriterlerinden biri olacak. Ayrıntı ve testler §5.2'de.

### 3.4 Ürün 3'ün tamamı: yorum, görüş, projeksiyon, sapma analizi
- **Talep:** §1.1 "Ürün 3 — Yorumlama", §7'deki departman yol haritaları, B-23'ün "hukuki gerekçe, savunma argümanı, risk değerlendirmesi" kısmı (§8.2.4/7), B-21'in tahmini KGÜP/KÜPST/gelecek ödeme öngörüsü (§8.3), §7.6.4 "yıl sonu gelir projeksiyonu".
- **Çelişki:** Kural 6 (NO OPINION V0) ve ADR-014: "no opinion, projection, recommendation or speculation". Kural 3: projeksiyon bir hesaptır, LLM yapamaz; §1.5.1 Ürün 3 satırı "Aritmetik + projeksiyon" der ama motorunu söylemez.
- **Açılma koşulu:** V0 sonrası, ADR-014'ün superseded edilmesiyle. O gün bile projeksiyon aritmetiği DuckDB/Python'da kalır, LLM yalnızca "ne hesaplanacağını" belirler (ADR-011 deseni). Ürün sahibi bu ayrımı §1.5.5/1'de zaten yakalamış (B-21 tahmin içerdiği için Ürün 3); tutarlıdır. Bugün: ADR taslağı bile yok, yalnızca bu not.

### 3.5 B-21 EPİAŞ + mahsuplaşma
- **Durum:** Ürün sahibi BEKLEMEDE demiş (§8.3 "kod yazma, tablo açma, EPİAŞ istemcisi kurma"). Backend aynı görüşte. Ek gerekçe: dış API entegrasyonu `CLAUDE.md` V0 dışı listesindeki "SAP/ERP" sınıfındadır; EPİAŞ şifresi ortam değişkeninde olsa da yeni bir dış bağımlılık ve ağ çıkışı ADR-015'e ek ister. "Ay kapandıktan sonra kesin veriyle mahsuplaşma" kısmı (Ürün 2 aritmetiği) ADR-011 desenine tam oturur; tam metin gelince §2'ye taşınır.

### 3.6 B-15 Word yükleme, B-24 e-posta ve sözleşme ilişkilendirme
- **Çelişki:** `CLAUDE.md` V0 kapsamı dışı listesi: "Word/e-posta ingest", "E-mail / Microsoft Graph / Gmail". Ürün sahibi de V0 dışı olduğunu yazmış (§11).
- **Not:** B-15 teknik olarak kolaydır (`.docx` → PDF dönüşümü zaten `ocr-worker`'ın önüne konabilir, ADR-006 hattı değişmez). B-24'ün `document_links(link_type, created_by: ai|user, confirmed)` modeli, `related_document_ids` (ADR-012) alanının genellemesidir ve ADR-012 ile çelişmez; ADR-012'yi "linklerin türü ve onayı var" diye genişletir. İkisi de V0 sonrası ilk adaylardır; şimdi değil.

### 3.7 B-16 canlı veri kaynağı alanı (`AskResponse.live_sources`)
- **Çelişki:** Kural 2 ve ADR-008: her kaynak belge+sayfa veya dosya+sheet+aralık. Canlı bir API cevabı bu ikisinden biri değildir; denetim kaydında (kural 4) "hangi anda hangi değer" yeniden üretilemez. Kabul edilebilmesi için canlı verinin çekildiği anda **belge olarak saklanması** (ör. günlük EPİAŞ özeti bir belge) ve kaynağın o belgeye işaret etmesi gerekir. B-21 ile birlikte, V0 sonrası.

### 3.8 B-10 ve B-12
- Ürün sahibi bunları B-26 ve B-28'e devretmiş; ayrı iş yok. Kayıt için: `document_shares` tablosu açılmayacak (ürün sahibinin kararı, ADR-004 ile de uyumlu).

### 3.9 Arayüzün kendisi kural ihlali talep ediyor mu?
Kod düzeyinde **hayır**. Kontrol edilenler:
- **LLM'e hesap yaptırma (kural 3):** `frontend/src/**` içinde finansal aritmetik yok; tek `Math.round` güven çubuğu genişliği (`MetadataSuggestionPanel.tsx:278`), tek `Math.max` sayfalama (`AdminAuditLogPage.tsx:209`). Sözleşmeler hesabı backend'e bırakıyor (`proposed.ts:283,285,430`). Arayüz metni de aynı şeyi söylüyor (`strings.ts:97,185`).
- **Yetki kontrolünü atlama (kural 1):** Arama `/api/documents` (zaten süzülmüş) listesini süzüyor (`SearchPanel.tsx:17,22`); sohbet ekleri kullanıcının kendi listesinden (`TeamConversation.tsx:18,40`); dosya linkleri `/download`'a gidiyor, 403 sunucuda. `FileLink` `document_id` yoksa linki üretmiyor (`FileLink.tsx:16-21`); bu P-4'ün "her kaynak yetki kontrolünden geçmiş id taşır" kuralını arayüz tarafında zorlar. Klasör görünümünde "yetki süzmesini backend yapar" notu doğru (`DocumentsTab.tsx:79-80`).
- **Audit log'u hafıza gibi kullanma (ADR-016):** Talep yok. B-03 geçmişi ayrı tabloda ve retrieval dışı (§3.2); B-04 geri bildirimi denetim kaydına yazıyor, oradan yalnızca admin okuyor; "her soru-cevabı kaydet" fikri ertelenmiş (§4.5). Uyumlu.
- **Doküman düzeyinde iki risk (kod değil):** (1) P-1…P-10 arasında "LLM hesap yapmaz" ilkesi yok; kural 3'ün karşılığı yalnızca dağınık notlarda (§8.1.2, §8.2.5). Öneri: **P-11** olarak eklensin ki iki repo arasında sözleşme olsun. **Durum (30.09): Tansu #9 ile kabul edildi** ("Ürün 1 için uygun"); Tansu'nun "Ürün 1 için" kaydı önemli: ilke Ürün 2 ve 3 için de geçerlidir (ADR-011 "final number never comes from the model" ürün katmanından bağımsızdır), P-11 metni bunu açıkça söylemeli. Ekleme ürün sahibinin reposunda yapılır. (2) §8.1.2 örnek diyalogda Balbal "kalan yıllık izniniz 11 gün görünüyor" diyor; bu sayı kodun ürettiği bir alan olmalı, LLM'in cümlesi değil. Metin bunu satır 837'de söylüyor; sözleşmede `LeaveBalance.remaining_estimated` alanı var (`proposed.ts:324`); tutarlı, ama ADR'de "cevaptaki her sayı bir alan adından gelir, modelden değil" diye yazılmalı (ADR-011'in "final number never comes from the model" cümlesinin izin akışına taşınması).
- **Kural 1'in yazma tarafı:** `UploadTab.tsx:82` belgenin departmanını klasörden alıp gönderiyor ve backend'in klasör yazma yetkisini kontrol etmesine güveniyor; o kontrol bugün yok (§2, B-26/3). Bu arayüzün hatası değil, iki tarafın ortak boşluğudur.

---

## 4. Arayüz–backend yetenek boşluğu

### 4.1 Backend'in bugünkü yetenekleri arayüzde nasıl görünüyor (kod okumasıyla)

| Yetenek (backend) | Arayüzde | Durum | Eksik alan / gereken |
|---|---|---|---|
| `DOCUMENT_QUERY` cevabı + `[K<n>]` kaynaklar (ADR-021) | `AnswerView.tsx:43-48` → `SourceCardList` | Gösteriliyor | — |
| **Sayfa numarası** (ADR-008) | `SourceCardList.tsx:26` `Sayfa {page_number}` | Gösteriliyor | — |
| **Güncel / tarihsel** (ADR-012, `is_current`) | `SourceCardList.tsx:28-30` GÜNCEL/TARİHSEL rozeti; `v{version}`; yürürlük tarihi `:35` | Gösteriliyor | `is_initial` (ADR-021 `version_chain.py:91`'de hesaplanıyor, prompt'a "İLK HALKA" olarak giriyor) `SourceCard`'da **yok** → arayüz "ilk halka" ayrımını gösteremiyor. Öneri: `SourceCard.is_initial`. |
| Versiyon bağlantısı (süperseded uyarısı) | `SourceCardList.tsx:38-43` yalnızca başlık | Kısmen | id yok (B-07) → link değil |
| Proje (ADR-008 "proje" atfı) | `AnswerView` `projectOfDocument` ile `/api/documents` listesinden türetiliyor (`BalbalChat.tsx:35-38`, `AskPanel.tsx:21-24`) | Dolaylı | `SourceCard.project_code/name` eklensin; ek liste isteği ve "kullanıcının listeleyebildiği belge" varsayımı kalkar |
| `DATA_QUERY` (Excel, ADR-011) | Rozet "Excel"; `ExcelSourceCardList` dosya/sheet/aralık + link + İndir (`AnswerView.tsx:29,49-54`; `SourceCardList.tsx:52-69`) | Gösteriliyor | `ExcelSourceCard.document_id` `None` olabilir (`schemas/excel.py:29`) → `FileLink` "bağlantı yok" işareti. Backend'de cited workbook her zaman `documents` satırıdır; `None` yalnızca teorik, `NOT NULL`'a çekilebilir. |
| `MIXED_QUERY` (iki başlık, ADR-010) | Rozet "Belge + Excel"; iki kaynak listesi; `.answer { white-space: pre-wrap }` (`styles.css:521-522`) başlıkları korur | Gösteriliyor | — |
| ~~`GENERAL_QUERY`~~ | Rozet "Genel bilgi" (warn); `notice` gizli çünkü cevap aynı cümleyle başlıyor (`AnswerView.tsx:36`); kaynak listesi gizli | **Ölü kod (30.09.2026):** backend bu tipi artık hiç üretmiyor (§6.6), bu satır yalnızca frontend'in hâlâ taşıdığı dalı kaydediyor | §4.4'te de not var |
| `answered=false` sabit metin (ADR-014) | Gri cevap + "belge yükleyebilirsiniz" linki (`AnswerView.tsx:34,37-42`) | Gösteriliyor | Link yalnızca `uploadPath` varsa; birden çok departmanlı kullanıcıda ilk departmana gider |
| `notice` (yorum içermez) | `AnswerView.tsx:36` | Gösteriliyor | — |
| `model`, `tokens_in`, `tokens_out` | company-ai `AskPanel.tsx:80-84` gösteriyordu; AI-BalBal `AnswerView` **göstermiyor** | Kaldırılmış | P-7 sadelik kararı olabilir; denetim kaydında duruyor (kural 4 korunur). Bilinçli olduğu teyit edilmeli. |
| `retrieved_document_ids` | Kullanılmıyor | — | Gerekmez (eval/test alanı) |
| Denetim kaydı listesi + detay (ADR-016) | `AdminAuditLogPage.tsx` company-ai kopyası | Gösteriliyor | Detayda `sources` `JSON.stringify` ile ham; `chunks_retrieved` ve `documents_retrieved` **gösterilmiyor**; `rating` sütunu B-04 ile gelir |
| Geri bildirim | `AnswerView.tsx:61-91` butonlar var | **Tansu #1: bu butonlar istenmiyor** | Ürün sahibi tarafı `FeedbackRow`'u kaldırır; yerine `AskResponse.warnings` (§5.3) için üç uyarı görünümü ve "diğer departmandan bilgi talep et" butonu (B-11) gelir |
| Belge detayı versiyon zinciri | `DocumentDetailPanel.tsx:65-67` id'ler `FileLink` | Gösteriliyor | Link metni sabit "Belgeyi aç", belge başlığı değil (`strings.ts:221`); `useDocument` ile başlık çekilebilir |
| Excel yapısı (`/inspect`) | `WorkbookInspectCard.tsx` | Gösteriliyor | Her belge detayı için bir 422 çağrısı (B-13 kapatır) |
| Metadata önerisi üret/uygula/reddet | `MetadataSuggestionPanel.tsx` (aynı) | Gösteriliyor | Onay yetkisi B-28 kararına bağlı |
| Manuel metadata düzenleme, "kim görebilir", kullanıcı yönetimi | company-ai Phase 5.2 kopyaları | Gösteriliyor | — |
| Yükleme (pdf/png/jpg/xlsx/xlsm/csv, ADR-015) | `UploadTab.tsx:144` accept listesi Excel'i içeriyor | Gösteriliyor | company-ai'ın kendi formu yalnızca pdf/png/jpg kabul ediyordu; AI-BalBal düzeltmiş. `folder_id` gönderiliyor, backend yok sayıyor (FastAPI bilinmeyen form alanını atar), hata çıkmaz |
| `AuthorizationScope.project_id` (`/api/documents?project_id=`) | `DocumentsTab.tsx:104-108` projeyi istemcide süzüyor | Kullanılmıyor | Sunucu parametresi var; liste büyüyünce sunucu tarafı süzme tercih edilmeli |
| `POST /api/excel/ask` (yapılandırılmış `value/unit/formatted_value/plan`, `document_ids` daraltma) | Kullanılmıyor | — | Router'lı `/api/ask` yeterli; belge bazlı "bu Excel'e sor" ekranı istenirse hazır |
| `GET /ask` geliştirici sayfası | Kullanılmıyor | — | Gerekmez |

### 4.2 Hangi ekrana hangi alan eklenmeli (özet)

| Ekran | Eklenecek / değişecek alan | Kaynak |
|---|---|---|
| Balbal cevabı, kaynak kartı | `SourceCard.supersedes_document_id`, `superseded_by_document_id` (link), `is_initial` (İLK rozeti), `project_code`/`project_name` | B-07, ADR-012/021 |
| Balbal cevabı | `AskResponse.warnings[]` (`missing_data` / `data_conflict` / `product_limit`, §5.3), `product_level` (eşleme §6, artık yazılabilir); ~~`audit_log_id`~~ (Tansu #1 ile düştü); `conversation_id` ertelendi (Tansu #3) | B-04 (yeni hali), B-25 |
| Balbal cevabı | `model` ve token sayısının bilinçli kaldırıldığının teyidi | P-7 |
| Belge listesi / detayı | `file_kind`; indirme adı; `?inline=1` | B-13, B-17 |
| Belge detayı versiyon linkleri | Link metni belge başlığı | — |
| Departman "Balbal'a Sor" sekmesi | `project_id` çipi kaldırılsın ya da belge güncellensin (`AskPanel.tsx:16,31`) | §1.4/1, §3.3 |
| Denetim kaydı detayı | `chunks_retrieved` (belge, sayfa, sıra) ve `documents_retrieved` gösterimi; ~~`rating`~~ yerine cevabın `warnings` ve `product_level` alanları | ADR-016, B-04 (yeni hali), B-25 |
| Üst bar arama | `/api/search` snippet + sayfa; `/api/directory` | B-14, B-05 |
| Kullanıcı menüsü, üst bar | `primary_department_slug`, `title` | B-09, §2.3 |
| Yükleme | `folder_id` (B-26 sonrası), `department` seçiminin yükleyenin yetkisiyle sınırlanması | §2, B-26 |
| Yönetim › Kullanıcılar | `department_manager` rolü (B-08 sonrası), `title`, `manager_id`, ana departman | B-08, B-09, §2.3 |
| Yönetim › (yeni) Ürün paketi, Onay kuralları | `enabled_products` düzenleme, onay akışı parametreleri (§5.2). ~~Departman CRUD~~ **çıkarıldı (30.09.2026, Naci):** platform yöneticilerinin işi, müşteri admin arayüzüne konmaz — bkz. §5.1 B-20, §8. | Tansu #2, §5.1 |

### 4.3 Tersine liste: backend'de olup arayüzde olmayanlar (B-19)

| Yetenek | Uç / alan | Ürün katmanı (ürün sahibinin tablosuna göre) | Öneri |
|---|---|---|---|
| Yapılandırılmış Excel cevabı | `POST /api/excel/ask` → `value, unit, formatted_value, plan_kind, plan, sources` | Ürün 2 (hesap) — §3.1 kararına bağlı | Belge detayında "bu workbook'a sor" kutusu; `document_ids` ile daraltma |
| Sunucu tarafı proje süzme | `GET /api/documents?project_id=` | Ürün 1 | `DocumentsTab` proje çipi sunucu parametresine bağlansın |
| Sayfa düzeyi retrieval izi | `AuditLogDetail.chunks_retrieved` | Ortak (denetim) | Denetim kaydı detayında tablo |
| Yükleme durumu ayrıntısı | `GET /api/documents/{id}/status` `ingestion_error` | Ürün 1 | Kullanılıyor (`UploadTab`) |
| Kaynak kartı "ilk halka" | `version_chain.py` `is_initial` (yalnızca prompt'ta) | Ürün 1 (temporal) | `SourceCard`'a taşınsın, rozet |
| Cevap model/token bilgisi | `AskResponse.model, tokens_*` | Ortak (denetim) | Kaldırıldıysa bilinçli olduğu teyit edilsin |
| Öneri tetikleme / ret | `POST …/suggest-metadata`, `…/reject` | Ürün 1 | Kullanılıyor |
| Retrieval-only ölçüm | `make eval EVAL_ARGS="--retrieval-only"` | Ortak (test) | Ürün testinde veri bütünlüğü kanıtı için kullanılabilir |

### 4.4 Frontend'in kendi içindeki tutarsızlıklar (bilgi)
- **(30.09.2026, backend tarafında kaldırıldı)** `GENERAL_QUERY` — `strings.ts:49`, `types.ts:235`, `AskPanel.tsx:73,77-78,86`, `AdminAuditLogPage.tsx:15` hâlâ bu değeri biliyor/gösteriyor; backend artık hiç üretmediği için zararsız ölü kod. Bu fazda dokunulmadı (Naci'nin kararı, `docs/reports/GENERAL_QUERY_KALDIRMA_REPORT.md` §6).
- `AskPanel.tsx:16,31,46-58` proje çipi ve `project_id`; belge "kaldırıldı" diyor (§1.4/1, §3.3).
- `BalbalChat.tsx:32` çalışan kapsamını `department_slugs[0]`'a daraltıyor; iki üyelikli demo `finans` kullanıcısı Balbal'da `mali_isler` belgelerini görmez. B-09 ve B-20/5 ile çözülür; o güne kadar bilinen fark.
- `proposed.ts:18` 404'ü "henüz yok" sayıyor; uçlar açıldığında gerçek "bulunamadı" 404'ü de "Backend bekleniyor" görünür. Öneri: "henüz yok" için 501, 404 anlamını korur.
- `types.ts` şemaları elle aynalanıyor; backend `/openapi.json` üretiyor. ~40 yeni uçla el ile senkron kırılır; TS tip üretimi (openapi-typescript) önerilir. Bu, ürün sahibi tarafının kararıdır.
- Test yok, CI yok; yalnızca `tsc` + `eslint`. README'deki "Çalışıyor" ifadeleri elle test iddiasıdır. company-ai'ın kendi frontend'inde de UI testi yok (CLAUDE.md, ADR-019), backend 383 test taşır.
- 28 dosya company-ai `frontend/` ile bayt bayt aynı (Phase 5.2 yönetim ekranları dahil). B-27 §1.8.1/2 "backend reposundaki frontend testte kullanılmaz" diyor.
- **KAPANDI (30.09.2026, Naci):** company-ai `frontend/` **emekli edilir**. AI-BalBal (`github.com/ftansu/AI-BalBal`), Naci ve Tansu'nun projesinin tek, asıl frontend'i olacak. company-ai `frontend/` **silinmez** — repoda kalır, yalnızca artık geliştirilmez; ileride hiçbir fazda "temizlik" gerekçesiyle kaldırılmaz, yalnızca kullanılmadığı işaretlenir.
  **Pratik sonuçlar:** company-ai backend'i (FastAPI, yetki, retrieval, Excel motoru, router) değişmeden kalır ve AI-BalBal'ın API istemcisi olarak kullanacağı katman olmaya devam eder; backend uçları AI-BalBal'ın beklediği sözleşmeyle (response şemaları, `enabled_products`, vb.) uyumlu tutulur — bu zaten backend'in her fazda takip ettiği bir kısıt, yeni bir yük değil. Test/lint kapsamı için önerimiz: `company-ai/frontend/` artık `make test`/`make lint`'in **zorunlu** yeşil kapsamından çıkarılsın (geliştirilmeyen bir ağacı her backend değişikliğinde yeşil tutmak gereksiz bakım yükü ve zamanla anlamsız hale gelir — ör. `types.ts` API şemasından sürüklenir ama kimse güncellemeyecek); kod fiziksel olarak repoda kalır, yalnızca CI'ın zorunlu adımı olmaktan çıkar. Geçiş dönemi diye ayrı bir ara aşama yok — karar netleştiği anda AI-BalBal asıl arayüz, company-ai `frontend/` günden güne paralel sunulmaz (Caddy'nin hangi build'i sunacağı zaten B-27/§1'de ayrı bir iştir).

---

## 5. Yeni tasarım kararları (Tansu, 30.09.2026) ve etkileri

Bu iki karar BACKEND_GAPS'ta yoktu; B-08, B-20, B-26, B-28 ve B-22 planlarını değiştiriyor. Her ikisi de mevcut kurallarla uyumludur; ikisi de ADR ister.

### 5.1 "Yetkilendirmeyi müşteri kendi yönetim arayüzünden belirler; Balbal yalnızca araçları sağlar"

**Anlamı:** Departman ağacı, roller, klasör yetkileri, onay zinciri ve ürün paketi **veridir, kod değildir** (P-8 ile aynı yönde). Backend'in işi kural motorunu tek yerde tutmak (ADR-004: `allowed_document_ids`) ve o motorun okuduğu tabloları admin uçlarıyla düzenlenebilir kılmaktır. Demo yapısı seed ile gelir ama müşteri için başlangıç noktasıdır, sabit değildir.

**Düzeltme (30.09.2026, Naci):** Bu başlık iki ayrı yetkilendirme türünü tek cümlede karıştırıyordu. Naci'nin ayrımı: **Personel Yetkilendirmesi** (var olan departman/rol yapısı içinde kişi atama/çıkarma) — müşterinin kendi admin arayüzünden yaptığı budur, bu bölümün geri kalanı için geçerli. **Platform Yetkilendirmesi** (departman/rol gibi yapı taşlarının tanımı/ekleme/kaldırma) — yalnızca platform yöneticileri (Üretici Taraflar/Proje Yetkilileri) yapar, müşteri arayüzüne konmaz. Yani "departman ağacı ... müşteri için başlangıç noktasıdır, sabit değildir" cümlesi **rolleri kişilere atama** için doğru, **departmanın kendisini ekleme/kaldırma** için yanlıştır — bkz. B-20 satırı (aşağıda) ve §8 (Anayasa O-10 ile çelişki).

**Kurallarla ilişkisi:** ADR-004 değişmez; motor tektir, yalnızca girdileri tablo olur. Kural 1'in "önce yetki" sırası korunur. Yeni bir yetki yolu açılmaz.

**Etkilenen maddeler:**

| Madde | Eski plan | Yeni durum |
|---|---|---|
| B-20 (1–5) departman yapısı | Migration + seed ile sabit ağaç | **Düzeltildi (30.09.2026, Naci):** Departman CRUD bir *Platform Yetkilendirmesi* işi — **müşterinin admin arayüzüne konmaz**, platform yöneticileri (Üretici Taraflar/Proje Yetkilileri) tarafından yapılır (migration/seed veya ayrı, müşteriye kapalı bir mekanizma ile). Phase 1.2'nin "seed-only" kararı bu haliyle büyük ölçüde korunur; `POST/PATCH /api/departments`'ın müşteri admin'ine açık bir uç olacağı varsayımı **yanlıştı, düzeltildi**. Bunun Anayasa v1.1 O-10'la çelişkisi §8'de. |
| B-08 departman yöneticisi | Rol enum'a eklenir, kim olduğu seed'den | Rolü admin `PATCH /api/users/{id}` ile verir (uç zaten var). Ek: "hangi rol hangi gizliliği görür" tablosu mu, sabit kural mı? Önerimiz: V0'da sabit kural (`employee: normal`, `department_manager: normal+restricted`, `management: hepsi`), tablo değil; müşteri kişileri role atar, kuralı değiştirmez. Aksi, kural motorunu tabloya taşımak demektir ve ayrı ADR ister. |
| B-26 klasör yetkileri | Zaten admin sayfası | Değişmez; bu karar B-26'nın tasarımını teyit eder. |
| B-25 ürün paketi | CLI ile ayar, admin UI "şimdilik gerekmez" | Admin ucu ve Yönetim sekmesi gerekir (§2 B-25). |
| B-28 / §5.2 onay zinciri | Belgede sabit ("yükleyen onaylar") | Onay kuralı role bağlı (§5.2); "kim onaysız yükler, kim ikinci onaycıdır" artık **sabit kural** — hedef departmanın kendi `department_manager`'ı (KAPANDI 30.09.2026, bkz. §5.2). Admin arayüzünden değişen yalnızca *kimin* o rolde olduğu, kuralın kendisi değil. |
| B-22 onay mercii (§8.1.5) | `manager_id → department_manager → İK` zinciri kodda | Zincir aynı, ama kişileri (`manager_id`, roller) müşteri arayüzden atar; B-05'in `users.manager_id` alanı admin `UserForm`'a girer. |
| ADR-004 Phase 1.2 notu | "departments/projects are seed-only in V0" | Superseded olacak (departmanlar için); ADR concretization satırı. |

**Backend tarafının sınırı:** "Balbal araç sağlar" cümlesi, yetki **kararlarını** LLM'in vermediğini de içerir. Yetki değişiklikleri yalnızca admin uçlarından, denetim kaydına yazılarak (§2 B-26/2 `folder_grant_events` deseni, roller için de aynı) yapılır; Balbal'a "X'e Y klasörünü aç" demek işlem başlatmaz (P-1).

### 5.2 İki aşamalı, role bağlı belge onayı

**Tansu #5:** "Yönetici kendi belgesini eklerse onay gerekmez; personel eklerse kendi onayı + departman yetkilisinden 2. onay gerekir."

**KAPANDI (30.09.2026, Naci):** "Yönetici" = **belgenin yüklendiği departmanın kendi `department_manager`'ı** — genel `management` rolü değil, sistem `admin`'i de değil. Naci'nin literal örneği: "Finans departmanına yüklenen bir belgeyi Finans departmanının yetkilisi onaylar, sistem admin'i değil." Yani rol değil, **o belgenin departmanına özgü kişi** belirleyici. "Departman yetkilisi" (2. onaycı) ile "yönetici" (1. onaycı/onaysız yükleyici) aynı kişi/rolü işaret eder: her ikisi de **hedef departmanın `department_manager`'ı**. Akış:

```
yükleyen = belgenin departmanının kendi department_manager'ı
   → belge doğrudan `approved` (yayınlanır), kayıt defterine "auto: department_manager" olayı

yükleyen = employee, ya da department_manager/management/admin ama BAŞKA/genel bir sıfatla
            (kendi departmanının yetkilisi olmadığı bir belge yüklüyorsa — örn. sistem admin'i
            Finans'a belge yüklerse, ya da bir başka departmanın department_manager'ı)
   → 1. aşama: yükleyen metadata'yı (Balbal önerisi + kendi alanları) onaylar → `pending_review`
   → 2. aşama: **hedef departmanın kendi `department_manager`'ı** onaylar → `approved`; ya da yorumla geri gönderir → `changes_requested`
   → onaydan sonra içerik/metadata değişirse onay düşer (P-1/4)
```

`management`/`admin` rolleri **genel bir onaysız-yükleme ayrıcalığı taşımaz**; onlar da başka bir departmana belge yüklerken o departmanın kendi yetkilisinin 2. onayına tabidir. (Bu, B-08'deki okuma/görünürlük kuralı — "management: hepsini görür" — ile çelişmez; o ayrı bir eksen, salt görüntüleme içindir, yükleme onayı değil.)

**Kurallarla ilişkisi:**
- Phase 3.2 SORU 2 (admin-only apply) bu akışla **değiştirilir**; Naci'nin kararı ve PHASES.md notu gerekir (§3.3).
- Durum geçişleri kodda, LLM tetiklemez (P-1/5, kural 6). `document_metadata_suggestions.status` bunun için yetmez (öneri durumu ≠ belge onay durumu); `documents.review_status` + `document_review_events` (kayıt defteri, §2 B-28) gelir.
- P-1'in dört testi burada da yazılır: personel onayı olmadan `pending_review` olunmaz; başkası adına 1. aşama onayı 403; onaydan sonra değişiklik onayı düşürür; onaylanmamış belge başkasının listesinde görünmez (**§3.3'ün 2. sorusu — KAPANDI (30.09.2026, Naci): görünmez, `allowed_document_ids`'e `review_status = approved` koşulu girer**).
- Yazma boşluğu (Tansu #6): ikinci onay personelin yanlış departmana yüklediği belgeyi durdurur; ama hedef departmanın kendi `department_manager`'ı onaysız yayınlar, dolayısıyla "yüklenen belgenin departmanı ⊆ yükleyenin yetkili olduğu departmanlar" kontrolü **ayrıca** şarttır, onay akışı onun yerine geçmez.
- Yetkilendirme müşteride (§5.1): "ikinci onaycı kim" artık sabit kural (hedef departmanın `department_manager`'ı); `company_settings` parametresi olacak kısım yalnızca "department_manager tanımlı değilse ne olur" gibi istisna durumlar (açık nokta 2, aşağıda).

**Etkilenen maddeler:** B-28 (onay çekirdeği yeniden yazılır; %80 eşiği 1. aşamada uygulanır: personel %80 altı alanı açıkça onaylamadan 1. aşamayı geçemez), B-12 (kapanmıştı, öyle kalır), B-08 (ön koşul oldu, **ikinci onaycı tanımı KAPANDI** — bkz. §2), B-01 gündem (`approval` kalemi = hedef departmanın yetkilisinin bekleyen 2. aşama kuyruğu; "kimin göreceği B-12'ye bağlı" notu çözüldü), B-02 bildirim (`changes_requested`, `approved` olayları), B-26 (klasör `write` yetkisi 1. aşamanın ön koşulu).

**Açık noktalar:** ~~(1) "Yönetici" kelimesinin kapsamı~~ **KAPANDI (30.09.2026)** — yalnızca hedef departmanın `department_manager`'ı; `management`/`admin` genel onaysız-yükleme ayrıcalığı taşımaz (yukarıya bkz.). Kalan açık noktalar: (2) `department_manager` tanımlı olmayan departmanda personel yüklemesi ne olur (öneri: `409 approver_not_configured` + admin'e bildirim, §8.1.5 deseni). (3) Excel yüklemeleri de aynı akışa mı girer (öneri: evet; Ürün 2 hesabı onaysız workbook'a dayanmamalı).

### 5.3 Üç bildirim türü (Tansu #1) — uygulama notları

| Tür | Ne zaman | Nereden gelir | Kural sınırı |
|---|---|---|---|
| `missing_data` | `answered=false` | ADR-021: chunk yoksa LLM çağrılmadan; chunk var ama model "bulamadım" dediğinde (ADR-014 kanonik metin) | Var olan davranış, yalnızca yapılandırılmış alan eklenir. Buton: B-11 evrak talebi (departmanı kullanıcı seçer). |
| `data_conflict` | Kullanıcının **görebildiği** kaynaklar aynı olgu için farklı değer veriyorsa | Cevap prompt'una tek kural: "iki kaynak aynı şey için farklı değer veriyorsa ikisini de kaynağıyla yaz ve `[ÇELİŞKİ]` işaretle, hangisinin doğru olduğunu söyleme"; `parse_citations` işareti alana çevirir. **Versiyon zinciri farkları çelişki değildir** (ADR-012 "eski ≠ yanlış"; `version_chain.py` GÜNCEL/İLK ayrımı prompt'ta zaten var) — aksi halde her tadil "çelişki" görünür. | Kural 6: hangi değerin doğru olduğuna karar verilmez; yalnızca aktarılır. **Kural 1/P-2 sınırı:** "departmanlar arası çelişki" ancak kullanıcı iki departmanın belgesini de görebiliyorsa saptanabilir; görmediği departmanın belgesiyle karşılaştırma yapılamaz, varlığı söylenemez. Tansu'nun "diğer departmandan veri talep et" butonu bu yüzden kullanıcının kendi kararıyla çalışır, Balbal "diğer departmanda farklı değer var" **demez**. Prompt değişikliği → prompt fazı, `--repeat 3` ölçümü, eval'e `conflict` kategorisi. |
| `product_limit` | Router `DATA`/`MIXED` seçti ama P2 kapalı; ileride `ACTION` niyeti ama P2 kapalı | `require_product` (B-25) + §6'daki düşürme kuralı | Sabit metin ("Bu özellik şirketinizin paketinde yok"), LLM üretmez. |

---

## 6. Ürün 1 / Ürün 2 sınırının netleşmesi: sonuçlar

**Tansu #7:** "Şimdilik Ürün 2'den başlayacak. Ürün 1 yalnızca veri yükleyecek, yüklenen veriyi bulup bilgilendirecek." Backend okuması: mevcut sistem bütünüyle **Ürün 2 seviyesindedir**; Ürün 1, aynı sistemin hesaplama dalları kapatılmış halidir. Bu, §1.5.1 tablosuyla ("Ürün 1: hesaplama yok") tutarlıdır ve BAGLANTI §2.1/4'ün "bugün her cevap P1" varsayımını düşürür.

### 6.1 `product_level` eşlemesi

| `query_type` (ADR-010) | `product_level` | Gerekçe |
|---|---|---|
| `DOCUMENT_QUERY` | `P1` | Bul, oku, kaynakla aktar; hesap yok |
| `DATA_QUERY` | `P2` | DuckDB hesabı (ADR-011) |
| `MIXED_QUERY` | `P2` | Excel dalı hesap içerir |
| ~~`GENERAL_QUERY`~~ | ~~karar gerekiyor~~ | **KALDIRILDI (30.09.2026)** — bu tip artık hiç yok, bkz. §6.6. Aşağıdaki satır artık geçerli değil, yalnızca tarihçe için korunuyor. |
| `ACTION` (ileride, B-22) | `P2` | §3.5 zaten öyle diyor |

Eşleme koddadır (`ask_router.py`), tablo değil; katman tanımı ürün sahibinin değil sistemin özelliğidir.

### 6.2 Ürün 1 paketinde davranış (`enabled_products = ["P1"]`)

- Router `DATA_QUERY`/`MIXED_QUERY` seçerse istek **reddedilmez**; ADR-010'un güvenli yönü uygulanır: soru `DOCUMENT_QUERY` olarak cevaplanır (fall-through zaten var: "DATA miss falls through to documents"), cevaba `warnings: [{kind: "product_limit"}]` eklenir, `product_level: P1` döner. Böylece "Ankara RES 2026 Q2 DSCR kaç?" P1 müşteride belgelerden (covenant raporu PDF'i) cevaplanır, Excel hesabı yapılmaz. Bu, Tansu #1'in "yetkilendirme uyarısı" türünün ilk somut kullanımıdır.
- `POST /api/excel/ask` `require_product("P2")` ile 403 `product_not_enabled`.
- **Excel yükleme ve `GET /api/excel/{id}/inspect` P1'de açık kalır**: "veri yükleyecek" ifadesi Excel'i de kapsar; inspect hesap yapmaz (openpyxl okuma, ADR-011). Workbook P1'de bir belgedir; içeriği FTS'e girmez (ADR-006 Phase 4.2: Excel'e chunk yok), yani P1'de Excel yalnızca listelenir ve indirilir. Bu sınırlama ürün sahibine söylenmeli.
- Metadata önerisi (LLM sınıflandırma) P1'de açık: "bulup bilgilendirme"nin parçası, hesap değil.

### 6.3 Eval ve demo

- Demo ortamında üç ürün açık (§1.5.4); `make eval` değişmez. Ek olarak P1-only için küçük bir kabul testi: `data`/`mixed` kategorisindeki sorular `product_limit` uyarısıyla `DOCUMENT_QUERY` döner ve `product_level: P1` taşır (T-03/T-05'in somut hali).
- `questions.json`'a `expected_product_level` alanı; `eval_lib.score_question` bunu da puanlar.

### 6.4 Arayüz

- Örnek sorular (`strings.ts:47-52`): "Ankara RES 2026 Q2 DSCR kaç?" ve "Güncel DSCR kaç?" P2 örnekleridir; P1 paketinde gösterilmemeli ya da `product_limit` uyarısıyla cevaplanacağı bilinmeli. Ürün sahibi tarafının kararı.
- Cevap rozeti (`AnswerView.tsx:33`) `query_type` gösteriyor; `product_level` ayrıca gösterilecekse tip `types.ts`'e eklenir.
- Balbal footnote (`strings.ts:97` "Hesaplamalar Excel verisinden sistem tarafından yapılır") P1'de yanıltıcı olur; pakete göre metin.

### 6.5 Sıralama

Tansu #7 "şimdilik Ürün 2'den başlayacak" dediği için ilk müşteri/test P2 ile çalışır; P1 kısıtı bir **test senaryosudur**, geliştirme önceliği değil. Bu, B-25'in "küçük, hemen" etiketini korur: `enabled_products` + `require_product` + eşleme + düşürme kuralı tek fazda.

### 6.6 Güncelleme (30.09.2026) — bu bölüm yazıldıktan sonra üç gelişme oldu

1. **GENERAL_QUERY tamamen kaldırıldı** (Naci + Tansu kararı, backend AI-BalBal incelemesinden bağımsız ayrı bir konuşma). Sistem artık hiçbir zaman modelin kendi genel dünya bilgisinden cevap vermiyor — tanım soruları ("DSCR ne demek?" dahil) da `DOCUMENT_QUERY`'ye yönlendiriliyor, `general_answer.py` silindi. §6.1'deki eşleme tablosundaki `GENERAL_QUERY` satırı ve "karar gerekiyor" notu bu yüzden **artık geçersiz** — o tip router'da hiç yok, `product_level` kararı gerektirmiyor. Canlı Gemini ile doğrulandı: korpus bu terimleri (DSCR, ÇED, covenant testi) genel biçimde hiçbir yerde tanımlamadığı için gerçekçi sonuç sabit "bilgi bulamadım" metni oluyor — uydurma bir tanım değil. Detay: `docs/plans/GENERAL_QUERY_KALDIRMA_PLAN.md`, `docs/reports/GENERAL_QUERY_KALDIRMA_REPORT.md`.
2. **"Farklı tanım varsa hepsini göster" kuralı eklendi:** `answer_prompt.py`'ye yeni bir kural (9. kural): birden fazla **ilgisiz** kaynak (zincir/versiyon ilişkisi yoksa — 5. kural o durumu ayrıca kapsıyor) aynı terim veya kavram için farklı bir tanım/açıklama veriyorsa, hepsi kendi kaynak etiketiyle ayrı ayrı yazılır, biri diğerine tercih edilmez. `docs/prompts/ANSWER_SYSTEM_PROMPT.md`'ye `make prompt-doc` ile yansıtıldı. Gerçek bir "çelişen tanım" senaryosu bugünkü korpusta yok (kural yalnızca prompt talimatı olarak var, sentetik bir fixture'la uçtan uca kanıtlanmadı — bilinçli bir karar, bkz. rapor §5).
3. **Erişim kararı uygulandı — §3.2/B-27'nin cevabı netleşti:** Tansu'ya **Tailscale ile erişim verildi**. "Web'de görüntülenecek" ifadesi VPN/Tailscale anlamına geliyormuş (§3.2'nin üç seçenekten (b) seçeneği); internete açık HTTPS **değil**. `CLAUDE.md`/ADR-015/SPEC_06 §6'nın "V0 internete açık değil" kararına dokunulmadı — VPN içinden LAN gibi erişim, WAN'a açılma değil. Ayrıntı: §3.2 (güncellendi).

---

## 7. Karar durumu

### 7.1 Cevaplananlar (Tansu, 30.09.2026)

| Eski # | Soru | Cevap |
|---|---|---|
| 1 | DuckDB hesaplı `DATA`/`MIXED` Ürün 1 mi 2 mi? | **Ürün 2** (Tansu #7). `GENERAL_QUERY` artık router'da hiç yok (30.09.2026'da tamamen kaldırıldı, §6.6), bu yüzden `product_level` kararı da gerekmiyor. |
| — | B-27 / §3.2 "web'de görüntülenecek" ne demek? | **KAPANDI (30.09.2026)** — VPN/Tailscale; Tansu'ya erişim verildi, internete açık HTTPS değil. §6.6, §3.2 (güncellendi). |
| — | §6.1 `GENERAL_QUERY` katmanı kararı | **KAPANDI (30.09.2026)** — GENERAL_QUERY tamamen kaldırıldı, karar gerekmiyor. §6.6, `docs/reports/GENERAL_QUERY_KALDIRMA_REPORT.md`. |
| 3 | B-28 onay yetkisi (iki nokta: kim onaylar + onaysız belge görünür mü) | **İkisi de KAPANDI (30.09.2026).** Kim onaylar: hedef departmanın kendi `department_manager`'ı, `management`/`admin` değil (Tansu #5 + Naci netliği; §5.2, §2 B-08). Onaysız belge görünürlüğü: görünmez, `allowed_document_ids`'e `review_status = approved` koşulu girer (Naci; §3.3, §5.2). |
| — | §5.2 — "Yönetici"/"departman yetkilisi" tanımı, onaysız yükleme kuralı | **KAPANDI (30.09.2026, Naci)** — ikisi de hedef departmanın kendi `department_manager`'ı; `management`/`admin` genel onaysız-yükleme ayrıcalığı taşımaz. Naci: "Finans departmanına yüklenen bir belgeyi Finans departmanının yetkilisi onaylar, sistem admin'i değil." §5.2, §2 B-08 güncellendi. |
| — | BACKEND_GAPS sürüm dondurma | **KAPANDI (30.09.2026, Naci'nin kararı)** — `BACKEND_GAPS.md` v7.9, commit `b219600`, 29.09.2026 donduruldu (bkz. not başlığı). Sonraki güncellemeler bu notta otomatik takip edilmez, ayrı bir inceleme turunda ele alınır. |
| 4 | ~~B-26 gelene kadar yükleme kısıtı~~ | **KAPANDI** (30.09.2026) — bağımsız güvenlik yaması, `docs/plans/GUVENLIK_YAMA_2026-09-30_PLAN.md`, `docs/PHASES.md` Adım 5 notu. `employee` artık yalnızca kendi üyeliklerindeki departmana yükleyebiliyor; `management`/`admin` muaf, `department=None` değişmedi. B-26 tam klasör yetkisi çözümünün yerini almaz, yalnızca en acil boşluğu kapatır. |
| 8 (kısmen) | B-23 gizlilik | Bireysel model: **kendisi + İK** (Tansu #4, izin ve yazışma için). |
| 9 | P-11 | **Kabul** (Tansu #9). |
| 11 | Çelişkide öncelik | **`CLAUDE.md`/ADR'ler önce**; GitHub üzerinden çözüm; çözülmezse Tansu + Naci (Tansu #10). |
| — | B-03 | **Ertelendi** (Tansu #3). |
| — | Geri bildirim butonları | **Reddedildi**, yerine üç uyarı türü (Tansu #1, §5.3). |
| — | Yetkilendirmeyi kim yönetir | **NETLEŞTİ, ikiye ayrıldı (30.09.2026, Naci):** *Personel Yetkilendirmesi* (var olan departman/rol içinde çalışan atama/çıkarma) — **müşteri**, admin arayüzünden (Tansu #2, §5.1). *Platform Yetkilendirmesi* (departman/rol gibi yapı taşlarının tanımı/ekleme/kaldırma) — **platform yöneticileri** (Üretici Taraflar/Proje Yetkilileri), müşteri değil. Bu ayrım Anayasa v1.1 O-10 ile çelişiyor; **karar Tansu'nun/Proje Yetkililerinin**, bkz. §8. |
| — | Departman CRUD'unun V0'a alınması (eski §7.2 öncelikli #2) | **KAPANDI, backend tarafı için (30.09.2026, Naci):** Departman CRUD bir *Platform Yetkilendirmesi* işidir — **platform yöneticileri tarafından yapılır, müşterinin admin arayüzüne konmaz.** §5.1'in B-20 satırındaki "admin CRUD" varsayımı bu yüzden düzeltildi. Bunun O-10 ile çelişkisi ayrı, anayasa seviyeli bir açık madde — bkz. §8. |

### 7.2 Açık kalanlar

**Öncelikli:** yok — bu turda kapanan iki madde (belge görünürlüğü, departman CRUD'un platform tarafı)
dışında, "kim yetkilendirir" ayrımının Anayasa v1.1 O-10 ile çelişkisi artık backend'in önceliklendirdiği
bir liste maddesi değil, **§8'de ayrı ve doğrudan Tansu'nun/Proje Yetkililerinin kararını gerektiren bir
anayasa maddesi** olarak izleniyor.

Not: §7'de açık madde **kalmıyor değil** — §8'deki anayasa çelişkisi ve aşağıdaki sekiz teyit/ikincil
madde hâlâ açık; yalnızca bu turda ele alınan iki backend sorusu (belge görünürlüğü, departman CRUD'unu kim yapar)
kapandı.

**Teyit / ikincil:**
1. §2 B-08 — müdür `board` görür mü; "hangi rol neyi görür" sabit kural mı (öneri) yoksa müşteri tablosu mu (§5.1'in sınırı).
2. §2 B-22/3 — onay zincirindeki yönetici, personelin izin belgesini görür mü (Tansu #4 yalnızca "kendisi + İK" dedi).
3. §2 B-23/2 — yazışma için de "kendisi + İK" mi, yoksa "kendisi + departman yetkilisi" mi (İK'nın yazışmayla ilgisi yok).
4. §2 B-02 — "departmana belge yüklendi" bildiriminin alıcısı.
5. §2 B-06a — görüş talebi belgesinin departmanı ve gizliliği.
6. §4.1 — `model`/token bilgisinin arayüzden kaldırılmasının bilinçli olduğu.
7. §5.2 açık nokta 2–3 — `department_manager` yoksa ne olur; Excel yüklemeleri aynı onay akışına girer mi.
8. §6.4 — P1 paketinde örnek soruların ve footnote'un durumu (ürün sahibi tarafı).

Backend tarafı §3'te kalan maddelere (B-27 internet kısmı, Ürün 3, B-21, B-15/B-24, B-16) kod yazmaz; §1, §2, §5 ve §6'daki maddeler Naci'nin faz planı onayıyla başlar (`CLAUDE.md` çalışma biçimi 2–3).

**Önerilen ilk somut adım — Aşama 0 (kapandı) ve Aşama A (başlatılabilir):**
- **Aşama 0 — kapandı:** Yükleme yetki açığı ara düzeltmesi (Tansu #6), bağımsız güvenlik yaması olarak uygulandı (§7.1 satır 4).
- **Aşama A — "Balbal cevap döngüsü":** `B-07, B-09, B-13, B-17, B-05, B-25` eşlemesi, `warnings` alanının `missing_data`/`product_limit` türleri; somut karşılıkları `audit_log_id`, `product_level`, versiyon linki, `POST /api/ask/feedback`, `enabled_products`. **KAPANDI engel: company-ai `frontend/`'in kaderi netleşmemişti** (bu adımın hangi arayüze hizmet edeceği belirsizdi). Bu artık netleşti — AI-BalBal asıl frontend (yukarıda, §0 ve §4.4) — **Aşama A'nın önünde bekleyen bir engel kalmadı, şimdi başlatılabilir.** Planı Naci ayrı bir mesajda başlatacak.

---

## 8. Anayasa (Balbal Anayasası v1.1) ile ilgili geri bildirim

**Not:** Backend tarafı Balbal Anayasası'nın tam metnine sahip değil; bu bölümdeki madde kodları (O-10, Ç-1, Ç-3, Ç-7, Ü-9) ve alıntılar Naci'nin 30.09.2026'da relay ettiği özetten alınmıştır. Tam metin gerekirse Tansu'dan istenmelidir — burada var olmayan bir madde metni **uydurulmamıştır**.

### 8.1 Çelişki: O-10 vs. Naci'nin Personel/Platform Yetkilendirmesi ayrımı

- **O-10 (Balbal Anayasası v1.1):** "Müşteri departman yönetimini yönetir." Bu ifade, §5.1'in bu notta önceki halinin dayandığı Tansu #2 cevabıyla ("şirketteki tüm yetkilendirmeleri müşteri kendi yönetim arayüzünden belirler") aynı yöndeydi ve backend bu ikisini **departman CRUD'unun müşteri admin arayüzüne açılacağı** şeklinde okumuştu (§5.1 B-20 satırı, `POST/PATCH /api/departments`).
- **Naci'nin cevabı (30.09.2026), §7.1'de "departman CRUD" sorusuna:** "Platform yöneticileri tarafından yapılacak" — yani müşteri değil. Bu, O-10'un "departman yönetimi" ifadesiyle **doğrudan çelişiyor** (Ç-1'in kapsadığı türden bir çelişki — anayasa maddesiyle yeni bir kararın çatışması).
- **Naci'nin önerisi — iki yeni tanım, anayasaya eklenmek üzere:**
  1. **Personel Yetkilendirmesi:** Müşterinin, var olan departman/rol yapısı içinde çalışan atama/çıkarma yetkisi. (Bu, O-10'un muhtemelen kastettiği "departman yönetimi" ile örtüşür — bir departmana kim üye, kim yönetici, gibi.)
  2. **Platform Yetkilendirmesi:** Departman/rol gibi yapı taşlarının tanımlanması, eklenmesi, kaldırılması. **Yalnızca Üretici Taraflar/Proje Yetkilileri** yapar; müşteriye açılmaz.
- **Sonuç:** Bu ayrım kabul edilirse O-10'un "departman yönetimi" ifadesinin **kaldırılması veya "Personel Yetkilendirmesi" ile sınırlanacak şekilde daraltılması** gerekir (örn. "Müşteri, Personel Yetkilendirmesi kapsamında departman yönetimini yönetir").
- **Karar mercii:** **Ç-3** gereği anayasayı yalnızca Üretici Taraflar/Proje Yetkilileri değiştirebilir — backend tarafı bu maddeyi tek taraflı yorumlayıp uygulamaz. Bu, §7.2'nin eski "öncelikli" listesinden çıkan bir backend sorusu değil, **Tansu'nun/Proje Yetkililerinin karar vereceği bir anayasa maddesi**dir. Backend, karara kadar §5.1/B-20'de belirttiği yorumla (departman CRUD = platform işi) plan yapar; karar tersi yönde çıkarsa (O-10 aynen kalır, müşteri departman CRUD'u da yapar) B-20 ve §5.1 buna göre geri alınır.

### 8.2 Genel gözlem: Ç-7 ve Ü-9, GENERAL_QUERY kaldırma kararını doğruluyor

Balbal Anayasası v1.1'in iki maddesi, bugün (30.09.2026) bağımsız olarak aldığımız `GENERAL_QUERY` kaldırma kararıyla (§6.6, `docs/reports/GENERAL_QUERY_KALDIRMA_REPORT.md`) tam uyumlu, hatta onu anayasa seviyesinde doğruluyor:

- **Ç-7 (Veri Durumları):** Kesin Veri / Veri Yok / Yeterli Veri Bulunmamaktadır / Çelişkili Veri / AI Yorumu — beş durumlu bir sınıflandırma, hiçbirinde "modelin genel dünya bilgisinden cevap" diye bir durum yok. Bu, kural 2'nin (SOURCE GROUNDING) ve GENERAL_QUERY'nin tamamen kaldırılmasının anayasa diliyle karşılığıdır: sistem ya kaynaktan kesin/yetersiz/çelişkili bilgi bulur ya da bulamaz, üçüncü bir "bildiğimi söyleyeyim" seçeneği yok.
- **Ü-9 (kapsam dışı sorulara cevap verilmez):** Bu da aynı ilkenin ürün tarafındaki karşılığı — kapsam dışı (şirket kaynaklarında karşılığı olmayan) bir soru, model tarafından "genel bilgiyle" doldurulmaz, reddedilir/yönlendirilir.
- **Sonuç:** Backend'in GENERAL_QUERY'yi kaldırma kararı **anayasaya aykırı değil, anayasanın zaten öngördüğü davranışı** koda döküyor. Ayrı bir onay/karar gerektirmez; bu yalnızca bir tutarlılık notudur.
