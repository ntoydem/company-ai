# Phase 5.4 Raporu — Temiz kurulum doğrulaması + README final

**Tarih:** 26.09.2026  **Model:** Sonnet 5  **Tag:** phase-5-4  **Commit:** (bu rapor commit'iyle aynı)

## 0. Kapsam notu — planlanandan sapma (önemli)

`docs/PHASES.md`'deki Phase 5.4 planı `company-ai-prod` (Proxmox'ta temiz klon veya sıfır VM) üzerinde
`git clone`'dan başlayan tam bir kurulum + geniş bir kabul kriteri seti öngörüyordu. Bu oturum bunun yerine
**`company-ai-test` VM'inde (192.168.8.72), önceden var olan bir repo kopyası üzerinde** çalıştı: Naci'nin
isteği "hiçbir bağlamı olmayan biri için bu README yeterli mi?" testiydi — `.env` oluşturma → `make up` →
`make seed` → giriş → gerçek bir soru → yetki izolasyonu, sırayla ve README'nin dediğinin dışına çıkmadan.
Bu süreçte README'de iki gerçek eksik bulundu ve düzeltildi (bkz. §2). Bu, planlanan tam "prod'da temiz kurulum"
doğrulamasının **yerine geçmez** — aşağıdaki kabul kriterleri tablosu hangi kısmın karşılandığını, hangisinin
karşılanmadığını kelimesi kelimesine gösteriyor. Durum bu yüzden **kısmen tamamlandı** olarak işaretlendi.

**Naci'nin ek onayı ve talimatı (aynı gün, ikinci tur):** resmi eval kategorilerini (document/temporal/
isolation/hallucination) canlı LLM ile atlama kararı onaylandı — kota riski, zaten `company-ai-dev`'de
kanıtlanmış durumda. Buna karşılık iki ek iş istendi: (1) Excel/DuckDB hattının en az bir gerçek soruyla bu
VM'de de doğrulanması, (2) tarayıcı UI testinin Naci tarafından elle yapılacağının rapora/PHASES.md'ye not
düşülmesi. (1) denendi ama **günlük Gemini kotası bu VM'de de tükendiği için başarısız oldu** — bkz. §2/§3'ün
sonu; bu aslında §7'de zaten işaretlenen "iki VM aynı kotayı paylaşıyor" riskinin gerçekleştiğinin canlı kanıtı.
(2) Naci'nin kendisi yapacak; rapor/PHASES.md'de "elle yapılacak" olarak işaretlendi, tamamlandı diye
işaretlenmedi.

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt |
|---|---|---|---|
| 1 | `git clone` → `.env` (`DATA_ROOT=/srv/company-ai`) → `make up` → `make seed` → çalışır | ⏭ kısmen | `git clone` yapılmadı (repo bu VM'de zaten vardı); `.env` `cp infra/.env.example .env` ile oluşturuldu, 4 şifre rotate edildi; `DATA_ROOT` prod yolu (`/srv/company-ai`) değil dev varsayılanı (`./data`) kullanıldı — bu bir `company-ai-prod` VM'i değil. `make up` → `curl localhost:8080/health` → `{"status":"ok","version":"0.1.0","database":"ok"}` (README'deki örnekle birebir). `make seed` → 70 belge + 4 workbook, hepsi `ready`, "demo veri hazır." |
| 2 | Türkçe UI | ⏭ Naci elle yapacak | Bu oturumda yalnızca `curl`/API kullanıldı; tarayıcıda `http://<vm-ip>:8080` hiç açılmadı. Naci'nin talimatıyla: bu test Naci tarafından elle yapılacak, Claude Code kapsamı dışına alındı (bkz. §7) |
| 3 | `enerji` finansa ulaşamaz (UI+API+AI) | ⏭ kısmen | API: `/api/documents` finans içermiyor (36 belge, tek departman `enerji_grubu`), finans belgesini indirme → `403`. AI: aynı DSCR sorusu `enerji` ile sorulunca `answered:false`, `sources:[]`, sabit "...bulamadım" cevabı — sıfır kaynak sızıntısı. UI kısmı Naci elle yapacak (bkz. #2) |
| 4 | güncel/ilk DSCR farklı ve doğru | ⏭ kısmen | Yalnızca **güncel** DSCR test edildi: "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → **1,20x**, `[K76]`/`[K75]`/`[K53]`/`[K68]` kaynaklarıyla (Facility Agreement → Amendment 01 → Amendment 02 zinciri doğru okundu, `is_current` doğru). **İlk** DSCR (1,25x, EXECUTED) sorusu bu oturumda sorulmadı |
| 5 | Ankara/İzmir karışmaz | ❌ test edilmedi (Naci onayıyla atlandı) | Bu oturumda canlı bir LLM sorgusuyla doğrudan test edilmedi. Dolaylı kanıt: `--retrieval-only` eval'de `IZM-ISO-001`/`ANK-ISO-002`/`ANK-ISO-003` (isolation kategorisi) hedef sayfaları %100 prompt'a giriyor, ama bu yalnızca retrieval recall'u ölçer, LLM'in cevapta projeleri karıştırmadığını değil. Naci resmi eval kategorilerini (isolation dahil) kota riski nedeniyle atlamayı onayladı — bkz. §0/§3 |
| 6 | en az bir DuckDB analizi | ❌ denendi, günlük kota nedeniyle başarısız | "Ankara RES 2026 Q2 DSCR kaç?" `/api/excel/ask`'a soruldu, 5 kez (40 sn arayla) yeniden denendi — hepsi `503`. Backend logu kök nedeni doğruluyor: `gemini-3.5-flash-lite` (LLM_MODEL_CLASSIFY) için `RESOURCE_EXHAUSTED`, `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue: 500` — 5 denemenin 5'i de aynı hata, yani bu dakikalık değil **günlük** bir tükenme (muhtemelen `company-ai-dev`'in paralel kullanımından). §7'de zaten işaretlenen "iki VM aynı kotayı paylaşıyor" riskinin canlı, gerçekleşmiş kanıtı |
| 7 | kaynaksız soru uydurmaz | ⏭ kısmen (Naci onayıyla kısıtlı) | Resmi `GEN-HAL-*` soru seti canlı LLM ile koşulmadı — Naci kota riski nedeniyle onayladı (bkz. §0/§3). Dolaylı gözlem: alakasız bir test sorusu ("key hala calisiyor mu") ve yetkisiz DSCR sorusu, ikisi de kaynak uydurmadan doğru şekilde "bulamadım" dedi |
| 8 | README'de kurulum, model değiştirme, backup/restore, bilinen sınırlar (embedding opsiyonel, HTTPS yok, consume yok, Word/e-posta yok, Gemini ücretsiz katman günlük kota, eval isolation/temporal eşik altı) | ✅ | Bu oturumda bulunan 2 eksik (Gemini key alma, `.env` sonrası recreate) eklendi; geri kalanı önceki fazlardan zaten mevcut ve güncel (model değiştirme: `make eval MODEL=...`, backup/restore: Phase 5.3, "Bilinen sınırlar (V0)" bölümü embedding/HTTPS/consume/Word-e-posta/Gemini kota/eval eşiklerinin hepsini kapsıyor) |

**Genel sonuç:** README'nin "hiçbir bağlamı olmayan biri için yeterli mi" testinde iki gerçek eksik bulundu ve
düzeltildi; bulunan/düzeltilen kısımların hepsi gerçek, canlı bir ortamda (bu VM) doğrulandı. İkinci turda
Naci resmi eval kategorilerini kota riski nedeniyle atlamayı onayladı ve tarayıcı UI testini kendisi elle
yapacağını belirtti; buna karşılık istediği Excel/DuckDB testi **denendi ama günlük Gemini kotası (bu VM'in
`company-ai-dev` ile paylaştığı aynı key) tükendiği için başarısız oldu** — §1 satır 6, §2. `docs/PHASES.md`'nin
orijinal Phase 5.4 planı — `company-ai-prod`'da sıfırdan `git clone`, en az bir başarılı Excel/DuckDB analizi,
Ankara/İzmir'in canlı bir soruda karışmadığının kontrolü, ilk DSCR — bu oturumda **karşılanmadı**. Bu iş kapsam
dışı bırakılmadı; UI hariç geri kalanı ya denendi ve engellendi ya da Naci'nin açık onayıyla atlandı, hepsi
§7'de not düşüldü.

## 2. Yapılanlar
- **`README.md` — iki eksik giderildi** (Naci'nin "hiçbir bağlamı olmayan biri için README yeterli mi" testi
  sırasında bulundu):
  1. "Soru sorma (Phase 0.3)" bölümüne **Gemini API key alma** talimatı eklendi:
     `https://aistudio.google.com/apikey`, Google hesabıyla giriş, "Create API key", ücretsiz katman (kredi
     kartı gerekmez).
  2. Yeni **"`.env` değiştikten sonra"** bölümü eklendi (Kurulum'un hemen ardına): sıradan
     `docker compose restart <servis>` yetmiyor, `docker compose --project-directory . -f infra/docker-compose.yml
     --env-file .env up -d --force-recreate <servis>` gerekiyor; nedeni tek cümlede açıklandı (`env_file`
     içeriği compose'un değişiklik takibine dahil değil, yalnızca `environment:` bloğundaki değişkenler
     diff'leniyor — `docker-compose.yml`'daki mevcut bir koddan doğrulandı).
- **Gerçek doğrulama (bu VM, canlı):**
  - `.env` oluşturuldu, `POSTGRES_PASSWORD`/`ADMIN_PASSWORD`/`JWT_SECRET`/`DEMO_USER_PASSWORD` rastgele
    değerlerle değiştirildi (`openssl rand -hex`).
  - `make up` → health check README'deki örnekle birebir.
  - `make seed` → 70 belge + 4 workbook, `ready`.
  - `LLM_API_KEY` Naci'den ayrı bir kanaldan alınıp `.env`'e yazıldı (company-ai-dev VM'indeki mevcut key'in
    aynısı — key rotasyonu yapılmadı, yalnızca kopyalandı); `.env` gitignore'lu, hiç commit edilmedi.
  - `docker compose restart backend` denendi → **yetmedi**, `LLM_API_KEY` hâlâ boş algılandı (`/api/ask` 503
    vermeye devam etti) — README'ye eklenen 2. eksik tam olarak bu şekilde canlı olarak doğrulandı.
    `--force-recreate` ile düzeltildi.
  - "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → doğru cevap + 4 kaynak kartı (§1 satır 4).
  - `enerji` kullanıcısıyla finans izolasyonu üç ayrı yoldan doğrulandı: belge listesi, indirme (403),
    `/api/ask` (§1 satır 3).
  - `make test`: 383 backend + 9 ocr-worker, tamamı yeşil.
  - `make eval EVAL_ARGS="--retrieval-only"`: recall@80 **36/36 (%100.0)** — Phase 5.3'teki temel çizgiyle
    birebir aynı.
  - **Excel/DuckDB testi (ikinci tur, Naci'nin talimatıyla):** `POST /api/excel/ask` ile "Ankara RES 2026 Q2
    DSCR kaç?" soruldu → `503`. 40 sn arayla 5 kez yeniden denendi (toplam ~3 dk) → 5/5 `503`. Backend logu:
    her denemede `gemini-3.5-flash-lite` (LLM_MODEL_CLASSIFY, Excel akışının plan çağrısı) için `429
    RESOURCE_EXHAUSTED`, `quotaId: GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue: 500` —
    API'nin döndürdüğü "N sn sonra tekrar dene" mesajına rağmen 5 ayrı denemenin hepsi aynı hatayı verdi, yani
    bu geçici/dakikalık bir sınır değil, **o günkü 500 istek/model kotası gerçekten tükenmiş** durumda (bu
    key `company-ai-dev` VM'iyle paylaşıldığı için muhtemelen oradaki eşzamanlı kullanımdan). Sonuç: bu
    kriter bu oturumda **karşılanamadı** — atlanmadı, denendi ve engellendi.

## 3. Eval kararı: `--retrieval-only`, tam `make eval` değil (Naci onayladı)
Tam `make eval` (61 soru, canlı LLM) yerine `--retrieval-only` çalıştırıldı; bu karar ilk turda Claude Code
tarafından gerekçelendirildi, ikinci turda **Naci açıkça onayladı** ("tam eval kategorilerini atla, kota
riski, zaten company-ai-dev'de kanıtlandı"). Gerekçe:
- `LLM_API_KEY`, company-ai-dev VM'iyle **paylaşılan aynı key** — o VM'de aktif geliştirme sürüyor olabilir;
  günlük kota (README "Bilinen sınırlar": `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, 500/gün/model)
  25-26.09.2026'da zaten bir kez tükenmişti (Phase 5.1 notu). Tam eval, dakika başına 5 istek sınırına uymak
  için soru başına ~26 sn bekliyor ve soru başına 2-4 LLM çağrısı yapıyor (61 soru × en az 2 = ~120+ çağrı) —
  paylaşılan kotayı gereksiz yere riske atardı.
- Bu oturumun asıl amacı (README'nin yeterliliğini test etmek + iki eksiği kapatmak) zaten güçlü, canlı
  kanıtla doğrulandı: gerçek DSCR sorusu + gerçek izolasyon testi, ikisi de tam LLM zinciriyle (router +
  answer) çalıştı ve doğru sonuç verdi (§1 satır 3-4). `--retrieval-only` bunun üzerine, kota harcamadan,
  retrieval/prompt katmanının Phase 5.3'teki durumdan sapmadığını (36/36, aynı sayı) doğruladı.
- Bu, resmi `document`/`temporal`/`isolation`/`hallucination` eval kategorilerinin bu oturumda **ölçülmediği**
  anlamına gelir — §1 satır 5/7'de buna açıkça işaret edildi.

## 4. Değişen dosyalar
`git diff --stat` (bu rapor commit'iyle): `README.md` (+15, iki yeni bölüm/not), `docs/PHASES.md` (durum
tablosu + Phase 5.4 notu), `docs/reports/PHASE_5_4_REPORT.md` (yeni). Kod değişikliği yok — plandaki "kod
değişikliği beklenmez" notuyla tutarlı. Migration yok.

## 5. Testler
- `make test`: 383 backend + 9 ocr-worker, tamamı yeşil (LLM çağrısı içermez).
- `make lint` bu oturumda ayrıca koşulmadı — değişiklik yalnızca `README.md`/`docs/*.md`, `lint` hedefi bunları
  kontrol etmiyor (yalnızca `ruff`/`mypy`/`eslint`/`tsc`/prompt-doküman eşitliği/ledger-belge-excel
  validasyonları — bkz. `Makefile`); Phase 5.3'te zaten yeşildi ve bu fazda kod dokunulmadı.
- `make eval EVAL_ARGS="--retrieval-only"`: recall@80 36/36 (%100.0) — §1/§3.

## 6. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `company-ai-prod` yerine `company-ai-test` VM'inde çalışıldı, `git clone` yapılmadı | Naci'nin bu oturumdaki açık talebi buydu ("bu test VM'indeki repo kopyasında yap... company-ai-dev VM'inde DEĞİL"); orijinal Phase 5.4 planı ayrı, daha geniş bir doğrulamayı öngörüyordu | Plan'daki "prod'da temiz kurulum" kriterleri hâlâ açık — §1/§7'de işaretlendi |
| Tam `make eval` yerine `--retrieval-only` | Paylaşılan/kota riski taşıyan `LLM_API_KEY`, uzun çalışma süresi (~26+ dk); asıl doğrulama zaten canlı tek-soru testleriyle sağlandı | Resmi eval kategorileri (document/temporal/isolation/hallucination) bu oturumda ölçülmedi |
| `LLM_API_KEY` rotate edilmedi, company-ai-dev'deki mevcut key aynen kopyalandı | Naci'nin talebi buydu; key üretimi/rotasyonu bu oturumun kapsamında değildi | İki VM aynı Gemini kotasını paylaşıyor — ileride biri diğerinin kotasını tüketebilir, ayrı key önerilir (bkz. §7) |

## 7. Açık sorular / riskler (Naci değerlendirmeli)
- **Tarayıcı UI testi (Türkçe UI, `enerji`↔finans UI kısmı) Naci tarafından elle yapılacak** — Naci'nin
  talimatı; bu oturumda (Claude Code, yalnızca `curl`/API) hiç yapılmadı, kapsam dışı bırakıldı. `docs/PHASES.md`
  §5.4'te ve bu raporda "elle yapılacak" olarak işaretli, tamamlandı denmedi.
- **`docs/PHASES.md`'nin orijinal Phase 5.4 planı hâlâ tam karşılanmadı**: `company-ai-prod`'da sıfırdan
  `git clone` + `DATA_ROOT=/srv/company-ai`, en az bir Excel/DuckDB analizi (denendi, kota nedeniyle
  başarısız — bkz. §1 satır 6/§2), ilk DSCR (1,25x), Ankara/İzmir'in canlı bir soruda karışmadığının
  kontrolü, resmi `GEN-HAL-*`/`isolation` eval kategorilerinin canlı LLM ile koşulması (Naci onayıyla
  atlandı) — bunların hiçbiri bu oturumda tamamlanamadı. `SORU:` Bu kalan iş ayrı bir faz olarak mı
  planlanacak (ör. "Phase 5.5 — prod klon doğrulaması"), yoksa Phase 5.4 kapsamı bilinçli olarak bu
  oturumdaki dar anlamıyla mı kabul edilecek?
- **İki VM'nin aynı `LLM_API_KEY`'i (dolayısıyla aynı günlük Gemini kotasını) paylaşması artık teorik değil,
  bu oturumda canlı olarak gerçekleşti**: Excel/DuckDB testi tam bu yüzden 5/5 başarısız oldu
  (`gemini-3.5-flash-lite`, `GenerateRequestsPerDayPerProjectPerModel-FreeTier`, `quotaValue: 500` tükendi —
  §1 satır 6/§2). Ayrı bir `LLM_API_KEY` (VM başına) önerilir; aksi halde `company-ai-test`'teki gelecekteki
  testler `company-ai-dev`'deki geliştirmeyi kesintiye uğratabilir ve tam tersi.
- `env.backup`/`.env` şifrelemesi ve `BACKUP_SECONDARY_PATH` durumu bu fazın kapsamı dışında, Phase 5.3'ten
  değişmedi.

## 8. Doğruladığım üçüncü taraf davranışları
- **`docker compose`'ta `env_file:` içeriği "değişti mi" karşılaştırmasına dahil değil** — yalnızca
  `environment:` bloğunda açıkça yazılan değişkenler (`docker-compose.yml`'da zaten `LLM_MODEL_ANSWER` için
  aynı sebeple tekrarlanmış) diff'leniyor. Canlı doğrulandı: `.env`'de `LLM_API_KEY` değiştirilip
  `docker compose restart backend` çalıştırıldığında `/api/ask` hâlâ 503 ("Yapay zeka servisi
  yapılandırılmamış.") döndü; `--force-recreate` ile container yeniden oluşturulunca aynı istek 200 döndü.
- **`make eval` (MODEL override olmadan bile) sonunda backend image'ını `--build` ile yeniden inşa edip
  servisi yeniden başlatıyor** — bu, `.env`'deki `LLM_API_KEY`'i otomatik olarak da tazeliyor (yan etki);
  eval sonrası `/api/ask` sorunsuz çalışmaya devam etti.

## 9. Kaynak kullanımı
- Başarılı LLM çağrısı: 1 gerçek DSCR sorusu (admin, router+answer = 2 çağrı) + 1 aynı soru (`enerji`,
  router+answer = 2 çağrı, sıfır kaynakla sonuçlandı) + 1 kısa test sorusu (router+answer = 2 çağrı) —
  toplam ~6 başarılı LLM çağrısı. `--retrieval-only` eval LLM çağırmadı.
- Başarısız/reddedilen LLM çağrısı: Excel/DuckDB testi 5 kez denendi, hepsi `gemini-3.5-flash-lite`
  kotasında `429`'a takıldı (§1 satır 6/§2) — bunlar Google tarafında işlenmediği için muhtemelen günlük
  kotaya sayılmıyor, ama bu VM'in tarafında 5 ayrı istek+2 retry (SDK'nın kendi retry mantığı) anlamına
  geliyor.
- Docker: `make test` ~3,5 dk (206 sn backend + 6 sn ocr-worker); `make eval --retrieval-only` birkaç saniye
  (LLM yok) + backend'in sonundaki `--build` yeniden başlatması ~1 dk.
