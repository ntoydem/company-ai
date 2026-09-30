# AI-BalBal taleplerine backend geri bildirimi — 30.09.2026

**Kime:** Ürün sahibi tarafı (`ftansu/AI-BalBal`) ve onun yapay zekası
**Hazırlayan:** Backend tarafı (`ntoydem/company-ai`, Claude Code ile), Naci'nin talebiyle
**İncelenen:** `ftansu/AI-BalBal` @ `b219600` (29.09.2026; `docs/BACKEND_GAPS.md` v7.9, `docs/BAGLANTI_YOL_HARITASI.md` 28.09.2026, `frontend/src/**`) ↔ `ntoydem/company-ai` @ `4301968` (Phase 5.4b)
**Esas alınan çerçeve:** `CLAUDE.md` altı değişmez kural (1 SECURITY, 2 SOURCE GROUNDING, 3 CALCULATION, 4 AUDITABILITY, 5 TEMPORAL TRUTH, 6 NO OPINION), `docs/ARCHITECTURE.md` ADR-001…ADR-021, `docs/SPEC_06` §6 ağ kuralı, backend'in bugünkü uçları (28 uç, aşağıda §4.3).

Bu not karar gerekçeli bir sınıflandırmadır; kod içermez. Backend'de değişiklik yapılmadı. AI-BalBal çalıştırılmadı; "çalışıyor" ifadeleri kod okumasına dayanır, çalıştırma kanıtı değildir. Backend tarafı, ürün sahibinin BACKEND_GAPS §1.7.1 soru kuralını kabul eder: aşağıdaki her "karar gerekiyor" satırı bir sorudur, tahminle uygulanmayacaktır.

Kısaltmalar: **kural N** = `CLAUDE.md`'deki N numaralı değişmez kural. **ADR-N** = `docs/ARCHITECTURE.md`. **B-N / P-N / §N** = `BACKEND_GAPS.md`. Satır numaraları o dosyanın 29.09.2026 halidir.

---

## 1. Benimseyeceğimiz talepler ve yöntemi

Bu maddeler mevcut kurallarla ve ADR'lerle çelişmiyor; her biri var olan bir deseni genişletir. Sıra, `BACKEND_GAPS` §12 ile uyumludur; bağımlılığı olanlar belirtilmiştir.

| Kod | Talep | Yöntem (hangi mevcut kod / desen genişletilir) | Bağımlılık |
|---|---|---|---|
| **B-04** | `AskResponse.audit_log_id`; `POST /api/ask/feedback {audit_log_id, rating, comment?}` | `audit_writer.write_audit_row` zaten satırı yazıyor, id'sini döndürmesi yeterli (`services/audit_writer.py`). `audit_log` tablosuna `rating`, `feedback_comment`, `feedback_at` sütunları (migration 0009). Feedback ucu yalnızca satırın `user_id`'si ile eşleşen kullanıcıdan kabul eder; admin listesi (`GET /api/audit-log`) `has_feedback` filtresi alır. ADR-016 korunur: geri bildirim denetim kaydında kalır, retrieval'a ve prompt'a girmez; "eval setini büyütme" (§3.4) admin'in kaydı okuyup soru setine elle eklemesi demektir, otomatik akış yoktur. | Yok |
| **B-07** | `SourceCard`'a `supersedes_document_id` / `superseded_by_document_id` | `services/ask.py` kaynak kartını `load_with_chains` ile yüklenen zincirden kuruyor; ADR-021'e göre zincir **her halkada** `allowed_document_ids` ile kısıtlı yüklenir, görünmeyen komşu hiç yüklenmez. Dolayısıyla id'yi eklemek yetki kontrolünü kendiliğinden taşır: yüklenmemiş komşu → `None`. `schemas/ask.py:31-46`'ya iki alan; `SourceCardList.tsx:38-43`'teki uyarı linke dönüşür. | Yok |
| **B-09** | `users.primary_department_id`, `/me` ve `/login`'de `primary_department_slug` | Migration: sütun + mevcut kullanıcılar için ilk üyelikten backfill. `schemas/auth.py::CurrentUserResponse`'a alan. `api/users.py` create/update'te "ana departman üyeliklerden biri olmalı, management/admin için boş olabilir" doğrulaması. ADR-003 concretization notu. Frontend `Home.tsx:33`, `BalbalChat.tsx:32`, `ShellContext.tsx:19`'daki `department_slugs[0]` varsayımı kalkar. | Yok |
| **B-13** | `file_kind` alanı | `documents.file_name` (migration 0008, ADR-011) ve `storage_path` uzantısı zaten var; `DocumentListItem`/`DocumentDetailResponse`'a türetilmiş `file_kind: pdf\|image\|xlsx\|xlsm\|csv` eklenir, migration gerekmez. `WorkbookInspectCard.tsx:7`'nin her belge için attığı 422 çağrısı kalkar. | Yok |
| **B-17** | İndirme adı belge başlığı + uzantı; `?inline=1` | `api/documents.py:253` `FileResponse(path, filename=path.name)` → `filename=f"{title}.{ext}"`, Starlette `FileResponse`'un `content_disposition_type` parametresiyle `inline`/`attachment` seçimi. Başlıktaki dosya-sistemi-güvensiz karakterler temizlenir. | Yok |
| **B-05** | `users.title`; `GET /api/directory?q=&department=` | Migration: `users.title` (nullable). Yeni uç `api/departments.py` deseniyle (her kimlikli kullanıcı, `get_current_user`), dar şema: `id, display_name, title, department_slug, department_name`. `password_hash`, rol, aktiflik dönmez. `users.manager_id` (§2.3) aynı migration'da eklenebilir, kullanımı B-22'ye kalır. | Yok |
| **B-14** | `GET /api/search?q=` içerik araması | `services/search_query.build_search_query` (ADR-020, sözlük genişletmeli OR sorgusu) + `retrieval.py`'nin FTS bacağı zaten var; `allowed_document_ids` önce (ADR-004). Dönüş: belge + `snippet` + `page_number` (chunk'tan), proje eşleşmesi. `people` kısmı B-05'e bağlı. `SearchPanel.tsx:22-24`'teki istemci tarafı başlık süzmesi yerini alır. | B-05 (people için) |
| **B-20/6** | Tek sohbette çok proje; `project_id` zorunlu değil | Backend'de `AskRequest.project_id` zaten opsiyonel (`schemas/ask.py:28`); değişiklik gerekmez. Ek olarak `SourceCard`'a `project_code`/`project_name` eklenir ki arayüz projeyi `/api/documents` listesinden türetmek zorunda kalmasın (`AskPanel.tsx:21-24`, `BalbalChat.tsx:35-38`). **Uyarı:** proje ayrımı bugün retrieval'da `project_id` filtresi + prompt disipliniyle sağlanıyor (ADR-020/021); filtre kaldırılınca `isolation` eval kategorisi (bugün %75, bilinen sınırlama) daha da zorlanır. Kaldırma kararı eval ile birlikte alınır. Frontend'in kendi içinde tutarsızlık: `AskPanel.tsx:16,31,46-58` hâlâ proje çipi gösterip `project_id` gönderiyor, yalnızca `BalbalChat` göndermiyor. | Yok |
| **B-11** | Evrak talebi, varlık ele vermeden | Bugünkü "bilgi bulamadım" sabit metni (ADR-014, ADR-021: chunk yoksa LLM çağrılmadan döner) zaten belge varlığını ele vermez; bu kısım yapılmış durumda. Yeni: `document_requests(id, from_user_id, to_department_id, description, status)` tablosu + `POST /api/document-requests`; departmanı kullanıcı seçer. Hedef departmanın görmesi B-01 gündemine bağlı. | B-01 |
| **B-01** (ilk kısım) | Gündem: süresi dolacak belgeler | Deterministik SQL: `documents.expiration_date` 60 gün içinde ve `allowed_document_ids` içinde. LLM yok. `GET /api/me/agenda` döner `kind: deadline`. "Onay bekleyen öneri" kalemi B-28 kararına, diğer kalemler B-06a/B-11/B-22/B-23'e bağlı. Ürün 2 kapısı B-25'e bağlı. | B-25 (kapı için) |
| **B-19** | Arayüz incelemesi + tersine liste | Bu not. Tersine liste §4.3'te. | — |
| **B-27** (yalnızca "AI-BalBal'ı sun" kısmı) | Caddy'nin `ftansu/AI-BalBal/frontend` build'ini sunması, tek komutla güncelleme | `infra/caddy/Dockerfile` bugün `./frontend` bağlamından build alıyor (ADR-018). Build bağlamını bir `FRONTEND_DIR` değişkeniyle seçilebilir yapmak ve `make update-frontend` (git pull + build + `up -d caddy`) eklemek küçük iş. Bu kısım LAN'da düz HTTP ile bugün yapılabilir. HTTPS/internet kısmı §3'te. | Yok |
| **B-18** (yöntem olarak) | Demo veri seti genişletme, 15 kişilik personel, kurgu şirket | Mevcut üretim hattı genişletilir: ledger (`seed_data/master/*.yaml`) → `make prose` (LLM bir kez, `[[token]]` ile, rakam görmez) → `generate_documents.py` (deterministik) → `validate_documents.py` → `manifest.json` → `make seed` (ADR-013). Personel listesi ledger'a `personnel` bölümü olarak girer; `demo_users_seed.py` ve `demo_departments_seed.py` ledger'dan okur. Excel seti `generate_excel.py` + LibreOffice recalc hattıyla (ADR-011). **Şirket adı:** ledger'daki "ABC Enerji A.Ş." `USER_FACT` olarak onaylı (Phase 2.1, 23.09.2026); canvas'taki "NATA" ledger'a uydurulur, tersi değil. Her yeni rakam/tarih/isim `AI_ASSUMPTION` etiketiyle girer ve Naci onayı bekler; bu kural ürün sahibinin de kabul ettiği P-9 ile aynı yöndedir. | B-20 (İK belgeleri için) |

Bu tablodaki maddeler için ADR gerekmez; B-04, B-07, B-09, B-13, B-17, B-05 tek bir küçük phase'e sığar ("Balbal cevap döngüsü"). Naci'nin faz planı onayı gerekir; bu not onun yerine geçmez.

---

## 2. Uyarlayarak benimseyeceklerimiz

Talebin özü kabul; şu noktalar değişmeden uygulanamaz.

### B-25 mekanizması — ürün anahtarı (sınıflandırma sorunu §3'te)
- **Kabul:** `company_settings.enabled_products` (tek satır, `text[]`, değerler `P1|P2|P3`), `require_product("P2")` FastAPI bağımlılığı (`require_admin` deseni, `api/deps.py:38`), `enabled_products` hem `/me` hem `/login` cevabında, `set-enabled-products` CLI komutu. Alan adı ve değerler `frontend/src/api/products.ts` ile birebir.
- **Değişmesi gereken:** `AskResponse.product_level` için "bugün her cevap P1" varsayımı (BAGLANTI §2.1/4) yapılamaz; bkz. §3.1. Karar gelene kadar `product_level` alanı eklenmez, yalnızca `enabled_products` ve `require_product` yazılır.

### B-20 (1–5) — departman yapısı
- **Kabul:** Görünen ad değişiklikleri, İK ve Üretim/Piyasa, Mali İşler alt birimleri, `finans` üyelik düzeltmesi. Slug'lar sabit (BAGLANTI §3.1 önerisi doğru).
- **Değişmesi gereken:** Üç yer birlikte değişmek zorunda: Alembic **veri** migration'ı (seed "varsa dokunma" davranışlı, `demo_departments_seed.py:49`), seed dosyası ve ledger (`seed_data/master/company.yaml` departmanları slug olarak taşır, ADR-013; `validate_ledger` slug'ları denetler). BAGLANTI ilk ikisini görmüş, ledger'ı görmemiş. Ayrıca `search_glossary.py`'de departman adı geçen bir sözlük satırı yok, o tarafta iş çıkmaz. `README.md`'deki demo hesap tablosu güncellenir.

### B-08 — departman yöneticisi rolü
- **Kabul:** Kural yalnızca `allowed_document_ids` içinde (P-2 = ADR-004). Önerilen iki seçenekten **rol** (`UserRole.department_manager`) tercih edilir: `user_departments.max_confidentiality` alternatifi, gizlilik kararını üyelik satırına dağıtır ve `SingleDocumentIdsProvider` (`authorization.py:84-110`) ile "kim görebilir" ucunu ikinci bir kural kaynağına bağlar.
- **Değişmesi gereken:** `user_role` Postgres enum'una değer eklemek migration ister; `ROLE_LABELS`/`ROLE_VALUES` (frontend `lib/format.ts`) ve `UserForm` ürün sahibi tarafında güncellenir. ADR-004'e concretization satırı. "Departman müdürü kendi departmanının `restricted` belgelerini görür, `board` görmez" varsayımı ürün sahibince teyit edilmeli; §2.4 yalnızca `restricted` diyor.

### B-26 — klasörler ve departman erişim yetkileri
- **Kabul:** `folders`, `folder_grants`, `documents.folder_id`; yetki yalnızca gate içinde; her belge tek klasörde ve belgenin `department`'ı klasörün sahibi departmanı (ADR-004'ün "yetki departmandan gelir" ilkesi korunur); yetki kaldırılınca anında geçerli (gate her istekte hesaplanır, ek iş yok); `SingleDocumentIdsProvider` aynı kuralı taşıdığı için "kim görebilir" ucu tutarlı kalır.
- **Değişmesi gereken:**
  1. `DocumentIdsProvider` protokolüne Phase 1.2'deki gibi bir metot eklenir (`list_document_ids_for_folder_grants(department_slugs, confidentiality_levels)`); `allowed_document_ids`'in `employee` dalı üyelik ∪ klasör-grant birleşimini alır. Bu bir **ADR** ister (ADR-004'ün superseding değil, concretization'ı; imza değişmez).
  2. Yetki değişikliği geçmişi (`§2.6.1/8`) `audit_log`'a **yazılmaz**; o tablo soru-cevap kaydıdır (ADR-016, satır başına bir `/api/ask`). Ayrı `folder_grant_events` tablosu; `GET /api/admin/folders/audit` oradan okur.
  3. `POST /api/documents/upload` `folder_id` alır ve `write` yetkisi yoksa 403 döner. Bu, bugün her iki repoda da bulunan **yazma tarafı yetki boşluğunu** kapatır: `api/documents.py:113` yüklemeyi her kimlikli kullanıcıya açıyor, `:137-138` departman slug'ını yalnızca "var mı" diye kontrol ediyor; Enerji çalışanı `department=finans` ile belge yükleyebilir ve o belge Finans kullanıcılarının Balbal cevaplarına kaynak olur. Kural 1 okumayı korur, yazmayı korumaz. B-26 gelene kadar ara düzeltme olarak "yüklenen belgenin departmanı ⊆ yükleyenin üyelikleri (management/admin hariç)" kuralı önerilir; kararı Naci verir.
  4. `documents.department` FK'sız serbest string (ADR-004 Phase 1.2 notu) klasör sahibiyle çift kaynak olur; ADR'de "klasörün `owner_department`'ı belirleyici, `documents.department` ondan türetilir" yazılmalı.

### B-03 — sohbet geçmişi ve çok turlu soru
- **Kabul:** `ask_conversations` / `ask_turns` ayrı tablolar, kullanıcıya özel, 90 gün, retrieval'a girmez (ADR-016 ile aynı disiplin; temizlik döngüsü paylaşılır). Her turda retrieval yeniden `allowed_document_ids` üzerinden.
- **Değişmesi gereken:** "Önceki turun sorusu sınıflandırıcıya bağlam olarak verilir" (§3.2) router prompt'unu değiştirir (`services/router.py`, kopyası `docs/prompts/ROUTER_PROMPTS.md`, `make lint` eşitliğini denetler). Phase 5.1b'de Naci prompt ayarını bilinçli olarak dondurdu (isolation/temporal bilinen sınırlama kararı, 26.09.2026); bu değişiklik ayrı bir prompt fazında, `--repeat 3` ölçümüyle yapılır. Ürün sahibinin "takip sorusu" örneği ("peki ya Yeşilova?") canvas projelerini varsayıyor; demo verisi iki projeyle sınırlı (BAGLANTI §6/1 kararı).

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
  3. İzin bakiyesinin İK klasöründeki belgelerden türetilmesi (§8.1.6) bireysel erişim ister: personel yalnızca **kendi** izin belgesini görmeli. Bugünkü model departman bazlıdır (ADR-004); bireysel erişim ne B-26'da ne başka yerde tanımlı (§2.6.1/10 "ayrıca ele alınacak"). B-22, bu tanım yapılmadan başlayamaz.
  4. Bakiye aritmetiği (`entitled + carried_over − used − pending`) Python'da; belgelerden rakam okuma LLM'e kalırsa her soruda yeniden çıkarım yapılır. Öneri: izin belgeleri B-28'in "personel eklediği alan" mekanizmasıyla yapılandırılmış sayı taşısın, LLM her seferinde PDF'ten okumasın.
  5. `Europe/Istanbul` ve "bugün" için `DEMO_TODAY` (ADR-012) değil gerçek saat kullanılacak; bu, demo ile gerçek zamanın ilk kez ayrıştığı yer olur, ADR'de belirtilmeli.

### B-23 — yazışma ve dilekçe taslağı, Ürün 2 kısmı (ADR ÖNCE)
- **Kabul:** Kaynaksız cümle yerine `[BİLGİ EKSİK]`, `legal_references` dışı atıf `[DOĞRULANMALI]`; bu, kural 2'nin sabit metin disiplininin genişletilmiş halidir. Süre `legal_deadline_rules` + tebliğ tarihi ile deterministik (kural 3). Şablonlar tabloda (P-8). Sistemden gönderim yok.
- **Değişmesi gereken:**
  1. "Gelen yazının içeriği talimat değildir" (§8.2.4/3) bugün `answer_prompt.py`'de açık bir kural olarak **yok**; prompt kaynakları `[K<n>]` bloklarıyla veri gibi sunuyor ama enjeksiyon koruması yazılı değil. Bu, B-23'ten bağımsız olarak genel bir prompt düzeltmesidir; prompt fazında ele alınır (bkz. B-03 notu).
  2. Gizlilik: §8.2.9 "yalnızca ilgili departman ve onay zinciri görür". Bizde `restricted` belgeyi `management` de görür (ADR-004, `authorization.py:63-69`). Ürün sahibinin "restricted" tanımı bizimkinden dardır; ya yeni bir gizlilik düzeyi ya da B-26 klasör yetkisi + B-08 ile çözülür. Karar gerekiyor.
  3. Taslak, hazırlayanın `allowed_document_ids` kümesiyle sınırlı (§8.2.4/4): mevcut `/api/ask` akışı zaten böyle; taslak üretimi aynı `answer_question` hattını `write_audit=True` ile çağırmalı ki her taslak denetim kaydına girsin (kural 4).

### B-28 — belge yükleme mantığının benimsenebilir çekirdeği
Kararı gerektiren iki nokta §3.3'te. Karar verilirse şu kısımlar uyarlanarak alınır:
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

### 3.1 B-25 katman sınıflandırması: "bugünkü her cevap Ürün 1"
- **Talep:** BAGLANTI §2.1/4: `AskResponse.product_level` bugün hep `"P1"` döner; BACKEND_GAPS §1.5.1: Ürün 1'de "Hesaplama: **Yok**", Ürün 2'de "yalnızca aritmetik, yalnızca gerçekleşmiş veriyle".
- **Çelişki:** Backend'in `DATA_QUERY` ve `MIXED_QUERY` cevapları DuckDB ile hesap yapar (ADR-010, ADR-011; `services/excel_ask.py`, `dscr`, `outstanding_debt`, `budget_variance`, `capacity_factor`, `production` fonksiyonları). Ürün sahibinin tablosuna göre bu Ürün 2 yeteneğidir. İkisi aynı anda doğru olamaz: ya bu cevaplar `P2` etiketlenir ve yalnızca-P1 müşteride `require_product("P2")` ile kapanır, ya da §1.5.1 tablosu "Ürün 1: kesin veriyle aritmetik dahil" diye düzeltilir. Arayüzdeki örnek sorular (`strings.ts:49` "Ankara RES 2026 Q2 DSCR kaç?") ve eval setinin `data`/`mixed` kategorileri (`questions.json`) bu karara bağlı.
- **Ek belirsizlik:** `GENERAL_QUERY` ("DSCR ne demek?", şirket verisi kullanmaz, ADR-010) hiçbir katmana atanmamış.
- **Açılma koşulu:** Ürün sahibinin tek cümlelik kararı. Karar gelene kadar `product_level` alanı yazılmaz; `enabled_products` ve `require_product` (§2) yazılabilir.

### 3.2 B-27 internet'e açık HTTPS test ortamı
- **Talep:** §1.8.1/1 "sabit web adresi ve HTTPS", §1.8.1/4 "ortam internete açık".
- **Çelişki:** `CLAUDE.md` stack kararı "V0'da LAN üzerinde düz HTTP", kapsam dışı listesi "HTTPS/Tailscale (V0 sonrası)"; ADR-015 "Network: LAN only, plain HTTP … V0"; `docs/SPEC_06` §6 "V0 internete açık değildir … Public WAN exposure yok". Üç belge aynı şeyi söylüyor; bu bir V0 kapsam kararıdır, teknik zorluk değildir.
- **Açılma koşulu:** Naci'nin V0 kapsamını değiştirmesi (ADR-015 superseded) **veya** ürün sahibinin LAN/VPN erişimini kabul etmesi. Öneri: Tailscale/WireGuard ile ürün sahibinin VM'e LAN gibi ulaşması; bu, CLAUDE.md'nin "V0 sonrası" dediği Tailscale'i öne çeker ama WAN'a açmaz ve TLS'siz cookie riskini (ADR-003 `secure=false`) yalnızca VPN içinde tutar. "AI-BalBal'ı Caddy'den sunma" kısmı §1'de kabul edildi; bu kısım ondan bağımsızdır.

### 3.3 B-28'in iki kararı: onay yetkisi ve onaysız belgenin görünmezliği
- **Talep 1 (§4.7.5, §4.2 güncellemesi):** Etiket önerisini **yükleyen personel** onaylar.
- **Çelişki:** Phase 3.2 planında SORU 2 (`docs/plans/PHASE_3_2_PLAN.md:207-209`) tam bu soruyu sordu: "yalnızca admin mi, yükleyen de mi?" Naci "admin" dedi; `api/documents.py:337` ve `:380` buna göre `require_admin`. B-28 bu kararı tersine çevirir. Tersine çevirmek mümkündür, ama Naci'nin açık kararıyla ve `docs/PHASES.md`'ye "Phase 3.2 SORU 2 kararı B-28 ile değiştirildi" notuyla; sessiz değişiklik olmaz. Ayrıca yükleyen onayı, §3'teki yazma boşluğuyla birleşince (herkes her departmana yükleyip kendi onayıyla yayınlar) riski büyütür; B-26 yazma yetkisi veya ara düzeltme **önce** gelmeli.
- **Talep 2 (§4.7.5 son madde):** "Onaylanmamış belge ne aramada ne Balbal'ın cevaplarında yer alır."
- **Çelişki:** Bugün belge `ready` olduğu anda `allowed_document_ids` içindedir ve retrieval'a girer (ADR-006, ADR-021); metadata önerisi belgenin görünürlüğünü etkilemez (SPEC_02 §4: "kullanıcı kabul/düzenleyene kadar belge metadata'sı değişmez", görünürlük değil). B-28 bir **yayın durumu** ekler. Bu yalnızca `allowed_document_ids` içinde uygulanabilir (P-2 = ADR-004), yani gate'e `documents.published` benzeri bir koşul girer ve `SingleDocumentIdsProvider`, eval seed'i (`make seed` sonrası 74 belgenin hepsi yayınlanmış olmalı) ve mevcut testler etkilenir. Yapılabilir; ama "ürün kararı" olduğu için Naci onayı ve ADR-004 concretization ister. Kendi başımıza uygulamayız.

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
- **Doküman düzeyinde iki risk (kod değil):** (1) P-1…P-10 arasında "LLM hesap yapmaz" ilkesi yok; kural 3'ün karşılığı yalnızca dağınık notlarda (§8.1.2, §8.2.5). Öneri: **P-11** olarak eklensin ki iki repo arasında sözleşme olsun. (2) §8.1.2 örnek diyalogda Balbal "kalan yıllık izniniz 11 gün görünüyor" diyor; bu sayı kodun ürettiği bir alan olmalı, LLM'in cümlesi değil. Metin bunu satır 837'de söylüyor; sözleşmede `LeaveBalance.remaining_estimated` alanı var (`proposed.ts:324`); tutarlı, ama ADR'de "cevaptaki her sayı bir alan adından gelir, modelden değil" diye yazılmalı (ADR-011'in "final number never comes from the model" cümlesinin izin akışına taşınması).
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
| `GENERAL_QUERY` | Rozet "Genel bilgi" (warn); `notice` gizli çünkü cevap aynı cümleyle başlıyor (`AnswerView.tsx:36`); kaynak listesi gizli | Gösteriliyor | — |
| `answered=false` sabit metin (ADR-014) | Gri cevap + "belge yükleyebilirsiniz" linki (`AnswerView.tsx:34,37-42`) | Gösteriliyor | Link yalnızca `uploadPath` varsa; birden çok departmanlı kullanıcıda ilk departmana gider |
| `notice` (yorum içermez) | `AnswerView.tsx:36` | Gösteriliyor | — |
| `model`, `tokens_in`, `tokens_out` | company-ai `AskPanel.tsx:80-84` gösteriyordu; AI-BalBal `AnswerView` **göstermiyor** | Kaldırılmış | P-7 sadelik kararı olabilir; denetim kaydında duruyor (kural 4 korunur). Bilinçli olduğu teyit edilmeli. |
| `retrieved_document_ids` | Kullanılmıyor | — | Gerekmez (eval/test alanı) |
| Denetim kaydı listesi + detay (ADR-016) | `AdminAuditLogPage.tsx` company-ai kopyası | Gösteriliyor | Detayda `sources` `JSON.stringify` ile ham; `chunks_retrieved` ve `documents_retrieved` **gösterilmiyor**; `rating` sütunu B-04 ile gelir |
| Geri bildirim | `AnswerView.tsx:61-91` butonlar var | UI hazır, backend yok | `audit_log_id` (B-04) |
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
| Balbal cevabı | `AskResponse.audit_log_id` (geri bildirim), `product_level` (karar sonrası), `conversation_id` (B-03) | B-04, B-25, B-03 |
| Balbal cevabı | `model` ve token sayısının bilinçli kaldırıldığının teyidi | P-7 |
| Belge listesi / detayı | `file_kind`; indirme adı; `?inline=1` | B-13, B-17 |
| Belge detayı versiyon linkleri | Link metni belge başlığı | — |
| Departman "Balbal'a Sor" sekmesi | `project_id` çipi kaldırılsın ya da belge güncellensin (`AskPanel.tsx:16,31`) | §1.4/1, §3.3 |
| Denetim kaydı detayı | `chunks_retrieved` (belge, sayfa, sıra) ve `documents_retrieved` gösterimi; `rating` sütunu | ADR-016, B-04 |
| Üst bar arama | `/api/search` snippet + sayfa; `/api/directory` | B-14, B-05 |
| Kullanıcı menüsü, üst bar | `primary_department_slug`, `title` | B-09, §2.3 |
| Yükleme | `folder_id` (B-26 sonrası), `department` seçiminin yükleyenin yetkisiyle sınırlanması | §2, B-26 |
| Yönetim › Kullanıcılar | `department_manager` rolü (B-08 sonrası), `title`, `manager_id`, ana departman | B-08, B-09, §2.3 |

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
- `AskPanel.tsx:16,31,46-58` proje çipi ve `project_id`; belge "kaldırıldı" diyor (§1.4/1, §3.3).
- `BalbalChat.tsx:32` çalışan kapsamını `department_slugs[0]`'a daraltıyor; iki üyelikli demo `finans` kullanıcısı Balbal'da `mali_isler` belgelerini görmez. B-09 ve B-20/5 ile çözülür; o güne kadar bilinen fark.
- `proposed.ts:18` 404'ü "henüz yok" sayıyor; uçlar açıldığında gerçek "bulunamadı" 404'ü de "Backend bekleniyor" görünür. Öneri: "henüz yok" için 501, 404 anlamını korur.
- `types.ts` şemaları elle aynalanıyor; backend `/openapi.json` üretiyor. ~40 yeni uçla el ile senkron kırılır; TS tip üretimi (openapi-typescript) önerilir. Bu, ürün sahibi tarafının kararıdır.
- Test yok, CI yok; yalnızca `tsc` + `eslint`. README'deki "Çalışıyor" ifadeleri elle test iddiasıdır. company-ai'ın kendi frontend'inde de UI testi yok (CLAUDE.md, ADR-019), backend 383 test taşır.
- 28 dosya company-ai `frontend/` ile bayt bayt aynı (Phase 5.2 yönetim ekranları dahil). B-27 §1.8.1/2 "backend reposundaki frontend testte kullanılmaz" diyor; company-ai `frontend/`'inin kaderi (emekli / senkron) Naci'nin kararıdır ve bu notun dışındadır.

---

## Karar bekleyen maddeler (özet, ürün sahibi ve Naci)

1. §3.1 — DuckDB hesaplı `DATA`/`MIXED` cevapları Ürün 1 mi Ürün 2 mi? `GENERAL` hangi katman?
2. §3.2 — B-27 için internet/HTTPS mi, VPN/LAN mı? (V0 kapsam kararı, Naci)
3. §3.3 — B-28: Phase 3.2 SORU 2'nin tersine çevrilmesi ve "onaysız belge görünmez" yayın durumu. (Naci)
4. §2 B-26/3 — B-26 gelene kadar yüklemede departmanın yükleyenin üyelikleriyle sınırlanması. (Naci)
5. §2 B-08 — rol mü, üyelik alanı mı; müdür `board` görür mü?
6. §2 B-02 — "departmana belge yüklendi" bildiriminin alıcısı kim?
7. §2 B-06a — görüş talebi belgesinin departmanı ve gizliliği.
8. §2 B-23/2 — "yalnızca ilgili departman görür" için yeni gizlilik düzeyi mi, klasör yetkisi mi?
9. §3.9 — P-11 "LLM hesap yapmaz" ilkesinin BACKEND_GAPS'a eklenmesi.
10. §4.1 — `model`/token bilgisinin arayüzden kaldırılmasının bilinçli olduğu.
11. Genel — `BACKEND_GAPS.md` ile `CLAUDE.md`/`PHASES.md` çelişirse öncelik; ilk backend fazının bağlanacağı BACKEND_GAPS sürümü (iki günde v5→v7.9).

Backend tarafı bu cevaplar gelmeden §3'teki hiçbir maddeye kod yazmaz; §1'deki maddeler Naci'nin faz planı onayıyla başlar (`CLAUDE.md` çalışma biçimi 2–3).
