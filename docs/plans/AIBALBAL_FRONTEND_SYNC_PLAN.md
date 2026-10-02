# AI-BalBal frontend ↔ company-ai backend senkronizasyonu — Uygulama Planı

**Tarih:** 02.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.** · **Hedef repo:** `ftansu/AI-BalBal` (yazma izni teyitli: `ntoydem`, `push: true`) · **Yeni dal:** `feat/backend-sync-urun1` · **Teslim:** PR → Tansu inceler, merge kararı onun. **main'e doğrudan push yok** (T-14).

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

## 3. Önerilen kapsam — "sade, aynı mimari, backend'le tam uyumlu"

**İlke:** var olan bileşenleri gerçek uçlara bağla; `proposed.ts`'teki artık gerçek olan sözleşmeleri gerçek API dosyalarına taşı; yeni ekran yalnızca **onay akışı için** ve mevcut dilden parçalarla. Ürün 2 öğeleri (gündem, görüş talebi, izin, yazışma) **dokunulmaz** (`proposed`'da kalır, P2 kapalıyken zaten gizli). Backend'e **hiçbir** değişiklik yok (bu plan yalnızca AI-BalBal).

**Dahil (Ürün 1, Ek-B atıflarıyla):**
1. `feat/urun1-arayuz` merge'i (Ürün 1 ekranı + ekip sohbeti netliği, T3/T2).
2. Tip senkronu `types.ts` (F1–F4, F9) — tek dosya, geriye uyumlu.
3. `FileLink`: Aç = `?inline=1`, İndir = düz (F5) — Ü-10 "her referans açılabilir/indirilebilir".
4. `SourceCardList`: versiyon linkleri, proje adı karttan (F3).
5. `AnswerView`: `warnings` + `product_level` (F2, F12) — Ç-7 durum etiketleri arayüzde.
6. `proposed` → gerçek: `api/directory.ts` (F7), `api/folders.ts` (F8), `api/search.ts` + `SearchPanel` (F6).
7. Roller (F9): `department_manager` her yerde.
8. Onay akışı (F10): a) `UploadTab` sonrası `MetadataSuggestionPanel` **yükleyen** için: öneri satırları + düzenlenebilir alanlar + güveni <0.8 satırlarda "Onaylıyorum" kutusu + "Onaya gönder" → `submit`; 409 `suggestion_pending` → sayaçla bekle (`useSuggestion poll` zaten var); 422 `low_confidence_not_confirmed` → `detail.fields` işaretlenir. b) `DocumentsTab`/`DocumentTable`: `review_status` rozeti (Bekliyor / Onay bekliyor / Geri gönderildi / Onaylı), müdür için "Onay bekleyen" süzgeci (`?review_status=pending_review`), personel için "Geri gönderilenler". c) `DocumentDetailPanel`: durum + `review_comment` + müdür ise **Onayla / Geri gönder (yorum)** düğmeleri → `review`. d) Admin `DocumentDetailPanel`'de kayıt defteri (`review-events`) küçük liste.
9. README + `docs/BACKEND_GAPS.md`'de "yapıldı" notları (belge güncellemesi, Ç-16 kapsamında: yalnızca bağlanan maddelerin durum satırları).

**Hariç (öneri olarak PR notunda):** gündem/bildirim/ekip sohbeti uçları (backend yok), `/api/ask/feedback` ve sohbet geçmişi (backend yok), Yönetim › Ayarlar (SORU 2), stil yeniden düzenlemesi, örnek soru içerikleri (B-18), `extra_fields`/etiket kataloğu (B-28b).

## 4. Yeniden kullanılacak parçalar

| Parça | Nereden | Nasıl |
|---|---|---|
| `Urun1Home.tsx`, `.u1-*` stilleri, `Department`/`AskTab`/`Layout` koşulları | `feat/urun1-arayuz` | merge, değiştirilmeden |
| `TeamNewChat`/`TeamConversation`/`proposed §5` Balbal'sız sohbet | `docs/ekip-sohbeti-ve-netlik` | merge (feat dalı içinde) |
| `AdminFoldersPage`, `DocumentsTab.FolderDocuments`, `UploadTab` klasör seçimi, `lib/folders.ts` | `main` | yalnızca veri kaynağı değişir (`proposed §10` → `api/folders.ts`) |
| `MetadataSuggestionPanel` (satır/alan düzeni, güven çubuğu, seçili alan gövdesi) | `main` | `isAdmin` kapısı yerine **rol-bağımsız "yükleyen"** modu; `apply` → `submit`; kutular eklenir |
| `DocumentVisibilityCard`, `DocumentDetailPanel`, `DocumentTable`, `badge` sınıfları | `main` | yeni alanlar eklenir |
| `SearchPanel` düzeni | `main` | veri kaynağı `/api/search` |
| `FeedbackRow` | `main` | dokunulmaz (uç yok) |

## 5. Dosyalar (AI-BalBal `frontend/src`)

`api/types.ts` (F1–F4, F9, warnings, review tipleri) · `api/documents.ts` (+`submit`, `review`, `?review_status`, `inlineUrl`) · **yeni** `api/search.ts`, `api/directory.ts`, `api/folders.ts`, `api/admin-documents.ts` · `api/proposed.ts` (§4, §10 ve `useDirectory` kaldırılır; §1–3, §5–9 kalır) · `components/common/FileLink.tsx` · `components/SourceCardList.tsx` · `components/balbal/AnswerView.tsx` · `components/shell/SearchPanel.tsx` · `components/MetadataSuggestionPanel.tsx` (→ 1. aşama) · `components/DocumentTable.tsx`, `DocumentDetailPanel.tsx` (+ `ReviewActions`, `ReviewEvents` küçük iç bileşenler) · `pages/department/{DocumentsTab,UploadTab}.tsx` · `pages/department/ProjectsTab.tsx` (dokunulmaz) · `lib/format.ts` (`ROLE_LABELS`, `REVIEW_STATUS_LABELS`, `FILE_KIND_LABELS`) · `lib/visibility.ts`, `pages/Home.tsx`, `components/balbal/BalbalChat.tsx` (müdür = üyelik) · `lib/strings.ts` (yeni metinler Türkçe) · `styles.css` (yalnızca rozet renk sınıfları varsa; yeni düzen yok) · `README.md`, `docs/BACKEND_GAPS.md` durum satırları.

**Backend'e dokunulmaz.** company-ai tarafında bu PR'dan sonra yapılacak tek iş: Tansu merge edince `frontend-balbal` submodule pinini yeni main'e almak (ayrı küçük commit, bu planın dışında).

## 6. Sıra (her adım ayrı commit, aynı dal; adım sonunda `npm run typecheck && npm run lint && npm run build`)

1. `git checkout -b feat/backend-sync-urun1 origin/main` → `git merge origin/feat/urun1-arayuz` (çakışma yoksa olduğu gibi) → build yeşil.
2. `types.ts` + `format.ts` + roller (F1, F4, F9) → build.
3. `FileLink` inline/indir (F5) + `SourceCardList` (F3) + `AnswerView` warnings/product_level/footnote (F2, F12).
4. `api/directory.ts`, `api/folders.ts`, `api/search.ts`; `proposed.ts`'ten çıkar; `SearchPanel`, `DocumentsTab`, `UploadTab`, `AdminFoldersPage`, `TeamNewChat` bağlanır (F6–F8).
5. Onay akışı (F10): `api/documents.ts` uçları → `MetadataSuggestionPanel` 1. aşama → `DocumentTable`/`DocumentsTab` rozet+süzgeç → `DocumentDetailPanel` müdür aksiyonları + admin defteri.
6. Canlı doğrulama dev VM'de: `frontend-balbal` submodule'ünde dalı checkout et (pin commit'lenmez) → `make up` (Caddy imajı yeniden kurulur) → tarayıcı: `finans` yükler → 1. aşama → `finans_mudur` onaylar → `yonetim` görür; `hukuk` upload 409 mesajı; `finans_mudur` restricted belgeyi listede görür; arama snippet'li; klasör ağacı gerçek; Ürün 1 ekranı P1'de, sekmeli ekran P2'de (`make set-products` ile iki durum). Sonra submodule `b219600`'a geri alınır.
7. README/BACKEND_GAPS durum satırları → PR aç (açıklama şablonu §8) → **dur**; merge Tansu'da.

## 7. Kabul kriterleri

| # | Kriter |
|---|---|
| S-01 | `npm run typecheck`, `npm run lint`, `npm run build` yeşil; Caddy imajı aynı Dockerfile ile kurulur (yeni bağımlılık yok — T-14) |
| S-02 | P1 paketinde departman girişi = `Urun1Home`; P2 açıkken sekmeli ekran; ekip sohbeti düğmesi her pakette (T-22/T-23 **değişti** — v8.0 kararı; PR notunda açıkça) |
| S-03 | Cevap kartı: `warnings` sabit metinleriyle (`missing_data`/`insufficient_data`/`product_limit`), `product_level` rozeti; Ç-7 etiketi ekranda; kaynak kartında önceki/sonraki versiyon tıklanabilir, proje adı backend'den |
| S-04 | "Aç" PDF/görüntüyü sekmede açar (`?inline=1`), "İndir" başlık adlı dosya indirir; Excel yalnızca indirir |
| S-05 | Arama: içerik eşleşmesinde snippet + sayfa; proje ve kişi sonuçları gerçek; yetkisiz belge görünmez (T-21) |
| S-06 | Klasörler: `DocumentsTab` ağaç gerçek, `UploadTab` yazılabilir klasör listesi gerçek, admin klasör/grant/audit sayfası çalışır; "Backend bekleniyor" kutusu bu ekranlarda kalmaz |
| S-07 | `department_manager`: etiket "Departman Yöneticisi", admin formu atayabilir, müdür kendi departmanının restricted belgesini listede görür, kartlar üyelik bazlı |
| S-08 | Onay akışı uçtan uca tarayıcıda: personel yükler → 1. aşama (0.8 altı alan onaysız → 422 mesajı alanda görünür) → müdür kuyruğunda → Onayla/Geri gönder (yorum zorunlu) → onaylı belge aramada ve Balbal'da; onaysız belge meslektaşa görünmez; `hukuk` upload 409 mesajı okunur Türkçe |
| S-09 | Ürün 2 öğeleri (gündem, görüş talebi, izin, yazışma) değişmedi; P2 kapalıyken görünmüyor (T-2, Ü-10) |
| S-10 | PR açıklaması: değişen/neden listesi, "İçerdiği dallar", "Yeni görsel öğeler (tasarım onayı bekliyor)", "Kapsam dışı öneriler", `[ANAYASA KONTROLÜ]` notu (v2.0; Çekirdek + 01 Ürün + 02 Teknik + Ek-B; Ürün 1; gizli bilgi/yeni bağımlılık yok; kapsam dışı: öneri; kendi kararlar listesi) |

LLM çağrısı: canlı doğrulamada Balbal soruları için **en fazla 3** (`/api/ask`, P1 örnek soru + onay sonrası belge sorusu + `product_limit` tetiklemesi için bir DSCR sorusu); gerisi LLM'siz.

## 8. PR açıklama iskeleti

```
feat: Ürün 1 arayüzünü company-ai backend'inin yeni alanlarına bağla

İçerdiği dallar: feat/urun1-arayuz (Ürün 1 ekranı), docs/ekip-sohbeti-ve-netlik (v8.0, Balbal'sız ekip sohbeti)
Neler değişti / neden: (F1…F12 tablosu — her satır "backend'de X var, arayüz bağlı değildi, şimdi Y")
Backend'e dokunulmadı; yeni bağımlılık yok.
Yeni görsel öğeler (T-12 — Ürün Yetkilisi tasarım onayı bekliyor): onay durumu rozeti, "Onaya gönder", "Onaylıyorum" kutusu, "Onayla / Geri gönder", kayıt defteri listesi (admin)
Kapsam dışı öneriler (Ç-16): …
Doğrulama: typecheck/lint/build; dev VM'de tarayıcı akışı (S-01…S-09)
[ANAYASA KONTROLÜ] … (Ç-14 formatı)
```

---

## SORU (Naci cevaplamalı)

1. **Onay akışı bu PR'da mı?** Önerim **evet** (F10, §3/8): backend'de tam, arayüzsüz kullanılamaz; `docs/gorev-devri-urun2` §6/2 de ilk sırada sayıyor. Alternatif: F1–F9 + F12 ile küçük bir PR, onay akışı ikinci PR — Tansu'nun incelemesi kolaylaşır. (Ben tek PR'dan yanayım ama iki PR'a bölmek de mümkün: `feat/backend-sync-urun1` + `feat/onay-akisi-arayuz`.)
2. **Yönetim › Ayarlar (`enabled_products`, F11)** eklensin mi? Önerim **hayır** (`make set-products` var; T-12 yeni ekran; ürün sahibinin aracı). Evet dersen `AdminLayout`'a dördüncü sekme, üç onay kutusu.
3. **T-12 yaklaşımı:** yeni küçük öğeleri mevcut dil parçalarıyla kodlayıp PR'da "tasarım onayı bekliyor" işaretlemek (önerim) mi, yoksa Tansu canvas'ta onaylayana kadar F10 arayüzünü **hiç** kodlamamak mı? İkincisi F10'u PR dışına atar (SORU 1 → alternatif).
4. **PR'ı ben açarım, merge etmem** — teyit. PR açıldığında Tansu'ya iletilecek kısa Türkçe özet de hazırlarım (NOT'a da işlenir).

---

## Uygulama sırası (özet)

1. Dal + merge (§6/1) → 2. tipler/roller → 3. cevap/kaynak/dosya linkleri → 4. `proposed`→gerçek (rehber, klasör, arama) → 5. onay akışı → 6. dev VM canlı doğrulama (submodule geçici checkout) → 7. docs + PR → dur (merge Tansu'da). company-ai tarafında: NOT güncellemesi (Tansu'ya devredilmiş kalemler "PR'da yapıldı") + bu planın raporu; submodule pini merge sonrası ayrı commit.
