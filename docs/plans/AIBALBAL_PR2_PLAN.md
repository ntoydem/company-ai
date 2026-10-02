# AI-BalBal PR-2 — B-28 onay akışı arayüzü (`feat/onay-akisi-arayuz`) — Uygulama Planı

**Tarih:** 02.10.2026 · **Durum:** **UYGULANDI** — PR #3 https://github.com/ftansu/AI-BalBal/pull/3 (`feat/onay-akisi-arayuz` @ `a072968`, base PR #2; merge Tansu'da); rapor `docs/reports/AIBALBAL_SYNC_PR2_REPORT.md`. · **Hedef repo:** `ftansu/AI-BalBal` · **Dal:** `feat/onay-akisi-arayuz`, **`feat/backend-sync-urun1`'in üstünden** (PR-1 #2 henüz merge edilmedi → PR-2'nin base'i PR-1 dalı; PR-1 merge olunca GitHub base'i `main`'e çevirir) · **Teslim:** PR → Tansu inceler, merge kararı onun; main'e push yok (T-14).

Kaynak: `docs/plans/AIBALBAL_FRONTEND_SYNC_PLAN.md` §3 "PR-2" tablosu (esas), ADR-024, `docs/reports/B28_ONAY_AKISI_REPORT.md`, backend `schemas/document.py` (`DocumentSubmitRequest`, `DocumentReviewRequest`, `ReviewEventResponse`, `DocumentDetailResponse`), `api/documents.py` hata kodları, `api/admin_documents.py`; AI-BalBal `feat/backend-sync-urun1` @ `14f8c1c`: `components/MetadataSuggestionPanel.tsx`, `DocumentDetailPanel.tsx`, `pages/department/{DocumentsTab,UploadTab}.tsx`, `api/{client,documents,types}.ts`, `lib/{strings,format}.ts`, `styles.css` (`.chips/.chip`, `.badge`, `.inline-check`, `.suggestion-row`, `.confidence`, `.modal-*`), `components/common/Modal.tsx`; Anayasa (Çekirdek O-1/O-3 "Onaylı Belge", Ç-7, T-11/T-12/T-14, Ç-14/16); BACKEND_GAPS §4.7.5 (%80 kutusu), §4.7.6 (defter admin), §4.7.7 (iç açıklama ekrana konmaz).

---

## 0. Ürün etiketi ve Anayasa çerçevesi

Her şey **Ürün 1 — Tanıma** (Ek-B Ürün 1: "belgeleri sınıflandırır, indeksler"; Çekirdek O-1 Onaylı Belge akışı, Ek-D S-6 "Belge Girişi": ilk okuma → öneri → %80 altı alan bazında açık onay → Kullanıcı kontrolü → Kullanıcı onayı). Yeni görsel öğeler **T-12** gereği "Ürün Yetkilisi tasarım onayı bekliyor" olarak PR'da listelenir; mevcut dil parçaları (`badge`, `chip`, `inline-check`, `button`, `Modal`, `suggestion-row`) dışında yeni bileşen dili icat edilmez. Ç-16: yalnızca bu akış; refactor yok. Ekrana iç açıklama konmaz (§4.7.7) — metinler kullanıcı dilinde, kısa.

## 1. Tespitler (PR-1 planındaki PR-2 tablosuna göre güncellemeler)

- **T1 — Yükleyen kimliği arayüzde yok (yeni, backend ön koşulu).** Backend `DocumentDetailResponse` `uploaded_by_id` **döndürmüyor**; `submit` yalnızca yükleyene açık (P-1). `UploadTab`'da az önce yükleyen kişi bellidir ama bekleyen/geri gönderilen bir belgeyi **sonradan** detaydan açan kullanıcının yükleyen olup olmadığı bilinemez → "Onaya gönder" düğmesi ya herkese gösterilip 403 yedirilir (kötü UX, Ü-10'a aykırı) ya da alan eklenir. **Karar önerisi:** company-ai'da **tek alan**: `DocumentDetailResponse.uploaded_by_id: UUID | None` (+ `AdminUser` değil; liste öğesine gerekmez). Backend'e 1 satır şema + 1 test; ADR gerekmez (ADR-024 "review trail" alanı). PR-2'den **önce** company-ai'a düz commit (SORU 1).
- **T2 — Hata gövdesinden `code`/`fields` okunmuyor.** `client.ts::describeError` yalnızca `message` ve 422 `errors` alıyor. B-28 hataları `{code, message, fields?}`; 422 `low_confidence_not_confirmed` → `fields` listesi, 409 `suggestion_pending`/`review_state_conflict`/`approver_not_configured`, 403 `not_the_uploader`/`not_the_approver`, 422 `comment_required`/`department_required`. **Zorunlu yan değişiklik (Ç-16):** `ApiError`'a `code: string | null` ve `fields: string[]` eklenir; `describeError` `record.code`/`record.fields`'ı taşır. Mesaj bugünkü gibi `detail.message`.
- **T3 — Panel modu.** `MetadataSuggestionPanel` bugün `isAdmin` ile iki mod (admin: işaretle + uygula/reddet; diğerleri salt okunur). Üçüncü mod **`uploader`**: tüm alanlar düzenlenebilir, varsayılan değer = öneri varsa öneri değeri yoksa belgenin mevcut değeri; satırda güven çubuğu zaten var; güveni `< 0.8` **ve** değer öneriyle aynı kalan satırlarda "Onaylıyorum" kutusu (`inline-check`); alt düğme **"Onaya gönder"** (durum `changes_requested` ise "Yeniden onaya gönder"). Gönderilen gövde = dolu alanların hepsi (`MetadataSuggestionApply` 9 alan) + `confirmed_fields`. Workbook'ta (`file_kind ∈ xlsx|xlsm|csv`) öneri yok → satırlar mevcut değerlerle, kutu yok, düğme açık. OCR belgede öneri yokken düğme kapalı + "Öneri hazırlanıyor" (mevcut `waiting` metni; `poll` zaten `UploadTab`'da true). Eşik frontend'de sabit `0.8` (yalnızca kutuyu göstermek için; **kural sunucuda** — 422 gelirse `fields` satırları işaretlenir, kutular zorunlu olur). Admin modu aynen kalır; `apply` düğmesinin altına kısa not: "Yayınlama onay akışıyla yapılır" (**şimdi `apply` yayınlamaz**, ADR-024).
- **T4 — Rol/yetki hesabı istemcide (yalnızca gösterim):** `isTargetManager = user.role === "department_manager" && doc.department ∈ user.department_slugs`; `isUploader = doc.uploaded_by_id === user.id` (T1). Düğmeler buna göre gösterilir; **yetki sunucuda** (403 yine `ErrorBox`).
- **T5 — Kuyruk süzgeci istemci tarafında.** `GET /api/documents` bekleyenleri işleyene zaten döndürüyor (handling view); liste küçük → `DocumentsTab`'da çipler **yerel süzgeç**: "Tümü" · "Onay bekleyen" (`pending_review`) · "Onaya hazırlanıyor" (`pending_metadata`) · "Geri gönderildi" (`changes_requested`) — yalnızca sayısı > 0 olan çipler görünür. `?review_status=` parametresi backend'de var; ek istek gereksiz (plan §3/3'teki iki çip yerine dört durumlu tek çip grubu — Ü-10 sade, kullanıcıya göre doğru olanlar kendiliğinden kalır).
- **T6 — Detay paneli üç kart kazanır:** (a) **Onay durumu kartı** (herkese, belge onaylı değilse): rozet (`REVIEW_STATUS_LABELS`), `review_comment` (varsa, "Geri gönderme açıklaması"), `submitted_at`/`reviewed_at` tarihleri; (b) hedef dept müdürü + `pending_review` → **Onayla** / **Geri gönder** (yorum zorunlu; `Modal` içinde `textarea`, boşsa düğme kapalı; 422 `comment_required` yine `ErrorBox`); (c) admin → **Kayıt defteri** kartı (`review-events`, salt okunur tablo: zaman, kişi, olay, alan, önce → sonra, güven, yorum; `REVIEW_EVENT_LABELS` Türkçe). Yükleyen + `pending_metadata|changes_requested` → mevcut `MetadataSuggestionPanel` **uploader** modunda (detayın altında zaten render ediliyor; `poll=false`).
- **T7 — `UploadTab` sonrası akış:** `ready` → panel `uploader` modu (`poll` true) → "Onaya gönder" → başarıda panel yerine kısa durum satırı: "Onaya gönderildi — departman yetkilisi onaylayınca aramada ve Balbal'da görünür" (`badge warn` + metin); yükleyen hedef dept müdürüyse backend `approved` döner → "Yayınlandı" (`badge ok`). Upload anında 409 `approver_not_configured` zaten `ErrorBox` ile Türkçe görünür (PR-1 sonrası doğrulandı) — ek iş yok.
- **T8 — Tablo rozeti (PR-1'de var)** `REVIEW_STATUS_LABELS` ile `approved` dışını gösteriyor; PR-2 ekleme yapmaz; çip süzgeci aynı etiketleri kullanır.
- **T9 — Backend sözleşmesi (değişmez):** `POST /api/documents/{id}/submit` gövde `MetadataSuggestionApply` alanları + `confirmed_fields: string[]` → `DocumentDetail`; `POST /api/documents/{id}/review` `{decision: "approve"|"request_changes", comment?}` → `DocumentDetail`; `GET /api/admin/documents/{id}/review-events` → `ReviewEvent[]` (kind: uploaded, auto_approved, field_edited, field_confirmed, submitted, resubmitted, approved, changes_requested, metadata_changed_after_approval). İstemci cache: başarıda `["document", id]`, `documents*`, `["suggestion", id]` invalidate.
- **T10 — Dondurulmuş ekranlar bozulmaz:** admin paneli (`apply`/`reject`), `DocumentMetadataEditForm` (admin PATCH — onaylı belgede onayı düşürür; forma tek satır not), `DocumentVisibilityCard` (`review_status` alanı geldi, bekleyen belgede "işleyenler" listesi — başlığa küçük açıklama).

## 2. Kapsam

**Dahil (Ürün 1):**
1. company-ai (ön koşul, ayrı düz commit): `DocumentDetailResponse.uploaded_by_id` + test + README/ADR-024 satırı. (SORU 1)
2. AI-BalBal `api/client.ts`: `ApiError.code/fields` (T2).
3. `api/types.ts`: `DocumentDetail.uploaded_by_id`, `DocumentSubmitRequest`, `DocumentReviewRequest`, `ReviewEventKind`, `ReviewEvent`.
4. `api/documents.ts`: `submitDocument`, `reviewDocument`; **yeni** `api/admin-documents.ts`: `useReviewEvents(id)`.
5. `lib/format.ts`: `REVIEW_EVENT_LABELS`, `CONFIRM_THRESHOLD = 0.8`; `lib/strings.ts`: `review` bölümü (Türkçe metinler).
6. `components/MetadataSuggestionPanel.tsx`: `mode: "admin" | "uploader" | "readonly"` (mevcut `isAdmin` prop'u `mode`'a dönüşür; çağıranlar güncellenir), uploader modu (T3), 422 `fields` vurgusu, `apply` altına not.
7. **Yeni** `components/review/ReviewStatusCard.tsx` (durum + yorum + tarihler + müdür aksiyonları + yorum modalı), **yeni** `components/review/ReviewEventsCard.tsx` (admin defteri). Küçük, tek sorumluluklu.
8. `components/DocumentDetailPanel.tsx`: kartları yerleştir; `mode` hesapla (`useAuth`).
9. `pages/department/DocumentsTab.tsx`: onay durumu çipleri (iki görünümde de), yerel süzgeç.
10. `pages/department/UploadTab.tsx`: panel `uploader` modu + gönderim sonrası durum satırı.
11. `styles.css`: en fazla iki kural (`.suggestion-row.needs-confirm` vurgu, `.review-events` tablo sıkılığı) — T-12 listesine girer.
12. README ekran tablosu + BACKEND_GAPS §4.7 durum satırı ("arayüz: PR-2").

**Hariç (PR notunda öneri):** `extra_fields`/etiket kataloğu/tür bazlı rehber (B-28b), gündem `approval` kalemi (B-01), bildirimler (B-02), müdür için metadata düzenleme ucu (backend'de yok; T9 istisnası yalnızca kuralda), admin `apply`/`reject` davranış değişikliği.

## 3. Yeni görsel öğeler (T-12 — Ürün Yetkilisi tasarım onayı bekliyor)

1. Öneri panelinde **"Onaylıyorum" kutusu** (güveni 0.8 altı satırlar) ve **"Onaya gönder" / "Yeniden onaya gönder"** düğmesi; 422'de satır vurgusu.
2. Belge detayında **Onay durumu kartı** (rozet + açıklama + tarihler) ve müdür için **Onayla / Geri gönder** düğmeleri + **yorum modalı**.
3. Belgeler sekmesinde **onay durumu çipleri**.
4. Admin için **Kayıt defteri kartı** (tablo).
5. Yükleme sonrası **"Onaya gönderildi" / "Yayınlandı"** durum satırı.

## 4. Sıra (her adım ayrı commit; adım sonunda `npm run typecheck && npm run lint && npm run build`)

0. company-ai: `uploaded_by_id` alanı → test → `make test` ilgili dosyalar + lint → düz commit + push (SORU 1 onayıyla).
1. `git checkout -b feat/onay-akisi-arayuz feat/backend-sync-urun1` (yerel klon güncel).
2. `client.ts` + `types.ts` + `api/documents.ts` + `api/admin-documents.ts` + `format.ts`/`strings.ts`.
3. `MetadataSuggestionPanel` `mode` + uploader akışı; `UploadTab` bağlantısı (T7).
4. `ReviewStatusCard` + `ReviewEventsCard` + `DocumentDetailPanel` yerleşimi (T6).
5. `DocumentsTab` çipleri (T5).
6. Dev VM canlı doğrulama (geçici submodule checkout, Caddy build; curl ile uçlar + Naci tarayıcı: §5 S-08) → submodule `b219600`'a geri.
7. README/BACKEND_GAPS → PR-2 aç (base `feat/backend-sync-urun1`, "Bağımlı olduğu PR: #2"), Tansu özeti → company-ai rapor + PHASES.md + NOT + commit/push → **dur**.

## 5. Kabul kriterleri

| # | Kriter |
|---|---|
| P2-01 | `typecheck`/`lint`/`build` yeşil; `package.json` değişmedi; Caddy imajı kurulur |
| P2-02 | Personel yükler (OCR belge) → `ready` → öneri gelir → panelde tüm alanlar düzenlenebilir, 0.8 altı satırlarda kutu; kutu işaretlenmeden "Onaya gönder" → 422 mesajı + ilgili satırlar vurgulu; işaretleyip gönder → "Onaya gönderildi" satırı, listede "Onay bekliyor" rozeti |
| P2-03 | Personel workbook yükler → öneri yok → panel mevcut değerlerle, kutu yok → gönder → `pending_review` |
| P2-04 | Öneri henüz yokken düğme kapalı/`suggestion_pending` mesajı; `department_required` → departman satırı vurgulu |
| P2-05 | Meslektaş/`yonetim`/`admin` detayda "Onaya gönder" **görmez** (`uploaded_by_id` eşleşmez); müdür `pending_review` belgede **Onayla / Geri gönder** görür, başkası görmez; sunucu 403'leri `ErrorBox`'ta Türkçe |
| P2-06 | Geri gönder: yorumsuz düğme kapalı; yorumla → `changes_requested`; yükleyen detayda yorumu ve "Yeniden onaya gönder"i görür; yeniden gönder → `pending_review` |
| P2-07 | Onayla → `approved`; belge aramada ve Balbal'da (PR-1'in arama paneli ile), listede rozet kalkar |
| P2-08 | Belgeler çipleri: yalnızca sayısı > 0 olanlar; müdürde "Onay bekleyen" doğru sayıyla; süzgeç yerel |
| P2-09 | Admin detayda kayıt defteri sıralı (`uploaded → field_confirmed/field_edited → submitted → approved`), Türkçe etiketlerle; personel/müdür bu kartı görmez |
| P2-10 | Admin `apply`/`reject`/`PATCH` çalışmaya devam eder; onaylı belgede PATCH sonrası rozet "Onay bekliyor" (backend T9) ve formda tek satır not |
| P2-11 | Ürün 2 öğeleri değişmedi; `proposed.ts` dokunulmadı |
| P2-12 | PR açıklaması: bağımlı PR #2, değişen/neden, **Yeni görsel öğeler (5)**, kapsam dışı öneriler, `[ANAYASA KONTROLÜ]` |

LLM çağrısı: canlıda **≤ 1** (onay sonrası belge sorusu; gerisi LLM'siz — öneri satırı testte elle yazılır ya da canlıda arka plan taraması bekleniyorsa Excel ile denenir).

## 6. Dosyalar

**company-ai:** `backend/app/schemas/document.py` (+`uploaded_by_id`), `backend/tests/test_documents.py` (1 assert), `README.md`/ADR-024 satırı.
**AI-BalBal:** `api/client.ts`, `api/types.ts`, `api/documents.ts`, **yeni** `api/admin-documents.ts`, `lib/format.ts`, `lib/strings.ts`, `components/MetadataSuggestionPanel.tsx`, **yeni** `components/review/ReviewStatusCard.tsx`, **yeni** `components/review/ReviewEventsCard.tsx`, `components/DocumentDetailPanel.tsx`, `components/DocumentMetadataEditForm.tsx` (tek satır not), `components/DocumentVisibilityCard.tsx` (bekleyen belgede başlık notu), `pages/department/DocumentsTab.tsx`, `pages/department/UploadTab.tsx`, `styles.css` (≤ 2 kural), `README.md`, `docs/BACKEND_GAPS.md` (§4.7 durum satırı).

---

## SORU (Naci cevaplamalı)

1. **Backend'e `DocumentDetailResponse.uploaded_by_id` eklensin mi?** (T1) Önerim **evet**, PR-2'den önce company-ai'a düz commit (şema + test, ADR yok). Alternatif: düğmeyi bekleyen her belgede herkese göstermek ve 403'e dayanmak — önermiyorum.
2. **Kuyruk çipleri yerel süzgeç** (T5, 4 durumlu tek grup) mi, planın önceki "müdüre Onay bekleyen / personele Geri gönderilenler" iki çipi mi? Önerim yerel 4'lü (kendiliğinden kullanıcıya göre daralır).
3. **`styles.css`'e ≤ 2 kural** (satır vurgusu, defter tablosu) kabul mü? Alternatif: sıfır yeni CSS (mevcut `error-box`/`table-wrap` ile idare edilir, vurgu daha zayıf).
4. PR-2 base = `feat/backend-sync-urun1` (PR-1 merge olmadan açılır) — teyit; merge sırası Tansu'da.
