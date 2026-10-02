# AI-BalBal PR #2 + #3 merge ve canlı doğrulama Raporu

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok  **company-ai commit:** `<commit>` (pin commit'i `81178cb`)
**AI-BalBal:** PR #2 `feat/backend-sync-urun1` → `main` (`fa329e5`), PR #3 `feat/onay-akisi-arayuz` → `main` (`b709f09`); `--merge` (merge commit), dallar silinmedi.

## 1. Yetkilendirme kaydı

Tansu PR #2/#3'ü sözlü olarak onayladı (Naci aktardı); vakti kısıtlı olduğu için GitHub'daki merge işlemi **Naci'nin açık talimatıyla** gerçekleştirildi. Merge komutlarını Naci bu oturumda `!` ile kendisi çalıştırdı — otomatik izin sınıflandırıcısı "merge without review" eylemini Claude için engelledi ve dolanılmadı. Tansu döndüğünde PR'ları ve canlı sonucu inceleyebilir, gerekirse geri alabilir veya düzeltme isteyebilir. Kayıt: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §0 banner.

## 2. Adımlar

| # | Adım | Sonuç |
|---|---|---|
| 1 | PR #2 merge → PR #3 base `main`'e çevrildi (`gh pr edit --base main`) → PR #3 merge | `fa329e5`, `b709f09` |
| 2 | `frontend-balbal` pini `b219600` → `b709f09` | commit `81178cb` (pushlandı) |
| 3 | Caddy yeniden kurulum (`docker compose up -d --build caddy`) | bundle `index-Csq0AN8a.js`; `/api/search`, `/api/folders`, `/api/directory`, `inline=1`, "Departman Yöneticisi", "Onaya gönder", "Onaylıyorum", "Kayıt defteri", `u1-bar` içeriyor |
| 4 | Canlı doğrulama (§3) | tamamı geçti |
| 5 | Pin commit + push | `81178cb` |
| 6 | Tansu notuna kayıt | §0 banner |
| 7 | Rapor + PHASES.md | bu dosya |

## 3. Canlı doğrulama (Caddy üzerinden, LLM yok)

```text
giriş: finans=employee, finans_mudur=department_manager, yonetim=management, admin=admin
       enabled_products [P1,P2,P3]; title ve primary_department_slug dolu
arama (finans_mudur, q="Financial Model"): 5 belge, snippet "Financial institutions acting on behalf of PQR Bank…", sayfa 3
klasörler: finans → [Proje Finans, write, 15]; admin ağaç 6 klasör
rehber (?department=finans): Proje Finans / Proje Finans Uzmanı, Proje Finans Müdürü / Proje Finans Müdürü
dosya linkleri: ?inline=1 → Content-Disposition: inline; filename*=…pdf — düz → attachment; filename*=…
Ürün 1 ekranı: SPA /departman/finans 200; paket P1,P2,P3 → sekmeli ekran (P1 ekranı için make set-products PRODUCTS=P1)
onay akışı: finans upload (Excel, department=finans) → pending_metadata, uploaded_by_id dolu; yonetim listede GÖRMEZ
            finans submit → pending_review; finans_mudur ?review_status=pending_review kuyruğunda
            finans_mudur approve → approved; yonetim listede görür ve /api/search bulur
            admin defteri: uploaded, submitted, approved
temizlik: test belgesi silindi (documents = 74)
```

Tarayıcı görünümleri (kutu/çip/pencere, Ürün 1 ekranı P1'de): Naci/Tansu.

## 4. Dev ortam durumu

Caddy http://192.168.8.70:8080 yeni sürümde (`b709f09`); backend `a8308b2` (`uploaded_by_id` dahil); paket P1,P2,P3; 74 belge onaylı; company-ai çalışma ağacı temiz.

## 5. Açık noktalar

- Tansu: PR #2/#3 sonradan inceleme; 9 küçük görsel öğe (PR-1: 4, PR-2: 5) için T-12 tasarım onayı/düzeltme; isterse geri alma (merge commit'lerini `git revert` + pin geri).
- B-18: `hukuk`/`enerji_grubu` için `department_manager` yoksa personel yüklemesi 409 (kabul edilmiş davranış).
- Sırada: B-28b (`extra_fields`, etiket kataloğu, tür bazlı rehber) ya da NOT §7.2 kalanları.
