# AI-BalBal PR-2 Raporu — B-28 onay akışı arayüzü (`feat/onay-akisi-arayuz`)

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok  **company-ai commit:** `<commit>`
**Plan:** `docs/plans/AIBALBAL_PR2_PLAN.md` · **Hedef repo:** `ftansu/AI-BalBal` · **PR:** https://github.com/ftansu/AI-BalBal/pull/3 (**açık, merge edilmedi**; base `feat/backend-sync-urun1` = PR #2) · **Dal:** `feat/onay-akisi-arayuz` @ `a072968` (PR-1 dalı + 4 commit) · **Backend ön koşulu:** company-ai `a8308b2` (`DocumentDetailResponse.uploaded_by_id`)

Naci'nin SORU cevapları: (1) `uploaded_by_id` backend'e eklendi (düz commit); (2) yerel 4'lü tek çip grubu, yalnızca sayısı >0; (3) ≤2 CSS kuralı; (4) PR-2 base = PR-1 dalı. Backend'e bu alan dışında dokunulmadı. **LLM çağrısı: 0** (canlı akış Excel ile, curl).

## 1. Kabul kriterleri (plan §5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| P2-01 | typecheck/lint/build yeşil; `package.json` değişmedi; Caddy imajı kurulur | ✅ | node:20 container; dev VM `Image company-ai-caddy Built` |
| P2-02 | OCR belge: öneri → düzenlenebilir satırlar, 0.8 altı kutu; kutusuz 422 + vurgu; işaretle → "Onaya gönderildi", listede rozet | ✅ kod / ⚠️ tarayıcı | `MetadataSuggestionPanel` uploader modu (`needsConfirm`, `serverFlagged`), `.needs-confirm`; sunucu kuralı backend testlerinde (O-04) kanıtlı; görsel kontrol Naci/Tansu |
| P2-03 | Workbook: öneri yok → mevcut değerler, kutu yok → `pending_review` | ✅ | canlı: `finans` Excel upload → `submit {counterparty}` → `pending_review` |
| P2-04 | Öneri yokken düğme kapalı (`canSend`), `department_required` → departman satırı vurgulu | ✅ kod | panel `canSend = isWorkbook \|\| data !== null`; `onError` code eşlemesi |
| P2-05 | "Onaya gönder" yalnızca yükleyene (`uploaded_by_id`); Onayla/Geri gönder yalnızca hedef dept müdürüne; 403'ler `ErrorBox` | ✅ | `DocumentDetailPanel` `isUploader`/`isTargetManager`; canlı `uploaded_by_id` dolu |
| P2-06 | Geri gönder yorumsuz kapalı (UI) + sunucu 422 `comment_required`; yorumla `changes_requested`; yükleyen yorumu görür; yeniden gönder → `pending_review`, yorum sıfır | ✅ | canlı: `comment_required` → `changes_requested \| "Muhatap tam unvan olsun."` → resubmit `pending_review None` |
| P2-07 | Onayla → `approved`; rozet kalkar; belge aramada/Balbal'da | ✅ | canlı `approved`; arama/Balbal görünürlüğü B-28 backend testleri (O-05) + PR-1 arama paneli |
| P2-08 | Çipler yalnızca sayısı >0; müdür kuyruğu doğru; yerel süzgeç | ✅ kod | `ReviewFilterChips` + `lib/review.ts`; iki görünümde |
| P2-09 | Admin defteri sıralı Türkçe; personel/müdür görmez | ✅ | canlı `['uploaded','submitted','changes_requested','resubmitted','approved']`; kart `isAdmin` ile |
| P2-10 | Admin `apply`/`reject`/`PATCH` çalışır; notlar | ✅ kod | admin modu aynen; `applyNote`, `editNote` |
| P2-11 | Ürün 2 öğeleri değişmedi; `proposed.ts` dokunulmadı | ✅ | diff |
| P2-12 | PR açıklaması: bağımlı PR #2, değişen/neden, 5 görsel öğe, kapsam dışı, `[ANAYASA KONTROLÜ]` | ✅ | PR #3 gövdesi |

## 2. Yapılanlar

- **company-ai `a8308b2`:** `DocumentDetailResponse.uploaded_by_id` + test + ADR-024 satırı (90 ilgili test yeşil; lint yeşil).
- **AI-BalBal (4 commit):** `0442c3a` API katmanı (`ApiError.code/fields`, `DocumentSubmitRequest`/`DocumentReviewRequest`/`ReviewEvent`, `submitDocument`/`reviewDocument`, `useReviewEvents`, `REVIEW_EVENT_LABELS`, `CONFIRM_THRESHOLD`, `review` metinleri) · `b628b58` 1. aşama (`MetadataSuggestionPanel` `mode: uploader|admin|readonly`, kutu/vurgu/durum satırı; `UploadTab` mod seçimi; 2 CSS kuralı) · `2f638b8` 2. aşama + kuyruk (`ReviewStatusCard`, `ReviewEventsCard`, `ReviewFilterChips`, `DocumentDetailPanel` yerleşimi, not satırları) · `a072968` README + BACKEND_GAPS §4.7 durum satırı.
- Dokunulmayanlar: backend (tek alan hariç), `proposed.ts`, Ürün 2 öğeleri, `anayasa/`.

## 3. Doğrulama

- Container'da typecheck/lint/build yeşil (bir fast-refresh uyarısı → `applyReviewFilter` `lib/review.ts`'e taşındı).
- Dev VM: submodule geçici olarak `2f638b8`'e alındı → Caddy kuruldu → bundle `/submit`, `/review`, `review-events`, "Onaya gönder", "Onaylıyorum", "Geri gönder", "Kayıt defteri" içeriyor → Caddy üzerinden tam akış (§1) → test belgesi silindi (74 belge) → submodule `b219600`'a geri, Caddy yeniden kuruldu (`index-ClaCzDVC.js`), ağaç temiz.

## 4. Kendi aldığım küçük kararlar

| Karar | Neden |
|---|---|
| Uploader modunda gövde = dolu tüm alanlar (+`confirmed_fields`) | backend yalnızca verilen alanları yazar; yükleyen tüm formu onaylıyor |
| 0.8 eşiği frontend'de sabit | yalnızca kutuyu göstermek için; 422 `fields` ile sunucu kararı üstün |
| `department_required` → departman satırı vurgulu | aynı 422 vurgusu mekanizması |
| Yükleyen hedef dept müdürüyse panel `readonly`/`admin` | belge zaten `approved` |
| Admin aynı zamanda yükleyense `uploader` modu | admin de `submit` etmeli (403 `not_the_uploader` yalnızca başkası için) |
| Onay kartı yalnızca onaylı değilken | sadelik (Ü-10) |

## 5. Açık sorular

- Yok. Tansu: PR #2 ve #3 inceleme/merge sırası; 5 görsel öğe tasarım onayı; tarayıcı kontrolü.

## 6. Sonraki adım

- Merge sonrası company-ai: `frontend-balbal` pinini yeni main'e al; README/NOT notu.
- B-28b (backend + UI): `extra_fields`, etiket kataloğu, tür bazlı rehber; B-01/B-02 gelince çipler gündem/bildirimle birleşir.
