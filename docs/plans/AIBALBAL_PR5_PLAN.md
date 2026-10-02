# AI-BalBal PR-5 — B-28b arayüzü (`feat/b28b-arayuz`) — Uygulama Planı

**Tarih:** 02.10.2026 · **Durum:** **UYGULANDI** — Naci 6 SORU'yu planın önerisiyle onayladı; PR #5 açıldı (https://github.com/ftansu/AI-BalBal/pull/5, `feat/b28b-arayuz` @ `1d4cca2`, merge edilmedi); rapor `docs/reports/AIBALBAL_PR5_REPORT.md` · **Hedef repo:** `ftansu/AI-BalBal` · **Dal:** `feat/b28b-arayuz` (`main@b709f09`'dan; PR-4 `feat/ux-kucuk-duzeltmeler`'den **bağımsız**, bkz. §7) · **Teslim:** PR → Tansu inceler, merge kararı onun; main'e push yok (T-14) · **Ürün:** Ürün 1 — Tanıma (Ek-B: "belgeleri sınıflandırır, indeksler"; Ek-D S-6 belge girişi; Çekirdek O-1 Onaylı Belge)

Kaynak: company-ai ADR-025 + `docs/reports/B28B_REPORT.md` (backend uçları ve sözleşme), NOT §2 B-28 "PR-5 to-do" (etiket seçici katalogdan, 1. aşama panelinde ek alan satırları + "alan ekle", tür rehberi ipuçları, Yönetim › Etiketler ve Tür rehberi sayfaları, arama sonucunda `matched_on` rozeti); BACKEND_GAPS §4.7.3 (personel alan ekler, "personel ekledi" ayrışır), §4.7.4 (etiket az ve tutarlı, listeden), §4.7.7 (ekrana iç açıklama konmaz), §4.7.9/2 (etiket listesi ve rehberi ürün sahibi tamamlar → artık admin ekranından); AI-BalBal `main@b709f09`: `components/MetadataSuggestionPanel.tsx` (PR-2 `mode` yapısı, `suggestion-row`, güven çubuğu, `needs-confirm`), `components/shell/SearchPanel.tsx` (`search-row`, `badge`), `pages/admin/AdminFoldersPage.tsx` (`folder-layout` sol liste + sağ kart, `chips` görünüm değiştirici, `access-matrix` tablo, satır içi `NewFolderForm`, `FolderHistory`), `pages/admin/AdminUsersPage.tsx` + `components/UserForm.tsx` (tablo + satır içi form), `api/users.ts` (CRUD deseni), `AdminLayout.tsx` (3 sekme), `router.tsx`.

---

## 0. Çerçeve

- **Backend sözleşmesi (hazır, company-ai `75234e6`):** `GET /api/tags` (aktif), `GET/POST/PATCH /api/admin/tags`; `GET /api/document-type-guide` (aktif aileler), `GET/POST/PATCH /api/admin/document-type-guide`, `GET …/signals`; `GET /api/admin/events?kind=`; `DocumentDetail.extra_fields {key: {value, source, confidence, added_by_id, added_at}}`; `submit`/`apply`/`PATCH` gövdesinde `extra_fields {key: value|null}`, `tags` katı (422 `unknown_tag` + `unknown`), 422 `invalid_extra_fields`, `low_confidence_not_confirmed.fields` artık `extra_fields.<key>` içerebilir; öneri `fields.extra_fields` + `fields.tags.dropped`; `SearchDocumentHit.matched_on`.
- **Anayasa:** T-11 Ürün 1; T-12 yeni görsel öğeler "tasarım onayı bekliyor" (§6); Ç-16 yalnızca bu kapsam; Ü-10 sadelik (gereksiz olanı gösterme: `prompt_hint` kullanıcıya **gösterilmez**, yalnızca admin düzenler — §4.7.7); yetki sunucuda, arayüz yalnızca kime ne göstereceğini seçer.
- **Tasarım dili:** yeni bileşen dili yok — `chip`/`chips`, `badge`, `suggestion-row`, `inline-check`, `card`, `table-wrap`, `folder-layout`, `form-grid`, `Modal`. CSS: en fazla 3 kural (seçili etiket çipi vurgusu, ek alan satırı "anahtar" girişi, sinyal tablosu) — §6'da listelenir.

## 1. Etiket seçici (`MetadataSuggestionPanel`, uploader + admin modları)

- **Veri:** yeni `api/tags.ts` → `useTags()` (`GET /api/tags`, `staleTime` 5 dk), `useAdminTags()`, `createTag`, `updateTag`, `TAGS_KEY`.
- **Bugünkü hâl:** `tags` satırı serbest virgüllü metin (`renderInput` → `<input type="text">`). **Yeni:** `tags` satırında metin yerine **çip seçici** (`TagPicker` bileşeni): aktif katalog çipleri; seçili = `chip active`; `kind=change` çipleri ayrı grupta ("Değişiklik etiketleri") ve yalnızca belgenin ailesi `amendment` ise açık, diğer ailelerde katlanmış ("göster") — §4.7.4 "yalnızca başka belgeyi değiştiren belgelerde" (SORU 1). Önce rehberin `suggested_tags`'i ve AI'nın önerdiği etiketler (zaten katalog süzgeçli) işaretli gelir.
- **Katalog dışı giriş engeli:** serbest metin kutusu **yok** → istemci katalog dışı etiket gönderemez; sunucu 422 `unknown_tag` yine `ErrorBox` ile görünür (katalog bu arada değiştiyse). AI'nın katalog dışı önerdiği etiketler (`fields.tags.dropped`) uploader'a **gösterilmez** (§4.7.7 — kullanıcıya iç bilgi yok), **admin** modunda küçük not: "Balbal şunu da önerdi, katalogda yok: …" + Yönetim › Etiketler linki (admin isterse kataloga ekler; büyüme insan kararı).
- `buildBody` `tags` → seçili slug listesi; readonly modda etiketler `badge neutral` çipler olarak okunur.

## 2. Ek alan satırları + "alan ekle"

- **Konum:** uploader modunda 9 standart satırın altında **"Ek alanlar"** alt başlığı; admin modunda da (admin `apply`/`PATCH` ile ek alan yazabilir); readonly modda değerler salt okunur.
- **Satır kaynakları (birleşik, anahtara göre tek satır):** (a) AI önerisi `fields.extra_fields[key]` → değer + güven çubuğu + `<0.8` ise "Onaylıyorum" kutusu (mevcut `needsConfirm` mantığı `extra_fields.<key>` anahtarıyla); (b) belgenin mevcut `extra_fields` (sonradan açılan belgede) → değer dolu, kaynak rozeti `source` (**"Balbal"** / **"personel"**, `badge neutral`); (c) rehber ailesinin `suggested_extra_fields` → **boş** satır, etiket (`label`) ve ipucu (`hint`) placeholder olarak, "önerilen" küçük işaret; (d) kullanıcının **"+ Alan ekle"** ile açtığı satır: anahtar girişi (serbest; yazarken normalize önizleme `Sözleşme Bedeli → sozlesme_bedeli`, boş/geçersizse düğme kapalı) + değer girişi.
- **Sınır:** sayaç **"n / 20"** alt başlığın yanında; 20'de "+ Alan ekle" kapalı ve kısa açıklama; boş değerli satırlar gönderilmez (sayılmaz). Satır silme "×": mevcut anahtar için gövdeye `null` (kaldırma), yeni satır için yalnızca UI'dan düşer.
- **Gönderim:** `buildBody` → `extra_fields: {key: value|null}`; `confirmed_fields` `extra_fields.<key>` biçiminde; 422 `low_confidence_not_confirmed.fields` içindeki `extra_fields.*` anahtarları ilgili satırları `needs-confirm` ile vurgular (mevcut `serverFlagged` genişler); 422 `invalid_extra_fields` → `ErrorBox` (sunucu mesajı).
- **Olay şeffaflığı:** gönderimden sonra durum satırında ek alan sayısı ("3 ek alan kaydedildi"); defterdeki `field_added` yöneticide zaten görünüyor (`ReviewEventsCard`), etiket "Alan eklendi (personel)" — `REVIEW_EVENT_LABELS.field_added` eklenir.

## 3. Rehber ipuçları

- **Veri:** `api/guide.ts` → `useGuide()` (`GET /api/document-type-guide`), admin hook'ları (§4); `lib/typeFamily.ts` — backend `type_family.match_family` ile **aynı kural** (en uzun eşleşen desen; Türkçe İ katlama) istemcide; birim testi yok (repo'da test altyapısı yok), kural küçük.
- **Yükleme formunda (`UploadTab`):** "Belge türü" alanı yazılırken altında tek satır: *"Bu tür için genellikle: Yürürlük tarihi, Muhatap"* (`standard_fields_emphasis` → Türkçe etiketler) ve ilgili standart alan etiketlerinin yanında küçük "önemli" işareti. Zorunluluk **yok** (Naci SORU 3 — form bloke edilmez).
- **1. aşama panelinde:** aile adı rozeti ("Sözleşme") başlığın yanında; §2(c) satırları; `prompt_hint` gösterilmez.
- **Admin modunda:** aynı ipuçları + aile satırına "Rehberi düzenle" linki (Yönetim › Tür rehberi, aile seçili).

## 4. Yönetim › Etiketler / Tür rehberi (admin CRUD)

**Rota/sekme:** `AdminLayout`'a iki sekme: `etiketler`, `tur-rehberi`; `router.tsx` iki sayfa (`RequireAdmin` altında).

**`AdminTagsPage` (desen: `AdminUsersPage` tablo + satır içi form):**
- Başlık + "+ Etiket" düğmesi → satır içi `TagForm` (`slug`, `label`, `kind` seçimi identity/change; slug yazarken küçük harf/tire önizlemesi; sunucu 422 `INVALID_SLUG`/409 `TAG_EXISTS` → `ErrorBox`).
- Tablo: Etiket (slug), Ad (`label` satır içi düzenlenebilir), Tür (`badge`: Kimlik / Değişiklik), Durum (Aktif / Emekli), işlem: **Emekli et / Yeniden aktifleştir** (`PATCH is_active`), "Düzenle" (`label`/`kind`). **Silme yok** (backend yok; eski belgeler referans verir) — satır notu.
- Alt kart "Değişiklik geçmişi": `GET /api/admin/events?kind=tag_created|tag_updated` (iki istek ya da `kind` filtresiz + istemci süzgeci) → `FolderHistory` tablosuyla aynı biçim (zaman, kim, etiket, önce → sonra).
- Üst not (`notice`): "Etiketler şirketin sabit listesinden gelir; liste yalnızca buradan büyür. Katalog dışı etiket kaydedilemez."

**`AdminGuidePage` (desen: `AdminFoldersPage` sol liste + sağ kart + `chips` görünüm):**
- Sol: aile listesi (`label`, pasifler soluk, "+ Aile" → satır içi `NewFamilyForm`: `family` slug `^[a-z][a-z0-9_]*$`, `label`, ilk desenler).
- Sağ, görünüm çipleri: **"Rehber"** (form), **"Sinyaller"** (`GET …/signals` tablosu: aile, anahtar, sayı; satırda **"Rehbere ekle"** → seçili aileye `suggested_extra_fields` satırı olarak önceden doldurur, kaydı admin yapar — §4.7.3 "karar insanın"), **"Geçmiş"** (`events?kind=guide_*`).
- Rehber formu (`GuideForm`, `form-grid`): `label`; **tür desenleri** (çip listesi + ekleme kutusu; küçük harfe çevrilir); **önerilen ek alanlar** (satırlar: `key` (normalize), `label`, `hint`; ekle/sil/sırala yok); **önerilen etiketler** (§1 `TagPicker`'ın aynısı, katalogdan); **vurgulanan standart alanlar** (9 standart alan + `effective_date`/`expiration_date`/`supersedes_document_id` onay kutuları); **Balbal ipucu** (`prompt_hint`, textarea, "yalnızca Balbal görür" notu); **Aktif** anahtarı. Kaydet → `PATCH`; "kaydedilmedi" uyarısı `AdminFoldersPage.dirty` deseniyle.
- Silme yok (`is_active=false`).

**API:** `api/tags.ts`, `api/guide.ts` (`useGuide`, `useAdminGuide`, `createFamily`, `updateFamily`, `useGuideSignals`), `api/admin-events.ts` (`useAdminEvents(kind)`); `types.ts`: `Tag`, `TagKind`, `TagCreate`, `TagUpdate`, `GuideFamily`, `GuideField`, `GuideSignal`, `AdminEvent`, `ExtraFieldValue`, `DocumentDetail.extra_fields`, `MetadataSuggestion.fields.extra_fields/tags.dropped` (tipte `SuggestionField` genişler), `SearchDocumentHit.matched_on`, `MetadataSuggestionApply.extra_fields`, `DocumentSubmitRequest` (miras).

## 5. Arama sonucunda `matched_on` rozeti (`SearchPanel`)

- Belge satırında, `matched_on !== "content"` ise küçük `badge neutral`: `title` → "Başlıkta", `type` → "Türde", `counterparty` → "Muhatapta", `reference` → "Referansta", **`tag` → "Etiket eşleşmesi"**, **`extra_field` → "Ek alan eşleşmesi"**; `content` → rozet yok (snippet zaten var). Metinler `S.shell.matchedOn`.
- `DocumentDetailPanel`: `Etiketler` satırı çip olarak; yeni **"Ek alanlar"** satırı (`dt/dd`: `key: value` + kaynak rozeti). PR-4 ile çakışma riski için bkz. §7.

## 6. Yeni görsel öğeler (T-12 — Ürün Yetkilisi tasarım onayı bekliyor)

1. 1. aşama panelinde **etiket çip seçici** (katalog; değişiklik etiketleri grubu katlanabilir) — serbest metin kaldırılır.
2. **Ek alanlar** alt bölümü: öneri/mevcut/rehber satırları, kaynak rozeti ("Balbal"/"personel"), **"+ Alan ekle"** satırı (anahtar + değer), **"n / 20"** sayacı, "×" kaldırma.
3. Yükleme formunda ve panelde **rehber ipucu satırı** ("Bu tür için genellikle: …") ve **aile rozeti**.
4. **Yönetim › Etiketler** sayfası (tablo, satır içi form, emekli et/aktifleştir, geçmiş).
5. **Yönetim › Tür rehberi** sayfası (sol aile listesi, rehber formu, sinyaller tablosu + "Rehbere ekle", geçmiş).
6. Arama sonucunda **eşleşme rozeti**; belge detayında **Ek alanlar** satırı ve çip etiketler.
7. Admin öneri panelinde **"katalogda yok" notu**.
CSS: ≤ 3 kural (`.tag-picker .chip.change` ayrımı, `.extra-key` giriş genişliği, `.signals td` sıkılık).

## 7. Dal, sıra ve PR-4 ilişkisi

- **Dal:** `feat/b28b-arayuz`, **`main@b709f09`'dan** (PR-2/#3 merge sonrası). **PR-4'ten bağımsız:** PR-4 `Layout.tsx` ("Belgeler" linki), `DocumentTable.tsx` (rozet), `DocumentDetailPanel.tsx` (**durum hücresi**, satır 68–72) dokunuyor; PR-5 `DocumentDetailPanel`'de yalnızca **`Etiketler` `dd`'si ve yeni `Ek alanlar` dt/dd'si** (satır 83–84 civarı) → farklı bölge, çakışma beklenmez; olursa PR-5 rebase edilir (dakikalık). `DocumentTable`/`Layout`'a PR-5 dokunmaz.
- **Önerilen merge sırası:** PR-4 (küçük) → PR-5. Her ikisi `main`'e açık; Tansu hangisini önce alırsa diğeri rebase ile güncellenir.
- **Backend bağımlılığı:** company-ai `75234e6` (B-28b) dev VM'de kurulu; canlı doğrulama için submodule geçici checkout (PR-1/2 deseni), sonra `b709f09`'a geri. **LLM:** canlıda 0–1 (`suggest-metadata` ile öneri paneli `extra_fields` görünümü için en fazla 1).

## 8. Kabul kriterleri

| # | Kriter |
|---|---|
| P5-01 | `npm run typecheck`, `lint`, `build` yeşil; `package.json` değişmedi; Caddy imajı kurulur |
| P5-02 | 1. aşama: etiketler yalnızca çip seçiciden; AI/rehber önerileri işaretli gelir; serbest metin yok; sunucu 422 `unknown_tag` (katalog değişirse) `ErrorBox`'ta; değişiklik etiketleri grubu `amendment` dışı ailede katlı |
| P5-03 | Ek alanlar: AI önerisi satırı güven çubuğu + <0.8 kutusu; rehber satırları boş placeholder; "+ Alan ekle" normalize önizlemesi; 20'de düğme kapalı + sayaç; "×" mevcut anahtarı `null` ile kaldırır; gönderimde `extra_fields` + `confirmed_fields: extra_fields.<key>`; 422 `fields` vurgusu ek alan satırlarında da |
| P5-04 | Belge detayında ek alanlar (`key: value` + kaynak rozeti) ve çip etiketler; `ReviewEventsCard` `field_added` etiketi Türkçe |
| P5-05 | Yükleme formunda tür yazılınca rehber ipucu satırı + "önemli" işareti; zorunluluk yok |
| P5-06 | Yönetim › Etiketler: oluştur (slug/label/kind), 409/422 mesajları, emekli et/aktifleştir, label düzenle, geçmiş tablosu; employee rotaya giremez (`RequireAdmin`) |
| P5-07 | Yönetim › Tür rehberi: aile seç/oluştur, desen çipleri, ek alan satırları, önerilen etiketler (katalog), vurgulanan alanlar, Balbal ipucu, aktif anahtarı; kaydet → PATCH; sinyaller tablosu + "Rehbere ekle" ön doldurma; geçmiş |
| P5-08 | Arama: `tag`/`extra_field` eşleşmesinde rozet; içerik eşleşmesinde rozet yok |
| P5-09 | Admin öneri panelinde `tags.dropped` notu; uploader'a gösterilmez |
| P5-10 | Ürün 2 öğeleri ve `proposed.ts` değişmedi; PR açıklamasında bağımsızlık/PR-4 notu, **Yeni görsel öğeler (7)**, `[ANAYASA KONTROLÜ]` |
| P5-11 | Canlı (dev VM, geçici checkout, Caddy): admin etiket oluşturur → `finans` belge yükler → panelde etiket çipleri + rehber satırları + "alan ekle" → onaya gönderir → `finans_mudur` onaylar → arama etiketle bulur ve rozet görünür; LLM ≤ 1 |

## 9. SORU (Naci cevaplamalı)

1. **Değişiklik etiketleri** her belgede açık mı, yoksa yalnızca `amendment` ailesinde açık, diğerlerinde katlı ("göster") mı? Önerim **katlı** (§4.7.4 "yalnızca değiştiren belgelerde").
2. **`tags.dropped` notu** admin modunda gösterilsin mi (önerim evet; uploader'a hayır — §4.7.7)?
3. **Belge detayında ek alanlar** herkese mi (önerim evet — belge metadata'sıdır), kaynak rozeti ("Balbal"/"personel") dahil mi (önerim evet, küçük)?
4. **"Rehbere ekle"** sinyal kısayolu PR-5'te mi (önerim evet, ön doldurma yalnızca; kayıt admin'in "Kaydet"i ile) yoksa sinyaller salt okunur tablo mu?
5. PR sırası: PR-4 → PR-5 (önerim); PR-5 `main`'den bağımsız açılır — teyit.
6. CSS ≤ 3 kural — teyit.
