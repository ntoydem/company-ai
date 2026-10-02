# SPEC 02 — Doküman, metadata, yetki ve kullanıcı deneyimi

## 1. Doküman yükleme
Ana yöntem web uygulaması. Form alanları: Departman, Alt departman (varsa), Proje, Belge Türü, Muhatap, Belge Tarihi, Gizlilik, dosya. Yükleme sonrası AI önerisi (SPEC 02 §4) kullanıcıya gösterilir; kullanıcı kabul eder veya düzeltir.
Consume klasörü V0 dışı. Kabul edilen türler: `.pdf .xlsx .xlsm .csv` (+ `.png/.jpg` taranmış belge). MIME doğrulaması zorunlu. `.xlsm` macro asla çalıştırılmaz.

## 2. Metadata modeli (backend Postgres, master)
Zorunlu: `title, department, subdepartment, project_id, document_type, counterparty, document_date, status, confidentiality, tags, source(web|consume), created_at, updated_at`.
Temporal: `effective_date, expiration_date, version, revision, supersedes_document_id, superseded_by_document_id, related_document_ids`.
Sistem: `storage_path, ingestion_status(uploaded|ocr|ready|failed), ingestion_error, uploaded_by, ai_suggestion_id, page_count`.
Ek alanlar (B-28b, 02.10.2026, ADR-025): `extra_fields` JSONB — türe göre değişen olgular (`parties`, `licence_no`, `period`…), anahtar `snake_case`, en fazla 20, yalnızca metin; `source: ai|user`. `tags` yalnızca şirketin etiket kataloğundan (`tag_catalog`, admin yönetir; `identity | change` türleri).
`status` değerleri: `draft | executed | amended | superseded | active`. `confidentiality`: `normal | restricted | board`.
Sayfa tablosu (`document_pages`): `document_id, page_number, text`. Chunk tablosu (`document_chunks`): `id, document_id, chunk_index, page_number (DOLU), text, tsv, embedding (NULL, pgvector)`.

## 3. Dosya isimlendirme
Gerçek kullanıcı için zorunlu standart yok; sınıflandırmanın kaynağı metadata'dır. **Dosya adı primary information source olarak kullanılmaz.** Synthetic belgeler için: `YYYY-MM-DD_PROJECT_DOCUMENT_VERSION_STATUS.pdf`, örn. `2024-07-21_ANK_RES_Facility_Agreement_V02_EXECUTED.pdf`.

## 4. AI metadata önerisi
Upload sonrası `LLM_MODEL_CLASSIFY` ile: departman, alt departman, proje, belge türü, muhatap, belge tarihi, durum, gizlilik, etiketler; her alan için confidence. Öneri ayrı tabloda (`document_metadata_suggestions`); kullanıcı kabul/düzenleyene kadar belge metadata'sı değişmez. Kritik alanlar sessizce overwrite edilmez. Öneri üretimi başarısız olursa upload yine başarılıdır.

**Yayın durumu ve iki aşamalı onay (B-28, 02.10.2026, ADR-024):** `documents.review_status` (`pending_metadata | pending_review | changes_requested | approved`). Yalnızca `approved` belge aramaya, Balbal'a ve Excel kataloğuna girer. Belgenin hedef departmanının kendi `department_manager`'ı yüklerse belge anında yayınlanır; diğer herkes (personel, `management`, `admin`, başka departmanın müdürü) iki aşamadan geçer: (1) **yükleyen** `POST /api/documents/{id}/submit` ile nihai metadata'yı onaylar — güveni `METADATA_CONFIRM_THRESHOLD` (0.8) altındaki öneri değeri `confirmed_fields`'ta açıkça onaylanmadan kaydedilmez (422); (2) hedef departmanın müdürü `POST /api/documents/{id}/review` ile `approve` ya da yorumlu `request_changes` verir. Onaycısı olmayan departmana yükleme 409 `approver_not_configured` (dosya yazılmaz). Onaylı belgenin metadata'sı değişirse onay düşer (müdürün kendisi hariç). Kayıt defteri `document_review_events`, yalnızca admin okur.

**Etiket kataloğu ve tür rehberi (B-28b, 02.10.2026, ADR-025):** etiket **katalogdan** gelir (katalog dışı 422 `unknown_tag`; AI'nın önerdiği katalog dışı etiket düşer ve öneride `tags.dropped` olarak görünür); kataloğu müşteri admin'i büyütür/emekli eder (`/api/admin/tags`). Belge türü **ailesi** için rehber (`document_type_guide`: önerilen ek alanlar, etiketler, vurgulanan standart alanlar, prompt ipucu) sınıflandırıcıyı ve yükleme ekranını yönlendirir; **zorunlu form değildir**. Personelin açtığı ek alan `field_added` olayıyla ayrışır; `GET /api/admin/document-type-guide/signals` hangi ailede hangi anahtarın sık eklendiğini gösterir — rehberi insan günceller. Yapılandırma değişiklikleri `admin_events`'e yazılır.

## 5. Roller ve yetki
Roller: `admin | management | department_manager | employee`. Kullanıcı bir veya daha fazla departmana üye olur (`user_departments`).
Kurallar:
- `employee`: yalnızca üye olduğu departmanların `normal` belgeleri.
- `department_manager` (B-08, 02.10.2026): üye olduğu departmanların `normal` + `restricted` belgeleri (klasör yetkileriyle de aynı iki seviye); `board` **görmez**, başka departmanı görmez. Rolü kişiye admin verir; kural sabittir, tablo değil.
- `management`: tüm departmanlar, `normal` + `restricted` + `board`.
- `admin`: her şey + yönetim işlemleri.
- Bir proje birden fazla departman tarafından kullanılabilir; belgenin yetkisi departmandan gelir, projeden değil.
Authorization **tek bir serviste** (`allowed_document_ids`) ve **backend'de** uygulanır; frontend gizleme güvenlik değildir. Adım 0'da bu fonksiyon tüm belgeleri döndürür (tek admin), Adım 1'de doldurulur; kod yolu baştan vardır.
AI sorgu sırası: AUTHORIZATION → allowed document ids → retrieval → LLM. Yetkisiz belge içeriği LLM'e hiçbir yolla gitmez.

Demo hesapları: `admin` (admin), `yonetim` (management), `finans` (employee: finance + accounting), `hukuk` (employee: legal), `enerji` (employee: energy/*; finans erişimi YOK — güvenlik testlerinin ana hesabı), `finans_mudur` (department_manager: finans — tek `restricted` demo belgeyi görür, B-08).

## 6. Proje yönetimi
Projeler hard-code edilmez. Admin: oluştur, düzenle, aktif/pasif. Alanlar: `id, name, code (ANK_RES, IZM_RES), stage (development|construction|operation), is_active, department_ids`.

## 7. Auth
JWT, httpOnly + SameSite cookie, 8 saat; Argon2 hash; basit login rate limit. `auth_provider` (`local`) ve `external_id` alanları ileride SSO için hazır, V0'da kullanılmaz.

## 8. Ana UI
- Giriş.
- Ana sayfa: departman kartları (ENERJİ GRUBU, FİNANS, HUKUK, MALİ İŞLER, İDARİ İŞLER) + **Genel Sor** (yetkilerin izin verdiği her şeyde arar).
- Enerji: GELİŞTİRME / EPC-İNŞAAT / BAKIM alt kartları.
- Departman ekranı: AI'ya Sor (o departmanla filtreli) / Belgeler / Belge Yükle / Projeler.
- Sor ekranı: soru, cevap, kaynak kartları (belge adı, sayfa, tarih, versiyon, proje, section; Excel için dosya/sheet/range). Cevap yorum/görüş içermez (kural 6); kullanıcıya bu kısaca belirtilir.
- Sade, profesyonel, hızlı, responsive. Tasarım süsü değil, okunabilirlik.

## 9. Soru-cevap akışı
1. Yetki kontrolü → izinli document id kümesi.
2. Proje/departman filtresi (scope veya sorudan çıkarım).
3. Retrieval (FTS + metadata; embedding açıksa hibrit) → chunk'lar.
4. Versiyon/tarih değerlendirmesi: `supersedes` zinciri, `effective_date`, `document_date`, `DEMO_TODAY`.
5. "Güncel" soruları → zincirin son halkası; "ilk/tarihsel" soruları → ilgili eski belge (eski ≠ yanlış).
6. Yalnızca kaynaklardan cevap; her cevapta kaynak listesi.
7. Kaynak yoksa standart "bilgi bulamadım" cevabı.
Örnek: "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → güncel değer + "Bu değer Amendment 01 ile önceki X seviyesinden değiştirilmiştir." + Kaynaklar: Facility Agreement — EXECUTED; Amendment 01 — tarih.

## 10. Zorunlu kaynak gösterme
Belge cevabı: belge adı, **sayfa numarası**, tarih, versiyon, proje, ilgili section. Excel cevabı: dosya, sheet, range. Kaynaksız factual şirket cevabı verilmez.

## 11. Temporal reasoning ve versiyon zinciri
Örnek: Initial Licence 80 MW, Licence Amendment 02 100 MW → "Güncel kapasite?" 100 MW; "İlk lisans kapasitesi?" 80 MW. Zincir: `DRAFT → V01 → V02 → EXECUTED → AMENDMENT 01 → AMENDMENT 02`; içerik değişimleri gerçek (dosya adı değil). Sonraki belgeler güncel şartlarla uyumlu.

## 12. Belge ilişki grafı
Licence → Technical Report → EPC Contract → Financial Model → Facility Agreement → Board Resolution → Insurance → Construction → Commissioning → COD → Operation. Kapasite, tarih, şirket, kredi tutarı, COD, sözleşme bedeli, SPV adı ilgili sonraki belgelerde tutarlıdır. `related_document_ids` ile bağlanır.

## 13. Hata mesajları
Kullanıcı stack trace görmez. Örn.: "Belge işlenirken bir hata oluştu." Backend structured error log yazar (request id ile).
