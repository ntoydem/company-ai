# AI-BalBal'ı Caddy'den sunma — Uygulama Planı

**Tarih:** 30.09.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Hedef: `http://<vm-ip>:8080` açıldığında company-ai'ın emekli `frontend/`'i yerine **AI-BalBal** (`github.com/ftansu/AI-BalBal`, `frontend/` alt klasörü) görünsün; backend, Caddyfile ve `/api` sözleşmesi değişmesin; tek bir değişkenle eski arayüze dönülebilsin. Kapsam B-27'nin "AI-BalBal'ı sun" kısmıdır (NOT §1 B-27, §3.2); erişim yolu Tailscale/LAN düz HTTP olarak kalır (ADR-015).

Okunanlar: `infra/docker-compose.yml`, `infra/Caddyfile`, `infra/caddy/Dockerfile`, `frontend/{Dockerfile,vite.config.ts,package.json,.dockerignore}`, `Makefile` (`up`, `dirs`, `build-frontend`, `dev-frontend`, `lint`), `scripts/wait_for_services.sh`, `infra/.env.example`, `.gitignore`, README "Arayüz (Phase 3.3)" / "Kurulum", ADR-018 (Phase 3.3 concretization), SPEC_06 §6. AI-BalBal salt okunur klon @ `b219600` (= `main` ucu, 29.09.2026): `frontend/{package.json,vite.config.ts,Dockerfile,.dockerignore,index.html}`, `src/api/client.ts`, `src/router.tsx`, `src/styles.css`, `README.md`; uzak dallar: `main`, `feat/urun1-arayuz`, `docs/ekip-sohbeti-ve-netlik` (ikisi `main`'e girmemiş). Ortam: Docker 29.8.1 (BuildKit), Compose **v5.5.1**, git 2.43.

---

## 1. Tespitler

- **T1 — İki frontend yapısal olarak ikiz.** AI-BalBal `frontend/` ile company-ai `frontend/` aynı `package.json` (ad bile `company-ai-frontend`), aynı `vite.config.ts` (dev proxy `/api`, `/health`, `/ask` → `VITE_DEV_API_TARGET`), aynı `Dockerfile`/`.dockerignore` (`node_modules`, `dist`), aynı `npm run build = vite build`. Dolayısıyla **mevcut `infra/caddy/Dockerfile` değişmeden AI-BalBal'ı derleyebilir**; değişmesi gereken yalnızca build **context**'idir.
- **T2 — API adresi zaten göreli.** `client.ts` `fetch(path, {credentials: "same-origin"})` ile `/api/...` çağırıyor; `import.meta.env.VITE_*` yok, mutlak URL yok (`vite.config.ts`'teki `http://backend:8000` yalnızca dev proxy hedefi). `createBrowserRouter` `basename`'siz, Vite `base` varsayılan `/`. Aynı origin → CORS yok, cookie (`SameSite=Lax`, ADR-003) aynen çalışır. **Backend'de ve Caddyfile'da sıfır değişiklik.**
- **T3 — Rota çakışması yok.** AI-BalBal istemci rotaları `/giris`, `/`, `/sor`, `/departman/:slug/*`, `/yonetim/*`, `*`; Caddy'nin backend'e proxy'lediği `/api/*`, `/health`, `/ask` ile kesişmiyor. SPA fallback (`try_files … /index.html`) yeterli.
- **T4 — Build context bugün sabit `./frontend`.** `docker-compose.yml` `caddy.build.context: ./frontend`, `dockerfile: ../infra/caddy/Dockerfile` (context'e göreli). Context'i env'den seçilebilir yapınca `dockerfile`'ın göreli yolu klasör derinliğine göre bozulur (`frontend-balbal/frontend` için `../../infra`). Compose v5.5.1 `build.additional_contexts` destekliyor (v2.17+): Dockerfile `infra/caddy/`'de sabit kalır, **kaynak** ikinci bir adlandırılmış context olarak `${FRONTEND_DIR}`'den gelir. Bu, T1'in "Dockerfile değişmez" sonucunu korur ve rollback'i tek değişkene indirir.
- **T5 — `.dockerignore` yalnızca ana context'e uygulanır.** Adlandırılmış context'te `node_modules`/`dist` filtrelenmez; dev VM'de biri `frontend-balbal/frontend`'de `npm install` çalıştırırsa `COPY . .` yüz MB'ları taşır. Dockerfile bu yüzden **açık dosya listesi** kopyalar (`package.json package-lock.json` → `npm ci` → `index.html vite.config.ts tsconfig.json tsconfig.node.json src/`). İki frontend'in dosya düzeni aynı olduğu için (T1) aynı liste eski arayüz için de geçerli.
- **T6 — Sağlık kontrolü ve compose ağı değişmiyor.** `scripts/wait_for_services.sh` yalnızca `/health`'i yoklar; `backend` host portu kapalı (ADR-018); `${DATA_ROOT}/app-data/caddy` mount'u, `CADDY_PORT` aynı.
- **T7 — Bundle'ı ayırt eden işaret.** İki `index.html`'in `<title>`'ı da "Company AI" — başlık ayırt etmez. AI-BalBal `src`'sinde "Balbal" 14 dosyada geçiyor (`strings.ts:4 app: "Balbal"`, `"Balbal'a Sor"`), company-ai `frontend/src`'de **0**. Kabul testi bu yüzden servis edilen JS bundle'ında "Balbal" arar (§5).
- **T8 — Dış bağımlılık: Google Fonts.** AI-BalBal `styles.css:1` `fonts.googleapis.com`'dan CSS import ediyor (tarayıcı tarafı). LAN/VPN'de tarayıcının internete çıkışı yoksa yazı tipleri sistem fontuna düşer, uygulama çalışır; backend'i ilgilendirmez. Tansu'ya bilgi notu (SORU 5).
- **T9 — Dondurulmuş sürüm Aşama A alanlarını göstermez.** `b219600`, `SourceCard` id'lerini (`types.ts`'te yok) ve `warnings`/`product_level`'ı bilmiyor; **görünür** olan tek Aşama A etkisi `enabled_products` (ekip sohbeti launcher'ı `Layout.tsx:27`, "Gündeminiz" `Home.tsx:73`). "Versiyon linki çalışıyor" kabulü bu sürümle tarayıcıda **kanıtlanamaz**; ağ sekmesinde alanın geldiği gösterilir, link Tansu'nun `SourceCardList` değişikliğiyle gelir (§5, SORU 2).
- **T10 — Repoya dahil etme.** Üç yol: (a) **git submodule** `frontend-balbal/` → `https://github.com/ftansu/AI-BalBal.git`, sabit commit; (b) kopyalayıp vendor'lamak (28 dosya zaten bayt bayt ikiz, provenans kaybolur, her Tansu güncellemesi elle diff); (c) repo dışı kardeş klasör + `.env` yolu (prod klonunda "git clone + .env + make up" akışı bozulur, hangi sürümün yayında olduğu git geçmişinde görünmez). Öneri **(a)**: hangi AI-BalBal commit'inin yayında olduğu company-ai geçmişinde bir pointer olarak durur, güncelleme = pointer'ı ilerleten bir commit. Repo public, kimlik bilgisi gerekmez.

---

## 2. Tasarım

### 2.1 Dahil etme: submodule `frontend-balbal/` (SORU 1)

- `git submodule add https://github.com/ftansu/AI-BalBal.git frontend-balbal` → `.gitmodules` + pointer **`b219600`** (SORU 2). Build context: `frontend-balbal/frontend`.
- company-ai `frontend/` **silinmez, taşınmaz, dokunulmaz** (NOT §4.4); yalnızca Caddy artık onu derlemez. `frontend` tooling servisi (`make lint`, `make dev-frontend`) `./frontend`'e bağlı kalır (SORU 4).
- Submodule'ün boş kalmaması `make up`'a bağlanır: `dirs` hedefine `@git submodule update --init frontend-balbal` (idempotent; klon zaten varsa no-op, `.git` yoksa — örn. tarball — atlanır). Prod klonu için README'ye `git clone --recurse-submodules` yazılır ama şart değildir. `--depth` kullanılmaz (repo küçük; sığ submodule'de sabit SHA fetch'i sunucu ayarına bağlı).
- `.gitignore`: `frontend-balbal/frontend/node_modules/`, `frontend-balbal/frontend/dist/` gerekmez (submodule'ün kendi `.gitignore`'u var ve içerik submodule'e ait), eklenmez.

### 2.2 Build: `additional_contexts` + açık kopya listesi

`infra/docker-compose.yml` (`caddy` servisi):
```yaml
build:
  context: ./infra/caddy
  additional_contexts:
    src: ${FRONTEND_DIR:-./frontend-balbal/frontend}
```
`infra/caddy/Dockerfile`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=src package.json package-lock.json ./
RUN npm ci
COPY --from=src index.html vite.config.ts tsconfig.json tsconfig.node.json ./
COPY --from=src src ./src
RUN npm run build
FROM caddy:2-alpine
COPY --from=build /app/dist /srv
```
- `infra/caddy/` ana context olduğu için oradaki `.dockerignore` gereksiz; klasörde yalnızca Dockerfile var.
- `${FRONTEND_DIR}` compose interpolasyonuyla önce **shell env**, sonra `.env`'den okunur; `infra/.env.example`'a yorumlu satır eklenir (varsayılan boş = AI-BalBal): `# Caddy'nin derleyip sunduğu arayüz kaynağı. Boş = AI-BalBal (frontend-balbal/frontend). Eski arayüz: FRONTEND_DIR=./frontend`.
- `make build-frontend` aynı kalır (`compose build caddy`); `make up` zaten `--build`.
- Yeni hedef `make update-frontend REF=<sha|main>`: `git -C frontend-balbal fetch origin && git -C frontend-balbal checkout $(REF) && $(COMPOSE) up -d --build caddy`. Pointer'ı commit etmek **insan işi** (hangi Tansu commit'inin yayına alındığı bilinçli bir karardır; BACKEND_GAPS dondurmasından bağımsız). Hedef `REF` boşsa hata.

### 2.3 API base URL

T2 gereği iş yok. Kanıt: bundle'da `fetch(` çağrıları göreli; Caddy `/api/*` → `backend:8000`. Cookie `path=/`, `SameSite=Lax`, `secure=false` (ADR-015) — AI-BalBal aynı origin'de olduğu için birebir çalışır; 401'de `UNAUTHORIZED_EVENT` ile oturum düşmesi de aynı (`client.ts:5`).

### 2.4 Rollback

Tek değişken: `.env`'e `FRONTEND_DIR=./frontend` (ya da shell'de `FRONTEND_DIR=./frontend make build-frontend`) → `make up` (veya `docker compose up -d --build caddy`). Caddyfile, backend, veri, cookie, portlar değişmediği için oturumlar bile korunur. Geri dönüş: değişkeni sil → `make up`. Submodule'e dokunulmaz. Kabul testinde iki yöne de gidilir (§5 A6).

### 2.5 Dokunulmayanlar

Backend kodu, `infra/Caddyfile`, `scripts/wait_for_services.sh`, `${DATA_ROOT}` düzeni, `make lint`/`make test`, company-ai `frontend/`, AI-BalBal reposu (Tansu'nun; company-ai yalnızca pointer tutar).

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `.gitmodules` (yeni), `frontend-balbal/` (submodule @ `b219600`) | §2.1 |
| `infra/docker-compose.yml` | `caddy.build`: `context: ./infra/caddy` + `additional_contexts.src`; yorum güncellenir |
| `infra/caddy/Dockerfile` | `COPY --from=src …` açık liste (T5) |
| `infra/.env.example` | `FRONTEND_DIR` yorumlu satır |
| `Makefile` | `dirs`: submodule init; `update-frontend REF=…`; `build-frontend`/`up` açıklamaları |
| `README.md` | Kurulum (`--recurse-submodules` notu), "Arayüz" bölümü (AI-BalBal, `FRONTEND_DIR`, rollback, `make update-frontend`), Make hedefleri tablosu |
| `docs/ARCHITECTURE.md` | ADR-018'e concretization satırı (build context ayrımı, submodule, rollback değişkeni); ADR-001/yeni ADR gerekmez — topoloji aynı |
| `docs/PHASES.md` | Adım 5 altına kısa not (Aşama A notunun yanına), commit hash'i |
| `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` | §1 B-27 satırı → "sunma kısmı UYGULANDI"; §4.4 "AI-BalBal artık Caddy'den sunuluyor" |
| `docs/reports/AIBALBAL_DEPLOY_REPORT.md` | Şablonla rapor |

---

## 4. Uygulama sırası

1. Submodule ekle, pointer `b219600`; `git status` temiz.
2. Dockerfile + compose + `.env.example`; `docker compose build caddy` (AI-BalBal) → imaj boyutu/süre not.
3. Makefile (`dirs`, `update-frontend`); `make up` → `wait_for_services` yeşil.
4. §5 kabul testleri A1–A6 (A2/A3 tarayıcı adımları Naci).
5. Docs (README, ADR-018, PHASES, NOT) → rapor → commit + push (etiket yok, Aşama A ile aynı kural — SORU 6).

---

## 5. Kabul kriterleri ve kanıt

| # | Kriter | Kanıt |
|---|---|---|
| A1 | `make up` sonrası `:8080` **AI-BalBal** sunuyor | `curl -s localhost:8080/` → `index.html`'deki `/assets/index-*.js` yolu alınır, `curl -s localhost:8080/assets/index-*.js \| grep -c "Balbal'a Sor"` ≥ 1 (company-ai bundle'ında 0, T7); `docker compose images caddy` yeni imaj |
| A2 | Tarayıcıdan giriş | Naci elle: `http://<vm-ip>:8080` → Balbal markalı giriş kartı; `finans` ile giriş; ana sayfa departman kartları + Balbal launcher; `/departman/finans` belge listesi dolu; `/api/auth/me` ağ sekmesinde `enabled_products: ["P1","P2","P3"]` |
| A3 | Aşama A alanları | **Ürün paketi:** ekip sohbeti launcher'ı görünür (P2 açık); `make set-products PRODUCTS=P1` + sayfa yenile → launcher ve "Gündeminiz" gizli; `PRODUCTS=P1,P2,P3` geri. **Versiyon linki:** Balbal'a "Ankara RES kredi sözleşmesindeki minimum DSCR covenant'ı nedir?" → kaynak kartında "güncel versiyon: …" uyarısı; ağ sekmesinde `/api/ask` cevabında `superseded_by_document_id` dolu — **tıklanabilir link dondurulmuş sürümde yok** (T9), Tansu güncellemesiyle gelir; bu satır raporda "kısmen (sözleşme tarafı)" yazılır |
| A4 | `/api`, `/health`, cookie aynı origin | `curl -c c -X POST :8080/api/auth/login` → 200 + cookie; `curl -b c :8080/api/auth/me` → 200; `curl :8080/health` → 200; `curl :8080/departman/finans` → 200 `index.html` (SPA fallback); `curl :8080/ask` → backend geliştirici sayfası (değişmedi) |
| A5 | Backend/veri değişmedi | `git diff --stat` backend'de sıfır; `make test` (koşulmaz — backend değişmedi; `make lint` koşulur, yeşil); `${DATA_ROOT}` dokunulmadı |
| A6 | Rollback tek değişkenle | `FRONTEND_DIR=./frontend make build-frontend && make up` → A1'in grep'i **0**, oturum cookie'si hâlâ geçerli (`/api/auth/me` 200); değişken kaldırılıp `make up` → grep tekrar ≥ 1 |
| A7 | Temiz klon | `git clone` (submodule'süz) + `make up`'ın `dirs` adımı submodule'ü doldurur: dev VM'de `/tmp`'ye klon, `git submodule update --init` + `docker compose -p tmp build caddy` ile derleme kanıtı (port çakışması olmadan) |

---

## 6. SORU (Naci cevaplamalı)

1. **Dahil etme yolu:** git submodule `frontend-balbal/` (öneri, T10) — mi, yoksa kopya (vendor) mı? Submodule prod klon talimatını `git clone --recurse-submodules`'a çevirir (unutulursa `make up` yine doldurur).
2. **Sabitlenecek commit:** `main@b219600` (dondurulmuş BACKEND_GAPS ile aynı) — mi, yoksa Tansu'nun Aşama A alanlarını gösteren güncellemesi beklensin mi? Öneri: şimdi `b219600`, Tansu güncelleyince `make update-frontend REF=…` + pointer commit'i.
3. **Klasör adı:** `frontend-balbal/` uygun mu?
4. **`make lint`'in frontend adımı:** emekli `frontend/`'i lint'lemeye devam (değişiklik yok, öneri) — mi, AI-BalBal'ı mı lint'lesin (Tansu'nun reposu, kendi kontrolleri var; bizim CI'ımız ona bağlanmamalı), yoksa kaldırılsın mı (NOT §4.4 önerisi)?
5. **Google Fonts (T8):** Tansu'ya "LAN/VPN'de font internete çıkmadan yüklenmez, sistem fontuna düşer" notu iletilsin mi, yoksa fontları bundle'a alması istensin mi? Backend kararı değil, bilgi.
6. **Faz birimi:** etiketsiz düz commit + PHASES.md notu (Aşama A gibi) — uygun mu?

---

## 7. Kendi aldığım küçük kararlar

- Dockerfile'da `COPY . .` yerine açık dosya listesi (T5); `eslint.config.js`, `Dockerfile`, `package-lock` dışı dosyalar imaja girmez.
- `FRONTEND_DIR` varsayılanı compose içinde (`${FRONTEND_DIR:-./frontend-balbal/frontend}`), `.env.example`'da yorumlu; boş/eksik = AI-BalBal.
- `make update-frontend` pointer'ı commit **etmez**; yalnızca fetch + checkout + rebuild.
- Submodule init `dirs`'te (her `make up`/`make test` öncesi, saniyeler), ayrı bir hedef değil.
- `/ask` geliştirici sayfası Caddy'de kalır (rota çakışması yok, T3).
- AI-BalBal'ın `Dockerfile`'ı (tooling imajı) kullanılmaz; derleme yalnızca `infra/caddy/Dockerfile` ile.
