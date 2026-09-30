# Rapor — AI-BalBal'ın Caddy'den sunulması

**Tarih:** 30.09.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `24ba438` (uygulama), docs commit'i onu izler
**Plan:** `docs/plans/AIBALBAL_DEPLOY_PLAN.md` · **ADR:** ADR-018 + ADR-019 concretization (yeni ADR yok, topoloji aynı)

Naci'nin SORU cevapları: (1) git submodule; (2) `main@b219600`, ilerletme `make update-frontend`; (3) `frontend-balbal/`; (4) `make lint`'ten frontend adımı **kaldırıldı** (emekli `frontend/` de, AI-BalBal da lint'lenmez); (5) Google Fonts Tansu'ya **bilgi** olarak notta; (6) etiketsiz düz commit. A2/A3 tarayıcı adımları **Naci elle**; bu rapor A1/A4–A7'yi kanıtlar.

## 1. Kabul kriterleri (plan §5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| A1 | `make up` sonrası `:8080` AI-BalBal sunuyor | ✅ | `curl :8080/` → `/assets/index-ClaCzDVC.js` (359.597 B); bundle'da `"Balbal'a Sor"` **3**, `"Balbal"` **31** (company-ai bundle'ında 0); `compose images caddy` → yeni imaj `4f230ea85128`, 89 MB |
| A2 | Tarayıcıdan giriş | ⏭ Naci elle | — |
| A3 | Aşama A alanları (ürün paketi göstergesi, versiyon linki) | ⏭ Naci elle; **versiyon linki dondurulmuş sürümde tıklanamaz** (plan T9) — ağ sekmesinde `superseded_by_document_id` gelir, link Tansu'nun `SourceCardList` değişikliğiyle | Backend tarafı Aşama A raporunda kanıtlı |
| A4 | `/api`, `/health`, cookie, SPA fallback aynı origin | ✅ | `finans` login **200** + `access_token` cookie; `/api/auth/me` **200**; `/health` **200**; `/departman/finans` ve `/yonetim/klasorler` → **200** + `index.html` (`<div id="root">`); `/ask` → backend geliştirici sayfası **200** (değişmedi) |
| A5 | Backend/veri değişmedi; `make lint` yeşil | ✅ | `git diff --stat backend` boş; `make lint` çıkış 0 (ruff/mypy backend, ruff ocr-worker, 3 prompt dokümanı, ledger/documents/excel doğrulayıcıları; frontend adımı yok); `make test` koşulmadı (backend'e dokunulmadı) |
| A6 | Rollback tek değişkenle, oturum korunur | ✅ | `FRONTEND_DIR=./frontend make up` → bundle `/assets/index-CfN3Ml-t.js`, `"Balbal"` **0**, A4'ün cookie'siyle `/me` **200**; değişken kaldırılıp `make up` → `/assets/index-ClaCzDVC.js`, `"Balbal"` **31**, `/me` **200** |
| A7 | Temiz klon | ✅ | Yerel repodan `git clone` (`--recurse-submodules`'süz) → `frontend-balbal/` **boş**; `git submodule update --init` → `b219600`, 9 giriş; `docker compose -p aibalbal-clonetest build --no-cache caddy` → OK. Negatif test: `FRONTEND_DIR=./does-not-exist` → build **başarısız** (`failed to get build context src: stat …/does-not-exist`), sessizce başka yerden derlemez |

## 2. Yapılanlar

- `frontend-balbal/` git submodule (`https://github.com/ftansu/AI-BalBal.git`) @ `b219600`; `.gitmodules`.
- `infra/caddy/Dockerfile`: kaynak adlandırılmış `src` context'inden, **açık dosya listesi** (`package.json package-lock.json` → `npm ci` → `index.html vite.config.ts tsconfig*.json src/`); Caddy aşaması aynı.
- `infra/docker-compose.yml` `caddy.build`: `context: ./infra/caddy`, `additional_contexts.src: ${FRONTEND_DIR:-./frontend-balbal/frontend}`.
- `infra/.env.example`: `FRONTEND_DIR` yorumlu satır (boş = AI-BalBal; `./frontend` = geri dönüş).
- `Makefile`: `dirs` → `git submodule update --init frontend-balbal` (`.git` yoksa atlanır); `update-frontend REF=…` (fetch + checkout + `up -d --build caddy`, pointer commit'i insana kalır); `build-frontend` açıklaması; `lint`'ten frontend satırı kaldırıldı.
- Docs: README (Kurulum `--recurse-submodules`, "Arayüz — AI-BalBal" bölümü, Make tablosu), ADR-018/ADR-019 satırları, PHASES.md notu, NOT §1 B-27 + §4.4 (Google Fonts bilgi notu).
- **Dokunulmayanlar:** backend, `infra/Caddyfile`, `scripts/wait_for_services.sh`, `${DATA_ROOT}`, company-ai `frontend/` (emekli, yerinde), AI-BalBal reposu.

## 3. Değişen dosyalar

`24ba438`: `.gitmodules`, `frontend-balbal` (gitlink), `Makefile`, `infra/.env.example`, `infra/caddy/Dockerfile`, `infra/docker-compose.yml`. Docs commit'i: `README.md`, `docs/ARCHITECTURE.md`, `docs/PHASES.md`, `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md`, bu rapor.

## 4. Testler

- `make lint`: yeşil (frontend adımı artık yok). `make test`: koşulmadı — backend/ocr-worker değişmedi (A5).
- Canlı: A1, A4, A6, A7 dev VM'de; canlı LLM çağrısı **yok** (giriş + `/me` + statik dosyalar).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| A7'nin ilk denemesi geçersizdi: klon, submodule pointer'ı commit edilmeden alınmıştı ve build cwd farkından gerçek repoyu derledi | Test tasarım hatası; negatif test (yanlış `FRONTEND_DIR` → hata) ve commit sonrası `--no-cache` tekrar ile kapatıldı | Sonuç tablosu ikinci (geçerli) denemeye dayanır |
| `dirs`'te `test ! -d .git \|\| git submodule update --init` | Tarball/`.git`'siz kopyada `make up` kırılmasın | Submodule yoksa Docker "context yok" hatasıyla durur (sessiz değil) |
| `--depth` yok | Repo küçük; sığ submodule'de sabit SHA fetch'i sunucu ayarına bağlı | İlk klon birkaç MB |
| `frontend` tooling servisi kaldı (`make dev-frontend`) | Emekli `frontend/` için; silme yok kararı | README'de "kalıcı değil" notu |
| README'nin Phase 3.3 ekran açıklamaları yerinde | Emekli arayüzü anlatıyor, tarihçe | Başına "emekli arayüze ait" cümlesi |

## 6. Açık sorular (Naci cevaplamalı)

- Yok. A2/A3 tarayıcı sonuçlarını Naci raporlar; A3'ün "versiyon linki" kısmı Tansu'nun `types.ts` + `SourceCardList` güncellemesine bağlı (NOT §4.1).

## 7. Riskler / sonraki adım için notlar

- Tansu `main`'i ilerlettiğinde yayın **otomatik değişmez** (pointer sabit) — `make update-frontend REF=main` + pointer commit'i bilinçli adımdır; BACKEND_GAPS dondurmasından bağımsızdır.
- `update-frontend` kayıtlı olmayan bir REF'te `git checkout` hata verir, caddy yeniden derlenmez (eski imaj çalışmaya devam eder).
- Google Fonts (`styles.css:1`) internete çıkış ister; LAN/VPN'de sistem fontuna düşer (Tansu'ya bilgi, NOT §4.4).
- `make dev-frontend` hâlâ emekli `frontend/`'i açar; AI-BalBal geliştirmesi Tansu'nun reposunda (`npm run dev`, Vite proxy backend'e).

## 8. Doğruladığım üçüncü taraf davranışları

- Docker Compose v5.5.1 `build.additional_contexts` (adlandırılmış context, `COPY --from=src`) çalışıyor; göreli yol **proje dizinine** göre çözülür ve yoksa build `failed to get build context src` ile durur (negatif test).
- Adlandırılmış context'te `.dockerignore` uygulanmaz → açık `COPY` listesi (plan T5); `frontend-balbal/frontend`'de `node_modules` olmadığı temiz klonda da doğrulandı.
- `git submodule update --init <path>`: `.gitmodules` commit'te yoksa `pathspec … did not match` (ilk A7 denemesi), commit'ten sonra `b219600`'ü çıkarır.

## 9. Kaynak kullanımı

- Caddy imajı 89 MB (öncekiyle aynı mertebe); build (npm ci + vite build) ~1 dk; çalışma zamanı değişmedi (Caddy 11 MiB).
