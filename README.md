# Company AI V0

Kurumsal doküman + Excel + AI bilgi platformu. Şirket bilgisinin **kaynağını, erişim yetkisini, tarihini,
versiyonunu ve ilişkilerini** koruyarak AI tarafından güvenilir kullanılmasını sağlar. Basit bir chatbot değildir.

Bu README Phase 5.1 (Tam dataset + consistency checks) durumunu anlatır; her phase sonunda güncellenir. Plan ve kabul kriterleri:
`docs/PHASES.md`. Mimari kararlar: `docs/ARCHITECTURE.md`. Alan modeli: `docs/DOMAIN_MODEL.md`.

## Gereksinimler (VM)
- Ubuntu 24.04, Docker Engine + Compose plugin (v2+), `make`, `curl`, `git`.
- Host'ta Python/Node gerekmez; test ve lint dahil her şey container içinde çalışır.
- RAM: temel servisler (postgres, backend, ocr-worker, caddy) 6 GB'a sığar; `embed` servisi (`make up-full`) 16 GB ister.

## Kurulum
```bash
git clone --recurse-submodules <repo> company-ai && cd company-ai   # arayüz (AI-BalBal) git submodule'dür; unutulursa `make up` doldurur
cp infra/.env.example .env      # şifreleri değiştir (POSTGRES_PASSWORD, ADMIN_PASSWORD, JWT_SECRET, DEMO_USER_PASSWORD)
make up                         # postgres + backend build & start, /health bekler
curl localhost:8080/health      # {"status":"ok","version":"0.1.0","database":"ok"}
```
İlk açılışta backend container'ı sırayla: veritabanını bekler → `alembic upgrade head` → admin kullanıcısını
oluşturur (`ADMIN_USERNAME` / `ADMIN_PASSWORD`; kullanıcı varsa dokunmaz) → demo kullanıcılarını, demo
departmanlarını (+ üyeliklerini) ve demo projelerini oluşturur (`DEMO_USER_PASSWORD`, aşağıdaki tablo; var
olanlara dokunmaz) → API'yi başlatır. `ocr-worker` aynı anda ayağa kalkar ve `ingestion_jobs` kuyruğunu 2
saniyede bir yoklar.

Veri kökü `.env` içindeki `DATA_ROOT` altındadır (dev: `./data`, prod: `/srv/company-ai`):
`postgres/ documents/ excel/ app-data/ backups/`. Container'ları silmek veri kaybettirmez.

## `.env` değiştikten sonra
`.env`'i düzenledikten sonra (örn. `LLM_API_KEY` girme/rotasyon) sıradan `docker compose restart <servis>`
**YETMEZ** — container'ın yeniden oluşturulması (recreate) gerekir:
```bash
docker compose --project-directory . -f infra/docker-compose.yml --env-file .env up -d --force-recreate backend
```
Neden: `docker-compose.yml`'da `env_file: .env` kullanılıyor, ama `env_file`'ın içeriği compose'un "değişti mi"
karşılaştırmasına dahil değil (yalnızca `environment:` bloğunda açıkça yazılan değişkenler diff'lenir) — bu
yüzden `.env` değişse bile `docker compose up -d` container'ı kendiliğinden yeniden oluşturmaz, `--force-recreate`
şart. `<servis>` yerine `backend`, `ocr-worker` gibi etkilenen servisin adı yazılır.

## Arayüz — AI-BalBal (30.09.2026'dan itibaren; Phase 3.3 altyapısı)
`make up` Caddy'yi de başlatır: **`http://<vm-ip>:8080`** tek giriş noktasıdır — arayüz ve `/api/*`, `/health`, `/ask`
proxy'si. Backend'in 8000 portu host'a **açık değil** (ADR-018); aşağıdaki `curl` örnekleri bu yüzden `:8080` kullanır.
Arayüz bundle'ı Caddy imajının içindedir (`infra/caddy/Dockerfile`, çok aşamalı build); ayrı bir Node container'ı çalışmaz.

**Sunulan arayüz AI-BalBal'dır** (`github.com/ftansu/AI-BalBal`, Tansu'nun reposu): company-ai reposunda
`frontend-balbal/` git submodule'ü olarak durur ve sabit bir commit'e bağlıdır (`git -C frontend-balbal log -1`).
Caddy imajı `frontend-balbal/frontend`'den derlenir (`docker-compose.yml` `additional_contexts`, `FRONTEND_DIR`).
company-ai'ın kendi `frontend/` klasörü **emekli**dir: repoda kalır, geliştirilmez, `make lint` onu artık denetlemez;
yalnızca geri dönüş için tutulur.
```bash
make update-frontend REF=main        # AI-BalBal'ı ilerlet (fetch + checkout + caddy rebuild); sonra pointer'ı commit et:
git add frontend-balbal && git commit -m "chore: AI-BalBal -> <sha>"
# Geri dönüş (eski arayüz), tek değişken:
FRONTEND_DIR=./frontend make up      # ya da .env'e FRONTEND_DIR=./frontend yazıp make up; kaldırınca AI-BalBal'a döner
```
Backend, Caddyfile, veri ve oturum cookie'si iki yönde de değişmez (aynı origin). AI-BalBal `fonts.googleapis.com`'dan
yazı tipi yükler; internete çıkışı olmayan LAN/VPN'de sistem fontuna düşer, uygulama çalışır.

Aşağıdaki ekran açıklamaları company-ai'ın emekli arayüzüne aittir (Phase 3.3); AI-BalBal'ın ekranları için
`frontend-balbal/README.md`.

- **Giriş** → **Ana sayfa**: departman kartları (yalnızca erişebildikleriniz — `employee` için kendi üyelikleri,
  `management`/`admin` için hepsi; kart gizleme yalnızca kolaylıktır, yetki her zaman sunucuda) + **Genel Sor**.
- **Departman ekranı** (`/departman/<slug>`): **AI'ya Sor** (o departmanla sınırlı) / **Belgeler** (liste, detay, indir,
  AI önerisi) / **Belge Yükle** (form → OCR durumu → AI önerisi) / **Projeler** (admin: oluştur/düzenle). Enerji'de
  Geliştirme / EPC-İnşaat / Bakım alt kartları yalnızca belge listesini filtreler.
- **Sor**: cevap + `[K#]` kaynak kartları (belge, **sayfa**, tarih, versiyon, durum, GÜNCEL rozeti, proje, indir).
  Her cevabın üstünde "yorum içermez" notu. Kaynak yoksa gri "bilgi bulamadım". Phase 4.3: cevap başlığında soru
  tipi rozeti (**Belge** / **Excel** / **Belge + Excel** / **Genel bilgi**); Excel kaynakları ayrı "Excel kaynakları"
  kartında (dosya, sheet, aralık, indir); Genel bilgi cevabı "şirket verisi kullanılmamıştır" cümlesiyle başlar.
- **AI önerisi**: `ready` belgede otomatik (arka plan taraması) ya da admin'in "Şimdi üret"i ile; admin alanları
  düzenler, **yalnızca işaretlediği** alanları uygular ya da reddeder; diğer roller salt-okunur görür.
- Hatalar: backend'in Türkçe `detail`'i + küçük "İstek no" satırı; ağ hatasında "Sunucuya ulaşılamadı."
- Dar ekranda tek sütun (responsive). Türkçe metinlerin tamamı `frontend/src/lib/strings.ts`'te.

Geliştirme: `make dev-frontend` → Vite HMR `http://<vm-ip>:5173` (`/api` backend'e proxy'lenir; `make up` çalışıyor
olmalı). `make lint` frontend için eslint + tsc de çalıştırır. Playwright/UI otomasyon testi V0'da yoktur
(CLAUDE.md); kabul kriterleri tarayıcıda elle doğrulanır (bkz. `docs/reports/PHASE_3_3_REPORT.md`).

## Giriş yapma (Phase 1.1)
JWT, httpOnly cookie'de (`access_token`, 8 saat, `samesite=lax`; V0'da `secure=false` — LAN, düz HTTP).
```bash
curl -i -X POST http://localhost:8080/api/auth/login \
  -H 'content-type: application/json' -d '{"username":"admin","password":"<ADMIN_PASSWORD>"}' \
  -c cookies.txt
curl -b cookies.txt http://localhost:8080/api/auth/me
# {"id":"...","username":"admin","display_name":"Yönetici","role":"admin"}
curl -i -X POST http://localhost:8080/api/auth/logout -b cookies.txt
```
Yanlış şifre, bilinmeyen kullanıcı adı ve devre dışı hesap aynı `401` mesajını döner (kullanıcı adı sızdırılmaz).
Başarısız denemeler sınırlıdır: kullanıcı adı başına 5 / 15 dk, IP başına 20 / 15 dk — aşılınca `429`.

Demo hesapları — hepsi tek `DEMO_USER_PASSWORD` şifresini paylaşır; erişim departman üyeliğinden gelir, rolden
değil (`yonetim`/`admin` üyelikten bağımsız her şeyi görür):

| Kullanıcı adı | Rol | Departman üyeliği |
|---|---|---|
| `admin` | `admin` (ayrı `ADMIN_PASSWORD`) | — (her şeyi görür) |
| `yonetim` | `management` | — (üyelikten bağımsız her şeyi görür) |
| `finans` | `employee` | `finans`, `mali_isler` |
| `hukuk` | `employee` | `hukuk` |
| `enerji` | `employee` | `enerji_grubu` (Geliştirme/EPC-İnşaat/Bakım dahil) |

## Departman, rol, proje, yetki (Phase 1.2)
`allowed_document_ids()` gerçek kuralları uygular (SPEC_02 §5): `employee` yalnızca üye olduğu departman(lar)ın
`normal` belgelerini görür; `management` tüm departmanları ve tüm gizlilik seviyelerini (`normal`/`restricted`/
`board`) görür; `admin` her şeyi görür. Yetki her zaman belgenin `department` alanından gelir, projesinden değil.
Belge listesi, indirme (`GET /api/documents/{id}/download`) ve `/api/ask` — hepsi bu fonksiyondan geçer;
yetkisiz erişimde indirme `403`, liste ve `/api/ask` sessizce dışarıda bırakır ("bilgi bulamadım").

```bash
curl http://localhost:8080/api/departments -b cookies.txt   # ağaç: id, name, slug, parent_id
curl http://localhost:8080/api/projects -b cookies.txt      # ANK_RES, IZM_RES (herkes okuyabilir)

# Admin: yeni proje (yalnızca admin; diğerleri 403)
curl -i -X POST http://localhost:8080/api/projects -b admin_cookies.txt \
  -H 'content-type: application/json' \
  -d '{"name":"Yeni Proje","code":"YENI_PRJ","stage":"development","department_ids":["<departman-uuid>"]}'
curl -i -X PATCH http://localhost:8080/api/projects/<id> -b admin_cookies.txt \
  -H 'content-type: application/json' -d '{"is_active": false}'
```

Departmanların CRUD ucu yok (V0'da yalnızca seed); admin'in proje formunda departman seçebilmesi için
`GET /api/departments` salt-okunur. Ankara RES ve İzmir RES `enerji_grubu`, `finans` ve `hukuk`
departmanlarına bağlı (`mali_isler`/`idari_isler` şirket geneli, proje-spesifik değil) — bu bağlantı yalnızca
organizasyonel/filtreleme amaçlıdır, belge yetkisini etkilemez.

## Yönetim paneli (Phase 5.2)
Arayüzde yalnızca `admin` rolüne görünen bir "Yönetim" bağlantısı (`/yonetim/kullanicilar`,
`/yonetim/denetim-kaydi`); başka bir rol bu yollara giderse anasayfaya sessizce yönlendirilir
(`enerji`/`finans`/`hukuk` gibi ayrı bir 403 sayfası yok, `DepartmentPage`'in bilinmeyen slug
davranışıyla tutarlı). Tüm uçlar `require_admin` arkasında; employee 403 alır.

```bash
curl http://localhost:8080/api/users -b admin_cookies.txt   # kullanıcı listesi (yalnızca admin)
curl -i -X POST http://localhost:8080/api/users -b admin_cookies.txt \
  -H 'content-type: application/json' \
  -d '{"username":"yeni_calisan","password":"...","display_name":"Yeni Çalışan","role":"employee","department_ids":["<departman-uuid>"]}'
curl -i -X PATCH http://localhost:8080/api/users/<id> -b admin_cookies.txt \
  -H 'content-type: application/json' -d '{"role":"management","is_active":true}'
```
Kullanıcı ekleme/rol/aktiflik/departman üyeliği admin panelinden yönetilir; şifre sıfırlama V0 kapsamı
dışında (yalnızca oluşturma sırasında bir şifre girilir). Bir admin kendi hesabının rolünü düşüremez veya
hesabını devre dışı bırakamaz (`409`) — V0'da şifre kurtarma akışı olmadığı için kimsenin admin
endpoint'lerine erişemeyeceği bir kilitlenmeyi önler. "Departman izinleri" burada yalnızca kullanıcı↔departman
üyeliği ataması anlamına gelir; departmanların kendisi (isim/ağaç) hâlâ seed-only'dir (Phase 1.2).

Belge detay ekranında admin'e iki ek bölüm görünür: **"Bu belgeyi kim görebilir"**
(`GET /api/documents/{id}/visibility`, `allowed_document_ids`'i tersinden çalıştırarak o belgeyi görebilen
kullanıcıları listeler) ve **manuel metadata düzenleme** (`PATCH /api/documents/{id}`, AI öneri akışından
bağımsız — öneri hiç üretilmemiş/reddedilmiş bir belgede de çalışır; versiyon zinciri alanları burada yoktur,
bkz. "AI metadata önerisi" bölümü). Denetim kaydının filtrelenebilir admin arayüzü "Audit log (Phase 3.4)"
bölümünde anlatılan uçları birebir kullanır.

## Belge yükleme (Phase 0.2, 3.2)
Tüm `/api/documents/*` ve `/api/ask` istekleri artık giriş yapılmış olmayı gerektirir (yukarıdaki `cookies.txt`).
```bash
curl -X POST http://localhost:8080/api/documents/upload -b cookies.txt \
  -F "file=@sözleşme.pdf;type=application/pdf" \
  -F "title=Facility Agreement" -F "document_type=facility_agreement" \
  -F "document_date=2023-06-01" -F "counterparty=PQR Bank" -F "status=executed" \
  -F "department=finans" -F "confidentiality=normal"   # ikisi de opsiyonel (Phase 3.2)
# {"id":"...","ingestion_status":"uploaded"} — birkaç saniye içinde "ready" olur:
curl -b cookies.txt http://localhost:8080/api/documents/<id>/status
curl -b cookies.txt http://localhost:8080/api/documents   # yetkili (Adım 0'da: tüm) belgeler
```
Kabul edilen türler: pdf/png/jpg (MIME imzasıyla doğrulanır, `.xlsx/.xlsm/.csv` Phase 4.2). Taranmış (görüntü)
PDF'ler `ocr-worker`'da `ocrmypdf` (tur+eng) ile OCR'lanır; sayfa metni ve ~800 kelimelik chunk'lar
(`document_pages`/`document_chunks`) full-text search (`turkish` + `simple`) için hazırlanır. Demo belgeler
manuel upload yerine `make seed` ile yüklenir (bkz. "Demo veri (Phase 3.1)"). `department` verilirse bilinen
bir departman slug'ına karşı doğrulanır (422); `project_id` verilirse var olan bir projeye karşı doğrulanır (404).
`supersedes_document_id` ile bir belge başka birinin yerini aldığında, eskisinin `status`'u otomatik olarak
`superseded` olur (Phase 3.2).

**Dosya türü, indirme adı, tarayıcıda açma (Aşama B, 30.09.2026):** her liste/detay/yükleme cevabında
`file_kind: pdf | image | xlsx | xlsm | csv` bulunur (saklanan dosyadan türetilir). `GET /api/documents/{id}/download`
dosyayı **belge başlığıyla** adlandırır (`Ankara RES Kredi Sözleşmesi.pdf`; Türkçe karakterler korunur, RFC 5987) ve
`?inline=1` ile PDF/görüntüyü tarayıcıda açar (`Content-Disposition: inline`; Excel/CSV her zaman indirilir). Yetki
davranışı aynıdır (yetkisiz `403`).
```bash
# (GET ile; uç HEAD desteklemez -> `curl -I` 405 döner)
curl -s -D - -o /dev/null -b cookies.txt "http://localhost:8080/api/documents/<id>/download" | grep -i "content-disposition\|content-type"
curl -s -D - -o /dev/null -b cookies.txt "http://localhost:8080/api/documents/<id>/download?inline=1" | grep -i content-disposition
```

## AI metadata önerisi (Phase 3.2)
Belge `ready` olduktan sonra (yukarıdaki `/status` ile takip edilir) `LLM_MODEL_CLASSIFY` ile bir metadata önerisi
üretilebilir: departman, alt departman, proje kodu, belge türü, muhatap, tarih, durum, gizlilik, etiketler —
her biri için 0-1 arası bir `confidence`. Öneri ayrı bir tabloda durur; kullanıcı **açıkça** kabul etmeden
belgenin kendi metadata'sı hiç değişmez (SPEC_02 §4, "kritik alan sessiz overwrite yok").
```bash
# Otomatik: backend, ready + önerisiz belgeleri arka planda tarar (15 sn'de bir, 5'li grup halinde).
# Elle tetiklemek/yeniden denemek için (yalnızca admin):
curl -X POST http://localhost:8080/api/documents/<id>/suggest-metadata -b admin_cookies.txt
curl http://localhost:8080/api/documents/<id>/metadata-suggestion -b cookies.txt
# {"status":"pending","fields":{"department":{"value":"finans","confidence":0.86}, ...}}

# Kabul (yalnızca admin; yalnızca gövdede adı geçen alanlar yazılır):
curl -X POST http://localhost:8080/api/documents/<id>/metadata-suggestion/apply -b admin_cookies.txt \
  -H 'content-type: application/json' -d '{"department":"finans","project_code":"ANK_RES"}'
# Ret (öneriyi reddeder, belgeye dokunmaz; sonra tekrar suggest-metadata çağrılabilir):
curl -X POST http://localhost:8080/api/documents/<id>/metadata-suggestion/reject -b admin_cookies.txt
```
LLM hatası (kota, bağlantı) önerinin `status:"failed"` olmasına yol açar, upload'ı hiçbir zaman bozmaz. Arka plan
taraması yalnızca `LLM_API_KEY` doluyken ve `_test` veritabanına karşı çalışmıyorken başlar (`make test`
sırasında hiç çalışmaz).

Öneri hiç üretilmemiş/reddedilmiş bir belgede de metadata elle düzeltilebilir (Phase 5.2, yalnızca admin):
```bash
curl -X PATCH http://localhost:8080/api/documents/<id> -b admin_cookies.txt \
  -H 'content-type: application/json' -d '{"title":"Düzeltilmiş Başlık","effective_date":"2024-01-01"}'
```
Aynı 9 alan + `title`/`effective_date`/`expiration_date`; `null` gönderilen alan temizlenir. Versiyon zinciri
alanları (`supersedes_document_id` vb.) burada yoktur — o bağlantılar yalnızca upload sırasında kurulur
(ADR-012, zincir bütünlüğü).

## Soru sorma (Phase 0.3)
`LLM_API_KEY` `.env`'de dolu olmalı (varsayılan Gemini, OpenAI-uyumlu endpoint; model adları `LLM_MODEL_ANSWER` /
`LLM_MODEL_CLASSIFY`, thinking bütçesi `LLM_REASONING_EFFORT=low`). Anahtar yoksa yalnızca `/api/ask` 503 döner
("Yapay zeka servisi yapılandırılmamış."), belge hattı çalışmaya devam eder.

**Gemini API key alma:** `https://aistudio.google.com/apikey` adresine Google hesabınızla giriş yapın, "Create
API key" butonuna tıklayın; ücretsiz katman için kredi kartı gerekmez. Aldığınız değeri `.env`'deki
`LLM_API_KEY=` satırına yapıştırın, sonra ilgili container'ı yeniden oluşturun (bkz. "`.env` değiştikten sonra").
```bash
# Demo belgeler yüklüyse (bkz. "Demo veri (Phase 3.1)"), doğrudan soru sorulabilir:
curl -s -X POST localhost:8080/api/ask -b cookies.txt -H 'content-type: application/json' \
  -d '{"question": "Ankara RES'\''in güncel minimum DSCR covenant'\''ı nedir?"}'
# {"answer":"... 1,20x'tir [K1] ...","answered":true,"sources":[{"ref":"K1","title":"Amendment 01","page_number":3,
#   "document_date":"2025-03-15","version":1,"status":"executed","is_current":true,...}],"model":"...","tokens_in":..}
```
`/api/ask` gövdesi `question` + opsiyonel `department`'tır; `project_id` 30.09.2026'da kaldırıldı (bir sohbet birden çok
proje içerebilir, kaynak kartları projeyi ayırır; eski istemcinin gönderdiği alan yok sayılır, 422 olmaz).
Tek sayfalık test arayüzü: `http://<vm-ip>:8080/ask` (Caddy ve build gerektirmez). Cevaplar Türkçe'dir, her olgu
cümlesi `[K#]` etiketiyle bir belge+sayfaya bağlanır; kaynak yoksa sabit "…yeterli bilgi bulamadım." cevabı döner ve
LLM hiç çağrılmaz. "Güncel" / "ilk" ayrımı `supersedes` zinciri ve `DEMO_TODAY` ile kodda hesaplanır (ADR-021).
Yüklemede zincir kurmak için `effective_date`, `version`, `supersedes_document_id` form alanları opsiyoneldir.
Sistem promptu `backend/app/services/answer_prompt.py`'dedir; kopyası `docs/prompts/ANSWER_SYSTEM_PROMPT.md`
(`make prompt-doc` ile yenilenir, `make lint` eşitliği denetler).

Retrieval (Phase 3.2b): soru kelimeleri `backend/app/services/search_glossary.py`'deki alan sözlüğüyle genişletilir
(Türkçe "finansman/kredi/faiz…" → İngilizce belgedeki "financing/loan/interest…", ve tersi), böylece Türkçe soru
İngilizce finans belgesinin **doğru sayfasını** bulur; en iyi `RETRIEVAL_TOP_K` (varsayılan 80 — Phase 3.2b'de 40,
Phase 5.1b'de 70 belgelik korpus için 80'e çıkarıldı) chunk (sayfa) prompt'a girer, eşit skorlu sayfalar
deterministik sırayla (belge, sayfa) seçilir. Her cevabın prompt'a giren sayfaları `audit_log.chunks_retrieved`'da
saklanır.

Canlı LLM testleri `make test`'in dışındadır: `make test-llm` (ücretsiz katman 5 istek/dk — testler kendini yavaşlatır;
model saturasyonunda `make test-llm MODEL=gemini-3.5-flash`).

## Soru yönlendirme — router (Phase 4.3)
`/api/ask` tek giriş noktasıdır (ADR-010). Her soru önce ucuz bir sınıflandırma çağrısından geçer
(`LLM_MODEL_CLASSIFY`, JSON) ve üç tipten birine yönlenir; tip cevapta `query_type` olarak döner ve
`audit_log.query_type`'a yazılır (`GENERAL_QUERY` 30.09.2026'da kaldırıldı — sistem hiçbir soruyu modelin genel
bilgisinden cevaplamaz, tanım soruları da belgelere bakar):

| Tip | Ne olur | Kaynak |
|---|---|---|
| `DOCUMENT_QUERY` | eskisi gibi belge hattı (retrieval → prompt → `[K#]`) | `sources` (belge + sayfa) |
| `DATA_QUERY` | `POST /api/excel/ask` ile **aynı** kod (plan → DuckDB/Python → aktarım); Excel'de bulunamazsa soru **belge hattına düşer** (cevap `DOCUMENT_QUERY` olarak döner) | `excel_sources` (dosya + sheet + aralık) |
| `MIXED_QUERY` | router iki alt soru üretir; belge hattı + Excel hattı **ikisi de** koşar; iki cevap "Belgelere göre: / Excel verisine göre:" başlıklarıyla **yorumsuz** birleştirilir (üçüncü LLM çağrısı yok) | ikisi birden |

Belirsiz sorular ("Güncel DSCR kaç?") MIXED'dir: belge tarafı sözleşmedeki covenant'ı (1,20x, Amendment 01),
Excel tarafı gerçekleşen değeri (1,37x, `Covenant_Report.xlsx Q2_2026!D14`) verir. Router hatası/bozuk JSON →
`DOCUMENT_QUERY`. Bir `/api/ask` çağrısı = **bir** audit satırı (`sources` JSON'unda her kart `kind: document|excel`
taşır, `excel_files_used` dolu); satırın id'si cevapta `audit_log_id` olarak döner. `/api/excel/ask` router'sız DATA
ucu olarak kalır (Ürün 2 kapısı, aşağıda).
```bash
curl -s -X POST localhost:8080/api/ask -b cookies.txt -H 'content-type: application/json' \
  -d '{"question": "Güncel DSCR kaç?"}'
# {"query_type":"MIXED_QUERY","answer":"Belgelere göre:\n... 1,20x ... [K1]\n\nExcel verisine göre:\n... 1,37x ...",
#  "sources":[{"ref":"K1","title":"Facility Agreement Amendment 01","page_number":3,...}],
#  "excel_sources":[{"file":"Covenant_Report.xlsx","sheet":"Q2_2026","range":"D14","label":"Covenant_Report.xlsx Q2_2026!D14"}],...}
```
Router promptu `backend/app/services/router.py`; kopyası `docs/prompts/ROUTER_PROMPTS.md` (`make prompt-doc`,
`make lint` eşitliği denetler). Maliyet: soru başına LLM çağrısı DOCUMENT 2, DATA 3, MIXED 4 — ücretsiz katmanda
(5 istek/dk) `make eval` istek aralığı bu yüzden 26 sn.

## Ürün paketi ve cevap alanları — Aşama A (30.09.2026, B-25 / B-04 / B-07)
Müşteride hangi ürün katmanlarının açık olduğu tek satırlık `company_settings.enabled_products` tablosunda tutulur
(`P1` Tanıma, `P2` Birleştirme, `P3` Yorumlama; demo'da üçü de açık, ADR-022). Değer `/api/auth/login` ve
`/api/auth/me` cevabında `enabled_products` olarak döner; AI-BalBal arayüzü buna göre ekran açar/kapatır.
```bash
make set-products PRODUCTS=P1              # demo/test: yalnızca Ürün 1 (CLI: python -m app.cli set-enabled-products P1)
make set-products PRODUCTS=P1,P2,P3        # geri al
curl -s localhost:8080/api/admin/settings -b admin_cookies.txt                       # {"enabled_products":["P1","P2","P3"]}
curl -s -X PATCH localhost:8080/api/admin/settings -b admin_cookies.txt \
  -H 'content-type: application/json' -d '{"enabled_products":["P1","P2"]}'          # yalnızca admin
```
Ürün 2 kapalıyken: `POST /api/excel/ask` → `403 {"detail":"product_not_enabled"}`; `/api/ask`'ta router DATA/MIXED
seçse bile soru **reddedilmez**, yalnızca belgelerden cevaplanır (`query_type: DOCUMENT_QUERY`, `product_level: P1`)
ve cevaba `product_limit` uyarısı eklenir. Excel yükleme ve `/inspect` Ürün 1'de açık kalır (hesap yapmazlar).

`/api/ask` cevabındaki ek alanlar (hepsi eklemeli, eski istemciler etkilenmez):

| Alan | Anlamı |
|---|---|
| `audit_log_id` | Bu cevabın `audit_log` satırı (yalnızca admin API'siyle okunur; id'yi bilmek yetki vermez) |
| `product_level` | Cevabın üretildiği katman: `DOCUMENT_QUERY → P1`, `DATA/MIXED → P2` (nihai tipe göre) |
| `warnings[]` | `{kind, message, action?}` — `missing_data` (kaynak yok; `action: request_data`, B-11 butonu) veya `product_limit`; metinler sabit, LLM üretmez |
| `sources[].supersedes_document_id`, `superseded_by_document_id`, `is_initial` | Versiyon zinciri komşularının id'si (yetkisiz komşu → `null`, başlığı gibi) ve "ilk halka" işareti |

Denetim kaydı satırı da `product_level` ve `warnings` taşır (`GET /api/audit-log/{id}`). "Beğendim / hatalı" geri
bildirim ucu **yoktur** (Tansu, 30.09.2026): uyarılar onun yerini alır.

## Audit log (Phase 3.4)
Her `/api/ask` çağrısı (cevaplı, "bilgi bulamadım" veya LLM hatası — hepsi) `audit_log` tablosuna bir satır yazar:
kim sordu, ne zaman, hangi kapsamda, hangi belgeler getirildi, cevap, kaynaklar, model, token, süre, `request_id`,
hata (varsa). Audit log **kurumsal hafıza değildir** (ADR-016): retrieval'da veya prompt'ta hiç kullanılmaz,
yalnızca admin görür, 90 gün sonra otomatik silinir (arka planda 6 saatte bir; elle: `make cleanup-audit-log`).
Şifre/API key/JWT hiçbir zaman yazılmaz.
```bash
curl "http://<vm-ip>:8080/api/audit-log?limit=20" -b admin_cookies.txt        # hafif liste (cevap/kaynak yok)
curl "http://<vm-ip>:8080/api/audit-log?has_error=true" -b admin_cookies.txt # yalnızca hatalı çağrılar
curl "http://<vm-ip>:8080/api/audit-log/<id>" -b admin_cookies.txt           # tam kayıt (cevap + kaynaklar)
```
Filtreli görüntüleme arayüzü admin panelinde (`/yonetim/denetim-kaydi`, Phase 5.2) — yukarıdaki filtreleri
birebir bir form + sayfalanmış tablo + satır tıklayınca tam kayıt paneli olarak sunar, backend değişmedi.
`cost_estimate` V0'da her zaman `null` — gerçek model fiyatları doğrulanmadan uydurulmuyor.

## Embedding (Phase 3.4, opsiyonel)
`EMBEDDINGS_ENABLED=false` varsayılan ve **referans yapılandırma**: sistem ve test paketi `embed` servisi hiç
çalışmadan tam çalışır. `true` yapılıp `make up-full` ile `embed` (bge-m3, `text-embeddings-inference`, CPU)
başlatılırsa, `/api/ask` retrieval'ı FTS + vektör aramayı Reciprocal Rank Fusion ile birleştirir — bazı sorularda
(örn. metinde literal geçmeyen kısaltmalar/eş anlamlılar) yalnızca FTS'in bulamadığı belgeleri de bulur. Arka
planda bir döngü mevcut chunk'ları otomatik embedler (`document_chunks.embedding`, ~15 sn'de bir, elle:
`make backfill-embeddings`). `embed` servisi geçici kapalıysa/yavaşsa retrieval sessizce FTS-only'e düşer —
`/api/ask` bu yüzden asla 503 vermez.
```bash
sed -i 's/^EMBEDDINGS_ENABLED=.*/EMBEDDINGS_ENABLED=true/' .env
make up-full        # embed'i indirir + başlatır (~2 GB indirme, ilk açılış birkaç dakika)
```
**Canlı ölçüm (bu VM, 24.09.2026):** `embed` container'ı hazır olana kadar ~3 dk 45 sn (model indirme + ONNX
ağırlıkları + ısınma); RAM **~10,5 GB** (bge-m3'ün yayınlanan ağırlık boyutundan — ~1,1 GB fp16 — beklenenin çok
üzerinde; fark TEI'nin CPU çalışma zamanı overhead'i — batch tamponları, ONNX runtime, tokenization worker'ları).
16 GB VM'e sığıyor (`free -h` her şey çalışırken ~4 GB "available" gösterdi) ama planlanandan daha az pay
bırakıyor — `docs/reports/PHASE_3_4_REPORT.md`'de tam rakamlar ve canlı bir "önce FTS'te 0 sonuç, embedding
açılınca doğru cevap" örneği var.

## Excel analizi (Phase 4.2)
Excel doküman RAG'ıyla çözülmez (SPEC_04): `.xlsx/.xlsm/.csv` upload'da OCR'a girmeden hemen `ready` olur, chunk
yazılmaz; sheet'ler soru anında DuckDB tablolarına (`<dosya>__<sheet>`, `_row` = Excel satır no) yüklenir.
**LLM matematik yapmaz:** bir *plan* çağrısı (`LLM_MODEL_CLASSIFY`, JSON) predefined fonksiyonlardan birini
(`dscr`, `outstanding_debt`, `budget_variance`, `capacity_factor`, `production`) ya da tek bir read-only `SELECT`
seçer; hesabı DuckDB/Python yapar; ikinci çağrı sonucu Türkçe aktarır — cevapta motorun rakamı aynen yoksa
şablon cevap döner. Her cevap **dosya + sheet + range** gösterir (`Covenant_Report.xlsx Q2_2026!D14`) ve
`audit_log`'a `excel_files_used` ile yazılır. Phase 4.3'ten itibaren `/api/ask` DATA sorularını da aynı koda
yönlendirir (bkz. "Soru yönlendirme"); `/api/excel/ask` router'sız doğrudan uç olarak kalır.
```bash
curl -s -X POST localhost:8080/api/excel/ask -b cookies.txt -H 'content-type: application/json' \
  -d '{"question": "Ankara RES 2026 Q2 DSCR kaç?"}'
# {"answer":"... 1,37x ...","answered":true,"value":1.37,"formatted_value":"1,37x",
#  "sources":[{"file":"Covenant_Report.xlsx","sheet":"Q2_2026","range":"D14","label":"Covenant_Report.xlsx Q2_2026!D14"}],
#  "plan_kind":"function","plan":{"kind":"function","name":"dscr","params":{"period":"Q2_2026"}},...}
curl -s localhost:8080/api/excel/<document_id>/inspect -b cookies.txt   # sheet'ler, gizli sheet, named range'ler, has_macros
```
Güvenlik: SQL whitelist (`;`/yorum yok, `SELECT`/`WITH` ile başlar, `DROP/ATTACH/INSTALL/LOAD/PRAGMA/COPY…` ve
`read_csv` gibi dosya fonksiyonları yasak, yalnızca bilinen tablolar, `LIMIT` ≤ `EXCEL_ROW_LIMIT`) + DuckDB
`enable_external_access=false` + `EXCEL_QUERY_TIMEOUT_S` zaman aşımı. **`.xlsm` macro asla çalıştırılmaz:** VBA
projesi zip içinden algılanıp `has_macros` olarak işaretlenir, hiçbir kod yolu yüklemez (`tests/test_no_execution_paths.py`).
Formül sonuçları dosyada yoksa (Excel dışı bir araçla kaydedilmişse) "dosyanın Excel'de yeniden hesaplanıp
kaydedilmesi gerekiyor" mesajı döner; sunucuda hesaplama yok. CSV: tek tablo, yalnızca SQL yolu.

Demo workbook'lar (`seed_data/excel/`, **commit'li**): Financial Model (Inputs/Debt/DSCR/Cashflow), Covenant Report
(Summary + çeyrek sheet'leri), Budget vs Actual, Monthly Production — hepsi ledger'dan formüllerle üretilir
(`generate_excel.py`), LibreOffice headless `tools` container'ında yeniden hesaplanır (`recalc.sh`, ~3 sn) ve
`validate_excel.py` ile doğrulanır (cached değer eksik yok, named range'ler, gizli `_meta`, ledger tutarlılığı):
```bash
make excel            # üret + recalc + doğrula (yalnızca dev'de; prod klonu LibreOffice gerektirmez)
make validate-excel   # commit'li dosyaları doğrula (make lint'in parçası)
```
Financial Model'in taban faiz, geri ödeme takvimi ve çeyreklik CFADS girdileri ledger'a `AI_ASSUMPTION` olarak
eklendi (`validate_ledger` F9-F11: DEMO_TODAY bakiyesi 44,1M, DSCR'ler covenant testleriyle ±0,01 tutarlı).

## Truth ledger (Phase 2.1)
İki demo projenin **tüm** rakam, tarih ve isimleri tek yerde: `seed_data/master/` — `company.yaml` (kurgusal
taraflar, SPV'ler, isim whitelist'i), `ankara_res.yaml` (işletmedeki proje: lisans → finansman → inşaat → COD →
operasyon, Facility zinciri DRAFT→V01→V02→EXECUTED→AMD01→AMD02), `izmir_res.yaml` (development; lisans sonrası
alanlar tasarım gereği `null`), `fx_rates.yaml` (kurgusal sabit kurlar). Şema: `seed_data/generator/ledger_schema.py`
(Pydantic). Golden sorular: `seed_data/evaluation/questions.json` (cevaplar rakam değil, `ledger:` yol referansı).
```bash
make validate-ledger     # kronoloji, finans tutarlılığı, İzmir izolasyonu, para birimi, isim whitelist, soru kotaları
# ... 0 error(s), 0 warning(s)  +  tags: USER_FACT=… AI_ASSUMPTION=…
```
**Onay akışı (ADR-013):** her değer `tag: AI_ASSUMPTION` (Claude taslağı) ya da `tag: USER_FACT` (Naci/ortak onayı)
taşır. Taslak tamamen `AI_ASSUMPTION` ile teslim edilir; onaylanan değerin tag'i YAML'da `USER_FACT` yapılır (değer
değişiyorsa yeni değer + `USER_FACT`), `make validate-ledger` tekrar 0 hata vermelidir. **Adım 3 (Phase 3.1, belge
üretimi) ayrı bir "ledger onayı" commit'i olmadan başlamaz.** Durum: v1 ledger **23.09.2026'da onaylandı**
(269/269 `USER_FACT`, "ledger onayı" commit'i); ileride eklenen her yeni değer yine `AI_ASSUMPTION` ile girer ve aynı
akıştan geçer. Onay tablosu `docs/reports/PHASE_2_1_REPORT.md §10`. `make lint` de validator'ı çalıştırır; ledger'ı
bozan bir düzenleme lint'i kırar.

## Eval (Phase 4.1)
`scripts/run_eval.py`: `seed_data/evaluation/questions.json` (v3: 61 soru — Phase 5.1'de `general` kategorisi ve
yeni belgelere değen 13 soru eklendi) → gerçek `/api/ask` çağrıları (`ask_as_user` ile giriş yapılmış demo kullanıcı) → skor →
`seed_data/evaluation/results/<model>_<tarih>/results.{md,json}` (git-ignored). Kaynak (required/forbidden)
kontrolü `seed_data/documents/manifest.json` + `seed_data/excel/manifest.json`'dan (`excel_sources[].file` →
workbook başlığı); beklenen değer,
ledger yolunu `seed_data/generator/facts.py::format_ledger_leaf` ile demo belgelere gömülen **aynı** biçimde
formatlayıp cevap metninde arar — liste/sözlük/`DOC-*` referansı/"henüz olmadı" tipi değerler için bu kontrol
atlanır (yalnızca kaynak+`answered` ile puanlanır; hangi sorular atlandığı raporda açıkça listelenir).
```bash
make eval                          # .env'deki mevcut LLM_MODEL_ANSWER ile
make eval MODEL=gemini-3.5-flash   # backend'i geçici olarak bu modelle yeniden başlatır, koşar, .env'e geri döner
```
İki teşhis modu (Phase 3.2b): `make eval EVAL_ARGS="--retrieval-only"` LLM çağırmadan, her sorunun **hedef sayfasının**
(`manifest.json key_facts_used` literal'inden türetilir) prompt'a girip girmediğini ölçer (recall@k, saniyeler, kota
harcamaz); `make eval EVAL_ARGS="--repeat 3 --ids ANK-FIN-002,ANK-FIN-007"` aynı soruyu tekrar sorup retrieval
kararlılığı ile model kararlılığını ayrı raporlar (`audit_log.chunks_retrieved` üzerinden).
Kategori eşikleri: `isolation`/`hallucination`/`authorization` %100, diğerleri ≥%80 (PHASES.md); altında kalınırsa
`make eval` sıfırdan farklı çıkar. Gemini ücretsiz katmanına uyum: istekler arası en az 26 sn (paylaşılan, tüm
demo kullanıcılar arasında; her `/api/ask` router + cevap = ≥ 2 LLM isteği), 503'te 3 kez artan gecikmeyle yeniden
deneme, 5 ardışık hata sonrası koşu güvenli
şekilde durur ("günlük kota tükenmiş olabilir" uyarısıyla) — bkz. `docs/reports/PHASE_4_1_REPORT.md`.

## Demo veri (Phase 3.1 + 5.1)
İki demo proje için 70 belge (Ankara RES 45, İzmir RES 15, şirket geneli 10 — SPEC_05 §6 dağılımı, Phase 5.1):
lisans + tadili, Facility Agreement zinciri (DRAFT→V01→V02→EXECUTED→AMD01→AMD02) + destek finans belgeleri
(security/pledge/drawdown/waiver), EPC sözleşmesi + tamamlama/garanti belgeleri, ÇED/arazi/bağlantı yazıları,
aylık üretim + bakım raporları, hukuk görüşleri, mali/idari onaylar, yönetim kurulu/pay sahipleri kararları vb.
Rakam/tarih/isim **yalnızca** `seed_data/master/*.yaml` truth ledger'dan gelir; LLM'e hiçbir zaman gerçek değer
verilmez — yalnızca `[[placeholder]]` token adları ve doldurulacak bölüm başlıkları. Prose'u (placeholder'lı
paragraflar) LLM bir kez üretir, `seed_data/generator/prose/*.yaml` olarak `tag: AI_ASSUMPTION` ile commit edilir;
gerçek değerleri (`generate_documents.py`, LLM çağırmadan) deterministik olarak yerine koyar ve WeasyPrint ile
PDF'i render eder. Bu yüzden **`make seed` hiçbir zaman LLM çağırmaz** — prod klonu API anahtarı olmadan da
demo veriyi yükleyebilir.

```bash
make prose               # yalnızca içerik değiştiğinde: LLM ile prose/*.yaml üretir/günceller, elle commit edilir
make validate-documents  # prose (P1/P2: sayı/para birimi/gerçek isim sızıntısı yok) + üretilmiş PDF (G1-G6) kontrolü
make seed                # ledger doğrula → 70 PDF render et → admin/demo kullanıcı/departman/proje → belgeleri yükle
                          # → ingestion_jobs'ın "ready" olmasını bekle
make reset-demo           # yalnızca belgeleri siler (TRUNCATE documents CASCADE + dosyalar); kullanıcı/departman/
                          # proje korunur; onay ister, `--yes` ile atlanır
```
Her belgenin taranmış (görüntüsel, OCR gerektiren) ya da dijital (metin katmanlı) kopyası vardır — gerçek OCR
hattını da uçtan uca test eder. Üretilen belgelerin manifesti: `seed_data/documents/manifest.json` (sayfa
haritaları, versiyon zinciri referansları — `app/` bu dosyayı okur, `seed_data.generator` paketini **asla**
import etmez, ADR-013). Belge spec'leri (`document_specs.py`) Phase 5.1'de tek dosyadan
`seed_data/generator/document_specs/` paketine bölündü — proje/departman başına bir dosya (400+ satır kuralı,
CLAUDE.md); `document_specs/__init__.py` hepsini tek bir `SPECS` sözlüğünde birleştirir. Hukuk departmanı artık
kendi belgelerine sahip (Ankara 3, İzmir 4 — Phase 5.1, bkz. `docs/reports/PHASE_5_1_REPORT.md`).

## Make hedefleri
| Hedef | Açıklama |
|---|---|
| `make up` / `make down` | postgres + backend + ocr-worker + caddy başlat (arayüz `:8080`) / durdur (veri kalır) |
| `make up-full` | `embed` dahil (profile `full`, 16 GB) |
| `make ps`, `make logs SVC=backend` | Durum ve loglar |
| `make test` | pytest: backend → şema doğrulaması → ocr-worker, sırayla; test DB (`company_ai_test`) compose içindeki Postgres'tedir |
| `make lint` / `make format` | ruff + mypy (backend), ruff (ocr-worker), prompt/ledger/excel doğrulamaları / otomatik biçimlendirme (frontend lint'i yok — `frontend/` emekli) |
| `make build-frontend` | Arayüz bundle'ını içeren caddy imajını yeniden derle (`make up` zaten yapar); kaynak `FRONTEND_DIR` (boş = AI-BalBal) |
| `make update-frontend REF=<sha\|main>` | AI-BalBal submodule'ünü ilerlet + caddy'yi yeniden derle (pointer'ı commit etmek sana kalır) |
| `make dev-frontend` | Emekli `frontend/` için Vite dev server `:5173` (kalıcı değil; AI-BalBal geliştirmesi Tansu'nun reposunda) |
| `make migrate`, `make migration NAME=...` | Alembic upgrade / yeni migration |
| `make seed-admin`, `make seed-demo-users`, `make seed-demo-departments`, `make seed-demo-projects` | Admin/demo kullanıcı/demo departman+üyelik/demo proje oluştur (yoksa) |
| `make set-products PRODUCTS=P1,P2` | Ürün paketini değiştir (B-25, bkz. "Ürün paketi ve cevap alanları") |
| `make prose` | LLM ile `seed_data/generator/prose/*.yaml` üret (yalnızca içerik değiştiğinde, elle commit edilir) |
| `make validate-documents` | Prose (P1/P2) + üretilmiş PDF (G1-G6) doğrulaması; `make lint`'in parçası (`--prose-only`) |
| `make seed` | 15 demo belgeyi render edip yükler (bkz. "Demo veri (Phase 3.1)"); LLM çağırmaz |
| `make reset-demo` | Demo belgeleri siler (kullanıcı/departman/proje korunur); `--yes` ile onaysız |
| `make psql`, `make shell` | Postgres'e psql / backend container'ında bash |
| `make eval`, `make eval MODEL=...` | Eval runner (bkz. "Eval (Phase 4.1)") |
| `make excel` / `make validate-excel` | Demo workbook'ları üret+recalc+doğrula / yalnızca doğrula (bkz. "Excel analizi (Phase 4.2)") |
| `make backup`, `make backup ARGS="--sync-secondary"` | Yedek al (bkz. "Backup / restore (Phase 5.3)") |
| `make restore ARGS="2026-09-26"` | Yedekten geri yükle — **YIKICI** (bkz. "Backup / restore (Phase 5.3)") |

Postgres portu host'a açılmaz; `make psql` kullanın. Backend'in 8000 portu da Phase 3.3'ten beri host'a
açık değildir (`BACKEND_PORT` yalnızca compose ağı içindir); her şey Caddy'nin `CADDY_PORT`'u (8080) üzerinden.

## Backup / restore (Phase 5.3)
```bash
make backup                        # $DATA_ROOT/backups/<bugün>/: postgres.dump, documents.tar.gz,
                                    # excel.tar.gz, app-data.tar.gz, env.backup — 14 gün rotasyon
make backup ARGS="--sync-secondary" # yukarıdakinin yanı sıra backups/'ı BACKUP_SECONDARY_PATH'e (yerel
                                    # 8 TB disk) rsync ile aynalar; bunu ne zaman çalıştıracağınız
                                    # (disk spindown'dan önce) kendi cron'unuz — bu repo bir cron kurmaz
make restore ARGS="2026-09-26"      # YIKICI: mevcut tüm veriyi siler, yedekle değiştirir, onay ister
make restore ARGS="2026-09-26 --yes" # onaysız (otomasyon için)
```
Neler yedekleniyor: Postgres (`pg_dump -Fc`, `pg_restore --clean --if-exists` ile geri yüklenir —
docker-compose.yml'a hiç dokunmadan, çalışan `postgres` servisine stdin/stdout ile), `$DATA_ROOT/documents`,
`$DATA_ROOT/excel` (bugün fiilen boş — Excel workbook'ları da `documents/` altında saklanıyor),
`$DATA_ROOT/app-data` (**`models/` alt dizini hariç** — bge-m3 embedding ağırlıkları, HuggingFace'ten yeniden
inebilen bir önbellek, kurumsal veri değil; `EMBEDDINGS_ENABLED=true` ile ilk açılışta kendini yeniden indirir).

`.env` **ayrı bir dosya** olarak (`env.backup`, `chmod 600`) yedeklenir, **şifrelenmemiş** olarak durur — bu
dosya `LLM_API_KEY`, `JWT_SECRET`, DB şifresi gibi sırlar içerir. İkincil diske veya başka bir yere taşımadan
önce kendi anahtarınızla şifreleyin, örn.:
```bash
gpg --symmetric --cipher-algo AES256 env.backup   # env.backup.gpg üretir; orijinali elle silin
```
`restore.sh` `.env`'i **hiçbir zaman otomatik değiştirmez** — geri yüklenen ortamın sırları (farklı bir host'a
restore ediliyor olabilir) kasıtlı olarak farklı olabilir; script yalnızca yedeğin `env.backup`'ının yolunu
yazdırır, taşımak size kalır.

`restore.sh`, Postgres verisini host'tan değil kısa ömürlü bir `--user root` konteynerinden siler — bind
mount'un sahibi container-içi `postgres` kullanıcısıdır (uid farklı), host kullanıcısının o dizine doğrudan
yazma izni yoktur.

## Repo düzeni
```
backend/      FastAPI (app/api, app/services, app/repositories, app/models, app/schemas, app/core), tests/, alembic/
frontend/     Vite + React 18 + TS (src/api istemci, src/auth, src/pages, src/components, src/lib/strings.ts); Dockerfile = lint/dev aracı
ocr-worker/   ocrmypdf + PyMuPDF ingestion worker; kendi pyproject/tests'i, backend/app'i import etmez
infra/        docker-compose.yml, Caddyfile, caddy/Dockerfile (frontend build + Caddy), .env.example, postgres/init, ocr-worker/Dockerfile
seed_data/    master/ (truth ledger), generator/ (prose, template, render, validate — app/ tarafından import edilmez),
              documents/ (üretilen PDF'ler + manifest.json, git'e girmez), evaluation/ (golden sorular)
scripts/      wait_for_services.sh, seed_demo.sh, reset_demo.sh (+ ileride backup/restore/eval)
docs/         SPEC_0x, PHASES.md, ARCHITECTURE.md (ADR), DOMAIN_MODEL.md, plans/, reports/, prompts/
```

## Bilinen sınırlar (V0)
- Yalnızca LAN, düz HTTP; HTTPS/Tailscale V0 sonrası.
- Embedding opsiyonel (`EMBEDDINGS_ENABLED=false` varsayılan); sistem yalnızca full-text + metadata ile çalışır.
- Consume klasörü, Word/e-posta ingest, SSO yok.
- Router bir LLM sınıflandırmasıdır (Phase 4.3): yanlış tip mümkündür; hata yönü DOCUMENT'a (kaynaklı) doğru
  tasarlanmıştır, GENERAL'e yanlış düşen bir soru yine de "şirket verisi kullanılmadı" der. MIXED birleştirme
  deterministik (iki parça, başlık), sentez yok.
- Gemini ücretsiz katmanı: `gemini-3.8-flash` için 5 istek/dk; yoğunlukta "high demand" 503 dönebilir — `/api/ask`
  bunu Türkçe 503 mesajıyla iletir, sistem çalışmaya devam eder.
- **Ücretsiz katmanın ayrı bir sınırı daha var: günlük 500 istek/proje/model** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
  dakika bazlı 5 istek/dk sınırından bağımsız). Phase 5.1'de tek bir yoğun geliştirme/test gününde (55 belgelik
  `make prose` + birkaç `make eval` denemesi + canlı testler) `gemini-3.5-flash-lite` bu kotayı tüketti; kota
  tükenince her çağrı 429 alıyor, uygulama bunu 503 olarak yansıtıyor (backend log'unda `quotaId`/`quotaValue`
  görünür). Kota genelde Pasifik gece yarısı civarı sıfırlanıyor. **Sonuç:** ücretsiz katman yoğun bir geliştirme
  gününü (özellikle içerik üretimi + eval + canlı test'in aynı güne denk geldiği fazları) tek başına kaldırmıyor —
  ücretli bir katman/kota artışı ya da işi birden fazla güne yaymak gerekebilir; bkz. `docs/PHASES.md` Phase 5.1 notu.
- `documents.department` bir FK değil, serbest slug string'idir (upload/apply endpoint'leri bilinen slug'a
  karşı doğrular, ama DB'ye doğrudan yazılan bir kayıt bunu atlayabilir); yanlış yazılmış bir slug güvenli
  yönde başarısız olur (belge admin dışında kimseye görünmez) ama sessizce.
- Departman CRUD ucu yok (V0'da yalnızca seed); proje-departman bağlantısı yalnızca organizasyonel/filtreleme
  amaçlıdır, belge yetkisi her zaman belgenin kendi `department` alanından gelir.
- AI metadata önerisinde (Phase 3.2) yalnızca tek bir öneri geçmişi tutulur (satır başına belge); geçmiş/analiz
  Phase 4.1'in eval kapsamına bırakıldı. Licence → Licence Amendment 01 çifti `related_document_ids` ile
  bağlı, `supersedes` değil (Phase 3.1) — bu yüzden "güncel"/"ilk" zincir mekanizmasına hiç girmiyor; SPEC_02
  §11'in kapasite örneği bu çift için değil, gerçek bir `supersedes` zinciri (örn. Facility Agreement) için
  geçerlidir.
- **Eval skoru (Phase 3.2c, 25.09.2026):** authorization/hallucination/isolation %100, document %87,0, temporal %88,9 —
  PHASES.md eşikleri (%100 / ≥%80) geçildi. Kalan 4 başarısızlık: iki negatif-olgu sorusu (NO OPINION kuralıyla çelişiyor,
  karar bekliyor) ve iki doğru cevabın soru setindeki ikinci atıf beklentisi — bkz. `docs/reports/PHASE_3_2C_REPORT.md`.
- **`make backup`'ın `.env` kopyası şifrelenmemiş** (`env.backup`, yalnızca `chmod 600` ile izinle kilitli) —
  script otomatik şifreleme yapmıyor (gpg/age gibi bir aracın VM'de kurulu olduğu doğrulanmadı); ikincil diske
  veya başka bir yere taşımadan önce elle şifrelemek operatörün sorumluluğunda (bkz. "Backup / restore (Phase
  5.3)").
