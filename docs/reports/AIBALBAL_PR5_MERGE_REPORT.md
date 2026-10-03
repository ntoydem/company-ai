# AI-BalBal PR #5 merge ve canlı doğrulama Raporu

**Tarih:** 03.10.2026  **Model:** Claude Sonnet 5  **Tag:** yok  **company-ai commit:** `9abcde0` (pin commit'i)
**AI-BalBal:** PR #5 `feat/b28b-arayuz` → `main` (merge commit `59421ed`, 2026-10-03T08:25:46Z); dal silinmedi.

## 1. Gerçek durum kontrolü

`docs/reports/AIBALBAL_PR4_MERGE_REPORT.md`'de PR #5 hâlâ `OPEN` olarak raporlanmıştı. Naci'nin talimatıyla
`gh pr view 5 --repo ftansu/AI-BalBal --json state,mergedAt` tekrar çalıştırıldı:

| Alan | Değer |
|---|---|
| `state` | `MERGED` |
| `mergedAt` | `2026-10-03T08:25:46Z` |
| `mergeCommit.oid` | `59421edb1ec531af73de4925fa3efe27bd21879b` |

Gerçekten merge olmuş; tüm adımlar işlendi.

## 2. Adımlar

| # | Adım | Sonuç |
|---|---|---|
| 1 | `frontend-balbal` pini `92bd778` → `59421ed` | `git checkout 59421ed` (submodule) |
| 2 | Caddy yeniden kurulum (`docker compose build caddy` + `up -d caddy`) | bundle güncellendi |
| 3 | Canlı doğrulama (§3) | tamamı geçti |
| 4 | Pin commit + push | `9abcde0` (pushlandı) |
| 5 | Tansu notuna kayıt | §0 banner |
| 6 | Rapor + PHASES.md | bu dosya |

## 3. Canlı doğrulama (Caddy üzerinden, backend B-28b zaten vardı — ADR-025, `75234e6`)

```text
bundle: grep "Etiketler", "Tür rehberi", "Rehbere ekle", "Alan ekle", "Sinyaller", "matched_on" →
        hepsi /srv/assets/*.js içinde bulundu

Yönetim ekranları:
  SPA /yonetim/etiketler (admin): 200
  SPA /yonetim/tur-rehberi (admin): 200
  GET /api/admin/tags: 59 etiket, katalog dolu
  GET /api/admin/document-type-guide: 10 aile (amendment dahil), suggested_extra_fields dolu
  GET /api/admin/document-type-guide/signals: personelin elle eklediği anahtar sayılıyor (aşağıdaki
        test sonrası pr5_manual_field/contract/count=1 göründü)

Belge yükleme + etiket/ek alan arabirimi (uçtan uca, finans kullanıcısı, LLM gerçek):
  1. upload (seed_data/documents/2022-03-01_COMPANY_Board_Resolution..., department=finans) → uploaded
  2. OCR tamam (ingestion_status=ready, ~3 sn)
  3. POST /suggest-metadata → tags: [COMPANY, EXECUTED] (katalogda mevcut), extra_fields önerisi
     (meeting_date, resolution_no, decision_subject, güven 0.9-0.95)
  4. POST /submit → department+confidentiality confirmed_fields ile, tags aynen, + kullanıcının elle
     eklediği 4. alan (pr5_manual_field, "+ Alan ekle" senaryosu) → review_status=pending_review
     dönen extra_fields'ta source ayrımı doğru: AI alanları source=ai, elle eklenen source=user

Onay akışı (iki aşamalı, ADR-024/B-08):
  5. finans_mudur kuyruğunda görür (?review_status=pending_review)
  6. POST /review {"decision":"approve"} → review_status=approved, reviewed_by_id dolu

Arama matched_on (B-28b):
  7. q="EXECUTED" (etiket) → matched_on: "content" (doğal metinde de geçiyor)
  8. q="pr5_manual_field" (yalnızca ek alan anahtarı) → matched_on: "extra_field"

Temizlik: test belgesi (id 22dc5676-...) DB'den tek satır DELETE (FK cascade: pages/chunks/
        suggestion/review_events) + ${DATA_ROOT}/documents/22dc5676-.../ dizini silindi;
        documents sayısı önceki durumuna döndü (75).
```

Tarayıcı (gerçek görsel) testi yapılmadı — doğrulama curl + bundle grep + gerçek LLM çağrısıyla uçtan
uca API akışı ile sınırlı; biçim `AIBALBAL_MERGE_REPORT.md`/`AIBALBAL_PR4_MERGE_REPORT.md` ile aynı
yöntemdir. Görsel teyit Naci/Tansu'da.

## 4. Dev ortam durumu

Caddy http://192.168.8.70:8080 yeni sürümde (`59421ed`); backend değişmedi (B-28b zaten `75234e6`'da
vardı); company-ai çalışma ağacı temiz; `frontend-balbal` pini `59421ed`; `documents` = 75 (test
belgesi temizlendi).

## 5. Açık noktalar

- Tansu: PR #4 + #5 sonradan inceleme; T-12 tasarım onayı (toplam 7 + 9 = 16 görsel öğe, iki PR
  birlikte) hâlâ bekliyor; isterse geri alabilir.
- B-28b §4.7.9/1 "klasör önerisi" ve yerleştirme onayı Tansu'nun kararına kalan açık nokta (ayrı iş).
