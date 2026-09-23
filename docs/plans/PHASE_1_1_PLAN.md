# Phase 1.1 — Auth + kullanıcılar: Implementation Plan

## Bağlam ve tespitler

Phase 0.3 (`phase-0-3`) T0'ı kapattı; ADIM 1 ("Kapı: kullanıcılar ve yetkiler") başlıyor. Phase 1.1, `docs/PHASES.md`'deki kapsamı kapatır: `users` tablosu zaten var (0.1'den), Argon2 hash zaten var (0.1'den) — asıl iş `/api/auth/login|logout|me`, JWT httpOnly cookie (8 saat), login rate limit ve 4 demo kullanıcının seed'i.

Okunanlar: `docs/PHASES.md` (1.1 + 1.2 bağlamı), `docs/SPEC_02_dokuman_metadata_yetki_ux.md` §5/§7 (+ §2/§6/§8 bağlam), `docs/DOMAIN_MODEL.md` §4/§5/§9, `docs/ARCHITECTURE.md` ADR-003/004/015/017, ve kod: `app/models/user.py`, `app/services/security.py`, `app/api/deps.py`, `app/api/ask.py`, `app/api/documents.py`, `app/api/router.py`, `app/core/config.py`, `app/core/logging.py`, `app/core/main.py`, `app/services/admin_seed.py`, `app/cli.py`, `entrypoint.sh`, `app/repositories/user_repo.py`, `tests/conftest.py`, `tests/test_ask.py`, `tests/test_admin_seed.py`, `infra/.env.example`, `infra/Caddyfile`.

Planı şekillendiren tespitler:

- **T1 — Migration gerekmiyor.** `users` tablosu (migration `0001_init_users.py`) spec'in istediği tüm kolonlara (`username, password_hash, display_name, role, is_active, auth_provider, external_id`) zaten sahip; `User` modeliyle birebir.
- **T2 — Stub zaten bu değişikliği bekliyor.** `app/api/deps.py::get_current_user`'ın docstring'i: "Replaced by a JWT-cookie dependency in Phase 1.1." `app/api/ask.py` ve `app/api/documents.py` zaten `Annotated[User, Depends(get_current_user)]` kullanıyor — çağıran taraflarda **hiçbir değişiklik gerekmiyor**, yalnızca dependency'nin arkası değişiyor.
- **T3 — `jwt_secret` zaten hazırlanmış.** `Settings.jwt_secret: SecretStr | None = None` (yorum: "# Phase 1.1") ve `infra/.env.example`'da `JWT_SECRET=change-me-jwt-secret` placeholder'ı zaten var. Bu fazda `admin_password` gibi **zorunlu** hale getirilecek (artık gerçekten kullanılıyor; eksikse uygulama açılışta patlamalı, her istekte None kontrolü yapmak yerine).
- **T4 — Aynı origin, `SameSite=Lax` yeterli.** `infra/Caddyfile`, `/api/*`'ı ve (Phase 3.3'te gelecek) frontend'i aynı `:80`/`CADDY_PORT` origin'i altında proxy'liyor.
- **T5 — Tek process, in-memory rate limiter mimari olarak uygun.** `entrypoint.sh` tek bir `uvicorn` process'i çalıştırıyor (`--workers` yok). İleri not (şimdi çözülmeyecek): Caddy varsayılan giriş noktası olduğunda (Phase 3.3) IP bazlı limit için `--proxy-headers` gerekecek.
- **T6 — Log maskeleme `extra` dict key'lerine bakıyor, mesaj string'ini taramıyor.** `app/core/logging.py::_is_sensitive` yalnızca `record.__dict__` üzerindeki key'leri maskeliyor. "loglarda şifre/hash yok" kabul kriterinin testi hem `auth.py`'nin kendi log çağrılarının şifreyi mesaj metnine gömmediğini hem de mevcut maskelemenin çalıştığını kanıtlamalı.
- **T7 — Departman/proje bu fazda yok.** `departments`/`user_departments`/`projects` tabloları Phase 1.2'de geliyor (DOMAIN_MODEL §9). 1.1'deki 4 demo kullanıcı yalnızca `role` alır; SPEC_02 §5'teki "finans: finance+accounting", "enerji: energy/* (finans erişimi yok)" gibi departman nitelikleri **yapısal olarak 1.2'de** kurulacak — bu fazda yalnızca rol (`management`/`employee`/`employee`/`employee`) seed edilir.
- **T8 — Mevcut endpoint testleri artık cookie'siz 401 alır, conftest'te tek noktadan düzeltilir.** `tests/test_ask.py`/`test_documents.py`'deki `admin_user` fixture'ı bugün yalnızca admin'i DB'ye yazıyor (stub zaten koşulsuz admin döndürdüğü için override gerekmiyordu). Gerçek auth gelince bu fixture, `fake_llm`'in (`test_ask.py`) kullandığı `app.dependency_overrides[...] = ...` desenini `get_current_user` için de uygulayacak şekilde `conftest.py`'de değiştirilecek — **`test_ask.py`/`test_documents.py`'nin kendisi değişmez.**

---

## 1. Bağımlılık: PyJWT

`backend/pyproject.toml`'a `pyjwt>=2.9`. Gerekçe: `python-jose` bakımı yavaş ve geçmişte CVE'leri var; PyJWT, HS256 için ek kripto bağımlılığı gerektirmeyen, FastAPI ekosisminin standart tercihi. Mevcut auth bağımlılığı zaten yalnızca `argon2-cffi` — minimal bağımlılık ilkesiyle uyumlu.

## 2. JWT — `app/services/security.py`'ye ekleme

Yeni dosya açmak yerine mevcut `security.py`'ye eklenir (dosya zaten "auth kriptografisi" için tek yer; `hash_password`/`verify_password` ile aynı kategoride, framework/DB'den bağımsız saf fonksiyonlar):

```python
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_COOKIE_NAME = "access_token"

class AccessTokenError(Exception):
    """Süresi dolmuş / imzası geçersiz / bozuk / `sub` eksik-geçersiz — hepsi tek hata."""

def create_access_token(*, user_id: uuid.UUID, role: UserRole, secret: str, expires_in_s: int) -> str: ...
def decode_access_token(token: str, secret: str) -> uuid.UUID:
    """`sub`'dan user id döner. `role` claim'i yalnızca bilgi amaçlıdır — yetki kararı
    için asla kullanılmaz; çağıran her zaman User satırını DB'den taze okur."""
```

**Yetki kararı için token içeriği değil DB güncel: ** JWT'de `sub` (user id), `role` (yalnızca gözlemlenebilirlik amaçlı, yetkilendirmede kullanılmaz), `iat`, `exp`. Refresh token yok (ADR-003) ve revoke mekanizması yok; bu yüzden `get_current_user` her istekte kullanıcıyı **id ile DB'den tekrar okur** ve DB'deki güncel `role`/`is_active`'i kullanır — token'daki `role` bayağı metadata'dır. Böylece bir kullanıcı deaktive edilirse/rolü değişirse, 8 saatlik token süresini beklemeden **bir sonraki istekte** etkili olur.

Hata sınıfının adı `AccessTokenError` (PyJWT'nin kendi `jwt.InvalidTokenError`'ıyla karışmasın diye farklı isim).

## 3. Cookie mekaniği

| Ayar | Değer | Gerekçe |
|---|---|---|
| ad | `access_token` | |
| `max_age` | `28800` (8 saat) | SPEC_02 §7, JWT `exp` ile aynı |
| `httponly` | `True` | ADR-003 |
| `secure` | `False` + satır içi yorum (`# V0: LAN düz HTTP (ADR-015); TLS gelince True`) | ADR-015 |
| `samesite` | `"lax"` | T4 — aynı origin doğrulandı |
| `path` | `"/"` | tek cookie, tüm uygulama |
| `domain` | belirtilmez | tek host |

Login'de `Response.set_cookie(...)`; logout'ta `Response.delete_cookie(key=ACCESS_TOKEN_COOKIE_NAME, path="/")` (silme de `path="/"` tekrar etmeli, yoksa tarayıcı eşleştirmez).

## 4. Endpoint'ler

**`app/schemas/auth.py`** (yeni), mevcut `app/schemas/` konvansiyonuna uyar (`ConfigDict(from_attributes=True)`):
```python
class LoginRequest(BaseModel):
    username: str
    password: str

class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    display_name: str
    role: UserRole
```
`password_hash` şemada hiç yok — `/login` ve `/me`'nin tek response body'si bu, yapısal olarak sızamaz.

**`app/api/auth.py`** (yeni), `router = APIRouter(prefix="/api/auth", tags=["auth"])`:

- **`POST /login`** — body `LoginRequest`, `response_model=CurrentUserResponse`, 200. Sıra: rate limit kontrolü → `get_by_username` → `verify_password` → `is_active` kontrolü → token üret → cookie set → user dön. **Yanlış kullanıcı adı, yanlış şifre ve `is_active=False` üçü de aynı 401 + aynı mesajı döner** (`"Kullanıcı adı veya şifre hatalı."`) — farklı mesajlar username enumeration'a izin verir.
- **`POST /logout`** — `get_current_user` bağımlılığı **yok** (bilinçli karar): cookie'yi koşulsuz temizler, `204` döner. Zaten bozuk/süresi dolmuş bir cookie ile "çıkış yap" isteyen kullanıcı 401 almamalı — logout'un var olma sebebi tam da bu durum.
- **`GET /me`** — `Depends(get_current_user)`, `response_model=CurrentUserResponse`, 200; 401, `get_current_user`'ın kendisinden gelir (§5).

## 5. `get_current_user` yeniden yazımı — `app/api/deps.py`

```python
def get_current_user(
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if access_token is None:
        raise HTTPException(401, NOT_AUTHENTICATED_MESSAGE)
    try:
        user_id = decode_access_token(access_token, settings.jwt_secret.get_secret_value())
    except AccessTokenError:
        raise HTTPException(401, NOT_AUTHENTICATED_MESSAGE) from None
    user = user_repo.get_by_id(session, user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, NOT_AUTHENTICATED_MESSAGE)
    return user
```
FastAPI'nin `Cookie()` parametresi kullanılır (dosyanın mevcut `Annotated[..., Depends(...)]` stiliyle tutarlı). Yeni: `user_repo.get_by_id(session, user_id: uuid.UUID) -> User | None` (repo'da şu an yalnızca `get_by_username` var).

**Etkilenen/etkilenmeyen endpoint'ler:** `/health` değişmez (auth yok, Docker healthcheck). `/api/documents/*`, `/api/ask` zaten `get_current_user`'a bağımlıydı — gerçek çağıranlar için davranış aynı, yalnızca testlerin cookie/override alması gerekiyor (§9). `/api/auth/login` ve `/logout` kasıtlı olarak public. `/api/auth/me` korumalı. `get_optional_current_user` gibi bir şey **eklenmiyor** — şu an anonim-veya-kimlikli davranış isteyen hiçbir yer yok, spekülatif olur.

## 6. Rate limiting — `app/services/rate_limit.py` (yeni)

Redis yok (stack kararı). Tek process (T5) → in-memory, kullanıcı adı **ve** IP'ye göre (yalnızca kullanıcı adı → tek kaynaktan çoklu hesaba saldırıyı durdurmaz; yalnızca IP → dağıtık/rotasyonlu saldırıyı durdurmaz):

```python
class LoginRateLimiter:
    def __init__(self, *, max_per_username: int = 5, max_per_ip: int = 20, window_s: float = 900) -> None: ...
    def is_blocked(self, *, username: str, client_ip: str) -> bool: ...
    def record_failure(self, *, username: str, client_ip: str) -> None: ...
    def record_success(self, *, username: str) -> None: ...  # yalnızca o kullanıcının penceresini temizler
```
`app/api/deps.py`'de mevcut `_cached_llm_client`/`get_llm_client` deseniyle aynı şekilde `@lru_cache` singleton olarak sağlanır (`get_login_rate_limiter`). `login()` önce `is_blocked` kontrol eder → tripse `429` + Türkçe mesaj; sonra `record_failure`/`record_success`.

Process yeniden başlayınca sıfırlanması kabul edilebilir (T5, "basit" + kalıcı depo yok — bu bir ürün kararı değil, "basit rate limit" ifadesinin doğrudan sonucu).

## 7. Demo kullanıcı seed

Mevcut mekanizma (`app/services/admin_seed.py::ensure_admin_user` — var-ise-dokunma, `app/cli.py::cmd_seed_admin` → `entrypoint.sh`'te `alembic upgrade head`'den sonra, `uvicorn`'dan önce çalışıyor) **birebir mirror'lanır**:

**`app/services/demo_users_seed.py`** (yeni):
```python
_DEMO_USERS: tuple[tuple[str, str, UserRole], ...] = (
    ("yonetim", "Yönetim", UserRole.management),
    ("finans", "Finans", UserRole.employee),
    ("hukuk", "Hukuk", UserRole.employee),
    ("enerji", "Enerji", UserRole.employee),
)

def ensure_demo_users(session: Session, settings: Settings) -> list[DemoSeedResult]: ...
```
- `app/cli.py`'ye `seed-demo-users` alt komutu; `entrypoint.sh`'te `seed-admin`'den hemen sonra çağrılır.
- Departman/proje bağlantısı **yok** (T7) — yalnızca `role`.
- Şifre kaynağı: bkz. **SORU 2**.

## 8. Config/env değişiklikleri — `app/core/config.py`, `infra/.env.example`

- `jwt_secret: SecretStr | None = None` → `jwt_secret: SecretStr` (artık zorunlu; `admin_password` ile aynı desen — `.env.example`'daki placeholder zaten var, yalnızca satırdaki yorum güncellenir).
- Rate limit eşikleri env'e **taşınmaz** — `LoginRateLimiter`'ın constructor default'ları olarak kalır (V0'da `.env`'i şişirmemek için; sayılar kendisi SORU 1'de netleşecek).
- Demo şifre(ler)i için yeni env değişken(ler)i — bkz. SORU 2, cevaba göre `.env.example`'a eklenecek.

## 9. Testler

**`tests/conftest.py`** değişikliği: `admin_user` fixture'ı, `test_ask.py`'deki `fake_llm`'in kullandığı `app.dependency_overrides[...] = ...` desenini `get_current_user` için de uygulayacak şekilde genişletilir (override + `try/finally pop`). Ayrıca yeni `inactive_user` fixture'ı (`user_repo.create(...)` + `is_active=False` + commit) — demo hesapların durumunu bozmadan "disable" senaryosunu test etmek için.

**`tests/test_auth.py`** (yeni):

| Kabul kriteri (PHASES.md) | Test | Kanıt |
|---|---|---|
| "doğru login 200 + cookie" | `test_login_with_correct_credentials_returns_200_and_sets_cookie` | seed `ensure_admin_user` ile (fixture'ı değil, gerçek uçtan uca akış için); `client.post("/api/auth/login", ...)` → 200; `"access_token" in response.cookies`; body'de `password_hash` yok |
| "yanlış şifre / disable 401" | `test_login_with_wrong_password_returns_401`, `test_login_with_inactive_user_returns_401` (`inactive_user` fixture'ıyla), `test_login_wrong_password_and_inactive_user_return_identical_error_body` | üçü de 401; son test iki hatalı gövdenin bayt bayt aynı olduğunu doğrular (enumeration koruması) |
| "cookie'siz `me` 401" | `test_me_without_cookie_returns_401` + eşlik eden `test_me_with_valid_cookie_returns_current_user` | 401 / 200 |
| "loglarda şifre/hash yok" | `test_login_failure_does_not_log_password_or_hash` | `caplog` ile yanlış şifre denemesi (belirgin bir sentinel şifre); yakalanan her kayıt gerçek `app.core.logging.JsonFormatter().format(record)`'dan geçirilir; ne sentinel plaintext'i ne de kullanıcının gerçek `password_hash`'i render edilen JSON'da bulunur — bu hem `auth.py`'nin log çağrılarının şifreyi mesaj metnine gömmediğini (mevcut maskeleme bunu korumaz, T6) hem de mevcut `extra`-key maskelemesinin çalıştığını kanıtlar |

Destek testi (kabul kriteri değil ama kapsamda): `test_login_rate_limited_returns_429` — eşik sayısı kadar başarısız denemeden sonra 429.

`user_repo`, `security.py` (JWT fonksiyonları) ve `LoginRateLimiter` için ayrıca saf birim testleri (`test_user_repo.py` genişletme veya `test_security.py`, `test_rate_limit.py` — dosya bölünmesi küçük teknik detay, raporda netleşir).

---

## SORU (Naci cevaplamalı)

1. **Rate limit eşikleri.** Spec'te sayı yok ("basit login rate limit" dışında). Önerim: **kullanıcı adı başına 5 başarısız deneme / 15 dk**, **IP başına 20 başarısız deneme / 15 dk**, ikisi de aşılınca 429. Çok sıkı olursa demo sırasında yanlış şifre yazan biri kilitlenir, çok gevşek olursa anlamsızlaşır — onaylıyor musun, yoksa farklı sayılar mı istiyorsun?
2. **Demo kullanıcı şifreleri nereden gelecek.** `admin` için zaten `ADMIN_PASSWORD` env değişkeni var. `yonetim`/`finans`/`hukuk`/`enerji` için iki seçenek: (a) tek paylaşılan `DEMO_USER_PASSWORD` (dördü de aynı şifre — V0 demo için daha basit, `.env.example`'ı şişirmiyor), (b) dört ayrı env değişkeni (`DEMO_YONETIM_PASSWORD` vb. — her hesap için farklı şifre, gerçek kişilere teslim edilecekse daha güvenli). Önerim **(a)** — bunlar 1.2'ye kadar zaten gerçek yetki ayrımı taşımıyor, tek şifre demo akışını basitleştirir — ama bu senin karar vereceğin bir ürün tercihi.

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- JWT kütüphanesi: PyJWT (§1 gerekçesi).
- JWT/cookie yardımcıları `app/services/security.py`'de (yeni `app/core/jwt.py` açılmıyor).
- Hata sınıfı adı `AccessTokenError` (PyJWT'nin kendi istisnasıyla karışmasın).
- Cookie adı `access_token`, `path="/"`, `samesite="lax"`, `secure=False` (V0, ADR-015).
- `logout` auth gerektirmez, koşulsuz 204.
- Yanlış şifre / yanlış kullanıcı adı / disabled kullanıcı → aynı 401 mesajı (enumeration koruması).
- `get_current_user` her istekte DB'den taze `User` okur; JWT'deki `role` yetkilendirmede kullanılmaz.
- `jwt_secret` artık zorunlu (Optional değil).
- Rate limit sayıları `LoginRateLimiter` constructor default'u, env'e taşınmıyor (sayılar SORU 1'e bağlı).
- "disable" testi demo hesaplarından birini değil, ayrı bir `inactive_user` fixture'ını kullanır.
- Yeni migration yok, yeni `departments`/`user_departments` yok.

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: yeni bir ADR açılmıyor — ADR-003 zaten bu tasarımı kapsıyor (JWT cookie, argon2, seed deseni); ADR-003'ün faz notuna somutlaşan parametreler (cookie adı, rate limit yaklaşımı) kısa bir ek cümleyle işlenir.
- `infra/.env.example`: `JWT_SECRET` yorumu güncellenir (artık zorunlu); demo şifre değişken(ler)i eklenir (SORU 2'ye göre).
- `README.md`: "Giriş yapma (Phase 1.1)" bölümü — `curl` ile login/logout/me örneği, demo hesap listesi.
- `docs/reports/PHASE_1_1_REPORT.md` (şablon `docs/reports/TEMPLATE.md`), `docs/PHASES.md` durum satırı güncellenir, `git tag phase-1-1`.

## Uygulama sırası

1. `pyjwt` bağımlılığı; `security.py`'ye JWT fonksiyonları + birim testleri.
2. `user_repo.get_by_id` + testi.
3. `app/schemas/auth.py`, `app/api/auth.py` (login/logout/me), `router.py`'ye ekleme.
4. `app/services/rate_limit.py` + testleri; `deps.py`'ye `get_login_rate_limiter`.
5. `deps.py::get_current_user` yeniden yazımı; `config.py`'de `jwt_secret` zorunlu hale getirme.
6. `demo_users_seed.py`, `cli.py::seed-demo-users`, `entrypoint.sh` güncellemesi.
7. `conftest.py` (`admin_user` override + `inactive_user`), `tests/test_auth.py`.
8. `test_ask.py`/`test_documents.py`'nin conftest değişikliğiyle hâlâ yeşil olduğunu doğrula (değişiklik gerekmemeli).
9. `.env.example`, README, ADR-003 notu → `make test` yeşil → rapor → `docs/PHASES.md` → commit + tag `phase-1-1` + push.

## Kritik dosyalar

- `backend/app/api/deps.py`, `backend/app/services/security.py`
- `backend/app/api/auth.py`, `backend/app/schemas/auth.py`
- `backend/app/services/rate_limit.py`, `backend/app/services/demo_users_seed.py`
- `backend/tests/conftest.py`, `backend/tests/test_auth.py`
