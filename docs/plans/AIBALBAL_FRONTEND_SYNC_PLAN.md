# AI-BalBal frontend ↔ company-ai backend senkronizasyonu — Uygulama Planı

**Tarih:** 02.10.2026 (rev. 2 — iki PR) · **Durum:** SORU'lar cevaplandı, Naci'nin "uygula" onayı bekleniyor · **Kod yazılmadı.** · **Hedef repo:** `ftansu/AI-BalBal` (yazma izni teyitli: `ntoydem`, `push: true`) · **Dallar:** **PR-1** `feat/backend-sync-urun1` (bağlantı düzeltmeleri + Ürün 1 giriş ekranı), **PR-2** `feat/onay-akisi-arayuz` (B-28 onay akışı arayüzü, PR-1'e bağımlı) · **Teslim:** her dal için PR → Tansu inceler, merge kararı onun. **main'e doğrudan push yok** (T-14).

**Naci'nin SORU cevapları (02.10.2026):** (1) onay akışı **ayrı PR** — Tansu küçük/az tartışmalı bağlantı düzeltmelerini hızlı onaylasın, tasarım onayı isteyen en hassas parça ayrı dursun; (2) Yönetim › Ayarlar **eklenmez**; (3) küçük yeni öğeler mevcut dil parçalarıyla kodlanır, PR'da **"tasarım onayı bekliyor"** işaretlenir; (4) PR açılır, **merge edilmez**; Tansu'ya kısa özet hazırlanır.

Kaynak: AI-BalBal `main@bdefb29` (= `b219600` + Anayasa v2.0 klasörü), dallar `feat/urun1-arayuz@97a37b4`, `docs/ekip-sohbeti-ve-netlik@a05db56`, `docs/gorev-devri-urun2@e12b152`; AI-BalBal `anayasa/` (00-cekirdek, 01-urun, 02-teknik, ek-b, ek-d), `AGENTS.md`/`CLAUDE.md`, `docs/URUN1_ARAYUZ.md`, `docs/GOREV_DEVRI_URUN2.md`, `docs/BAGLANTI_YOL_HARITASI.md` §9 (T-19…T-25), `README.md`; company-ai `backend/app/schemas/{ask,auth,document,search,folder,directory,excel,settings}.py`, `api/*.py`, ADR-022/023/024, NOT §2/§5/§7.

---

## 0. Önemli çerçeve — AI-BalBal'da Anayasa geçerli

AI-BalBal'ın `CLAUDE.md`'si Balbal Anayasası v2.0'ı her oturumda yükler; orada çalışırken **Üretici AI** olarak ona tabiyim. Bu planı etkileyen maddeler:

- **T-14 / Ç-11:** ayrı dal + PR, main'e push yok, force push yok — Naci'nin talimatıyla aynı. Yeni kütüphane/dış servis eklenmez (bu planda **yok**).
- **T-11 / Ü-1:** her ekran/özellik ürün etiketi taşır ve Ek-B maddesine atıf yapar. Bu PR'daki her şey **Ürün 1 — Tanıma** (Ek-B: "belgeleri sınıflandırır/indeksler", "yetkiye göre erişim", "bilgiyi/belgeyi bulur, okur", "her kaynağı ayrı ayrı gösterir"). Onay akışı O-1/O-3 (Çekirdek'te Onaylı Belge tanımı) → Ürün 1.
- **Ç-14:** PR açıklamasına `[ANAYASA KONTROLÜ]` görev sonu notu zorunlu; notsuz PR birleştirilmez.
- **T-12:** yeni görsel/UI öğesi Ürün Yetkilisi (Tansu) tasarım onayı olmadan kodlanmaz; **onaylı tasarımı birebir uygulayan** kod ayrıca onay istemez. Sonuç: bu PR **yeni ekran icat etmez**; var olan bileşenleri backend alanlarına bağlar, `feat/urun1-arayuz`'daki (Tansu'nun kendi canvas'ından kodlanmış) Ürün 1 ekranını kullanır. Kaçınılmaz küçük yeni öğeler (onay durumu rozeti, "Onaya gönder"/"Onayla" düğmeleri, "Onaylıyorum" kutusu) mevcut tasarım dilinin parçalarıyla (`badge`, `button`, `inline-check`, `card`) kurulur ve PR'da **"Yeni görsel öğeler"** başlığıyla listelenir — `docs/GOREV_DEVRI_URUN2.md` §4'ün önerdiği biçim. **Not:** o devir dokümanı henüz dal üzerinde (`docs/gorev-devri-urun2`), PR'ı/merge'i yok → yürürlükte değil; bu yüzden T-12 **tam** geçerli sayılır ve bu öğeler PR'da "ürün sahibi tasarım onayı bekliyor" olarak işaretlenir, Tansu PR'ı birleştirmeden önce isterse canvas'ta düzeltir.
- **Ç-16:** kapsam dışı değişiklik (refactor, stil temizliği, ek uç) yapılmaz; öneri olarak PR notuna yazılır.
- **Ç-15/9 — iki dal arasında çelişki yok:** `docs/gorev-devri-urun2` dokümanı ("arayüzün yeni backend alanlarına bağlanması ve bekleyen iki dalın birleştirilmesi" → §6/1, onay akışı → §6/2) bu planla aynı yöndedir; Naci'nin talimatıyla da çelişmez. Ancak o doküman yürürlükte olmadığından "geliştirici kendi PR'ını birleştirebilir" maddesi **kullanılmaz** — merge kararı Tansu'da (Naci'nin talimatı).

---

## 1. Tespitler — dallar

- **T1 — `main@bdefb29`:** `b219600` (BACKEND_GAPS v7.9, company-ai submodule pini) + yalnızca `anayasa/` klasörü ve `AGENTS.md`/`CLAUDE.md`. Frontend kodu `b219600` ile **aynı**. Yani dondurulmuş sürüm = main'in frontend'i; `frontend-balbal/` submodule'ü güncel sayılır.
- **T2 — `docs/ekip-sohbeti-ve-netlik` (2 commit, main'den 2 geride):** BACKEND_GAPS **v8.0** (29.09): "ürünün gerçek arayüzü AI-BalBal, company-ai `frontend/` test arayüzüdür"; ekip sohbeti (birebir/grup) **Ürün 1**, Balbal sohbete **dahil edilemez** (`include_balbal` alanı kaldırıldı, `sender_id=null` = sistem mesajı), görüş talebi sekmesi yalnızca P2; `Layout` ekip sohbeti düğmesini her pakette gösterir (eski `hasTeamChat = P2` kaldırıldı), B-28'de "etiket önerisini **yükleyen** onaylar", agenda `approval` kalemi yükleyene. Kod etkisi küçük (`proposed.ts` §5, `Layout.tsx`, `TeamNewChat.tsx`, `TeamConversation.tsx`, `strings.ts` 1 satır). **Anayasa ile uyumlu** (Ü-7.1/7.2 birebir). Backend'de `/api/chats` hâlâ yok → arayüz "Backend bekleniyor" gösterir; bu PR o kısmı değiştirmez.
- **T3 — `feat/urun1-arayuz` (T2 + 1 commit):** `pages/urun1/Urun1Home.tsx` — Ürün 1 departman giriş ekranı (ortada Balbal çubuğu, departmana özel 3 örnek soru, cevaplar `AnswerView` ile akar); `AskTab` P2 kapalıyken bunu gösterir; `Department.tsx` başlık/sekme gizler; `Layout.tsx` üst arama + Balbal düğmesini bu sayfada gizler; `styles.css` `.u1-*` (130 satır); `docs/URUN1_ARAYUZ.md`. Tasarım kaynağı Tansu'nun canvas'ı ("X Platformu — Ürün 1") → **T-12 onaylı sayılır**, birebir alınır. Ekranın kendisi `/api/ask`'ten başka bir şey beklemiyor. **Not:** örnek sorular arasında backend demo verisinde karşılığı olmayanlar var (Hukuk: "İzmir RES davasında son duruşma", İK soruları — demo belgesi yok). Ü-10 "sadelik"e uygun; içerik B-18'in işi, bu PR'da **dokunulmaz** (Ç-16), PR notunda belirtilir.
- **T4 — `docs/gorev-devri-urun2` (1 commit, main güncel):** yalnızca doküman (§0). Bu PR'a **dahil edilmez** (Anayasa süreci, Tansu'nun PR'ı).
- **T5 — Birleştirme sırası:** `feat/urun1-arayuz` zaten `docs/ekip-sohbeti-ve-netlik`'i içeriyor (ortak 2 commit). Yeni dal `feat/backend-sync-urun1`, **`main`'den** açılır ve `feat/urun1-arayuz` **merge** edilir (çakışma beklenmez: main'in o dallardan sonraki tek farkı `anayasa/` + 2 talimat dosyası). Böylece PR tek seferde: Ürün 1 ekranı + ekip sohbeti netliği + backend bağlantıları. Tansu'nun kendi dalları silinmez, PR'da "şu iki dalı içerir" yazılır.

## 2. Tespitler — backend'de var, AI-BalBal `main`'de bağlı değil

| # | Backend (company-ai) | AI-BalBal `main` durumu | Etki |
|---|---|---|---|
| F1 | `CurrentUser.enabled_products` (B-25, ADR-022), `primary_department_slug`, `title` | `enabled_products?` **opsiyonel tip var**, `products.ts` alan yoksa P1 varsayıyor → **artık dolu geliyor, çalışıyor**; `primary_department_slug`/`title` tipte yok (ama `department_slugs[0]` = ana departman, Aşama C bunu garanti etti) | Tip tamamlanır; `UserMenu`'de unvan gösterimi (küçük) |
| F2 | `AskResponse.audit_log_id`, `product_level`, `warnings[{kind: missing_data\|insufficient_data\|product_limit, message, action}]` (Aşama A, Ürün 1 uyum turu) | `audit_log_id?` yalnızca `FeedbackRow`'da; `warnings`/`product_level` **yok**; "kaynak bulunamadı" metni `answered=false`'tan türetiliyor | `AnswerView`: `warnings` listesini sabit mesajıyla göster (Ç-7 durum etiketi: Veri Yok / Yeterli Veri Bulunmamaktadır / paket sınırı), `product_level` rozeti; `FeedbackRow` zaten `audit_log_id` kullanıyor (feedback ucu backend'de yok → "bekleniyor" kalır) |
| F3 | `SourceCard.supersedes_document_id` / `superseded_by_document_id`, `is_initial`, `project_code` / `project_name` (Aşama A/D) | `SourceCardList` "güncel versiyon link değil (B-07)" yorumu; proje adını belge listesinden türetiyor (`projectOfDocument`) | Güncel/önceki versiyon **tıklanabilir** (`FileLink`), proje adı doğrudan karttan; `projectOfDocument` türetmesi kalkabilir (Ç-16: yalnızca bu kartta) |
| F4 | `DocumentListItem.file_kind` (pdf\|image\|xlsx\|xlsm\|csv), `folder_id`, **`review_status`** (B-28) | `folder_id?` var; `file_kind` ve `review_status` yok | Tipler; belge tablosunda tür simgesi (metin rozeti), onay durumu rozeti |
| F5 | `GET /download?inline=1` (pdf/görüntü tarayıcıda açılır) + başlık bazlı dosya adı (Aşama B) | `FileLink`: aynı `downloadUrl` hem `target=_blank` hem `download` | "Aç" → `?inline=1`, "İndir" → düz; dosya adı backend'den gelir (frontend'de değişiklik yok) |
| F6 | `GET /api/search?q=&limit=` → `{documents[+snippet,page_number], projects, people}` (Aşama D) | `SearchPanel` belge/proje listesini **istemci tarafında** süzüyor, kişi için `useDirectory` (`proposed`) | Panel tek uca bağlanır; içerik eşleşmesinde snippet + sayfa; kişiler gerçek |
| F7 | `GET /api/directory?q=&department=` (Aşama C) | `proposed.ts §4 useDirectory` → 404 → "Backend bekleniyor" | `proposed`'dan gerçek `api/directory.ts`'e taşınır; `TeamNewChat` kişi seçici ve `SearchPanel` kişi sonuçları çalışır |
| F8 | Klasörler: `GET /api/folders`, `GET/POST/PATCH/DELETE /api/admin/folders`, `PUT …/grants`, `GET …/audit`; upload `folder_id` (Aşama E) — sözleşme `proposed.ts §10` ile **birebir** | `proposed.ts §10` → 404 → "Backend bekleniyor" (`DocumentsTab`, `UploadTab`, `AdminFoldersPage`) | §10 `proposed`'dan `api/folders.ts`'e taşınır; `PendingNotice` dalları kalkar. Ekranlar hazır (Tansu kodlamış) |
| F9 | `department_manager` rolü (B-08) | `UserRole` birliğinde yok → etiket boş, `UserForm` atayamaz, `visibility.ts`/`Home`/`BalbalChat` `role !== "employee"`'yi "her şeyi görür" sayıyor | Birlik + `ROLE_LABELS` "Departman Yöneticisi" + `ROLE_VALUES`; üç dosyada müdür **üyelik bazlı** (employee gibi) ele alınır |
| F10 | Onay akışı (B-28): `review_status`, `POST /submit` (`confirmed_fields`, hata kodları), `POST /review`, `?review_status=…`, `GET /api/admin/documents/{id}/review-events`, `suggest-metadata` yükleyene açık, `apply` yayınlamaz | **Hiçbiri yok**; `MetadataSuggestionPanel` `isAdmin` ile `apply` gösteriyor → personelin 1. aşama düğmesi yok | En büyük parça: yükleme sonrası 1. aşama paneli (öneri + nihai alanlar + <0.8 "Onaylıyorum" kutusu → `submit`), müdür için "Onay bekleyen" listesi + `review`, belge listesi/detayında durum rozeti ve yorum |
| F11 | `GET/PATCH /api/admin/settings` (`enabled_products`) | Yok | Yönetim › Ayarlar: üç onay kutusu (admin). Küçük; Ü-10/T-2 ile uyumlu (paket ürün sahibinin aracı). **Opsiyonel — SORU 2** |
| F12 | `warnings.product_limit`, P1'de DATA→DOCUMENT düşürme (ADR-022) | Arayüz `query_type` rozetini gösteriyor; sabit footnote "Hesaplamalar Excel verisinden…" P1'de yanıltıcı (NOT §6.4) | F2 ile `product_limit` uyarısı görünür; footnote `product_level`'a göre; örnek DSCR soruları P1'de gizlenir (NOT §6.4, Tansu'ya devredilmişti — bu PR'da yapılır) |

Hata gövdesi: backend `detail` ya Türkçe string ya `{code, message}`; `client.ts` ikisini de okuyor → B-28 kodları (`approver_not_configured`, `low_confidence_not_confirmed` + `fields`, `suggestion_pending`…) için ek ayrıştırma yalnızca `fields` listesi.

## 3. Kapsam — iki PR

**İlke (ikisinde de):** var olan bileşenleri gerçek uçlara bağla; `proposed.ts`'teki artık gerçek olan sözleşmeleri gerçek API dosyalarına taşı; Ürün 2 öğeleri (gündem, görüş talebi, izin, yazışma) dokunulmaz; backend'e **hiçbir** değişiklik yok; yeni bağımlılık yok. Her şey **Ürün 1 — Tanıma** (Ek-B: sınıflandırma/indeks, yetkiye göre erişim, belgeyi bulma/okuma/gösterme, her kaynağı ayrı gösterme; onay akışı için Çekirdek O-1/O-3 "Onaylı Belge").

### PR-1 — `feat/backend-sync-urun1` (küçük, az tartışmalı; Tansu hızlı onaylayabilsin)

| # | İş | Tablo §2 | Yeni görsel öğe? |
|---|---|---|---|
| 1 | `feat/urun1-arayuz` merge'i: Ürün 1 giriş ekranı + ekip sohbeti netliği (v8.0) | T2/T3 | Hayır — Tansu'nun canvas'ından kodlanmış, T-12 onaylı sayılır |
| 2 | Tip senkronu `types.ts`: `CurrentUser.primary_department_slug/title`, `AskResponse.audit_log_id/product_level/warnings`, `SourceCard` versiyon id'leri + `is_initial` + `project_code/name`, `DocumentListItem.file_kind/folder_id/review_status`, `UserRole` + `department_manager` | F1–F4, F9 | Hayır |
| 3 | Roller: `ROLE_LABELS` "Departman Yöneticisi", `ROLE_VALUES`; `visibility.ts`/`Home.tsx`/`BalbalChat.tsx` müdürü **üyelik bazlı** ele alır | F9 | Hayır (mevcut etiket/seçim) |
| 4 | `FileLink`: "Aç" → `?inline=1` (pdf/görüntü sekmede), "İndir" → düz; dosya adı backend'den | F5 | Hayır |
| 5 | `SourceCardList`: önceki/sonraki versiyon tıklanabilir (`FileLink` + id), proje adı karttan (`projectOfDocument` türetmesi yalnızca bu kartta kalkar) | F3 | Hayır |
| 6 | `AnswerView`: `warnings[]` sabit mesajlarıyla (Ç-7 durumu: Veri Yok / Yeterli Veri Bulunmamaktadır / paket sınırı), `product_level` rozeti; P1'de Excel footnote ve DSCR örnek soruları gizli | F2, F12 | **Küçük:** uyarı satırı + rozet — mevcut `badge`/`answer-notice` sınıflarıyla; "tasarım onayı bekliyor" |
| 7 | `proposed` → gerçek: `api/directory.ts` (rehber), `api/folders.ts` (§10 birebir), `api/search.ts`; `SearchPanel` tek uca bağlanır (snippet + sayfa, kişiler gerçek); `DocumentsTab`/`UploadTab`/`AdminFoldersPage`/`TeamNewChat` `PendingNotice` dalları kalkar | F6–F8 | Hayır — ekranlar hazır, yalnızca veri kaynağı |
| 8 | `DocumentTable`: `file_kind` metin rozeti; `review_status` **yalnızca gösterim** (Onaylı / Bekliyor / Onay bekliyor / Geri gönderildi) — aksiyon yok | F4 | **Küçük:** iki rozet; "tasarım onayı bekliyor" |
| 9 | README + `docs/BACKEND_GAPS.md` durum satırları (bağlanan maddeler "yapıldı") | — | — |

Hariç (PR notunda öneri): gündem/bildirim/ekip sohbeti/feedback/sohbet geçmişi uçları (backend yok), Yönetim › Ayarlar (SORU 2: hayır), stil düzenlemesi, örnek soru içerikleri (B-18), onay akışı (PR-2).

### PR-2 — `feat/onay-akisi-arayuz` (PR-1'e bağımlı; tasarım onayı isteyen parça)

Dal **PR-1'in üstünden** açılır (`feat/backend-sync-urun1`'den); PR-1 merge olmadan PR-2 açılırsa GitHub'da base = `feat/backend-sync-urun1` seçilir, PR-1 merge olunca base `main`'e çevrilir (GitHub bunu otomatik yapar).

| # | İş | Tablo §2 | Yeni görsel öğe? |
|---|---|---|---|
| 1 | `api/documents.ts`: `submitDocument(id, body)`, `reviewDocument(id, body)`, `useDocuments({review_status})`; `api/admin-documents.ts`: `useReviewEvents(id)`; `types.ts`: `DocumentSubmitRequest`, `DocumentReviewRequest`, `ReviewEvent`, hata gövdesi `detail.fields` | F10 | Hayır |
| 2 | **1. aşama paneli** — `MetadataSuggestionPanel`'in yükleyen modu: öneri satırları + düzenlenebilir alanlar (mevcut düzen) + güveni < 0.8 satırlarda "Onaylıyorum" kutusu (`inline-check`) + **"Onaya gönder"** → `POST /submit`; 409 `suggestion_pending` → mevcut `useSuggestion poll` ile bekle + bilgi satırı; 422 `low_confidence_not_confirmed` → `detail.fields` satırları işaretlenir, mesaj alanda; 422 `department_required` → departman alanı vurgulanır. `apply`/`reject` admin görünümünde kalır (yayınlamaz — açıklama metni) | F10a | **Evet:** kutu + düğme + hata vurgusu — "tasarım onayı bekliyor" |
| 3 | `DocumentsTab`: müdür için **"Onay bekleyen"** süzgeci (`?review_status=pending_review`), personel için **"Geri gönderilenler"** (`changes_requested`) — mevcut `chips` deseni | F10b | **Evet:** iki süzgeç çipi — "tasarım onayı bekliyor" |
| 4 | `DocumentDetailPanel`: durum + `review_comment` + `submitted_at/reviewed_at`; müdür ise **Onayla / Geri gönder** (yorum zorunlu, `Modal`) → `POST /review`; admin ise kayıt defteri listesi (`review-events`, salt okunur) | F10c/d | **Evet:** iki düğme + yorum modalı + defter listesi — "tasarım onayı bekliyor" |
| 5 | Belge yüklendikten sonra `UploadTab` akışı: `ready` → öneri → 1. aşama paneli → "Onaya gönderildi" bilgi satırı (`badge ok`) | F10a | Hayır (mevcut akışın devamı) |
| 6 | README + BACKEND_GAPS §4.7 "arayüz yapıldı" satırı | — | — |

Hariç: `extra_fields`/etiket kataloğu/tür bazlı rehber (B-28b), `/api/me/agenda` `approval` sarmalaması (B-01, backend yok), bildirimler (B-02).

## 4. Yeniden kullanılacak parçalar

| Parça | Nereden | PR | Nasıl |
|---|---|---|---|
| `Urun1Home.tsx`, `.u1-*`, `Department`/`AskTab`/`Layout` koşulları | `feat/urun1-arayuz` | 1 | merge, değiştirilmeden |
| Balbal'sız ekip sohbeti (`TeamNewChat`/`TeamConversation`/`proposed §5`) | `docs/ekip-sohbeti-ve-netlik` (feat dalı içinde) | 1 | merge |
| `AdminFoldersPage`, `DocumentsTab.FolderDocuments`, `UploadTab` klasör seçimi, `lib/folders.ts` | `main` | 1 | veri kaynağı `proposed §10` → `api/folders.ts` |
| `SearchPanel` düzeni | `main` | 1 | veri kaynağı `/api/search` |
| `FileLink`, `SourceCardList`, `AnswerView`, `DocumentTable`, `badge` sınıfları | `main` | 1 | alan eklemeleri |
| `MetadataSuggestionPanel` (satır düzeni, güven çubuğu, seçili alan gövdesi) | `main` | 2 | `isAdmin` kapısı yerine "yükleyen" modu; `apply` → `submit` |
| `DocumentDetailPanel`, `Modal`, `chips` | `main` | 2 | aksiyonlar + süzgeçler |
| `FeedbackRow` | `main` | — | dokunulmaz (uç yok) |

## 5. Dosyalar

**PR-1:** `api/types.ts`, `api/documents.ts` (+`inlineUrl`), **yeni** `api/search.ts`, `api/directory.ts`, `api/folders.ts`; `api/proposed.ts` (§4 `useDirectory` ve §10 çıkar); `components/common/FileLink.tsx`, `components/SourceCardList.tsx`, `components/balbal/AnswerView.tsx`, `components/shell/SearchPanel.tsx`, `components/DocumentTable.tsx`; `pages/department/{DocumentsTab,UploadTab}.tsx`, `pages/admin/AdminFoldersPage.tsx`, `components/team/TeamNewChat.tsx` (yalnızca import), `lib/format.ts` (`ROLE_LABELS`, `FILE_KIND_LABELS`, `REVIEW_STATUS_LABELS`), `lib/visibility.ts`, `pages/Home.tsx`, `components/balbal/BalbalChat.tsx`, `lib/strings.ts`, `README.md`, `docs/BACKEND_GAPS.md`.
**PR-2:** `api/types.ts` (+review tipleri), `api/documents.ts` (+`submit`/`review`/süzgeç), **yeni** `api/admin-documents.ts`; `components/MetadataSuggestionPanel.tsx`, `components/DocumentDetailPanel.tsx` (+ `ReviewActions`, `ReviewEvents` iç bileşenler), `pages/department/{DocumentsTab,UploadTab}.tsx`, `lib/strings.ts`, `styles.css` (yalnızca varsa rozet rengi), `README.md`, `docs/BACKEND_GAPS.md`.
**Backend'e dokunulmaz.** company-ai'da merge sonrası tek iş: `frontend-balbal` submodule pinini yeni main'e almak (ayrı küçük commit, plan dışı).

## 6. Sıra (her adım ayrı commit; adım sonunda `npm run typecheck && npm run lint && npm run build`)

**PR-1**
1. `git checkout -b feat/backend-sync-urun1 origin/main` → `git merge origin/feat/urun1-arayuz` → build yeşil.
2. `types.ts` + `format.ts` + roller (3 dosya).
3. `FileLink` + `SourceCardList` + `AnswerView` (uyarılar, rozet, footnote/örnek gizleme).
4. `api/directory.ts`, `api/folders.ts`, `api/search.ts`; `proposed.ts`'ten çıkar; `SearchPanel`, `DocumentsTab`, `UploadTab`, `AdminFoldersPage`, `TeamNewChat` bağla.
5. `DocumentTable` rozetleri.
6. Dev VM canlı doğrulama (S-01…S-07, §7): `frontend-balbal` submodule'ünde dal checkout (pin commit'lenmez) → `make up` → tarayıcı; `make set-products` ile P1 ve P1+P2 iki durum; sonra submodule `b219600`'a geri.
7. README/BACKEND_GAPS → **PR-1 aç** (şablon §8) → Tansu'ya kısa özet → PR-2'ye geç.

**PR-2** (PR-1 dalından)
8. `git checkout -b feat/onay-akisi-arayuz feat/backend-sync-urun1`.
9. API + tipler → 10. 1. aşama paneli → 11. süzgeçler + detay aksiyonları + defter → 12. canlı doğrulama (S-08) → 13. README/BACKEND_GAPS → **PR-2 aç** (base: `feat/backend-sync-urun1`) → Tansu'ya özet → **dur**. Merge kararları Tansu'da.

## 7. Kabul kriterleri

| # | PR | Kriter |
|---|---|---|
| S-01 | 1,2 | `npm run typecheck`, `npm run lint`, `npm run build` yeşil; Caddy imajı aynı Dockerfile ile kurulur (yeni bağımlılık yok — T-14) |
| S-02 | 1 | P1 paketinde departman girişi = `Urun1Home`; P2 açıkken sekmeli ekran; ekip sohbeti düğmesi her pakette (T-22/T-23 **v8.0 ile değişti** — PR notunda açıkça) |
| S-03 | 1 | Cevap kartı: `warnings` sabit metinleriyle, `product_level` rozeti; P1'de DSCR örnekleri ve Excel footnote yok; kaynak kartında önceki/sonraki versiyon tıklanabilir, proje adı backend'den |
| S-04 | 1 | "Aç" PDF/görüntüyü sekmede açar (`?inline=1`), "İndir" başlık adlı dosya indirir; Excel yalnızca indirir |
| S-05 | 1 | Arama: içerik eşleşmesinde snippet + sayfa; proje ve kişi sonuçları gerçek; yetkisiz belge görünmez (T-21) |
| S-06 | 1 | Klasörler: ağaç, yazılabilir klasör listesi, admin klasör/grant/audit gerçek; "Backend bekleniyor" bu ekranlarda kalmaz |
| S-07 | 1 | `department_manager`: etiket, admin formu, müdür kendi departmanının restricted belgesini görür, kartlar üyelik bazlı; `review_status` rozeti **gösterilir** (aksiyon yok) |
| S-08 | 2 | Onay akışı tarayıcıda uçtan uca: personel yükler → 1. aşama (0.8 altı alan onaysız → 422 alanda görünür; `suggestion_pending` bekleme satırı) → müdür "Onay bekleyen" → Onayla / Geri gönder (yorum zorunlu) → onaylı belge aramada ve Balbal'da; onaysız belge meslektaşa görünmez; `hukuk` upload 409 mesajı Türkçe okunur; admin defteri sıralı |
| S-09 | 1,2 | Ürün 2 öğeleri değişmedi; P2 kapalıyken görünmüyor (T-2, Ü-10) |
| S-10 | 1,2 | PR açıklaması: değişen/neden listesi, "İçerdiği dallar" (PR-1), "Bağımlı olduğu PR" (PR-2), **"Yeni görsel öğeler (tasarım onayı bekliyor)"**, "Kapsam dışı öneriler", `[ANAYASA KONTROLÜ]` notu (v2.0; Çekirdek + 01 Ürün + 02 Teknik + Ek-B; Ürün 1; gizli bilgi/yeni bağımlılık yok; kapsam dışı: öneri; kendi kararlar) |

LLM çağrısı: canlı doğrulamada toplam **en fazla 3** `/api/ask` (P1 örnek soru, `product_limit` için bir DSCR sorusu, PR-2'de onay sonrası belge sorusu); gerisi LLM'siz.

## 8. PR açıklama iskeleti (ikisi için aynı biçim)

```
feat: <başlık>

Bağımlı olduğu PR: (PR-2 için: #<PR-1>)      İçerdiği dallar: (PR-1 için: feat/urun1-arayuz, docs/ekip-sohbeti-ve-netlik)
Neler değişti / neden: (satır satır — "backend'de X var, arayüz bağlı değildi, şimdi Y")
Backend'e dokunulmadı; yeni bağımlılık yok.
Yeni görsel öğeler (T-12 — Ürün Yetkilisi tasarım onayı bekliyor): …
Kapsam dışı öneriler (Ç-16): …
Doğrulama: typecheck/lint/build; dev VM tarayıcı akışı (S-…)
[ANAYASA KONTROLÜ]  (Ç-14 formatı: versiyon, okunan modüller, ürün etiketi, gizli bilgi/yeni bağımlılık, kapsam dışı, kendi kararlar)
```

Tansu'ya kısa Türkçe özet (her PR için 5–8 satır: ne değişti, neyi onaylaması bekleniyor, nasıl deneyeceği) PR yorumu olarak ve company-ai NOT'una işlenir.

---

## SORU — cevaplandı (02.10.2026)

1. Onay akışı → **PR-2 `feat/onay-akisi-arayuz`**, PR-1'e bağımlı (Naci; planın "tek PR" önerisi yerine).
2. Yönetim › Ayarlar → **eklenmez**.
3. Küçük yeni öğeler mevcut dil parçalarıyla kodlanır, PR'da **"tasarım onayı bekliyor"** işaretlenir.
4. PR'lar açılır, **merge edilmez**; Tansu'ya kısa özet hazırlanır.

Kalan açık soru yok; "uygula" onayı bekleniyor.

---

## Uygulama sırası (özet)

**PR-1:** dal + merge → tipler/roller → dosya linkleri + kaynak + cevap kartı → `proposed`→gerçek (rehber, klasör, arama) → tablo rozetleri → dev VM canlı → docs → PR-1 + Tansu özeti. **PR-2:** PR-1 dalından → API/tipler → 1. aşama paneli → süzgeçler + detay aksiyonları + defter → canlı → docs → PR-2 (base PR-1) + özet → **dur**. company-ai: NOT güncellemesi + rapor; submodule pini merge sonrası ayrı commit.
