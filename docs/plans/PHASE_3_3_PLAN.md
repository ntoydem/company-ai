# Phase 3.3 — Frontend: Implementation Plan

## Bağlam ve tespitler

Phase 3.2 (`phase-3-2`) backend'i Adım 3'ün ürün yüzeyi için tamamladı: auth, belge listesi/yükleme/indirme,
AI metadata önerisi (admin kabul/red), `/api/ask` sayfa-kaynaklı cevap. Phase 3.3 bunun **ilk gerçek kullanıcı
arayüzü**: Vite + React 18 + TypeScript + react-router + TanStack Query (CLAUDE.md'de **karar verilmiş**,
alternatif önerilmiyor; Next.js yok), Caddy arkasında `http://<vm-ip>:8080`.

Okunanlar: `docs/PHASES.md` (Phase 3.3), `docs/SPEC_02_dokuman_metadata_yetki_ux.md` §1/§4/§5/§8/§9/§13,
`docs/ARCHITECTURE.md` ADR-001/003/004/014/015/018/019/021, `CLAUDE.md` (stack + "V0 kapsamı dışında" listesi);
kod: `backend/app/api/{auth,departments,projects,documents,ask,ask_page,health,router}.py`, `backend/app/schemas/
{auth,department,project,document,ask,authorization}.py`, `backend/app/core/errors.py`, `backend/app/static/ask.html`,
`infra/{docker-compose.yml,Caddyfile,.env.example}`, `Makefile`.

### T1 — Backend API yüzeyi (frontend'in çağıracağı her şey)
| Endpoint | Yetki | Not |
|---|---|---|
| `POST /api/auth/login` `{username,password}` → `CurrentUserResponse` + httpOnly cookie | açık | 401 tek mesaj (enumeration yok), 429 rate limit |
| `POST /api/auth/logout` → 204 | açık | cookie'yi koşulsuz siler |
| `GET /api/auth/me` → `{id, username, display_name, role}` | giriş | **departman üyeliği YOK** (T3) |
| `GET /api/departments` → `[{id,name,slug,parent_id}]` | giriş | **filtrelenmemiş tam ağaç** (T3) |
| `GET /api/projects` / `POST` / `PATCH /{id}` | giriş / admin / admin | |
| `POST /api/documents/upload` (multipart) | giriş | Phase 3.2: `department/subdepartment/project_id/confidentiality` opsiyonel |
| `GET /api/documents?department=&project_id=` → `DocumentListItem[]` | giriş, yetki-filtreli | `subdepartment`/`confidentiality` **yok** (T4) |
| `GET /api/documents/{id}/status` → `{ingestion_status, ingestion_error, page_count}` | giriş | yükleme sonrası polling |
| `GET /api/documents/{id}/download` | giriş, yetkisizse **403** | kabul kriteri 2'nin API tarafı |
| `POST /api/documents/{id}/suggest-metadata` | **admin** | ready değilse 409 |
| `GET /api/documents/{id}/metadata-suggestion` | giriş | 404 = henüz öneri yok |
| `POST …/metadata-suggestion/apply` / `…/reject` | **admin** | apply: yalnızca gövdedeki alanlar yazılır |
| `POST /api/ask` `{question, department?, project_id?}` → `AskResponse` | giriş | `sources[]` = `SourceCard` (title, page_number, document_date, effective_date, version, status, is_current, supersedes_title, superseded_by_title) — **Sor ekranı için hiçbir backend değişikliği gerekmiyor** |
| `GET /ask`, `GET /health` | — | dev sayfası + healthcheck; Caddy'de proxy'lenmeli |

### T2 — Hata gövdesi iki biçimde geliyor
`app/core/errors.py::_response()` → `{"detail": …, "request_id": …}`. `detail` çoğu durumda **düz Türkçe string**
(401/403/404/409/413/415/429/503/500), ama **422'de nesne**: `{"message": "İstek geçersiz.", "errors": [pydantic]}`.
API istemcisi ikisini de tek bir Türkçe mesaja normalize etmeli; `request_id` hata kutusunda küçük yazıyla
gösterilmeli (SPEC_02 §13 — kullanıcı stack trace görmez, ama destek için id görür).

### T3 — Kabul kriteri 2 ("enerji ile Finans kartı görünmez") bugünkü API ile **kurulamıyor**
`/api/departments` yetkiye göre filtrelenmiyor (herkes tam ağacı alır — admin'in proje formu bunu gerektiriyor,
değiştirilmemeli) ve `/api/auth/me` kullanıcının departman üyeliklerini döndürmüyor. Frontend'in "bu kullanıcı
hangi kartları görsün" kararını verecek verisi **yok**. Küçük, geriye uyumlu backend eklemesi şart (§6.1).

### T4 — Belgeler ekranı için `DocumentListItem` eksik
`subdepartment` (Enerji alt kartlarında filtre) ve `confidentiality` (liste sütunu) dönmüyor. `project_id` var ama
proje adı yok — `/api/projects` bir kez çekilip istemci tarafında eşlenir, backend'e alan eklenmez.

### T5 — httpOnly cookie ⇒ frontend token'ı hiç görmez
Auth durumu istemcide JWT okunarak **belirlenemez** (tasarım gereği, ADR-003). Tek doğruluk kaynağı
`GET /api/auth/me`: 200 → giriş yapılmış (kullanıcı bilgisi), 401 → yapılmamış. Login zaten
`CurrentUserResponse` döndürüyor, ayrıca `/me` çağrısı gerekmez.

### T6 — Vite proxy ⇒ CORS'a hiç gerek yok
Frontend yalnızca **göreli** yollar kullanır (`/api/...`). Prod'da Caddy aynı origin'den proxy'ler; dev'de Vite'ın
`server.proxy`'si `/api`, `/health`, `/ask`'i backend'e yönlendirir. Tarayıcı her iki modda da tek origin görür —
backend'e CORS middleware eklenmez (ADR-015 "CORS limited to the Caddy origin" zaten bu anlama geliyor).

### T7 — Caddy ve port kararı zaten verilmiş
ADR-018: "Backend port 8000 is exposed on the host until Caddy arrives (Phase 3.3); afterwards it is closed to the
compose network." `infra/.env.example`'daki `BACKEND_PORT` yorumu da aynısını söylüyor. `caddy` servisi compose'da
placeholder olarak (`profiles: ["web"]`) ve `infra/Caddyfile` "arayüz Phase 3.3'te eklenecek" cevabıyla duruyor.

### T8 — Playwright / UI testi V0 kapsamı **dışında**
CLAUDE.md "V0 kapsamı dışında" listesinde açıkça: "Playwright/UI testleri". ADR-019: "frontend adds `eslint` +
`tsc` in Phase 3.3". Dolayısıyla kanıt = eslint + tsc (otomatik) + **tarayıcıda elle uçtan uca doğrulama**
(CLAUDE.md: "UI değişikliklerinde dev server'ı başlat, tarayıcıda kullan"), Playwright yazılmaz.

---

## 1. Proje iskeleti — `frontend/`

```
frontend/
  package.json  vite.config.ts  tsconfig.json  .eslintrc.cjs  index.html  Dockerfile
  src/
    main.tsx            React root + QueryClientProvider + RouterProvider
    router.tsx          rota ağacı (aşağıda)
    api/
      client.ts         fetch sarmalayıcı: göreli URL, credentials: "same-origin", JSON, hata normalizasyonu (T2)
      types.ts          backend şemalarının TS karşılıkları (CurrentUser, Department, Project, DocumentListItem,
                        DocumentStatus, MetadataSuggestion, AskResponse/SourceCard) — elle yazılır, küçük
      auth.ts documents.ts ask.ts projects.ts departments.ts   uç başına fonksiyon + TanStack Query hook'ları
    auth/
      AuthProvider.tsx  `useQuery(["me"])` sarmalayan context; `useAuth()` → {user, isLoading, logout}
      RequireAuth.tsx   yükleniyorsa spinner, 401 ise `/giris`'e yönlendir (dönüş yolu `state.from`)
    pages/  Login, Home, Department (+ AskTab, DocumentsTab, UploadTab, ProjectsTab), Ask
    components/  DepartmentCard, DocumentTable, SourceCardList, MetadataSuggestionPanel, ErrorBox, Spinner, Layout
    lib/
      strings.ts        TÜM Türkçe UI metinleri tek dosyada (i18n kütüphanesi yok — tek dil, ama tek yerde)
      format.ts         tarih DD.MM.YYYY (tr-TR), durum/gizlilik etiket eşlemeleri
      visibility.ts     kart görünürlük kuralı (§2.2)
```

- **Paket yöneticisi:** `npm` (Vite varsayılanı, ek araç yok). Node 20 LTS (Docker'da `node:20-alpine`).
- **Bağımlılıklar (minimum):** `react`, `react-dom`, `react-router-dom`, `@tanstack/react-query`. Ek UI kütüphanesi,
  Redux/Zustand, axios, form kütüphanesi **yok** — uygulama küçük, `fetch` + TanStack Query + React `useState`
  yeter; `ask.html`'in mevcut sade CSS token'ları (`--bg/--card/--line/--accent`) tek bir `styles.css`'e taşınır.
- **Rotalar (react-router v6, nested):**
  ```
  /giris                          Login (giriş yapılmışsa / 'e yönlendir)
  /                               Home — RequireAuth
  /sor                            Genel Sor (department yok) — RequireAuth
  /departman/:slug                Department layout (başlık + sekmeler) — RequireAuth
     index  → sor                 AskTab   (department=slug ile /api/ask)
     belgeler                     DocumentsTab
     yukle                        UploadTab (+ öneri paneli)
     projeler                     ProjectsTab
  ```
  Bilinmeyen/yetkisiz slug → Home'a yönlendir (§2.2 kuralıyla).
- **Durum yönetimi:** sunucu durumu = TanStack Query (`["me"]`, `["departments"]`, `["projects"]`,
  `["documents", scope]`, `["suggestion", id]`); UI durumu = yerel `useState`. Login/logout `["me"]`'yi
  `invalidate`/`setQueryData` eder — başka global store yok.

## 2. Ekranlar

### 2.1 Giriş (`/giris`)
Kullanıcı adı + şifre; `POST /api/auth/login`; 401 → "Kullanıcı adı veya şifre hatalı." (backend mesajı aynen),
429 → backend mesajı. Başarıda `["me"]` cache'i login cevabıyla doldurulur, `state.from` veya `/`'e gidilir.

### 2.2 Ana sayfa (`/`) — departman kartları + Genel Sor
- Kartlar `GET /api/departments`'tan **`parent_id === null`** olanlar (ENERJİ GRUBU, FİNANS, HUKUK, MALİ İŞLER,
  İDARİ İŞLER — seed ile birebir; hard-code edilmez).
- **Görünürlük kuralı (kabul kriteri 2):** `user.role !== "employee" || user.department_slugs.includes(card.slug)`
  (`department_slugs` = §6.1'in eklediği alan; admin/management için boş kalır, kural zaten rolle kısa devre yapar).
  Enerji'nin alt kartları (Geliştirme/EPC-İnşaat/Bakım = `parent_id === enerji_grubu.id`) **ayrı görünürlük
  kontrolü taşımaz** — alt departman yetki birimi değil (Phase 1.2 T7), üst kart görünüyorsa hepsi görünür.
- Gizleme yalnızca UX; güvenlik backend'de (ADR-004). Kart gizli olsa da URL'ye `/departman/finans` yazan `enerji`
  için: liste boş döner, indirme 403 döner, sor "bilgi bulamadım" döner — ekran bunları olduğu gibi gösterir,
  ayrıca §2.2 kuralına göre bilinen-ama-yetkisiz slug'da Home'a yönlendirir.
- "Genel Sor" büyük buton → `/sor`.

### 2.3 Departman ekranı (`/departman/:slug`)
Başlık (departman adı) + Enerji için alt kart şeridi (seçim = `subdepartment` filtresi, yalnızca Belgeler sekmesini
etkiler — `/api/ask` alt departman almıyor, Sor sekmesi her zaman `department=enerji_grubu` ile çalışır; bu
sınırlama ekranda küçük notla belirtilir) + 4 sekme:
- **Sor** — §2.6'daki Ask bileşeni, `department=slug` sabit.
- **Belgeler** — `GET /api/documents?department=slug`; tablo: başlık, tür, muhatap, tarih, durum, gizlilik,
  işlem durumu (`ingestion_status` rozeti: işleniyor/hazır/hata + `ingestion_error`), proje adı (istemci tarafı
  `/api/projects` eşlemesi), alt departman; indir butonu (`/download`); Enerji'de alt-kart filtresi
  (`subdepartment` alanı, istemci tarafı). Satıra tıklayınca detay/öneri paneli (SORU 1).
- **Yükle** — §2.4.
- **Projeler** — `GET /api/projects` içinden `department_ids` bu departmanı içerenler (ad, kod, aşama, aktif);
  **admin için** "Yeni proje" + satır düzenleme (`POST`/`PATCH`, `department_ids` çoklu seçim `/api/departments`'tan) —
  SORU 3.

### 2.4 Belge Yükle (departman sekmesi) — form + AI önerisi
1. Form (SPEC_02 §1): dosya (pdf/png/jpg), başlık, belge türü, muhatap, belge tarihi, durum
   (`draft/executed/amended`), gizlilik (`normal/restricted/board`), proje (opsiyonel, `/api/projects`), alt departman
   (yalnızca Enerji, opsiyonel), yürürlük tarihi + versiyon + "şu belgeyi değiştirir" (opsiyonel, `supersedes_
   document_id` = aynı departmanın Belgeler listesinden seçim). `department` sekmenin slug'ı, form alanı değil.
2. `POST /upload` (multipart, ilerleme çubuğu yok — V0 sadeleştirmesi) → `{id, ingestion_status}`.
3. `GET /{id}/status` 3 sn'de bir polling → `ready`/`failed`. `failed` → `ingestion_error` Türkçe gösterilir.
4. `ready` sonrası `GET /{id}/metadata-suggestion` polling (arka plan tarama 15 sn'de bir çalışıyor, Phase 3.2):
   404 → "Öneri hazırlanıyor…"; admin'e ayrıca "Şimdi üret" (`POST /suggest-metadata`).
5. **Öneri paneli** (`MetadataSuggestionPanel`): her alan için önerilen değer + confidence çubuğu + mevcut değer;
   **admin:** her alan düzenlenebilir + "Uygula" (`apply`, yalnızca değiştirilen/işaretlenen alanlar gövdeye girer —
   SPEC_02 §4 "sessiz overwrite yok" UI'da da: kutucuğu işaretlenmeyen alan gönderilmez) + "Reddet"; **admin
   olmayan:** salt-okunur + "Öneriyi yalnızca yönetici uygulayabilir" notu (Phase 3.2 SORU 2). `status: failed` →
   `error` gösterilir, admin'e "Tekrar dene".

### 2.5 Belgeler (`/departman/:slug/belgeler`) — §2.3'te.

### 2.6 Sor (`/sor` ve departman sekmesi)
`ask.html`'in yapısı React'e taşınır: soru kutusu (3–1000 karakter, backend ile aynı sınır), örnek soru linkleri,
cevap alanı, **kaynak kartları** = `SourceCard`: `[K1]` etiketi, belge adı, **sayfa**, tarih (`document_date`,
varsa `effective_date`), versiyon, durum rozeti, `is_current` → "GÜNCEL" rozeti, `supersedes_title`/
`superseded_by_title` → "…'i değiştirir / … tarafından değiştirildi" satırı, indir linki. Proje adı: `SourceCard`
`project_id` taşımıyor — kart üzerinde proje, belge listesi cache'inden (`document_id` eşlemesi) veya SORU 1'in
detay ucundan alınır; bulunamazsa gösterilmez (backend'e alan eklenmez, SPEC "section" alanı da V0'da yok —
sayfa numarası bunu karşılıyor, ADR-008). `answered: false` → cevap gri, kaynak yok. `notice` alanı ("Bu cevap
yorum içermez…") her cevabın üstünde (SPEC_02 §8 kural-6 notu). 503 → backend'in Türkçe mesajı ("Yapay zeka
servisi…"). `model`/token sayıları küçük gri satırda.

## 3. Caddy + compose

- **`infra/caddy/Dockerfile` (yeni, çok aşamalı):** `node:20-alpine` aşaması `frontend/`'i `npm ci && npm run
  build` ile derler → `caddy:2-alpine` aşaması `dist/`'i `/srv`'ye, `infra/Caddyfile`'ı `/etc/caddy/`'ye kopyalar.
  Statik dosyalar Caddy imajının **içinde** — ayrı "frontend" runtime container'ı yok (ADR-001 "minimal moving
  parts"; servis sayısı değişmiyor). Compose: `caddy: build: {context: ., dockerfile: infra/caddy/Dockerfile}`
  (bağlam repo kökü; `frontend/` + `infra/Caddyfile`'a erişmesi gerekiyor), `profiles: ["web"]` **kaldırılır**
  (artık placeholder değil, çekirdek servis) — SORU 2.
- **`frontend/Dockerfile` (yeni, ayrı, tek aşama `node:20-alpine` + `npm ci`):** yalnızca `docker compose run
  --rm --no-deps frontend sh -c 'npm run lint && npm run typecheck'` için (`backend`'in ruff/mypy deseniyle aynı).
  `npm ci` iki imajda tekrar ediyor (lint imajı + caddy'nin build aşaması) — çapraz-servis build koordinasyonu
  yerine bilinçli, basit tekrar. Compose'da `frontend` servisi `profiles: ["tools"]` (hiç `up` edilmez, yalnızca `run`).
- **`infra/Caddyfile`:**
  ```
  :80 {
    handle /api/*  { reverse_proxy backend:8000 }
    handle /health { reverse_proxy backend:8000 }
    handle /ask    { reverse_proxy backend:8000 }   # Phase 0.3 dev sayfası kalır (ADR-021)
    handle {
      root * /srv
      try_files {path} /index.html                 # SPA: react-router derin linkleri
      file_server
    }
  }
  ```
- **Backend host portu kapanır (ADR-018):** `backend.ports` compose'dan silinir; `BACKEND_PORT` `.env.example`'da
  kalır ama yorumu "yalnızca `scripts/wait_for_services.sh` ve Vite dev proxy hedefi" olur. `curl localhost:8000`
  artık çalışmaz; her şey `:$CADDY_PORT` (`/api/*`, `/health`, `/ask`). `scripts/wait_for_services.sh` `/health`'i
  Caddy üzerinden bekleyecek şekilde güncellenir. SORU 2.
- **Makefile:** `up` → `postgres backend ocr-worker caddy` (build dahil); `lint` → + frontend eslint/tsc;
  yeni `build-frontend` (yalnızca caddy imajını yeniden derler, `make up` zaten yapıyor) ve `dev-frontend`
  (`docker compose run --rm --service-ports frontend npm run dev -- --host` → Vite HMR `:5173`, `/api`'yi
  `backend:8000`'e proxy'ler; günlük geliştirme için, `make up` çalışırken).
- **Vite dev proxy:** `vite.config.ts` `server.proxy`: `/api`, `/health`, `/ask` → `VITE_DEV_API_TARGET`
  (varsayılan `http://backend:8000`, container içinden). Tek kod yolu, her modda göreli URL (T6).

## 4. Türkçe metinler, responsive, hata mesajları

- **Metinler:** `src/lib/strings.ts` tek kaynak (tüm etiket, buton, boş-durum, doğrulama metinleri). Backend'den
  gelen `detail` **olduğu gibi** gösterilir (zaten Türkçe, SPEC_02 §13) — frontend yeniden çevirmez. Enum'lar
  (`status`, `confidentiality`, `ingestion_status`, `stage`, `role`) `format.ts`'te Türkçe etikete eşlenir
  (`executed` → "İmzalandı", `superseded` → "Yerini yenisi aldı", `restricted` → "Kısıtlı", `board` → "Yönetim
  kurulu"…); tarihler `DD.MM.YYYY` (CLAUDE.md), sayılar backend'den geldiği biçimde.
- **Hata gösterimi (T2):** `client.ts` → `ApiError {status, message, requestId, fieldErrors?}`; `message` =
  `detail` string ise o, nesne ise `detail.message` (+ 422'de alan hataları formun altına). `ErrorBox` bileşeni
  mesaj + küçük `İstek no: <request_id>`. Ağ hatası → "Sunucuya ulaşılamadı." (frontend metni). Hiçbir yerde
  `JSON.stringify(err)`/stack yok. 401 (oturum süresi doldu, 8 saat) → `["me"]` sıfırlanır, `/giris`'e dönüş yolu ile.
- **Responsive:** tek sütun ≤ 640px (kartlar dikey, tablo → satır-kart), ≥ 641px grid; `ask.html`'in mevcut
  basit token'ları, CSS framework yok (SPEC_02 §8 "tasarım süsü değil, okunabilirlik"). Sekmeler dar ekranda yatay
  kaydırma.

## 5. Kabul kriteri → kanıt

| Kriter (PHASES.md) | Otomatik | Elle (tarayıcı, `http://<vm-ip>:8080`, rapora ekran görüntüsü) |
|---|---|---|
| `http://<vm-ip>:8080` uçtan uca | `make up` + `wait_for_services.sh` Caddy üzerinden `/health` yeşil; `make lint` (eslint+tsc) temiz | admin ile giriş → Ana sayfa 5 kart → Finans → Belgeler (15 demo belgeden finans'ınkiler) → Sor ("güncel DSCR" → cevap + `[K1]` kartı sayfa/tarih/versiyon/GÜNCEL rozeti) → çıkış |
| `enerji` ile Finans kartı görünmez **VE** API 403 | Backend zaten: `test_documents.py::test_employee_download_other_department_document_returns_403`, `::test_employee_list_excludes_other_department_documents`; yeni: `test_auth.py` `/me` `department_slugs` testi (§6.1) | `enerji` ile giriş → Ana sayfada yalnızca ENERJİ GRUBU (+ alt kartlar); adres çubuğuna `/departman/finans` → Home'a yönlendirme; DevTools Network'te bir finans belgesinin `/download` isteği **403** ve gövdesi "Bu belgeye erişim yetkiniz yok."; Sor'da finans sorusu → "bilgi bulamadım" |
| Yükleme akışı çalışır | Backend upload/öneri testleri (Phase 3.2, 191 test) | `admin` ile Finans → Yükle: küçük bir PDF, form doldur → "işleniyor" → `ready` → öneri paneli dolar (arka plan tarama ≤ 15 sn) → bir alanı düzenle, iki alanı işaretle, Uygula → Belgeler listesinde güncel değerler; `enerji` ile aynı ekran: panel salt-okunur + yönetici notu |
| Hata mesajları Türkçe, stack trace yok | `make lint`; backend `test_errors.py` mevcut | yanlış şifre (401), `.exe` yükleme (415), 60 MB dosya (413), LLM anahtarı boş `.env` ile Sor (503 "Yapay zeka servisi yapılandırılmamış."), backend'i durdurup Sor ("Sunucuya ulaşılamadı.") — hepsinde yalnızca Türkçe cümle + istek no |

Playwright/UI otomasyonu **yok** (T8). Elle doğrulama adımları raporda ekran görüntüleriyle belgelenir
(`docs/reports/assets/phase_3_3/`), Phase 3.1'deki gibi.

## 6. Backend eklemeleri (bu fazın parçası, küçük ve geriye uyumlu)

1. **`CurrentUserResponse.department_slugs: list[str]`** — `user.departments` ilişkisinden doğrudan üyelik slug'ları
   (admin/management için boş). `/login` ve `/me` ikisi de döner. Test: `test_auth.py`'ye `enerji` için
   `["enerji_grubu"]`, `yonetim` için `[]`. Kabul kriteri 2 bunsuz kurulamaz (T3).
2. **`DocumentListItem` += `subdepartment: str | None`, `confidentiality: Confidentiality`** (T4). Mevcut testler
   tam-dict eşitliği yapmıyor, kırılma beklenmiyor.
3. SORU 1'e bağlı: `GET /api/documents/{id}` detay ucu (varsa `_get_authorized_document` ile, `DocumentListItem`
   şeması + `tags`, `version`, `effective_date`, `supersedes_document_id`, `related_document_ids`).

Başka backend değişikliği yok: `/api/ask`, upload, öneri uçları olduğu gibi.

---

## SORU (Naci cevaplamalı)

1. **Belge detayı:** Belgeler listesinde satıra tıklayınca / Sor kaynak kartından belgeye giderken tam metadata için
   (a) yeni `GET /api/documents/{id}` ucu mu (temiz REST, derin linkte ve sayfa yenilemede güvenilir — **önerim**),
   yoksa (b) hiç backend değişikliği yapmadan liste sorgusunun TanStack cache'inden mi bulunsun (sayfa yenilenince
   listeyi yeniden çekip içinden arar; daha az kod, ama dolaylı)?
2. **`make up` artık Caddy'yi de başlatsın ve backend'in host portu (8000) kapansın** (ADR-018 + `.env.example`
   yorumu zaten böyle diyor) — onaylıyor musun? Sonuç: `curl localhost:8000` biter, her şey `:8080`; `make
   dev-frontend` (Vite HMR :5173) günlük geliştirme için eklenir. Alternatif: `up` değişmez, yeni `up-web` hedefi
   ve 8000 açık kalır (ADR-018'den sapma, ADR güncellenir).
3. **Proje CRUD formu:** SPEC_02 §8 "Projeler" sekmesini listeliyor ama oluştur/düzenle formundan söz etmiyor;
   backend admin CRUD'u Phase 1.2'den beri hazır ve başka arayüzü yok. Bu fazda admin'e "Yeni proje" + düzenleme
   formu eklensin mi (**önerim: evet**, aksi halde proje oluşturmanın hiçbir UI yolu kalmıyor), yoksa Phase 5.2
   Admin panel'e mi bırakılsın (bu fazda salt-okunur liste)?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- Stack CLAUDE.md'de sabit: Vite + React 18 + TS + react-router + TanStack Query; **ek** bağımlılık yok (axios,
  Redux/Zustand, UI kit, form/i18n kütüphanesi yok). `npm`, Node 20.
- Auth durumu = `/me` sorgusu, istemcide JWT ayrıştırma yok (T5); global store yok.
- Tek origin, göreli URL, CORS yok (T6). Vite dev proxy container içinden `backend:8000`'e.
- Statik dosyalar Caddy imajına gömülü (çok aşamalı build); lint için ayrı hafif `frontend` servisi
  (`profiles: ["tools"]`); `npm ci` iki imajda bilinçli tekrar.
- Departman kartları `/api/departments`'tan (`parent_id === null`), hard-code yok; görünürlük kuralı §2.2, alt
  kartlar ayrı kontrol taşımaz (Phase 1.2 T7).
- Enerji alt kartı yalnızca Belgeler sekmesini filtreler (`subdepartment`, istemci tarafı); Sor her zaman
  `department=enerji_grubu` (backend alt departman almıyor) — ekranda notla belirtilir. Sunucu tarafı
  `subdepartment` filtresi **eklenmez**.
- Proje adı istemci tarafı eşleme (`/api/projects` bir kez), backend'e alan eklenmez.
- Öneri paneli: apply gövdesine yalnızca kullanıcının işaretlediği alanlar girer (SPEC_02 §4'ün UI karşılığı).
  `status` seçenekleri UI'da `draft/executed/amended` (Phase 3.2 kararıyla tutarlı; API daha fazlasına izin verse de).
- Yükleme ilerleme çubuğu yok; `/status` ve `/metadata-suggestion` 3 sn polling (WebSocket/SSE yok — V0).
- `ask.html` dev sayfası kalır, Caddy `/ask`'i proxy'ler (ADR-021).
- `make down`'daki `--profile web` kaldırılır (caddy artık profilsiz), `--profile full` kalır.

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: ADR-018'e "Phase 3.3: yapıldı" notu (port kapandı, Caddy imajı statikleri taşır, Vite
  proxy/CORS yok); ADR-019'a frontend eslint+tsc'nin `make lint`'e eklendiği; ADR-003'e "auth durumu `/me` ile" notu.
  Yeni ADR **açılmıyor** (SORU 2 alternatif seçilirse ADR-018 güncellenir).
- `README.md`: "Arayüz (Phase 3.3)" bölümü — `make up` → `http://<vm-ip>:8080`, demo hesaplarıyla tur, `make
  dev-frontend`; "Belge yükleme"/"Soru sorma" bölümlerindeki `localhost:8000` örnekleri `:8080`'e; "Repo düzeni"'ne
  `frontend/`; "Make hedefleri" tablosu.
- `infra/.env.example`: `BACKEND_PORT` yorumu; `VITE_DEV_API_TARGET` **eklenmez** (compose ortamında sabit).
- `docs/reports/PHASE_3_3_REPORT.md` (+ `assets/phase_3_3/` ekran görüntüleri), `docs/PHASES.md` durum satırı,
  `git tag phase-3-3`.

## Uygulama sırası

1. Backend eklemeleri (§6.1, §6.2, SORU 1'e göre §6.3) + testleri; `make test` yeşil.
2. `frontend/` iskeleti: Vite+React+TS, eslint/tsc, `Dockerfile`, compose `frontend` servisi, `make lint` genişlemesi.
3. `api/client.ts` + `types.ts` + hata normalizasyonu; `AuthProvider`/`RequireAuth`; Login; Layout (üst bar:
   kullanıcı adı/rol, çıkış).
4. Home (kartlar + görünürlük kuralı) → Department layout + sekmeler → Belgeler → Sor (kaynak kartları) →
   Yükle + öneri paneli → Projeler (SORU 3'e göre form).
5. `infra/caddy/Dockerfile`, `Caddyfile`, compose (`caddy` profilsiz, `backend.ports` silinir), `wait_for_services.sh`,
   Makefile `up`/`build-frontend`/`dev-frontend`.
6. Tarayıcıda §5 elle doğrulama (admin, enerji, finans hesaplarıyla), ekran görüntüleri.
7. README/ADR notları → `make test` + `make lint` yeşil → rapor → `docs/PHASES.md` → commit + tag `phase-3-3` + push.

## Kritik dosyalar

- `frontend/src/api/client.ts`, `frontend/src/auth/{AuthProvider,RequireAuth}.tsx`, `frontend/src/lib/visibility.ts`
- `frontend/src/pages/{Home,Department,Ask}.tsx`, `frontend/src/components/{SourceCardList,MetadataSuggestionPanel}.tsx`
- `infra/caddy/Dockerfile`, `infra/Caddyfile`, `infra/docker-compose.yml`, `Makefile`, `scripts/wait_for_services.sh`
- `backend/app/schemas/{auth,document}.py`, `backend/app/api/{auth,documents}.py` (§6)
