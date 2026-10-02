# AI-BalBal PR #5 Raporu — B-28b arayüzü (`feat/b28b-arayuz`)

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok  **company-ai commit:** bu rapor ile aynı commit (hash cross-ref commit'inde)
**PR:** https://github.com/ftansu/AI-BalBal/pull/5 (**açık, merge edilmedi**; base `main` = `b709f09`) · **Dal:** `feat/b28b-arayuz` @ `1d4cca2` (4 commit, 21 dosya, +1509/−31) · **Backend:** dokunulmadı (company-ai `75234e6` B-28b zaten canlı) · **LLM:** 0
**Plan:** `docs/plans/AIBALBAL_PR5_PLAN.md` — Naci'nin 6 SORU cevabı planın önerisiyle aynı: (1) değişiklik etiketleri yalnızca `amendment` ailesinde açık; (2) `tags.dropped` yalnızca admin modunda; (3) ek alanlar herkese + kaynak rozeti; (4) "Rehbere ekle" sinyal kısayolu dahil (yalnızca ön doldurma); (5) sıra PR-4 → PR-5, PR-5 `main`'den bağımsız; (6) CSS ≤ 3 kural.

## 1. Kabul kriterleri (plan §8)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| P5-01 | typecheck/lint/build yeşil; `package.json` değişmedi; Caddy imajı kurulur | ✅ | node:20-alpine'de üçü yeşil; dev VM'de Caddy imajı dalla yeniden kuruldu, `/`, `/yonetim/etiketler`, `/yonetim/tur-rehberi` → 200 |
| P5-02 | Etiket yalnızca çipten; AI önerisi seçili gelir; serbest metin yok; 422 `unknown_tag` `ErrorBox`'ta; değişiklik grubu `amendment` dışında katlı | ✅ | `TagPicker` (`useTags`), panelde `tags` durumu AI listesinden başlar; rehberin `suggested_tags`'i "Bu tür için önerilen" grubunda önde (seçili değil, tek tık); `submit.isError → ErrorBox`; `changeOpen` kuralı |
| P5-03 | Ek alanlar: AI satırı güven çubuğu + <0.8 kutusu; rehber satırları boş; "+ Alan ekle" normalize ön izleme; 20'de kapalı + sayaç; "×" mevcut anahtarı `null`; gönderimde `extra_fields` + `confirmed_fields: extra_fields.<key>`; 422 `fields` vurgusu | ✅ | `ExtraRow.origin` (suggestion/existing/guide/user), `needsConfirmExtra`, `extraBody()`, `serverFlagged` `extra_fields.` önekli anahtarları okur, `S.extra.counter`, `extraFull` |
| P5-04 | Detayda ek alanlar (`key: value` + kaynak rozeti) ve çip etiketler; `field_added` Türkçe | ✅ | `DocumentDetailPanel` yeni `<dt>Ek alanlar</dt>`, `TagPicker readOnly`; `REVIEW_EVENT_LABELS.field_added = "Alan eklendi (personel)"` |
| P5-05 | Yükleme formunda tür yazılınca rehber ipucu + "önemli"; zorunluluk yok | ✅ | `UploadTab`: `guideFor(form.documentType)` → `other` dışı ailede tek satır ipucu (aile · genellikle doldurulan ek alanlar · önemli: standart alanlar) |
| P5-06 | Yönetim › Etiketler: oluştur, 409/422, emekli et/aktifleştir, ad düzenle, geçmiş; employee rotaya giremez | ✅ | `AdminTagsPage` (`TagForm`, `TagRow`, `TagHistory` = `/api/admin/events` `tag_*`); rota `RequireAdmin` altında |
| P5-07 | Yönetim › Tür rehberi: aile seç/oluştur, desen çipleri, ek alan satırları, önerilen etiketler, vurgu, Balbal ipucu, aktif; kaydet → PATCH; sinyaller + "Rehbere ekle" ön doldurma; geçmiş | ✅ | `AdminGuidePage` (`FamilyForm`, `GuideForm` dirty/saved, `Signals` → `prefill` → forma satır, `GuideHistory`) |
| P5-08 | Arama: `tag`/`extra_field` rozeti; içerik eşleşmesinde yok | ✅ | `SearchPanel`: `matched_on !== "content"` → `MATCHED_ON_LABELS` rozeti |
| P5-09 | Admin panelinde `tags.dropped` notu; uploader'a gösterilmez | ✅ | `droppedNote={isAdmin && … ? data.fields.tags?.dropped : null}` |
| P5-10 | Ürün 2 öğeleri ve `proposed.ts` değişmedi; PR açıklaması bağımsızlık/PR-4 notu, 7 yeni görsel öğe, `[ANAYASA KONTROLÜ]` | ✅ | `git diff --stat b709f09..HEAD` içinde `proposed.ts`, `Layout.tsx`, `DocumentTable.tsx` yok; PR gövdesi |
| P5-11 | Canlı uçtan uca (admin etiket → `finans` yükler → panel → onay → aramada rozet), LLM ≤ 1 | ⚠️ kısmi | Dal dev Caddy'ye geçici alındı: SPA rotaları 200, bundle yeni metinleri içeriyor; ekranların çağırdığı uçlar admin olarak doğrulandı (`/api/tags` 20 aktif / 9 değişiklik, rehber 10 aile, `signals` [], `events` `tag_created pf-kredi`). **Tarayıcı tıklama akışı yapılmadı** (host'ta tarayıcı yok); aynı akış API düzeyinde B-28b raporunda (§3) kanıtlı. Pin `b709f09`'a geri alındı. LLM 0 |

## 2. Yapılanlar (AI-BalBal, 4 commit)

| Commit | İçerik |
|---|---|
| `74e24b8` feat(api) | `types.ts` (`SuggestionField.dropped`, `ExtraFieldValue`, `Tag*`, `Guide*`, `GuideSignal`, `AdminEvent`, `DocumentDetail.extra_fields`, `ReviewEventKind.field_added`), `api/tags.ts`, `api/guide.ts`, `api/admin-events.ts`, `search.ts` `matched_on`, `lib/typeFamily.ts` (backend ile aynı en uzun desen + Türkçe İ katlama, `normalizeExtraKey`), `lib/review.ts` `EXTRA_PREFIX`/`extraFieldSuggestions`, `lib/format.ts` etiketler |
| `7259915` feat(ui) | `TagPicker` (yeni), `MetadataSuggestionPanel` yeniden yazım (etiket çipleri, "Ek alanlar" bölümü, "+ Alan ekle" katlı satır, aile rozeti, admin `dropped` notu + "Rehberi düzenle" bağlantısı), `UploadTab` ipucu, `DocumentDetailPanel` etiket çipleri + ek alanlar, `SearchPanel` rozeti, `strings.ts` (`S.tags`, `S.extra`, `S.guide`, `S.admin.tags`, `S.admin.guide`), `styles.css` 3 kural |
| `b6c9a08` feat(admin) | `AdminTagsPage`, `AdminGuidePage`, `AdminLayout` 2 sekme, `router.tsx` `etiketler`, `tur-rehberi` |
| `1d4cca2` docs | README özellik satırı; `BACKEND_GAPS.md` §4.7.2 / §4.7.3 / §4.7.4 "Durum" satırları |

## 3. Doğrulama

- `./fe.sh "npm run typecheck && npm run lint && npm run build"` → yeşil (156 modül, JS 402 kB / gzip 120 kB; CSS 24.7 kB). İlk turda iki typecheck hatası (`field_added` birlikte yoktu; `form` kullanımdan önce) → düzeltildi.
- Canlı: §1 P5-11. Smoke komutları Caddy üzerinden `admin` ile; dal sonra `b709f09`'a döndürüldü ve Caddy yeniden kuruldu (`git -C frontend-balbal rev-parse --short HEAD` = `b709f09`; company-ai çalışma ağacı temiz).

## 4. Anayasa

T-11 Ürün 1 + Ek-B · T-12 PR'da 7 yeni görsel öğe "tasarım onayı bekliyor" · Ç-14 `[ANAYASA KONTROLÜ]` notu · Ç-16 kapsam dışı 3 öneri (klasör önerisi, sürükle-sıralama, geriye dönük öneri) · §4.7.7 kullanıcı ekranında iç not yok (`prompt_hint` yalnızca admin formunda, "kullanıcıya gösterilmez" notuyla) · P-1 insan kaydeder ("Rehbere ekle" yalnızca ön doldurma; etiket emekli edilir, silinmez) · T-14 dal + PR, main'e push yok, yeni bağımlılık yok.

## 5. Kendi aldığım küçük kararlar

| Karar | Neden |
|---|---|
| "+ Alan ekle" satırı katlı; tıklanınca anahtar/değer girdileri açılır | Ü-10 sadelik; ek alanı olmayan belgede panel uzamaz |
| Rehber satırları yalnızca düzenlenebilir modda ve kullanıcı sildiyse geri gelmez (`removedKeys`) | boş placeholder gönderilmez; "×" ile kapatılan satır tür değişince tekrar belirmesin |
| `source=ai` rozeti yalnızca değer öneriyle aynıysa; kullanıcı değiştirirse backend `user` yazar | backend `merge_extra_fields` kuralıyla aynı; arayüz tahmin etmez |
| Geçmiş tabloları `kind=null` ile çekip `tag_*`/`guide_*` önekine göre süzer | `?kind=` tam eşleşme (`tag_created` ≠ `tag`); iki istek yerine bir |
| Tür ipucu `other` ailesinde gösterilmez | "Diğer" rozeti boş tür alanında gürültü olur |
| Admin panelinde "Rehberi düzenle" bağlantısı yalnızca `other` dışı ailede | rehbersiz türde yönlendirecek bir satır yok |
| `TagPicker readOnly` seçili olmayan etiketleri göstermez; değişiklik etiketi `badge warn` | detay ve salt okunur panelde kalabalık olmasın; "değiştiren belge" bir bakışta ayrışsın |
| Canlı tarayıcı akışı yapılmadı | host'ta tarayıcı yok; API akışı B-28b raporunda kanıtlı; UI akışı Naci/Tansu PR incelemesinde |

## 6. Açık sorular / Tansu'ya

- T-12: 7 görsel öğe (PR gövdesinde). Özellikle "Ek alanlar" satır düzeni ve admin rehber formu yoğun — Tansu sadeleştirmek isteyebilir.
- `TagPicker`'da rehberin önerdiği etiketler önde ama **seçili gelmiyor** (yalnızca Balbal'ın önerdikleri seçili). İstenirse tek satırla seçili başlatılır — ürün kararı.

## 7. Tansu'ya kısa özet (PR #4 ile birlikte)

> İki PR bekliyor, ikisi de **merge edilmedi**, kararın sende; önerilen sıra #4 → #5 (bağımsızlar).
> **#4 (`feat/ux-kucuk-duzeltmeler`):** iki küçük düzeltme — Ürün 1 ekranında üst bara "Belgeler" linki; onaylı belgede yeşil "Onaylı" rozeti.
> **#5 (`feat/b28b-arayuz`):** etiketler artık listeden seçiliyor (yazılmıyor; değişiklik etiketleri yalnızca tadillerde açık), personel Balbal'ın açmadığı alanı kendisi ekleyebiliyor ("+ Alan ekle"; kim ekledi Balbal/Personel rozetiyle görünüyor), belge türüne göre ipucu satırı, Yönetim'de **Etiketler** ve **Tür rehberi** sayfaları (etiket ekle/emekli et; aile başına desen, ek alan, etiket, vurgu, Balbal ipucu; "Sinyaller" personelin elle sık eklediği alanları gösterir, "Rehbere ekle" yalnızca formu doldurur, kaydı sen yaparsın), arama sonucunda "Etiket eşleşmesi / Ek alan eşleşmesi" rozeti. Senin §4.7.9'daki "etiket listesini ve rehberi tamamla" işi artık ekrandan yapılabiliyor. 7 yeni görsel öğe tasarım onayına tabi; biçimi değiştirebilir ya da geri alabilirsin.

## 8. Sonraki adım

- Tansu'nun #4/#5 kararı → merge sonrası submodule pin + Caddy rebuild + merge raporu (PR #2/#3'teki gibi).
- Kalan B-28: klasör önerisi + 4.7.9/1 yerleştirme onayı (Tansu kararı). B-18: `hukuk_mudur`/`enerji_mudur`.
