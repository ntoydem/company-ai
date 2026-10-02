# AI-BalBal frontend senkronu — PR-1 Raporu (`feat/backend-sync-urun1`)

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok  **company-ai commit:** `aa1c232`
**Plan:** `docs/plans/AIBALBAL_FRONTEND_SYNC_PLAN.md` (rev. 2, iki PR) · **Hedef repo:** `ftansu/AI-BalBal` · **PR:** https://github.com/ftansu/AI-BalBal/pull/2 (**açık, merge edilmedi** — karar Tansu'da) · **Dal:** `feat/backend-sync-urun1` @ `14f8c1c` (main `bdefb29` + `feat/urun1-arayuz` merge + 4 commit)

Naci'nin kararları: iki PR (onay akışı arayüzü ayrı PR-2'de), Yönetim › Ayarlar yok, küçük yeni öğeler "tasarım onayı bekliyor" işaretli, PR açılır/merge edilmez, Tansu'ya kısa özet. Backend'e **dokunulmadı**; company-ai'da yalnızca docs değişti. **LLM çağrısı: 0** (canlı kontrol curl ile).

## 1. Kabul kriterleri (plan §7, PR-1 satırları)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| S-01 | `npm run typecheck`, `lint`, `build` yeşil; Caddy imajı aynı Dockerfile ile kurulur, yeni bağımlılık yok | ✅ | node:20-alpine container'ında 3 komut yeşil; `package.json` değişmedi; dev VM'de `docker compose up --build caddy` → `Image company-ai-caddy Built` |
| S-02 | P1'de departman girişi `Urun1Home`, P2'de sekmeli ekran; ekip sohbeti düğmesi her pakette | ⚠️ kod merge edildi, **tarayıcı kontrolü Naci/Tansu** | `feat/urun1-arayuz` çakışmasız merge (`6970f8b`); mantık o daldan değişmedi |
| S-03 | Cevap kartı: `warnings` + `product_level` rozeti; P1'de DSCR örnekleri/Excel dipnotu yok; kaynak kartında versiyon linkleri, proje adı backend'den | ✅ kod / ⚠️ tarayıcı | `AnswerView`, `SourceCardList`, `AskPanel`, `BalbalChat`; bundle'da "Yeterli veri bulunmamaktadır" metni var |
| S-04 | "Aç" `?inline=1`, "İndir" düz | ✅ | `FileLink`; Caddy üzerinden `GET …/download?inline=1` → `Content-Disposition: inline; filename*=…pdf`, `Content-Type: application/pdf` |
| S-05 | Arama tek uçtan: snippet + sayfa, proje, kişi | ✅ | `SearchPanel` → `/api/search`; canlı: `q=Financial Model` → 5 belge, snippet dolu |
| S-06 | Klasörler gerçek (Belgeler, Yükle, Yönetim › Klasörler); "Backend bekleniyor" kalmaz | ✅ | `api/folders.ts` (proposed §10 ile alan alan aynı); canlı `/api/folders` → Proje Finans (write) |
| S-07 | `department_manager` etiketi/atama; kartlar üyelik bazlı; `review_status` rozeti yalnızca gösterim | ✅ | `ROLE_LABELS`/`ROLE_VALUES`, `isMembershipBased`; canlı `/login` → `department_manager`, `title`, `primary_department_slug`; bundle'da "Departman Yöneticisi", "Onay bekliyor" |
| S-09 | Ürün 2 öğeleri değişmedi | ✅ | `proposed.ts` §1–3, §5–9 aynen; `useHasProduct("P2")` kapıları aynen |
| S-10 | PR açıklaması: değişen/neden tablosu, içerdiği dallar, "Yeni görsel öğeler (tasarım onayı bekliyor)", kapsam dışı öneriler, `[ANAYASA KONTROLÜ]` | ✅ | PR #2 gövdesi |

Tarayıcıda yapılacaklar (S-02/S-03 görsel kontrol): `make set-products` ile P1 ve P1+P2 iki durum; `finans` ve `finans_mudur` ile giriş; cevap kartı rozetleri; klasör ağacı; arama paneli.

## 2. Yapılanlar (AI-BalBal, 5 commit)

1. `6970f8b` merge `feat/urun1-arayuz` — Ürün 1 giriş ekranı + ekip sohbeti netliği (v8.0).
2. `1b93ef0` tipler/roller — `types.ts` (`ProductLevel`, `FileKind`, `ReviewStatus`, `AskWarning`; `CurrentUser.enabled_products` zorunlu + `primary_department_slug`/`title`; `DocumentListItem.file_kind/folder_id/review_status`; `DocumentDetail` review alanları; `SourceCard` versiyon id'leri + proje; `AskResponse.audit_log_id/product_level/warnings`; `AdminUser` title/primary; `AskRequest.project_id` kaldırıldı), `format.ts` (`ROLE_LABELS/VALUES` + `department_manager`, `FILE_KIND_LABELS`, `REVIEW_STATUS_LABELS`, `PRODUCT_LEVEL_LABELS`), `visibility.ts` (`isMembershipBased`), `Home.tsx` (ana departman `primary_department_slug`), `UserMenu` (müdür yetki metni + unvan), `products.ts` yorum.
3. `70adb0c` dosya linkleri/kaynak/cevap — `FileLink` (`inlineUrl`), `SourceCardList` (versiyon linkleri, proje adı karttan), `AnswerView` (uyarı etiketleri + rozet), `AskPanel` (ölü proje çipi kaldırıldı, P1'de Excel örnekleri gizli), `BalbalChat` (pakete göre dipnot, müdür = üyelik).
4. `b684610` gerçek API'ler — yeni `api/search.ts`, `api/directory.ts`, `api/folders.ts`; `proposed.ts` §4/§10 kaldırıldı; `SearchPanel` tek uca; `DocumentsTab`/`UploadTab`/`AdminFoldersPage`/`TeamChat`/`TeamNewChat` import değişimi; `DocumentTable` `file_kind` + `review_status` rozeti.
5. `14f8c1c` docs — README ekran tablosu (7 satır), BACKEND_GAPS 10 maddeye "Durum (02.10.2026, PR …)" satırı (metin yeniden yazılmadı — ürün sahibinin belgesi).

Dokunulmayanlar: backend, `styles.css` (yeni sınıf yok), Ürün 2 öğeleri, `anayasa/`, `docs/gorev-devri-urun2` dalı.

## 3. Anayasa (AI-BalBal `CLAUDE.md`) uyumu

T-14 dal+PR ✓ · T-11 Ürün 1 etiketi + Ek-B atfı ✓ · Ç-14 görev sonu notu PR'da ✓ · T-12 yeni küçük öğeler "tasarım onayı bekliyor" listelendi (4 kalem) ✓ · Ç-16 kapsam dışı öneri olarak yazıldı ✓ · T-9 başka tarafın koduna dokunulmadı (backend yok; Tansu'nun ekranları yalnızca veri kaynağı değiştirildi) ✓ · yeni bağımlılık yok ✓.

## 4. Doğrulama

- Container'da (`node:20-alpine`, host'ta node yok) `npm ci` → `typecheck` → `lint` → `build`: temel (merge sonrası) ve son hal yeşil. İlk typecheck turunda 7 hata (kullanılmayan `putJson` importu, literal tuple tipi `includes`, `SearchPanel` birlik tipi, kaldırılmış `PendingNotice` kullanımı) — hepsi düzeltildi.
- Dev VM: `frontend-balbal` submodule geçici olarak dal commit'ine alındı → Caddy imajı kuruldu → SPA 200, bundle `index-sXsbkT0h.js` içinde `/api/search`, `/api/folders`, `/api/directory`, `inline=1`, "Departman Yöneticisi", "Onay bekliyor", "Yeterli veri bulunmamaktadır" → Caddy üzerinden API çağrıları (§1) → submodule `b219600`'a geri alındı; company-ai çalışma ağacı temiz (submodule pini **değişmedi**; merge sonrası ayrı commit).

## 5. Kendi aldığım küçük kararlar

| Karar | Neden |
|---|---|
| `AskPanel` proje çipi kaldırıldı | backend `/api/ask` `project_id` almıyor (Aşama B, Naci kararı) → çip sessizce etkisizdi; Ü-10 "Balbal penceresinde proje seçimi yok" |
| P1'de Excel örnek soruları ve dipnot cümlesi gizli | ADR-022: P1'de DATA sorusu `product_limit` uyarısıyla belgeye düşer; örnek göstermek yanıltıcı (NOT §6.4) |
| `review_status` rozeti yalnızca onaylı değilse | sadelik (Ü-10); 74 demo belge onaylı → liste değişmez |
| `enabled_products` tipi zorunlu, `products.ts` fallback kaldı | backend 30.09'dan beri gönderiyor; eski backend'e karşı güvenli varsayım korunur |
| `isPending` importu `AdminFoldersPage`'de kaldı | `PendingNotice` dalları artık ölü ama kaldırmak Ç-16 dışı refactor; PR notunda öneri |
| Olmayan `noFolderField`/`pending`/`peoplePending` string'leri silindi | kendi değişikliğimin ölü bıraktığı satırlar |

## 6. Açık sorular

- Yok. Tansu'nun kararı: PR #2 merge; 4 görsel öğe için tasarım onayı/düzeltme; S-02/S-03 tarayıcı kontrolü.

## 7. Sonraki adım

- **PR-2 `feat/onay-akisi-arayuz`** (PR-1 dalından): `submit`/`review` API'leri, 1. aşama paneli ("Onaylıyorum" kutusu, "Onaya gönder"), müdür kuyruğu + Onayla/Geri gönder, kayıt defteri. Naci "başla" dediğinde.
- Merge sonrası company-ai: `frontend-balbal` submodule pinini yeni main'e al (küçük commit) + README/NOT notu.

## 8. Doğruladığım üçüncü taraf davranışları

- Vite 5.4 + TS 5.6 + eslint 9 container'da sorunsuz; `npm ci` package-lock ile tam eşleşti.
- Caddy Dockerfile `additional_contexts` ile submodule'ün o anki checkout'unu aldı (dal commit'i); pin değişmeden imaj kuruldu — plan §6/6'daki "geçici checkout" yöntemi çalışıyor.

## 9. Kaynak kullanımı

LLM: 0. Build süresi ~1 dk (npm ci dahil ~3 dk ilk sefer).
