# AI-BalBal PR #4 merge ve canlı doğrulama Raporu

**Tarih:** 03.10.2026  **Model:** Claude Sonnet 5  **Tag:** yok  **company-ai commit:** `63efe16` (pin commit'i)
**AI-BalBal:** PR #4 `feat/ux-kucuk-duzeltmeler` → `main` (merge commit `92bd778`); dal silinmedi.
**PR #5** (`feat/b28b-arayuz`) bu raporun kapsamı dışında — hâlâ `OPEN`, merge edilmedi, pinlenmedi (bkz. §5).

## 1. Gerçek durum kontrolü

Tansu PR #4 ve #5'i onayladığını söyledi; `gh pr view` ile iki PR da ayrı ayrı sorgulandı:

| PR | state | mergedAt | Not |
|---|---|---|---|
| #4 | `MERGED` | 2026-10-03T07:57:44Z | merge commit `92bd778` |
| #5 | `OPEN` | `null` | `reviews: []`, `mergeable: MERGEABLE` — yalnızca yorum bırakılmış olabilir, formal onay/merge yok |

Naci'nin talimatıyla yalnızca PR #4 kapsamı işlendi; PR #5 için hiçbir şey değiştirilmedi.

## 2. Adımlar

| # | Adım | Sonuç |
|---|---|---|
| 1 | `frontend-balbal` pini `b709f09` → `92bd778` | `git checkout 92bd778` (submodule) |
| 2 | Caddy yeniden kurulum (`docker compose build caddy` + `up -d caddy`) | bundle `index-CxavvDU0.js` |
| 3 | Canlı doğrulama (§3) | tamamı geçti |
| 4 | Pin commit + push | `63efe16` (pushlandı) |
| 5 | Tansu notuna kayıt | §0 banner |
| 6 | Rapor + PHASES.md | bu dosya |

## 3. Canlı doğrulama (Caddy üzerinden, LLM yok — PR #4 kapsamı)

```text
bundle: grep "Belgeler" ve "Onaylı" /srv/assets/index-CxavvDU0.js içinde bulundu
giriş (finans/123456): display_name=Proje Finans, role=employee, primary_department_slug=finans,
       enabled_products=[P1,P2,P3]
SPA /departman/finans: 200
SPA /departman/finans/belgeler ("Belgeler" linkinin hedefi): 200
GET /api/documents?review_status=approved: "Test Belgesi — Onay Akışı Denemesi" döndü —
       status=draft ("Taslak"), review_status=approved — tam olarak PR #4'ün çözdüğü
       kafa karıştırıcı durum (Taslak yazıyor ama onaylı); rozet artık bu belgede de
       görünür olmalı (bundle'da "Onaylı" string'i doğrulandı, backend alanı değişmedi).
```

Tarayıcı (gerçek görsel) testi yapılmadı — bu doğrulama curl + bundle grep ile sınırlı; biçim,
`AIBALBAL_MERGE_REPORT.md` §3'teki önceki PR #2/#3 doğrulamasıyla aynı yöntemdir. Görsel teyit
Naci/Tansu'da.

## 4. Dev ortam durumu

Caddy http://192.168.8.70:8080 yeni sürümde (`92bd778`); backend değişmedi; company-ai çalışma
ağacı temiz; `frontend-balbal` pini `92bd778`.

## 5. PR #5 — dokunulmadı

`feat/b28b-arayuz` hâlâ `OPEN`; `reviews: []`. Tansu'nun PR #5 üzerinde bıraktığı not bir yorum
olabilir, formal onay/merge değil. Pin, Caddy, canlı doğrulama PR #5'i kapsamıyor — B-28b arayüzü
(etiket kataloğu, ek alanlar, Yönetim › Etiketler/Tür rehberi, arama `matched_on` rozeti) main'de
**yok**. Sıradaki adım Tansu'nun PR #5'i gerçekten merge etmesi (ya da Naci'nin açık talimatı).
