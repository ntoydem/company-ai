# Phase 1.1 Raporu — Auth + kullanıcılar

**Tarih:** 23.09.2026  **Model:** Claude Sonnet 5  **Tag:** phase-1-1  **Commit:** `git rev-list -n1 phase-1-1`

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | doğru login 200 + cookie | ✅ | `tests/test_auth.py::test_login_with_correct_credentials_returns_200_and_sets_cookie` + canlı `curl` (rapor §"Canlı doğrulama") |
| 2 | yanlış şifre / disable 401 | ✅ | `::test_login_with_wrong_password_returns_401`, `::test_login_with_inactive_user_returns_401`, `::test_login_failure_paths_return_identical_error_body` (enumeration koruması, üçü de aynı `detail`) |
| 3 | cookie'siz `me` 401 | ✅ | `::test_me_without_cookie_returns_401` (+ eşlik eden `::test_me_with_valid_cookie_returns_current_user`) |
| 4 | loglarda şifre/hash yok (test) | ✅ | `::test_login_failure_does_not_log_password_or_hash` — yakalanan her log kaydı gerçek `JsonFormatter().format()`'dan geçirilip sentinel şifre ve gerçek `password_hash` aranıyor |

## 2. Yapılanlar
- `POST /api/auth/login|logout`, `GET /api/auth/me` (`app/api/auth.py`, `app/schemas/auth.py`).
- JWT yardımcıları `app/services/security.py`'ye eklendi (PyJWT, HS256): `create_access_token`/`decode_access_token`/`AccessTokenError`. Token yalnızca `sub` (user id) taşır; `role` claim'i bilgi amaçlıdır — `get_current_user` her istekte `User`'ı DB'den taze okur, yetki kararını hep DB'nin güncel `role`/`is_active`'i verir (refresh/revoke yok, ADR-003).
- `app/api/deps.py::get_current_user` gerçek cookie-tabanlı dependency'ye çevrildi (`app/api/ask.py`/`app/api/documents.py` değişmedi — aynı `Depends(get_current_user)` imzası).
- In-memory login rate limiter (`app/services/rate_limit.py`): kullanıcı adı başına 5/15dk, IP başına 20/15dk (SORU 1 cevabı) → `429`.
- Demo kullanıcı seed'i (`app/services/demo_users_seed.py`, `cli.py seed-demo-users`, `entrypoint.sh`): `yonetim` (management), `finans`/`hukuk`/`enerji` (employee), hepsi tek `DEMO_USER_PASSWORD`'u paylaşıyor (SORU 2 cevabı) — departman bağlantısı yok, Phase 1.2'de gelecek.
- `user_repo.get_by_id` eklendi.
- `Settings.jwt_secret` ve yeni `Settings.demo_user_password` artık zorunlu (Optional değil) — eksikse uygulama açılışta patlıyor.
- `tests/conftest.py`: `admin_user` fixture'ı artık `get_current_user`'ı override ediyor (var olan `fake_llm`/`get_llm_client` deseniyle aynı) — `test_ask.py`/`test_documents.py` hiç değişmeden yeşil kaldı. Yeni `inactive_user` fixture'ı + process-wide rate limiter'ı testler arası sıfırlayan autouse fixture.
- `seed_data/t0/upload.sh` güncellendi: artık önce `admin` olarak login olup cookie jar kullanıyor (aksi halde artık 401 alırdı).

## 3. Değişen dosyalar
`git diff --stat` (28 dosya): 769 satır eklendi, 25 satır çıkarıldı. Yeni dosyalar: `app/api/auth.py`, `app/schemas/auth.py`, `app/services/rate_limit.py`, `app/services/demo_users_seed.py`, `tests/test_auth.py`, `tests/test_security.py`, `tests/test_rate_limit.py`, `tests/test_user_repo.py`, `tests/test_demo_users_seed.py`. Değişen: `app/api/{deps,router}.py`, `app/cli.py`, `app/core/{config,errors}.py`, `app/repositories/user_repo.py`, `app/services/security.py`, `entrypoint.sh`, `pyproject.toml`, `uv.lock`, `tests/{conftest,test_cli,test_config}.py`, `infra/.env.example`, `seed_data/t0/upload.sh`, `README.md`, `Makefile`, `docs/{ARCHITECTURE,PHASES}.md`.

## 4. Testler
- Backend: **108 geçti**, 3 atlandı (`live_llm`, `make test-llm` ile ayrı), 5 uyarı (aşağıda). ~28 sn.
- `assert-pipeline-schema`: geçti (şema etkilenmedi).
- ocr-worker: **9 geçti**.
- `make lint` (ruff check + format --check + mypy, backend/ocr-worker): temiz. `docs/prompts/ANSWER_SYSTEM_PROMPT.md` eşitliği: güncel (bu faz dokunmadı).
- Migration: yok — `users` tablosu Phase 0.1'den beri tüm kolonlara sahipti.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| JWT kütüphanesi: PyJWT (`python-jose` değil) | Daha az bakım riski, HS256 için ek kripto bağımlılığı gerekmiyor | `pyproject.toml`/`uv.lock`'a tek bağımlılık |
| JWT/cookie yardımcıları `app/services/security.py`'de, ayrı `app/core/jwt.py` yok | Dosya zaten tek "auth kriptografisi" yeri | — |
| Hata sınıfı adı `AccessTokenError` | PyJWT'nin kendi `jwt.InvalidTokenError`'ıyla karışmasın | — |
| Cookie: `access_token`, `path=/`, `samesite=lax`, `secure=false` (V0) | Caddyfile aynı origin'i doğruluyor; ADR-015 LAN düz HTTP | TLS gelince `secure=true`'ya çevrilecek (not bırakıldı) |
| `logout` auth gerektirmiyor, koşulsuz 204 | Bozuk/süresi dolmuş cookie ile çıkış isteyen 401 almamalı | — |
| Yanlış şifre / bilinmeyen kullanıcı / disabled → aynı 401 mesajı | Username enumeration koruması | Test: `test_login_failure_paths_return_identical_error_body` |
| Rate limit sayıları `.env`'e taşınmadı, `LoginRateLimiter` default'u | V0'da `.env`'i şişirmemek | Sayı değişikliği kod değişikliği gerektirir |
| "disable" testi ayrı `inactive_user` fixture'ı kullanıyor | Demo hesap state'i testlerde bozulmasın | — |

## 6. Açık sorular (Naci cevaplamalı)
Yok. `docs/plans/PHASE_1_1_PLAN.md`'deki iki SORU (rate limit eşikleri; demo şifre stratejisi) Naci tarafından uygulama öncesi cevaplandı ve doğrudan uygulandı (§2, §5).

## 7. Riskler / sonraki phase için notlar
- **Canlı doğrulamada bulunan ve düzeltilen hata:** `cmd_seed_demo_users`'ın ilk hâli `log.info(..., extra={"created": [...]})` kullanıyordu — `created`, Python `logging`'in rezerve `LogRecord` alanı olduğu için `KeyError` ile container crash-loop'a giriyordu. Birim testleri bunu yakalamadı çünkü yalnızca `ensure_demo_users`'ı doğrudan çağırıyorlardı, CLI komutunun kendisini değil. Canlı `docker compose up` denemesinde ortaya çıktı; `was_created` olarak yeniden adlandırıldı (`cmd_seed_admin`'in zaten kullandığı isim) ve `tests/test_cli.py::test_seed_demo_users_succeeds_and_is_idempotent` regresyon testi eklendi (gerçek `log.info(extra=...)` çağrısını uçtan uca çalıştırıyor).
- Rate limiter process-wide, tek `uvicorn` worker varsayımına dayanıyor (T5); çoklu worker'a geçilirse yeniden düşünülmeli — şu an gündemde değil.
- Caddy varsayılan giriş noktası olduğunda (Phase 3.3), gerçek client IP tespiti için `uvicorn --proxy-headers --forwarded-allow-ips=...` gerekecek; şimdilik backend port doğrudan host'a açık olduğu için `request.client.host` doğru.
- `GET /ask` geliştirici sayfası (`ask.html`) artık tarayıcıda önce `/api/auth/login`'e login olmadan `/api/ask`'a 401 alır — sayfaya bir login formu eklenmedi (bu fazın onaylı kapsamı dışında; gerçek frontend Phase 3.3'te geliyor).
- Phase 1.2: `departments`/`user_departments`/`projects` + `allowed_document_ids` rol/departman kuralları. 4 demo kullanıcı şu an yalnızca `role` taşıyor; SPEC_02 §5'teki "finans: finance+accounting", "enerji: energy/* (finans erişimi yok)" nitelikleri o fazda yapısal olarak kurulacak.

## 8. Doğruladığım üçüncü taraf davranışları
- PyJWT 2.14.0 (`uv lock` ile çözüldü): `jwt.encode`/`jwt.decode` HS256 ile beklendiği gibi çalıştı; imza/süre/claim hataları tek `InvalidTokenError` ailesi altında yakalanabiliyor. <32 bayt secret'ta `InsecureKeyLengthWarning` veriyor (RFC 7518 §3.2) — `.env.example` zaten `openssl rand -hex 32` öneriyor, gerçek dağıtımda uygulanmalı.
- Python `logging`: `extra` dict'inde `LogRecord`'un kendi alan adlarından biri (örn. `created`, `message`, `msg`, `args`, `name`) kullanılırsa `makeRecord` `KeyError` fırlatıyor — `extra` key seçerken bu isim kümesinden kaçınmak gerekiyor (§7).
- `docker compose run ... uv lock` mevcut çalışan (eski) image içinde bile host'a bind-mount edilmiş `pyproject.toml`'u okuyup `uv.lock`'u güncelleyebiliyor; yeni bağımlılık eklerken image rebuild öncesi bu adım gerekiyor (`--frozen` build'i aksi halde reddediyor).

## 9. Kaynak kullanımı
- Bu fazda LLM çağrısı yok (auth katmanı). Container'lar sağlıklı kaldı (`docker compose ps` → `healthy`); ayrı RAM ölçümü alınmadı (temel servisler zaten 6 GB bütçesinin içinde, Phase 0.1'den beri değişmedi).

## Canlı doğrulama
```
curl -i -X POST localhost:8000/api/auth/login -c ck.txt -d '{"username":"admin","password":"***"}' \
  -H 'content-type: application/json'
# HTTP/1.1 200 OK; set-cookie: access_token=...; HttpOnly; Max-Age=28800; Path=/; SameSite=lax
curl localhost:8000/api/auth/me -b ck.txt
# {"id":"...","username":"admin","display_name":"Yönetici","role":"admin"}
curl -w '%{http_code}' localhost:8000/api/auth/me            # cookie'siz → 401
curl -w '%{http_code}' -X POST localhost:8000/api/auth/login -d '{"username":"admin","password":"yanlis"}'  # 401
curl -i -X POST localhost:8000/api/auth/login -c ck2.txt -d '{"username":"finans","password":"***"}'  # 200, role=employee
curl -w '%{http_code}' -X POST localhost:8000/api/auth/logout -b ck.txt   # 204
bash seed_data/t0/upload.sh    # login + upload uçtan uca çalıştı (Facility Agreement → Amendment 01)
```
